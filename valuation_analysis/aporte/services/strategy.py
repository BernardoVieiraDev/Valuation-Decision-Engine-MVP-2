from abc import ABC, abstractmethod
from aporte.services.bandas_aporte import (banda_permite_aporte, valor_para_a_banda)

class RecomendacaoAporteDTO:
    def __init__(self, ativo_carteira, valor_recomendado: float):
        self.ativo_carteira = ativo_carteira
        self.valor_recomendado = valor_recomendado

class Strategy(ABC):
    # Alterado para receber uma lista de ativos_excluidos
    def _obter_ativos_filtrados(self, carteira, tipos_permitidos: list = None, ativos_excluidos: list = None):
        """Coleta e filtra os ativos baseados nos tipos permitidos e múltiplos tickers excluídos."""
        todos_ativos = []

        if not tipos_permitidos or "acao" in tipos_permitidos:
            todos_ativos.extend(carteira.ativos.all())
        if not tipos_permitidos or "fii" in tipos_permitidos:
            todos_ativos.extend(carteira.fiis.all())
        if not tipos_permitidos or "cripto" in tipos_permitidos:
            todos_ativos.extend(carteira.criptos.all())
        if not tipos_permitidos or "etf" in tipos_permitidos:
            todos_ativos.extend(carteira.etfs_br.all())
            todos_ativos.extend(carteira.etfs_internacionais.all())

        ativos_filtrados = []
        
        # Converte tudo para maiúsculo para evitar erros de case (ex: 'petr4' vs 'PETR4')
        excluidos_upper = [ticker.upper() for ticker in ativos_excluidos] if ativos_excluidos else []
        
        for ativo in todos_ativos:
            ticket = ""
            if hasattr(ativo, 'acao'): ticket = ativo.acao.ticket
            elif hasattr(ativo, 'fii'): ticket = ativo.fii.ticket
            elif hasattr(ativo, 'cripto'): ticket = ativo.cripto.ticket
            elif hasattr(ativo, 'etf'): ticket = ativo.etf.ticket

            # Checa se o ticker consta na lista de exclusão
            if excluidos_upper and ticket.upper() in excluidos_upper:
                continue
            ativos_filtrados.append(ativo)

        return ativos_filtrados

    @abstractmethod
    def definir_aporte(self, aporte: float, carteira, limite_ativos: int = None, tipos_permitidos: list = None, ativos_excluidos: list = None) -> list[RecomendacaoAporteDTO]:
        pass 

class StrategyConcentrado(Strategy):
    def definir_aporte(self, aporte: float, carteira, limite_ativos: int = None, tipos_permitidos: list = None, ativos_excluidos: list = None) -> list[RecomendacaoAporteDTO]:
        aporte_restante = aporte
        recomendacoes = []

        ativos_filtrados = self._obter_ativos_filtrados(carteira, tipos_permitidos, ativos_excluidos)
        ativos_ordenados = sorted(
            ativos_filtrados, 
            key=lambda a: getattr(a, 'margem_de_seguranca', 0), 
            reverse=True
        )

        if limite_ativos:
            ativos_ordenados = ativos_ordenados[:limite_ativos]

        for ativo_carteira in ativos_ordenados:
            if aporte_restante <= 0:
                recomendacoes.append(RecomendacaoAporteDTO(ativo_carteira, 0.0))
                continue
            
            if not banda_permite_aporte(carteira, ativo_carteira):
                recomendacoes.append(RecomendacaoAporteDTO(ativo_carteira, 0.0))
            elif getattr(ativo_carteira, 'margem_de_seguranca', 0) < carteira.margem_de_seguranca_minima:
                recomendacoes.append(RecomendacaoAporteDTO(ativo_carteira, 0.0))
            else:
                valor_banda = valor_para_a_banda(carteira, ativo_carteira, carteira.banda_mais)
                
                if valor_banda >= aporte_restante:
                    recomendacoes.append(RecomendacaoAporteDTO(ativo_carteira, aporte_restante))
                    aporte_restante = 0 
                else:
                    recomendacoes.append(RecomendacaoAporteDTO(ativo_carteira, valor_banda))
                    aporte_restante -= valor_banda
                    
        if aporte_restante > 0:
            print(f"Caixa de Oportunidade: R$ {aporte_restante:.2f}")
            
        return recomendacoes

class StrategyDividido(Strategy):
    def definir_aporte(self, aporte: float, carteira, limite_ativos: int = None, tipos_permitidos: list = None, ativos_excluidos: list = None) -> list[RecomendacaoAporteDTO]:
        recomendacoes = []
        ativos_filtrados = self._obter_ativos_filtrados(carteira, tipos_permitidos, ativos_excluidos)

        ativos_elegiveis = [
            a for a in ativos_filtrados 
            if getattr(a, 'margem_de_seguranca', 0) >= carteira.margem_de_seguranca_minima
        ]
        
        ativos_elegiveis.sort(key=lambda a: getattr(a, 'margem_de_seguranca', 0), reverse=True)
        if limite_ativos:
            ativos_elegiveis = ativos_elegiveis[:limite_ativos]

        if not ativos_elegiveis:
            return [RecomendacaoAporteDTO(a, 0.0) for a in ativos_filtrados]

        valor_por_ativo = aporte / len(ativos_elegiveis)

        for ativo in ativos_filtrados:
            if ativo in ativos_elegiveis:
                valor_banda = valor_para_a_banda(carteira, ativo, carteira.banda_mais)
                valor_a_aportar = min(valor_por_ativo, valor_banda)
                recomendacoes.append(RecomendacaoAporteDTO(ativo, valor_a_aportar))
            else:
                recomendacoes.append(RecomendacaoAporteDTO(ativo, 0.0))
                
        return recomendacoes