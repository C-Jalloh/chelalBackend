from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils import timezone

User = get_user_model()

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer to allow login with email or username.
    Also records login activity.
    """
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        # Accept either username or email in the 'username' field
        credentials = {
            self.username_field: attrs.get('username'),
            'password': attrs.get('password')
        }
        user_obj = None
        # Try username
        try:
            user_obj = User.objects.get(username=credentials[self.username_field])
        except User.DoesNotExist:
            # Try email
            try:
                user_obj = User.objects.get(email__iexact=credentials[self.username_field])
            except User.DoesNotExist:
                pass
        if user_obj:
            credentials[self.username_field] = user_obj.username
        result = super().validate(credentials)
        # Record login activity if successful
        if user_obj and user_obj.is_active:
            from core.models import LoginActivity
            request = self.context.get('request')
            ip = None
            user_agent = ''
            if request:
                xff = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            LoginActivity.objects.create(
                user=user_obj,
                ip_address=ip,
                user_agent=user_agent,
                status='success',
                timestamp=timezone.now()
            )
        return result
