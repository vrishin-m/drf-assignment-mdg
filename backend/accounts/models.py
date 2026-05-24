# accounts/models.py

# Python imports
import uuid

# Django imports
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)

# ---------------------------
# Custom User Manager
# ---------------------------

class CustomUserManager(BaseUserManager):

    def create_user(self, email , password , **extra_fields):
        """
        create normal user
        """
        if not email:
            raise ValueError("Email field is required")
        if not password:
            raise ValueError("Password required")    #abhi OAuth ko nhi appy kr rha me 
        email = self.normalize_email(email)

        user = self.model(
            email= email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    

    def create_superuser(self, email , password , **extra_fields):
        """
        create admin user
        """
        
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        return self.create_user(email=email , password=password , **extra_fields)


# ---------------------------
# Custom User Model
# ---------------------------

class CustomUser(AbstractBaseUser, PermissionsMixin):

    # UUID primary key
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4,
        editable=False
    )

    # authentication field
    email = models.EmailField(   # automatically checks for @ 
        unique=True
    )

    # profile fields
    full_name = models.CharField(
        max_length=100
    )
    avatar_url = models.URLField(
        blank=True,
        null=True


    )
    bio = models.TextField(
        blank=True
    )

    # required auth fields
    is_active = models.BooleanField(
        default=True
    )
    is_staff = models.BooleanField(
        default=False
    )

    # timestamps
    created_at = models.DateTimeField(
        auto_now_add=True     #will remain same even if object is updated 
    )
    updated_at = models.DateTimeField(
        auto_now= True    
    )

    # manager
    objects = CustomUserManager()

    # tells Django login uses email
    USERNAME_FIELD = "email"

    # optional required fields
    REQUIRED_FIELDS = ["fullname" ]

  
    """
    This becomes very useful in places like:

    Django admin:

    Without __str__():

    Users
    --------------------------------
    CustomUser object(1)
    CustomUser object(2)
    CustomUser object(3)

    With __str__():

    Users
    --------------------------------
    krish@gmail.com
    john@gmail.com
    abc@gmail.com
    """
    def __str__(self):
        return self.email


# # ---------------------------
# # Membership Roles
# # ---------------------------
"""
here we are defining the exact choices so user do not have to manually type Designer with spelling errors and populate db with multiple string refering to same role """
class StudioRole(models.TextChoices):      

    STUDIO_ADMIN = "studio_admin", "Studio Admin"
    PROJECT_LEAD = "project_lead", "Project Lead"
    DESIGNER = "designer", "Designer"
    WRITER = "writer", "Writer"
    REVIEWER = "reviewer", "Reviewer"
    CLIENT_VIEWER = "client_viewer", "Client Viewer"


# ---------------------------
# Studio Membership
# ---------------------------

class StudioMembership(models.Model):

    id = models.UUIDField(
        primary_key=True , 
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(     #many to one relationship  one user can have many memberships 
        CustomUser,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    studio = models.ForeignKey(     # many to one , one studio has many memberships 
        "studios.Studio",
        on_delete=models.CASCADE,
        related_name="members"
    )
    role = models.CharField(
        choices=StudioRole.choices,
        max_length=30 
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "studio", "role"],
                name="unique_user_studio_role"
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.studio.name} - {self.role}"