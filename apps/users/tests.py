from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the custom User model."""

    def setUp(self):
        """Set up test data for User model tests."""
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'phone': '+1234567890',
            'address': '123 Test Street, Test City'
        }

    def test_create_user_with_email(self):
        """Test creating a user with email as username field."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            password=self.user_data['password']
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))

    def test_create_user_with_all_fields(self):
        """Test creating a user with all optional fields."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.phone, '+1234567890')
        self.assertEqual(user.address, '123 Test Street, Test City')

    def test_user_str_method(self):
        """Test the string representation of User model."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')

    def test_email_unique_constraint(self):
        """Test that email field enforces uniqueness."""
        User.objects.create_user(**self.user_data)

        duplicate_user_data = self.user_data.copy()
        duplicate_user_data['username'] = 'anotheruser'

        with self.assertRaises(IntegrityError):
            User.objects.create_user(**duplicate_user_data)

    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email."""
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_required_fields_includes_username(self):
        """Test that username is in REQUIRED_FIELDS."""
        self.assertIn('username', User.REQUIRED_FIELDS)

    def test_phone_field_optional(self):
        """Test that phone field is optional."""
        user_data = self.user_data.copy()
        del user_data['phone']
        user = User.objects.create_user(**user_data)
        self.assertIsNone(user.phone)

    def test_address_field_optional(self):
        """Test that address field is optional."""
        user_data = self.user_data.copy()
        del user_data['address']
        user = User.objects.create_user(**user_data)
        self.assertIsNone(user.address)

    def test_phone_max_length(self):
        """Test phone field maximum length validation."""
        user_data = self.user_data.copy()
        user_data['phone'] = 'a' * 21  # Exceeds max_length of 20
        user = User(**user_data)
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_email_validation(self):
        """Test email field validation."""
        user_data = self.user_data.copy()
        user_data['email'] = 'invalid-email'
        user = User(**user_data)
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertEqual(superuser.email, 'admin@example.com')

    def test_user_authentication_with_email(self):
        """Test user authentication using email."""
        user = User.objects.create_user(**self.user_data)
        from django.contrib.auth import authenticate

        authenticated_user = authenticate(
            username='test@example.com',  # Using email for authentication
            password='testpass123'
        )
        self.assertEqual(authenticated_user, user)

    def test_blank_and_null_fields(self):
        """Test that phone and address fields accept blank and null values."""
        user_data = self.user_data.copy()
        user_data['phone'] = ''
        user_data['address'] = ''

        user = User.objects.create_user(**user_data)
        self.assertEqual(user.phone, '')
        self.assertEqual(user.address, '')

    def test_user_model_inheritance(self):
        """Test that User model inherits from AbstractUser."""
        from django.contrib.auth.models import AbstractUser
        self.assertTrue(issubclass(User, AbstractUser))

    def test_required_fields_validation(self):
        """Test validation of required fields."""
        # Test missing email
        with self.assertRaises((ValidationError, IntegrityError)):
            user = User(username='testuser', password='testpass123')
            user.full_clean()

        # Test missing username
        with self.assertRaises((ValidationError, IntegrityError)):
            user = User(email='test@example.com', password='testpass123')
            user.full_clean()