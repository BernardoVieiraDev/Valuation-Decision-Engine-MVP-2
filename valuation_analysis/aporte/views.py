import math
import time
import uuid

from .services.simulation import snapshot
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from portfolio.models import Carteira
from .models import Aporte, ItemAporte
from django.views.decorators.http import require_POST
from django.db import transaction
from portfolio.services.api_client import PlaybookAPIClient
from portfolio.services.portfolio_updates import atualizar_posicao
from .services.strategy import StrategyConcentrado, StrategyDividido

def simulador_aporte(request):
    carteira = Carteira.objects.first()
    recomendacoes = []
    aporte_restante = 0
    erro = None
    resumo = None
    
    if carteira and request.method == 'POST' and (
        'atualizar_precos' in request.POST or 'calcular_tetos' in request.POST
    ):
        try:
            client = PlaybookAPIClient()
            for ativo in carteira.ativos.select_related('acao'):
                atualizar_posicao(ativo, client=client,
                    cotacao='atualizar_precos' in request.POST,
                    teto='calcular_tetos' in request.POST)
            messages.success(request, 'Carteira atualizada com sucesso.')
        except Exception:
            messages.error(request, 'Não foi possível concluir a atualização. Verifique a API e tente novamente.')
        return redirect('simulador_aporte')

    ativos_ordenados = []
    if carteira:
        ativos_ordenados = sorted(
            carteira.ativos.all(), 
            key=lambda a: getattr(a, 'margem_de_seguranca', 0), 
            reverse=True
        )

    if request.method == "POST" and "calcular_aporte" in request.POST:
        try:
            valor_aporte = float(request.POST.get("valor", 0.0))
            if not math.isfinite(valor_aporte) or valor_aporte <= 0:
                raise ValueError('Valor inválido')
            tipo_estrategia = request.POST.get("estrategia", "dividido")
            limite_ativos_str = request.POST.get("limite_ativos", "")
            limite_ativos = int(limite_ativos_str) if limite_ativos_str.isdigit() else None
            
            ativos_excluidos = request.POST.getlist("ativos_excluidos")
            tipos_permitidos = request.POST.getlist("tipos_permitidos")
            
            if tipo_estrategia == "concentrado":
                estrategia = StrategyConcentrado()
            else:
                estrategia = StrategyDividido()
                
            if carteira:
                recomendacoes = estrategia.definir_aporte(
                    aporte=valor_aporte, 
                    carteira=carteira,
                    limite_ativos=limite_ativos,
                    tipos_permitidos=tipos_permitidos,
                    ativos_excluidos=ativos_excluidos
                )
                
                itens = snapshot(recomendacoes)
                total_alocado = sum(item['valor_aportado'] for item in itens)
                aporte_restante = max(0, valor_aporte - total_alocado)
                token = str(uuid.uuid4())
                resumo = {
                    'token': token, 'carteira_id': carteira.id,
                    'valor_total': valor_aporte, 'total_alocado': total_alocado,
                    'caixa': aporte_restante, 'estrategia': tipo_estrategia,
                    'itens': itens, 'criado_em': time.time(),
                }
                drafts = request.session.get('simulacoes_aporte', {})
                drafts = {k: v for k, v in drafts.items() if time.time() - v['criado_em'] < 1800}
                drafts = dict(list(drafts.items())[-4:])
                drafts[token] = resumo
                request.session['simulacoes_aporte'] = drafts

        except ValueError:
            erro = "Por favor, insira um valor numérico válido."
            
    context = {
        "carteira": carteira,
        "ativos_ordenados": ativos_ordenados,
        "recomendacoes": recomendacoes,
        "aporte_restante": aporte_restante,
        "erro": erro,
        "resumo": resumo,
        "filtros": request.POST,
        "tipos_selecionados": request.POST.getlist("tipos_permitidos") if "calcular_aporte" in request.POST else ["acao", "fii", "etf", "cripto"],
        "excluidos_selecionados": request.POST.getlist("ativos_excluidos")
    }          
    return render(request, "aporte/simulador.html", context)


