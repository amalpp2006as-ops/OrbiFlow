from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from organization.models import Company
from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework.exceptions import AuthenticationFailed


User = get_user_model()


# ==========================================
# BUSINESS OWNER REGISTRATION
# ==========================================

class OwnerRegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    company_name = serializers.CharField(max_length=200, write_only=True)
    company_phone = serializers.CharField(max_length=15, write_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'confirm_password',
            'first_name',
            'last_name',
            'phone',
            'company_name',
            'company_phone',
            'profile_picture',
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):

        company_name = validated_data.pop('company_name')
        company_phone = validated_data.pop('company_phone')
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')

        user = User(**validated_data)
        user.role = 'BUSINESS_OWNER'
        user.set_password(password)
        user.save()

        company = Company.objects.create(
            name=company_name,
            email=user.email,
            phone=company_phone,
            created_by=user
        )

        user.company = company
        user.save(update_fields=['company'])

        return user


# ==========================================
# CUSTOMER REGISTRATION
# ==========================================

class CustomerRegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'confirm_password',
            'first_name',
            'last_name',
            'phone',
            'profile_picture',
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):

        password = validated_data.pop('password')
        validated_data.pop('confirm_password')

        user = User(**validated_data)
        user.role = 'CUSTOMER'
        user.set_password(password)
        user.save()

        return user


# ==========================================
# JWT LOGIN
# ==========================================
# ==========================================
# JWT LOGIN
# ==========================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):

        token = super().get_token(user)

        token['role'] = user.role
        token['email'] = user.email

        return token

    def validate(self, attrs):

        identifier = attrs.get('username')
        password = attrs.get('password')

        # Find account using username OR email
        users = User.objects.filter(
            Q(username__iexact=identifier) |
            Q(email__iexact=identifier)
        ).distinct()

        matching_users = list(users[:2])

        # Reject if no account or multiple accounts match
        if len(matching_users) != 1:
            raise AuthenticationFailed(
                'Invalid username/email or password.'
            )

        account = matching_users[0]

        # Authenticate using the actual username
        user = authenticate(
            request=self.context.get('request'),
            username=account.username,
            password=password
        )

        if user is None:
            raise AuthenticationFailed(
                'Invalid username/email or password.'
            )

        if not user.is_active:
            raise AuthenticationFailed(
                'This account is inactive.'
            )

        self.user = user

        # Generate JWT tokens
        refresh = self.get_token(user)

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'company': (
                user.company.name if user.company else None
            )
        }

        return data


# ==========================================
# FORGOT PASSWORD
# ==========================================

class ForgotPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def save(self):

        email = self.validated_data['email']

        user = User.objects.filter(
            email__iexact=email,
            is_active=True
        ).first()

        if user:

            # Generate UID
            uid = urlsafe_base64_encode(
                force_bytes(user.pk)
            )

            # Generate secure token
            token = default_token_generator.make_token(user)

            # Generate password reset URL
            reset_path = reverse(
                'password_reset_confirm',
                kwargs={
                    'uidb64': uid,
                    'token': token
                }
            )

            request = self.context.get('request')

            reset_link = request.build_absolute_uri(reset_path)

            # Send password reset email
            send_mail(
                subject="OrbiFlow - Password Reset",

                message=(
                    f"Hello {user.first_name or user.username},\n\n"
                    "You requested a password reset for your OrbiFlow account.\n\n"
                    f"Click the link below to reset your password:\n\n"
                    f"{reset_link}\n\n"
                    "If you did not request this, ignore this email."
                ),

                from_email=settings.DEFAULT_FROM_EMAIL,

                recipient_list=[user.email],

                fail_silently=False,
            )

# ==========================================
# CHANGE PASSWORD
# ==========================================

class ChangePasswordSerializer(serializers.Serializer):

    current_password = serializers.CharField(
        write_only=True
    )

    new_password = serializers.CharField(
        write_only=True
    )

    confirm_password = serializers.CharField(
        write_only=True
    )

    def validate_current_password(self, value):

        user = self.context['request'].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Your current password is incorrect."
            )

        return value

    def validate_new_password(self, value):

        user = self.context['request'].user

        validate_password(value, user=user)

        return value

    def validate(self, attrs):

        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'New passwords do not match.'
            })

        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password.'
            })

        return attrs

    def save(self):

        user = self.context['request'].user

        user.set_password(
            self.validated_data['new_password']
        )

        user.save(update_fields=['password'])

        return user