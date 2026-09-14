class CalculadoraPrecoTetoBBSE3:
    
    def calcular_preco_teto(self, dividendos_5_anos, dy_minimo):
        """
        Calcula o preço teto pelo Método Bazin Ajustado com base na média 
        dos dividendos dos últimos 5 anos e o DY mínimo exigido.
        """
        media_dividendos = sum(dividendos_5_anos) / len(dividendos_5_anos)
        preco_teto = media_dividendos / dy_minimo
        return preco_teto

#  Método Bazin Ajustado (Dividendo Normalizado)