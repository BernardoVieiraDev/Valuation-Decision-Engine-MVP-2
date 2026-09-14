import traceback
from enum import Enum

from dotenv import load_dotenv

from data_providers.api_provider.alpha_vantage import alpha_vantage
from data_providers.api_provider.awesomeapi_provider import awesomeapi_provider
from data_providers.api_provider.brapi_provider import brapi_provider
from data_providers.api_provider.coingecko_provider import coingecko_provider
from data_providers.api_provider.commodity_price import commodity_price_provider
from data_providers.api_provider.fred_api import fred_provider
from data_providers.api_provider.fundamentus_provider import fundamentus_provider
from data_providers.api_provider.twelvedata import twelvedata_provider
from data_providers.api_provider.yahoo_provider import yahoo_provider
from infra.cache.decorator import async_cache
from models.stock import ModelStock


class AssetType(Enum):
    STOCK = "stock"
    CURRENCY = "currency"
    CRYPTO = "crypto"
    INTEREST_RATE = "interest_rate"
    FUTURES_INDEX = "futures_index"
    MARKET_INDEX = "market_index"
    COMMODITY = "commodity"


class DataProvider:
    def __init__(self):
        # Providers de ações (fallback já existente)
        self.alpha_vantage = alpha_vantage
        self.brapi = brapi_provider
        self.yahoo = yahoo_provider
        self.fundamentus = fundamentus_provider

        # Providers dos novos tipos de dado
        self.awesomeapi = awesomeapi_provider
        self.coingecko = coingecko_provider
        self.fred = fred_provider
        self.twelvedata = twelvedata_provider
        self.commodity_price = commodity_price_provider

        # Mapa: AssetType -> lista de providers (ordem = ordem de fallback)
        self._market_providers: dict[AssetType, list] = {
            AssetType.CURRENCY: [self.awesomeapi],
            AssetType.CRYPTO: [self.coingecko],
            AssetType.INTEREST_RATE: [self.fred],
            AssetType.FUTURES_INDEX: [self.yahoo],
            AssetType.MARKET_INDEX: [self.twelvedata],
            AssetType.COMMODITY: [self.commodity_price],
        }

    # ==========================================================
    # Resolução de providers
    # ==========================================================

    def _resolve_stock_providers(self, stock: ModelStock):
        if stock.country == "Brazilian Stock":
            return [self.brapi, self.fundamentus, self.yahoo, self.alpha_vantage]

        if stock.country == "USA Stock":
            return [self.alpha_vantage, self.yahoo]

        raise ValueError("No provider available for this stock")

    def _resolve_market_providers(self, asset_type: AssetType):
        if asset_type == AssetType.STOCK:
            raise ValueError(
                "AssetType.STOCK precisa de um ModelStock — use os métodos "
                "get_price/get_fundamental_data/etc, não get_market_data."
            )

        providers = self._market_providers.get(asset_type)

        if not providers:
            raise ValueError(
                f"Nenhum provider configurado para o tipo de ativo: {asset_type}"
            )

        return providers

    # ==========================================================
    # Motor de fallback (genérico, sem dependência de ModelStock)
    # ==========================================================

    async def _safe_fetch_generic(
        self,
        providers: list,
        method_name: str,
        *args,
        log_context: str = "",
        **kwargs,
    ):
        print("\n==============================")
        print(f"FETCH START")
        print(f"Method: {method_name}")
        if log_context:
            print(f"Context: {log_context}")
        print("==============================\n")

        for provider in providers:

            provider_name = provider.__class__.__name__

            try:
                print(f"[TRY] Provider: {provider_name}")
                method = getattr(provider, method_name, None)

                if not method:
                    print(f"[SKIP] {provider_name} has no method {method_name}")
                    continue

                print(f"[CALL] {provider_name}.{method_name}(args={args}, kwargs={kwargs})")
                value = await method(*args, **kwargs)
                print(f"[SUCCESS] {provider_name} returned: {value}")

                if value is not None:
                    return value

                print(f"[WARN] {provider_name} returned None")

            except Exception as e:
                print("\n========== ERROR ==========")
                print(f"Provider: {provider_name}")
                print(f"Method: {method_name}")
                if log_context:
                    print(f"Context: {log_context}")
                print(f"Error: {repr(e)}")
                traceback.print_exc()
                print("===========================\n")
                continue

        print(f"[FAIL] No provider returned value for {method_name}")
        return None

    async def _safe_fetch(self, method_name: str, stock: ModelStock):
        """Mantido para os métodos de ação (usa ticker do ModelStock)."""
        providers = self._resolve_stock_providers(stock)
        log_context = f"Ticker: {stock.ticker} | Country: {stock.country}"
        return await self._safe_fetch_generic(
            providers, method_name, stock.ticker, log_context=log_context
        )

    # ==========================================================
    # API pública — Ações (comportamento inalterado)
    # ==========================================================
    
    @async_cache(prefix="data:price", ttl=300) # Preço muda rápido, TTL curto (5 min)
    async def get_price(self, stock: ModelStock):
        return await self._safe_fetch("get_price", stock)

    @async_cache(prefix="data:fundamental", ttl=86400) # 24 horas
    async def get_fundamental_data(self, stock: ModelStock):
        return await self._safe_fetch("get_fundamental_data", stock)

    @async_cache(prefix="data:lpa", ttl=86400) # 24 horas
    async def get_lpa(self, stock: ModelStock):
        return await self._safe_fetch("get_lpa", stock)
    
    @async_cache(prefix="data:dividendos", ttl=86400) # 24 horas
    async def get_dividendos_medios(self, stock: ModelStock):
        return await self._safe_fetch("get_dividendos_medios", stock)
    
    @async_cache(prefix="data:vpa", ttl=86400) # 24 horas
    async def get_vpa(self, stock: ModelStock):
        return await self._safe_fetch("get_vpa", stock)
    
    @async_cache(prefix="data:crescimento", ttl=86400) # 24 horas
    async def get_crescimento_lucro(self, stock: ModelStock):
        return await self._safe_fetch("get_crescimento_lucro_cagr", stock)
    
    @async_cache(prefix="data:fcl", ttl=86400) # 24 horas
    async def get_fluxo_caixa_livre(self, stock: ModelStock):
        return await self._safe_fetch("get_fluxo_caixa_livre", stock)
    
    @async_cache(prefix="data:divida", ttl=86400) # 24 horas
    async def get_divida_liquida(self, stock: ModelStock):
        return await self._safe_fetch("get_divida_liquida", stock)
    
    @async_cache(prefix="data:acoes", ttl=86400) # 24 horas
    async def get_n_de_acoes(self, stock: ModelStock):
        return await self._safe_fetch("get_n_de_acoes", stock)
    
    @async_cache(prefix="data:dpa", ttl=86400) # 24 horas
    async def get_dpa_indicators(self, stock: ModelStock):
        return await self._safe_fetch("get_dpa_indicators", stock)

    # ==========================================================
    # API pública — Novos tipos de ativo
    # ==========================================================
    
    # NÃO CACHEAR ESTA FUNÇÃO BASE! O cache fica nas funções específicas abaixo.
    async def get_market_data(self, asset_type: AssetType, method_name: str, *args, **kwargs):
        providers = self._resolve_market_providers(asset_type)
        return await self._safe_fetch_generic(
            providers, method_name, *args, log_context=f"AssetType: {asset_type}", **kwargs
        )

    @async_cache(prefix="market:currency", ttl=900) # 15 minutos
    async def get_currency(self, method_name: str, *args, **kwargs):
        return await self.get_market_data(AssetType.CURRENCY, method_name, *args, **kwargs)

    @async_cache(prefix="market:crypto", ttl=300) # 5 minutos (Cripto é mais volátil)
    async def get_crypto(self, method_name: str, *args, **kwargs):
        return await self.get_market_data(AssetType.CRYPTO, method_name, *args, **kwargs)

    @async_cache(prefix="market:interest", ttl=21600) # 6 horas (Juros não mudam a toda hora)
    async def get_interest_rate(self, method_name: str, *args, **kwargs):
        return await self.get_market_data(AssetType.INTEREST_RATE, method_name, *args, **kwargs)

    @async_cache(prefix="market:futures", ttl=900) # 15 minutos
    async def get_futures_index(self, method_name: str, *args, **kwargs):
        return await self.get_market_data(AssetType.FUTURES_INDEX, method_name, *args, **kwargs)

    @async_cache(prefix="market:indices", ttl=900) # 15 minutos
    async def get_market_index(self, method_name: str, *args, **kwargs):
        return await self.get_market_data(AssetType.MARKET_INDEX, method_name, *args, **kwargs)

    @async_cache(prefix="market:commodity", ttl=3600) # 1 hora
    async def get_commodity(self, method_name: str, *args, **kwargs):
        return await self.get_market_data(AssetType.COMMODITY, method_name, *args, **kwargs)