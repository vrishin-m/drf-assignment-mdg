from rest_framework import serializers
from .models import CustomUser
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only= True
    )

    class Meta:
        model= CustomUser
        fields=[
            "email",
            "bio",
            "full_name",
            "password",
            "avatar_url"
        ]
    def validate_email(self,value):
        if CustomUser.objects.filter(
            email=value
        ).exists():
            raise serializers.ValidationError(
                "Email already exists"
            )
        return value 
    def create(self , validated_data):
        return CustomUser.objects.create_user(
            **validated_data
        )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model= CustomUser
        fields=[
            "id",
            "email",
            "full_name",
            "bio",
            "avatar_url",
            "created_at",
            "updated_at",
        ]
        read_onlu_fields=[   #PATCH req can not change these 
            "id",
            "email",
            "created_at",
            "updated_at"
        ]
class ChangePasswordSerializer(serializers.Serializer):
    old_password= serializers.CharField(
        write_only=True     #this ensures that server never sends password in any response 
    )
    new_password = serializers.CharField(
        write_only=True
    )
    confirm_password = serializers.CharField(
        write_only= True
    )
    def validate(self, data):
        user = self.context["request"].user
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {
                    "old_password" : "Old password is incorrect"
                }
            )
        
        if new_password != confirm_password :
            raise serializers.ValidationError(
                {
                    "confirm_password" : "Passwords did not match "
                }
            )
        if old_password == new_password:
            raise serializers.ValidationError(
            {"new_password": "New password cannot be same as old password"}
            )
        return data 
       