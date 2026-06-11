from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        VOLUNTEER = 'volunteer', 'Volunteer'
        PUBLIC = 'public', 'Public'

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.PUBLIC,
        help_text='Determines access level in the system.'
    )

    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN

    def is_volunteer(self) -> bool:
        return self.role == self.Roles.VOLUNTEER

# Create your models here.
