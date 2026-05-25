from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserSerializer,
    ChangePasswordSerializer
)
from .serializers import RegisterSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenRefreshView

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()

            return Response(
                {
                    "message": "User registered successfully",
                    "email": user.email,
                    "full_name": user.full_name,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class MeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(
            request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    def patch(self, request):

        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
class ChangePasswordView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():

            request.user.set_password(
                serializer.validated_data[
                    "new_password"
                ]
            )

            request.user.save()

            return Response(
                {
                    "message":
                    "Password changed successfully"
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self,request):

        refresh_token=request.data.get(
            "refresh"
        )

        if not refresh_token:

            return Response(
                {
                    "error":
                    "Refresh token required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            token=RefreshToken(
                refresh_token
            )

            token.blacklist()

            return Response(
                {
                    "message":
                    "Logged out successfully"
                },
                status=status.HTTP_200_OK
            )

        except Exception:

            return Response(
                {
                    "error":
                    "Invalid token"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
from django.contrib.auth import authenticate

class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email")
        password = request.data.get("password")

        # Validate required fields first
        if not email:

            return Response(
                {
                    "error": "Email is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not password:

            return Response(
                {
                    "error": "Password is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            request,
            email=email,
            password=password
        )

        if user is None:

            return Response(
                {
                    "error": "Invalid credentials"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            },
            status=status.HTTP_200_OK
        )