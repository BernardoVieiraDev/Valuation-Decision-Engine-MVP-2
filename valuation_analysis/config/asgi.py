import os
import sys
from pathlib import Path
from django.core.asgi import get_asgi_application
from starlette.routing import Mount
from starlette.applications import Starlette
from dotenv import load_dotenv  # <-- IMPORTANTE: Importa o leitor de .env

# Adiciona o diretório principal ao sys.path para que o Python ache a pasta "app"
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# <-- NOVO: Carrega as variáveis de ambiente do arquivo app/.env
env_path = BASE_DIR / "app" / ".env"
load_dotenv(dotenv_path=env_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_asgi = get_asgi_application()

# Agora isto não vai falhar por falta de variáveis de ambiente
from app.main import app as fastapi_app

routes = [
    Mount("/api", app=fastapi_app),
    Mount("/", app=django_asgi),
]

application = Starlette(routes=routes)