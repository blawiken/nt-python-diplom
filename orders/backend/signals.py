from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from yaml import safe_load

from .models import *

__all__ = [
    'new_user_registered_signal',
    'import_price',
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


def import_price(request_files, user_id):
    with open(request_files.get_file(), 'r') as f:
        file = safe_load(f)

    shop, _ = Shop.objects.get_or_create(user_id=user_id,
                                         defaults={'name': file['shop']})
    
    load_cat = [Category(id=category['id'],
                 name=category['name']) for category in file['categories']]
    Category.objects.bulk_create(load_cat)
    Product.objects.filter(shop_id=shop.id).delete()

    load_products = []
    product_id = {}
    load_product_parameters = []
    for item in file['goods']:
        load_products.append(Product(name=item['name'],
                                 category=item['category'],
                                 model=item['model'],
                                 external_id=item['id'],
                                 shop_id=shop.id,
                                 quantity=item['quantity'],
                                 price=item['price'],
                                 price_rrc=item['price_rrc']))
        product_id[item['id']] = {}

        for name, value in item['parameters'].items():
            parameter, _ = Parameter.objects.get_or_create(name=name)
            product_id[item['id']].update({parameter.id: value})
            load_product_parameters.append(ProductParameter(product_id=product_id[item['id']][parameter.id],
                                            parameter_id=parameter.id,
                                            value=value))
    Product.objects.bulk_create(load_products)
    ProductParameter.objects.bulk_create(load_product_parameters)

