import re

from django.core.exceptions import ValidationError


def validate_username(username):
    """Checks username for validity."""

    pattern = re.compile(r'^[\w.@+-]+\Z')

    if username.lower() == "me":
        raise ValidationError(
            message="Cannot use 'me' as username. "
        )
    if not pattern.findall(username):
        raise ValidationError(
            "Username contains invalid characters."
        )
