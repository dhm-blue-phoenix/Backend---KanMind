# Django
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpRequest

# Django REST Framework
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework import status

# Local imports
from .serializers import UserRegistrationSerializer


class UserRegistrationView(APIView):
    """
    Handles user registration.
    POST: Creates a new user and returns token/user data.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_save = serializer.save()

        token, created = Token.objects.get_or_create(user=user_save)

        return Response({
            'token': token.key,
            'fullname': user_save.get_full_name(),
            'email': user_save.email,
            'user_id': user_save.id,
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """
    Handles user login.
    POST: Authenticates user and returns token/user data.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"message": "Email or password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'token': token.key,
                    'fullname': user.get_full_name(),
                    'email': user.email,
                    'user_id': user.id,
                }, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)