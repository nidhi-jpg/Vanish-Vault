from rest_framework import viewsets, permissions
from persons.models import MissingPerson, FoundPerson
from reports.models import Report
from .serializers import MissingPersonSerializer, FoundPersonSerializer, ReportSerializer


class MissingPersonViewSet(viewsets.ModelViewSet):
    queryset = MissingPerson.objects.all().order_by('-created_at')
    serializer_class = MissingPersonSerializer
    permission_classes = [permissions.AllowAny]


class FoundPersonViewSet(viewsets.ModelViewSet):
    queryset = FoundPerson.objects.all().order_by('-created_at')
    serializer_class = FoundPersonSerializer
    permission_classes = [permissions.AllowAny]


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().order_by('-created_at')
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# Create your views here.
