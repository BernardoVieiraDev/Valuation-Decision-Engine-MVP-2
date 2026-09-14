import aiohttp
from bs4 import BeautifulSoup


class FundamentusProvider:
    """
    Provider via scraping do Fundamentus (fundamentus.com.br).
    Só funciona para ações brasileiras.
    Não precisa de API key.
    """

    BASE_URL = "https://www.fundamentus.com.br/detalhes.php"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def safe_float(self, value: str) -> float | None:
        """Converte string do Fundamentus (ex: '5,98' ou '1.234,56') para float."""
        try:
            # Remove pontos de milhar e troca vírgula por ponto
            cleaned = value.strip().replace(".", "").replace(",", ".")
            # Remove % se houver
            cleaned = cleaned.replace("%", "").strip()
            result = float(cleaned)
            return result if result != 0.0 else None
        except (TypeError, ValueError, AttributeError):
            return None

    async def _get_page(self, ticker: str) -> BeautifulSoup | None:
        url = f"{self.BASE_URL}?papel={ticker.upper()}"
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        print(f"[FundamentusProvider] Status {response.status} para {ticker}")
                        return None
                    html = await response.text(encoding="latin-1")
                    return BeautifulSoup(html, "html.parser")
            except Exception as e:
                print(f"[FundamentusProvider] Erro HTTP: {e}")
                return None

    def _extract_field(self, soup: BeautifulSoup, label: str) -> str | None:
        """
        Encontra o valor de um campo pela label na tabela do Fundamentus.
        A página usa <span> com o texto da label e o valor fica no próximo <td>.
        """
        try:
            # Busca o span com o texto exato da label
            span = soup.find("span", string=lambda t: t and label.lower() in t.lower())
            if not span:
                return None
            # O valor fica no próximo td após o td que contém o span
            td_label = span.find_parent("td")
            if not td_label:
                return None
            td_value = td_label.find_next_sibling("td")
            if not td_value:
                return None
            return td_value.get_text(strip=True)
        except Exception:
            return None

    async def get_vpa(self, ticker: str) -> float | None:
        soup = await self._get_page(ticker)
        if not soup:
            return None
        raw = self._extract_field(soup, "VPA")
        vpa = self.safe_float(raw)
        print(f"[FundamentusProvider] VPA para {ticker}: {raw} → {vpa}")
        return vpa

    async def get_lpa(self, ticker: str) -> float | None:
        soup = await self._get_page(ticker)
        if not soup:
            return None
        raw = self._extract_field(soup, "LPA")
        lpa = self.safe_float(raw)
        print(f"[FundamentusProvider] LPA para {ticker}: {raw} → {lpa}")
        return lpa

    async def get_n_de_acoes(self, ticker: str) -> float | None:
        soup = await self._get_page(ticker)
        if not soup:
            return None
        raw = self._extract_field(soup, "Nro. Ações")
        n = self.safe_float(raw)
        print(f"[FundamentusProvider] Nro. Ações para {ticker}: {raw} → {n}")
        return n

    async def get_fundamental_data(self, ticker: str) -> dict | None:
        # Fundamentus não tem preço em tempo real confiável
        # Esse método existe só para manter compatibilidade com o DataProvider
        return None
    
    async def get_dividendos_medios(self, ticker: str) -> float | None:
        soup = await self._get_page(ticker)
        if not soup:
            return None

        # Pega o DY (ex: "8,52%") e o preço atual (ex: "34,52")
        raw_dy = self._extract_field(soup, "Div. Yield")
        raw_preco = self._extract_field(soup, "Cotação")

        dy = self.safe_float(raw_dy)      # já remove o %, vira ex: 8.52
        preco = self.safe_float(raw_preco)

        if dy is None or preco is None:
            print(f"[FundamentusProvider] Dados insuficientes para dividendos de {ticker}")
            return None

        # Converte DY de percentual para decimal e calcula dividendo/ação
        dividendo_por_acao = (dy / 100) * preco
        print(f"[FundamentusProvider] Dividendo/ação para {ticker}: {dividendo_por_acao}")
        return dividendo_por_acao


fundamentus_provider = FundamentusProvider()