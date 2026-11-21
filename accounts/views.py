from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.response import Response
from .serializers import (
    OwnerRegisterSerializer,
    CustomerRegisterSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer
)
from .serializers import (
    OwnerRegisterSerializer,
    CustomerRegisterSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    ChangePasswordSerializer
)

# Business Owner Registration
class OwnerRegisterView(generics.CreateAPIView):
    serializer_class = OwnerRegisterSerializer
    permission_classes = [AllowAny]


# Customer Registration
class CustomerRegisterView(generics.CreateAPIView):
    serializer_class = CustomerRegisterSerializer
    permission_classes = [AllowAny]


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# Forgot Password
class ForgotPasswordView(generics.GenericAPIView):

    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'If an account exists with this email, a password reset link has been sent.'
        })

# ==================================
# CHANGE PASSWORD
# ==================================

class ChangePasswordView(generics.GenericAPIView):

    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Password changed successfully."
        })
