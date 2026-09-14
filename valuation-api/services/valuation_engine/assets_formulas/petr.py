class CalculadoraPrecoTetoPETR4:

    def calcular_preco_teto(self, vpa, taxa_livre_risco_real, premio_risco_especifico, crescimento_real, roe_normalizado):
        # Ke = Taxa livre de risco (Rf) + Prêmio de risco Petrobras
        ke_real = taxa_livre_risco_real + premio_risco_especifico
        
        # P/VP Justo = (ROE normalizado - g) / (Ke - g)
        pvp_justo = (roe_normalizado - crescimento_real) / (ke_real - crescimento_real)
        
        # Preço Teto = P/VP Justo x VPA
        preco_teto = pvp_justo * vpa
        
        return preco_teto