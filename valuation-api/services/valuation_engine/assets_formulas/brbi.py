class CalculadoraPrecoTetoBRBI11:
    
    def calcular_preco_teto(self, vpa, roe_normalizado, taxa_livre_risco, premio_risco, beta, crescimento_perpetuo):
        """
        Calcula o preço teto pelo Método P/VPA Justo usando o Modelo de Gordon.
        O Ke (Custo de Capital Próprio) inclui a variável Beta nesta versão.
        """
        ke = taxa_livre_risco + (beta * premio_risco)
        pvpa_justo = (roe_normalizado - crescimento_perpetuo) / (ke - crescimento_perpetuo)
        preco_teto = pvpa_justo * vpa
        return preco_teto