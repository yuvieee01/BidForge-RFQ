from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, role='buyer'):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(email, name, password, role='buyer')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        BUYER = 'buyer', 'Buyer'
        SUPPLIER = 'supplier', 'Supplier'

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.name} ({self.role})"
