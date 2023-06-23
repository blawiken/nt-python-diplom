import pytest
from rest_framework.test import APIClient
from .models import User


@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def admin():
    return User.objects.create_user(email='admin@admin.admin', password='admin')

@pytest.fixture
def user_shop():
    return User.objects.create_user(
        email='df33@dsa.kz',
        password='sd43fdsf',
        username='user_test',
        type='shop'
    )

@pytest.mark.django_db
def user_login(client, user):
    response = client.post(
        f'user/login/',
        data={
            'email': 'df33@dsa.kz',
            'password': 'sd43fdsf'
        }
    )
    assert response.status_code == 201
