"""Diagnóstico mínimo: não imprime chaves nem envia dados do Playbook."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.conf import settings
import requests

agent = next(a for a in settings.PLAYBOOK_AI_AGENTS if a['id'] == 'kimi')
key = os.getenv(agent['key_env'], '').strip()
print(json.dumps({'configurada': bool(key), 'modelo': agent['model']}))
if not key:
    sys.exit(1)
try:
    if '--analysis' in sys.argv:
        import time
        from datetime import datetime, timezone
        from types import SimpleNamespace
        from playbook.services.ai_analysis import PlaybookAIAnalyzer, AnalysisError
        from playbook.services.analysis_prompt import build_analysis_messages
        payload = {'nota': 'Dados fictícios para teste de integração.', 'ativos': [
            {'ticker': 'TEST3', 'tipo': 'graham', 'precoTeto': '35.68',
             'precoPago': '22.50', 'values': {'vpa': 20, 'lpa': 3}}]}
        messages = build_analysis_messages(payload, SimpleNamespace(data_criacao=datetime.now(timezone.utc)))
        started = time.monotonic()
        try:
            result = PlaybookAIAnalyzer().analyze(messages, preferred_agent='kimi')
            print(json.dumps({'sucesso': True, 'agente': result['agente'], 'parcial': result['parcial'],
                              'caracteres': len(result['analise']), 'segundos': round(time.monotonic()-started),
                              'tokens': result['tokens_utilizados']}))
        except AnalysisError as exc:
            print(json.dumps({'sucesso': False, 'codigo': exc.code, 'tentativas': exc.attempts,
                              'segundos': round(time.monotonic()-started)}))
        sys.exit(0)
    if '--models' in sys.argv:
        response = requests.get('https://api.moonshot.ai/v1/models',
                                headers={'Authorization': 'Bearer ' + key}, timeout=30)
        print(json.dumps({'status': response.status_code,
                          'modelos': [m['id'] for m in response.json().get('data', [])]}))
        sys.exit(0)
    response = requests.post('https://api.moonshot.ai/v1/chat/completions',
        headers={'Authorization': 'Bearer ' + key},
        json={'model': agent['model'].removeprefix('moonshot/'),
              'messages': [{'role': 'user', 'content': 'Responda apenas OK.'}],
              'max_tokens': 32, 'stream': False}, timeout=45)
    body = response.json()
    if response.ok:
        print(json.dumps({'status': response.status_code, 'sucesso': True,
                          'finish_reason': body.get('choices', [{}])[0].get('finish_reason')}))
    else:
        error = body.get('error', {})
        safe = {k: str(error.get(k, '')).replace(key, '[REDACTED]')[:1200]
                for k in ('type', 'code', 'message')}
        print(json.dumps({'status': response.status_code, 'erro': safe}))
except Exception as exc:
    print(json.dumps({'falha_conexao': type(exc).__name__}))
