from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.db.models.query import Prefetch
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from rest_framework import fields
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.throttling import AnonRateThrottle

from distutils.util import strtobool
from yaml import safe_load
from ujson import loads

from .models import *
from .serializers import *
from .tasks import *


__all__ = [
    'MainPage',
    'RegisterAccount',
    'ConfirmAccount',
    'LoginAccount',
    'AccountDetails',
    'Contact',
    'CategoryView',
    'ShopView',
    'PartnerUpdateView',
    'PartnerState',
    'PartnerOrders',
    'ProductInfoView',
    'Basket',
    'Orders',
]

MSG_NO_REQUIRED_FIELDS = 'No required fields'

class MainPage(APIView):
    '''
    Навигация 
    '''
    throttle_classes = [AnonRateThrottle]

    def get(self, request):
        data = {
            'user-register': 'http://127.0.0.1:8000/api/user/register/',
            'user-register-confirm': 'http://127.0.0.1:8000/api/user/register/confirm/',
            'user-login': 'http://127.0.0.1:8000/api/user/login/',
            'user-details': 'http://127.0.0.1:8000/api/user/details/',
            'user-contacts': 'http://127.0.0.1:8000/api/user/contacts/',
            'user-password-reset': 'http://127.0.0.1:8000/api/user/password_reset/',
            'user-password-reset-confirm': 'http://127.0.0.1:8000/api/user/password_reset/confirm',
            'basket': 'http://127.0.0.1:8000/api/basket/',
            'orders': 'http://127.0.0.1:8000/api/orders/',
            'categories': 'http://127.0.0.1:8000/api/categories/',
            'products': 'http://127.0.0.1:8000/api/products/',
            'shops': 'http://127.0.0.1:8000/api/shops/',
            'shop-update-price': 'http://127.0.0.1:8000/api/shop/update/',
            'shop-state': 'http://127.0.0.1:8000/api/shop/state/',
            'shop-orders': 'http://127.0.0.1:8000/api/shop/orders/',
            'api-swagger': 'http://127.0.0.1:8000/api/swagger/',
            'api-redoc': 'http://127.0.0.1:8000/api/redoc/',
        }
        return Response(data)


class RegisterAccount(APIView):
    '''
    Регистрация пользователя
    '''
    @extend_schema(request=UserSerializer)
    def post(self, request):
        '''post method registration'''
        if not {'email', 'password', 'username'}.issubset(request.data):
            return Response({'Error': MSG_NO_REQUIRED_FIELDS})
        
        try:
            validate_password(request.data['password'])
        except Exception as error:
            return Response({'Error': list(error)})
        else:
            request.data.update({})
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                user.save()
                new_user_registered(user.id)
                return Response(user_serializer.data)
            
            else:
                return Response({'Error': user_serializer.errors})


class ConfirmAccount(APIView):
    '''
    Подтверждение почты
    '''
    @extend_schema(request=inline_serializer('user-confirm',{
        'email': fields.EmailField(),
        'token': fields.CharField(),
    }))
    def post(self, request):
        if not {'email', 'token'}.issubset(request.data):
            return Response({'Error': MSG_NO_REQUIRED_FIELDS})
        
        token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                 key=request.data['token']).first()
        if token:
            token.user.is_active = True
            token.user.save()
            token.delete()
            return Response({'OK': True})
        else:
            return Response({'Error': 'Invalid email or token'})


class LoginAccount(APIView):
    '''
    Авторизация пользователя
    '''
    @extend_schema(request=inline_serializer('user-login',{
        'email': fields.EmailField(),
        'password': fields.CharField(),
    }))
    def post(self, request):
        if not {'email', 'password'}.issubset(request.data):
            return Response({'Error': MSG_NO_REQUIRED_FIELDS})

        user = authenticate(request, username=request.data['email'],
                            password=request.data['password'])
        if user is not None:
            if user.is_active:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({'OK': token.key})
        return Response({'Error': 'Invalid request'})
    

class AccountDetails(APIView):
    '''
    Информация о пользователе
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(request=UserSerializer)
    def post(self, request):
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return Response({'Error': list(error)})
            else:
                request.user.set_password(request.data['password'])
        
        user_serializer = UserSerializer(request.user, data=request.data,
                                         partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response(user_serializer.data)
        return Response({'Error': user_serializer.errors})


class Contact(APIView):
    '''
    Контакты пользователя
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ContactSerializer(request.user.contacts.all(), many=True)
        return Response(serializer.data)

    @extend_schema(request=ContactSerializer)
    def post(self, request):
        '''get contacts'''
        if not {'city', 'phone'}.issubset(request.data):
            return Response({'Error': MSG_NO_REQUIRED_FIELDS})
        
        mutable = request.POST._mutable
        request.POST._mutable = True
        request.POST._mutable = mutable
        request.data.update({'user': request.user.id})
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'Error': serializer.errors})
    
    def delete(self, request):
        '''remove contacts'''
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return Response({'Deleted count': deleted_count})
        return Response({'Error': MSG_NO_REQUIRED_FIELDS})

    def put(self, request):
        '''edit contacts'''
        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'],
                                                 user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(contact,
                                                   data=request.data,
                                                   partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                    return Response({'Error': serializer.errors})
        return Response({'Error': MSG_NO_REQUIRED_FIELDS})


class CategoryView(ModelViewSet):
    '''
    Список категорий
    '''
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    ordering = ('name',)
    http_method_names = ('get',)


class ShopView(ModelViewSet):
    '''
    Список магазинов
    '''
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    ordering = ('name',)
    http_method_names = ('get',)


class PartnerUpdateView(ModelViewSet):
    '''
    Обновление прайса магазина
    '''
    queryset = Shop.objects.none()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        if request.user.type != 'shop':
            return Response({'Error': 'Only for shops'})

        file = request.data.get('file_name')
        if file:
            try:
                data = safe_load(file)
            except Exception as error:
                return Response({'Error': str(error)})

            shop, _ = Shop.objects.get_or_create(user_id=request.user.id,
                                                 defaults={'name': data['shop']})

            for category in data['categories']:
                new_cat, __ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                new_cat.shops.add(shop.id)
                new_cat.save()

            ProductInfo.objects.filter(shop_id=shop.id).all().delete()
            for item in data['goods']:
                product, _ = Product.objects.get_or_create(name=item['name'],
                                                           category_id=item['category'])
                
                product_info = ProductInfo.objects.create(product_id=product.id,
                                                          external_id=item['id'],
                                                          model=item['model'],
                                                          price=item['price'],
                                                          price_rrc=item['price_rrc'],
                                                          quantity=item['quantity'],
                                                          shop_id=shop.id)
                
                for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)
            return Response(data)
        return Response({'Error': 'Invalid file'})


