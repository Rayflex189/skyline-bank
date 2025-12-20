from django_use_email_as_username.models import BaseUser, BaseUserManager
from django.db import models

class User(BaseUser):
    is_email_verified = models.BooleanField(default=False)

    objects = BaseUserManager()

    def __str__(self):
        return self.email
