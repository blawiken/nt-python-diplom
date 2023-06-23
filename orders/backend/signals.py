from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from .models import *


__all__ = [
    'new_user_registered_signal',
    'send_email',
]

def new_user_registered_signal(user_id):
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)
    msg = EmailMultiAlternatives(
        f'Token for {token.user.email}',
        token.key,
        settings.EMAIL_HOST_USER,
        [token.user.email]
    )
    msg.send()

def send_email(title, msg, to_email):
    msg = EmailMultiAlternatives(
        title,
        msg,
        settings.EMAIL_HOST_USER,
        [to_email]
    )
    msg.send()
