"""Agentes sequenciais via LiteLLM; nenhuma execução de ferramentas ou de código."""
import hashlib
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')
import litellm
from django.conf import settings
from django.core.cache import cache

litellm.suppress_debug_info = True


class AnalysisError(Exception):
    def __init__(self, code, message, attempts=None, http_status=503):
        super().__init__(message)
        self.code = code
        self.attempts = attempts or []
        self.http_status = http_status


@dataclass(frozen=True)
class AIAgent:
    id: str
    name: str
    model: str
    api_key: str = field(repr=False)

    @property
    def cache_key(self):
        # Trocar a chave/modelo não reaproveita o bloqueio da configuração anterior.
        digest = hashlib.sha256(f'{self.id}:{self.model}:{self.api_key}'.encode()).hexdigest()
        return f'playbook-ai:cooldown:{digest}'


class PlaybookAIAnalyzer:
    def __init__(self, agents=None, completion=None, cache_backend=None):
        self.agents = agents if agents is not None else [
            AIAgent(item['id'], item['name'], item['model'], os.getenv(item['key_env'], '').strip())
            for item in settings.PLAYBOOK_AI_AGENTS
        ]
        self.completion = completion or litellm.completion
        self.cache = cache_backend if cache_backend is not None else cache

    def public_agents(self):
        return [{'id': a.id, 'name': a.name, 'configured': bool(a.api_key and a.model)} for a in self.agents]

    def reset_limits(self, agent_id=None):
        for agent in self.agents:
            if agent_id is None or agent.id == agent_id:
                self.cache.delete(agent.cache_key)

    @staticmethod
    def _retry_after(exc, default):
        headers = getattr(getattr(exc, 'response', None), 'headers', {}) or getattr(exc, 'headers', {}) or {}
        value = headers.get('retry-after')
        try:
            seconds = float(value)
        except (TypeError, ValueError):
            try:
                seconds = (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                seconds = default
        if not math.isfinite(seconds):
            seconds = default
        return max(1, min(int(seconds), 86400))

    @staticmethod
    def _failure(exc):
        # Texto bruto serve somente para classificação; nunca vai para HTML/log da aplicação.
        if isinstance(exc, litellm.ContentPolicyViolationError):
            raise AnalysisError('conteudo_recusado', 'O provedor recusou esta solicitação. Revise os dados do Playbook.', http_status=422)
        if isinstance(exc, litellm.ContextWindowExceededError):
            return 'contexto', 'O Playbook excede a capacidade de contexto deste modelo.', 0
        if isinstance(exc, (litellm.AuthenticationError, litellm.PermissionDeniedError, litellm.NotFoundError)):
            return 'configuracao', 'Chave, permissão ou modelo inválido. Verifique a configuração.', 60
        text = str(exc).lower()
        quota_markers = ('insufficient_quota', 'insufficient balance', 'credit balance', 'billing_hard_limit',
                         'quota exceeded', 'exceeded your current quota', 'insufficient credit')
        if isinstance(exc, litellm.BudgetExceededError) or (
            getattr(exc, 'status_code', None) in (400, 402, 429) and any(m in text for m in quota_markers)
        ):
            return 'cota', 'Cota ou créditos indisponíveis neste provedor.', settings.PLAYBOOK_AI_QUOTA_COOLDOWN
        if isinstance(exc, litellm.RateLimitError):
            return 'limite', 'Limite temporário de requisições ou tokens atingido.', settings.PLAYBOOK_AI_LIMIT_COOLDOWN
        if isinstance(exc, litellm.Timeout):
            return 'timeout', 'O tempo de espera pela resposta terminou. Tente novamente; isso não indica falta de créditos.', 30
        if isinstance(exc, (litellm.APIConnectionError, litellm.ServiceUnavailableError)) or (
            isinstance(exc, litellm.APIError) and (getattr(exc, 'status_code', 0) or 0) >= 500
        ):
            return 'indisponivel', 'Provedor sem resposta ou temporariamente indisponível.', 30
        # Requisição inválida não significa que os tokens acabaram.
        raise AnalysisError('requisicao_invalida', 'A IA não aceitou a solicitação. Verifique o modelo e os parâmetros configurados.', http_status=422)

    def analyze(self, messages, preferred_agent=None):
        agents = list(self.agents)
        if preferred_agent:
            if preferred_agent not in {a.id for a in agents}:
                raise AnalysisError('agente_invalido', 'Selecione um agente válido.', http_status=400)
            agents.sort(key=lambda a: a.id != preferred_agent)
        if not any(a.api_key and a.model for a in agents):
            raise AnalysisError('sem_configuracao', 'Configure ao menos uma chave de API no .env: Claude, GPT ou Kimi.')
        attempts = []
        for agent in agents:
            if not agent.api_key or not agent.model:
                attempts.append({'agente': agent.name, 'motivo': 'nao_configurado', 'mensagem': 'Agente sem chave ou modelo configurado.'})
                continue
            paused = self.cache.get(agent.cache_key)
            if paused:
                attempts.append({'agente': agent.name, **paused, 'em_espera': True})
                continue
            try:
                response = self.completion(
                    model=agent.model, api_key=agent.api_key, messages=messages,
                    max_tokens=settings.PLAYBOOK_AI_MAX_TOKENS,
                    timeout=settings.PLAYBOOK_AI_TIMEOUT, num_retries=0,
                    stream=False, drop_params=True,
                )
            except Exception as exc:
                reason, message, seconds = self._failure(exc)
                failure = {'motivo': reason, 'mensagem': message}
                if seconds:
                    seconds = self._retry_after(exc, seconds)
                    failure['tentar_apos'] = int(time.time()) + seconds
                    self.cache.set(agent.cache_key, failure, timeout=seconds)
                attempts.append({'agente': agent.name, **failure})
                continue
            choices = getattr(response, 'choices', None)
            content = choices[0].message.content if choices else None
            finish = choices[0].finish_reason if choices else None
            if finish == 'content_filter':
                raise AnalysisError('conteudo_recusado', 'O provedor interrompeu a análise por restrição de conteúdo.', attempts, 422)
            if not isinstance(content, str) or not content.strip():
                attempts.append({'agente': agent.name, 'motivo': 'resposta_vazia', 'mensagem': 'O modelo não retornou uma análise em texto.'})
                continue
            usage = getattr(response, 'usage', None)
            return {
                'agente': agent.name, 'modelo': agent.model, 'analise': content,
                'tentativas': attempts, 'parcial': finish == 'length',
                'aviso': 'A resposta atingiu o limite de saída e pode estar incompleta. Isso não indica esgotamento da cota.' if finish == 'length' else '',
                'tokens_utilizados': getattr(usage, 'total_tokens', None),
            }
        configured = [a for a in attempts if a['motivo'] != 'nao_configurado']
        if configured and all(a['motivo'] in ('cota', 'limite') for a in configured):
            raise AnalysisError('limites_esgotados', 'Todas as IAs configuradas atingiram suas cotas ou limites de uso. Aguarde a liberação do provedor ou revise seus créditos.', attempts, 429)
        raise AnalysisError('agentes_indisponiveis', 'Nenhuma IA conseguiu concluir a análise. Confira os motivos abaixo.', attempts)