def historico_aportes(request):
    """ View para listar os aportes e gerenciar seus status """
    aportes = Aporte.objects.select_related('diario_playbook').prefetch_related('ativos').all().order_by('-data_criacao')
    
    context = {
        "aportes": aportes
    }
    return render(request, "aporte/historico.html", context)

def mudar_status_aporte(request, aporte_id):
    """ View para processar a aprovação ou cancelamento do aporte """
    if request.method == "POST":
        aporte = get_object_or_404(Aporte, id=aporte_id)
        novo_status = request.POST.get("status")
        
        status_validos = dict(Aporte.STATUS_CHOICES).keys()
        if novo_status in status_validos:
            aporte.status = novo_status
            aporte.save()
            
            if novo_status == 'efetuado':
                messages.success(request, f"Aporte #{aporte.id} marcado como Efetuado com sucesso!")
            else:
                messages.warning(request, f"Aporte #{aporte.id} foi Cancelado.")
        
    return redirect('historico_aportes')

def editar_item_aporte(request, item_id):
    """ View para alterar o valor aportado e o teto calculado em um ativo específico """
    if request.method == "POST":
        item = get_object_or_404(ItemAporte, id=item_id)
        
        # Só permite editar se o aporte estiver "Em Análise"
        if item.aporte.status != 'em_analise':
            messages.error(request, "Não é possível editar itens de um aporte já finalizado ou cancelado.")
            return redirect('historico_aportes')

        novo_valor_str = request.POST.get("valor_aportado", "").replace(',', '.')
        novo_teto_str = request.POST.get("preco_teto_calculado", "").replace(',', '.')
        
        try:
            # Atualiza o valor do aporte (obrigatório)
            if novo_valor_str:
                item.valor_aportado = float(novo_valor_str)
            
            # Atualiza o preço teto (opcional, pode vir vazio dependendo do método)
            if novo_teto_str:
                item.preco_teto_calculado = float(novo_teto_str)
                
            item.save()
            
            # Recalcula o valor total do Aporte Pai
            aporte = item.aporte
            novo_total = sum(i.valor_aportado for i in aporte.ativos.all())
            aporte.valor_total = novo_total
            aporte.save()
            
            messages.success(request, f"Valores do ativo {item.ticker} atualizados com sucesso.")
        except ValueError:
            messages.error(request, "Valor inválido inserido. Certifique-se de usar apenas números e pontos/vírgulas.")
            
    return redirect('historico_aportes')

@require_POST
def excluir_aporte(request, aporte_id):
    aporte = get_object_or_404(Aporte, id=aporte_id)
    with transaction.atomic():
        aporte.delete()
    messages.success(request, 'Aporte, itens e Playbook associado excluídos.')
    return redirect('historico_aportes')


@require_POST
def salvar_simulacao(request):
    token = request.POST.get('simulacao_token', '')
    resumo = request.session.get('simulacoes_aporte', {}).get(token)
    if not resumo or time.time() - resumo['criado_em'] > 1800:
        messages.error(request, 'Esta simulação expirou. Simule novamente antes de salvar.')
        return redirect('simulador_aporte')
    if not resumo['itens']:
        messages.error(request, 'Não há ativos elegíveis para salvar neste aporte.')
        return redirect('simulador_aporte')
    carteira = get_object_or_404(Carteira, id=resumo['carteira_id'])
    with transaction.atomic():
        aporte, created = Aporte.objects.get_or_create(
            simulacao_id=token,
            defaults={'carteira': carteira, 'valor_total': resumo['valor_total'],
                      'estrategia_utilizada': resumo['estrategia'], 'status': 'em_analise'},
        )
        if created:
            ItemAporte.objects.bulk_create([ItemAporte(aporte=aporte, **item) for item in resumo['itens']])
    messages.success(request, 'Aporte salvo no Histórico como Em Análise.' if created else 'Este aporte já foi salvo no Histórico.')
    return redirect('historico_aportes')
