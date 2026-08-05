#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desenhos tecnicos das pecas da caixa - PIBIC UniCEUB.
Autor: Rafael Alves de Sousa Costa.

Le a geometria DIRETO dos .3mf do repositorio, entao o desenho nao pode
divergir do modelo: toda cota sai de uma medicao na malha, nenhuma e
digitada a mao.

  Projeto PIBIC-caixa.3mf   -> desenho-caixa-painel.svg  (z 0..10)
                            -> desenho-caixa-corpo.svg   (z 10..65)
  tampa.3mf                 -> desenho-caixa-tampa.svg

Pranchas em A2 paisagem (594 x 420 mm), projecao no 1o diedro: a vista
superior fica ABAIXO da vista frontal e, nela, a face frontal da peca e a
aresta de baixo.

Nao confundir com desenho-tampa.svg, que e da tampa parametrica de
gerar_stl.py (209,30 x 108,50). Estes aqui sao das pecas do Fusion.

Uso:  python gerar_desenhos_3mf.py
"""

import math
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict

from gerar_desenhos import (Desenho, L_CONTORNO, L_FINA, L_TRACO,
                            D_OCULTA, D_CENTRO, D_FANTASMA,
                            FONTE, FONTE_P, C_COTA, C_REF, C_TXT, C_ATEN)

NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"

# O Fusion exportou com a peca longe da origem; isto traz o canto para (0,0).
DX, DY = 470.0, -90.0

# Prancha A2 paisagem: coluna das vistas a esquerda, notas e detalhes a direita.
FOLHA_W, FOLHA_H = 594.0, 420.0
COL_DIR = 330.0


# =====================================================================
# Interruptor lateral - COMPONENTE AINDA NAO DEFINIDO
# =====================================================================
# Enquanto o modelo nao for escolhido, o desenho reserva uma AREA na parede
# frontal do corpo (linha traco-ponto-ponto) em vez de desenhar um recorte
# que ainda nao existe. Definido o componente, basta preencher 'rasgo_l' e
# 'rasgo_h' (recorte retangular) ou 'furo_d' (recorte redondo): o desenho
# passa a mostrar o recorte real, cotado, sem nenhuma outra edicao.
INTERRUPTOR = {
    "modelo":  None,    # ex.: "KCD1-101", "MTS-101", "PBS-26B"
    "rasgo_l": None,    # recorte retangular - comprimento (mm)
    "rasgo_h": None,    # recorte retangular - altura (mm)
    "furo_d":  None,    # recorte redondo - diametro (mm)
    "esp_max": None,    # espessura maxima de painel aceita pelo componente
    "env_l":   30.0,    # area reservada enquanto o componente e indefinido
    "env_h":   25.0,
    "x":       None,    # centro ao longo da face (None = meio do comprimento)
    "z":       None,    # centro na altura do corpo (None = meia altura)
}


# =====================================================================
# Leitura do 3MF e seccionamento
# =====================================================================

def ler_3mf(caminho):
    root = ET.fromstring(zipfile.ZipFile(caminho).read("3D/3dmodel.model"))
    objs = {}
    for o in root.find(NS + "resources").findall(NS + "object"):
        malha = o.find(NS + "mesh")
        if malha is None:
            continue
        V = [(float(v.get("x")) + DX, float(v.get("y")) + DY, float(v.get("z")))
             for v in malha.find(NS + "vertices")]
        T = [(int(t.get("v1")), int(t.get("v2")), int(t.get("v3")))
             for t in malha.find(NS + "triangles")]
        objs[o.get("id")] = (V, T)
    return objs


def secao(V, T, z):
    """Segmentos da interseccao da malha com o plano z."""
    segs = []
    for tri in T:
        P = [V[i] for i in tri]
        pts = []
        for i in range(3):
            a, b = P[i], P[(i + 1) % 3]
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
    """Encadeia os segmentos em contornos fechados ordenados."""
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
    """Devolve (contornos_abertos_ordenados, furos) no plano z."""
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
    tang = [p[1] for p in loop if abs(p[0] - x0) < 1e-6]
    return min(tang) - y0 if tang else None


def parede_min_max(ext, inte):
    """
    Espessura minima e maxima da parede entre dois contornos fechados.
    Para cada vertice do contorno interno, distancia ate o segmento mais
    proximo do externo. Nao assume que um seja offset uniforme do outro.
    """
    seg = [(ext[i], ext[(i + 1) % len(ext)]) for i in range(len(ext))]
    dists = []
    for p in inte:
        melhor = 1e9
        for a, b in seg:
            dx, dy = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx +
                                                       (p[1] - a[1]) * dy) / L2))
            melhor = min(melhor, math.hypot(p[0] - (a[0] + t * dx),
                                            p[1] - (a[1] + t * dy)))
        dists.append(melhor)
    return min(dists), max(dists)


# =====================================================================
# Auxiliares de desenho
# =====================================================================

def vg(s):
    return f"{s:.2f}".replace(".", ",")


class Vista:
    """
    Converte coordenadas da PECA em coordenadas da prancha.

    Na peca a origem e o canto inferior esquerdo e y cresce para cima; no SVG
    y cresce para baixo. Sem esta inversao a vista sai espelhada em relacao a
    tabela de coordenadas e a face que aparece embaixo na vista superior nao e
    a que aparece na vista frontal.
    """

    def __init__(self, ox, oy, larg, alt):
        self.ox, self.oy, self.larg, self.alt = ox, oy, larg, alt

    def px(self, x):
        return self.ox + x

    def py(self, y):
        return self.oy + self.alt - y

    def p(self, x, y):
        return (self.px(x), self.py(y))


def contorno(D, loop, V, lw=L_CONTORNO, cor="#111"):
    D.poli([V.p(x, y) for x, y in loop], lw, cor=cor, fechar=True)


def furo(D, V, f, marca=True, lw=L_CONTORNO, cor="#111", dash=None):
    cx, cy, r = f
    x, y = V.p(cx, cy)
    D.circ(x, y, r, lw, cor=cor, dash=dash)
    if marca:
        D.centro(x, y, r)


def tabela_furos(D, x, y, furos, titulo, rot="FURO"):
    """Tabela de coordenadas dos furos, na ordem em que aparecem na peca."""
    linhas = [(f"{rot} {i}", vg(f[0]), vg(f[1]), f"&#216;{vg(2 * f[2])}")
              for i, f in enumerate(sorted(furos, key=lambda f: (f[1], f[0])), 1)]
    return D.tabela(x, y, ("FURO", "X [mm]", "Y [mm]", "&#216;"), linhas,
                    (22, 24, 24, 22), titulo=titulo)


# =====================================================================
# 1. Painel dos botoes  (Body1, z 0..10)
# =====================================================================

def desenho_painel(objs):
    V, T = objs["1"]
    conts, furos = analisar(V, T, 5.0)
    esp = max(p[2] for p in V) - min(p[2] for p in V)
    lo = conts[0]
    larg = max(p[0] for p in lo) - min(p[0] for p in lo)
    alt = max(p[1] for p in lo) - min(p[1] for p in lo)
    R = raio_canto(lo)

    grandes = sorted([f for f in furos if f[2] > 8], key=lambda f: f[0])
    pequenos = [f for f in furos if f[2] <= 8]
    bv, bg = grandes                      # vermelho (capa 98,5) e verde (60,8)

    # circunferencias de furacao de cada botao
    def furacao(b):
        rs = [math.hypot(p[0] - b[0], p[1] - b[1]) for p in pequenos]
        return min(r for r in rs if r < 60)

    rf_v, rf_g = furacao(bv), furacao(bg)
    n_v = sum(1 for p in pequenos
              if abs(math.hypot(p[0] - bv[0], p[1] - bv[1]) - rf_v) < 0.5)
    n_g = len(pequenos) - n_v
    folga = (bg[0] - bv[0]) - 98.5 / 2 - 60.8 / 2

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - PAINEL DOS BOTÕES",
                "Vista superior e corte pelos eixos dos furos",
                escala="1:1 (corte 3:1 na vertical)", codigo="PIBIC-CX-01")
    W = Vista(60, 70, larg, alt)

    contorno(D, lo, W)
    for f in grandes + pequenos:
        furo(D, W, f)

    # capas dos botoes e circunferencias de furacao: referencia, sem texto
    # sobre o desenho - o que elas sao esta nas notas 3 e 4
    for b, cap in ((bv, 98.5), (bg, 60.8)):
        D.circ(*W.p(*b[:2]), cap / 2, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    for b, rf in ((bv, rf_v), (bg, rf_g)):
        D.circ(*W.p(*b[:2]), rf, L_TRACO, cor=C_ATEN, dash=D_CENTRO)

    # --- cotas: todas abaixo ou a esquerda da vista, nunca sobre ela ---
    yb = W.py(0)
    D.cota_h(W.px(0), W.px(bv[0]), yb + 14, vg(bv[0]), yb)
    D.cota_h(W.px(bv[0]), W.px(bg[0]), yb + 14, f"{vg(bg[0]-bv[0])} entre centros",
             W.py(bv[1]))
    D.cota_h(W.px(0), W.px(bg[0]), yb + 26, vg(bg[0]), yb)
    D.cota_h(W.px(0), W.px(larg), yb + 38, vg(larg), yb)
    D.cota_v(W.py(bv[1]), yb, W.px(0) - 14, vg(bv[1]), W.px(0))
    D.cota_v(W.py(alt), yb, W.px(0) - 28, vg(alt), W.px(0))
    D.cota_h(W.px(bv[0]) - rf_v, W.px(bv[0]) + rf_v, W.py(alt) - 14,
             f"&#216;{vg(2*rf_v)}", W.py(bv[1] + rf_v), tam=FONTE_P)
    D.cota_h(W.px(bg[0]) - rf_g, W.px(bg[0]) + rf_g, W.py(alt) - 26,
             f"&#216;{vg(2*rf_g)}", W.py(bg[1] + rf_g), tam=FONTE_P)

    # --- chamadas numeradas (o texto correspondente esta no bloco de notas) ---
    D.bandeira(*W.p(bv[0], bv[1] + bv[2]), 1, ang=-115, comp=22)
    D.bandeira(*W.p(pequenos[0][0], pequenos[0][1] - pequenos[0][2]), 2,
               ang=118, comp=20)
    D.bandeira(*W.p(bg[0] + 60.8 / 2, bg[1]), 3, ang=-20, comp=20)
    D.bandeira(*W.p(bg[0], bg[1] - rf_g), 4, ang=60, comp=22)
    D.bandeira(W.px(larg - R * 0.293), W.py(alt - R * 0.293), 5, ang=-45, comp=18)

    D.rotulo_vista(W.px(larg / 2), yb + 50, "VISTA SUPERIOR", "1:1")

    # --- corte com todos os furos projetados ---
    yc = yb + 72
    D.hachura(W.px(0), yc, larg, esp * 3)
    for f in grandes + pequenos:
        D.ret(W.px(f[0]) - f[2], yc, 2 * f[2], esp * 3, L_CONTORNO, fill="#fff")
    D.cota_v(yc, yc + esp * 3, W.px(0) - 14, vg(esp), W.px(0))
    D.rotulo_vista(W.px(larg / 2), yc + esp * 3 + 10,
                   "CORTE - todos os furos projetados", "vertical 3:1")

    # --- notas e tabela ---
    y = D.notas(COL_DIR, 42, [
        (1, f"2x &#216;{vg(2*bv[2])} - passagem do barril M24 do botão "
            f"(especificação Adafruit)."),
        (2, f"{len(pequenos)}x &#216;{vg(2*pequenos[0][2])} passantes: "
            f"{n_v} a 60&#176; sobre &#216;{vg(2*rf_v)} (botão vermelho) e "
            f"{n_g} a 120&#176; sobre &#216;{vg(2*rf_g)} (botão verde)."),
        (3, "&#216;98,50 e &#216;60,80 - capas dos botões, apenas referência "
            "de montagem; não fazem parte da peça."),
        (4, "Circunferências de furação em linha de centro; coordenadas de "
            "cada furo na tabela ao lado."),
        (5, f"Contorno externo {vg(larg)} x {vg(alt)}, cantos R{vg(R)} nos "
            f"quatro cantos."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=200)

    y = D.notas(COL_DIR, y + 6, [
        (None, f"Espessura do painel {vg(esp)} mm - dentro do máximo de "
               f"12,70 mm admitido pelo botão, com 2,70 mm de folga."),
        (None, f"Folga livre entre as capas = {vg(bg[0]-bv[0])} &#8722; 98,50/2 "
               f"&#8722; 60,80/2 = {vg(folga)} mm."),
        (None, f"Os {len(pequenos)} furos &#216;{vg(2*pequenos[0][2])} caem sob "
               f"as capas, fora do flange do corpo: posição compatível com LED "
               f"&#216;10 iluminando a capa por baixo."),
        (None, "A função desses furos não é determinável pela geometria - "
               "confirmar antes de imprimir."),
    ], titulo="OBSERVAÇÕES DE PROJETO", larg=200)

    tabela_furos(D, COL_DIR, y + 14, grandes + pequenos,
                 "COORDENADAS DOS FUROS - origem no canto inferior esquerdo")
    D.salvar("desenho-caixa-painel.svg")


# =====================================================================
# 2. Corpo da caixa  (Body2, z 10..65)
# =====================================================================

def desenho_corpo(objs):
    V, T = objs["3"]
    z0 = min(p[2] for p in V)
    z1 = max(p[2] for p in V)
    hh = z1 - z0
    conts, _ = analisar(V, T, (z0 + z1) / 2)
    ext, inte = conts[0], conts[1]
    larg = max(p[0] for p in ext) - min(p[0] for p in ext)
    alt = max(p[1] for p in ext) - min(p[1] for p in ext)
    larg_i = max(p[0] for p in inte) - min(p[0] for p in inte)
    alt_i = max(p[1] for p in inte) - min(p[1] for p in inte)
    Re = raio_canto(ext)
    Ri = raio_canto(inte)
    par = min(p[0] for p in inte) - min(p[0] for p in ext)
    pmin, pmax = parede_min_max(ext, inte)

    _, ins = analisar(V, T, z1 - 2.0)          # furos de inserto
    zi = min(p[2] for p in V if abs(p[2] - z0) > 1e-6 and abs(p[2] - z1) > 1e-6)
    prof = z1 - zi
    dins = 2 * ins[0][2]
    esp_tampa = 4.0

    sw = _interruptor(larg, hh, Re)

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - CORPO",
                "Vista frontal, vista superior, corte da parede e detalhe",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-02")

    # ---------------- vista frontal (elevacao) ----------------
    OX, y_top = 60.0, 42.0
    _vista_frontal(D, OX, y_top, larg, hh, par, z0, esp_tampa, Re,
                   sorted({round(f[0], 3) for f in ins}), dins, prof, sw)

    # ---------------- vista superior ----------------
    W = Vista(OX, 186, larg, alt)
    contorno(D, ext, W)
    contorno(D, inte, W)
    for f in ins:
        furo(D, W, f)

    # pegada do interruptor na parede frontal (aresta de baixo, 1o diedro)
    D.ret(W.px(sw["x"] - sw["l"] / 2), W.py(par), sw["l"], par,
          L_TRACO, cor=C_ATEN, dash=None if sw["definido"] else D_FANTASMA)

    yb = W.py(0)
    xs = sorted({round(f[0], 3) for f in ins})
    ys = sorted({round(f[1], 3) for f in ins})
    D.cota_h(W.px(0), W.px(xs[0]), W.py(alt) - 14, vg(xs[0]), W.py(alt))
    D.cota_h(W.px(0), W.px(xs[1]), W.py(alt) - 26, vg(xs[1]), W.py(alt))
    D.cota_h(W.px(0), W.px(larg_i) + par, yb + 26, vg(larg_i), yb)
    D.cota_h(W.px(0), W.px(larg), yb + 38, vg(larg), yb)
    D.cota_v(W.py(alt), yb, W.px(0) - 28, vg(alt), W.px(0))
    D.cota_v(W.py(alt - par), W.py(par), W.px(0) - 14, vg(alt_i), W.px(0))
    D.cota_v(W.py(ys[0]), yb, W.px(larg) + 14, vg(ys[0]), W.px(larg))
    D.cota_v(W.py(ys[1]), yb, W.px(larg) + 28, vg(ys[1]), W.px(larg))

    D.bandeira(*W.p(xs[2], ys[2] + ins[0][2]), 1, ang=-45, comp=18)
    D.bandeira(W.px(larg - Re * 0.293), W.py(alt - Re * 0.293), 2,
               ang=-30, comp=18)
    D.bandeira(W.px(par + Ri * 0.293), W.py(par + Ri * 0.293), 3,
               ang=135, comp=20)

    D.rotulo_vista(W.px(larg / 2), yb + 50, "VISTA SUPERIOR", "1:1")

    # ---------------- corte da parede + detalhe (coluna direita) -------------
    xw = COL_DIR + 15
    D.hachura(xw, 46, par, hh)
    D.ret(xw + par / 2 - dins / 2, 46, dins, prof, L_TRACO, fill="#fff",
          cor=C_ATEN)
    D.cota_v(46, 46 + hh, xw - 12, vg(hh), xw)
    D.cota_h(xw, xw + par, 40, vg(par), 46, tam=FONTE_P)
    D.rotulo_vista(xw + par / 2, 46 + hh + 10, "CORTE DA PAREDE", "1:1")

    _detalhe_inserto(D, 470, 62, par, prof, dins, esp_tampa)

    # ---------------- notas, observacoes e tabela ----------------
    y = D.notas(COL_DIR, 150, [
        (1, f"6x &#216;{vg(dins)} x {vg(prof)} - furo para inserto roscado de "
            f"latão M3, aplicado a quente. Coordenadas na tabela abaixo."),
        (2, f"Contorno externo {vg(larg)} x {vg(alt)}, cantos R{vg(Re)}."),
        (3, f"Contorno interno {vg(larg_i)} x {vg(alt_i)}, cantos R{vg(Ri)}. "
            f"A parede não é offset uniforme do contorno externo: varia de "
            f"{vg(pmin)} a {vg(pmax)} mm"),
        (None, "ao longo do perímetro e vale 10,00 mm nas seis posições de "
               "fixação, que é onde a espessura importa."),
        (4, f"Fixação da tampa: 6x M3 x 6 ISO 7380. Um M3 x 10 encosta no "
            f"fundo do furo antes de a cabeça assentar (ver detalhe)."),
    ] + _notas_interruptor(sw, larg, Re), titulo="NOTAS DE FABRICAÇÃO", larg=240)

    y = D.notas(COL_DIR, y + 6, [
        (None, f"Altura da caixa montada = {vg(z0)} (painel) + {vg(hh)} "
               f"(corpo) + {vg(esp_tampa)} (tampa) = {vg(z1 + esp_tampa)} mm."),
    ], titulo="OBSERVAÇÕES DE PROJETO", larg=240)

    tabela_furos(D, COL_DIR, y + 14, ins,
                 "COORDENADAS DOS FUROS DE INSERTO - origem no canto inferior "
                 "esquerdo")
    D.salvar("desenho-caixa-corpo.svg")


def _interruptor(larg, hh, Re):
    """Posicao e tamanho do recorte do interruptor (ou da area reservada)."""
    s = dict(INTERRUPTOR)
    definido = bool(s["furo_d"]) or bool(s["rasgo_l"] and s["rasgo_h"])
    s["definido"] = definido
    s["x"] = larg / 2 if s["x"] is None else s["x"]
    s["z"] = hh / 2 if s["z"] is None else s["z"]
    if s["furo_d"]:
        s["l"] = s["h"] = s["furo_d"]
    elif definido:
        s["l"], s["h"] = s["rasgo_l"], s["rasgo_h"]
    else:
        s["l"], s["h"] = s["env_l"], s["env_h"]
    s["reto"] = (Re, larg - Re)       # trecho plano da face frontal
    return s


def _notas_interruptor(sw, larg, Re):
    if sw["definido"]:
        forma = (f"&#216;{vg(sw['furo_d'])}" if sw["furo_d"]
                 else f"{vg(sw['l'])} x {vg(sw['h'])}")
        return [
            (5, f"Recorte do interruptor {sw['modelo']}: {forma}, centro a "
                f"{vg(sw['x'])} da aresta esquerda e {vg(sw['z'])} da base "
                f"do corpo."),
            (6, "A parede tem 10,00 mm; prever rebaixo local na face interna "
                f"se o componente admitir painel de no máximo "
                f"{vg(sw['esp_max'])} mm."),
        ]
    return [
        (5, f"ÁREA RESERVADA PARA O INTERRUPTOR LATERAL - componente ainda não "
            f"definido. O retângulo {vg(sw['l'])} x {vg(sw['h'])} em linha "
            f"traço-ponto-ponto é"),
        (None, "reserva de espaço, NÃO é recorte. Antes de imprimir, definir: "
               "modelo, formato do recorte (retangular L x H ou &#216;), "
               "espessura máxima de painel"),
        (None, "admitida pelo componente e corrente/tensão de trabalho."),
        (6, "A parede tem 10,00 mm de espessura e a maioria dos interruptores "
            "de encaixe aceita painel de 2 a 5 mm: prever rebaixo local na "
            "face interna,"),
        (None, "na região do recorte, reduzindo a espessura ao valor admitido "
               "pelo componente escolhido."),
        (7, f"A face frontal só é plana entre x = {vg(sw['reto'][0])} e "
            f"x = {vg(sw['reto'][1])} (tangência dos raios R{vg(Re)}); o "
            f"recorte deve ficar contido nesse trecho."),
    ]


def _vista_frontal(D, ox, y_top, larg, hh, par, esp_pain, esp_tampa, Re,
                   xs, dins, prof, sw):
    """
    Elevacao do corpo, com painel e tampa em linha de referencia para dar a
    altura da caixa montada, e o recorte (ou a reserva) do interruptor.
    """
    y_t0 = y_top                       # topo da tampa
    y_c0 = y_t0 + esp_tampa            # topo do corpo
    y_c1 = y_c0 + hh                   # base do corpo
    y_p1 = y_c1 + esp_pain             # base do painel

    D.ret(ox, y_t0, larg, esp_tampa, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + larg + 4, y_t0 + 3, "TAMPA (ref.)", FONTE_P, anc="start",
          cor=C_REF)
    D.ret(ox, y_c1, larg, esp_pain, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + larg + 4, y_p1 - 3, "PAINEL (ref.)", FONTE_P, anc="start",
          cor=C_REF)
    D.ret(ox, y_c0, larg, hh, L_CONTORNO)

    # arestas invisiveis: faces internas da cavidade e furos de inserto
    for x in (ox + par, ox + larg - par):
        D.linha(x, y_c0, x, y_c1, L_TRACO, "#555", dash=D_OCULTA)
    for x in xs:
        D.ret(ox + x - dins / 2, y_c0, dins, prof, L_TRACO, "none", "#555",
              dash=D_OCULTA)

    # limites do trecho plano da face
    for x in sw["reto"]:
        D.linha(ox + x, y_t0 - 6, ox + x, y_p1 + 6, L_TRACO, C_ATEN,
                dash=D_CENTRO)

    # recorte do interruptor, ou area reservada enquanto ele nao existe
    xs_c, ys_c = ox + sw["x"], y_c1 - sw["z"]
    if sw["definido"] and sw["furo_d"]:
        D.circ(xs_c, ys_c, sw["furo_d"] / 2, L_CONTORNO)
        D.centro(xs_c, ys_c, sw["furo_d"] / 2)
    else:
        D.ret(xs_c - sw["l"] / 2, ys_c - sw["h"] / 2, sw["l"], sw["h"],
              L_CONTORNO if sw["definido"] else L_TRACO,
              cor="#111" if sw["definido"] else C_ATEN,
              dash=None if sw["definido"] else D_FANTASMA)
        D.centro(xs_c, ys_c, min(sw["l"], sw["h"]) / 2)

    D.bandeira(xs_c - sw["l"] / 2, ys_c - sw["h"] / 2, 5, ang=-125, comp=18)

    D.cota_v(y_c0, y_c1, ox - 14, vg(hh), ox)
    D.cota_v(y_t0, y_p1, ox - 28, vg(hh + esp_pain + esp_tampa), ox)
    D.cota_h(ox, xs_c, y_p1 + 14, vg(sw["x"]), y_p1)
    D.cota_h(xs_c - sw["l"] / 2, xs_c + sw["l"] / 2, y_p1 + 26, vg(sw["l"]),
             ys_c + sw["h"] / 2, tam=FONTE_P)
    D.cota_v(ys_c, y_c1, ox + larg + 14, vg(sw["z"]), ox + larg)
    D.cota_v(ys_c - sw["h"] / 2, ys_c + sw["h"] / 2, ox + larg + 28,
             vg(sw["h"]), ox + larg, tam=FONTE_P)

    D.rotulo_vista(ox + larg / 2, y_p1 + 40, "VISTA FRONTAL", "1:1")


def _detalhe_inserto(D, ox, oy, par, prof, dfuro, esp_t):
    """
    Detalhe 4:1 do topo da parede com a tampa e o parafuso, conferindo o
    M3 x 6 contra a profundidade de furo realmente modelada.
    """
    S = 4.0
    reb = 2.0
    L = 6.0                        # M3 x 6: decisao do projeto
    H = 12.0                       # trecho de parede mostrado
    w = par * S / 2
    D.hachura(ox - w, oy, par * S, H * S)                             # parede
    D.ret(ox - dfuro * S / 2, oy, dfuro * S, prof * S, L_CONTORNO, fill="#fff")
    D.hachura(ox - w - 10, oy - esp_t * S, par * S + 20, esp_t * S)   # tampa
    D.ret(ox - 6.5 * S / 2, oy - esp_t * S, 6.5 * S, reb * S,
          L_CONTORNO, fill="#fff")
    D.ret(ox - dfuro * S / 2, oy - (esp_t - reb) * S, dfuro * S,
          (esp_t - reb) * S, L_CONTORNO, fill="#fff")

    # parafuso, a partir do fundo do rebaixo
    z_cab = oy - (esp_t - reb) * S
    z_pta = z_cab + L * S
    D.ret(ox - 3.0 * S / 2, z_cab, 3.0 * S, L * S, L_TRACO, cor=C_REF)
    D.el.append(f'<path d="M {ox-5.7*S/2:.2f} {z_cab:.2f} Q {ox:.2f} '
                f'{z_cab-2*1.65*S:.2f} {ox+5.7*S/2:.2f} {z_cab:.2f} Z" '
                f'fill="none" stroke="{C_REF}" stroke-width="{L_TRACO}"/>')
    D.txt(ox + 6.5 * S / 2 + 4, z_cab - 4, "M3 x 6 ISO 7380 (ref.)", FONTE_P,
          anc="start", cor=C_REF)

    # folga entre a ponta do parafuso e o fundo do furo
    sobra = prof - (L - (esp_t - reb))
    cor = "#1a7a3c" if sobra >= 0 else C_ATEN
    D.linha(ox - 3.0 * S / 2, z_pta, ox + 3.0 * S / 2, z_pta, L_CONTORNO, cor)
    D.cota_v(min(z_pta, oy + prof * S), max(z_pta, oy + prof * S), ox + 26,
             vg(abs(sobra)), ox + 3.0 * S / 2, tam=FONTE_P)
    D.txt(ox + 30, (oy + prof * S + z_pta) / 2 + 1,
          f"folga no fundo {vg(sobra)}" if sobra >= 0
          else f"INTERFERÊNCIA {vg(-sobra)}", FONTE_P, anc="start", cor=cor)

    D.cota_v(oy, oy + prof * S, ox - w - 22, vg(prof), ox - w, tam=FONTE_P)
    D.cota_v(oy - esp_t * S, oy, ox - w - 22, vg(esp_t), ox - w - 10,
             tam=FONTE_P)
    D.txt(ox - w - 12, oy - esp_t * S - 4, "TAMPA", FONTE_P, anc="end",
          cor=C_TXT)
    D.txt(ox - w - 2, oy + 8, "PAREDE", FONTE_P, anc="end", cor=C_TXT)
    D.rotulo_vista(ox, oy + H * S + 10, "DETALHE - topo da parede", "4:1")


# =====================================================================
# 3. Tampa  (tampa.3mf)
# =====================================================================

def desenho_tampa_3mf(objs):
    V, T = objs["1"]
    z0 = min(p[2] for p in V)
    z1 = max(p[2] for p in V)
    zm = sorted({round(p[2], 3) for p in V})[1]
    esp = z1 - z0
    hreb = z1 - zm

    conts, passantes = analisar(V, T, (z0 + zm) / 2)
    _, rebaixos = analisar(V, T, (zm + z1) / 2)
    lo = conts[0]
    larg = max(p[0] for p in lo) - min(p[0] for p in lo)
    alt = max(p[1] for p in lo) - min(p[1] for p in lo)
    R = raio_canto(lo)
    dp, dr = 2 * passantes[0][2], 2 * rebaixos[0][2]

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - TAMPA DE SERVIÇO",
                "Vista superior, corte e detalhe do furo de fixação",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-03")
    W = Vista(60, 70, larg, alt)

    contorno(D, lo, W)
    for f in rebaixos:
        furo(D, W, f)
    for f in passantes:
        furo(D, W, f, marca=False, lw=L_TRACO, cor="#555", dash=D_OCULTA)

    yb = W.py(0)
    xs = sorted({round(f[0], 3) for f in rebaixos})
    ys = sorted({round(f[1], 3) for f in rebaixos})
    D.cota_h(W.px(0), W.px(xs[1]), yb + 14, vg(xs[1]), yb)
    D.cota_h(W.px(0), W.px(xs[2]), yb + 26, vg(xs[2]), yb)
    D.cota_h(W.px(0), W.px(larg), yb + 38, vg(larg), yb)
    D.cota_v(W.py(alt), yb, W.px(0) - 14, vg(alt), W.px(0))
    D.cota_v(W.py(ys[0]), yb, W.px(larg) + 14, vg(ys[0]), W.px(larg))
    D.cota_v(W.py(ys[1]), yb, W.px(larg) + 28, vg(ys[1]), W.px(larg))

    D.bandeira(*W.p(xs[2], ys[2] + dr / 2), 1, ang=-45, comp=18)
    D.bandeira(W.px(larg - R * 0.293), W.py(alt - R * 0.293), 2, ang=-30,
               comp=18)

    D.rotulo_vista(W.px(larg / 2), yb + 50, "VISTA SUPERIOR", "1:1")

    # --- corte: rebaixo em cima, furo passante atravessando ---
    yc = yb + 72
    D.hachura(W.px(0), yc, larg, esp * 4)
    for f in rebaixos:
        D.ret(W.px(f[0]) - dp / 2, yc, dp, esp * 4, L_CONTORNO, fill="#fff")
        D.ret(W.px(f[0]) - dr / 2, yc, dr, hreb * 4, L_CONTORNO, fill="#fff")
    D.cota_v(yc, yc + esp * 4, W.px(0) - 14, vg(esp), W.px(0))
    D.rotulo_vista(W.px(larg / 2), yc + esp * 4 + 10,
                   "CORTE - furos de fixação projetados", "vertical 4:1")

    _detalhe(D, 470, 100, esp, hreb, dp, dr)

    y = D.notas(COL_DIR, 172, [
        (1, f"6x &#216;{vg(dp)} passante com rebaixo &#216;{vg(dr)} x "
            f"{vg(hreb)} para a cabeça do parafuso M3 ISO 7380."),
        (2, f"Silhueta idêntica à do corpo: {vg(larg)} x {vg(alt)}, cantos "
            f"R{vg(R)}."),
        (3, f"Espessura {vg(esp)}; sob a cabeça do parafuso restam "
            f"{vg(esp - hreb)} mm - é a seção mais fina da peça."),
        (4, "Fixação com 6x M3 x 6 ISO 7380 em inserto de latão M3 no corpo "
            "(ver desenho PIBIC-CX-02)."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=240)

    tabela_furos(D, COL_DIR, y + 14, rebaixos,
                 "COORDENADAS DOS FUROS - origem no canto inferior esquerdo")
    D.salvar("desenho-caixa-tampa.svg")


def _detalhe(D, ox, oy, esp, hreb, dp, dr):
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
    D.txt(ox + rr + 8, oy - 2, "M3 x 6 ISO 7380 (ref.)", FONTE_P,
          anc="start", cor=C_REF)
    D.linha(ox + rr + 7, oy - 3, ox + dk * 0.6, oy + k * 0.45, L_FINA, C_REF)

    D.cota_h(ox - rr, ox + rr, oy - 9, f"&#216;{vg(dr)}", oy, tam=FONTE_P)
    D.cota_h(ox - rp, ox + rp, oy + ht + 13, f"&#216;{vg(dp)}", oy + ht,
             tam=FONTE_P)
    D.cota_v(oy, oy + hr, ox - W - 9, vg(hreb), ox - W, tam=FONTE_P)
    D.cota_v(oy + hr, oy + ht, ox - W - 9, vg(esp - hreb), ox - W, tam=FONTE_P)
    D.cota_v(oy, oy + ht, ox - W - 24, vg(esp), ox - W, tam=FONTE_P)
    D.bandeira(ox + rp + 2, oy + (hr + ht) / 2, 3, ang=0, comp=W - rp)
    D.rotulo_vista(ox, oy + ht + 26, "DETALHE - furo de fixação (6x)", "8:1")


if __name__ == "__main__":
    print("desenhos gerados a partir dos .3mf:")
    caixa = ler_3mf("Projeto PIBIC-caixa.3mf")
    desenho_painel(caixa)
    desenho_corpo(caixa)
    desenho_tampa_3mf(ler_3mf("tampa.3mf"))
