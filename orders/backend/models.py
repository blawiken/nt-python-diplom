from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django_rest_passwordreset.tokens import get_token_generator


__all__ = [
    'User',
    'Contact',
    'ConfirmEmailToken',
    'Shop',
    'Category',
    'Product',
    'ProductInfo',
    'Parameter',
    'ProductParameter',
    'Order',
    'OrderItem',
]

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)

STATUS_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
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


class Shop(models.Model):
    name = models.CharField(verbose_name='Название',
                            max_length=50)
    url = models.URLField(verbose_name='URL',
                          blank=True, null=True)
    file_name = models.FileField(verbose_name='Прайс',
                                 blank=True, null=True,
                                 storage=FileSystemStorage(settings.STORAGE))
    user = models.OneToOneField(User, verbose_name='Владелец',
                                blank=True, null=True)
    state = models.BooleanField(verbose_name='Статус',
                                default=True)
    
    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('-id',)

    def __str__(self):
        return f'{self.name} - {self.user}'


class Category(models.Model):
    name = models.CharField(verbose_name='Название',
                            max_length=50)
    shops = models.ManyToManyField(Shop, verbose_name='Магазины',
                                   related_name='categories',
                                   blank=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('-id',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(verbose_name='Название',
                            max_length=50)
    category = models.ForeignKey(Category, verbose_name='Категория',
                                 related_name='products',
                                 blank=True,
                                 on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Продукты"
        ordering = ('-id',)

    def __str__(self):
        return f'{self.category} - {self.name}'
    

class ProductInfo(models.Model):
    model = models.CharField(verbose_name='Модель',
                             max_length=50)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена')
    product = models.ForeignKey(Product, verbose_name='Продукт',
                                related_name='product_infos',
                                blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин',
                             related_name='product_infos',
                             blank=True,
                             on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Список информации о продуктах'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'],
                                    name='unique_product_info')]

    def __str__(self):
        return f'{self.shop.name} - {self.product.name}'
    

class Parameter(models.Model):
    name = models.CharField(verbose_name='Название',
                            max_length=50)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Параметры"
        ordering = ('-id',)

    def __str__(self):
        return self.name
    

class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте',
                                     blank=True,
                                     related_name='product_parameters',
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр',
                                  related_name='product_parameters',
                                  blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение',
                             max_length=50)

    class Meta:
        verbose_name = 'Параметр продукта'
        verbose_name_plural = 'Параметры продуктов'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'],
                                    name='unique_product_parameter')]

    def __str__(self):
        return f'{self.product_info.model} - {self.parameter.name}'
    

class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='orders',
                             blank=True,
                             on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, verbose_name='Контакт',
                                related_name='Контакт',
                                blank=True, null=True,
                                on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус',
                              max_length=20,
                              choices=STATUS_CHOICES)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Заказы"
        ordering = ('-dt',)

    def __str__(self):
        return f'{self.user} - {self.dt}'
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ',
                              related_name='ordered_items',
                              blank=True,
                              on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте',
                                     related_name='ordered_items',
                                     blank=True,
                                     on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество',
                                           default=1)
    price = models.PositiveIntegerField(verbose_name='Цена',
                                        default=0)
    total_amount = models.PositiveIntegerField(verbose_name='Общая стоимость',
                                               default=0)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = "Позиции заказов"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'],
                                    name='unique_order_item'),]

    def __str__(self):
        return f'''Заказ: {self.order} | {self.product_info.model}.
        Кол-во: {self.quantity}.
        Сумма: {self.total_amount}'''

    def save(self, *args, **kwargs):
        self.total_amount = self.price * self.quantity
        super(OrderItem, self).save(*args, **kwargs)
