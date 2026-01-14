import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("❌ Erro: SUPABASE_URL ou SUPABASE_KEY não encontrados no arquivo .env")

# Cria o cliente de conexão
supabase: Client = create_client(url, key)