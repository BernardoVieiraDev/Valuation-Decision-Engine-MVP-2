class DCFCalculator:

    def calcular_preco_teto(
        self,
        fluxos,
        taxa_desconto,
        crescimento_perpetuo,
        divida_liquida,
        numero_acoes
    ):

        if not fluxos:
            raise ValueError("Lista de fluxos vazia")

        if numero_acoes <= 0:
            raise ValueError("Número de ações inválido")

        if taxa_desconto <= 0:
            raise ValueError("Taxa de desconto deve ser positiva")

        if crescimento_perpetuo >= taxa_desconto:
            raise ValueError(
                "Crescimento perpétuo deve ser menor que a taxa de desconto"
            )

        # --- CORREÇÃO DE ESCALA ---
        # Converte os fluxos (onde 1 = 1 milhão) para valores absolutos
        # para que fiquem na mesma grandeza da dívida líquida e do número de ações.
        fluxos_absolutos = [f * 1_000_000 for f in fluxos]

        # Valor presente dos fluxos
        valor_presente_fluxos = sum(
            f / (1 + taxa_desconto) ** (i + 1)
            for i, f in enumerate(fluxos_absolutos)
        )

        # Valor terminal
        valor_terminal = (
            fluxos_absolutos[-1]
            * (1 + crescimento_perpetuo)
            / (taxa_desconto - crescimento_perpetuo)
        )

        # Valor terminal trazido para o presente
        valor_terminal_pv = (
            valor_terminal
            / (1 + taxa_desconto) ** len(fluxos_absolutos)
        )

        # Enterprise Value
        enterprise_value = (
            valor_presente_fluxos
            + valor_terminal_pv
        )

        # Equity Value
        equity_value = (
            enterprise_value
            - divida_liquida
        )

        # Preço por ação
        preco_teto = equity_value / numero_acoes

        return max(0.0, preco_teto)