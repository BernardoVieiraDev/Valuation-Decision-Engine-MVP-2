class CalculadoraPrecoTetoFIIPapel:

    def calcular_preco_teto(
        self, 
        preco_atual, 
        vp_cota, 
        pct_cdi, 
        pct_ipca, 
        selic_atual, 
        selic_normalizada, 
        dividendos_12m, 
        dy_minimo_aceitavel
    ):
        """
        Calcula o preço teto para FIIs de Papel usando o método de DY Normalizado.
        Ajusta a parcela indexada ao CDI para a Selic normalizada.
        """
        # Soma os dividendos dos últimos 12 meses (R$/cota)
        dividendo_anual = sum(dividendos_12m)
        
        # Fator de normalização (Selic de longo prazo / Selic atual)
        fator_normalizacao_cdi = selic_normalizada / selic_atual
        
        # Dividendo anual normalizado
        # (Ajusta a parcela CDI; assume que a parcela IPCA+ se mantém constante em R$)
        dividendo_normalizado = dividendo_anual * ((pct_cdi * fator_normalizacao_cdi) + (pct_ipca * 1.0))
        
        # Preço Teto
        preco_teto = dividendo_normalizado / dy_minimo_aceitavel
        
        return preco_teto