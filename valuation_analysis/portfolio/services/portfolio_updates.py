"""Atualizações compartilhadas pela tela de aporte e pelo botão individual."""
import json

from .api_client import PlaybookAPIClient


def calcular_teto(ativo, client):
    ticker = ativo.acao.ticket
    metodo = ativo.metodo_valuation
    if metodo == 'graham':
        return client.get_graham_price(ticker)
    if metodo == 'bazin':
        return client.get_bazin_price(ticker, ativo.parametro_bazin_dy)
    if metodo == 'lynch':
        return client.get_peter_lynch_price(ticker, ativo.parametro_lynch_crescimento)
    if metodo == 'projetivo':
        return client.get_projetivo_price(ticker, ativo.parametro_projetivo_pl_justo)
    if metodo == 'dfc':
        try:
            fluxos = json.loads(ativo.parametro_dfc_fluxos or '[]')
        except json.JSONDecodeError:
            fluxos = []
        return client.get_dfc_price(ticker, ativo.parametro_dfc_taxa_desconto,
                                    ativo.parametro_dfc_crescimento, fluxos)
    return client.get_asset_formula_price(metodo, ticker, ativo.parametros_especificos)


def atualizar_posicao(ativo, *, cotacao=False, teto=False, client=None):
    client = client or PlaybookAPIClient()
    if cotacao:
        preco = client.get_price(ativo.acao.ticket)
        if preco > 0:
            ativo.acao.preco_atual = preco
            ativo.acao.save(update_fields=['preco_atual'])
    if teto:
        preco = calcular_teto(ativo, client)
        if preco > 0:
            ativo.preco_teto = preco
            ativo.save(update_fields=['preco_teto'])
