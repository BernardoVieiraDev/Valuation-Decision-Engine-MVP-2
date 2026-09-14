class PeterLynchCalculator:
    
    def calculate_peter_lynch(self, lpa, taxa_de_crescimento_lucro):
        taxa_decimal = taxa_de_crescimento_lucro / 100
        preco_teto = lpa * (6 + 2 * taxa_decimal)
        return preco_teto