import json
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.http import JsonResponse
from aporte.models import Aporte
from portfolio.models import AtivoNaCarteira, FIINaCarteira
from .models import DiarioPlaybook
from .services.analysis_prompt import ASSET_TYPES, build_analysis_messages
from .services.ai_analysis import PlaybookAIAnalyzer, AnalysisError
from django.core.cache import cache
from django.conf import settings
from django.http import UnreadablePostError
from django.core import signing
from django.utils import timezone

def playbook_list(request):
    """ Exibe a aba principal com a lista de todos os aportes e status do seu playbook """
    aportes = Aporte.objects.select_related('diario_playbook').exclude(diario_playbook__excluido=True).order_by('-data_criacao')
    return render(request, 'playbook/list.html', {'aportes': aportes})

def preencher_playbook(request, aporte_id):
    aporte = get_object_or_404(Aporte, id=aporte_id)
    
    # Mapeamento dos métodos do backend para as chaves do JS (ASSET_TYPES)
    mapa_metodos = {
        'bbas': 'bbas3', 'bbse': 'bbse3', 'brbi': 'brbi11',
        'flry': 'flry3', 'grnd': 'grnd3', 'itsa': 'itsa4',
        'klbn': 'klbn4', 'petr': 'petr4', 'sapr': 'sapr4',
        'taee': 'taee11', 'vale': 'vale3', 'wege': 'wege3',
        # Métodos genéricos
        'graham': 'graham', 'bazin': 'bazin', 'lynch': 'lynch',
        'dfc': 'dfc', 'projetivo': 'projetivo'
    }

    diario, created = DiarioPlaybook.objects.get_or_create(aporte=aporte)
    if diario.excluido:
        messages.info(request, 'Recrie o Playbook pelo Histórico de Aportes.')
        return redirect('historico_aportes')
    state_ativos = []

    # Se já tem registro salvo E com ativos válidos
    if diario.dados_json and isinstance(diario.dados_json, dict) and diario.dados_json.get('ativos'):
        state_ativos = diario.dados_json['ativos']
    else:
        # Se for o primeiro acesso, importa do simulador
        for item in aporte.ativos.all():
            tipo_js = mapa_metodos.get(item.metodo_valuation, '')
            if item.tipo_ativo == 'fii' and not tipo_js:
                tipo_js = 'fii_tijolo'
                
            raw_params = item.parametros_valuation or {}
            mapped_values = {}
            
            # De -> Para (Converte a chave salva no banco para a chave que o HTML precisa)
            key_map = {
                'roe_normalizado': 'roe', 'taxa_livre_risco': 'rf', 'taxa_livre_risco_real': 'rfReal',
                'premio_risco': 'erp', 'premio_risco_especifico': 'erp', 'crescimento_perpetuo': 'g',
                'crescimento_real': 'g', 'g_real': 'g', 'multiplo_alvo_ev_ebitda': 'multiplo',
                'multiplo_ev_ebitda': 'multiplo', 'desconto_alvo': 'desconto', 'dy_minimo': 'dyMin',
                'ntnb_real': 'ntnbReal', 'historico_dividendos_5_anos': 'histDiv5anos',
                'dividendos_5_anos': 'div5anos', 'historico_ebitda': 'histEbitda', 'ebitda_ttm': 'ebitdaTtm',
                'beta': 'beta', 'g1': 'g1', 'n1': 'n1', 'g3': 'g3', 'ke': 'ke'
            }
            
            for k, v in raw_params.items():
                frontend_key = key_map.get(k, k)
                if isinstance(v, list):
                    mapped_values[frontend_key] = "; ".join(map(str, v))
                else:
                    mapped_values[frontend_key] = v

            # Resgatar parâmetros dos métodos antigos (Graham, Bazin, DFC) direto da Carteira
            if item.tipo_ativo == 'acao':
                ativo_orig = AtivoNaCarteira.objects.filter(acao__ticket=item.ticker, carteira=aporte.carteira).first()
                if ativo_orig:
                    if item.metodo_valuation == 'bazin':
                        mapped_values['dyMin'] = ativo_orig.parametro_bazin_dy
                    elif item.metodo_valuation == 'lynch':
                        mapped_values['g'] = ativo_orig.parametro_lynch_crescimento
                    elif item.metodo_valuation == 'dfc':
                        mapped_values['ke'] = ativo_orig.parametro_dfc_taxa_desconto
                        mapped_values['g'] = ativo_orig.parametro_dfc_crescimento
                        mapped_values['fluxos'] = ativo_orig.parametro_dfc_fluxos
                    elif item.metodo_valuation == 'projetivo':
                        mapped_values['plJusto'] = ativo_orig.parametro_projetivo_pl_justo
            elif item.tipo_ativo == 'fii':
                fii_orig = FIINaCarteira.objects.filter(fii__ticket=item.ticker, carteira=aporte.carteira).first()
                if fii_orig and item.metodo_valuation == 'bazin':
                    mapped_values['dyMin'] = fii_orig.parametro_bazin_dy

            ativo_data = {
                'id': f"item-{item.id}",
                'ticker': item.ticker,
                'tipo': tipo_js,
                'qty': '',
                'precoPago': item.preco_atual_momento,
                'precoTeto': item.preco_teto_calculado,
                'gatilho': '', 'tese': '', 'conviccao': 50,
                'falseability': '', 'premortem': '', 
                'horizonte': '', 'alternativa': '',
                'values': mapped_values 
            }
            state_ativos.append(ativo_data)

    # SEGURANÇA: Se por qualquer motivo a lista ainda estiver vazia, cria 1 card em branco
    if not state_ativos:
        state_ativos.append({
            'id': str(uuid.uuid4()), 'ticker': '', 'tipo': '', 'qty': '',
            'precoPago': '', 'precoTeto': '', 'gatilho': '', 'tese': '', 
            'conviccao': 50, 'falseability': '', 'premortem': '', 
            'horizonte': '', 'alternativa': '', 'values': {}
        })

    context = {
        'analise_salva': diario.dados_json.get('analise_ia') if isinstance(diario.dados_json, dict) else None,
        'asset_types': ASSET_TYPES,
        'ai_agents': PlaybookAIAnalyzer().public_agents(),
        'aporte': aporte,
        'state_ativos_json': json.dumps(state_ativos),
        'nota_geral': diario.dados_json.get('nota', '') if isinstance(diario.dados_json, dict) else ''
    }
    return render(request, 'playbook/index.html', context)


