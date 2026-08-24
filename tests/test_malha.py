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
