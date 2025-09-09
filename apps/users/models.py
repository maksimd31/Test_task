from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom user model.

      Extends Django's AbstractUser to use email as the unique identifier
      for authentication. Adds optional `phone` and `address` fields.
      `USERNAME_FIELD` is set to 'email' and 'username' remains a required field.
    """
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email