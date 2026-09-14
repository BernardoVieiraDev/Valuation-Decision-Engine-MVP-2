from django.db import models


# ==========================================================
# CONFIGURAÇÃO GLOBAL — cotação do dólar
# Usada para converter Cripto e ETF Internacional (cotados em
# USD) para BRL na hora de somar o valor da carteira.
# ==========================================================
class CotacaoDolar(models.Model):
    valor = models.FloatField(default=5.0, help_text="Cotação USD/BRL")
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"USD/BRL: {self.valor}"

    @classmethod
    def atual(cls):
        obj = cls.objects.first()
        return obj.valor if obj else 5.0


class Carteira(models.Model):
    nome = models.CharField(max_length=100, default="Minha Carteira Principal")
    margem_de_seguranca_minima = models.FloatField(default=5.0)
    banda_mais = models.FloatField(default=15.0)
    banda_menos = models.FloatField(default=2.5)

    def __str__(self):
        return self.nome

    @property
    def valor_total(self):
        total = 0.0
        # Um related_name para cada tipo de posição que existe na carteira.
        related_names = [
            "ativos",              # Ações
            "fiis",                # FIIs
            "criptos",             # Criptomoedas
            "rendas_fixas",        # Renda Fixa
            "etfs_br",             # ETFs Brasil
            "etfs_internacionais", # ETFs EUA
        ]
        for related_name in related_names:
            manager = getattr(self, related_name, None)
            if manager is not None:
                total += sum(pos.valor_total for pos in manager.all())
        return total


# ==========================================================
# AÇÕES (sem alterações em relação ao seu código original)
# ==========================================================
class Acao(models.Model):
    ticket = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    preco_atual = models.FloatField(default=0.0)

    def __str__(self):
        return self.ticket


class AtivoNaCarteira(models.Model):
    METODOS_CHOICES = [
        ('graham', 'Benjamin Graham'),
        ('bazin', 'Décio Bazin'),
        ('lynch', 'Peter Lynch'),
        ('dfc', 'Fluxo de Caixa Descontado (DFC)'),
        ('projetivo', 'Modelo Projetivo'),
        ('bbas', 'Preço Teto BBAS'),
        ('bbse', 'Preço Teto BBSE3'),
        ('brbi', 'Preço Teto BRBI11'),
        ('flry', 'Preço Teto FLRY3'),
        ('grnd', 'Preço Teto GRND3'),
        ('itsa', 'Preço Teto ITSA4'),
        ('klbn', 'Preço Teto KLBN4'),
        ('petr', 'Preço Teto PETR4'),
        ('sapr', 'Preço Teto SAPR4'),
        ('taee', 'Preço Teto TAEE11'),
        ('vale', 'Preço Teto VALE3'),
        ('wege', 'Preço Teto WEGE3'),
    ]

    parametros_especificos = models.JSONField(default=dict, blank=True, help_text="Guarda parâmetros das formulas específicas (BBAS, PETR, etc.)")

    carteira = models.ForeignKey(Carteira, related_name='ativos', on_delete=models.CASCADE)
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=0)
    preco_teto = models.FloatField(default=0.0)

    metodo_valuation = models.CharField(max_length=20, choices=METODOS_CHOICES, default='graham')

    parametro_bazin_dy = models.FloatField(default=6.0, help_text="Dividend Yield Desejado (%)")
    parametro_lynch_crescimento = models.FloatField(default=10.0, help_text="Taxa de Crescimento (%)")

    parametro_projetivo_pl_justo = models.FloatField(default=10.0, help_text="P/L Justo para modelo Projetivo")
    parametro_dfc_taxa_desconto = models.FloatField(default=10.0, help_text="Taxa de Desconto (%) para DFC")
    parametro_dfc_crescimento = models.FloatField(default=5.0, help_text="Crescimento Perpétuo (%) para DFC")
    parametro_dfc_fluxos = models.CharField(max_length=255, blank=True, null=True, help_text="Lista de fluxos (ex: [1.5, 1.7])")

    def __str__(self):
        return f"{self.acao.ticket} na {self.carteira.nome}"

    @property
    def margem_de_seguranca(self):
        if self.preco_teto > 0 and self.acao.preco_atual > 0:
            return ((self.preco_teto - self.acao.preco_atual) / self.preco_teto) * 100
        return 0.0

    @property
    def valor_total(self):
        return self.acao.preco_atual * self.quantidade

    @property
    def percentual_na_carteira(self):
        total_carteira = self.carteira.valor_total
        if total_carteira == 0:
            return 0
        return (self.valor_total / total_carteira) * 100


