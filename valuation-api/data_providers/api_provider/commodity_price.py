import os

import httpx
from dotenv import load_dotenv

# Garante que o .env foi carregado antes de ler a variável, independente
# da ordem de import de outros módulos do projeto (ex: data_provider.py
# que importa load_dotenv mas não a chama).
load_dotenv()

COMMODITY_PRICE_API_KEY = os.getenv("COMMODITY_PRICE_API_KEY")

if not COMMODITY_PRICE_API_KEY:
    print(
        "[commodity_price] AVISO: variável de ambiente COMMODITY_PRICE_API_KEY "
        "não encontrada. Confira se ela está definida no seu arquivo .env."
    )

class CommodityPriceApiProvider:
    BASE_URL = "https://api.commoditypriceapi.com/v2/rates/latest"
    TIMEOUT = 15

    # Símbolos usados pela CommodityPriceAPI (preços diretos em USD, sem
    # necessidade de inverter nada como em outras APIs de commodities).
    SYMBOLS = {
        "ouro": "XAU",
        "prata": "XAG",
        "petroleo_wti": "WTIOIL-FUT",
        "petroleo_brent": "BRENTOIL-FUT",
        "cobre": "HG-SPOT",
        "ferro": "TIOC",  # Minério de ferro 62% Fe CFR China (benchmark padrão)
    }

    def __init__(self, api_key):
        """
        A CommodityPriceAPI exige uma chave de API.
        Cadastro (com plano free) em: https://commoditypriceapi.com
        """
        self.api_key = api_key

    async def _fetch_many(self, keys: list[str]) -> dict[str, dict | None]:
        """
        Busca a cotação de uma ou mais commodities de uma vez, em uma única
        requisição HTTP.

        Retorna um dicionário {key: dados} (ou {key: None} se não encontrado
        ou em caso de erro), onde 'dados' contém price, unit e currency.
        """
        symbols = [self.SYMBOLS[key] for key in keys if key in self.SYMBOLS]
        reverse = {v: k for k, v in self.SYMBOLS.items()}

        params = {
            "apiKey": self.api_key,
            "symbols": ",".join(symbols),
        }

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(self.BASE_URL, params=params)

            if response.status_code != 200:
                print(
                    f"[CommodityPriceApiProvider] HTTP {response.status_code} "
                    f"ao buscar {symbols}: {response.text}"
                )
                return {key: None for key in keys}

            data = response.json()

        if not data.get("success"):
            print(
                f"[CommodityPriceApiProvider] API retornou success=False "
                f"para {symbols}: {data}"
            )
            return {key: None for key in keys}

        rates = data.get("rates", {})
        metadata = data.get("metadata", {})

        result: dict[str, dict | None] = {key: None for key in keys}

        for symbol, price in rates.items():
            key = reverse.get(symbol)
            if key is None:
                continue

            try:
                result[key] = {
                    "symbol": symbol,
                    "price": float(price),
                    "unit": metadata.get(symbol, {}).get("unit"),
                    "currency": metadata.get(symbol, {}).get("quote"),
                }
            except (TypeError, ValueError):
                result[key] = None

        missing = [key for key, value in result.items() if value is None]
        if missing:
            print(
                f"[CommodityPriceApiProvider] Sem dados retornados para: {missing} "
                f"(symbols pedidos: {symbols} | rates recebidos: {list(rates.keys())})"
            )

        return result

    async def get_commodity(self, key: str) -> dict | None:
        """Busca uma única commodity pela chave (ex: 'ouro', 'petroleo_wti')."""
        result = await self._fetch_many([key])
        return result.get(key)

    async def get_ouro(self) -> dict | None:
        """Cotação atual do Ouro (XAU), em USD por onça troy."""
        return await self.get_commodity("ouro")

    async def get_prata(self) -> dict | None:
        """Cotação atual da Prata (XAG), em USD por onça troy."""
        return await self.get_commodity("prata")

    async def get_petroleo_wti(self) -> dict | None:
        """Cotação atual do Petróleo WTI, em USD por barril."""
        return await self.get_commodity("petroleo_wti")

    async def get_petroleo_brent(self) -> dict | None:
        """Cotação atual do Petróleo Brent, em USD por barril."""
        return await self.get_commodity("petroleo_brent")

    async def get_cobre(self) -> dict | None:
        """Cotação atual do Cobre (spot), em USD por libra."""
        return await self.get_commodity("cobre")

    async def get_ferro(self) -> dict | None:
        """
        Cotação atual do minério de Ferro 62% Fe CFR China (TIOC),
        benchmark padrão de mercado, em USD por tonelada.
        """
        return await self.get_commodity("ferro")

    async def get_all_commodities(self) -> dict[str, dict | None]:
        """
        Busca todas as commodities cadastradas em SYMBOLS numa única
        requisição HTTP. Retorna um dicionário {chave: dados}, ex:
        {"ouro": {...}, "prata": {...}, ...}
        """
        return await self._fetch_many(list(self.SYMBOLS.keys()))


commodity_price_provider = CommodityPriceApiProvider(api_key=COMMODITY_PRICE_API_KEY)