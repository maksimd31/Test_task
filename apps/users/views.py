from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    User registration API view.

    POST: Creates a new user account with JWT token generation.

    Permissions:
        - Open to all users (AllowAny)

    Features:
        - User account creation with validation
        - Automatic JWT token generation upon registration
        - Password confirmation validation
        - Email uniqueness validation
        - Returns user profile data and tokens

    Request Body:
        - username: Unique username (required)
        - email: Unique email address (required)
        - password: User password (required, validated)
        - password_confirm: Password confirmation (required)
        - phone: Optional phone number
        - address: Optional address

    Response:
        - user: User profile information
        - refresh: JWT refresh token
        - access: JWT access token
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Create user account with JWT tokens.

        Args:
            request: HTTP request with user registration data

        Returns:
            Response: User profile and JWT tokens
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Создаем JWT токены
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    User authentication API view.

    POST: Authenticates user and returns JWT tokens.

    Permissions:
        - Open to all users (AllowAny)

    Features:
        - Email-based authentication
        - JWT token generation
        - Secure password validation
        - Returns user profile and tokens on success

    Request Body:
        - email: User's email address
        - password: User's password

    Response:
        Success (200):
            - user: User profile information
            - refresh: JWT refresh token
            - access: JWT access token
        Error (401):
            - error: Authentication error message
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Authenticate user and generate JWT tokens.

        Args:
            request: HTTP request with login credentials

        Returns:
            Response: User profile and JWT tokens or error message
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Authenticate user using email as username
        user = authenticate(request, username=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile management API view.

    GET: Returns authenticated user's profile information.
    PUT/PATCH: Updates authenticated user's profile.

    Permissions:
        - Authentication required (IsAuthenticated)
        - Users can only access/modify their own profile

    Features:
        - Secure profile access (own profile only)
        - Profile information updates
        - JWT authentication required
        - Read and write operations

    Fields (readable/updatable):
        - username: User's username
        - email: User's email address
        - phone: User's phone number (optional)
        - address: User's address (optional)
        - date_joined: Account creation date (read-only)
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Return the authenticated user's profile.

        Returns:
            User: Current authenticated user instance
        """
        return self.request.user
