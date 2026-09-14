"""


Graham
- Lucro por ação (LPA)
- Valor patrimonial por ação (VPA)

"""

from math import sqrt

class GrahamCalculator:
    
    def calculate_grahan_price(self, lpa, vpa):
        if lpa <= 0 or vpa <= 0:
            raise ValueError("LPA e VPA devem ser maiores que zero.")
            

        preco_teto = sqrt(22.5 * lpa * vpa)
        return preco_teto

        
