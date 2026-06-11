from django.db import models
from django.conf import settings
from persons.models import MissingPerson, FoundPerson


class Report(models.Model):
    REPORT_TYPE = (
        ('missing', 'Missing Person Report'),
        ('sighting', 'Sighting Report'),
        ('found', 'Found Person Report'),
    )

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE)
    missing_person = models.ForeignKey(
        MissingPerson, on_delete=models.CASCADE, null=True, blank=True
    )
    found_person = models.ForeignKey(
        FoundPerson, on_delete=models.CASCADE, null=True, blank=True
    )
    details = models.TextField(blank=True)
    photo = models.ImageField(upload_to='reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.get_report_type_display()} by {self.reporter or 'Anonymous'}"

# Create your models here.
