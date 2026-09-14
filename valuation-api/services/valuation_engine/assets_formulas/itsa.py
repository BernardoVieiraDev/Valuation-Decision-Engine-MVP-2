class CalculadoraPrecoTetoITSA4:

    def calcular_preco_teto(self, participacoes_mercado, total_acoes_holding, desconto_alvo):
        """
        Calcula o preço-teto de uma Holding pelo método SOTP (Soma das Partes).
        :param participacoes_mercado: Lista (ou tupla) com o valor de mercado atual em R$ das empresas investidas.
        :param total_acoes_holding: Número total de ações em circulação da holding.
        :param desconto_alvo: Desconto de holding exigido (margem de segurança).
        :return: Preço-teto (R$).
        """
        # SOTP = Soma das partes
        valor_mercado_total = sum(participacoes_mercado)
        
        # NAV (Net Asset Value) por ação
        nav_por_acao = valor_mercado_total / total_acoes_holding
        
        # Preço Teto ajustado pelo desconto exigido
        preco_teto = nav_por_acao * (1 - desconto_alvo)
        
        return preco_teto