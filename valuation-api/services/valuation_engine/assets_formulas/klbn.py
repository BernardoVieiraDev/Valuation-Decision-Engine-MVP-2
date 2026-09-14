class CalculadoraPrecoTetoKLBN4:

    def calcular_preco_teto(self, historico_ebitda, divida_liquida, total_acoes, multiplo_alvo_ev_ebitda):
        """
        Calcula o preço-teto de uma empresa cíclica pelo múltiplo EV/EBITDA médio.
        :param historico_ebitda: Lista com os resultados anuais de EBITDA recentes.
        :param divida_liquida: Dívida líquida atual da empresa (R$).
        :param total_acoes: Número total de ações da companhia (ON+PN).
        :param multiplo_alvo_ev_ebitda: Múltiplo histórico/premissa de EV/EBITDA para ciclo completo.
        :return: Preço-teto (R$).
        """
        # Média de EBITDA do ciclo histórico
        ebitda_normalizado = sum(historico_ebitda) / len(historico_ebitda)
        
        # Valor da Firma (EV - Enterprise Value)
        ev_implicito = multiplo_alvo_ev_ebitda * ebitda_normalizado
        
        # Valor do Acionista (Equity Value) = EV - Dívida Líquida
        equity_implicito = ev_implicito - divida_liquida
        
        # Preço Teto
        preco_teto = equity_implicito / total_acoes
        
        return preco_teto