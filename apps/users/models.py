from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """User entity with an optional phone contact number.

    Fields Added:
        phone: Optional raw phone string (may include country code). Not validated
               at the model layer to keep the entity simple and focused.
    """
    phone = models.CharField(max_length=20, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        """
        Returns the string representation of the user.

        Returns:
            str: User's email address.
        """
        return self.email

