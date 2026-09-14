from fastapi import APIRouter, HTTPException
from services.market_service import market_service
from services.valuation_engine.asset_service import assert_service

market_routes = APIRouter(prefix="/market", tags=['market'])


# ==========================================================
# Criptomoedas (CoinGecko via asset_service) - rotas especificas
# IMPORTANTE: precisam vir ANTES da rota generica /crypto/{coin_id}
# ==========================================================

@market_routes.get("/crypto/btc")
async def get_btc_to_usd():
    try:
        price = await assert_service.get_btc_to_usd()
        return {"asset": "BTC", "currency": "USD", "price": price}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/crypto/eth")
async def get_eth_to_usd():
    try:
        price = await assert_service.get_eth_to_usd()
        return {"asset": "ETH", "currency": "USD", "price": price}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/crypto/all")
async def get_all_crypto_to_usd():
    try:
        data = await assert_service.get_all_crypto_to_usd()
        return {"currency": "USD", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/crypto/{coin_id}")
async def get_crypto(coin_id: str, currency: str = "brl"):
    """
    Retorna o preco da criptomoeda informada.
    Por padrao retorna em BRL, mas voce pode passar ?currency=usd
    """
    try:
        price = await market_service.get_crypto_price(coin_id, currency)
        return {
            "asset": coin_id.capitalize(),
            "currency": currency.upper(),
            "price": price
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ==========================================================
# Moedas (AwesomeAPI via asset_service)
# ==========================================================

@market_routes.get("/currency/usd")
async def get_usd():
    """
    Retorna a cotacao atual do Dolar em Reais.
    """
    try:
        price = await market_service.get_usd_price()
        return {
            "asset": "USD",
            "currency": "BRL",
            "price": price
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/currency/eur")
async def get_eur():
    try:
        price = await assert_service.get_eur_to_brl()
        return {"asset": "EUR", "currency": "BRL", "price": price}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/currency/gbp")
async def get_gbp():
    try:
        price = await assert_service.get_gbp_to_brl()
        return {"asset": "GBP", "currency": "BRL", "price": price}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/currency/chf")
async def get_chf():
    try:
        price = await assert_service.get_chf_to_brl()
        return {"asset": "CHF", "currency": "BRL", "price": price}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/currency/dxy")
async def get_dxy():
    try:
        price = await assert_service.get_dxy()
        return {"asset": "DXY", "price": price}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ==========================================================
# Juros EUA (FRED)
# ==========================================================

@market_routes.get("/rates/treasury-10y")
async def get_treasury_10y():
    try:
        rate = await assert_service.get_treasury_10y()
        return {"asset": "US10Y", "rate": rate}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/rates/treasury-5y")
async def get_treasury_5y():
    try:
        rate = await assert_service.get_treasury_5y()
        return {"asset": "US5Y", "rate": rate}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/rates/all")
async def get_all_treasuries():
    try:
        data = await assert_service.get_all_treasuries()
        return {"data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ==========================================================
# Indices Futuros (Yahoo Finance)
# ==========================================================

@market_routes.get("/futures/sp500")
async def get_sp500_fut():
    try:
        data = await assert_service.get_sp500_fut()
        return {"asset": "SP500_FUT", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/futures/nasdaq")
async def get_nasdaq_fut():
    try:
        data = await assert_service.get_nasdaq_fut()
        return {"asset": "NASDAQ_FUT", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/futures/dow-jones")
async def get_dow_jones_fut():
    try:
        data = await assert_service.get_dow_jones_fut()
        return {"asset": "DOW_JONES_FUT", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/futures/all")
async def get_all_futures():
    try:
        data = await assert_service.get_all_futures()
        return {"data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ==========================================================
# Indices (IBOV, SMLL, IFIX, S&P500, etc. - TwelveData)
# ==========================================================

@market_routes.get("/indices/ibovespa")
async def get_ibovespa():
    try:
        data = await assert_service.get_ibovespa()
        return {"asset": "IBOVESPA", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/indices/sp500")
async def get_sp500():
    try:
        data = await assert_service.get_sp500()
        return {"asset": "SP500", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/indices/all")
async def get_all_indices():
    try:
        data = await assert_service.get_all_indices()
        return {"data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ==========================================================
# Commodities (ainda sem provider plugado no DataProvider)
# ==========================================================

@market_routes.get("/commodities/ouro")
async def get_ouro():
    try:
        data = await assert_service.get_commodity("get_ouro")
        return {"asset": "OURO", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/commodities/prata")
async def get_prata():
    try:
        data = await assert_service.get_commodity("get_prata")
        return {"asset": "PRATA", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/commodities/petroleo-wti")
async def get_petroleo_wti():
    try:
        data = await assert_service.get_commodity("get_petroleo_wti")
        return {"asset": "PETROLEO_WTI", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/commodities/petroleo-brent")
async def get_petroleo_brent():
    try:
        data = await assert_service.get_commodity("get_petroleo_brent")
        return {"asset": "PETROLEO_BRENT", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/commodities/cobre")
async def get_cobre():
    try:
        data = await assert_service.get_commodity("get_cobre")
        return {"asset": "COBRE", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/commodities/ferro")
async def get_ferro():
    try:
        data = await assert_service.get_commodity("get_ferro")
        return {"asset": "FERRO", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@market_routes.get("/commodities/all")
async def get_all_commodities():
    try:
        data = await assert_service.get_commodity("get_all_commodities")
        return {"data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")