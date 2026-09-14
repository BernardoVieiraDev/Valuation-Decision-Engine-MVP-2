class BazinCalculator:

    def calculate_bazin_price(self, dividendos_12m, dy_desejado=8) -> float:
        if dividendos_12m is None or dividendos_12m <= 0:
            raise ValueError("Dividendos insuficientes ou zerados para o cálculo de Bazin.")
            
        # Converte a porcentagem (ex: 8) para decimal (ex: 0.08) internamente
        preco_teto = dividendos_12m / (dy_desejado / 100)
        return preco_teto