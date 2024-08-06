from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from users.validators import validate_username

USER = 'user'  # Role for Test takers
MODERATOR = 'moderator'  # Role for Test creators
ADMIN = 'admin'  # Role for admins

ROLES = (
    (USER, 'User'),
    (MODERATOR, 'Moderator'),
    (ADMIN, 'Admin'),
)


class User(AbstractUser):
    """User model."""

    username = models.CharField(
        'username',
        max_length=settings.MAX_USERNAME_LENGTH,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[validate_username],
    )
    email = models.EmailField(
        max_length=settings.MAX_EMAIL_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    bio = models.TextField(
        blank=True,
        null=True,
    )
    role = models.CharField(
        max_length=settings.MAX_ROLE_LENGTH,
        choices=ROLES,
        default=USER,
    )

    @property
    def is_admin_or_superuser(self):
        return self.role == ADMIN or self.is_staff or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    def __str__(self):
        return self.username
