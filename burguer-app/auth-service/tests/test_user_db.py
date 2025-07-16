import pytest
from models.user_model import serialize_user

@pytest.mark.usefixtures("test_db")

def test_isercao_usuario(test_db):
    # Dados de exemplo
    usuario = {
        "email": "test@exemplo.com",
        "name": "Teste",
    }

    result = test_db["users"].insert_one(usuario)
    encontrado = test_db["users"].find_one({"_id": result.inserted_id})

    assert encontrado["email"] == "test@exemplo.com"