class CalculadoraPrecoTetoSAPR4:

    def calcular_preco_teto(self, vpa, roe_normalizado, crescimento_real, taxa_livre_risco_real, premio_risco):
        # Ke = Taxa livre de risco real + Prêmio de risco
        ke_real = taxa_livre_risco_real + premio_risco
        
        # P/VP Justo = (ROE normalizado - g) / (Ke - g)
        pvp_justo = (roe_normalizado - crescimento_real) / (ke_real - crescimento_real)
        
        # Preço Teto
        preco_teto = pvp_justo * vpa
        
        return preco_teto