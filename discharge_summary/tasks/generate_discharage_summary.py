from collections.abc import Iterable
from logging import Logger
from django.utils import timezone
import tempfile
from django.core import serializers
import json
import time
from botocore.exceptions import ClientError
from celery import shared_task
from celery.utils.log import get_task_logger
from care.facility.utils.reports.discharge_summary import (
    get_discharge_summary_data,
    set_lock,
    clear_lock,
)
from care.facility.models import PatientConsultation
from care.facility.models.file_upload import FileUpload
from care.utils.exceptions import CeleryTaskException
from uuid import uuid4
from django.template import Context, Template
from openai import OpenAI
from django.template.loader import render_to_string
from hardcopy import bytestring_to_pdf

from discharge_summary.constants import CONTINUED_PROMPT, INITIAL_PROMPT, SYSTEM_PROMPT
from discharge_summary.settings import plugin_settings

logger: Logger = get_task_logger(__name__)

OpenAIClient = None


def get_openai_client():
    global OpenAIClient
    if OpenAIClient is None:
        OpenAIClient = OpenAI(api_key=plugin_settings.SERVICE_PROVIDER_API_KEY)
    return OpenAIClient


def get_ai_response(user_prompt):
    response = get_openai_client().chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=4096,
        temperature=0.5,
    )
    return response.choices[0].message.content


def generate_discharge_summary_pdf(data, file, section_data):
    logger.info(
        f"Generating Discharge Summary html for {data['consultation'].external_id}"
    )
    logger.info(f"Section Data: {section_data}")

    total_progress = 40
    current_progress = 0
    ai_data = {}
    data_resolved = {}
    for key, value in data.items():
        if isinstance(value, Iterable):
            if hasattr(value, "all"):
                value = value.all()
            try:
                data_resolved[key] = [
                    serializers.serialize(
                        "json",
                        [
                            x,
                        ],
                    )
                    for x in value
                ]
            except:
                try:
                    data_resolved[key] = [json.dumps(x) for x in value]
                except:
                    data_resolved[key] = value

        else:
            data_resolved[key] = value

    summary_so_far = ""
    for i, section in enumerate(section_data.keys()):
        current_progress = int((total_progress / len(section_data.keys())) * (i + 1))
        set_lock(data["consultation"].external_id, current_progress)
        t = Template(section_data[section])
        c = Context(data)
        json_data = t.render(c)

        if i == 0:
            prompt = INITIAL_PROMPT.format(section=section, json_data=json_data)
        else:
            prompt = CONTINUED_PROMPT.format(
                summary_so_far=summary_so_far, section=section, json_data=json_data
            )
        logger.debug(prompt)

        section_summary = get_ai_response(prompt)
        ai_data[f"ai_summary_{section}"] = section_summary
        summary_so_far = section_summary
        time.sleep(10)

    combined_data = {
        **data,
        "ai_data": json.dumps(ai_data, indent=4).replace("\n", "<br>"),
    }

    combined_data["ai_summary"] = summary_so_far or "No Summary Generated"

    html_string = render_to_string(
        "reports/patient_ai_discharge_summary_pdf.html", combined_data
    )
    logger.info(
        f"Generating Discharge Summary pdf for {data['consultation'].external_id}"
    )
    bytestring_to_pdf(
        html_string.encode(),
        file,
        **{
            "no-margins": None,
            "disable-gpu": None,
            "disable-dev-shm-usage": False,
            "window-size": "2480,3508",
        },
    )


def generate_and_upload_discharge_summary(
    consultation: PatientConsultation, section_data
):
    logger.info(f"Generating Discharge Summary for {consultation.external_id}")

    set_lock(str(consultation.external_id), 5)
    try:
        current_date = timezone.now()
        summary_file = FileUpload(
            name=f"discharge_summary-{consultation.patient.name}-{current_date}.pdf",
            internal_name=f"{uuid4()}.pdf",
            file_type=FileUpload.FileType.DISCHARGE_SUMMARY.value,
            associating_id=consultation.external_id,
        )

        set_lock(str(consultation.external_id), 10)
        data = get_discharge_summary_data(consultation)
        data["date"] = current_date

        set_lock(str(consultation.external_id), 50)
        with tempfile.NamedTemporaryFile(suffix=".pdf") as file:
            generate_discharge_summary_pdf(data, file, section_data)
            logger.info(f"Uploading Discharge Summary for {consultation.external_id}")
            summary_file.put_object(file, ContentType="application/pdf")
            summary_file.upload_completed = True
            summary_file.save()
            logger.info(
                f"Uploaded Discharge Summary for {consultation.external_id}, file id: {summary_file.external_id}"
            )
    finally:
        clear_lock(str(consultation.external_id))

    return summary_file


@shared_task(
    autoretry_for=(ClientError,), retry_kwargs={"max_retries": 3}, expires=10 * 60
)
def generate_discharge_summary_task(consultation_ext_id: str, section_data: str):
    """
    Generate and Upload the Discharge Summary
    """
    logger.info(f"Generating Discharge Summary for {consultation_ext_id}")
    try:
        consultation = PatientConsultation.objects.get(external_id=consultation_ext_id)
    except PatientConsultation.DoesNotExist as e:
        raise CeleryTaskException(
            f"Consultation {consultation_ext_id} does not exist"
        ) from e

    summary_file = generate_and_upload_discharge_summary(consultation, section_data)
    if not summary_file:
        raise CeleryTaskException("Unable to generate discharge summary")

    return summary_file.external_id
