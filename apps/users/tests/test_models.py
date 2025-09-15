import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_user_creation_success():
    user = User.objects.create_user(email='u1@example.com', username='u1', password='pass12345')
    assert user.id is not None
    assert user.email == 'u1@example.com'
    assert user.check_password('pass12345')


def test_email_unique_constraint():
    User.objects.create_user(email='dup@example.com', username='dup1', password='pass12345')
    with pytest.raises(IntegrityError):
        User.objects.create_user(email='dup@example.com', username='dup2', password='pass12345')


def test_optional_fields_phone_address_blank():
    user = User.objects.create_user(email='opt@example.com', username='opt', password='pass12345')
    assert user.phone in (None, '')
    assert user.address in (None, '')


def test_str_returns_email():
    user = User.objects.create_user(email='str@example.com', username='str', password='pass12345')
    assert str(user) == 'str@example.com'


def test_username_field_config():
    assert User.USERNAME_FIELD == 'email'
    assert 'username' in User.REQUIRED_FIELDS


