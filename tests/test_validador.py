# -*- coding: utf-8 -*-
"""
Mutacao das sondas do berco. Uma sonda que nunca reprovou nada nao prova
nada - foi assim que a sonda do pino concordou com tudo por uma revisao
inteira, porque 'eh_circulo' rejeitava a secao em D.

A mutacao e na MALHA, nunca na expectativa: a tampa e gerada com um
parametro estragado, o parametro volta ao lugar, e so entao a sonda roda.
Estragar o parametro e sondar com ele estragado nao testaria nada - malha e
expectativa sairiam do mesmo numero errado.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gerar_modelo_3mf as P
import validar_modelo as V


def malha_com(carregador=None, **globais):
    guarda = {"CARREGADOR": P.CARREGADOR}
    guarda.update({k: getattr(P, k) for k in globais})
    try:
        P.CARREGADOR = dict(P.CARREGADOR, **(carregador or {}))
        for k, v in globais.items():
            setattr(P, k, v)
        S, esperado = P.tampa()
        S.conferir(esperado, tol_rel=1e-9)
    finally:
        for k, v in guarda.items():
            setattr(P, k, v)
    return [tuple(v) for v in S.v], list(S.t)


def falhas_do_berco(Vs, Ts):
    V.falhas = 0
    V.conferir_berco(Vs, Ts)
    return V.falhas


def test_a_tampa_como_esta_passa_nas_sondas():
    assert falhas_do_berco(*malha_com()) == 0


@pytest.mark.parametrize("carregador, globais", [
    (dict(janela=(12.0, 7.2)), {}),
    ({}, dict(FOLGA_ALIVIO=2.0)),
    (dict(folga=0.4), {}),
    (dict(degraus=((0.6, 0.4), (0.8, 0.4))), {}),
    (dict(comp=26.0), {}),
    (dict(x=167.0), {}),
], ids=["janela", "alivio", "canal", "degrau", "garra", "posicao"])
def test_cada_sonda_acusa_a_malha_estragada(carregador, globais):
    assert falhas_do_berco(*malha_com(carregador, **globais)) > 0
