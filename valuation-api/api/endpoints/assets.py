from fastapi import APIRouter, HTTPException

from models.stock import Acao, Stock
from services.valuation_engine.asset_service import assert_service

assets_routes = APIRouter(prefix="/assets", tags=['assets'])

@assets_routes.get("/{ticker}")
async def get_fundamental_data(ticker: str):
    ticker_clean = ticker.upper()
    
    if ticker_clean.endswith(".SA") or (ticker_clean and ticker_clean[-1].isdigit()):
        stock_obj = Acao(ticker_clean)
    else:
        stock_obj = Stock(ticker_clean)
             
    data = await assert_service.get_stock_data(stock_obj)
             
    try:
        if not data:
            raise ValueError("Dados não encontrados na resposta da API")
            
        return {
            "name":  data.get('name', 'Empresa Desconhecida'), 
            "price": data.get('price', 0.0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar ativo: {str(e)}")