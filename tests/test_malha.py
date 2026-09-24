# -*- coding: utf-8 -*-
"""Testes das primitivas de malha - PIBIC-CEUB."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import malha as M


def test_tubo_fecha_um_tronco_de_cone_vertical():
    """Tronco de cone: dois circulos de raios diferentes, em z diferentes."""
    r0, r1, h, n = 5.0, 3.0, 4.0, 48
    a = M.circulo(0.0, 0.0, r0, n)
    b = M.circulo(0.0, 0.0, r1, n)

    S = M.Solido("tronco")
    S.face(a, [], 0.0, cima=False)
    S.face(b, [], h, cima=True)
    S.tubo([(p[0], p[1], 0.0) for p in a], [(p[0], p[1], h) for p in b],
           inverter=False)

    # tronco de piramide sobre poligonos SEMELHANTES: exato
    A0, A1 = abs(M.area_assinada(a)), abs(M.area_assinada(b))
    esperado = h / 3 * (A0 + A1 + math.sqrt(A0 * A1))
    assert abs(S.conferir(esperado, tol_rel=1e-9) - esperado) < 1e-6


def test_tubo_fecha_um_cilindro_de_eixo_horizontal():
    """
    Uma laje de y=0 a y=3 com um furo cilindrico de eixo horizontal.

    E o caso exato da chave KCD1. O cilindro so pode sair de 'tubo': a parede
    do furo nao e vertical, entao 'faixa' nao serve.
    """
    L, H, W, R = 20.0, 12.0, 3.0, 4.0
    cx, cz = L / 2, H / 2
    c = M.circulo(cx, cz, R, 32)                    # pontos (x, z)
    anel = lambda y: [(p[0], y, p[1]) for p in c]

    S = M.Solido("laje")
    # tampas em y=0 e y=W, cada uma com o furo
    ret = [(0.0, 0.0), (L, 0.0), (L, H), (0.0, H)]
    S.face_vertical(ret, [c], 0.0, frente=False)
    S.face_vertical(ret, [c], W, frente=True)
    # as quatro faces restantes
    S.face([(0.0, 0.0), (L, 0.0), (L, W), (0.0, W)], [], 0.0, cima=False)
    S.face([(0.0, 0.0), (L, 0.0), (L, W), (0.0, W)], [], H, cima=True)
    S.faixa([(0.0, W), (0.0, 0.0)], 0.0, H)
    S.faixa([(L, 0.0), (L, W)], 0.0, H)
    # a parede do furo
    S.tubo(anel(0.0), anel(W), inverter=False)

    esperado = L * H * W - abs(M.area_assinada(c)) * W
    assert abs(S.conferir(esperado, tol_rel=1e-9) - esperado) < 1e-6


def test_face_vertical_triangula_no_plano_xz():
    """A area triangulada tem de ser a area da regiao, e as normais em +y."""
    ret = [(0.0, 0.0), (20.0, 0.0), (20.0, 12.0), (0.0, 12.0)]
    c = M.circulo(10.0, 6.0, 4.0, 32)

    S = M.Solido("face")
    S.face_vertical(ret, [c], 5.0, frente=True)

    assert len(S.t) > 0, "face_vertical nao emitiu triangulo nenhum"
    assert all(abs(S.v[i][1] - 5.0) < 1e-9 for t in S.t for i in t), \
        "algum vertice saiu fora do plano y=5"
    # normal de cada triangulo tem de apontar para +y
    for i, j, k in S.t:
        a, b, cc = S.v[i], S.v[j], S.v[k]
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        w = (cc[0] - a[0], cc[1] - a[1], cc[2] - a[2])
        ny = u[2] * w[0] - u[0] * w[2]
        assert ny > 0, "normal da face_vertical nao esta em +y"


def test_retangulo_e_anti_horario_e_tem_a_area_certa():
    r = M.retangulo(10.0, 5.0, 4.0, 2.0)
    assert abs(M.area_assinada(r) - 8.0) < 1e-12
    assert min(p[0] for p in r) == 8.0 and max(p[0] for p in r) == 12.0
    assert min(p[1] for p in r) == 4.0 and max(p[1] for p in r) == 6.0
