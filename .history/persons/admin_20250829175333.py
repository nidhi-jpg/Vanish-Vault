from django.contrib import admin
from .models import MissingPerson, FoundPerson


@admin.register(MissingPerson)
class MissingPersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "age", "gender", "last_seen_location", "last_seen_date")
    search_fields = ("full_name", "last_seen_location")
    list_filter = ("gender", "last_seen_date")


@admin.register(FoundPerson)
class FoundPersonAdmin(admin.ModelAdmin):
    list_display = ("possible_name", "estimated_age", "gender", "found_location", "found_date")
    search_fields = ("possible_name", "found_location")
    list_filter = ("gender", "found_date")

# Register your models here.
