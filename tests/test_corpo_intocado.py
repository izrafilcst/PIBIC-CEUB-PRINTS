# -*- coding: utf-8 -*-
"""
O corpo ja foi impresso. Esta revisao so pode reimprimir a tampa, entao a
malha do corpo nao pode mudar um vertice - nem por efeito colateral de mexer
numa constante que as duas pecas compartilham.

O hash e da MALHA (vertices e triangulos, na precisao gravada no .3mf), nao do
arquivo: o .3mf leva metadados que mudam a cada gravacao sem mudar a peca.
"""

import hashlib
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import gerar_modelo_3mf as P
import malha as M
import validar_modelo as V

# malha do caixa-corpo.3mf de 88db49b - identica ate 0ba9eb1, e a impressa
REFERENCIA = "c5e58c07c79b3695694d70010ca6ac83947300aeeafa0bdd023895d284806e0e"


def hash_malha(Vs, Ts):
    h = hashlib.sha256()
    for v in Vs:
        h.update(("%.6f %.6f %.6f\n" % tuple(v)).encode())
    for t in Ts:
        h.update(("%d %d %d\n" % tuple(t)).encode())
    return h.hexdigest()


def test_o_corpo_gerado_agora_e_o_corpo_impresso(tmp_path):
    S, esperado = P.corpo()
    S.conferir(esperado, tol_rel=1e-9)
    arq = tmp_path / "corpo.3mf"
    M.salvar_3mf(str(arq), S, titulo="caixa-corpo")
    assert hash_malha(*V.ler_3mf(str(arq))) == REFERENCIA


def test_o_arquivo_do_corpo_no_repositorio_e_o_impresso():
    assert hash_malha(*V.ler_3mf(str(RAIZ / "caixa-corpo.3mf"))) == REFERENCIA
