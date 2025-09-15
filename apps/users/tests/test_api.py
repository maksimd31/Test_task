import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_register_success(api_client):
    url = reverse('users:register')
    payload = {
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'StrongPass123',
        'password_confirm': 'StrongPass123',
        'phone': '+123456789',
        'address': 'Some street'
    }
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == status.HTTP_201_CREATED
    assert 'user' in resp.data
    assert resp.data['user']['email'] == 'new@example.com'
    assert 'access' in resp.data and 'refresh' in resp.data


def test_register_password_mismatch(api_client):
    url = reverse('users:register')
    payload = {
        'username': 'u2',
        'email': 'u2@example.com',
        'password': 'pass12345',
        'password_confirm': 'other',
    }
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Passwords do not match' in str(resp.data)


def test_register_duplicate_email(api_client):
    User.objects.create_user(email='dup@example.com', username='dup', password='pass12345')
    url = reverse('users:register')
    payload = {
        'username': 'dup2',
        'email': 'dup@example.com',
        'password': 'pass12345',
        'password_confirm': 'pass12345',
    }
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert 'already exists' in str(resp.data)


def test_login_success(api_client):
    user = User.objects.create_user(email='login@example.com', username='login', password='pass12345')
    url = reverse('users:login')
    payload = {'email': user.email, 'password': 'pass12345'}
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == status.HTTP_200_OK
    assert 'access' in resp.data and 'refresh' in resp.data
    assert resp.data['user']['email'] == user.email


def test_login_invalid_credentials(api_client):
    user = User.objects.create_user(email='bad@example.com', username='bad', password='pass12345')
    url = reverse('users:login')
    payload = {'email': user.email, 'password': 'wrong'}
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Invalid credentials' in str(resp.data)


def test_profile_requires_auth(api_client):
    url = reverse('users:profile')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_profile_get_authenticated(authenticated_client, user):
    url = reverse('users:profile')
    resp = authenticated_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['email'] == user.email


def test_profile_update(authenticated_client, user):
    url = reverse('users:profile')
    payload = {'phone': '+111', 'address': 'New addr'}
    resp = authenticated_client.patch(url, payload, format='json')
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['phone'] == '+111'
    assert resp.data['address'] == 'New addr'


def test_token_refresh(api_client):
    # Получаем токены через регистрацию
    reg_url = reverse('users:register')
    reg_payload = {
        'username': 'tokuser',
        'email': 'tok@example.com',
        'password': 'pass12345',
        'password_confirm': 'pass12345'
    }
    reg_resp = api_client.post(reg_url, reg_payload, format='json')
    assert reg_resp.status_code == status.HTTP_201_CREATED
    refresh_token = reg_resp.data['refresh']

    refresh_url = reverse('users:token_refresh')
    resp = api_client.post(refresh_url, {'refresh': refresh_token}, format='json')
    assert resp.status_code == status.HTTP_200_OK
    assert 'access' in resp.data

