import httpx
import os


TWELVE_DATA_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


class TwelveDataProvider:
    BASE_URL = "https://api.twelvedata.com"
    TIMEOUT = 15

    SYMBOLS = {
        "ibovespa": "IBOV",
        "small_caps": "SMLL",
        "ifix": "IFIX",

        "sp500": "GSPC",
        "vix": "VIX",
        "dow_jones": "DJI",
        "nasdaq": "IXIC",
        "russell_2000": "RUT",
        "sp_tsx": "GSPTSE",

        "ftse_100": "FTSE",
        "dax": "GDAXI",
        "cac_40": "FCHI",
        "euro_stoxx_50": "STOXX50E",
        "ibex_35": "IBEX",
        "smi": "SSMI",

        "nikkei_225": "N225",
        "topix": "TOPX",
        "hang_seng": "HSI",
        "shanghai": "SSEC",
        "shenzhen": "SZCOMP",
        "kospi": "KOSPI",
        "nifty_50": "NIFTY",
        "sensex": "SENSEX",
        "asx_200": "AXJO",

        "msci_world": "URTH",
        "msci_em": "EEM",
        "ftse_all_world": "VT",
        "ewz": "EWZ",
        "rare_earth": "REMX",
    }

    def __init__(self, api_key):
        self.api_key = api_key

    async def _fetch_quotes(self, keys: list[str]) -> dict[str, dict | None]:

        symbols = [self.SYMBOLS[key] for key in keys if key in self.SYMBOLS]
        reverse = {v: k for k, v in self.SYMBOLS.items()}

        params = {
            "symbol": ",".join(symbols),
            "apikey": self.api_key,
        }

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(f"{self.BASE_URL}/quote", params=params)

            if response.status_code != 200:
                return {key: None for key in keys}

            data = response.json()

        # Quando só um símbolo é pedido, a Twelve Data retorna um dict único
        # em vez de uma lista — normalizamos aqui.
        if isinstance(data, dict) and "symbol" in data:
            data = [data]
        elif not isinstance(data, list):
            return {key: None for key in keys}

        result: dict[str, dict | None] = {key: None for key in keys}

        for item in data:
            key = reverse.get(item.get("symbol"))
            if key is None:
                continue

            try:
                result[key] = {
                    "symbol": item["symbol"],
                    "name": item.get("name"),
                    "price": float(item["close"]),
                    "change": float(item["change"]),
                    "percent_change": float(item["percent_change"]),
                    "currency": item.get("currency"),
                    "exchange": item.get("exchange"),
                }
            except (KeyError, TypeError, ValueError):
                result[key] = None

        return result

    async def get_index(self, key: str) -> dict | None:
        """Busca um único índice pela chave (ex: 'ibovespa', 'sp500', 'nasdaq')."""
        result = await self._fetch_quotes([key])
        return result.get(key)

    # ------------------------------------------------------------------
    # Brasil
    # ------------------------------------------------------------------

    async def get_ibovespa(self) -> dict | None:
        """Índice Ibovespa (Brasil)."""
        return await self.get_index("ibovespa")

    async def get_small_caps(self) -> dict | None:
        """Índice Small Caps (Brasil)."""
        return await self.get_index("small_caps")

    async def get_ifix(self) -> dict | None:
        """Índice de Fundos Imobiliários (IFIX, Brasil)."""
        return await self.get_index("ifix")

    # ------------------------------------------------------------------
    # Estados Unidos / América do Norte
    # ------------------------------------------------------------------

    async def get_sp500(self) -> dict | None:
        """Índice S&P 500 (EUA)."""
        return await self.get_index("sp500")

    async def get_vix(self) -> dict | None:
        """Índice de volatilidade VIX (EUA)."""
        return await self.get_index("vix")

    async def get_dow_jones(self) -> dict | None:
        """Índice Dow Jones Industrial Average (EUA)."""
        return await self.get_index("dow_jones")

    async def get_nasdaq(self) -> dict | None:
        """Índice Nasdaq Composite (EUA)."""
        return await self.get_index("nasdaq")

    async def get_russell_2000(self) -> dict | None:
        """Índice Russell 2000 (EUA)."""
        return await self.get_index("russell_2000")

    async def get_sp_tsx(self) -> dict | None:
        """Índice S&P/TSX Composite (Canadá)."""
        return await self.get_index("sp_tsx")

    # ------------------------------------------------------------------
    # Europa
    # ------------------------------------------------------------------

    async def get_ftse_100(self) -> dict | None:
        """Índice FTSE 100 (Reino Unido)."""
        return await self.get_index("ftse_100")

    async def get_dax(self) -> dict | None:
        """Índice DAX (Alemanha)."""
        return await self.get_index("dax")

    async def get_cac_40(self) -> dict | None:
        """Índice CAC 40 (França)."""
        return await self.get_index("cac_40")

    async def get_euro_stoxx_50(self) -> dict | None:
        """Índice Euro Stoxx 50 (Zona do Euro)."""
        return await self.get_index("euro_stoxx_50")

    async def get_ibex_35(self) -> dict | None:
        """Índice IBEX 35 (Espanha)."""
        return await self.get_index("ibex_35")

    async def get_smi(self) -> dict | None:
        """Índice Swiss Market Index (Suíça)."""
        return await self.get_index("smi")

    # ------------------------------------------------------------------
    # Ásia / Pacífico
    # ------------------------------------------------------------------

    async def get_nikkei_225(self) -> dict | None:
        """Índice Nikkei 225 (Japão)."""
        return await self.get_index("nikkei_225")

    async def get_topix(self) -> dict | None:
        """Índice TOPIX (Japão)."""
        return await self.get_index("topix")

    async def get_hang_seng(self) -> dict | None:
        """Índice Hang Seng (Hong Kong)."""
        return await self.get_index("hang_seng")

    async def get_shanghai(self) -> dict | None:
        """Índice Shanghai Composite (China)."""
        return await self.get_index("shanghai")

    async def get_shenzhen(self) -> dict | None:
        """Índice Shenzhen Component (China)."""
        return await self.get_index("shenzhen")

    async def get_kospi(self) -> dict | None:
        """Índice KOSPI (Coreia do Sul)."""
        return await self.get_index("kospi")

    async def get_nifty_50(self) -> dict | None:
        """Índice Nifty 50 (Índia)."""
        return await self.get_index("nifty_50")

    async def get_sensex(self) -> dict | None:
        """Índice Sensex (Índia)."""
        return await self.get_index("sensex")

    async def get_asx_200(self) -> dict | None:
        """Índice ASX 200 (Austrália)."""
        return await self.get_index("asx_200")

    # ------------------------------------------------------------------
    # Globais / ETFs
    # ------------------------------------------------------------------

    async def get_msci_world(self) -> dict | None:
        """ETF que replica o índice MSCI World (mercados desenvolvidos)."""
        return await self.get_index("msci_world")

    async def get_msci_em(self) -> dict | None:
        """ETF que replica o índice MSCI Emerging Markets."""
        return await self.get_index("msci_em")

    async def get_ftse_all_world(self) -> dict | None:
        """ETF que replica o índice FTSE All-World."""
        return await self.get_index("ftse_all_world")

    async def get_ewz(self) -> dict | None:
        """ETF iShares MSCI Brazil (EWZ)."""
        return await self.get_index("ewz")

    async def get_rare_earth(self) -> dict | None:
        """ETF de terras raras e metais estratégicos (REMX)."""
        return await self.get_index("rare_earth")


    async def get_all_indices(self) -> dict[str, dict | None]:
        return await self._fetch_quotes(list(self.SYMBOLS.keys()))


twelvedata_provider = TwelveDataProvider(api_key=TWELVE_DATA_API_KEY)