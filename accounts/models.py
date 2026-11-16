from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower

username_validator = RegexValidator(r'^[A-Za-z0-9_.+-]+$', 'Use letters, numbers, dots, underscores, + or -. No @ or spaces.')
phone_validator = RegexValidator(r'^\+?[0-9][0-9 ()-]{5,23}$', 'Enter a valid contact number (6–24 characters; digits, spaces, +, parentheses or hyphens).')

class FoodLinkUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields['role'] = 'ADMIN'
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DONOR = 'DONOR', 'Donor'
        RECIPIENT = 'RECIPIENT', 'Recipient'
    username = models.CharField(max_length=150, unique=True, validators=[username_validator])
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=24, validators=[phone_validator])
    location = models.CharField(max_length=200)
    role = models.CharField(max_length=10, choices=Role.choices, null=True, blank=True, default=None)
    objects = FoodLinkUserManager()
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'contact_number', 'location']
    class Meta:
        constraints = [models.UniqueConstraint(Lower('username'), name='unique_username_ci'),
                       models.UniqueConstraint(Lower('email'), name='unique_email_ci'),
                       models.CheckConstraint(condition=models.Q(role__in=['ADMIN', 'DONOR', 'RECIPIENT']) | models.Q(role__isnull=True), name='valid_role')]
    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()
