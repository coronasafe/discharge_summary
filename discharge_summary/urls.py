from django.urls import path
from django.shortcuts import HttpResponse
from rest_framework.routers import DefaultRouter

from discharge_summary.viewsets.dischange_summary import AIDischargeSummaryViewset

def healthy(request):
    return HttpResponse("Hello from discharge_summary")


router = DefaultRouter()
router.register("ai_discharge_summary", AIDischargeSummaryViewset)

urlpatterns = [
    path("health", healthy),
] + router.urls
