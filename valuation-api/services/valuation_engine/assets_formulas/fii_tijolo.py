class CalculadoraPrecoTetoFIITijolo:

    def calcular_preco_teto(
        self,
        ntnb_referencia,
        dividendo_anual_normalizado,
        vp_cota,
        estabilidade_renda,
        potencial_crescimento,
        qualidade_ativos,
        estresse_operacional
    ):
        """
        Calcula o preço teto de FIIs de Tijolo usando os métodos combinados da planilha.
        Parâmetros textuais devem ser:
        - estabilidade_renda: "Alta", "Média", "Baixa"
        - potencial_crescimento: "Alto", "Médio", "Nulo"
        - qualidade_ativos: "Alta", "Média", "Baixa"
        - estresse_operacional: "Sim", "Não"
        """
        
        # 1. Tabelas de Parâmetros Qualitativos (conforme aba "Parametros" da planilha)
        tabela_premio_risco = {"Alta": 0.01, "Média": 0.02, "Baixa": 0.035}
        tabela_g = {"Alto": 0.015, "Médio": 0.0075, "Nulo": 0.0}
        tabela_pvp = {"Alta": 0.95, "Média": 0.85, "Baixa": 0.70}
        
        # 2. Definição das variáveis derivadas (com fallback caso texto venha fora do padrão)
        premio_risco = tabela_premio_risco.get(estabilidade_renda, 0.02)
        g = tabela_g.get(potencial_crescimento, 0.0)
        pvp_alvo = tabela_pvp.get(qualidade_ativos, 0.85)
        
        # 3. Cálculos
        yield_alvo = ntnb_referencia + premio_risco
        
        # Preço teto via Yield Spread (Dividendo / Yield-alvo)
        preco_teto_yield = dividendo_anual_normalizado / yield_alvo
        
        # Preço teto via P/VP Ajustado
        preco_teto_pvp = vp_cota * pvp_alvo
        
        # Preço teto via DDM/Gordon (se houver estresse, o crescimento 'g' é invalidado e não usamos DDM)
        if estresse_operacional.lower() == "sim":
            preco_teto_ddm = None # "N/A (estresse)"
        else:
            preco_teto_ddm = dividendo_anual_normalizado / (yield_alvo - g)
        
        # Como o modelo retorna múltiplas métricas que guiam a decisão, 
        # optamos por retornar o valor do DDM (se saudável) ou do Yield Spread (se em estresse), 
        # que é a linha de base para a rentabilidade real em FIIs de tijolo.
        if preco_teto_ddm is not None:
            return preco_teto_ddm
        return preco_teto_yield