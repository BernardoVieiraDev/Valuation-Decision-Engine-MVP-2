class CalculadoraPrecoTetoWEGE3:

    def calcular_preco_teto(self, lpa_base, g1, n1, g3, ke):
        # n1: Anos de alto crescimento (Estágio 1)
        total_anos = 10
        soma_vp_lpa = 0.0
        lpa_projetado = lpa_base
        
        for ano in range(1, total_anos + 1):
            # Determina o crescimento do ano
            if ano <= n1:
                crescimento_ano = g1
            else:
                # Interpolação linear da convergência (Estágio 2)
                crescimento_ano = g1 + (g3 - g1) * (ano - n1) / (total_anos - n1)
            
            # Projeta o LPA do ano
            lpa_projetado = lpa_projetado * (1 + crescimento_ano)
            
            # Fator de Desconto = (1 + Ke)^ano
            fator_desconto = (1 + ke) ** ano
            
            # Valor presente do fluxo do ano
            vp_ano = lpa_projetado / fator_desconto
            soma_vp_lpa += vp_ano
            
            if ano == total_anos:
                lpa_ano_10 = lpa_projetado
                fator_desconto_ano_10 = fator_desconto

        # Valor Terminal no ano 10 = LPA10 * (1 + g3) / (Ke - g3)
        valor_terminal = lpa_ano_10 * (1 + g3) / (ke - g3)
        
        # Valor Presente do Valor Terminal
        vp_valor_terminal = valor_terminal / fator_desconto_ano_10
        
        # Preço-Teto (Soma do VP dos LPAs + VP do Valor Terminal)
        preco_teto = soma_vp_lpa + vp_valor_terminal
        
        return preco_teto