from data_providers.api_provider.coingecko_provider import coingecko_provider
from data_providers.api_provider.awesomeapi_provider import awesomeapi_provider

class MarketService:
    def __init__(self):
        self.crypto_provider = coingecko_provider
        self.currency_provider = awesomeapi_provider

    async def get_crypto_price(self, coin_id: str, currency: str = "brl"):
        # Garante que o ID vai em letras minúsculas (padrão CoinGecko)
        coin_id = coin_id.lower() 
        price = await self.crypto_provider.get_crypto_price(coin_id, currency)
        
        if price is None:
            raise ValueError(f"Não foi possível buscar o preço para a criptomoeda '{coin_id}'. Verifique o nome/id.")
        return price

    async def get_usd_price(self):
        price = await self.currency_provider.get_usd_to_brl()
        
        if price is None:
            raise ValueError("Não foi possível buscar a cotação do Dólar no momento.")
        return price

market_service = MarketService()