@require_POST
def analisar_playbook(request, aporte_id):
    aporte = get_object_or_404(Aporte, id=aporte_id)
    if DiarioPlaybook.objects.filter(aporte=aporte, excluido=True).exists():
        return JsonResponse({'sucesso': False, 'erro': 'Recrie o Playbook antes de analisar.'}, status=409)
    try:
        if int(request.META.get('CONTENT_LENGTH') or 0) > 150000:
            return JsonResponse({'sucesso': False, 'erro': 'Playbook muito extenso.'}, status=413)
        body = request.body
        if len(body) > 150000:
            return JsonResponse({'sucesso': False, 'erro': 'Playbook muito extenso.'}, status=413)
        payload = json.loads(body)
        messages = build_analysis_messages(payload, aporte)
        preferred = payload.get('agente') or None
        if preferred is not None and not isinstance(preferred, str):
            raise ValueError('Agente inválido.')
    except (ValueError, TypeError, UnreadablePostError) as exc:
        # Mensagens de validação são nossas; JSON inválido não deve expor o corpo.
        message = 'Dados inválidos para análise.' if isinstance(exc, json.JSONDecodeError) else str(exc)
        return JsonResponse({'sucesso': False, 'erro': message}, status=400)
    lock = f'playbook-ai:running:{aporte.id}'
    ttl = settings.PLAYBOOK_AI_TIMEOUT * len(settings.PLAYBOOK_AI_AGENTS) + 60
    if not cache.add(lock, True, timeout=ttl):
        return JsonResponse({'sucesso': False, 'erro': 'Já existe uma análise em andamento para este aporte.'}, status=409)
    try:
        result = PlaybookAIAnalyzer().analyze(messages, preferred_agent=preferred)
        record = {**result, 'gerada_em': timezone.now().isoformat(), 'dados_analisados': json.loads(messages[1]['content'].split('\n', 1)[1])}
        result['analise_token'] = signing.dumps({'aporte_id': aporte.id, 'analise': record}, salt='playbook-analysis', compress=True)
        return JsonResponse({'sucesso': True, **result})
    except AnalysisError as exc:
        return JsonResponse({'sucesso': False, 'codigo': exc.code, 'erro': str(exc), 'tentativas': exc.attempts}, status=exc.http_status)
    except Exception:
        # Nunca retornar mensagens de SDK (podem incluir chaves, URLs ou dados do prompt).
        return JsonResponse({'sucesso': False, 'erro': 'Não foi possível concluir a análise. Tente novamente mais tarde.'}, status=503)
    finally:
        cache.delete(lock)

