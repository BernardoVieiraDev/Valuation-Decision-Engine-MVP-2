class CalculadoraPrecoTetoTAEE11:

    def calcular_preco_teto(self, historico_dividendos_5_anos, ntnb_real, premio_risco, ipca_esperado, crescimento_real):
        # D0: Dividendo normalizado (média dos últimos 5 anos)
        d0 = sum(historico_dividendos_5_anos) / len(historico_dividendos_5_anos)
        
        # Ke nominal: Taxa de desconto = Juro real + Prêmio de risco + Inflação esperada
        ke_nominal = ntnb_real + premio_risco + ipca_esperado
        
        # g nominal: Crescimento perpétuo = Inflação esperada + Crescimento real
        g_nominal = ipca_esperado + crescimento_real
        
        # D1: Dividendo projetado para o próximo ano = D0 * (1 + g nominal)
        d1 = d0 * (1 + g_nominal)
        
        # PREÇO-TETO: Método DDM / Gordon Growth = D1 / (Ke - g)
        preco_teto = d1 / (ke_nominal - g_nominal)
        
        return preco_teto