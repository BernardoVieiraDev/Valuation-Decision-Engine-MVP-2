class CalculadoraPrecoTetoVALE3:

    def calcular_preco_teto(self, ebitda_ttm, divida_liquida, total_acoes, multiplo_ev_ebitda):
        # EV Justo (Valor da Firma) = EBITDA x Múltiplo de Ciclo
        ev_justo = ebitda_ttm * multiplo_ev_ebitda
        
        # Equity Justo (Valor do Acionista) = EV Justo - Dívida Líquida
        equity_justo = ev_justo - divida_liquida
        
        # Preço Teto
        preco_teto = equity_justo / total_acoes
        
        return preco_teto