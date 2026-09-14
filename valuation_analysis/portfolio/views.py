import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt


from .models import Acao, AtivoNaCarteira, Carteira
from .services.api_client import PlaybookAPIClient


def dashboard(request):
    return redirect('simulador_aporte')


def configuracoes(request):
    carteira = Carteira.objects.first()
    sucesso = None
    erro = None

    if not carteira:
        return render(request, "portfolio/configuracoes.html", {"erro": "Nenhuma carteira encontrada."})

    # FUNÇÃO ESCUDO: Evita que campos vazios ou com vírgulas quebrem o sistema
    def safe_float(val, default_value=0.0):
        if val is None or str(val).strip() == "":
            return default_value
        try:
            return float(str(val).replace(',', '.'))
        except ValueError:
            return default_value

    if request.method == "POST":
        try:
            if "salvar_carteira" in request.POST:
                carteira.banda_mais = safe_float(request.POST.get("banda_mais"), carteira.banda_mais)
                carteira.banda_menos = safe_float(request.POST.get("banda_menos"), carteira.banda_menos)
                carteira.margem_de_seguranca_minima = safe_float(request.POST.get("margem_minima"), carteira.margem_de_seguranca_minima)
                
                carteira.save()
                sucesso = "Configurações da carteira atualizadas com sucesso!"

            elif "salvar_ativos" in request.POST:
                for ativo in carteira.ativos.all():
                    ativo_id = str(ativo.id)
                    
                    # Salva Quantidade com segurança
                    qtd_str = request.POST.get(f"quantidade_{ativo_id}")
                    if qtd_str and str(qtd_str).strip() != "":
                        try:
                            ativo.quantidade = int(qtd_str)
                        except ValueError:
                            pass
                            
                    ativo.metodo_valuation = request.POST.get(f"metodo_{ativo_id}", ativo.metodo_valuation)
                    
                    # Salva Parâmetros Genéricos de forma super segura
                    ativo.parametro_bazin_dy = safe_float(request.POST.get(f"bazin_dy_{ativo_id}"), ativo.parametro_bazin_dy)
                    ativo.parametro_lynch_crescimento = safe_float(request.POST.get(f"lynch_cresc_{ativo_id}"), ativo.parametro_lynch_crescimento)
                    ativo.parametro_projetivo_pl_justo = safe_float(request.POST.get(f"proj_pl_{ativo_id}"), ativo.parametro_projetivo_pl_justo)
                    ativo.parametro_dfc_taxa_desconto = safe_float(request.POST.get(f"dfc_taxa_{ativo_id}"), ativo.parametro_dfc_taxa_desconto)
                    ativo.parametro_dfc_crescimento = safe_float(request.POST.get(f"dfc_cresc_{ativo_id}"), ativo.parametro_dfc_crescimento)
                    
                    fluxos_str = request.POST.get(f"dfc_fluxos_{ativo_id}")
                    if fluxos_str is not None:
                        ativo.parametro_dfc_fluxos = fluxos_str.strip()
                    
                    # PRESERVA OS PARÂMETROS ANTIGOS para não zerar o banco acidentalmente
                    prefix = f"spec_{ativo_id}_"
                    especificos = ativo.parametros_especificos.copy() if isinstance(ativo.parametros_especificos, dict) else {}
                    
                    # Atualiza com os valores enviados (como arrumamos o JS, não haverá conflito)
                    for key, value in request.POST.items():
                        if key.startswith(prefix) and value.strip() != "":
                            param_name = key[len(prefix):]
                            try:
                                # Tratar listas como historico_ebitda (ex: "[1.5, 2.0]")
                                if '[' in value and ']' in value:
                                    especificos[param_name] = json.loads(value)
                                else:
                                    # Usa nossa função escudo para formatar números
                                    especificos[param_name] = safe_float(value, 0.0)
                            except (ValueError, json.JSONDecodeError):
                                especificos[param_name] = value.strip()

                    ativo.parametros_especificos = especificos
                    ativo.save()
                    
                sucesso = "Configurações dos ativos atualizadas com sucesso!"

        except Exception as e:
            erro = f"Ocorreu um erro ao guardar as alterações: {e}"

    context = {
        "carteira": carteira,
        "sucesso": sucesso,
        "erro": erro
    }
    return render(request, "portfolio/configuracoes.html", context)

@csrf_exempt
def atualizar_ativo_api(request, ativo_id):
    if request.method == "POST":
        ativo = get_object_or_404(AtivoNaCarteira, id=ativo_id)
        
        try:
            from .services.portfolio_updates import atualizar_posicao
            atualizar_posicao(ativo, cotacao=True, teto=True)

            return JsonResponse({
                "sucesso": True,
                "preco_atual": ativo.acao.preco_atual,
                "preco_teto": ativo.preco_teto,
                "margem_seguranca": ativo.margem_de_seguranca,
                "valor_total": ativo.valor_total,
                "percentual_na_carteira": ativo.percentual_na_carteira
            })
            
        except Exception as e:
            return JsonResponse({"sucesso": False, "erro": str(e)}, status=500)
            
    return JsonResponse({"erro": "Método não permitido"}, status=405)


def gerenciar_ativos(request):
    carteira = Carteira.objects.first()
    if not carteira:
        carteira = Carteira.objects.create(nome="Minha Carteira Principal")
    
    ativos = carteira.ativos.all()
    
    context = {
        "carteira": carteira,
        "ativos": ativos
    }
    return render(request, "portfolio/gerenciar_ativos.html", context)


def adicionar_ativo(request):
    if request.method == "POST":
        ticket = request.POST.get("ticket", "").strip().upper()
        nome = request.POST.get("nome", "").strip()
        
        if not ticket:
            messages.error(request, "O ticker do ativo é obrigatório.")
            return redirect('gerenciar_ativos')

        carteira = Carteira.objects.first()
        if not carteira:
            carteira = Carteira.objects.create(nome="Minha Carteira Principal")

        if not nome:
            nome = f"Empresa {ticket}"

        acao, created = Acao.objects.get_or_create(
            ticket=ticket,
            defaults={'nome': nome}
        )

        if created:
            try:
                client = PlaybookAPIClient()
                novo_preco = client.get_price(acao.ticket)
                if novo_preco > 0:
                    acao.preco_atual = novo_preco
                    acao.save()
            except Exception as e:
                print(f"Erro ao buscar preço inicial de {ticket}: {e}")

        ativo_existente = AtivoNaCarteira.objects.filter(carteira=carteira, acao=acao).exists()
        
        if not ativo_existente:
            AtivoNaCarteira.objects.create(
                carteira=carteira,
                acao=acao,
                quantidade=0,
                metodo_valuation='graham'
            )
            messages.success(request, f"Ativo {ticket} adicionado com sucesso à carteira!")
        else:
            messages.warning(request, f"O ativo {ticket} já faz parte da sua carteira.")

    return redirect('gerenciar_ativos')

def remover_ativo(request, ativo_id):
    if request.method == "POST":
        ativo = get_object_or_404(AtivoNaCarteira, id=ativo_id)
        ticket = ativo.acao.ticket
        ativo.delete()
        messages.success(request, f"Ativo {ticket} removido da carteira com sucesso.")
        
    return redirect('gerenciar_ativos')


