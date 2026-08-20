#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desenhos tecnicos das pecas da caixa - PIBIC UniCEUB.
Autor: Rafael Alves de Sousa Costa.

Le a geometria DIRETO dos .3mf, entao o desenho nao pode divergir do modelo:
toda cota sai de uma medicao na malha, nenhuma e digitada a mao.

  caixa-painel.3mf  -> desenho-caixa-painel.svg   PIBIC-CX-01
  caixa-corpo.3mf   -> desenho-caixa-corpo.svg    PIBIC-CX-02
  caixa-tampa.3mf   -> desenho-caixa-tampa.svg    PIBIC-CX-03
  caixa-corpo.3mf   -> desenho-caixa-berco.svg    PIBIC-CX-04

A CX-04 e detalhe do mesmo corpo da CX-02, em prancha propria: o berco do
interruptor envolve um componente COMPRADO, uma sequencia de montagem e um
conjunto de cotas ainda a confirmar, e nada disso cabe numa nota de rodape.

Alem de medir, o script CONFERE o que mediu contra gerar_modelo_3mf.py. Sao
duas fontes independentes - a malha gravada e os parametros de projeto - e a
funcao 'bate' para tudo se as duas discordarem. Sem isso o desenho continuaria
sendo gerado, bonito e errado, depois de uma edicao so no modelo.

Pranchas em A2 paisagem (594 x 420 mm), projecao no 1o diedro: a vista
superior fica ABAIXO da vista frontal e, nela, a face frontal da peca e a
aresta de baixo.

