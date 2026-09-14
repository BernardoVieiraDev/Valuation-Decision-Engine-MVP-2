from models.stock import ModelStock
from data_providers.data_provider import DataProvider


# ==========================================================
# Valuation Genérico
# ==========================================================
from services.valuation_engine.valuation_formulas.bazin import BazinCalculator
from services.valuation_engine.valuation_formulas.dfc import DCFCalculator
from services.valuation_engine.valuation_formulas.graham import GrahamCalculator
from services.valuation_engine.valuation_formulas.peter_lynch import PeterLynchCalculator
from services.valuation_engine.valuation_formulas.projetivo import ProjetivoCalculator

# ==========================================================
# Valuation Específico (Assets Formulas)
# ==========================================================
from services.valuation_engine.assets_formulas.bbas import CalculadoraPrecoTetoBBAS
from services.valuation_engine.assets_formulas.bbse import CalculadoraPrecoTetoBBSE3
from services.valuation_engine.assets_formulas.brbi import CalculadoraPrecoTetoBRBI11
from services.valuation_engine.assets_formulas.fii_papel import CalculadoraPrecoTetoFIIPapel
from services.valuation_engine.assets_formulas.fii_tijolo import CalculadoraPrecoTetoFIITijolo
from services.valuation_engine.assets_formulas.flry import CalculadoraPrecoTetoFLRY3
from services.valuation_engine.assets_formulas.grnd import CalculadoraPrecoTetoGRND3
from services.valuation_engine.assets_formulas.itsa import CalculadoraPrecoTetoITSA4
from services.valuation_engine.assets_formulas.klbn import CalculadoraPrecoTetoKLBN4
from services.valuation_engine.assets_formulas.petr import CalculadoraPrecoTetoPETR4
from services.valuation_engine.assets_formulas.sapr import CalculadoraPrecoTetoSAPR4
from services.valuation_engine.assets_formulas.taee import CalculadoraPrecoTetoTAEE11
from services.valuation_engine.assets_formulas.vale import CalculadoraPrecoTetoVALE3
from services.valuation_engine.assets_formulas.wege import CalculadoraPrecoTetoWEGE3


