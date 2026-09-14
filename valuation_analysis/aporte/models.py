from django.db import models
from portfolio.models import Carteira

class Aporte(models.Model):
    simulacao_id = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    STATUS_CHOICES = [
        ('em_analise', 'Em Análise'),
        ('cancelado', 'Cancelado'),
        ('efetuado', 'Efetuado'),
    ]

    carteira = models.ForeignKey(Carteira, on_delete=models.CASCADE, related_name="aportes_historico")
    valor_total = models.FloatField(default=0.0, help_text="Valor total simulado ou aportado")
    estrategia_utilizada = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: concentrado, dividido")
    
    # Status referenciando se foi feito ou não
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_analise')
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Aporte #{self.id} - {self.get_status_display()} - R$ {self.valor_total:.2f}"

class ItemAporte(models.Model):
    aporte = models.ForeignKey(Aporte, on_delete=models.CASCADE, related_name="ativos")

    # Identificação do ativo (salvo como texto para evitar quebras se o ativo for deletado no futuro)
    ticker = models.CharField(max_length=20, help_text="Ex: PETR4, KNCR11, BTC")
    tipo_ativo = models.CharField(max_length=20, help_text="acao, fii, cripto, etf")

    # Snapshot do Valuation (Fotografia do momento)
    metodo_valuation = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: bazin, graham, bbas")
    parametros_valuation = models.JSONField(default=dict, blank=True, help_text="Cópia dos parâmetros (P/L, DY, etc) no momento do cálculo")
    preco_teto_calculado = models.FloatField(default=0.0)
    preco_atual_momento = models.FloatField(default=0.0, help_text="Preço de mercado no momento do aporte")

    # Valores financeiros da recomendação
    valor_aportado = models.FloatField(default=0.0, help_text="Valor financeiro sugerido/destinado a este ativo")

    def __str__(self):
        return f"{self.ticker} - R$ {self.valor_aportado:.2f}"
