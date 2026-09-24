# -*- coding: utf-8 -*-
"""Cotas derivadas e poligonos do berco do TP4056 - PIBIC-CEUB."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gerar_modelo_3mf as P
import malha as M


def test_estacao_tem_as_cotas_da_spec():
    e = P.estacao_carregador()
    esperado = dict(x_usb=165.55, yc=65.0, canal_w=2.0, w_fundo=8.7,
                    w_ponta=7.5, w_fora=10.7, u_meia=2.2, z_garra=32.2,
                    topo=34.2, cobre=1.0, z_topo_corpo=32.8, braco=28.8)
    for k, v in esperado.items():
        assert abs(e[k] - v) < 1e-9, f"{k} = {e[k]}, a spec diz {v}"
    assert e["alivio"] == pytest.approx((14.0, 8.2))
    assert e["envelope"] == pytest.approx((163.9, 54.3, 170.2, 75.7))
    assert e["niveis"] == [0.4, 0.8, 1.2]
    assert [g for _, _, g in e["perfil"]] == [1.2, 0.0, 0.4, 0.8]
    assert abs(e["eps"] - 0.0078363) < 1e-6


def test_secao_da_coluna_tem_a_area_da_formula_fechada():
    e = P.estacao_carregador()
    um, wp, wf, cw = e["u_meia"], e["w_ponta"], e["w_fora"], e["canal_w"]
    for g in (0.0, 0.4, 0.8, 1.2):
        for lado in (1, -1):
            A = M.area_assinada(P.secao_coluna(e, g, lado))
            assert A > 0, "a secao tem de sair anti-horaria"
            assert abs(A - (2 * um * (wf - wp) - cw * g)) < 1e-9


def test_as_colunas_sao_espelho_uma_da_outra_em_y():
    e = P.estacao_carregador()
    cima = sorted(P.secao_coluna(e, 1.2, 1))
    baixo = sorted((x, 2 * e["yc"] - y) for x, y in P.secao_coluna(e, 1.2, -1))
    assert len(cima) == len(baixo)
    assert all(math.dist(a, b) < 1e-9 for a, b in zip(cima, baixo))


def test_o_lado_do_canal_carrega_os_niveis_mais_rasos():
    """
    A emenda entre secoes so fecha se o lado do canal tiver um vertice em
    cada nivel mais raso que ele - o mesmo T da corda do pino.
    """
    e = P.estacao_carregador()
    x_lado = e["x"] - e["canal_w"] / 2
    ws = sorted(y - e["yc"] for x, y in P.secao_coluna(e, 1.2, 1)
                if abs(x - x_lado) < 1e-9)
    assert ws == pytest.approx([7.5, 7.9, 8.3, 8.7])


def test_ranhura_entre_a_boca_e_o_fundo():
    e = P.estacao_carregador()
    r = P.ranhura(e, 0.0, 1.2, 1)
    assert abs(M.area_assinada(r) - e["canal_w"] * 1.2) < 1e-9
    assert len(r) == 8      # 4 cantos + os niveis 0,4 e 0,8 dos dois lados
