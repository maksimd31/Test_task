from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with validation.

    Handles new user account creation with comprehensive validation
    including password confirmation, email uniqueness, and Django's
    built-in password validation.

    Fields:
        - username: Unique username (required)
        - email: Unique email address (required)
        - password: User password (write-only, validated)
        - password_confirm: Password confirmation (write-only)
        - phone: Optional phone number
        - address: Optional address

    Validation:
        - Email uniqueness check
        - Password confirmation matching
        - Django password validation (strength, common passwords, etc.)

    Features:
        - Secure password handling (write-only)
        - Automatic password hashing
        - Comprehensive validation
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'phone', 'address']

    def validate_email(self, value):
        """
        Validate email uniqueness.

        Args:
            value (str): Email address to validate

        Returns:
            str: Validated email address

        Raises:
            ValidationError: If email already exists
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def validate(self, data):
        """
        Validate password confirmation.

        Args:
            data (dict): User registration data

        Returns:
            dict: Validated user data

        Raises:
            ValidationError: If passwords don't match
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        """
        Create user with hashed password.

        Args:
            validated_data (dict): Validated user data

        Returns:
            User: Created user instance
        """
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login authentication.

    Simple serializer for handling login credentials.
    Used for validating email and password format before authentication.

    Fields:
        - email: User's email address (used as username)
        - password: User's password

    Features:
        - Email format validation
        - Password field (non-empty validation)
        - No database queries (validation only)
    """
    email = serializers.EmailField()
    password = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.

    Used for displaying and updating user profile data.
    Excludes sensitive information and provides read-only fields
    for certain attributes.

    Fields:
        - id: User primary key (read-only)
        - username: User's username
        - email: User's email address
        - phone: User's phone number (optional)
        - address: User's address (optional)
        - date_joined: Account creation timestamp (read-only)

    Features:
        - Safe profile information display
        - Read-only sensitive fields
        - Optional contact information
        - No password exposure
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'address', 'date_joined']
        read_only_fields = ['id', 'date_joined']
