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


def test_corpo_fundido_fecha_e_bate_o_volume():
    S, esperado = P.corpo()
    vol = S.conferir(esperado, tol_rel=1e-9)
    assert vol > 0
    zs = [v[2] for v in S.v]
    assert abs(max(zs) - min(zs) - P.CORPO_H) < 1e-9
    xs = [v[0] for v in S.v]
    ys = [v[1] for v in S.v]
    assert abs(max(xs) - min(xs) - P.CX_L) < 1e-9
    assert abs(max(ys) - min(ys) - P.CX_A) < 1e-9


def test_nao_existe_mais_peca_de_painel():
    assert not hasattr(P, "painel")
    assert [n for n, _, _ in P.PECAS] == ["caixa-corpo", "caixa-tampa"]


def test_a_parede_de_tras_esta_vazada_no_eixo_da_chave():
    """
    Sonda de travessia: no eixo da chave nao pode sobrar material NENHUM
    entre a cavidade e a face externa.
    """
    import validar_modelo as V
    S, esperado = P.corpo()
    S.conferir(esperado, tol_rel=1e-9)
    V_, T_ = [tuple(v) for v in S.v], list(S.t)
    k = P.estacao_chave()
    segs = V.secao(V_, T_, k["z"])
    ys = V.travessia(segs, k["x"], y_min=k["y_cav"] - 1.0)
    assert ys == [], f"parede fechada no eixo da chave: material em y={ys}"


def test_o_rebaixo_da_chave_tem_o_diametro_certo():
    import validar_modelo as V
    S, esperado = P.corpo()
    S.conferir(esperado, tol_rel=1e-9)
    k = P.estacao_chave()
    # no eixo da chave a secao horizontal corta o rebaixo no diametro cheio
    segs = V.secao([tuple(v) for v in S.v], list(S.t), k["z"])
    larg, centro = V.largura_do_vao(segs, k["y_cav"])
    assert abs(larg - k["d_rebaixo"]) < 0.05, f"boca do rebaixo {larg:.3f}"
    assert abs(centro - k["x"]) < 0.01


def test_tampa_com_pinos_fecha_e_bate_o_volume():
    S, esperado = P.tampa()
    vol = S.conferir(esperado, tol_rel=1e-9)
    pn = P.pinos_placa()
    zs = [v[2] for v in S.v]
    assert abs(max(zs) - (P.TAMPA_ESP + pn["topo"])) < 1e-9, \
        "o pino nao tem a altura do perfil"
    assert abs(min(zs)) < 1e-9


def test_a_farpa_retem_a_placa():
    """A face de baixo da farpa tem de cair 0,20 acima da placa assentada."""
    pl, pn = P.PLACA, P.pinos_placa()
    topo_da_placa = pn["z"][1] + pl["esp"]
    assert abs(pn["z"][2] - topo_da_placa - pl["folga_placa"]) < 1e-9


# ---- estacao do carregador (TP4056) ----

def test_carregador_sobre_o_botao_verde_e_reprovado(restaurar):
    restaurar("CARREGADOR", dict(P.CARREGADOR, x=150.0))
    with pytest.raises(AssertionError, match="botao verde"):
        P.conferir_projeto()


def test_berco_encostado_na_parede_e_reprovado(restaurar):
    restaurar("CARREGADOR", dict(P.CARREGADOR, x=172.5))
    with pytest.raises(AssertionError, match="parede"):
        P.conferir_projeto()


def test_janela_que_nao_passa_a_capa_do_plugue_e_reprovada(restaurar):
    restaurar("CARREGADOR", dict(P.CARREGADOR, janela=(12.5, 7.2)))
    with pytest.raises(AssertionError, match="capa"):
        P.conferir_projeto()


def test_conector_largo_demais_para_a_janela_e_reprovado(restaurar):
    restaurar("CARREGADOR", dict(P.CARREGADOR, usb_l=11.5))
    with pytest.raises(AssertionError, match="conector"):
        P.conferir_projeto()


def test_placa_sem_apoio_na_chapa_e_reprovada(restaurar):
    restaurar("CARREGADOR", dict(P.CARREGADOR, larg=15.0))
    with pytest.raises(AssertionError, match="apoia"):
        P.conferir_projeto()


def test_garra_funda_demais_para_o_pla_e_reprovada(restaurar):
    # canal de 2,40: deflexao dobra e a fibra se afasta -> ~2,2 %
    restaurar("CARREGADOR", dict(P.CARREGADOR, prof_canal=2.4))
    with pytest.raises(AssertionError, match="deforma"):
        P.conferir_projeto()


def test_garra_que_nao_cobre_a_placa_e_reprovada(restaurar):
    restaurar("CARREGADOR", dict(P.CARREGADOR, folga=1.2))
    with pytest.raises(AssertionError, match="garra"):
        P.conferir_projeto()


def test_berco_fora_do_eixo_de_simetria_e_reprovado(restaurar):
    restaurar("CARREGADOR", dict(P.CARREGADOR, y=70.0))
    with pytest.raises(AssertionError, match="simetric"):
        P.conferir_projeto()