def salvar_playbook(request, aporte_id):
    if request.method == 'POST':
        aporte = get_object_or_404(Aporte, id=aporte_id)
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict) or not isinstance(data.get('ativos'), list):
                raise ValueError('Formato inválido')
            token = data.pop('analise_token', None)
            data.pop('analise_ia', None)  # Aceitar somente resultado assinado pelo servidor.
            if token:
                try:
                    signed = signing.loads(token, salt='playbook-analysis', max_age=7 * 86400)
                    if signed['aporte_id'] != aporte.id:
                        raise signing.BadSignature('Aporte diferente')
                    data['analise_ia'] = signed['analise']
                except (signing.BadSignature, TypeError, KeyError):
                    return JsonResponse({'sucesso': False, 'erro': 'Análise inválida ou expirada. Gere uma nova análise antes de salvar.'}, status=400)
            for ativo in data['ativos']:
                if not isinstance(ativo, dict):
                    raise ValueError('Ativo inválido')
                valor = Decimal(str(ativo.get('precoTeto', '')).replace(',', '.'))
                if not valor.is_finite() or valor <= 0:
                    raise ValueError('Preço-teto inválido')
                ativo['precoTeto'] = format(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), '.2f')
        except (ValueError, TypeError, InvalidOperation):
            return JsonResponse({'sucesso': False, 'erro': 'Informe ativos válidos e preço-teto positivo.'}, status=400)
        
        diario, _ = DiarioPlaybook.objects.get_or_create(aporte=aporte)
        if diario.excluido:
            return JsonResponse({'sucesso': False, 'erro': 'Recrie o Playbook pelo Histórico.'}, status=409)
        if 'analise_ia' not in data and isinstance(diario.dados_json, dict) and diario.dados_json.get('analise_ia'):
            data['analise_ia'] = diario.dados_json['analise_ia']
        # Preserva os campos antigos retirados do formulário, por identificador.
        antigos = diario.dados_json.get('ativos', []) if isinstance(diario.dados_json, dict) else []
        por_id = {a.get('id'): a for a in antigos if isinstance(a, dict)}
        for ativo in data['ativos']:
            anterior = por_id.get(ativo.get('id'), {})
            for campo in ('tese', 'conviccao', 'falseability', 'premortem', 'alternativa'):
                if campo in anterior:
                    ativo[campo] = anterior[campo]
        diario.dados_json = data
        diario.save()
        
        return JsonResponse({'sucesso': True})
    return JsonResponse({'sucesso': False}, status=405)

@require_POST
def excluir_playbook(request, aporte_id):
    aporte = get_object_or_404(Aporte, id=aporte_id)
    DiarioPlaybook.objects.update_or_create(aporte=aporte, defaults={'excluido': True, 'dados_json': {}})
    messages.success(request, 'Playbook excluído. O aporte permanece no Histórico.')
    return redirect('playbook_list')


@require_POST
def recriar_playbook(request, aporte_id):
    aporte = get_object_or_404(Aporte, id=aporte_id)
    diario, _ = DiarioPlaybook.objects.get_or_create(aporte=aporte)
    if diario.excluido:
        diario.excluido = False
        diario.dados_json = {}
        diario.save()
    return redirect('playbook_index', aporte_id=aporte.id)