# ==========================================================
# FIIs — Fundos de Investimento Imobiliário
# ==========================================================
class FII(models.Model):
    SEGMENTO_CHOICES = [
        ('tijolo', 'Tijolo (imóveis físicos)'),
        ('papel', 'Papel (CRI / recebíveis)'),
        ('hibrido', 'Híbrido'),
        ('fof', 'Fundo de Fundos (FOF)'),
    ]

    ticket = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    segmento = models.CharField(max_length=10, choices=SEGMENTO_CHOICES, default='tijolo')
    preco_atual = models.FloatField(default=0.0)

    def __str__(self):
        return self.ticket


class FIINaCarteira(models.Model):
    METODOS_CHOICES = [
        ('bazin', 'Décio Bazin (DY desejado)'),
        ('valor_patrimonial', 'Valor Patrimonial (P/VP)'),
    ]

    carteira = models.ForeignKey(Carteira, related_name='fiis', on_delete=models.CASCADE)
    fii = models.ForeignKey(FII, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=0)
    preco_teto = models.FloatField(default=0.0)

    metodo_valuation = models.CharField(max_length=20, choices=METODOS_CHOICES, default='bazin')
    parametro_bazin_dy = models.FloatField(default=8.0, help_text="Dividend Yield Desejado (%)")
    parametro_vp_maximo = models.FloatField(default=1.0, help_text="P/VP máximo aceitável")

    def __str__(self):
        return f"{self.fii.ticket} na {self.carteira.nome}"

    @property
    def margem_de_seguranca(self):
        if self.preco_teto > 0 and self.fii.preco_atual > 0:
            return ((self.preco_teto - self.fii.preco_atual) / self.preco_teto) * 100
        return 0.0

    @property
    def valor_total(self):
        return self.fii.preco_atual * self.quantidade

    @property
    def percentual_na_carteira(self):
        total_carteira = self.carteira.valor_total
        if total_carteira == 0:
            return 0
        return (self.valor_total / total_carteira) * 100


# ==========================================================
# CRIPTOMOEDAS
# APIs de cripto (CoinGecko, Binance etc.) quase sempre cotam
# em USD, então guardamos o preço em dólar e convertemos.
# ==========================================================
class Cripto(models.Model):
    ticket = models.CharField(max_length=10, unique=True)  # BTC, ETH, SOL...
    nome = models.CharField(max_length=100)
    preco_atual_usd = models.FloatField(default=0.0)

    def __str__(self):
        return self.ticket

    @property
    def preco_atual_brl(self):
        return self.preco_atual_usd * CotacaoDolar.atual()


class CriptoNaCarteira(models.Model):
    carteira = models.ForeignKey(Carteira, related_name='criptos', on_delete=models.CASCADE)
    cripto = models.ForeignKey(Cripto, on_delete=models.CASCADE)
    quantidade = models.FloatField(default=0.0, help_text="Permite frações, ex: 0.0053 BTC")
    preco_medio_compra_usd = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.cripto.ticket} na {self.carteira.nome}"

    @property
    def valor_total(self):
        return self.cripto.preco_atual_brl * self.quantidade

    @property
    def valor_total_usd(self):
        return self.cripto.preco_atual_usd * self.quantidade

    @property
    def percentual_na_carteira(self):
        total_carteira = self.carteira.valor_total
        if total_carteira == 0:
            return 0
        return (self.valor_total / total_carteira) * 100


