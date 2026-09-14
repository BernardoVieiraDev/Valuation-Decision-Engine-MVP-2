import httpx


class AwesomeApiProvider:
    BASE_URL = "https://economia.awesomeapi.com.br/last"

    async def _fetch_many(self, pairs: list[str]) -> dict[str, float | None]:
        """
        Busca vários pares '*-BRL' de uma vez em uma única requisição.
        Retorna um dicionário {par: bid} (ou {par: None} se não encontrado).
        """
        url = f"{self.BASE_URL}/{','.join(pairs)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            if response.status_code != 200:
                return {pair: None for pair in pairs}

            data = response.json()

        result: dict[str, float | None] = {}
        for pair in pairs:
            key = pair.replace("-", "")
            result[pair] = float(data[key]["bid"]) if key in data else None

        return result

    async def _fetch(self, pair: str) -> float | None:
        """Busca a cotação 'bid' de um único par '*-BRL'."""
        result = await self._fetch_many([pair])
        return result[pair]

    async def get_usd_to_brl(self):
        """Cotação atual do Dólar em Reais (BRL)."""
        return await self._fetch("USD-BRL")

    async def get_eur_to_brl(self):
        """Cotação atual do Euro em Reais (BRL)."""
        return await self._fetch("EUR-BRL")

    async def get_gbp_to_brl(self):
        """Cotação atual da Libra Esterlina em Reais (BRL)."""
        return await self._fetch("GBP-BRL")

    async def get_chf_to_brl(self):
        """Cotação atual do Franco Suíço em Reais (BRL)."""
        return await self._fetch("CHF-BRL")

    async def get_usd_to_eur(self):
        """
        Cotação do Dólar em Euro, derivada via BRL:
        USD/EUR = (USD/BRL) / (EUR/BRL)
        """
        rates = await self._fetch_many(["USD-BRL", "EUR-BRL"])
        usd_brl, eur_brl = rates["USD-BRL"], rates["EUR-BRL"]

        if usd_brl is None or eur_brl is None:
            return None

        return usd_brl / eur_brl

    async def get_usd_to_gbp(self):
        """
        Cotação do Dólar em Libra Esterlina, derivada via BRL:
        USD/GBP = (USD/BRL) / (GBP/BRL)
        """
        rates = await self._fetch_many(["USD-BRL", "GBP-BRL"])
        usd_brl, gbp_brl = rates["USD-BRL"], rates["GBP-BRL"]

        if usd_brl is None or gbp_brl is None:
            return None

        return usd_brl / gbp_brl

    async def get_usd_to_chf(self):
        """
        Cotação do Dólar em Franco Suíço, derivada via BRL:
        USD/CHF = (USD/BRL) / (CHF/BRL)
        """
        rates = await self._fetch_many(["USD-BRL", "CHF-BRL"])
        usd_brl, chf_brl = rates["USD-BRL"], rates["CHF-BRL"]

        if usd_brl is None or chf_brl is None:
            return None

        return usd_brl / chf_brl

    async def get_dxy(self):
        """
        Calcula o índice DXY (US Dollar Index) usando a fórmula oficial do
        ICE, a partir dos pares componentes (EUR, JPY, GBP, CAD, SEK, CHF),
        todos derivados via BRL:

        DXY = 50.14348112
              * (EUR/USD)^-0.576
              * (USD/JPY)^0.136
              * (GBP/USD)^-0.119
              * (USD/CAD)^0.091
              * (USD/SEK)^0.042
              * (USD/CHF)^0.036
        """
        pairs = ["USD-BRL", "EUR-BRL", "JPY-BRL", "GBP-BRL", "CAD-BRL", "SEK-BRL", "CHF-BRL"]
        rates = await self._fetch_many(pairs)

        if any(value is None for value in rates.values()):
            return None

        usd_brl = rates["USD-BRL"]
        eur_brl = rates["EUR-BRL"]
        jpy_brl = rates["JPY-BRL"]
        gbp_brl = rates["GBP-BRL"]
        cad_brl = rates["CAD-BRL"]
        sek_brl = rates["SEK-BRL"]
        chf_brl = rates["CHF-BRL"]

        if (
            usd_brl is None
            or eur_brl is None
            or jpy_brl is None
            or gbp_brl is None
            or cad_brl is None
            or sek_brl is None
            or chf_brl is None
        ):
            return None

        eur_usd = eur_brl / usd_brl
        usd_jpy = usd_brl / jpy_brl
        gbp_usd = gbp_brl / usd_brl
        usd_cad = usd_brl / cad_brl
        usd_sek = usd_brl / sek_brl
        usd_chf = usd_brl / chf_brl

        dxy = (
            50.14348112
            * eur_usd ** -0.576
            * usd_jpy ** 0.136
            * gbp_usd ** -0.119
            * usd_cad ** 0.091
            * usd_sek ** 0.042
            * usd_chf ** 0.036
        )

        return dxy


awesomeapi_provider = AwesomeApiProvider()