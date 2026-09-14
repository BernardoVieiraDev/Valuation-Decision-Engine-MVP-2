import httpx


class FredApiProvider:
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    # Séries disponíveis no FRED
    SERIES_IDS = {
        "TREASURY_10Y": "DGS10",  # Treasury 10 anos
        "TREASURY_5Y": "DGS5",    # Treasury 5 anos
    }

    def __init__(self, api_key: str):
        """
        A FRED API exige uma chave gratuita.
        Cadastro em: https://fredaccount.stlouisfed.org/apikeys
        """
        self.api_key = api_key

    async def _fetch_latest(self, series_id: str) -> float | None:
        """
        Busca o valor mais recente de uma série do FRED.
        A FRED não suporta múltiplas séries por requisição (diferente da
        AwesomeAPI e CoinGecko) — cada série exige uma chamada separada.
        """
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params)

            if response.status_code != 200:
                return None

            data = response.json()
            observations = data.get("observations", [])

            if not observations:
                return None

            value = observations[0].get("value")

            # O FRED retorna "." quando não há dado disponível para o dia
            if value in (None, "."):
                return None

            return float(value)

    async def get_treasury_10y(self):
        """Yield atual do Treasury americano de 10 anos (%)."""
        return await self._fetch_latest(self.SERIES_IDS["TREASURY_10Y"])

    async def get_treasury_5y(self):
        """Yield atual do Treasury americano de 5 anos (%)."""
        return await self._fetch_latest(self.SERIES_IDS["TREASURY_5Y"])

    async def get_all_treasuries(self) -> dict[str, float | None]:
        """
        Busca Treasury 10 anos e 5 anos.
        Retorna um dicionário, ex: {"TREASURY_10Y": 4.21, "TREASURY_5Y": 3.98}

        Nota: como o FRED exige uma requisição por série, aqui ainda são
        2 chamadas HTTP (sem opção de batch como nas outras APIs).
        """
        treasury_10y = await self.get_treasury_10y()
        treasury_5y = await self.get_treasury_5y()

        return {
            "TREASURY_10Y": treasury_10y,
            "TREASURY_5Y": treasury_5y,
        }

fred_provider = FredApiProvider(api_key="SUA_API_KEY_AQUI")