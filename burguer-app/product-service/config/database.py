# Conecta ao banco de dados MongoDB utilizando as variáveis de ambiente

from pymongo import MongoClient
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env

load_dotenv()
shared_env = Path(__file__).resolve().parents[2] / "auth-service" / ".env"
load_dotenv(shared_env)

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise RuntimeError(f"MONGO_URI não configurada; verifique {shared_env}")

# Cria a conexão com o banco de dados MongoDB

client = MongoClient(mongo_uri)

# Seleciona o banco de dados
db = client["burguer_app_db"]

# função para retornar a instância do banco de dados
def get_db():
    return db
