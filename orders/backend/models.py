from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django_rest_passwordreset.tokens import get_token_generator


USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    objects = UserManager()
    email = models.EmailField(verbose_name='Email',
                              max_length=50,
                              unique=True)
    company = models.CharField(verbose_name='Компания',
                               max_length=50,
                               blank=True, null=True)
    position = models.CharField(verbose_name='Должность',
                                max_length=50,
                                blank=True, null=True)
    type = models.CharField(verbose_name='Тип',
                            choices=USER_TYPE_CHOICES,
                            max_length=10,
                            default='buyer')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-id',)

    def __str__(self):
        return self.username


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='contacts',
                             blank=True)
    city = models.EmailField(verbose_name='Город',
                              max_length=50)
    street = models.CharField(verbose_name='Улица',
                               max_length=50,
                               blank=True)
    house = models.CharField(verbose_name='Дом',
                                max_length=50,
                                blank=True)
    apartment = models.CharField(verbose_name='Квартира',
                                max_length=50,
                                blank=True)
    phone  = models.CharField(verbose_name='Телефон',
                                max_length=50)
    
    class Meta:
        verbose_name = 'Контакт пользователя'
        verbose_name_plural = 'Контакты пользователей'
        ordering = ('user',)

    def __str__(self):
        return f'{self.city} {self.street} - {self.phone}'
    

class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()
    
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='confirm_email_tokens',
                             on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Время создания')
    key = models.CharField(verbose_name='Токен',
                           max_length=64,
                           db_index=True,
                           unique=True)
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)
    
    def  __str__(self):
        return f'Token for {self.user}'