Uso:  python gerar_desenhos_3mf.py
"""

import math
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict

import gerar_modelo_3mf as P
from gerar_desenhos import (Desenho, L_CONTORNO, L_FINA, L_TRACO,
                            D_OCULTA, D_CENTRO, D_FANTASMA,
                            FONTE, FONTE_P, C_COTA, C_REF, C_TXT, C_ATEN)

NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"

FOLHA_W, FOLHA_H = 594.0, 420.0
COL_DIR = 330.0


# =====================================================================
# Leitura do 3MF e seccionamento
# =====================================================================

def ler_3mf(caminho):
    root = ET.fromstring(zipfile.ZipFile(caminho).read("3D/3dmodel.model"))
    o = root.find(NS + "resources").find(NS + "object")
    m = o.find(NS + "mesh")
    V = [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
         for v in m.find(NS + "vertices")]
    T = [(int(t.get("v1")), int(t.get("v2")), int(t.get("v3")))
         for t in m.find(NS + "triangles")]
    return V, T


def niveis(V, tol=3):
    """Alturas distintas da malha - as quebras do perfil da peca."""
    return sorted({round(p[2], tol) for p in V})


def secao(V, T, z):
    segs = []
    for tri in T:
        Q = [V[i] for i in tri]
        pts = []
        for i in range(3):
            a, b = Q[i], Q[(i + 1) % 3]
            if (a[2] - z) * (b[2] - z) < 0:
                t = (z - a[2]) / (b[2] - a[2])
                pts.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
            elif abs(a[2] - z) < 1e-9:
                pts.append((a[0], a[1]))
        pts = list(dict.fromkeys([(round(x, 5), round(y, 5)) for x, y in pts]))
        if len(pts) == 2:
            segs.append(tuple(pts))
    return segs


def lacos(segs):
    adj = defaultdict(list)
    for a, b in segs:
        adj[a].append(b)
        adj[b].append(a)
    vistos, out = set(), []
    for s in adj:
        if s in vistos:
            continue
        loop, cur, prev = [s], s, None
        vistos.add(s)
        while True:
            nxt = [v for v in adj[cur] if v != prev and v not in vistos]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            vistos.add(cur)
            loop.append(cur)
        if len(loop) >= 3:
            out.append(loop)
    return out


def eh_circulo(loop, tol=0.06):
    n = len(loop)
    cx = sum(p[0] for p in loop) / n
    cy = sum(p[1] for p in loop) / n
    r = [math.hypot(p[0] - cx, p[1] - cy) for p in loop]
    if max(r) - min(r) < tol and n >= 8:
        # os vertices estao SOBRE o circulo verdadeiro; o raio e o maximo,
        # nao a media (a media e do poligono inscrito, sempre menor)
        return cx, cy, max(r)
    return None


def analisar(V, T, z):
    """(contornos_nao_circulares, furos) no plano z."""
    conts, furos = [], []
    for lo in lacos(secao(V, T, z)):
        c = eh_circulo(lo)
        if c:
            furos.append(c)
        else:
            conts.append(lo)
    conts.sort(key=lambda lo: -(max(p[0] for p in lo) - min(p[0] for p in lo)))
    furos.sort(key=lambda f: (round(f[1], 1), f[0]))
    return conts, furos


def camadas(V, T):
    """[(z0, z1, contornos, furos)] - uma entrada por camada prismatica."""
    zs = niveis(V)
    out = []
    for z0, z1 in zip(zs, zs[1:]):
        c, f = analisar(V, T, (z0 + z1) / 2)
        out.append((z0, z1, c, f))
    return out


def por_raio(furos, r, tol=0.05):
    return sorted([f for f in furos if abs(f[2] - r) < tol],
                  key=lambda f: (round(f[1], 1), f[0]))


def raios(furos, tol=0.05):
    """Raios distintos presentes, do maior para o menor."""
    rs = []
    for f in sorted(furos, key=lambda f: -f[2]):
        if not any(abs(f[2] - r) < tol for r in rs):
            rs.append(f[2])
    return rs


def raio_canto(loop):
    """
    Raio do canto de um retangulo arredondado, pelo PONTO DE TANGENCIA.

    Num retangulo arredondado o trecho reto da lateral vai de y0+R a y1-R.
    Logo o menor y entre os vertices que estao sobre x = xmin ja e y0 + R.
    E exato e nao depende de ajuste numerico, ao contrario de um circulo
    por minimos quadrados, que os vertices do trecho reto contaminam.
    """
    x0 = min(p[0] for p in loop)
    y0 = min(p[1] for p in loop)
    tang = [p[1] for p in loop if abs(p[0] - x0) < 1e-4]
    return min(tang) - y0 if tang else None


def raio_coluna(V, cx, cy, r_int, r_ext):
    """
    Raio da coluna de inserto, medido nos VERTICES da malha, na janela entre
    r_int e r_ext.

    Duas armadilhas, as duas ja pagas:

    Nao medir no corte. A secao de uma parede vertical devolve, alem dos
    vertices do contorno, o ponto MEDIO de cada corda - que num circulo cai
    para dentro. Num arco de 7 graus dá 0,01 mm, o bastante para a coluna de
    10,00 sair cotada como 9,98.

    E o MENOR raio da janela, nao o maior. Os vertices do arco da coluna estao
    todos exatamente sobre ele, mas o contorno da cavidade continua se
    afastando depois dos dois pontos onde o arco encontra a parede; o maximo
    pega um ponto qualquer dessa continuacao e devolve 10,57. A janela exclui
    o furo do inserto por baixo e o contorno externo por cima.
    """
    rs = [math.hypot(p[0] - cx, p[1] - cy) for p in V]
    rs = [r for r in rs if r_int < r < r_ext]
    return min(rs) if rs else None


def dist_ate(p, loop):
    melhor = 1e9
    n = len(loop)
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx +
                                                   (p[1] - a[1]) * dy) / L2))
        melhor = min(melhor, math.hypot(p[0] - (a[0] + t * dx),
                                        p[1] - (a[1] + t * dy)))
    return melhor


# =====================================================================
# Conferencia cruzada: malha medida x parametros de projeto
# =====================================================================

_divergencias = []


def bate(rotulo, medido, nominal, tol=0.02):
    if medido is None or abs(medido - nominal) > tol:
        _divergencias.append(
            f"{rotulo}: malha {medido if medido is None else f'{medido:.4f}'}"
            f" x projeto {nominal:.4f}")
    return medido


def encerrar_conferencia():
    if _divergencias:
        raise AssertionError(
            "desenho e modelo divergem - corrija gerar_modelo_3mf.py e "
            "regere os .3mf antes de emitir a prancha:\n  - "
            + "\n  - ".join(_divergencias))


# =====================================================================
# Auxiliares de desenho
# =====================================================================

def vg(s):
    return f"{s:.2f}".replace(".", ",")


def dm(d):
    return f"&#216;{vg(d)}"


class Vista:
    """
    Converte coordenadas da PECA em coordenadas da prancha.

    Na peca a origem e o canto inferior esquerdo e y cresce para cima; no SVG
    y cresce para baixo. Sem esta inversao a vista sai espelhada em relacao a
    tabela de coordenadas.
    """

    def __init__(self, ox, oy, larg, alt):
        self.ox, self.oy, self.larg, self.alt = ox, oy, larg, alt

    def px(self, x):
        return self.ox + x

    def py(self, y):
        return self.oy + self.alt - y

    def p(self, x, y):
        return (self.px(x), self.py(y))


def domo(D, cx, y_base, r, h, cor=C_REF, dash=D_FANTASMA, fechar=False):
    """
    Capa do botao em linha de referencia, com o apice EXATO em y_base - h.

    Numa Bezier quadratica o ponto mais alto nao e o de controle: o apice fica
    em (P0 + 2C + P2)/4. Com o controle posto direto na altura desejada a
    cupula sai um terco mais baixa do que a cota ao lado dela afirma - e essa
    cota, quanto do botao fica para fora, e o assunto da prancha.
    """
    c = 2 * (y_base - h) - y_base
    D.el.append(f'<path d="M {cx-r:.2f} {y_base:.2f} Q {cx:.2f} {c:.2f} '
                f'{cx+r:.2f} {y_base:.2f}{" Z" if fechar else ""}" '
                f'fill="none" stroke="{cor}" stroke-width="{L_TRACO}" '
                f'stroke-dasharray="{dash}"/>')


def linha_de_corte(D, W, larg, y_peca, letra="A"):
    """
    Traco de corte na vista superior, com as setas do sentido de projecao.

    As setas apontam para o +y DA PECA, que na vista sai para cima: e desse
    lado que esta o observador do corte, o mesmo da vista frontal. O corte
    correspondente e uma secao destacada - fica onde couber na prancha, sem
    espelhamento, e nao no lugar que o 1o diedro reservaria.
    """
    ya = W.py(y_peca)
    for sg, xa in ((-1, W.px(0) - 4), (1, W.px(larg) + 4)):
        D.linha(xa, ya, xa + sg * 12, ya, 0.5, C_ATEN)
        D.linha(xa, ya, xa, ya - 7, 0.5, C_ATEN)
        D.seta(xa, ya - 7, -math.pi / 2)
        D.txt(xa + sg * 17, ya + 1.2, letra, 3.4, cor=C_ATEN, peso="bold")


def contorno(D, loop, W, lw=L_CONTORNO, cor="#111", dash=None):
    D.poli([W.p(x, y) for x, y in loop], lw, cor=cor, fechar=True)


def furo(D, W, f, marca=True, lw=L_CONTORNO, cor="#111", dash=None):
    cx, cy, r = f
    x, y = W.p(cx, cy)
    D.circ(x, y, r, lw, cor=cor, dash=dash)
    if marca:
        D.centro(x, y, r)


def tabela_furos(D, x, y, grupos, titulo, por_coluna=10, larg_col=105.0):
    """
    Tabela de coordenadas. Quebra em colunas lado a lado em vez de descer:
    o painel tem 17 furos e uma coluna unica invadiria a legenda.
    'grupos' e uma lista de (rotulo, cx, cy, diametro).
    """
    D.txt(x, y - 2.4, titulo, 2.8, anc="start", peso="bold", cor=C_TXT)
    cab = ("FURO", "X [mm]", "Y [mm]", "&#216;")
    larg = (26, 26, 26, 24)
    fim = y
    for i in range(0, len(grupos), por_coluna):
        bloco = grupos[i:i + por_coluna]
        linhas = [(n, vg(cx), vg(cy), dm(d)) for n, cx, cy, d in bloco]
        fim = max(fim, D.tabela(x + (i // por_coluna) * larg_col, y,
                                cab, linhas, larg))
    return fim


def rotulos(prefixo, furos):
    return [(f"{prefixo}{i}", f[0], f[1], 2 * f[2])
            for i, f in enumerate(furos, 1)]


# =====================================================================
# 1. Painel dos botoes
# =====================================================================

def medir_painel(V, T):
    """Tudo o que a prancha do painel precisa, medido na malha."""
    cam = camadas(V, T)
    zs = niveis(V)
    esp = zs[-1]
    m = dict(esp=esp, zs=zs)

    base = cam[0][3]                       # camada de baixo: todos os passantes
    topo = cam[-1][3]                      # camada de cima: rebaixos
    m["contorno"] = cam[0][2][0]
    m["R"] = raio_canto(m["contorno"])
    m["larg"] = max(p[0] for p in m["contorno"]) - min(p[0] for p in m["contorno"])
    m["alt"] = max(p[1] for p in m["contorno"]) - min(p[1] for p in m["contorno"])

    rs = raios(base)
    m["barril"] = por_raio(base, max(r for r in rs if r > 8))
    m["led"] = por_raio(base, sorted(r for r in rs if 3 < r < 8)[0])
    m["passagem"] = por_raio(base, min(rs))
    # o rebaixo da cabeca e o MENOR furo da camada de cima - os dois maiores
    # sao os rebaixos das capas
    m["rebaixo_cab"] = por_raio(topo, min(raios(topo)))

    # rebaixos das capas: os furos grandes da camada de cima
    m["rebaixos"] = sorted([f for f in topo if f[2] > 20], key=lambda f: -f[2])

    # profundidade de cada rebaixo: primeira camada, de baixo para cima, em
    # que ele aparece. E medicao, nao suposicao - nao depende de o rebaixo
    # maior ser o mais fundo.
    m["prof"] = []
    for cx, cy, r in m["rebaixos"]:
        z0 = next(c[0] for c in cam
                  if any(abs(f[2] - r) < 0.05 and
                         math.hypot(f[0] - cx, f[1] - cy) < 0.05 for f in c[3]))
        m["prof"].append(esp - z0)
    m["z_cab"] = next(c[0] for c in cam
                      if any(abs(f[2] - m["rebaixo_cab"][0][2]) < 0.05
                             for f in c[3]))
    m["reb_cab"] = esp - m["z_cab"]

    # cada rebaixo com o barril que ele serve, e a circunferencia dos LEDs
    m["botoes"] = []
    for (cx, cy, r), prof in zip(m["rebaixos"], m["prof"]):
        bar = min(m["barril"], key=lambda f: math.hypot(f[0] - cx, f[1] - cy))
        sob = [f for f in m["led"] if math.hypot(f[0] - cx, f[1] - cy) < r]
        rf = sum(math.hypot(f[0] - cx, f[1] - cy) for f in sob) / len(sob)
        m["botoes"].append(dict(x=cx, y=cy, r=r, prof=prof, barril=bar,
                                leds=sob, rf=rf))
    m["botoes"].sort(key=lambda b: b["x"])
    return m


def desenho_painel():
    V, T = ler_3mf("caixa-painel.3mf")
    m = medir_painel(V, T)
    esp = m["esp"]

    # ---- conferencia contra o modelo ----
    bate("painel: espessura", esp, P.PAIN_ESP)
    bate("painel: largura", m["larg"], P.CX_L)
    bate("painel: profundidade", m["alt"], P.CX_A)
    bate("painel: raio de canto", m["R"], P.CX_R)
    bate("painel: rebaixo da cabeca", m["reb_cab"], P.REB_PAINEL)
    bate("painel: Ø de passagem", 2 * m["passagem"][0][2], P.D_PASSAGEM)
    bate("painel: Ø do barril", 2 * m["barril"][0][2], P.D_BARRIL)
    bate("painel: Ø do LED", 2 * m["led"][0][2], P.D_LED)
    bate("painel: n de furos de fixacao", len(m["passagem"]), 6)
    for b, pb in zip(m["botoes"], sorted(P.BOTOES, key=lambda b: b["x"])):
        bate(f"painel: rebaixo {pb['nome']} Ø",
             2 * b["r"], pb["capa"] + P.FOLGA_CAPA)
        bate(f"painel: rebaixo {pb['nome']} profundidade", b["prof"], pb["rebaixo"])
    bv, bg = m["botoes"]
    pv, pg = sorted(P.BOTOES, key=lambda b: b["x"])

    entre = bg["x"] - bv["x"]
    folga_capa = entre - pv["capa"] / 2 - pg["capa"] / 2
    nervura = entre - bv["r"] - bg["r"]

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - PAINEL DOS BOTÕES",
                "Vista superior, corte pelos eixos e detalhe do botão embutido",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-01")
    W = Vista(60, 52, m["larg"], m["alt"])

    # ---------------- vista superior ----------------
    contorno(D, m["contorno"], W)
    for b in m["botoes"]:
        furo(D, W, (b["x"], b["y"], b["r"]))
        furo(D, W, b["barril"], marca=False)
        D.circ(*W.p(b["x"], b["y"]), b["rf"], L_TRACO, cor=C_ATEN, dash=D_CENTRO)
    for f in m["led"]:
        furo(D, W, f, marca=False)
    for f, g in zip(m["passagem"], m["rebaixo_cab"]):
        furo(D, W, g)
        furo(D, W, f, marca=False, lw=L_TRACO, cor="#555", dash=D_OCULTA)

    yb = W.py(0)
    D.cota_h(W.px(0), W.px(bv["x"]), yb + 14, vg(bv["x"]), yb)
    D.cota_h(W.px(bv["x"]), W.px(bg["x"]), yb + 14, f"{vg(entre)} entre centros",
             W.py(bv["y"]))
    D.cota_h(W.px(0), W.px(m["larg"]), yb + 26, vg(m["larg"]), yb)
    D.cota_v(W.py(bv["y"]), yb, W.px(0) - 14, vg(bv["y"]), W.px(0))
    D.cota_v(W.py(m["alt"]), yb, W.px(0) - 28, vg(m["alt"]), W.px(0))
    for b in m["botoes"]:
        D.cota_h(W.px(b["x"]) - b["rf"], W.px(b["x"]) + b["rf"],
                 W.py(m["alt"]) - 14, dm(2 * b["rf"]),
                 W.py(b["y"] + b["rf"]), tam=FONTE_P)

    # diametro e profundidade de cada rebaixo, na folga entre a vista e a
    # coluna de notas - no alto da vista nao cabe mais nenhuma cota
    for b, comp in zip(m["botoes"], (90, 60)):
        D.chamada(*W.p(b["x"], b["y"]), b["r"],
                  f"{dm(2*b['r'])} x {vg(b['prof'])} rebaixo", ang=-30,
                  comp=comp, tam=FONTE_P)

    D.bandeira(*W.p(bv["barril"][0], bv["barril"][1] + bv["barril"][2]), 1,
               ang=-118, comp=20)
    D.bandeira(*W.p(bv["x"], bv["y"] + bv["r"]), 2, ang=-72, comp=22)
    D.bandeira(*W.p(bg["leds"][0][0], bg["leds"][0][1] - bg["leds"][0][2]), 3,
               ang=64, comp=20)
    D.bandeira(*W.p(*m["rebaixo_cab"][0][:2]), 4, ang=-135, comp=20)
    D.bandeira(W.px(m["larg"] - m["R"] * 0.293), W.py(m["alt"] - m["R"] * 0.293),
               5, ang=-38, comp=18)
    linha_de_corte(D, W, m["larg"], bv["y"], "A")
    D.rotulo_vista(W.px(m["larg"] / 2), yb + 38, "VISTA SUPERIOR", "1:1")

    # ---------------- corte pelos eixos dos botoes ----------------
    _corte_painel(D, W.px(0), 292.0, m, esp, S=3.0)

    # ---------------- coluna direita ----------------
    y = D.notas(COL_DIR, 40, [
        (1, f"2x {dm(2*bv['barril'][2])} - passagem do barril M24 do botão "
            f"(especificação Adafruit)."),
        (2, f"2x rebaixo de assento da capa: {dm(2*bv['r'])} x "
            f"{vg(bv['prof'])} ({pv['nome']}) e {dm(2*bg['r'])} x "
            f"{vg(bg['prof'])} ({pg['nome']}). O flange do botão apoia no FUNDO"),
        (None, f"do rebaixo, então o conjunto inteiro desce por esse valor - a "
               f"capa fica {vg(pv['h_capa']-bv['prof'])} mm para fora no "
               f"{pv['nome']} e {vg(pg['h_capa']-bg['prof'])} mm no {pg['nome']}, "
               f"metade da altura de cada capa."),
        (None, f"O diâmetro do rebaixo é o da capa mais {vg(P.FOLGA_CAPA)} de "
               f"folga diametral. É ajuste aparente, não de montagem: conferir "
               f"num corpo de prova com os dois"),
        (None, "diâmetros antes de imprimir o painel inteiro."),
        (3, f"{len(m['led'])}x {dm(2*m['led'][0][2])} passantes, sob as capas: "
            f"{len(bv['leds'])} a {vg(360/len(bv['leds']))}&#176; sobre "
            f"{dm(2*bv['rf'])} e {len(bg['leds'])} a "
            f"{vg(360/len(bg['leds']))}&#176; sobre {dm(2*bg['rf'])}."),
        (4, f"{len(m['passagem'])}x {dm(2*m['passagem'][0][2])} com rebaixo "
            f"{dm(2*m['rebaixo_cab'][0][2])} x {vg(m['reb_cab'])} - fixação no "
            f"corpo com M3 x {P.PAIN_ESP-P.REB_PAINEL+P.PENETRACAO:.0f} ISO 7380"),
        (None, "em inserto de latão M3 na coluna do corpo (ver PIBIC-CX-02)."),
        (5, f"Contorno externo {vg(m['larg'])} x {vg(m['alt'])}, cantos "
            f"R{vg(m['R'])} nos quatro cantos."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=250)

    y = D.notas(COL_DIR, y + 4, [
        (None, f"Espessura {vg(esp)} mm. O rebaixo desconta do trecho que a "
               f"porca M24 aperta: sobram {vg(esp-bv['prof'])} mm no "
               f"{pv['nome']} e {vg(esp-bg['prof'])} mm no {pg['nome']},"),
        (None, f"os dois dentro dos {vg(pv['esp_max'])} mm máximos admitidos "
               f"pelo botão. Foi por isso que o painel passou de 10 para "
               f"{vg(esp)} mm: sem engordar, o rebaixo comeria a rosca."),
        (None, f"Folga livre entre as capas {vg(folga_capa)} mm e nervura de "
               f"{vg(nervura)} mm entre os dois rebaixos. É o que sobra ao "
               f"manter os dois botões no mesmo eixo"),
        (None, f"dentro dos {P.MESA[0]:.0f} mm de mesa da Bambu Lab A1 mini - "
               f"só as duas capas já somam {vg(pv['capa']+pg['capa'])} mm."),
        (None, "Imprimir com a face interna na mesa: todos os rebaixos abrem "
               "para cima e a peça não pede um milímetro de suporte."),
        (None, "Anti-rotação: o pino do flange não está cotado na documentação "
               "do fabricante. Medir no botão físico antes de abrir o "
               "rasgo, ou travar com cola quente."),
    ], titulo="OBSERVAÇÕES DE PROJETO", larg=250)

    _detalhe_embutido(D, 430, y + 46, m, esp, pv)

    itens = (rotulos("BARRIL ", m["barril"]) + rotulos("LED ", m["led"])
             + rotulos("FIX ", m["rebaixo_cab"]))
    tabela_furos(D, COL_DIR, 300, itens,
                 "COORDENADAS DOS FUROS - origem no canto inferior esquerdo")
    D.salvar("desenho-caixa-painel.svg")


def _corte_painel(D, ox, oy, m, esp, S=3.0):
    """
    Corte pelos eixos dos dois botoes, com escala vertical S. As capas entram
    em linha de referencia, na mesma escala vertical, porque o assunto da
    prancha e exatamente quanto delas fica para fora.
    """
    larg = m["larg"]
    base = oy + esp * S

    for b in m["botoes"]:
        # capa em fantasma, apoiada no fundo do rebaixo
        pb = min(P.BOTOES, key=lambda q: abs(q["x"] - b["x"]))
        y_fundo = oy + b["prof"] * S
        y_topo = y_fundo - pb["h_capa"] * S
        r = pb["capa"] / 2
        domo(D, ox + b["x"], y_fundo, r, pb["h_capa"] * S)
        D.cota_v(y_topo, oy, ox + b["x"] + r + 8,
                 vg(pb["h_capa"] - b["prof"]), ox + b["x"] + r, tam=FONTE_P)

    # corpo do painel, com os rebaixos abertos por cima
    D.hachura(ox, oy, larg, esp * S)
    for b in m["botoes"]:
        D.ret(ox + b["x"] - b["r"], oy, 2 * b["r"], b["prof"] * S,
              L_CONTORNO, fill="#fff")
        D.ret(ox + b["barril"][0] - b["barril"][2], oy,
              2 * b["barril"][2], esp * S, L_CONTORNO, fill="#fff")
        for f in b["leds"]:
            D.ret(ox + f[0] - f[2], oy, 2 * f[2], esp * S, L_CONTORNO, fill="#fff")
    for f, g in zip(m["passagem"], m["rebaixo_cab"]):
        D.ret(ox + f[0] - f[2], oy, 2 * f[2], esp * S, L_CONTORNO, fill="#fff")
        D.ret(ox + g[0] - g[2], oy, 2 * g[2], m["reb_cab"] * S,
              L_CONTORNO, fill="#fff")

    b = m["botoes"][0]
    D.cota_v(oy, oy + b["prof"] * S, ox - 12, vg(b["prof"]), ox, tam=FONTE_P)
    D.cota_v(oy + b["prof"] * S, base, ox - 12, vg(esp - b["prof"]), ox,
             tam=FONTE_P)
    D.cota_v(oy, base, ox - 26, vg(esp), ox, tam=FONTE_P)
    for b, dy in zip(m["botoes"], (10, 20)):
        D.cota_h(ox + b["x"] - b["r"], ox + b["x"] + b["r"], base + dy,
                 dm(2 * b["r"]), base, tam=FONTE_P)
    D.rotulo_vista(ox + larg / 2, base + 32,
                   "CORTE A-A pelos eixos dos botões", f"vertical {S:.0f}:1")


def _detalhe_embutido(D, ox, oy, m, esp, pv):
    """
    O detalhe que da nome a revisao: quanto do botao entra no painel.
    Escala horizontal 1:1 e vertical 2:1 - a capa tem quase 100 mm de
    diametro e 17,5 de altura; na mesma escala nos dois eixos, ou o detalhe
    nao cabe na prancha ou a altura vira um risco.
    """
    b = m["botoes"][0]
    SV = 2.0
    r_cap = pv["capa"] / 2
    y_fundo = oy + b["prof"] * SV
    y_base = oy + esp * SV
    y_topo = y_fundo - pv["h_capa"] * SV
    W = r_cap + 16

    # painel em corte, com o rebaixo e o furo do barril
    rb, rf = b["r"], b["barril"][2]
    for sg in (-1, 1):
        D.hachura_poli([(ox + sg * rf, y_base), (ox + sg * rf, y_fundo),
                        (ox + sg * rb, y_fundo), (ox + sg * rb, oy),
                        (ox + sg * W, oy), (ox + sg * W, y_base)])

    # botao em linha de referencia
    domo(D, ox, y_fundo, r_cap, pv["h_capa"] * SV, fechar=True)
    for sg in (-1, 1):                       # barril M24 atravessando
        D.linha(ox + sg * 12, y_fundo, ox + sg * 12, y_base + 9 * SV,
                L_TRACO, C_REF, dash=D_OCULTA)
    D.ret(ox - 15, y_base, 30, 5 * SV, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + 17, y_base + 5 * SV - 1.5, "porca M24 (ref.)", FONTE_P,
          anc="start", cor=C_REF)
    D.txt(ox + r_cap * 0.55, y_topo - 2.5,
          f"capa {dm(pv['capa'])} (ref.)", FONTE_P, anc="start", cor=C_REF)

    # cotas
    D.cota_v(y_topo, oy, ox + W + 10, vg(pv["h_capa"] - b["prof"]), ox + r_cap,
             tam=FONTE_P)
    D.txt(ox + W + 14, (y_topo + oy) / 2, "para fora", FONTE_P, anc="start",
          cor=C_COTA)
    D.cota_v(oy, y_fundo, ox - W - 10, vg(b["prof"]), ox - W, tam=FONTE_P)
    D.txt(ox - W - 14, (oy + y_fundo) / 2, "rebaixo", FONTE_P, anc="end",
          cor=C_COTA)
    D.cota_v(y_fundo, y_base, ox - W - 10, vg(esp - b["prof"]), ox - W,
             tam=FONTE_P)
    D.txt(ox - W - 14, (y_fundo + y_base) / 2, "apertado pela porca", FONTE_P,
          anc="end", cor=C_COTA)
    D.cota_v(oy, y_base, ox - W - 26, vg(esp), ox - W, tam=FONTE_P)
    D.cota_h(ox - rb, ox + rb, oy - 8, dm(2 * rb), oy, tam=FONTE_P)
    D.cota_h(ox - rf, ox + rf, y_base + 26, dm(2 * rf), y_base, tam=FONTE_P)

    D.rotulo_vista(ox, y_base + 40,
                   f"DETALHE - botão {pv['nome']} meio embutido",
                   "horizontal 1:1, vertical 2:1")


# =====================================================================
# 2. Corpo
# =====================================================================

def desenho_corpo():
    V, T = ler_3mf("caixa-corpo.3mf")
    cam = camadas(V, T)
    zs = niveis(V)
    hh = zs[-1]
    prof = zs[1]                                # furo de inserto de baixo

    # 'analisar' ja devolve os contornos por extensao em x decrescente, entao
    # conts[0] e o externo. Nao da para desempatar por contagem de pontos: a
    # cavidade tem MAIS pontos que o contorno externo, por causa dos seis
    # arcos das colunas.
    ext, cav = cam[1][2][0], cam[1][2][1]
    larg = max(p[0] for p in ext) - min(p[0] for p in ext)
    alt = max(p[1] for p in ext) - min(p[1] for p in ext)
    Re = raio_canto(ext)
    ins = cam[0][3]
    dins = 2 * ins[0][2]
    par = min(dist_ate(p, ext) for p in cav)

    fix = [(f[0], f[1]) for f in ins]
    col = 2 * max(raio_coluna(V, fx, fy, dins / 2 + 0.5, P.FIX_INSET - 0.2)
                  for fx, fy in fix)

    larg_i = max(p[0] for p in cav) - min(p[0] for p in cav)
    alt_i = max(p[1] for p in cav) - min(p[1] for p in cav)
    Ri = raio_canto(cav)

    bate("corpo: altura", hh, P.CORPO_H)
    bate("corpo: largura", larg, P.CX_L)
    bate("corpo: profundidade", alt, P.CX_A)
    bate("corpo: raio de canto", Re, P.CX_R)
    # a parede sai do corte, entao carrega o erro do ponto medio de corda
    # descrito em 'raio_vertice' - 0,05 e o que ele vale, nao complacencia
    bate("corpo: parede", par, P.CORPO_PAR, tol=0.05)
    bate("corpo: Ø da coluna", col, P.COL_D)
    bate("corpo: Ø do inserto", dins, P.D_INSERTO)
    bate("corpo: profundidade do inserto", prof, P.PROF_INSERTO)
    bate("corpo: n de colunas", len(ins), 6)
    bate("corpo: insertos nas duas pontas", len(cam[-1][3]), len(ins))

    sw = _interruptor(V, larg, alt, Re, fix, col)
    assert sw, "estacao do interruptor nao encontrada na malha do corpo"
    E = P.estacao()
    bate("interruptor: parede no berco", sw["par"], P.CORPO_PAR)
    bate("interruptor: x do eixo", sw["x"], E["x"])
    bate("interruptor: z do eixo", sw["z"], E["z"])
    bate("interruptor: fundo da bolsa", sw["fundo"], E["fundo"])
    bate("interruptor: bolsa em x", sw["bolsa_l"], E["bolsa_l"])
    bate("interruptor: bolsa em z", sw["bolsa_h"], E["bolsa_h"])
    bate("interruptor: profundidade da bolsa", sw["bolsa_p"], E["bolsa_p"])
    bate("interruptor: rasgo em x", sw["rasgo_l"], E["rasgo_l"])
    bate("interruptor: rasgo em z", sw["rasgo_h"], E["rasgo_h"])
    bate("interruptor: largura do ressalto", sw["res_l"], E["res_l"])
    bate("interruptor: topo do ressalto", sw["z_topo"], E["z_topo"])
    bate("interruptor: avanco sobre a cavidade", sw["saliencia"], E["saliencia"])

    L_pain = P.PAIN_ESP - P.REB_PAINEL + P.PENETRACAO
    L_tampa = P.TAMPA_ESP - P.REB_TAMPA + P.PENETRACAO

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - CORPO",
                "Vista frontal, vista superior, corte da parede e detalhe",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-02")

    # ---------------- vista frontal ----------------
    OX = 60.0
    _vista_frontal(D, OX, 40.0, larg, hh, par, P.PAIN_ESP, P.TAMPA_ESP, Re,
                   sorted({round(f[0], 3) for f in ins}), dins, prof, sw)

    # ---------------- vista superior ----------------
    W = Vista(OX, 180, larg, alt)
    contorno(D, ext, W)
    contorno(D, cav, W)
    for f in ins:
        furo(D, W, f)

    # Berco, em posicao verdadeira na parede de tras. O contorno do ressalto
    # e visto (e material que avanca sobre a cavidade); bolsa e rasgo estao
    # atras dele, ocultos por esta vista.
    D.ret(W.px(sw["x"] - sw["res_l"] / 2), W.py(alt),
          sw["res_l"], sw["prof"], L_CONTORNO)
    D.ret(W.px(sw["x"] - sw["bolsa_l"] / 2), W.py(alt - sw["fundo"]),
          sw["bolsa_l"], sw["bolsa_p"], L_TRACO, cor="#555", dash=D_OCULTA)
    D.linha(W.px(sw["x"] - sw["rasgo_l"] / 2), W.py(alt),
            W.px(sw["x"] + sw["rasgo_l"] / 2), W.py(alt), 0.9, C_ATEN)
    D.centro(W.px(sw["x"]), W.py(alt - sw["prof"] / 2), sw["res_l"] / 2 + 3)

    yb = W.py(0)
    xs = sorted({round(f[0], 3) for f in ins})
    ys = sorted({round(f[1], 3) for f in ins})
    D.cota_h(W.px(0), W.px(xs[0]), W.py(alt) - 14, vg(xs[0]), W.py(alt))
    D.cota_h(W.px(0), W.px(xs[1]), W.py(alt) - 26, vg(xs[1]), W.py(alt))
    D.cota_h(W.px(0), W.px(larg), yb + 26, vg(larg), yb)
    D.cota_v(W.py(alt), yb, W.px(0) - 28, vg(alt), W.px(0))
    D.cota_v(W.py(ys[0]), yb, W.px(larg) + 14, vg(ys[0]), W.px(larg))
    D.cota_v(W.py(ys[1]), yb, W.px(larg) + 28, vg(ys[1]), W.px(larg))

    D.bandeira(*W.p(xs[2], ys[2] + dins / 2), 2, ang=-45, comp=18)
    D.bandeira(W.px(larg - Re * 0.293), W.py(alt - Re * 0.293), 3,
               ang=-30, comp=18)
    D.rotulo_vista(W.px(larg / 2), yb + 38, "VISTA SUPERIOR", "1:1")

    # ---------------- corte da parede e detalhe da coluna ----------------
    xw = COL_DIR + 10
    D.hachura(xw, 46, par, hh)
    D.cota_v(46, 46 + hh, xw - 12, vg(hh), xw)
    D.cota_h(xw, xw + par, 40, vg(par), 46, tam=FONTE_P)
    D.rotulo_vista(xw + par / 2 + 6, 46 + hh + 10, "CORTE DA PAREDE", "1:1")

    _detalhe_coluna(D, 460, 50, par, col, prof, dins, hh)

    # ---------------- notas ----------------
    y = D.notas(COL_DIR, 150, [
        (1, f"Parede {vg(par)} mm. O modelo anterior tinha 10,00; a redução "
            f"foi o que devolveu o espaço interno perdido ao encolher a "
            f"silhueta para caber"),
        (None, f"na mesa de {P.MESA[0]:.0f} x {P.MESA[1]:.0f} mm da Bambu Lab "
               f"A1 mini."),
        (2, f"{len(ins)} colunas {dm(col)} PASSANTES, com furo {dm(dins)} x "
            f"{vg(prof)} nas DUAS pontas - inserto roscado de latão M3 "
            f"aplicado a quente."),
        (None, f"São {2*len(ins)} insertos, não {len(ins)}: em cima prendem o "
               f"painel, embaixo a tampa. Coordenadas na tabela abaixo."),
        (3, f"Contorno externo {vg(larg)} x {vg(alt)}, cantos R{vg(Re)}. "
            f"Cavidade {vg(larg_i)} x {vg(alt_i)}, cantos R{vg(Ri)}, com a "
            f"mordida das {len(ins)} colunas."),
        (4, f"Fixação: em cima {len(ins)}x M3 x {L_pain:.0f} ISO 7380 "
            f"(painel de {vg(P.PAIN_ESP)}), embaixo {len(ins)}x M3 x "
            f"{L_tampa:.0f} ISO 7380 (tampa de {vg(P.TAMPA_ESP)})."),
    ] + _notas_interruptor(sw, alt, Re, par), titulo="NOTAS DE FABRICAÇÃO",
        larg=250)

    y = D.notas(COL_DIR, y + 4, [
        (None, f"Altura da caixa montada = {vg(P.PAIN_ESP)} (painel) + "
               f"{vg(hh)} (corpo) + {vg(P.TAMPA_ESP)} (tampa) = "
               f"{vg(P.PAIN_ESP + hh + P.TAMPA_ESP)} mm."),
        (None, "Imprimir em pé, como está modelado: as duas faces são planas "
               "e as camadas ficam perpendiculares ao eixo dos parafusos. "
               "SEM SUPORTE - o ressalto do berço"),
        (None, f"desce até a base justamente para não ficar em balanço; o "
               f"único trecho sobre o vazio é o teto da bolsa, uma ponte "
               f"reta de {vg(sw['bolsa_l'])} mm."),
        (None, f"NÃO há passagem de cabo no modelo. O rasgo de "
               f"{vg(sw['rasgo_l'])} x {vg(sw['rasgo_h'])} é da haste do "
               f"interruptor e não serve de passagem. Definir posição e "
               f"diâmetro do prensa-cabo"),
        (None, "junto com o microcontrolador - de preferência nesta mesma "
               "parede, entre x = 94 e x = 123, que é o resto do trecho reto "
               "livre."),
    ], titulo="OBSERVAÇÕES DE PROJETO", larg=250)

    itens = ([(f"COLUNA {i} topo", f[0], f[1], dins)
              for i, f in enumerate(ins, 1)]
             + [(f"COLUNA {i} base", f[0], f[1], dins)
                for i, f in enumerate(ins, 1)])
    tabela_furos(D, COL_DIR, y + 14, itens,
                 "FUROS DE INSERTO - origem no canto inferior esquerdo",
                 por_coluna=6)
    D.salvar("desenho-caixa-corpo.svg")


def _interruptor(V, larg, alt, Re, fix, col):
    """
    Le a estacao do interruptor DIRETO dos vertices do corpo.

    Ela e a unica feicao da peca que nao e prismatica: nao aparece em
    'camadas' e nao tem diametro para 'analisar' medir. O que a denuncia e a
    contagem de PLANOS. Num trecho reto da parede de tras, longe das
    colunas, a peca so deveria ter dois planos em y - a face externa e a face
    interna. Onde ha o berco aparecem mais dois, e os quatro saem ordenados:

        y[0]  face do ressalto     y[2]  fundo da bolsa
        y[1]  face interna         y[3]  face externa

    Dai vem tudo, inclusive a parede - que assim sai EXATA, e nao pela
    estimativa de corda que a medicao de perimetro devolve.

    Os dois filtros existem por motivos concretos: sem afastar das colunas, o
    furo de inserto da coluna central passa de y = 126 (o furo de 4,20 num
    centro a 6,00 da face chega a 126,10) e vira um quinto plano; sem entrar
    um pouco no trecho reto, um vertice de arco de canto entra como sexto.
    """
    tol = 1e-4
    dentro = [v for v in V
              if Re + 1.0 <= v[0] <= larg - Re - 1.0 and v[1] > alt / 2
              and all(math.hypot(v[0] - cx, v[1] - cy) > col / 2 + tol
                      for cx, cy in fix)]
    planos = sorted({round(v[1], 4) for v in dentro})
    if len(planos) == 2:
        return None                       # parede lisa - nao ha estacao
    assert len(planos) == 4, (
        f"parede de tras com {len(planos)} planos em y ({planos}) - "
        f"esperado 2 (parede lisa) ou 4 (parede com o berco)")
    y_res, y_cav, y_piso, y_face = planos
    assert abs(y_face - alt) < tol, "o maior plano nao e a face externa"

    def grupo(y):
        return [v for v in dentro if abs(v[1] - y) < tol]

    piso, face = grupo(y_piso), grupo(y_res)
    xs = sorted({round(v[0], 4) for v in piso})
    zs = sorted({round(v[2], 4) for v in piso})
    assert len(xs) == 4 and len(zs) == 4, (
        f"fundo da bolsa com {len(xs)} cotas em x e {len(zs)} em z - "
        f"esperado 4 e 4, que sao a bolsa e o rasgo")

    s = dict(modelo=getattr(P, "INTERRUPTOR", {}).get("modelo", "?"))
    s["par"] = y_face - y_cav
    s["fundo"] = y_face - y_piso
    s["prof"] = y_face - y_res
    s["bolsa_p"] = s["prof"] - s["fundo"]
    s["saliencia"] = s["prof"] - s["par"]
    s["bolsa_l"], s["rasgo_l"] = xs[3] - xs[0], xs[2] - xs[1]
    s["bolsa_h"], s["rasgo_h"] = zs[3] - zs[0], zs[2] - zs[1]
    s["x"], s["z"] = (xs[0] + xs[3]) / 2, (zs[0] + zs[3]) / 2
    assert abs((xs[1] + xs[2]) / 2 - s["x"]) < tol, "rasgo fora do eixo da bolsa"
    assert abs((zs[1] + zs[2]) / 2 - s["z"]) < tol, "rasgo fora do eixo da bolsa"

    xr = sorted({round(v[0], 4) for v in face})
    s["res_l"] = xr[-1] - xr[0]
    s["nervura"] = (s["res_l"] - s["bolsa_l"]) / 2
    s["z_topo"] = max(v[2] for v in face)
    assert abs((xr[0] + xr[-1]) / 2 - s["x"]) < tol, "ressalto fora do eixo"
    assert min(v[2] for v in face) < tol, \
        "ressalto nao desce ate a base - imprimiria em balanco"
    s["reto"] = (Re, larg - Re)
    return s


def _notas_interruptor(sw, alt, Re, par):
    """Resumo na CX-02; quem detalha o berço é a PIBIC-CX-04."""
    haste = getattr(P, "INTERRUPTOR", {}).get("haste", 0.0)
    return [
        (5, f"BERÇO DO INTERRUPTOR {sw['modelo']} na parede y = {vg(alt)}, "
            f"eixo da haste a {vg(sw['x'])} da aresta esquerda e "
            f"{vg(sw['z'])} da base. Ressalto {vg(sw['res_l'])} de largura"),
        (None, f"avançando {vg(sw['saliencia'])} sobre a cavidade, do piso "
               f"até z = {vg(sw['z_topo'])}; bolsa {vg(sw['bolsa_l'])} x "
               f"{vg(sw['bolsa_h'])} x {vg(sw['bolsa_p'])}, aberta para "
               f"dentro; rasgo da haste {vg(sw['rasgo_l'])} x "
               f"{vg(sw['rasgo_h'])},"),
        (None, f"único furo para fora, com {vg(haste - sw['fundo'])} mm de "
               f"haste sobrando. Prende com COLA QUENTE, sem parafuso. "
               f"COTAS, MONTAGEM E RESSALVAS: ver PIBIC-CX-04."),
        (6, f"A parede só é plana entre x = {vg(sw['reto'][0])} e "
            f"x = {vg(sw['reto'][1])} (tangência dos raios R{vg(Re)}) e a "
            f"coluna central ocupa x = 84,00 a 94,00. O berço fica em"),
        (None, f"{vg(sw['x'] - sw['res_l']/2)} a "
               f"{vg(sw['x'] + sw['res_l']/2)}, com "
               f"{vg(sw['x'] - sw['res_l']/2 - sw['reto'][0])} mm de sobra "
               f"dos dois lados - e não em x = 56,00, no eixo do botão "
               f"vermelho, onde invadiria 7,60 mm do raio."),
    ]


def _vista_frontal(D, ox, y_top, larg, hh, par, esp_pain, esp_tampa, Re,
                   xs, dins, prof, sw):
    """
    Elevacao do corpo, com painel e tampa em linha de referencia para dar a
    altura da caixa montada. No 1o diedro a vista superior fica abaixo desta,
    entao a face que aparece aqui e a aresta de baixo daquela.
    """
    y_p0 = y_top                       # topo do painel
    y_c0 = y_p0 + esp_pain             # topo do corpo
    y_c1 = y_c0 + hh                   # base do corpo
    y_t1 = y_c1 + esp_tampa            # base da tampa

    D.ret(ox, y_p0, larg, esp_pain, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + larg + 4, y_p0 + esp_pain / 2, "PAINEL (ref.)", FONTE_P,
          anc="start", cor=C_REF)
    D.ret(ox, y_c1, larg, esp_tampa, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + larg + 4, y_t1 - 1, "TAMPA (ref.)", FONTE_P, anc="start",
          cor=C_REF)
    D.ret(ox, y_c0, larg, hh, L_CONTORNO)

    for x in (ox + par, ox + larg - par):
        D.linha(x, y_c0, x, y_c1, L_TRACO, "#555", dash=D_OCULTA)
    for x in xs:                       # colunas e furos de inserto
        D.linha(ox + x - dins / 2, y_c0, ox + x - dins / 2, y_c1,
                L_TRACO, "#555", dash=D_OCULTA)
        D.linha(ox + x + dins / 2, y_c0, ox + x + dins / 2, y_c1,
                L_TRACO, "#555", dash=D_OCULTA)
        D.linha(ox + x - dins / 2, y_c0 + prof, ox + x + dins / 2, y_c0 + prof,
                L_TRACO, "#555", dash=D_OCULTA)
        D.linha(ox + x - dins / 2, y_c1 - prof, ox + x + dins / 2, y_c1 - prof,
                L_TRACO, "#555", dash=D_OCULTA)

    for x in sw["reto"]:
        D.linha(ox + x, y_p0 - 6, ox + x, y_t1 + 6, L_TRACO, C_ATEN,
                dash=D_CENTRO)

    # O berco esta na parede de TRAS, entao nesta vista ele e feicao oculta:
    # tres retangulos concentricos em linha tracejada. Quem mede a montagem
    # aqui e a altura; a espessura e assunto do detalhe ampliado.
    xs_c, ys_c = ox + sw["x"], y_c1 - sw["z"]
    for l, h, y0, y1 in (
            (sw["res_l"], None, y_c1 - sw["z_topo"], y_c1),
            (sw["bolsa_l"], sw["bolsa_h"], None, None),
            (sw["rasgo_l"], sw["rasgo_h"], None, None)):
        if h is None:
            D.ret(xs_c - l / 2, y0, l, y1 - y0, L_TRACO, cor="#555",
                  dash=D_OCULTA)
        else:
            D.ret(xs_c - l / 2, ys_c - h / 2, l, h, L_TRACO, cor="#555",
                  dash=D_OCULTA)
    D.centro(xs_c, ys_c, sw["bolsa_l"] / 2 + 3)
    D.bandeira(xs_c - sw["res_l"] / 2, y_c1 - sw["z_topo"], 5,
               ang=-125, comp=18)

    D.cota_v(y_c0, y_c1, ox - 14, vg(hh), ox)
    D.cota_v(y_p0, y_t1, ox - 28, vg(hh + esp_pain + esp_tampa), ox)
    D.cota_h(ox, xs_c, y_t1 + 14, vg(sw["x"]), y_t1)
    D.cota_h(xs_c - sw["res_l"] / 2, xs_c + sw["res_l"] / 2, y_t1 + 26,
             vg(sw["res_l"]), y_c1, tam=FONTE_P)
    D.cota_v(ys_c, y_c1, ox + larg + 20, vg(sw["z"]), ox + larg)
    D.cota_v(y_c1 - sw["z_topo"], y_c1, ox + larg + 34, vg(sw["z_topo"]),
             ox + larg, tam=FONTE_P)
    D.rotulo_vista(ox + larg / 2, y_t1 + 38, "VISTA FRONTAL", "1:1")


def _detalhe_coluna(D, ox, oy, par, col, prof, dfuro, hh):
    """
    A coluna vista de cima, em corte, com os dois furos de inserto. Mostra a
    coisa que a vista superior nao consegue mostrar: a coluna nasce na parede
    e avanca sobre a cavidade, e e por isso que o furo de Ø4,20 cabe numa
    peca de parede 4,00.
    """
    S = 4.0
    cx = ox
    cy = oy + P.FIX_INSET * S
    R = col / 2 * S
    W = 34.0
    y1 = oy + par * S                       # face interna da parede

    # Contorno da UNIAO parede + coluna, num traco so. Desenhar os dois
    # separados poe uma linha de contorno atravessando material continuo, que
    # e justamente o que este detalhe quer negar: a coluna nao esta encostada
    # na parede, ela e a parede engrossada.
    dx = math.sqrt(max(R * R - (y1 - cy) ** 2, 0.0))
    pts = [(cx - W, oy), (cx + W, oy), (cx + W, y1), (cx + dx, y1)]
    a0 = math.atan2(y1 - cy, dx)
    a1 = math.atan2(y1 - cy, -dx)
    n = 48
    pts += [(cx + R * math.cos(a0 + (math.pi - 2 * a0) * i / n),
             cy + R * math.sin(a0 + (math.pi - 2 * a0) * i / n))
            for i in range(1, n)]
    pts += [(cx - dx, y1), (cx - W, y1)]
    D.hachura_poli(pts)

    D.circ(cx, cy, dfuro / 2 * S, L_CONTORNO, fill="#fff")
    D.centro(cx, cy, R)
    D.txt(cx + W - 2, oy + par * S / 2 + 1, "PAREDE", FONTE_P, anc="end",
          cor=C_TXT)
    D.txt(cx + R + 6, cy + R - 4, "cavidade", FONTE_P, anc="start", cor=C_REF)

    D.cota_v(oy, cy, cx - W - 12, vg(P.FIX_INSET), cx - W, tam=FONTE_P)
    D.cota_h(cx - R, cx + R, cy + R + 12, dm(col), cy + R, tam=FONTE_P)
    D.cota_h(cx - dfuro / 2 * S, cx + dfuro / 2 * S, oy - 10, dm(dfuro),
             cy - dfuro / 2 * S, tam=FONTE_P)
    D.cota_h(cx - W, cx - W + par * S, oy - 10, vg(par), oy, tam=FONTE_P)
    D.txt(cx, cy + R + 24,
          f"furo {dm(dfuro)} x {vg(prof)} nas DUAS pontas da coluna",
          FONTE_P, cor=C_TXT)
    D.txt(cx, cy + R + 28.5,
          "inserto de latão M3 &#216;ext 4,6 x 4,0", FONTE_P, cor=C_TXT)
    D.rotulo_vista(cx, cy + R + 40,
                   "DETALHE - coluna de inserto (6x)", "4:1")


# =====================================================================
# 3. Tampa de servico
# =====================================================================

def desenho_tampa():
    V, T = ler_3mf("caixa-tampa.3mf")
    cam = camadas(V, T)
    zs = niveis(V)
    esp = zs[-1]
    hreb = esp - zs[1]

    lo = cam[0][2][0]
    larg = max(p[0] for p in lo) - min(p[0] for p in lo)
    alt = max(p[1] for p in lo) - min(p[1] for p in lo)
    R = raio_canto(lo)
    passantes = cam[0][3]
    rebaixos = cam[-1][3]
    dp, dr = 2 * passantes[0][2], 2 * rebaixos[0][2]

    bate("tampa: espessura", esp, P.TAMPA_ESP)
    bate("tampa: largura", larg, P.CX_L)
    bate("tampa: profundidade", alt, P.CX_A)
    bate("tampa: raio de canto", R, P.CX_R)
    bate("tampa: rebaixo", hreb, P.REB_TAMPA)
    bate("tampa: Ø de passagem", dp, P.D_PASSAGEM)
    bate("tampa: Ø do rebaixo", dr, P.D_REBAIXO)
    bate("tampa: n de furos", len(rebaixos), 6)

    L = esp - hreb + P.PENETRACAO

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - TAMPA DE SERVIÇO",
                "Vista superior, corte e detalhe do furo de fixação",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-03")
    W = Vista(60, 60, larg, alt)

    contorno(D, lo, W)
    for f in rebaixos:
        furo(D, W, f)
    for f in passantes:
        furo(D, W, f, marca=False, lw=L_TRACO, cor="#555", dash=D_OCULTA)

    yb = W.py(0)
    xs = sorted({round(f[0], 3) for f in rebaixos})
    ys = sorted({round(f[1], 3) for f in rebaixos})
    D.cota_h(W.px(0), W.px(xs[0]), yb + 14, vg(xs[0]), yb)
    D.cota_h(W.px(0), W.px(xs[1]), yb + 26, vg(xs[1]), yb)
    D.cota_h(W.px(0), W.px(larg), yb + 38, vg(larg), yb)
    D.cota_v(W.py(alt), yb, W.px(0) - 14, vg(alt), W.px(0))
    D.cota_v(W.py(ys[0]), yb, W.px(larg) + 14, vg(ys[0]), W.px(larg))
    D.cota_v(W.py(ys[1]), yb, W.px(larg) + 28, vg(ys[1]), W.px(larg))

    D.bandeira(*W.p(xs[2], ys[2] + dr / 2), 1, ang=-45, comp=18)
    D.bandeira(W.px(larg - R * 0.293), W.py(alt - R * 0.293), 2, ang=-30,
               comp=18)
    D.rotulo_vista(W.px(larg / 2), yb + 50, "VISTA SUPERIOR", "1:1")

    yc = yb + 72
    D.hachura(W.px(0), yc, larg, esp * 4)
    for f in rebaixos:
        D.ret(W.px(f[0]) - dp / 2, yc, dp, esp * 4, L_CONTORNO, fill="#fff")
        D.ret(W.px(f[0]) - dr / 2, yc, dr, hreb * 4, L_CONTORNO, fill="#fff")
    D.cota_v(yc, yc + esp * 4, W.px(0) - 14, vg(esp), W.px(0))
    D.rotulo_vista(W.px(larg / 2), yc + esp * 4 + 10,
                   "CORTE - furos de fixação projetados", "vertical 4:1")

    _detalhe_furo(D, 470, 200, esp, hreb, dp, dr, L)

    y = D.notas(COL_DIR, 40, [
        (1, f"{len(rebaixos)}x {dm(dp)} passante com rebaixo {dm(dr)} x "
            f"{vg(hreb)} para a cabeça do parafuso M3 ISO 7380."),
        (2, f"Silhueta idêntica à do corpo e à do painel: {vg(larg)} x "
            f"{vg(alt)}, cantos R{vg(R)}."),
        (3, f"Espessura {vg(esp)}; sob a cabeça do parafuso restam "
            f"{vg(esp - hreb)} mm - é a seção mais fina da peça."),
        (4, f"Fixação com {len(rebaixos)}x M3 x {L:.0f} ISO 7380 em inserto de "
            f"latão M3 na base das colunas do corpo (ver PIBIC-CX-02)."),
        (5, "Peça de serviço: fica na face de BAIXO da caixa montada. O "
            "rebaixo abre para fora, então imprimir com ele para cima."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=250)

    tabela_furos(D, COL_DIR, y + 14, rotulos("FIX ", rebaixos),
                 "COORDENADAS DOS FUROS - origem no canto inferior esquerdo",
                 por_coluna=6)
    D.salvar("desenho-caixa-tampa.svg")


def _detalhe_furo(D, ox, oy, esp, hreb, dp, dr, L):
    S = 8.0
    rr, rp = dr / 2 * S, dp / 2 * S
    hr, ht = hreb * S, esp * S
    W = 50.0
    for sg in (-1, 1):
        D.hachura_poli([(ox + sg * W, oy), (ox + sg * rr, oy),
                        (ox + sg * rr, oy + hr), (ox + sg * rp, oy + hr),
                        (ox + sg * rp, oy + ht), (ox + sg * W, oy + ht)])
    dk, k = 5.7 * S / 2, 1.65 * S
    D.el.append(f'<path d="M {ox-dk:.2f} {oy+k:.2f} Q {ox:.2f} {oy-k:.2f} '
                f'{ox+dk:.2f} {oy+k:.2f} Z" fill="none" stroke="{C_REF}" '
                f'stroke-width="{L_TRACO}" stroke-dasharray="3,1.5"/>')
    for sg in (-1, 1):
        D.linha(ox + sg * 1.5 * S, oy + k, ox + sg * 1.5 * S, oy + ht + 8,
                L_TRACO, C_REF, dash=D_OCULTA)
    D.txt(ox + rr + 8, oy - 2, f"M3 x {L:.0f} ISO 7380 (ref.)", FONTE_P,
          anc="start", cor=C_REF)
    D.linha(ox + rr + 7, oy - 3, ox + dk * 0.6, oy + k * 0.45, L_FINA, C_REF)

    D.cota_h(ox - rr, ox + rr, oy - 9, dm(dr), oy, tam=FONTE_P)
    D.cota_h(ox - rp, ox + rp, oy + ht + 13, dm(dp), oy + ht, tam=FONTE_P)
    D.cota_v(oy, oy + hr, ox - W - 9, vg(hreb), ox - W, tam=FONTE_P)
    D.cota_v(oy + hr, oy + ht, ox - W - 9, vg(esp - hreb), ox - W, tam=FONTE_P)
    D.cota_v(oy, oy + ht, ox - W - 24, vg(esp), ox - W, tam=FONTE_P)
    D.bandeira(ox + rp + 2, oy + (hr + ht) / 2, 3, ang=0, comp=W - rp)
    D.rotulo_vista(ox, oy + ht + 26, "DETALHE - furo de fixação (6x)", "8:1")


# =====================================================================
# 4. Berco do interruptor - detalhe do corpo, em prancha propria
# =====================================================================

def desenho_berco():
    """
    O berco tem folha propria porque nao e so geometria: envolve um
    componente COMPRADO, uma sequencia de montagem (cola quente depois de
    testar) e um conjunto de cotas que ainda precisa ser confirmado com a
    peca na mao. Espremer isso na PIBIC-CX-02 seria perder as tres coisas.

    Continua saindo da mesma malha - a prancha nao sabe nada que o
    caixa-corpo.3mf nao diga.
    """
    V, T = ler_3mf("caixa-corpo.3mf")
    cam = camadas(V, T)
    zs = niveis(V)
    hh = zs[-1]
    ext = cam[1][2][0]
    larg = max(p[0] for p in ext) - min(p[0] for p in ext)
    alt = max(p[1] for p in ext) - min(p[1] for p in ext)
    Re = raio_canto(ext)
    ins = cam[0][3]
    fix = [(f[0], f[1]) for f in ins]
    col = 2 * max(raio_coluna(V, fx, fy, ins[0][2] + 0.5, P.FIX_INSET - 0.2)
                  for fx, fy in fix)

    sw = _interruptor(V, larg, alt, Re, fix, col)
    assert sw, "estacao do interruptor nao encontrada na malha do corpo"
    I = getattr(P, "INTERRUPTOR", {})
    fora = I.get("haste", 0.0) - sw["fundo"]

    D = Desenho(FOLHA_W, FOLHA_H, "CORPO - BERÇO DO INTERRUPTOR",
                f"Detalhe da parede y = {vg(alt)}, para o {sw['modelo']}",
                escala="ver ampliações", codigo="PIBIC-CX-04")

    _berco_elevacao(D, 66, 50, sw, hh, larg, Re, S=3.0)
    _berco_corte_h(D, 46, 218, sw, S=5.0)
    _berco_corte_v(D, 240, 200, sw, S=5.0)

    y = D.notas(COL_DIR, 44, [
        (1, f"BERÇO fresado na parede de trás, y = {vg(alt)}. Eixo da haste "
            f"a {vg(sw['x'])} da aresta esquerda e {vg(sw['z'])} da base do "
            f"corpo."),
        (2, f"RESSALTO {vg(sw['res_l'])} de largura, avançando "
            f"{vg(sw['saliencia'])} sobre a cavidade, do piso (z = 0) até "
            f"z = {vg(sw['z_topo'])}."),
        (None, "Ele desce até a base de propósito: um bloco solto teria a "
               "face de baixo em balanço. Assim imprime sem uma linha de "
               "suporte e ainda se apoia na tampa."),
        (3, f"BOLSA {vg(sw['bolsa_l'])} x {vg(sw['bolsa_h'])} x "
            f"{vg(sw['bolsa_p'])} de profundidade, ABERTA para a cavidade - "
            f"é por ela que o interruptor entra."),
        (None, f"Sobram {vg(sw['nervura'])} mm de plástico de cada lado e no "
               f"topo, e {vg(sw['fundo'])} mm no fundo. O teto da bolsa é o "
               f"único trecho sobre o vazio: ponte reta de "
               f"{vg(sw['bolsa_l'])} mm."),
        (4, f"RASGO DA HASTE {vg(sw['rasgo_l'])} x {vg(sw['rasgo_h'])}, único "
            f"furo do berço para fora. Com haste de {vg(I.get('haste', 0))} "
            f"sobre fundo de {vg(sw['fundo'])},"),
        (None, f"sobram {vg(fora)} mm de haste para fora. O comprimento "
               f"{vg(sw['rasgo_l'])} = haste {vg(I.get('haste_l', 0))} + "
               f"curso {vg(I.get('curso', 0))} + folga, para a chave "
               f"completar as duas posições."),
        (5, f"POSIÇÃO EM x. A parede só é plana entre x = {vg(sw['reto'][0])} "
            f"e x = {vg(sw['reto'][1])} (tangência dos raios R{vg(Re)}), e a "
            f"coluna central ocupa"),
        (None, f"x = {vg(89 - col/2)} a {vg(89 + col/2)}. O berço ocupa "
               f"{vg(sw['x'] - sw['res_l']/2)} a {vg(sw['x'] + sw['res_l']/2)}"
               f", com {vg(sw['x'] - sw['res_l']/2 - sw['reto'][0])} mm de "
               f"sobra dos dois lados. NÃO cabe em x = 56,00,"),
        (None, "no eixo do botão vermelho, que foi onde o pedido apontou: "
               "ali o ressalto invadiria 7,60 mm do raio de canto e o rasgo "
               "sairia oblíquo em relação à face."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=250)

    y = D.notas(COL_DIR, y + 4, [
        (None, "1. Imprima o corpo e teste o encaixe A SECO, sem cola. O "
               "interruptor entra pela cavidade, com a haste indo para o "
               "rasgo."),
        (None, "2. Confira as DUAS posições da haste antes de colar. Se "
               "raspar, lixe a bolsa - não force."),
        (None, "3. Solde os três fios ANTES de colar: depois da cola o "
               "acesso aos terminais fica ruim."),
        (None, "4. Cole com cola quente nas duas bocas da bolsa, sem invadir "
               "o corpo da chave. A folga de "
               f"{vg(I.get('cola', 0))} mm atrás do componente é para isso."),
        (None, "5. NÃO use parafuso. Os furos de fixação do próprio "
               "interruptor ficam contra o fundo da bolsa e não são usados."),
    ], titulo="MONTAGEM", larg=250)

    D.notas(COL_DIR, y + 4, [
        (None, "As cotas do componente são NOMINAIS. Os datasheets públicos "
               "da série SS12D00 são digitalização, sem texto extraível."),
        (None, "Confirmado só o elétrico: 1P2T, curso 2,00 mm, 0,3 A / "
               "30 V CC, três terminais a 2,54 mm."),
        (None, "A chave tem 2 POSIÇÕES e 3 TERMINAIS - o anúncio que a chama "
               "de \"3 posições\" está errado. Se o projeto precisar mesmo de "
               "três estados,"),
        (None, "o componente é outro e este berço muda."),
        (None, "Meça o componente e ajuste INTERRUPTOR em gerar_modelo_3mf.py; "
               "o modelo se recusa a gerar geometria inconsistente e esta "
               "prancha se refaz sozinha."),
    ], titulo="ATENÇÃO - COTAS A CONFIRMAR", larg=250)

    D.tabela(COL_DIR, 330,
             ["COTA", "VALOR", "DE ONDE VEM"],
             [["Corpo do interruptor",
               f"{vg(I.get('corpo_l',0))} x {vg(I.get('corpo_w',0))} x "
               f"{vg(I.get('corpo_h',0))}", "nominal do componente"],
              ["Haste sobre o corpo", vg(I.get("haste", 0)),
               "nominal - o \"4mm\" do nome"],
              ["Folga bolsa/corpo", vg(I.get("folga", 0)) + " por lado",
               "projeto"],
              ["Bolsa",
               f"{vg(sw['bolsa_l'])} x {vg(sw['bolsa_h'])} x {vg(sw['bolsa_p'])}",
               "medida em caixa-corpo.3mf"],
              ["Rasgo da haste", f"{vg(sw['rasgo_l'])} x {vg(sw['rasgo_h'])}",
               "medida em caixa-corpo.3mf"],
              ["Ressalto", f"{vg(sw['res_l'])} x {vg(sw['z_topo'])} x "
                           f"{vg(sw['prof'])}", "medida em caixa-corpo.3mf"],
              ["Haste para fora", vg(fora), "haste - fundo da bolsa"]],
             [78, 62, 110], titulo="RESUMO DAS COTAS DO BERÇO")

    D.salvar("desenho-caixa-berco.svg")


def _berco_elevacao(D, ox, oy, sw, hh, larg, Re, S=3.0):
    """A parede vista DE FORA. E o que a pessoa ve da caixa montada."""
    W = sw["res_l"] / 2 + 7.0     # meia largura do trecho mostrado

    def p(x, z):
        return (ox + (x + W) * S, oy + (sw["z_topo"] + 8.0 - z) * S)

    D.ret(*p(-W, sw["z_topo"] + 8.0), 2 * W * S, (sw["z_topo"] + 8.0) * S,
          L_FINA, fill="#fafafa", cor=C_REF)
    D.linha(*p(-W, 0.0), *p(W, 0.0), L_CONTORNO)
    D.txt(*p(-W + 1, -2.6), "base do corpo, z = 0 - assenta na tampa",
          FONTE_P, anc="start", cor=C_REF)

    # ocultos: ressalto e bolsa
    D.ret(*p(-sw["res_l"] / 2, sw["z_topo"]), sw["res_l"] * S,
          sw["z_topo"] * S, L_TRACO, cor="#555", dash=D_OCULTA)
    D.ret(*p(-sw["bolsa_l"] / 2, sw["z"] + sw["bolsa_h"] / 2),
          sw["bolsa_l"] * S, sw["bolsa_h"] * S, L_TRACO, cor="#555",
          dash=D_OCULTA)
    # visto: o rasgo
    D.ret(*p(-sw["rasgo_l"] / 2, sw["z"] + sw["rasgo_h"] / 2),
          sw["rasgo_l"] * S, sw["rasgo_h"] * S, L_CONTORNO, fill="#fff")

    D.linha(*p(-W + 2, sw["z"]), *p(W - 2, sw["z"]), L_FINA, C_ATEN,
            dash=D_CENTRO)
    D.linha(*p(0.0, sw["z_topo"] + 6.0), *p(0.0, -2.0), L_FINA, C_ATEN,
            dash=D_CENTRO)

    xd = p(W, 0)[0]
    D.cota_v(p(0, sw["z"])[1], p(0, 0.0)[1], xd + 12, vg(sw["z"]),
             p(0, 0)[0], tam=FONTE_P)
    D.cota_v(p(0, sw["z_topo"])[1], p(0, 0.0)[1], xd + 26, vg(sw["z_topo"]),
             p(0, 0)[0], tam=FONTE_P)
    D.cota_h(*[p(s * sw["rasgo_l"] / 2, 0)[0] for s in (-1, 1)],
             p(0, sw["z"] + sw["rasgo_h"] / 2)[1] - 8, vg(sw["rasgo_l"]),
             p(0, sw["z"] + sw["rasgo_h"] / 2)[1], tam=FONTE_P)
    D.cota_h(*[p(s * sw["res_l"] / 2, 0)[0] for s in (-1, 1)],
             p(0, sw["z_topo"])[1] - 16, vg(sw["res_l"]),
             p(0, sw["z_topo"])[1], tam=FONTE_P)
    D.cota_v(p(0, sw["z"] + sw["rasgo_h"] / 2)[1],
             p(0, sw["z"] - sw["rasgo_h"] / 2)[1],
             p(sw["rasgo_l"] / 2, 0)[0] + 8, vg(sw["rasgo_h"]),
             p(sw["rasgo_l"] / 2, 0)[0], tam=FONTE_P)
    D.bandeira(*p(sw["res_l"] / 2, sw["z_topo"]), 2, ang=-35, comp=20)
    D.bandeira(*p(sw["rasgo_l"] / 2, sw["z"] - sw["rasgo_h"] / 2), 4,
               ang=35, comp=26)
    D.rotulo_vista(p(0, 0)[0], p(0, 0)[1] + 22,
                   "VISTA DA PAREDE, DE FORA", f"{S:.0f}:1")


def _berco_corte_h(D, ox, oy, sw, S=5.0):
    """Corte no plano do eixo da haste: mostra a parede afinada e engrossada."""
    I = getattr(P, "INTERRUPTOR", {})
    mr, mb, ms = sw["res_l"] / 2, sw["bolsa_l"] / 2, sw["rasgo_l"] / 2
    lado_livre = 7.0
    fora = I.get("haste", 0.0) - sw["fundo"]

    def p(x, d):
        return (ox + (x + mr + lado_livre) * S, oy + d * S)

    for s in (-1, 1):
        D.hachura_poli([
            p(s * (mr + lado_livre), 0.0), p(s * ms, 0.0),
            p(s * ms, sw["fundo"]), p(s * mb, sw["fundo"]),
            p(s * mb, sw["prof"]), p(s * mr, sw["prof"]),
            p(s * mr, sw["par"]), p(s * (mr + lado_livre), sw["par"])])

    cl, ch = I.get("corpo_l", 0.0), I.get("corpo_h", 0.0)
    if cl and ch:
        D.ret(*p(-cl / 2, sw["fundo"]), cl * S, ch * S, L_TRACO, cor=C_REF,
              dash=D_FANTASMA)
        D.txt(*p(0.0, sw["fundo"] + ch / 2 + 0.5), sw["modelo"], FONTE_P,
              cor=C_REF)
    hl = I.get("haste_l", 0.0)
    if hl:
        D.ret(*p(-hl / 2, -fora), hl * S, I.get("haste", 0.0) * S, L_TRACO,
              cor=C_REF, dash=D_FANTASMA)
        cu = I.get("curso", 0.0)
        D.linha(*p(-hl / 2 - cu / 2, -fora - 1.6),
                *p(hl / 2 + cu / 2, -fora - 1.6), L_FINA, C_ATEN,
                dash=D_OCULTA)
        D.txt(*p(0.0, -fora - 2.6), f"curso {vg(cu)}", FONTE_P, cor=C_ATEN)

    for s in (-1, 1):
        D.poli([p(s * mb, sw["prof"]), p(s * (mb - 1.8), sw["prof"]),
                p(s * mb, sw["prof"] - 1.8)], L_FINA, fill="#dcdcdc",
               cor="#888", fechar=True)
    D.txt(*p(0.0, sw["prof"] + 4.0), "cola quente nas duas bocas (2x)",
          FONTE_P, cor=C_TXT)

    D.linha(*p(-(mr + lado_livre), 0.0), *p(mr + lado_livre, 0.0), L_FINA,
            C_REF, dash=D_CENTRO)
    D.txt(*p(-(mr + lado_livre), -1.8), "FACE EXTERNA", FONTE_P, anc="start",
          cor=C_REF)
    D.txt(*p(mr + lado_livre, sw["par"] + 3.2), "cavidade", FONTE_P,
          anc="end", cor=C_REF)

    yb = p(0, sw["prof"])[1]
    D.cota_h(p(-ms, 0)[0], p(ms, 0)[0], p(0, 0)[1] - 14, vg(sw["rasgo_l"]),
             p(0, 0)[1], tam=FONTE_P)
    D.cota_h(p(-mb, 0)[0], p(mb, 0)[0], yb + 14, vg(sw["bolsa_l"]), yb,
             tam=FONTE_P)
    D.cota_h(p(-mr, 0)[0], p(mr, 0)[0], yb + 26, vg(sw["res_l"]), yb,
             tam=FONTE_P)
    xd = p(mr + lado_livre, 0)[0]
    D.cota_v(p(0, -fora)[1], p(0, 0.0)[1], xd + 11, vg(fora), xd, tam=FONTE_P)
    D.cota_v(p(0, 0.0)[1], p(0, sw["fundo"])[1], xd + 11, vg(sw["fundo"]), xd,
             tam=FONTE_P)
    D.cota_v(p(0, sw["fundo"])[1], yb, xd + 23, vg(sw["bolsa_p"]), xd,
             tam=FONTE_P)
    D.cota_v(p(0, 0.0)[1], p(0, sw["par"])[1], xd + 35, vg(sw["par"]), xd,
             tam=FONTE_P)
    D.bandeira(*p(-mb, sw["fundo"]), 3, ang=-140, comp=22)
    D.rotulo_vista(p(0, 0)[0], yb + 38,
                   "CORTE A-A - plano do eixo da haste", f"{S:.0f}:1")


def _berco_corte_v(D, ox, oy, sw, S=5.0):
    """
    Corte vertical no eixo da haste. E a vista que responde a pergunta de
    impressao: mostra que o ressalto desce ate a base - nada em balanco - e
    que o unico trecho sobre o vazio e o teto da bolsa.

    z para cima, profundidade para a direita: a face externa e a aresta
    esquerda, como na caixa em pe sobre a mesa.
    """
    I = getattr(P, "INTERRUPTOR", {})
    hb, hs = sw["bolsa_h"] / 2, sw["rasgo_h"] / 2
    z0, z1 = sw["z"] - hb, sw["z"] + hb
    topo, base, z_ref = sw["z_topo"], 0.0, sw["z_topo"] + 5.0
    fora = I.get("haste", 0.0) - sw["fundo"]

    def p(z, d):
        return (ox + d * S, oy + (z_ref - z) * S)

    # bloco de cima: parede lisa, ressalto, teto da bolsa e teto do rasgo
    D.hachura_poli([
        p(z_ref, 0.0), p(z_ref, sw["par"]), p(topo, sw["par"]),
        p(topo, sw["prof"]), p(z1, sw["prof"]), p(z1, sw["fundo"]),
        p(sw["z"] + hs, sw["fundo"]), p(sw["z"] + hs, 0.0)])
    # bloco de baixo: do piso ate a soleira do rasgo
    D.hachura_poli([
        p(base, 0.0), p(base, sw["prof"]), p(z0, sw["prof"]),
        p(z0, sw["fundo"]), p(sw["z"] - hs, sw["fundo"]),
        p(sw["z"] - hs, 0.0)])

    cw, ch = I.get("corpo_w", 0.0), I.get("corpo_h", 0.0)
    if cw and ch:
        D.ret(*p(sw["z"] + cw / 2, sw["fundo"]), ch * S, cw * S, L_TRACO,
              cor=C_REF, dash=D_FANTASMA)
    hw = I.get("haste_w", 0.0)
    if hw and I.get("haste"):
        D.ret(*p(sw["z"] + hw / 2, -fora), I["haste"] * S, hw * S, L_TRACO,
              cor=C_REF, dash=D_FANTASMA)

    D.linha(*p(z_ref, 0.0), *p(base, 0.0), L_FINA, C_REF, dash=D_CENTRO)
    D.txt(*p(z_ref + 1.4, 0.0), "FACE EXTERNA", FONTE_P, anc="middle",
          cor=C_REF)
    D.linha(*p(base, 0.0), *p(base, sw["prof"] + 4.0), L_FINA, C_REF)
    D.txt(*p(base - 1.6, sw["prof"] + 4.0), "base z = 0 - assenta na tampa",
          FONTE_P, anc="end", cor=C_REF)
    D.linha(*p(sw["z"], -fora - 1.0), *p(sw["z"], sw["prof"] + 2.0), L_FINA,
            C_ATEN, dash=D_CENTRO)

    # a ponte - unico trecho impresso sobre o vazio
    D.linha(*p(z1, sw["fundo"]), *p(z1, sw["prof"]), 0.7, C_ATEN)
    D.txt(*p(z1 + 1.0, sw["prof"] + 1.0),
          f"teto da bolsa: ponte reta de {vg(sw['bolsa_l'])} (ver A-A)",
          FONTE_P, anc="start", cor=C_ATEN)

    xd = p(0, sw["prof"])[0]
    D.cota_v(p(z1, 0)[1], p(z0, 0)[1], xd + 30, vg(sw["bolsa_h"]),
             p(z1, sw["prof"])[0], tam=FONTE_P)
    D.cota_v(p(sw["z"] + hs, 0)[1], p(sw["z"] - hs, 0)[1], xd + 18,
             vg(sw["rasgo_h"]), p(0, 0)[0], tam=FONTE_P)
    D.cota_v(p(topo, 0)[1], p(base, 0)[1], xd + 44, vg(topo), xd, tam=FONTE_P)
    D.cota_v(p(sw["z"], 0)[1], p(base, 0)[1], xd + 56, vg(sw["z"]), xd,
             tam=FONTE_P)
    D.cota_h(p(0, 0.0)[0], p(0, sw["fundo"])[0], p(base, 0)[1] + 12,
             vg(sw["fundo"]), p(base, 0)[1], tam=FONTE_P)
    D.cota_h(p(0, 0.0)[0], p(0, sw["prof"])[0], p(base, 0)[1] + 24,
             vg(sw["prof"]), p(base, 0)[1], tam=FONTE_P)
    D.bandeira(*p(topo, sw["prof"]), 2, ang=-40, comp=24)
    D.rotulo_vista(p(base, sw["prof"] / 2)[0], p(base, 0)[1] + 36,
                   "CORTE B-B - vertical, no eixo da haste", f"{S:.0f}:1")


if __name__ == "__main__":
    desenho_painel()
    desenho_corpo()
    desenho_tampa()
    desenho_berco()
    encerrar_conferencia()
    print("conferidos contra gerar_modelo_3mf.py: nenhuma divergencia")
