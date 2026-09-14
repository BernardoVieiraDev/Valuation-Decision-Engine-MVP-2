"""Snapshot revisável, independente de mudanças nas cotações após a simulação."""
def snapshot(recomendacoes):
    itens = []
    for rec in recomendacoes:
        if rec.valor_recomendado <= 0:
            continue
        posicao = rec.ativo_carteira
        for relation, tipo in [('acao', 'acao'), ('fii', 'fii'), ('cripto', 'cripto'), ('etf', 'etf')]:
            ativo = getattr(posicao, relation, None)
            if ativo is not None:
                preco = getattr(ativo, 'preco_atual_brl', getattr(ativo, 'preco_atual', 0.0))
                itens.append({
                    'ticker': ativo.ticket, 'tipo_ativo': tipo,
                    'metodo_valuation': getattr(posicao, 'metodo_valuation', 'N/A'),
                    'parametros_valuation': getattr(posicao, 'parametros_especificos', {}),
                    'preco_teto_calculado': getattr(posicao, 'preco_teto', 0.0),
                    'preco_atual_momento': preco, 'valor_aportado': rec.valor_recomendado,
                })
                break
    return itens
