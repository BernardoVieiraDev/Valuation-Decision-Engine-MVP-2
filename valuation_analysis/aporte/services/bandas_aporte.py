def valor_para_a_banda(carteira, ativo_carteira, banda: float) -> float: 
    v_carteira = carteira.valor_total
    v_ativo = ativo_carteira.valor_total
    banda_decimal = banda / 100
    
    # Impede divisão por zero caso a banda seja 100%
    if banda_decimal == 1:
        return 0.0
        
    return (banda_decimal * v_carteira - v_ativo) / (1 - banda_decimal)


def banda_permite_aporte(carteira, ativo_carteira) -> bool:
    pct_atual = ativo_carteira.percentual_na_carteira
    return pct_atual <= carteira.banda_mais