import os

import requests
from groq import Groq


class PlaybookAPIClient:
    """
    Cliente para consumir a API de Valuation rodando internamente no Django via ASGI.
    """
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")

    def get_price(self, ticker: str) -> float:
        url = f"{self.base_url}/valuation/get-price/{ticker}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        preco_raw = data.get("preco", 0.0)
        
        # Se o preço vier dentro de um dicionário, extraímos o valor
        if isinstance(preco_raw, dict):
            return float(preco_raw.get("price", 0.0))
        return float(preco_raw) if preco_raw is not None else 0.0

    def get_graham_price(self, ticker: str) -> float:
        url = f"{self.base_url}/valuation/graham/{ticker}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        raw = data.get("preco_teto_graham", 0.0)
        
        # CORREÇÃO AQUI: Se a API retornar um dicionário dentro da chave
        if isinstance(raw, dict):
            # Tenta pegar a chave 'price' ou 'preco_teto_graham' dentro do dict aninhado
            return float(raw.get("price", raw.get("preco_teto_graham", 0.0)))
        
        return float(raw) if raw is not None else 0.0

    # (Exemplo) Se for usar Bazin também, a lógica é a mesma
    def get_bazin_price(self, ticker: str, dy_desejado: float) -> float:
        url = f"{self.base_url}/valuation/bazin/{ticker}"
        response = requests.get(url, params={"dy_desejado": dy_desejado})
        response.raise_for_status()
        data = response.json()
        
        raw = data.get("preco_teto_bazin", 0.0)
        if isinstance(raw, dict):
            return float(raw.get("price", raw.get("preco_teto_bazin", 0.0)))
        return float(raw) if raw is not None else 0.0

    def get_peter_lynch_price(self, ticker: str, taxa_de_crescimento: float) -> float:
        url = f"{self.base_url}/valuation/peter/{ticker}"
        response = requests.get(url, params={"taxa_de_crescimento": taxa_de_crescimento})
        response.raise_for_status()
        data = response.json()
        
        raw = data.get("preco_teto_peter_lynch", 0.0)
        if isinstance(raw, dict):
            return float(raw.get("price", raw.get("preco_teto_peter_lynch", 0.0)))
        return float(raw) if raw is not None else 0.0
    
    def get_dfc_price(self, ticker: str, taxa_desconto: float, crescimento_perpetuo: float, fluxos: list[float]) -> float:
        url = f"{self.base_url}/valuation/dfc/{ticker}"
        
        # Passando os parâmetros exigidos pela API
        params = {
            "taxa_desconto": taxa_desconto,
            "crescimento_perpetuo": crescimento_perpetuo,
            "fluxos": fluxos
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        raw = data.get("preco_teto_dcf", 0.0)
        if isinstance(raw, dict):
            return float(raw.get("price", raw.get("preco_teto_dcf", 0.0)))
        return float(raw) if raw is not None else 0.0

    def get_projetivo_price(self, ticker: str, pl_justo: float) -> float:
        url = f"{self.base_url}/valuation/projetivo/{ticker}"
        
        # O FastAPI exige o pl_justo
        response = requests.get(url, params={"pl_justo": pl_justo})
        
        response.raise_for_status()
        data = response.json()
        
        raw = data.get("preco_teto_projetivo", 0.0)
        if isinstance(raw, dict):
            return float(raw.get("price", raw.get("preco_teto_projetivo", 0.0)))
        return float(raw) if raw is not None else 0.0
    
    def get_dpa(self, ticker: str) -> dict:
        url = f"{self.base_url}/valuation/get-dpa/{ticker}"
        response = requests.get(url)
        response.raise_for_status()
        
        return response.json()

    def get_asset_formula_price(self, method: str, ticker: str, params: dict) -> float:
        """Helper genérico para chamar os novos endpoints de valuation específico."""
        url = f"{self.base_url}/valuation/{method}/{ticker}"
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # A API retorna chaves como "preco_teto_bbas", "preco_teto_petr", etc.
        key = f"preco_teto_{method.replace('-', '_')}"
        raw = data.get(key, 0.0)
        
        if isinstance(raw, dict):
            return float(raw.get("price", raw.get(key, 0.0)))
        return float(raw) if raw is not None else 0.0
