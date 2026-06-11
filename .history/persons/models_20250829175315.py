from django.db import models


class MissingPerson(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    full_name = models.CharField(max_length=200)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    last_seen_location = models.CharField(max_length=255, blank=True)
    last_seen_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='missing/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.full_name


class FoundPerson(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    possible_name = models.CharField(max_length=200, blank=True)
    estimated_age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    found_location = models.CharField(max_length=255, blank=True)
    found_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='found/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.possible_name or f"Found at {self.found_location}"

# Create your models here.
