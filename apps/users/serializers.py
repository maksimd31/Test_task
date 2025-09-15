from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed

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
    email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all(), message="User with this email already exists")])

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'phone', 'address']

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
    Serializer for authenticating users via email and password.

    Validates:
        - Email (used as username in authentication)
        - Password
        - User existence and active status

    Returns:
        - user: Authenticated User instance
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Validate user credentials and authenticate.

        Args:
            attrs (dict): Dictionary containing 'email' and 'password'.

        Raises:
            serializers.ValidationError: If credentials are invalid.

        Returns:
            dict: Validated data including the authenticated user instance.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(username=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials")

        if not user.is_active:
            raise AuthenticationFailed("User account is disabled")

        attrs["user"] = user
        return attrs


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
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'address', 'date_joined']
        read_only_fields = ['id', 'date_joined']