# ==========================================================
# RENDA FIXA
# Diferente dos outros: não existe "ticker" nem cotação de
# mercado pública. Cada aplicação é uma posição própria, então
# não separamos "ativo cadastrado" de "posição na carteira".
# ==========================================================
class RendaFixa(models.Model):
    TIPO_CHOICES = [
        ('cdb', 'CDB'),
        ('lci', 'LCI'),
        ('lca', 'LCA'),
        ('tesouro_selic', 'Tesouro Selic'),
        ('tesouro_ipca', 'Tesouro IPCA+'),
        ('tesouro_pre', 'Tesouro Prefixado'),
        ('debenture', 'Debênture'),
        ('cri_cra', 'CRI/CRA'),
        ('poupanca', 'Poupança'),
        ('outro', 'Outro'),
    ]
    INDEXADOR_CHOICES = [
        ('cdi', '% do CDI'),
        ('ipca', 'IPCA +'),
        ('selic', 'Selic'),
        ('prefixado', 'Prefixado'),
    ]

    carteira = models.ForeignKey(Carteira, related_name='rendas_fixas', on_delete=models.CASCADE)
    nome = models.CharField(max_length=150, help_text="Ex: CDB Banco XP 2027")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='cdb')
    indexador = models.CharField(max_length=15, choices=INDEXADOR_CHOICES, default='cdi')
    taxa_contratada = models.FloatField(default=100.0, help_text="Ex: 110 (110% do CDI) ou 6.0 (IPCA + 6%)")

    data_aplicacao = models.DateField(null=True, blank=True)
    data_vencimento = models.DateField(null=True, blank=True)

    valor_aplicado = models.FloatField(default=0.0, help_text="Valor investido originalmente")
    valor_atual = models.FloatField(default=0.0, help_text="Valor atualizado — atualize manualmente ou calcule à parte")
    isento_ir = models.BooleanField(default=False, help_text="LCI/LCA/CRI/CRA geralmente são isentos de IR para PF")

    def __str__(self):
        return f"{self.nome} na {self.carteira.nome}"

    @property
    def rentabilidade_percentual(self):
        if self.valor_aplicado > 0:
            return ((self.valor_atual - self.valor_aplicado) / self.valor_aplicado) * 100
        return 0.0

    @property
    def valor_total(self):
        return self.valor_atual

    @property
    def percentual_na_carteira(self):
        total_carteira = self.carteira.valor_total
        if total_carteira == 0:
            return 0
        return (self.valor_total / total_carteira) * 100


# ==========================================================
# ETF — BRASIL (ex: BOVA11, IVVB11, SMAL11)
# ==========================================================
class ETF(models.Model):
    ticket = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    preco_atual = models.FloatField(default=0.0)

    def __str__(self):
        return self.ticket


class ETFNaCarteira(models.Model):
    carteira = models.ForeignKey(Carteira, related_name='etfs_br', on_delete=models.CASCADE)
    etf = models.ForeignKey(ETF, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=0)
    preco_teto = models.FloatField(default=0.0, help_text="Opcional — ETFs normalmente não têm 'preço justo'")

    def __str__(self):
        return f"{self.etf.ticket} na {self.carteira.nome}"

    @property
    def valor_total(self):
        return self.etf.preco_atual * self.quantidade

    @property
    def percentual_na_carteira(self):
        total_carteira = self.carteira.valor_total
        if total_carteira == 0:
            return 0
        return (self.valor_total / total_carteira) * 100


# ==========================================================
# ETF — INTERNACIONAL (comprado como se fosse em corretora dos EUA)
# Cotado em USD, quantidade em float pois corretoras americanas
# costumam permitir ações fracionárias (fractional shares).
# ==========================================================
class ETFInternacional(models.Model):
    ticket = models.CharField(max_length=10, unique=True)  # VOO, QQQ, SCHD...
    nome = models.CharField(max_length=100)
    preco_atual_usd = models.FloatField(default=0.0)

    def __str__(self):
        return self.ticket

    @property
    def preco_atual_brl(self):
        return self.preco_atual_usd * CotacaoDolar.atual()


class ETFInternacionalNaCarteira(models.Model):
    carteira = models.ForeignKey(Carteira, related_name='etfs_internacionais', on_delete=models.CASCADE)
    etf = models.ForeignKey(ETFInternacional, on_delete=models.CASCADE)
    quantidade = models.FloatField(default=0.0, help_text="Permite frações, ex: 1.35 cotas")
    preco_medio_compra_usd = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.etf.ticket} na {self.carteira.nome}"

    @property
    def valor_total(self):
        return self.etf.preco_atual_brl * self.quantidade

    @property
    def valor_total_usd(self):
        return self.etf.preco_atual_usd * self.quantidade

    @property
    def percentual_na_carteira(self):
        total_carteira = self.carteira.valor_total
        if total_carteira == 0:
            return 0
        return (self.valor_total / total_carteira) * 100