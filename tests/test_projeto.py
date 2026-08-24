# -*- coding: utf-8 -*-
"""
Testes de 'conferir_projeto' - PIBIC-CEUB.

Uma conferencia que nunca reprovou nada nao prova nada. Cada teste aqui
perturba UM parametro e exige que a conferencia acuse.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gerar_modelo_3mf as P


def test_o_projeto_como_esta_passa():
    info = P.conferir_projeto()
    assert info["sw"]["x"] == 69.5
    assert info["placa"]["centro"] == (73.0, 65.0)


@pytest.fixture
def restaurar():
    """Desfaz qualquer mexida nas constantes do modulo."""
    guarda = {}

    def mexer(nome, valor):
        if nome not in guarda:
            guarda[nome] = getattr(P, nome)
        setattr(P, nome, valor)

    yield mexer
    for nome, valor in guarda.items():
        setattr(P, nome, valor)


def test_chave_fora_do_trecho_reto_e_reprovada(restaurar):
    restaurar("CHAVE", dict(P.CHAVE, x=40.0))
    with pytest.raises(AssertionError, match="trecho reto"):
        P.conferir_projeto()


def test_painel_fino_demais_para_a_porca_e_reprovado(restaurar):
    restaurar("PAIN_ESP", 3.0)
    with pytest.raises(AssertionError, match="aperta"):
        P.conferir_projeto()


def test_placa_batendo_no_botao_verde_e_reprovada(restaurar):
    restaurar("PLACA", dict(P.PLACA, x=120.0))
    with pytest.raises(AssertionError, match="verde"):
        P.conferir_projeto()


def test_perna_curta_demais_e_reprovada(restaurar):
    # rasgo so na haste: braco de 1,8 mm em vez de 6,5 -> deformacao ~11 %
    restaurar("PLACA", dict(P.PLACA, rasgo_h=1.8))
    with pytest.raises(AssertionError, match="deforma"):
        P.conferir_projeto()
