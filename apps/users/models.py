from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Uses email as the primary authentication field instead of username.
    Adds optional contact information fields for enhanced user profiles.

    Authentication:
        - USERNAME_FIELD: email (unique identifier for login)
        - REQUIRED_FIELDS: username (still required for admin)

    Additional Fields:
        - phone: Optional phone number (max 20 characters)
        - address: Optional text address field

    Features:
        - Email-based authentication
        - Unique email constraint
        - Optional contact information
        - Backward compatibility with Django's user system

    Usage:
        User can authenticate using email and password.
        Username is still required but not used for authentication.
    """
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        """Return string representation of the user (email)."""
        return self.email