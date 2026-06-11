from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("report_type", "reporter", "created_at")
    list_filter = ("report_type", "created_at")
    search_fields = ("details",)

# Register your models here.
