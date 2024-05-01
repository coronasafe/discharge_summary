from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from care.facility.api.serializers.patient_consultation import (
    PatientConsultationDischargeSerializer,
    PatientConsultationSerializer,
)
from discharge_summary.tasks.generate_discharage_summary import (
    generate_discharge_summary_task,
)
from dry_rest_permissions.generics import DRYPermissions
from care.facility.models.patient_consultation import PatientConsultation
from django.db.models import Prefetch
from care.users.models import Skill, User
from care.utils.cache.cache_allowed_facilities import get_accessible_facilities
from django.db.models.query_utils import Q
from care.facility.utils.reports.discharge_summary import set_lock
from rest_framework.response import Response


class AIDischargeSummaryViewset(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    lookup_field = "external_id"
    serializer_class = PatientConsultationDischargeSerializer
    permission_classes = (
        IsAuthenticated,
        DRYPermissions,
    )
    queryset = (
        PatientConsultation.objects.all().select_related("facility").order_by("-id")
    )

    def get_queryset(self):
        if self.serializer_class == PatientConsultationSerializer:
            self.queryset = self.queryset.prefetch_related(
                "assigned_to",
                Prefetch(
                    "assigned_to__skills",
                    queryset=Skill.objects.filter(userskill__deleted=False),
                ),
                "current_bed",
                "current_bed__bed",
                "current_bed__assets",
                "current_bed__assets__current_location",
            )
        if self.request.user.is_superuser:
            return self.queryset
        elif self.request.user.user_type >= User.TYPE_VALUE_MAP["StateLabAdmin"]:
            return self.queryset.filter(
                patient__facility__state=self.request.user.state
            )
        elif self.request.user.user_type >= User.TYPE_VALUE_MAP["DistrictLabAdmin"]:
            return self.queryset.filter(
                patient__facility__district=self.request.user.district
            )
        allowed_facilities = get_accessible_facilities(self.request.user)
        # A user should be able to see all the consultations of a patient if the patient is active in an accessible facility
        applied_filters = Q(
            Q(patient__is_active=True) & Q(patient__facility__id__in=allowed_facilities)
        )
        # A user should be able to see all consultations part of their home facility
        applied_filters |= Q(facility=self.request.user.home_facility)
        return self.queryset.filter(applied_filters)

    @extend_schema(tags=["consultation"])
    @action(detail=True, methods=["POST"])
    def discharge_patient(self, request, *args, **kwargs):
        consultation = self.get_object()
        serializer = self.get_serializer(consultation, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(current_bed=None)
        set_lock(consultation.external_id, 0)
        generate_discharge_summary_task.delay(
            consultation.external_id,
            request.data["section_data"],
        )  # type: ignore (The celery library is an "untyped" library)
        return Response(status=status.HTTP_200_OK)
