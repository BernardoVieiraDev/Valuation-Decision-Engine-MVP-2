from fastapi import APIRouter, HTTPException, Query
from models.stock import Acao, Stock
from services.valuation_engine.asset_service import assert_service

valuation_routes = APIRouter(prefix="/valuation")

@valuation_routes.get("/get-price/{ticker}")
async def get_asset_price(ticker: str):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco = await assert_service.get_price(stock_obj)
        
        return {
            "ticker": ticker_clean,
            "preco": preco
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")
    
@valuation_routes.get("/bazin/{ticker}")
async def get_bazin_price(ticker: str, dy_desejado: float):
    
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_bazin_price(stock_obj, dy_desejado)
        
        return {
            "ticker": ticker_clean,
            "metodo": "Bazin",
            "dy_desejado": dy_desejado,
            "preco_teto_bazin": preco_teto
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")
    
@valuation_routes.get("/graham/{ticker}")
async def get_graham_price(ticker: str):
    
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_graham_price(stock_obj)
        
        return {
            "ticker": ticker_clean,
            "metodo": "Graham",
            "preco_teto_graham": preco_teto
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")
    
@valuation_routes.get("/peter/{ticker}")
async def get_peter_lynch_price(ticker: str, taxa_de_crescimento: float):
    
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_peter_lynch_price(stock_obj, taxa_de_crescimento)
        
        return {
            "ticker": ticker_clean,
            "metodo": "Peter Lynch",
            "preco_teto_peter_lynch": preco_teto
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")
    
@valuation_routes.get("/projetivo/{ticker}")
async def get_projetivo_price(ticker: str, pl_justo: float):
    
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_projetivo_price(stock_obj, pl_justo)
        
        return {
            "ticker": ticker_clean,
            "metodo": "Projetivo",
            "preco_teto_projetivo": preco_teto
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")
    

@valuation_routes.get("/dfc/{ticker}")
async def get_dcf_price(
    ticker: str, 
    taxa_desconto: float, 
    crescimento_perpetuo: float, 
    fluxos: list[float] = Query(...)
):
    
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        # Agora passamos apenas as projeções para o service
        preco_teto = await assert_service.get_dfc_price(
            stock_obj, 
            fluxos, 
            taxa_desconto, 
            crescimento_perpetuo
        )
        
        return {
            "ticker": ticker_clean,
            "metodo": "DCF",
            "preco_teto_dcf": preco_teto
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")
    
@valuation_routes.get("/get-dpa/{ticker}")
async def get_dpa_info(ticker: str):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
    # Busca o valuation e os indicadores do DPA em paralelo
        dpa_info = await assert_service.get_dpa_indicators(stock_obj)
        
        return {
            "ticker": ticker_clean,
            "dpa_atual": dpa_info["dpa_atual"],
            "dpa_projetado": dpa_info["dpa_projetado"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")

# ==========================================================
# Novas Rotas (Assets Formulas)
# ==========================================================

@valuation_routes.get("/bbas/{ticker}")
async def get_bbas_price(
    ticker: str, 
    roe_normalizado: float, 
    taxa_livre_risco: float, 
    premio_risco: float, 
    crescimento_perpetuo: float
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_bbas_price(
            stock_obj, roe_normalizado, taxa_livre_risco, premio_risco, crescimento_perpetuo
        )
        return {
            "ticker": ticker_clean,
            "metodo": "BBAS",
            "preco_teto_bbas": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/bbse/{ticker}")
async def get_bbse_price(
    ticker: str, 
    dy_minimo: float, 
    dividendos_5_anos: list[float] = Query(...)
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_bbse_price(
            stock_obj, dividendos_5_anos, dy_minimo
        )
        return {
            "ticker": ticker_clean,
            "metodo": "BBSE",
            "preco_teto_bbse": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/brbi/{ticker}")
async def get_brbi_price(
    ticker: str, 
    roe_normalizado: float, 
    taxa_livre_risco: float, 
    premio_risco: float, 
    beta: float, 
    crescimento_perpetuo: float
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_brbi_price(
            stock_obj, roe_normalizado, taxa_livre_risco, premio_risco, beta, crescimento_perpetuo
        )
        return {
            "ticker": ticker_clean,
            "metodo": "BRBI",
            "preco_teto_brbi": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/fii-papel/{ticker}")
async def get_fii_papel_price(
    ticker: str, 
    pct_cdi: float, 
    pct_ipca: float, 
    selic_atual: float, 
    selic_normalizada: float, 
    dy_minimo_aceitavel: float, 
    dividendos_12m: list[float] = Query(...)
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_fii_papel_price(
            stock_obj, pct_cdi, pct_ipca, selic_atual, selic_normalizada, dividendos_12m, dy_minimo_aceitavel
        )
        return {
            "ticker": ticker_clean,
            "metodo": "FII Papel",
            "preco_teto_fii_papel": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/fii-tijolo/{ticker}")
async def get_fii_tijolo_price(
    ticker: str, 
    ntnb_referencia: float, 
    dividendo_anual_normalizado: float, 
    estabilidade_renda: str, 
    potencial_crescimento: str, 
    qualidade_ativos: str, 
    estresse_operacional: str
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_fii_tijolo_price(
            stock_obj, ntnb_referencia, dividendo_anual_normalizado, estabilidade_renda, potencial_crescimento, qualidade_ativos, estresse_operacional
        )
        return {
            "ticker": ticker_clean,
            "metodo": "FII Tijolo",
            "preco_teto_fii_tijolo": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/flry/{ticker}")
async def get_flry_price(
    ticker: str, 
    roe_normalizado: float, 
    g_real: float, 
    rf_real: float, 
    erp: float
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_flry_price(
            stock_obj, roe_normalizado, g_real, rf_real, erp
        )
        return {
            "ticker": ticker_clean,
            "metodo": "FLRY",
            "preco_teto_flry": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/grnd/{ticker}")
async def get_grnd_price(
    ticker: str, 
    roe_normalizado: float, 
    selic_atual: float, 
    premio_risco: float, 
    ipca_esperado: float, 
    g_real: float
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_grnd_price(
            stock_obj, roe_normalizado, selic_atual, premio_risco, ipca_esperado, g_real
        )
        return {
            "ticker": ticker_clean,
            "metodo": "GRND",
            "preco_teto_grnd": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/itsa/{ticker}")
async def get_itsa_price(
    ticker: str, 
    desconto_alvo: float, 
    participacoes_mercado: list[float] = Query(...)
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_itsa_price(
            stock_obj, participacoes_mercado, desconto_alvo
        )
        return {
            "ticker": ticker_clean,
            "metodo": "ITSA",
            "preco_teto_itsa": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/klbn/{ticker}")
async def get_klbn_price(
    ticker: str, 
    multiplo_alvo_ev_ebitda: float, 
    historico_ebitda: list[float] = Query(...)
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_klbn_price(
            stock_obj, historico_ebitda, multiplo_alvo_ev_ebitda
        )
        return {
            "ticker": ticker_clean,
            "metodo": "KLBN",
            "preco_teto_klbn": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/petr/{ticker}")
async def get_petr_price(
    ticker: str, 
    taxa_livre_risco_real: float, 
    premio_risco_especifico: float, 
    crescimento_real: float, 
    roe_normalizado: float
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_petr_price(
            stock_obj, taxa_livre_risco_real, premio_risco_especifico, crescimento_real, roe_normalizado
        )
        return {
            "ticker": ticker_clean,
            "metodo": "PETR",
            "preco_teto_petr": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/sapr/{ticker}")
async def get_sapr_price(
    ticker: str, 
    roe_normalizado: float, 
    crescimento_real: float, 
    taxa_livre_risco_real: float, 
    premio_risco: float
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_sapr_price(
            stock_obj, roe_normalizado, crescimento_real, taxa_livre_risco_real, premio_risco
        )
        return {
            "ticker": ticker_clean,
            "metodo": "SAPR",
            "preco_teto_sapr": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/taee/{ticker}")
async def get_taee_price(
    ticker: str, 
    ntnb_real: float, 
    premio_risco: float, 
    ipca_esperado: float, 
    crescimento_real: float, 
    historico_dividendos_5_anos: list[float] = Query(...)
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_taee_price(
            stock_obj, historico_dividendos_5_anos, ntnb_real, premio_risco, ipca_esperado, crescimento_real
        )
        return {
            "ticker": ticker_clean,
            "metodo": "TAEE",
            "preco_teto_taee": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/vale/{ticker}")
async def get_vale_price(
    ticker: str, 
    ebitda_ttm: float, 
    multiplo_ev_ebitda: float
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_vale_price(
            stock_obj, ebitda_ttm, multiplo_ev_ebitda
        )
        return {
            "ticker": ticker_clean,
            "metodo": "VALE",
            "preco_teto_vale": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")


@valuation_routes.get("/wege/{ticker}")
async def get_wege_price(
    ticker: str, 
    g1: float, 
    n1: int, 
    g3: float, 
    ke: float
):
    ticker_clean = ticker.upper()
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
    try:
        preco_teto = await assert_service.get_wege_price(
            stock_obj, g1, n1, g3, ke
        )
        return {
            "ticker": ticker_clean,
            "metodo": "WEGE",
            "preco_teto_wege": preco_teto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valuation: {str(e)}")