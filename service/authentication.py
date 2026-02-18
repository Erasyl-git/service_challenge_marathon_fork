from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser


from types import SimpleNamespace

class JWTAuthentication(JWTAuthentication):
    
    def get_user(self, validated_token):
        if validated_token.get("token_type") != "access":
            raise exceptions.AuthenticationFailed("Invalid token")
        user = SimpleNamespace()
        user.id = validated_token["user_id"]
        user.is_authenticated = True
        return user