class AssertService:
    
    def __init__(self):
        self.data_provider = DataProvider()
        
        # Instâncias Genéricas
        self.bazin_calculator = BazinCalculator()
        self.dfc_calculator = DCFCalculator()
        self.graham_calculator = GrahamCalculator()
        self.peter_lynch_calculator = PeterLynchCalculator()
        self.projetivo_calculator = ProjetivoCalculator()
        
        # Instâncias Específicas
        self.bbas_calculator = CalculadoraPrecoTetoBBAS()
        self.bbse_calculator = CalculadoraPrecoTetoBBSE3()
        self.brbi_calculator = CalculadoraPrecoTetoBRBI11()
        self.fii_papel_calculator = CalculadoraPrecoTetoFIIPapel()
        self.fii_tijolo_calculator = CalculadoraPrecoTetoFIITijolo()
        self.flry_calculator = CalculadoraPrecoTetoFLRY3()
        self.grnd_calculator = CalculadoraPrecoTetoGRND3()
        self.itsa_calculator = CalculadoraPrecoTetoITSA4()
        self.klbn_calculator = CalculadoraPrecoTetoKLBN4()
        self.petr_calculator = CalculadoraPrecoTetoPETR4()
        self.sapr_calculator = CalculadoraPrecoTetoSAPR4()
        self.taee_calculator = CalculadoraPrecoTetoTAEE11()
        self.vale_calculator = CalculadoraPrecoTetoVALE3()
        self.wege_calculator = CalculadoraPrecoTetoWEGE3()


    async def get_price(self, stock: ModelStock):
        return await self.data_provider.get_price(stock)

    async def get_bazin_price(self, stock: ModelStock, dy_desejado):
        dy_medio = await self.data_provider.get_dividendos_medios(stock)

        if not dy_medio:
            raise ValueError(f"DY médio não disponível para o ativo {stock}")

        return self.bazin_calculator.calculate_bazin_price(dy_medio, dy_desejado)

    async def get_graham_price(self, stock: ModelStock):
        lpa = await self.data_provider.get_lpa(stock)
        vpa = await self.data_provider.get_vpa(stock)

        if not lpa:
            raise ValueError(f"LPA não encontrado para o ativo {stock}")
        
        if not vpa:
            raise ValueError(f"VPA não encontrado para o ativo {stock}")

        return self.graham_calculator.calculate_grahan_price(lpa, vpa)
        
    async def get_peter_lynch_price(self, stock: ModelStock, taxa_de_crescimento):
        lpa = await self.data_provider.get_lpa(stock)

        if not lpa:
            raise ValueError(f"LPA não encontrado para o ativo {stock}")

        return self.peter_lynch_calculator.calculate_peter_lynch(lpa, taxa_de_crescimento)
    
    async def get_projetivo_price(self, stock: ModelStock, pl_justo):
        lpa = await self.data_provider.get_lpa(stock)

        if not lpa:
            raise ValueError(f"LPA não encontrado para o ativo {stock}")

        return self.projetivo_calculator.calculate_projetivo(lpa, pl_justo)

    async def get_stock_data(self, stock: ModelStock):
        # ADICIONE O AWAIT AQUI NA FRENTE ↓
        data = await self.data_provider.get_fundamental_data(stock) 
        
        if not data:
            raise ValueError("Resposta vazia da API")
        
        return data

    async def get_dpa_indicators(self, stock: ModelStock):
        """Busca DPA atual e projetado e assegura que a estrutura de retorno exista."""
        indicators = await self.data_provider.get_dpa_indicators(stock)
        
        # Se todos os provedores falharem, retorna a estrutura zerada/indisponível
        if not indicators:
            import datetime
            agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return {
                "dpa_atual": {"valor": 0.0, "periodo_referencia": "TTM", "fonte": "N/A", "data_atualizacao": agora},
                "dpa_projetado": {"valor": None, "periodo_referencia": "N/A", "metodo": "indisponivel", "fonte": "N/A", "data_atualizacao": agora}
            }
            
        return indicators

    async def get_dfc_price(self, stock: ModelStock, fluxos: list, taxa_desconto: float, crescimento_perpetuo: float):
        # O SISTEMA DEVE BUSCAR ISSO AUTOMATICAMENTE:
        divida_liquida = await self.data_provider.get_divida_liquida(stock)
        numero_acoes = await self.data_provider.get_n_de_acoes(stock)

        if divida_liquida is None or numero_acoes is None:
             raise ValueError(f"Não foi possível buscar a dívida líquida ou número de ações para {stock.ticker}")

        if not fluxos:
            raise ValueError("A lista de fluxos de caixa não pode ser vazia.")
            
        if numero_acoes <= 0:
            raise ValueError("O número de ações deve ser maior que zero.")

        return self.dfc_calculator.calcular_preco_teto(
            fluxos=fluxos,
            taxa_desconto=taxa_desconto,
            crescimento_perpetuo=crescimento_perpetuo,
            divida_liquida=divida_liquida,
            numero_acoes=numero_acoes
        )

    # ==========================================================
    # Integrações Assets Formulas (Específicos por Ativo/Setor)
    # ==========================================================

    async def get_bbas_price(self, stock: ModelStock, roe_normalizado: float, taxa_livre_risco: float, premio_risco: float, crescimento_perpetuo: float):
        vpa = await self.data_provider.get_vpa(stock)
        
        if not vpa:
            raise ValueError(f"VPA não encontrado para o ativo {stock}")
            
        return self.bbas_calculator.calcular_preco_teto(
            vpa=vpa,
            roe_normalizado=roe_normalizado,
            taxa_livre_risco=taxa_livre_risco,
            premio_risco=premio_risco,
            crescimento_perpetuo=crescimento_perpetuo
        )

    async def get_bbse_price(self, stock: ModelStock, dividendos_5_anos: list, dy_minimo: float):
        # Provedor não traz a lista de 5 anos por padrão, o usuário informa
        if not dividendos_5_anos:
            raise ValueError("A lista de dividendos dos últimos 5 anos não pode estar vazia.")
            
        return self.bbse_calculator.calcular_preco_teto(
            dividendos_5_anos=dividendos_5_anos,
            dy_minimo=dy_minimo
        )

    async def get_brbi_price(self, stock: ModelStock, roe_normalizado: float, taxa_livre_risco: float, premio_risco: float, beta: float, crescimento_perpetuo: float):
        vpa = await self.data_provider.get_vpa(stock)
        
        if not vpa:
            raise ValueError(f"VPA não encontrado para o ativo {stock}")
            
        return self.brbi_calculator.calcular_preco_teto(
            vpa=vpa,
            roe_normalizado=roe_normalizado,
            taxa_livre_risco=taxa_livre_risco,
            premio_risco=premio_risco,
            beta=beta,
            crescimento_perpetuo=crescimento_perpetuo
        )

    async def get_fii_papel_price(self, stock: ModelStock, pct_cdi: float, pct_ipca: float, selic_atual: float, selic_normalizada: float, dividendos_12m: list, dy_minimo_aceitavel: float):
        preco_atual = await self.data_provider.get_price(stock)
        vp_cota = await self.data_provider.get_vpa(stock)
        
        if preco_atual is None:
            raise ValueError(f"Preço atual não encontrado para o ativo {stock}")
        if not vp_cota:
            raise ValueError(f"VP da cota (VPA) não encontrado para o ativo {stock}")
            
        return self.fii_papel_calculator.calcular_preco_teto(
            preco_atual=preco_atual,
            vp_cota=vp_cota,
            pct_cdi=pct_cdi,
            pct_ipca=pct_ipca,
            selic_atual=selic_atual,
            selic_normalizada=selic_normalizada,
            dividendos_12m=dividendos_12m,
            dy_minimo_aceitavel=dy_minimo_aceitavel
        )

    async def get_fii_tijolo_price(self, stock: ModelStock, ntnb_referencia: float, dividendo_anual_normalizado: float, estabilidade_renda: str, potencial_crescimento: str, qualidade_ativos: str, estresse_operacional: str):
        vp_cota = await self.data_provider.get_vpa(stock)
        
        if not vp_cota:
            raise ValueError(f"VP da cota (VPA) não encontrado para o ativo {stock}")
            
        return self.fii_tijolo_calculator.calcular_preco_teto(
            ntnb_referencia=ntnb_referencia,
            dividendo_anual_normalizado=dividendo_anual_normalizado,
            vp_cota=vp_cota,
            estabilidade_renda=estabilidade_renda,
            potencial_crescimento=potencial_crescimento,
            qualidade_ativos=qualidade_ativos,
            estresse_operacional=estresse_operacional
        )

    async def get_flry_price(self, stock: ModelStock, roe_normalizado: float, g_real: float, rf_real: float, erp: float):
        vpa = await self.data_provider.get_vpa(stock)
        
        if not vpa:
            raise ValueError(f"VPA não encontrado para o ativo {stock}")
            
        return self.flry_calculator.calcular_preco_teto(
            vpa=vpa,
            roe_normalizado=roe_normalizado,
            g_real=g_real,
            rf_real=rf_real,
            erp=erp
        )

    async def get_grnd_price(self, stock: ModelStock, roe_normalizado: float, selic_atual: float, premio_risco: float, ipca_esperado: float, g_real: float):
        vpa = await self.data_provider.get_vpa(stock)
        
        if not vpa:
            raise ValueError(f"VPA não encontrado para o ativo {stock}")
            
        return self.grnd_calculator.calcular_preco_teto(
            vpa=vpa,
            roe_normalizado=roe_normalizado,
            selic_atual=selic_atual,
            premio_risco=premio_risco,
            ipca_esperado=ipca_esperado,
            g_real=g_real
        )

    async def get_itsa_price(self, stock: ModelStock, participacoes_mercado: list, desconto_alvo: float):
        total_acoes_holding = await self.data_provider.get_n_de_acoes(stock)
        
        if total_acoes_holding is None or total_acoes_holding <= 0:
            raise ValueError(f"Número de ações não encontrado ou inválido para o ativo {stock.ticker}")
            
        if not participacoes_mercado:
            raise ValueError("A lista de participações a mercado não pode estar vazia.")
            
        return self.itsa_calculator.calcular_preco_teto(
            participacoes_mercado=participacoes_mercado,
            total_acoes_holding=total_acoes_holding,
            desconto_alvo=desconto_alvo
        )

    async def get_klbn_price(self, stock: ModelStock, historico_ebitda: list, multiplo_alvo_ev_ebitda: float):
        divida_liquida = await self.data_provider.get_divida_liquida(stock)
        total_acoes = await self.data_provider.get_n_de_acoes(stock)
        
        if divida_liquida is None or total_acoes is None or total_acoes <= 0:
            raise ValueError(f"Não foi possível buscar a dívida líquida ou número de ações para {stock.ticker}")
            
        if not historico_ebitda:
            raise ValueError("A lista com o histórico de EBITDA não pode estar vazia.")
            
        return self.klbn_calculator.calcular_preco_teto(
            historico_ebitda=historico_ebitda,
            divida_liquida=divida_liquida,
            total_acoes=total_acoes,
            multiplo_alvo_ev_ebitda=multiplo_alvo_ev_ebitda
        )

    async def get_petr_price(self, stock: ModelStock, taxa_livre_risco_real: float, premio_risco_especifico: float, crescimento_real: float, roe_normalizado: float):
        vpa = await self.data_provider.get_vpa(stock)
        
        if not vpa:
            raise ValueError(f"VPA não encontrado para o ativo {stock}")
            
        return self.petr_calculator.calcular_preco_teto(
            vpa=vpa,
            taxa_livre_risco_real=taxa_livre_risco_real,
            premio_risco_especifico=premio_risco_especifico,
            crescimento_real=crescimento_real,
            roe_normalizado=roe_normalizado
        )

    async def get_sapr_price(self, stock: ModelStock, roe_normalizado: float, crescimento_real: float, taxa_livre_risco_real: float, premio_risco: float):
        vpa = await self.data_provider.get_vpa(stock)
        
        if not vpa:
            raise ValueError(f"VPA não encontrado para o ativo {stock}")
            
        return self.sapr_calculator.calcular_preco_teto(
            vpa=vpa,
            roe_normalizado=roe_normalizado,
            crescimento_real=crescimento_real,
            taxa_livre_risco_real=taxa_livre_risco_real,
            premio_risco=premio_risco
        )

    async def get_taee_price(self, stock: ModelStock, historico_dividendos_5_anos: list, ntnb_real: float, premio_risco: float, ipca_esperado: float, crescimento_real: float):
        if not historico_dividendos_5_anos:
            raise ValueError("A lista de dividendos dos últimos 5 anos não pode estar vazia.")
            
        return self.taee_calculator.calcular_preco_teto(
            historico_dividendos_5_anos=historico_dividendos_5_anos,
            ntnb_real=ntnb_real,
            premio_risco=premio_risco,
            ipca_esperado=ipca_esperado,
            crescimento_real=crescimento_real
        )

    async def get_vale_price(self, stock: ModelStock, ebitda_ttm: float, multiplo_ev_ebitda: float):
        divida_liquida = await self.data_provider.get_divida_liquida(stock)
        total_acoes = await self.data_provider.get_n_de_acoes(stock)
        
        if divida_liquida is None or total_acoes is None or total_acoes <= 0:
            raise ValueError(f"Não foi possível buscar a dívida líquida ou número de ações para {stock.ticker}")
            
        return self.vale_calculator.calcular_preco_teto(
            ebitda_ttm=ebitda_ttm,
            divida_liquida=divida_liquida,
            total_acoes=total_acoes,
            multiplo_ev_ebitda=multiplo_ev_ebitda
        )

    async def get_wege_price(self, stock: ModelStock, g1: float, n1: int, g3: float, ke: float):
        lpa_base = await self.data_provider.get_lpa(stock)
        
        if not lpa_base:
            raise ValueError(f"LPA base não encontrado para o ativo {stock}")
            
        return self.wege_calculator.calcular_preco_teto(
            lpa_base=lpa_base,
            g1=g1,
            n1=n1,
            g3=g3,
            ke=ke
        )

    # ==========================================================
    # Moedas (AwesomeAPI)
    # ==========================================================

    async def get_currency(self, method_name: str, *args, **kwargs):
        """
        Acesso genérico a qualquer método de moeda do provider.
        Ex: get_currency("get_usd_to_brl"), get_currency("get_dxy")
        """
        data = await self.data_provider.get_currency(method_name, *args, **kwargs)

        if data is None:
            raise ValueError(f"Não foi possível obter a cotação ({method_name})")

        return data

    async def get_usd_to_brl(self):
        return await self.get_currency("get_usd_to_brl")

    async def get_eur_to_brl(self):
        return await self.get_currency("get_eur_to_brl")

    async def get_gbp_to_brl(self):
        return await self.get_currency("get_gbp_to_brl")

    async def get_chf_to_brl(self):
        return await self.get_currency("get_chf_to_brl")

    async def get_dxy(self):
        return await self.get_currency("get_dxy")

    # ==========================================================
    # Criptomoedas (CoinGecko)
    # ==========================================================

    async def get_crypto(self, method_name: str, *args, **kwargs):
        """
        Acesso genérico a qualquer método de cripto do provider.
        Ex: get_crypto("get_btc_to_usd"), get_crypto("get_all_to_usd")
        """
        data = await self.data_provider.get_crypto(method_name, *args, **kwargs)

        if data is None:
            raise ValueError(f"Não foi possível obter a cotação de cripto ({method_name})")

        return data

    async def get_btc_to_usd(self):
        return await self.get_crypto("get_btc_to_usd")

    async def get_eth_to_usd(self):
        return await self.get_crypto("get_eth_to_usd")

    async def get_all_crypto_to_usd(self):
        return await self.get_crypto("get_all_to_usd")

    # ==========================================================
    # Juros EUA (FRED)
    # ==========================================================

    async def get_interest_rate(self, method_name: str, *args, **kwargs):
        """
        Acesso genérico a qualquer método de juros do provider.
        Ex: get_interest_rate("get_treasury_10y")
        """
        data = await self.data_provider.get_interest_rate(method_name, *args, **kwargs)

        if data is None:
            raise ValueError(f"Não foi possível obter a taxa de juros ({method_name})")

        return data

    async def get_treasury_10y(self):
        return await self.get_interest_rate("get_treasury_10y")

    async def get_treasury_5y(self):
        return await self.get_interest_rate("get_treasury_5y")

    async def get_all_treasuries(self):
        return await self.get_interest_rate("get_all_treasuries")

    # ==========================================================
    # Índices Futuros (Yahoo Finance)
    # ==========================================================

    async def get_futures_index(self, method_name: str, *args, **kwargs):
        """
        Acesso genérico a qualquer método de índice futuro do provider.
        Ex: get_futures_index("get_sp500_fut")
        """
        data = await self.data_provider.get_futures_index(method_name, *args, **kwargs)

        if data is None:
            raise ValueError(f"Não foi possível obter o índice futuro ({method_name})")

        return data

    async def get_sp500_fut(self):
        return await self.get_futures_index("get_sp500_fut")

    async def get_nasdaq_fut(self):
        return await self.get_futures_index("get_nasdaq_fut")

    async def get_dow_jones_fut(self):
        return await self.get_futures_index("get_dow_jones_fut")

    async def get_all_futures(self):
        return await self.get_futures_index("get_all_futures")

    # ==========================================================
    # Índices (IBOV, SMLL, IFIX, S&P500, etc. — TwelveData)
    # ==========================================================

    async def get_market_index(self, method_name: str, *args, **kwargs):
        """
        Acesso genérico a qualquer método de índice (à vista) do provider.
        Ex: get_market_index("get_ibovespa"), get_market_index("get_sp500")
        """
        data = await self.data_provider.get_market_index(method_name, *args, **kwargs)

        if data is None:
            raise ValueError(f"Não foi possível obter o índice ({method_name})")

        return data

    async def get_ibovespa(self):
        return await self.get_market_index("get_ibovespa")

    async def get_sp500(self):
        return await self.get_market_index("get_sp500")

    async def get_all_indices(self):
        return await self.get_market_index("get_all_indices")

    # ==========================================================
    # Commodities (ainda sem provider plugado no DataProvider)
    # ==========================================================

    async def get_commodity(self, method_name: str, *args, **kwargs):
        """
        Genérico, pronto pra usar assim que um provider de commodities
        for adicionado ao DataProvider.
        """
        data = await self.data_provider.get_commodity(method_name, *args, **kwargs)

        if data is None:
            raise ValueError(f"Não foi possível obter a commodity ({method_name})")

        return data


assert_service = AssertService()