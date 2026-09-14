
class CalculadoraPrecoTetoBBAS:
    
    def calcular_preco_teto(self, vpa, roe_normalizado, taxa_livre_risco, premio_risco, crescimento_perpetuo):
        ke = taxa_livre_risco + premio_risco
        pvpa_justo = (roe_normalizado - crescimento_perpetuo) / (ke - crescimento_perpetuo)
        return pvpa_justo * vpa

# P/VPA Justo (ROE normalizado)
