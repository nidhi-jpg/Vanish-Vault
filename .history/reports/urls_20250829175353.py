from django.urls import path
from . import views


urlpatterns = [
    path('report-missing/', views.report_missing, name='report_missing'),
]


