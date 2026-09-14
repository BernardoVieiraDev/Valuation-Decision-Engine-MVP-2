class CalculadoraPrecoTetoFLRY3:

    def calcular_preco_teto(self, vpa, roe_normalizado, g_real, rf_real, erp):
        """
        Calcula o preço-teto pelo Método ROE-Ke-g.
        :param vpa: Valor Patrimonial por Ação.
        :param roe_normalizado: Retorno sobre o PL de ciclo.
        :param g_real: Crescimento real de longo prazo esperado.
        :param rf_real: Taxa livre de risco real (ex: NTN-B).
        :param erp: Equity risk premium.
        :return: Preço-teto (R$).
        """
        ke_real = rf_real + erp
        pvp_justo = (roe_normalizado - g_real) / (ke_real - g_real)
        preco_teto = pvp_justo * vpa
        
        return preco_teto