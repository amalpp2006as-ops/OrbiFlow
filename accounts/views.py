from django.shortcuts import render, redirect
from django.contrib.auth import login
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response

from .serializers import (
    OwnerRegisterSerializer,
    CustomerRegisterSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    ChangePasswordSerializer
)


# ==================================
# BUSINESS OWNER REGISTRATION
# ==================================

class OwnerRegisterView(generics.CreateAPIView):
    serializer_class = OwnerRegisterSerializer
    permission_classes = [AllowAny]


# ==================================
# CUSTOMER REGISTRATION
# ==================================

class CustomerRegisterView(generics.CreateAPIView):
    serializer_class = CustomerRegisterSerializer
    permission_classes = [AllowAny]


# ==================================
# JWT LOGIN
# ==================================

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        login(request._request, serializer.user)

        return Response(serializer.validated_data)


# ==================================
# FORGOT PASSWORD
# ==================================

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
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Password changed successfully."
        })


# ==================================
# LOGIN PAGE
# ==================================

def login_page(request):
    return render(request, 'accounts/login.html')


# ==================================
# REGISTER PAGE
# ==================================

def register_page(request):
    return render(request, 'accounts/register.html')


# ==================================
# FORGOT PASSWORD PAGE
# ==================================

def forgot_password_page(request):
    return render(request, 'accounts/forgot_password.html')


# ==================================
# ROLE-BASED DASHBOARD REDIRECTION
# ==================================

def dashboard_redirect(request):

    if not request.user.is_authenticated:
        return redirect('login-page')

    if request.user.role == 'BUSINESS_OWNER':
        return redirect('owner-dashboard')

    elif request.user.role == 'MANAGER':
        return redirect('manager-dashboard')

    elif request.user.role == 'EMPLOYEE':
        return redirect('employee-dashboard')

    elif request.user.role == 'CUSTOMER':
        return redirect('customer-dashboard')

    return redirect('login-page')