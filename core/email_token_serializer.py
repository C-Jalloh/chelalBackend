from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer to allow login with email or username.
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
        return super().validate(credentials)