class PartnerState(APIView):
    '''
    Изменение состояния магазина
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        '''get state'''
        if request.user.type != 'shop':
            return Response({'Error': 'Only for shops'})
        
        return Response(ShopSerializer(request.user.shop).data)
    
    @extend_schema(request=inline_serializer('shop-state',{
        'state': fields.CharField(),
    }))
    def post(self, request):
        '''edit state'''
        if request.user.type != 'shop':
            return Response({'Error': 'Only for shops'})
        
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(
                    user_id=request.user.id
                ).update(state=strtobool(state))
                return Response(ShopSerializer(request.user.shop).data)
            
            except ValueError as error:
                return Response({'Error': str(error)})
        return Response({'Error': MSG_NO_REQUIRED_FIELDS})
    

class PartnerOrders(APIView):
    ''''
    Заказы магазина
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.type != 'shop':
            return Response({'Error': 'Only for shops'})
        
        qureyset = OrderItem.objects.filter(product_info__shop__user_id=request.user.id)
        pr = Prefetch('ordered_items', qureyset)
        order = Order.objects.filter(user_id=request.user.id).exclude(status='basket').prefetch_related(
            pr).select_related('contact').annotate(
            total_sum=Sum('ordered_items__total_amount'),
            total_quantity=Sum('ordered_items__quantity'))
        
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class ProductInfoView(ReadOnlyModelViewSet):
    '''
    Поиск товаров
    '''
    serializer_class = ProductInfoSerializer

    def get_queryset(self):
        query = Q(shop__state=True)
        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        
        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()
        
        return queryset
    

class Basket(APIView):
    '''
    Корзина
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        '''get basket'''
        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)
    
    @extend_schema(request=inline_serializer('basket-post',{
        'items': fields.ListField(),
    }))
    def post(self, request):
        '''add in basket'''
        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = loads(items_sting)
            except:
                return Response({'Error': 'Invalid format request'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id,
                                                        state='basket')
                objects_created = 0

                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemCreateSerializer(data=order_item)
                    
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return Response({'Error': str(error)})
                        else:
                            objects_created += 1
                    return Response({'Error': serializer.errors})
        return Response({'Error': MSG_NO_REQUIRED_FIELDS})

    def delete(self, request):
        '''remove from basket'''
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id,
                                                    status='basket')
            query = Q()
            objects_deleted = False

            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True
            
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return Response({'Deleted count': deleted_count})
        return Response({'Error': MSG_NO_REQUIRED_FIELDS})
    
    def put(self, request):
        '''edit item in basket'''
        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = loads(items_sting)
            except:
                return Response({'Error': 'Invalid format request'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id,
                                                        status='basket')
                object_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        object_updated += OrderItem.objects.filter(
                            order_id=basket.id, id=order_item['id']).update(quantity=order_item['quantity'])
                return Response({'Objects updated:': object_updated})
        return Response({'Error': MSG_NO_REQUIRED_FIELDS})


class Orders(APIView):
    '''
    Заказ
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        '''get order status'''
        order = Order.objects.filter(
            user_id=request.user.id).exclude(status='basket').select_related(
            'contact').prefetch_related('ordered_items').annotate(
            total_quantity=Sum('ordered_items__quantity'),
            total_sum=Sum('ordered_items__total_amount')).distinct()
        seriazlier = OrderSerializer(order, many=True)
        return Response(seriazlier.data)
    
    @extend_schema(request=inline_serializer('basket-post',{
        'id': fields.CharField(),
        'contact': fields.CharField(),
    }))
    def post(self, request):
        '''change order status'''
        if request.data['id'].isdigit():
            try:
                is_updated = Order.objects.filter(
                    id=request.data['id'], user_id=request.user.id).update(
                    contact_id=request.data['contact'], status='new')
            except:
                return Response({'Error': 'Invalid format request'})
            else:

                if is_updated:
                    send_email(
                        'Update order status',
                        'Order is formed',
                        request.user.email
                    )
                    return Response({'OK': True})

        return Response({'Error': MSG_NO_REQUIRED_FIELDS})
