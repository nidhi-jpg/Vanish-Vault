from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MissingPersonViewSet, FoundPersonViewSet, ReportViewSet


router = DefaultRouter()
router.register('missing', MissingPersonViewSet, basename='api-missing')
router.register('found', FoundPersonViewSet, basename='api-found')
router.register('reports', ReportViewSet, basename='api-reports')


urlpatterns = [
    path('', include(router.urls)),
]


