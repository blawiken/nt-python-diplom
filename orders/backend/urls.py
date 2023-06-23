from django.urls import path, include
from rest_framework import routers
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from .views import *


router = routers.SimpleRouter()
router.register(r'categories', CategoryView, basename='categories')
router.register(r'products', ProductInfoView, basename='products')
router.register(r'shops', ShopView, basename='shops')
router.register(r'shop/update', PartnerUpdateView, basename='shop-update')

urlpatterns = [
    path('user/register/', RegisterAccount.as_view(), name='user-register'),
    path('user/register/confirm/', ConfirmAccount.as_view(), name='user-register-confirm'),
    path('user/login/', LoginAccount.as_view(), name='user-login'),
    path('user/details/', AccountDetails.as_view(), name='user-details'),
    path('user/contact/', Contact.as_view(), name='user-contact'),
    path('user/password_reset/', reset_password_request_token, name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
    
    path('basket/', Basket.as_view(), name='basket'),

    path('shop/state/', PartnerState.as_view(), name='shop-state'),

    path('', include(router.urls)),
] + router.urls
