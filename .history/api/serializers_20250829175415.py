from rest_framework import serializers
from persons.models import MissingPerson, FoundPerson
from reports.models import Report


class MissingPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissingPerson
        fields = '__all__'


class FoundPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundPerson
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


