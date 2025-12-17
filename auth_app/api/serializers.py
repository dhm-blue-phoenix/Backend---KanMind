# Standard library
from __future__ import annotations
from typing import Any, Dict

# Django
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

# Django REST Framework
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


class UserRegistrationSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(write_only=True, required=True)
    repeated_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {'password': {'write_only': True, 'validators': [validate_password]}}

    def validate(self: ModelSerializer, data: Dict[str, Any]) -> Dict[str, Any]:
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({"repeated_password": "Password does not match"})

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})

        return data

    def create(self, validated_data: Dict[str, Any]) -> User:
        fullname: str = validated_data.pop('fullname')
        validated_data.pop('repeated_password')

        parts: list[str] = fullname.strip().split()
        first_name: str = parts[0]
        last_name: str = " ".join(parts[1:]) if len(parts) > 1 else ""

        user: User = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name,
        )
        return user