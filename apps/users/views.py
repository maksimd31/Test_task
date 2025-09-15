from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
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
    permission_classes = [permissions.AllowAny]

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
    API endpoint for user authentication with JWT.

    Methods:
        POST:
            - Authenticates a user by email and password
            - Generates JSON Web Tokens (refresh and access)
            - Returns user profile and tokens on success

    Permissions:
        - AllowAny (open endpoint, no authentication required)

    Request Body:
        {
            "email": "user@example.com",
            "password": "secure_password123"
        }

    Responses:
        200 OK:
            {
                "user": { ...profile... },
                "refresh": "<refresh_token>",
                "access": "<access_token>"
            }
        400 Bad Request:
            {
                "error": "Invalid email or password"
            }
        403 Forbidden:
            {
                "error": "User account is disabled"
            }
    """
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for user login.

        Steps:
            1. Deserialize and validate incoming credentials
            2. Authenticate user
            3. Issue JWT refresh + access tokens
            4. Return serialized user profile and tokens

        Args:
            request (Request): HTTP request containing login credentials.

        Returns:
            Response: JSON with tokens and user data, or error message.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )

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
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Return the authenticated user's profile.

        Returns:
            User: Current authenticated user instance
        """
        return self.request.user
