SYSTEM_PROMPT = """You are a healthcare AI tasked with generating a discharge summary for a patient.
Given the patient details provided below, generate a summary of the data.
Strictly output just a summary without any extra data."""

INITIAL_PROMPT = """Here is the patient data for the discharge summary:
{section}
{json_data}
"""

CONTINUED_PROMPT = """
The following is the discharge summary so far:
{summary_so_far}

With the above context, include the following information to the provided summary. Remember to strictly output just the summary without any extra data.
{section}
{json_data}
"""
