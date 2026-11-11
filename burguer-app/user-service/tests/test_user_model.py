"""Testes da serialização de usuário."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# pylint: disable-next=wrong-import-position,import-error
from models.user_model import serialize_user


def test_serialize_user_completo():
    """Usuário com todos os campos é retornado igual."""
    # Create a mock user object
    user = {
        "email": "teste@examplo.com",
        "name": "Fulano",
        "address": "Rua A, 123",
        "role": "admin"
    }
    resultado = serialize_user(user)
    esperado = {
        "email": "teste@examplo.com",
        "name": "Fulano",
        "address": "Rua A, 123",
        "role": "admin"
    }
    assert resultado == esperado


def test_serialize_user_campos_ausentes():
    """Campos ausentes recebem valores padrão."""
    user = {
        "email": "teste@examplo.com",
    }
    resultado = serialize_user(user)
    esperado = {
        "email": "teste@examplo.com",
        "name": "",
        "address": "",
        "role": "cliente"
    }
    assert resultado == esperado


def test_serialize_user_email_ausentes():
    """Usuário vazio retorna email None e demais padrões."""
    user = {}

    resultado = serialize_user(user)

    esperado = {
        "email": None,
        "name": "",
        "address": "",
        "role": "cliente"
    }
    assert resultado == esperado


def test_serialize_user_none():
    """Usuário None levanta AttributeError."""
    with pytest.raises(AttributeError):
        serialize_user(None)


def test_serialize_user_valores_none():
    """Campos presentes mas com valor None: None deve ser mantido"""
    user = {
        "email": None,
        "name": None,
        "address": None,
        "role": None
    }
    resultado = serialize_user(user)
    esperado = {
        "email": None,
        "name": None,
        "address": None,
        "role": None
    }
    assert resultado == esperado
