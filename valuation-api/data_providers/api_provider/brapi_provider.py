import asyncio
import datetime
import os

import aiohttp
from brapi import AsyncBrapi
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BRAPI_API_KEY")

if not API_KEY:
    raise ValueError("Variável de ambiente BRAPI_API_KEY não definida!")


class BrapiProvider:

    BASE_URL = "https://brapi.dev/api/quote/"

    def __init__(self):
        self.client = AsyncBrapi(api_key=API_KEY)
        self.headers = { "Authorization": f"Bearer {API_KEY}" }


    async def _get_financial_data_field(self, ticker: str, field: str):
        url = f"{self.BASE_URL}{ticker}?modules=financialData"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    dados = await response.json()

                    resultado = dados["results"][0]
                    financial_data = resultado.get("financialData", {})
                    valor = financial_data.get(field)

                    moeda = financial_data.get("financialCurrency")


                    print("Empresa:", resultado.get("longName"))
                    print(f"{field}:", valor)
                    print(f"Data dos dados: {financial_data.get('updatedAt')}")
                    print(f"Moeda: {moeda}")

                    return valor

            except aiohttp.ClientError as e:
                print("Erro HTTP:", e)
                return None
            except (KeyError, IndexError):
                print("Erro ao processar resposta da API")
                return None
            

            
    async def _get_default_key_statistics(self, ticker: str, field: str):
        url = (
            f"{self.BASE_URL}{ticker}"
            f"?modules=defaultKeyStatistics,defaultKeyStatisticsHistory,defaultKeyStatisticsHistoryQuarterly"
            f"&token={API_KEY}"
        )

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    dados = await response.json()

                    resultado = dados["results"][0]
                    dados_atuais = resultado.get("defaultKeyStatistics", {})
                    valor = dados_atuais.get(field)

                    print("Empresa:", resultado.get("longName"))
                    print(f"{field}:", valor)

                    return valor

            except aiohttp.ClientError as e:
                print("Erro HTTP:", e)
                return None
            except (KeyError, IndexError):
                print("Erro ao processar resposta da API")
                return None
            
    async def _get_valueAddedHistory(self, ticker: str, field: str):
            # We request the valueAddedHistory module
            url = f"{self.BASE_URL}{ticker}?modules=valueAddedHistory"

            async with aiohttp.ClientSession(headers=self.headers) as session:
                try:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        dados = await response.json()

                        resultado = dados["results"][0]
                        
                        # FIX: valueAddedHistory is a LIST, not a DICT
                        historico = resultado.get("valueAddedHistory", [])
                        
                        if not historico or not isinstance(historico, list):
                            print(f"Histórico não encontrado ou inválido para {ticker}")
                            return None

                        # Extract the values from the list
                        valores = []
                        for report in historico:
                            val = report.get(field)
                            if val is not None:
                                valores.append(float(val))
                        
                        if not valores:
                            return None

                        # Calculate the average (Bazin uses the average of the last years)
                        # We can limit to 5 years if desired, or use all available history
                        valores = valores[:5] # Optional: Limit to recent 5 entries if API sorts new->old
                        media = sum(valores) / len(valores)

                        print("Empresa:", resultado.get("longName"))
                        print(f"Média calculada para {field} ({len(valores)} períodos):", media)

                        return media

                except aiohttp.ClientError as e:
                    print("Erro HTTP:", e)
                    return None
                except (KeyError, IndexError, TypeError) as e:
                    print(f"Erro ao processar resposta da API: {e}")
                    return None



    ####################
    async def get_price(self, ticker: str):
        data = await self.get_fundamental_data(ticker)
        if not data:
            raise RuntimeError(f"Ativo não encontrado (function get_price)")
        return {
            "price": data['price']
        }

    async def get_fundamental_data(self, ticker: str):
        quote = await self.client.quote.retrieve(ticker)
        preco_atual = quote.results[0].regular_market_price  # type: ignore
        nome_empresa =  quote.results[0].short_name  # type: ignore
        print(f"Preço atual: {preco_atual}")

        if not nome_empresa or not preco_atual:
            return None
        return {
            "name": nome_empresa,
            "price": preco_atual,

        }


    async def get_lpa(self, ticker: str):
        quote = await self.client.quote.retrieve(ticker)
        lpa = quote.results[0].earnings_per_share  # type: ignore
        return lpa


    async def get_crescimento_lucro(self, ticker: str):
        return await self._get_financial_data_field(
            ticker,
            "earningsGrowth"
        )


    async def get_fluxo_de_caixa_livre(self, ticker: str):
        return await self._get_financial_data_field(
            ticker,
            "freeCashflow"
        )


    async def get_divida_liquida(self, ticker: str):
        total_debt = await self._get_financial_data_field(
            ticker,
            "totalDebt"
        )
        total_cash = await self._get_financial_data_field(
            ticker,
            "totalCash"
        )

        if total_debt is None or total_cash is None:
            print("Não foi possível calcular a Dívida Líquida")
            return None

        divida_liquida = total_debt - total_cash

        print(f"Dívida Bruta: {total_debt}")
        print(f"Caixa Total: {total_cash}")
        print(f"Dívida Líquida: {divida_liquida}")

        return divida_liquida
    
    async def get_n_de_acoes(self, ticker:str):
        return await self._get_default_key_statistics(
            ticker,
            "sharesOutstanding"
        )

    async def get_vpa(self, ticker: str):
        return await self._get_default_key_statistics(
            ticker,
            "bookValue"
        )
    
    async def get_dividendos_medios(self, ticker: str):
        div = await self._get_valueAddedHistory(ticker, "dividends")
        jcp = await self._get_valueAddedHistory(ticker, "interestOnOwnEquity")
        n_de_acoes = await self._get_default_key_statistics(ticker, "sharesOutstanding")

        if div is None or jcp is None or n_de_acoes is None:
            print("Dados insuficientes para calcular dividendos médios")
            return None

        return (div + jcp) / n_de_acoes
    

    async def get_dpa_indicators(self, ticker: str):
        url = (
            f"{self.BASE_URL}{ticker}"
            f"?modules=defaultKeyStatistics,financialData"
            f"&dividends=true"
            f"&token={API_KEY}"
        )

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    dados = await response.json()

                    if not dados.get("results"):
                        return None

                    resultado = dados["results"][0]
                    stats = resultado.get("defaultKeyStatistics", {})
                    fin_data = resultado.get("financialData", {})

                    agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    
                    # 1. DPA ATUAL (TTM)
                    # Tenta pegar a taxa anual de dividendos. Se for None, assume 0 (não paga)
                    dpa_atual_valor = stats.get("trailingAnnualDividendRate")
                    if dpa_atual_valor is None:
                        dpa_atual_valor = 0.0

                    dpa_atual = {
                        "valor": dpa_atual_valor,
                        "periodo_referencia": "TTM",
                        "fonte": "brapi.dev",
                        "data_atualizacao": agora
                    }

                    # 2. DPA PROJETADO (Fallback: payout_ratio * lpa_projetado)
                    dpa_projetado_valor = None
                    metodo_proj = "indisponivel"
                    fonte_proj = "N/A"
                    
                    # Tenta extrair LPA projetado (forwardEps) e Payout Ratio
                    lpa_projetado = stats.get("forwardEps") or fin_data.get("forwardEps")
                    payout_ratio = stats.get("payoutRatio") or fin_data.get("payoutRatio")

                    if lpa_projetado is not None and payout_ratio is not None:
                        dpa_projetado_valor = lpa_projetado * payout_ratio
                        metodo_proj = "calculado_payout_x_lpa"
                        fonte_proj = "brapi.dev"

                    dpa_projetado = {
                        "valor": dpa_projetado_valor,
                        "periodo_referencia": str(datetime.datetime.now().year + 1),
                        "metodo": metodo_proj,
                        "fonte": fonte_proj,
                        "data_atualizacao": agora
                    }

                    return {
                        "dpa_atual": dpa_atual,
                        "dpa_projetado": dpa_projetado
                    }

            except Exception as e:
                print(f"Erro ao buscar DPA indicators para {ticker}: {e}")
                return None



brapi_provider = BrapiProvider()

async def main():
    ticker = "PETR4"

    print(await brapi_provider.get_lpa(ticker))


if __name__ == "__main__":
    asyncio.run(main())

