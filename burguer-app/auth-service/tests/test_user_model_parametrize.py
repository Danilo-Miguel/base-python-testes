import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user_model import serialize_user  # ajuste o import conforme seu arquivo

@pytest.mark.parametrize("user, esperado", [
    (
        {
            "email": "teste@exemplo",
            "name": "Fulano",
            "address": "Rua A, 123",
            "role": "admin"
        },
        {
            "email": "teste@exemplo",
            "name": "Fulano",
            "address": "Rua A, 123",
            "role": "admin"
        }
    ),
    (
        {
            "email": "teste@exemplo",
            
        },
        {
            "email": "teste@exemplo",
            "name": "",
            "address": "",
            "role": "cliente"
        }
    ),
    (
        {},
        {
            "email": None,
            "name": "",
            "address": "",
            "role": "cliente"
        }
    ),
    (
        {
            "email": None,
            "name": None,
            "address": None,
            "role": None
        },
          {
            "email": None,
            "name": None,
            "address": None,
            "role": None
        }
    ),
    (
          {
            "email": 123,
            "name": ["Nome", "Sobrenome"],
            "address": {"rua": "A"},
            "role": True
        },
        {   
            "email": 123,
            "name": ["Nome", "Sobrenome"],
            "address": {"rua": "A"},
            "role": True
        },

    )
])
def test_serialize_user_validado(user, esperado):
    """Testa a serialização de usuário com diferentes entradas."""
    resultado = serialize_user(user)
    assert resultado == esperado


@pytest.mark.parametrize("entrada", [
    None,  # Entrada é None
    "string",  # Entrada é string
    12345,  # Entrada é número
    [],  # Entrada é lista
])

def test_serialize_user_entradas_invalidas(entrada):
    """Testa a serialização de usuário com entradas inválidas."""
    with pytest.raises(AttributeError):
        serialize_user(entrada)
