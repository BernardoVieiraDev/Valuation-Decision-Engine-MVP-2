class CalculadoraPrecoTetoGRND3:

    def calcular_preco_teto(self, vpa, roe_normalizado, selic_atual, premio_risco, ipca_esperado, g_real):
        """
        Calcula o preço-teto nominal pelo Método de Gordon (P/VP Justo).
        :param vpa: Valor Patrimonial por Ação.
        :param roe_normalizado: Retorno sobre o PL sustentável.
        :param selic_atual: Taxa Selic vigente (usada para a Rf nominal).
        :param premio_risco: Prêmio de risco da bolsa/ativo.
        :param ipca_esperado: Expectativa de inflação de longo prazo.
        :param g_real: Crescimento real acima da inflação.
        :return: Preço-teto (R$).
        """
        ke = selic_atual + premio_risco
        g_nominal = ipca_esperado + g_real
        
        pvp_justo = (roe_normalizado - g_nominal) / (ke - g_nominal)
        preco_teto = pvp_justo * vpa
        
        return preco_teto