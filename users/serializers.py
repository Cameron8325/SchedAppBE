from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from django.db import transaction

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'tokens']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']

class RegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        # Check if a user with this email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        # Ensure that the password and password_confirm match
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        phone_number = validated_data.pop('phone_number')

        # Create a new User instance
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # Ensure the Profile exists and update it
        profile, created = Profile.objects.get_or_create(user=user)
        profile.phone_number = phone_number
        profile.is_verified = False
        profile.save()

        return user
