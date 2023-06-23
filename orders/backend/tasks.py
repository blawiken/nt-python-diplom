from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from orders.celery import app
from .models import *


__all__ = [
    'new_user_registered',
    'send_email',
]

@app.task()
def new_user_registered(user_id):
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)
    msg = EmailMultiAlternatives(
        f'Token for {token.user.email}',
        token.key,
        settings.EMAIL_HOST_USER,
        [token.user.email]
    )
    msg.send()

@app.task()
def send_email(title, msg, to_email):
    msg = EmailMultiAlternatives(
        title,
        msg,
        settings.EMAIL_HOST_USER,
        [to_email]
    )
    msg.send()
