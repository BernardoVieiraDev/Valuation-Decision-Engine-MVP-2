import httpx


class CoinGeckoProvider:
    BASE_URL = "https://api.coingecko.com/api/v3/simple/price"

    # Mapeamento símbolo -> id usado pela CoinGecko
    COIN_IDS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "XRP": "ripple",
        "SOL": "solana",
        "ADA": "cardano",
        "BNB": "binancecoin",
    }

    async def _fetch_many(self, coin_ids: list[str], currency: str = "usd") -> dict[str, float | None]:
        """
        Busca o preço de várias criptomoedas de uma vez, em uma única requisição.
        Retorna um dicionário {coin_id: preço} (ou {coin_id: None} se não encontrado).
        """
        url = f"{self.BASE_URL}?ids={','.join(coin_ids)}&vs_currencies={currency}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            if response.status_code != 200:
                return {coin_id: None for coin_id in coin_ids}

            data = response.json()

        return {
            coin_id: data[coin_id].get(currency) if coin_id in data else None
            for coin_id in coin_ids
        }

    async def get_crypto_price(self, coin_id: str, currency: str = "usd") -> float | None:
        """
        Busca o preço de uma única criptomoeda.
        Ex: coin_id = 'bitcoin', 'ethereum', 'solana'
        """
        result = await self._fetch_many([coin_id], currency)
        return result[coin_id]

    async def get_btc_to_usd(self):
        """Cotação atual do Bitcoin em Dólar (USD)."""
        return await self.get_crypto_price(self.COIN_IDS["BTC"])

    async def get_eth_to_usd(self):
        """Cotação atual do Ethereum em Dólar (USD)."""
        return await self.get_crypto_price(self.COIN_IDS["ETH"])

    async def get_xrp_to_usd(self):
        """Cotação atual do XRP (Ripple) em Dólar (USD)."""
        return await self.get_crypto_price(self.COIN_IDS["XRP"])

    async def get_sol_to_usd(self):
        """Cotação atual do Solana em Dólar (USD)."""
        return await self.get_crypto_price(self.COIN_IDS["SOL"])

    async def get_ada_to_usd(self):
        """Cotação atual do Cardano em Dólar (USD)."""
        return await self.get_crypto_price(self.COIN_IDS["ADA"])

    async def get_bnb_to_usd(self):
        """Cotação atual da Binance Coin em Dólar (USD)."""
        return await self.get_crypto_price(self.COIN_IDS["BNB"])

    async def get_all_to_usd(self) -> dict[str, float | None]:
        """
        Busca BTC, ETH, XRP, SOL, ADA e BNB em Dólar (USD) numa única requisição.
        Retorna um dicionário com os símbolos como chave, ex:
        {"BTC": 65000.0, "ETH": 3400.0, ...}
        """
        ids = list(self.COIN_IDS.values())
        prices = await self._fetch_many(ids, "usd")

        return {
            symbol: prices[coin_id]
            for symbol, coin_id in self.COIN_IDS.items()
        }


coingecko_provider = CoinGeckoProvider()