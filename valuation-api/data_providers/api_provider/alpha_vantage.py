import os

import aiohttp
from dotenv import load_dotenv

"""

- Limitar Alpha Vantage  (Acho que so pode uma requisição por vez, verificar isso)

- Trackear quantas requisições já fiz e quantas ainda posso fazer

"""

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

if not ALPHA_VANTAGE_API_KEY:
    raise ValueError("Variável de ambiente ALPHA_VANTAGE_API_KEY não definida!")


class AlphaVantageProvider:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str):
        self.api_key = api_key

    # ========================
    # Infra
    # ========================
    async def _fetch(self, params: dict) -> dict:
        async with aiohttp.ClientSession() as session:
            params["apikey"] = self.api_key
            async with session.get(self.BASE_URL, params=params) as response:
                content_type = response.headers.get("Content-Type", "")

                text = await response.text()

                if response.status != 200:
                    raise RuntimeError(
                        f"Erro Alpha Vantage {response.status}: {text[:200]}"
                    )

                if "application/json" not in content_type:
                    raise RuntimeError(
                        f"Resposta não é JSON. Content-Type={content_type}. Body={text[:200]}"
                    )
                
                data = await response.json()

                # Alpha Vantage costuma devolver JSON de erro silencioso
                if "Note" in data:
                    raise RuntimeError(f"Rate limit Alpha Vantage: {data['Note']}")

                if "Error Message" in data:
                    raise RuntimeError(f"Erro Alpha Vantage: {data['Error Message']}")

                print("Feito por ALpha Vantage API")
                
                return data

    def safe_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


    async def _get_overview(self, ticker: str) -> dict:
        return await self._fetch({
            "function": "OVERVIEW",
            "symbol": ticker
        })

    async def _get_income_statement(self, ticker: str) -> dict:
        return await self._fetch({
            "function": "INCOME_STATEMENT",
            "symbol": ticker
        })

    async def _get_balance_sheet(self, ticker: str) -> dict:
        return await self._fetch({
            "function": "BALANCE_SHEET",
            "symbol": ticker
        })

    async def _get_cash_flow(self, ticker: str) -> dict:
        return await self._fetch({
            "function": "CASH_FLOW",
            "symbol": ticker
        })
    
    async def _get_global_quote(self, ticker: str) -> dict:
        return await self._fetch({
            "function": "GLOBAL_QUOTE",
            "symbol": ticker
        })
    
    async def get_price(self, ticker: str):
        data = await self.get_fundamental_data(ticker)
        if not data:
            raise RuntimeError(f"Ativo não encontrado (function get_price)")
        return {
            "price": data['price']
        }

    async def get_fundamental_data(self, ticker: str):
        overview = await self._get_overview(ticker)
        quote = await self._get_global_quote(ticker)

        name = overview.get("Name")
        price = self.safe_float(
            quote.get("Global Quote", {}).get("05. price")
        )

        if not name or price == 0:
            return None

        return {
            "name": name,
            "price": price
        }



    async def get_lpa(self, ticker: str):
        overview = await self._get_overview(ticker)
        return self.safe_float(overview.get("EPS"))


    async def get_vpa(self, ticker: str):
        overview = await self._get_overview(ticker)
        return self.safe_float(overview.get("BookValue"))


    async def get_n_de_acoes(self, ticker: str):
        overview = await self._get_overview(ticker)
        return self.safe_float(overview.get("SharesOutstanding"))


    async def get_crescimento_lucro_cagr(self, ticker: str):
        income = await self._get_income_statement(ticker)
        reports = income.get("annualReports", [])

        # Precisamos de 6 anos para calcular o CAGR de 5 anos de distância
        if len(reports) < 6:
            return None

        reports = sorted(
            reports,
            key=lambda x: x.get("fiscalDateEnding", ""),
            reverse=True
        )

        lucro_atual = self.safe_float(reports[0].get("netIncome"))
        lucro_base = self.safe_float(reports[5].get("netIncome")) # Lucro de 5 anos atrás

        # O CAGR não funciona matematicamente se o ano base for negativo ou zero
        if lucro_base <= 0 or lucro_atual <= 0:
             # Fallback: se não dá pra calcular o CAGR, você pode querer 
             # retornar None, ou usar uma taxa conservadora padrão (ex: inflação)
            return None 

        anos = 5
        # Fórmula do CAGR: (Valor Final / Valor Inicial) ^ (1 / n) - 1
        cagr = ((lucro_atual / lucro_base) ** (1 / anos)) - 1

        return cagr * 100


    async def get_fluxo_caixa_livre(self, ticker: str):
        cash_flow = await self._get_cash_flow(ticker)
        reports = cash_flow.get("annualReports", [])
        
        if not reports:
            return 0.0
        
        latest_report = reports[0]
        
        fco = self.safe_float(latest_report.get("operatingCashflow"))
        capex = self.safe_float(latest_report.get("capitalExpenditures"))
        
        return fco - capex

    async def get_divida_liquida(self, ticker: str):
        balance = await self._get_balance_sheet(ticker)
        latest = balance.get("annualReports", [{}])[0]

        short_term_debt = self.safe_float(latest.get("shortTermDebt"))
        long_term_debt = self.safe_float(latest.get("longTermDebt"))

        total_debt = short_term_debt + long_term_debt

        cash = self.safe_float(
            latest.get("cashAndCashEquivalentsAtCarryingValue")
        )
        short_term_investments = self.safe_float(
            latest.get("shortTermInvestments")
        )

        liquidity = cash + short_term_investments

        return total_debt - liquidity


    async def get_dividendos_medios(self, ticker: str):
        # Alpha Vantage não é boa para isso
        return None
    

    async def get_dpa_indicators(self, ticker: str):
        try:
            overview = await self._get_overview(ticker)
            
            # Se não encontrar o ticker, retorna None para disparar o fallback da sua arquitetura
            if not overview or "Symbol" not in overview:
                return None
                
            import datetime
            agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # 1. DPA ATUAL (TTM)
            # Alpha Vantage traz no campo "DividendPerShare"
            dpa_atual_valor = self.safe_float(overview.get("DividendPerShare"))

            dpa_atual = {
                "valor": dpa_atual_valor,
                "periodo_referencia": "TTM",
                "fonte": "Alpha Vantage",
                "data_atualizacao": agora
            }

            # 2. DPA PROJETADO
            # O endpoint OVERVIEW gratuito não traz estimativa de consenso nem Forward EPS.
            # Sendo assim, cumprimos a regra de manter indisponível.
            dpa_projetado = {
                "valor": None,
                "periodo_referencia": str(datetime.datetime.now().year + 1),
                "metodo": "indisponivel",
                "fonte": "N/A",
                "data_atualizacao": agora
            }

            print(f"[AlphaVantageProvider] DPA Indicators para {ticker} carregados.")
            return {
                "dpa_atual": dpa_atual,
                "dpa_projetado": dpa_projetado
            }
            
        except Exception as e:
            print(f"[AlphaVantageProvider] Erro ao buscar DPA indicators para {ticker}: {e}")
            return None


alpha_vantage = AlphaVantageProvider(ALPHA_VANTAGE_API_KEY)

import asyncio


async def main():
    ticker = "AAPL"

    print(await alpha_vantage.get_lpa(ticker))

if __name__ == "__main__":
    asyncio.run(main())



"""

Crescimento do lucro:	Alpha Vantage (cálculo) TA PEGANDO SO UM ANO TEM QUE PEGAR MAUIS
Fluxo de caixa livre:	Alpha Vantage   TA PEGANDO O ANO DE 2025 MAS TEM QUE SER ULTIMOS 12 MESES
Dívida líquida: 	    Alpha Vantage   VALOR EXATO NAO FOI PEGO MAS ANALISANDO VARIOS SITES TODOS TEM VALORES DIFERENTES POREM RELATIVAMENTE PROXIMOS


Dividendos médios:  	brapi
LPA:	                Alpha Vantage           FEITO
Nº de ações:        	Alpha Vantage   100% CORRETO
VPA:                	Alpha Vantage   CERTO POREM FOI ARREDONDADO (DE 5,98 PARA 6) acho bom n ser

"""