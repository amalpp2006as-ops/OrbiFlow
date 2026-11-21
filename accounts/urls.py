from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    OwnerRegisterView,
    CustomerRegisterView,
    CustomLoginView,
    ForgotPasswordView
)
from .views import (
    OwnerRegisterView,
    CustomerRegisterView,
    CustomLoginView,
    ForgotPasswordView,
    ChangePasswordView
)


urlpatterns = [

    # ==================================
    # REGISTRATION
    # ==================================

    path(
        'register/owner/',
        OwnerRegisterView.as_view(),
        name='owner-register'
    ),

    path(
        'register/customer/',
        CustomerRegisterView.as_view(),
        name='customer-register'
    ),


    # ==================================
    # JWT AUTHENTICATION
    # ==================================

    path(
        'login/',
        CustomLoginView.as_view(),
        name='login'
    ),

    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='token-refresh'
    ),


    # ==================================
    # FORGOT PASSWORD
    # ==================================

    path(
        'forgot-password/',
        ForgotPasswordView.as_view(),
        name='forgot-password'
    ),


    # ==================================
    # RESET PASSWORD
    # ==================================

    path(
        'reset-password/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),


    # ==================================
    # PASSWORD RESET COMPLETE
    # ==================================

    path(
        'reset-password-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path(
    'change-password/',
    ChangePasswordView.as_view(),
    name='change-password'
    ),

]