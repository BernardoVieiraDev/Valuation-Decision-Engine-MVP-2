import aiohttp


class YahooFinanceProvider:
    # Tickers dos futuros de índices no Yahoo Finance (contratos "front month",
    # rolados automaticamente pelo próprio Yahoo).
    FUTURES_TICKERS = {
        "DOW_JONES": "YM=F",
        "SP500": "ES=F",
        "NASDAQ": "NQ=F",
        "RUSSELL_2000": "RTY=F",
        # Ibovespa Futuro NÃO existe no Yahoo Finance (contrato negociado só
        # na B3). O mais próximo disponível é o índice à vista (spot),
        # que NÃO é a mesma coisa que o futuro (pode ter diferença de pontos
        # por causa do "custo de carrego"). Usar com essa ressalva em mente.
        "IBOVESPA": "^BVSP",
    }

    def safe_float(self, value) -> float | None:
        try:
            result = float(value)
            return result if result != 0.0 else None
        except (TypeError, ValueError):
            return None

    async def _get_info(self, ticker: str) -> dict:
        import asyncio
        import yfinance as yf
        loop = asyncio.get_event_loop()

        def _fetch():
            t = yf.Ticker(ticker)
            return t.info

        info = await loop.run_in_executor(None, _fetch)
        return info

    def _normalize_ticker(self, ticker: str) -> str:
        if not ticker.endswith(".SA") and not ticker.endswith(".sa"):
            if len(ticker) <= 6 and ticker[-1].isdigit():
                return f"{ticker}.SA"
        return ticker

    async def get_vpa(self, ticker: str) -> float | None:
        normalized = self._normalize_ticker(ticker)
        try:
            info = await self._get_info(normalized)
            vpa = self.safe_float(info.get("bookValue"))
            print(f"[YahooFinanceProvider] bookValue para {normalized}: {vpa}")
            return vpa
        except Exception as e:
            print(f"[YahooFinanceProvider] Erro ao buscar VPA: {e}")
            return None

    async def get_lpa(self, ticker: str) -> float | None:
        normalized = self._normalize_ticker(ticker)
        try:
            info = await self._get_info(normalized)
            lpa = self.safe_float(info.get("trailingEps"))
            print(f"[YahooFinanceProvider] trailingEps para {normalized}: {lpa}")
            return lpa
        except Exception as e:
            print(f"[YahooFinanceProvider] Erro ao buscar LPA: {e}")
            return None

    async def get_n_de_acoes(self, ticker: str) -> float | None:
        normalized = self._normalize_ticker(ticker)
        try:
            info = await self._get_info(normalized)
            n = self.safe_float(info.get("sharesOutstanding"))
            print(f"[YahooFinanceProvider] sharesOutstanding para {normalized}: {n}")
            return n
        except Exception as e:
            print(f"[YahooFinanceProvider] Erro ao buscar nº de ações: {e}")
            return None

    async def get_fundamental_data(self, ticker: str) -> dict | None:
        normalized = self._normalize_ticker(ticker)
        try:
            info = await self._get_info(normalized)
            name = info.get("longName") or info.get("shortName")
            price = self.safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
            if not name or not price:
                return None
            return {"name": name, "price": price}
        except Exception as e:
            print(f"[YahooFinanceProvider] Erro ao buscar dados fundamentais: {e}")
            return None

    async def get_price(self, ticker: str):
        data = await self.get_fundamental_data(ticker)
        if not data:
            raise RuntimeError(f"Ativo não encontrado (function get_price)")
        return {
            "price": data['price']
        }

    async def get_dpa_indicators(self, ticker: str) -> dict | None:
        normalized = self._normalize_ticker(ticker)
        try:
            import asyncio
            import datetime
            import yfinance as yf

            info = await self._get_info(normalized)
            agora = datetime.datetime.now(datetime.timezone.utc).isoformat()

            def _fetch_dividends():
                t = yf.Ticker(normalized)
                return t.dividends

            loop = asyncio.get_event_loop()
            dividends = await loop.run_in_executor(None, _fetch_dividends)

            dpa_atual_valor = 0.0
            if dividends is not None and not dividends.empty:
                cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)
                divs_series = dividends
                if divs_series.index.tzinfo is None:
                    divs_series.index = divs_series.index.tz_localize("UTC")
                ttm_divs = divs_series[divs_series.index >= cutoff]
                dpa_atual_valor = round(float(ttm_divs.sum()), 4)

            dpa_atual = {
                "valor": dpa_atual_valor,
                "periodo_referencia": "TTM",
                "fonte": "yfinance",
                "data_atualizacao": agora
            }

            dpa_projetado_valor = None
            metodo_proj = "indisponivel"
            fonte_proj = "N/A"

            lpa_projetado = self.safe_float(info.get("forwardEps"))
            payout_ratio = self.safe_float(info.get("payoutRatio"))

            if payout_ratio is None:
                lpa_atual = self.safe_float(info.get("trailingEps"))
                if lpa_atual and dpa_atual_valor and lpa_atual > 0:
                    payout_ratio = dpa_atual_valor / lpa_atual


            if payout_ratio is not None and payout_ratio > 1.0:
                payout_ratio = 1.0

            if lpa_projetado is not None and payout_ratio is not None:
                dpa_projetado_valor = lpa_projetado * payout_ratio
                metodo_proj = "calculado_payout_x_lpa"
                fonte_proj = "yfinance"

            dpa_projetado = {
                "valor": dpa_projetado_valor,
                "periodo_referencia": str(datetime.datetime.now().year + 1),
                "metodo": metodo_proj,
                "fonte": fonte_proj,
                "data_atualizacao": agora
            }

            print(f"[YahooFinanceProvider] DPA Indicators para {normalized} carregados.")
            return {
                "dpa_atual": dpa_atual,
                "dpa_projetado": dpa_projetado
            }

        except Exception as e:
            print(f"[YahooFinanceProvider] Erro ao buscar DPA indicators para {ticker}: {e}")
            return None

    # ------------------------------------------------------------------
    # Índices Futuros
    # ------------------------------------------------------------------

    async def _get_futures_price(self, ticker: str) -> float | None:
        """
        Busca o preço atual de um contrato futuro pelo ticker do Yahoo
        Finance (ex: 'ES=F', 'NQ=F', 'YM=F', 'RTY=F').
        Não passa pelo _normalize_ticker, pois futuros não seguem o
        padrão de ações brasileiras (.SA).
        """
        try:
            info = await self._get_info(ticker)
            price = self.safe_float(
                info.get("regularMarketPrice") or info.get("currentPrice")
            )
            print(f"[YahooFinanceProvider] preço futuro para {ticker}: {price}")
            return price
        except Exception as e:
            print(f"[YahooFinanceProvider] Erro ao buscar futuro {ticker}: {e}")
            return None

    async def get_dow_jones_fut(self) -> float | None:
        """Cotação atual do futuro do Dow Jones (E-mini Dow, YM=F)."""
        return await self._get_futures_price(self.FUTURES_TICKERS["DOW_JONES"])

    async def get_sp500_fut(self) -> float | None:
        """Cotação atual do futuro do S&P 500 (E-mini S&P 500, ES=F)."""
        return await self._get_futures_price(self.FUTURES_TICKERS["SP500"])

    async def get_nasdaq_fut(self) -> float | None:
        """Cotação atual do futuro do Nasdaq (E-mini Nasdaq 100, NQ=F)."""
        return await self._get_futures_price(self.FUTURES_TICKERS["NASDAQ"])

    async def get_russell2000_fut(self) -> float | None:
        """Cotação atual do futuro do Russell 2000 (E-mini Russell, RTY=F)."""
        return await self._get_futures_price(self.FUTURES_TICKERS["RUSSELL_2000"])

    async def get_ibovespa_fut(self) -> float | None:
        """
        ATENÇÃO: o Yahoo Finance não tem o contrato futuro do Ibovespa
        (negociado só na B3, ticker WINFUT/INDFUT). O que este método
        retorna é o índice Ibovespa À VISTA (^BVSP), como aproximação.

        Isso pode divergir do valor real do futuro por causa do "custo
        de carrego" (diferença entre o preço futuro e o à vista, que
        varia com taxa de juros e dividendos esperados até o vencimento).
        Para o dado real do futuro, seria necessário uma fonte que cubra
        a B3 (ex: dados da própria bolsa ou provedores como Bloomberg,
        TradingView com plano B3, etc.).
        """
        return await self._get_futures_price(self.FUTURES_TICKERS["IBOVESPA"])

    async def get_all_futures(self) -> dict[str, float | None]:
        """
        Busca todos os futuros de índices de uma vez.
        Retorna um dicionário, ex:
        {"DOW_JONES": 53179.0, "SP500": ..., "NASDAQ": ..., "RUSSELL_2000": ..., "IBOVESPA": ...}

        Nota: cada ticker exige uma chamada separada ao yfinance (não há
        batch nativo aqui), então são 5 chamadas no total.
        """
        return {
            "DOW_JONES": await self.get_dow_jones_fut(),
            "SP500": await self.get_sp500_fut(),
            "NASDAQ": await self.get_nasdaq_fut(),
            "RUSSELL_2000": await self.get_russell2000_fut(),
            "IBOVESPA": await self.get_ibovespa_fut(),
        }


yahoo_provider = YahooFinanceProvider()