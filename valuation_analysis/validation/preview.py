"""Prévia local com dados fictícios, SQLite em memória e API simulada.

Executar a partir da raiz: venv/Scripts/python.exe valuation_analysis/validation/preview.py
Não usa nem altera db.sqlite3. Disponível apenas em http://127.0.0.1:8766.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from wsgiref.simple_server import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.conf import settings
settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

import django
django.setup()
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from portfolio.models import Carteira, Acao, AtivoNaCarteira
from aporte.models import Aporte, ItemAporte

call_command('migrate', verbosity=0)
carteira = Carteira.objects.create(banda_mais=60)
for ticker, metodo, preco, teto, qtd in [
    ('BBAS3', 'bbas', 22.5, 35.678, 100), ('PETR4', 'petr', 35.2, 42.2, 80),
    ('WEGE3', 'graham', 45.0, 39.2, 50), ('ITSA4', 'itsa', 10.2, 13.5, 200),
]:
    acao = Acao.objects.create(ticket=ticker, nome=ticker, preco_atual=preco)
    AtivoNaCarteira.objects.create(carteira=carteira, acao=acao, metodo_valuation=metodo,
                                  preco_teto=teto, quantidade=qtd)
for status in ('em_analise', 'cancelado', 'efetuado'):
    aporte = Aporte.objects.create(carteira=carteira, valor_total=1500, status=status,
                                   estrategia_utilizada='dividido')
    ItemAporte.objects.create(aporte=aporte, ticker='BBAS3', tipo_ativo='acao',
                              metodo_valuation='graham', preco_teto_calculado=35.678,
                              preco_atual_momento=22.5, valor_aportado=1500)

settings.PLAYBOOK_AI_AGENTS = [
    {'id': name.lower(), 'name': name, 'model': model, 'key_env': 'PREVIEW_AI_KEY'}
    for name, model in [('Claude', 'anthropic/test'), ('GPT', 'openai/test'), ('Kimi', 'moonshot/test')]]
os.environ['PREVIEW_AI_KEY'] = 'fake-preview-key'

def fake_completion(**kwargs):
    import litellm
    if kwargs['model'] == 'anthropic/test':
        raise litellm.RateLimitError(message='insufficient_quota', model='test', llm_provider='test')
    return SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content='## Ativo — BBAS3\nClassificação: Reavaliar\nAnálise fictícia para validar a interface.'),
        finish_reason='stop')], usage=SimpleNamespace(total_tokens=123))

with patch('litellm.completion', side_effect=fake_completion), patch('portfolio.services.api_client.requests.get') as request:
    request.return_value.json.return_value = {'preco': 24.0, 'preco_teto_graham': 36.0}
    print('Prévia fictícia: http://127.0.0.1:8766', flush=True)
    make_server('127.0.0.1', 8766, StaticFilesHandler(get_wsgi_application())).serve_forever()
