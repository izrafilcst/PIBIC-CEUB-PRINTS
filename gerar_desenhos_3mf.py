#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desenhos tecnicos das pecas da caixa - PIBIC UniCEUB.
Autor: Rafael Alves de Sousa Costa.

Le a geometria DIRETO dos .3mf, entao o desenho nao pode divergir do modelo:
toda cota sai de uma medicao na malha, nenhuma e digitada a mao.

  caixa-corpo.3mf   -> desenho-caixa-corpo.svg    PIBIC-CX-02
  caixa-tampa.3mf   -> desenho-caixa-tampa.svg    PIBIC-CX-03
  caixa-corpo.3mf   -> desenho-caixa-chave.svg    PIBIC-CX-04

A CX-01 esta APOSENTADA. Ela era a prancha do painel dos botoes, que deixou
de ser peca quando foi fundido dentro do corpo. As outras tres mantiveram o
numero de proposito - ha referencia cruzada a elas no README.

A CX-04 e detalhe do mesmo corpo da CX-02, em prancha propria: a estacao da
chave envolve um componente COMPRADO, uma faixa de espessura de painel que o
desenho do fabricante nao cota, e uma sequencia de montagem.

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
# 1. Corpo - painel e corpo fundidos
# =====================================================================

def medir_corpo(V, T):
    """
    Tudo o que as pranchas do corpo precisam, medido na malha.

    NAO da para usar 'camadas' aqui, e a razao e a estacao da chave. 'camadas'
    enumera as quebras de perfil supondo peca prismatica e indexa o resultado
    por posicao - cam[0], cam[1], cam[-1]. O circulo do rebaixo da chave,
    discretizado, poe 54 alturas distintas no corpo, e aquele indexar passa a
    apontar para camadas que nao tem nada a ver com o que se quer medir.

    Aqui cada sonda corta numa altura ESCOLHIDA, dentro da faixa da feicao que
    ela mede. E 'bate' confere tudo contra gerar_modelo_3mf.py no fim.
    """
    zs = niveis(V)
    m = dict(hh=zs[-1], reb_al=zs[1])
    m["prof_ins"] = m["hh"] - zs[-2]        # ultima quebra antes do topo
    # espessura do painel: a primeira altura, acima do alivio, em que a secao
    # deixa de ser so a silhueta e passa a ter tambem o contorno da cavidade.
    # E medicao - nao 'zs[2]', que so estaria certo por acidente de ordem.
    m["esp_pain"] = next(z for z in zs if z > m["reb_al"]
                         and len(analisar(V, T, z + 1e-3)[0]) > 1)

    k = P.estacao_chave()
    # boca dos furos, dentro do alivio; painel macico, ja no diametro nominal;
    # parede acima do painel e ABAIXO da estacao da chave; inserto no furo cego
    _, f_al = analisar(V, T, m["reb_al"] / 2)
    _, f_pa = analisar(V, T, (m["reb_al"] + P.PAIN_ESP) / 2)
    c_pr, _ = analisar(V, T, (P.PAIN_ESP + k["z"] - k["d_rebaixo"] / 2) / 2)
    c_in, f_in = analisar(V, T, m["hh"] - m["prof_ins"] / 2)

    m["ext"], m["cav"] = c_pr[0], c_pr[1]
    m["larg"] = max(p[0] for p in m["ext"]) - min(p[0] for p in m["ext"])
    m["alt"] = max(p[1] for p in m["ext"]) - min(p[1] for p in m["ext"])
    m["R"] = raio_canto(m["ext"])
    m["larg_i"] = max(p[0] for p in m["cav"]) - min(p[0] for p in m["cav"])
    m["alt_i"] = max(p[1] for p in m["cav"]) - min(p[1] for p in m["cav"])
    m["Ri"] = raio_canto(m["cav"])
    m["par"] = min(dist_ate(p, m["ext"]) for p in m["cav"])

    m["ins"] = f_in
    m["dins"] = 2 * f_in[0][2]
    m["col"] = 2 * max(raio_coluna(V, f[0], f[1], m["dins"] / 2 + 0.5,
                                   P.FIX_INSET - 0.2) for f in f_in)

    rs, rsa = raios(f_pa), raios(f_al)
    m["barril"] = por_raio(f_pa, max(rs))
    m["led"] = por_raio(f_pa, min(rs))
    m["al_bar"] = por_raio(f_al, max(rsa))
    m["al_led"] = por_raio(f_al, min(rsa))

    # cada barril com os LEDs que ficam sob a capa dele. O limiar de 40 mm
    # separa com folga: os LEDs do vermelho estao a 31,50 do proprio centro e
    # a 52,50 do verde; os do verde, a 21,00 e 63,00.
    m["botoes"] = []
    for bar in m["barril"]:
        sob = [f for f in m["led"]
               if math.hypot(f[0] - bar[0], f[1] - bar[1]) < 40]
        rf = sum(math.hypot(f[0] - bar[0], f[1] - bar[1]) for f in sob) / len(sob)
        m["botoes"].append(dict(x=bar[0], y=bar[1], barril=bar, leds=sob, rf=rf))
    m["botoes"].sort(key=lambda b: b["x"])
    return m


def medir_chave(V, hh):
    """
    A estacao da chave, lida dos VERTICES e nao de um corte.

    E a unica feicao da caixa com eixo HORIZONTAL: nao aparece em 'camadas' e
    nenhum corte em z mede o diametro dela. Mas os vertices dos dois circulos
    caem em tres planos de y bem definidos, e ali o raio sai exato - os pontos
    estao SOBRE o circulo, nao inscritos nele como acontece num corte.

    Dois filtros isolam o que interessa. O de z descarta tudo que esta nas
    cotas do painel e do topo, que e onde vivem os contornos prismaticos; o de
    y restringe a parede de tras. Sem o segundo, os circulos dos furos de
    inserto entrariam na conta.
    """
    por_y = defaultdict(list)
    for x, y, z in V:
        if P.PAIN_ESP + 1e-6 < z < hh - 1e-6 and y > P.CX_A - P.CORPO_PAR - 1e-6:
            por_y[round(y, 3)].append((x, z))

    achado = {}
    for y, pts in por_y.items():
        if len(pts) < 8:
            continue
        cx = (max(q[0] for q in pts) + min(q[0] for q in pts)) / 2
        cz = (max(q[1] for q in pts) + min(q[1] for q in pts)) / 2
        rs = sorted(math.hypot(q[0] - cx, q[1] - cz) for q in pts)
        grupos = [[rs[0]]]
        for r in rs[1:]:
            if r - grupos[-1][-1] < 0.05:
                grupos[-1].append(r)
            else:
                grupos.append([r])
        if all(g[-1] - g[0] < 0.06 for g in grupos):
            achado[y] = (cx, cz, [g[-1] for g in grupos])

    ys = sorted(achado)
    assert len(ys) == 3, f"esperava 3 planos na estacao da chave, achei {ys}"
    y_cav, y_reb, y_face = ys
    cx, cz, r_reb = achado[y_cav]
    return dict(x=cx, z=cz, y_cav=y_cav, y_reb=y_reb, y_face=y_face,
                d_rebaixo=2 * max(r_reb),
                d_furo=2 * max(achado[y_face][2]),
                prof_reb=y_reb - y_cav, parede=y_face - y_reb)


def desenho_corpo():
    V, T = ler_3mf("caixa-corpo.3mf")
    m = medir_corpo(V, T)
    sw = medir_chave(V, m["hh"])
    k = P.estacao_chave()
    hh, par, ins, dins = m["hh"], m["par"], m["ins"], m["dins"]

    # ---- conferencia contra o modelo ----
    bate("corpo: altura", hh, P.CORPO_H)
    bate("corpo: largura", m["larg"], P.CX_L)
    bate("corpo: profundidade", m["alt"], P.CX_A)
    bate("corpo: raio de canto", m["R"], P.CX_R)
    bate("corpo: parede", par, P.CORPO_PAR, tol=0.05)
    bate("corpo: espessura do painel", m["esp_pain"], P.PAIN_ESP)
    bate("corpo: alivio de boca", m["reb_al"], P.REB_ALIVIO)
    bate("corpo: Ø da coluna", m["col"], P.COL_D)
    bate("corpo: Ø do inserto", dins, P.D_INSERTO)
    bate("corpo: profundidade do inserto", m["prof_ins"], P.PROF_INSERTO)
    bate("corpo: n de colunas", len(ins), 6)
    bate("corpo: Ø do barril", 2 * m["barril"][0][2], P.D_BARRIL)
    bate("corpo: Ø do alivio do barril", 2 * m["al_bar"][0][2],
         P.D_BARRIL + P.FOLGA_ALIVIO)
    bate("corpo: Ø do LED", 2 * m["led"][0][2], P.D_LED)
    bate("corpo: Ø do alivio do LED", 2 * m["al_led"][0][2],
         P.D_LED + P.FOLGA_ALIVIO)
    bate("corpo: n de barris", len(m["barril"]), len(P.BOTOES))
    bate("corpo: n de LEDs", len(m["led"]),
         sum(b["led_n"] for b in P.BOTOES))
    bate("chave: x do eixo", sw["x"], k["x"])
    bate("chave: z do eixo", sw["z"], k["z"])
    bate("chave: Ø do rebaixo", sw["d_rebaixo"], k["d_rebaixo"])
    bate("chave: Ø do furo", sw["d_furo"], k["d_furo"])
    bate("chave: parede local", sw["parede"], k["parede"])

    L_tampa = P.TAMPA_ESP - P.REB_TAMPA + P.PENETRACAO

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - CORPO E PAINEL",
                "Peça única. Vista frontal, vista superior e detalhes",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-02")

    # ---------------- vista frontal ----------------
    OX = 60.0
    _vista_frontal(D, OX, 40.0, m["larg"], hh, par, P.TAMPA_ESP,
                   sorted({round(f[0], 3) for f in ins}), dins,
                   m["prof_ins"], sw, P.PAIN_ESP)

    # ---------------- vista superior ----------------
    W = Vista(OX, 172, m["larg"], m["alt"])
    contorno(D, m["ext"], W)
    contorno(D, m["cav"], W, lw=L_TRACO, cor="#555", dash=D_OCULTA)
    for f in m["al_bar"] + m["al_led"]:
        furo(D, W, f, marca=False)
    for f in m["barril"] + m["led"]:
        furo(D, W, f, lw=L_TRACO, cor="#555", dash=D_OCULTA)
    for f in ins:
        furo(D, W, f, lw=L_TRACO, cor="#555", dash=D_OCULTA)
    for b in m["botoes"]:
        D.circ(*W.p(b["x"], b["y"]), b["rf"], L_FINA, cor=C_ATEN,
               dash=D_CENTRO)
        # o circulo de furacao dos LEDs e a unica cota que os localiza: sao 9
        # furos e a tabela sozinha nao mostra que eles sao equiespacados
        D.cota_h(*[W.px(b["x"] + s * b["rf"]) for s in (-1, 1)],
                 W.py(b["y"] - b["rf"]) + 10,
                 f"{dm(2 * b['rf'])} - {len(b['leds'])} furos a "
                 f"{360 // len(b['leds'])}°", W.py(b["y"]), tam=FONTE_P)

    # a chave, na parede de tras, em posicao verdadeira
    D.circ(*W.p(sw["x"], m["alt"] - sw["parede"] / 2), sw["d_furo"] / 2,
           L_TRACO, cor="#555", dash=D_OCULTA)
    D.centro(*W.p(sw["x"], m["alt"]), sw["d_rebaixo"] / 2 + 3)

    yb = W.py(0)
    xs = sorted({round(f[0], 3) for f in ins})
    ys = sorted({round(f[1], 3) for f in ins})
    D.cota_h(W.px(0), W.px(m["botoes"][0]["x"]), W.py(m["alt"]) - 14,
             vg(m["botoes"][0]["x"]), W.py(m["alt"]))
    D.cota_h(W.px(0), W.px(m["botoes"][1]["x"]), W.py(m["alt"]) - 26,
             vg(m["botoes"][1]["x"]), W.py(m["alt"]))
    D.cota_h(W.px(0), W.px(sw["x"]), W.py(m["alt"]) - 38, vg(sw["x"]),
             W.py(m["alt"]))
    D.cota_h(W.px(0), W.px(m["larg"]), yb + 26, vg(m["larg"]), yb)
    D.cota_v(W.py(m["alt"]), yb, W.px(0) - 28, vg(m["alt"]), W.px(0))
    D.cota_v(W.py(ys[0]), yb, W.px(m["larg"]) + 14, vg(ys[0]), W.px(m["larg"]))
    D.cota_v(W.py(ys[1]), yb, W.px(m["larg"]) + 28, vg(ys[1]), W.px(m["larg"]))

    D.bandeira(*W.p(m["botoes"][0]["x"], m["botoes"][0]["y"] + 13), 1,
               ang=-90, comp=16)
    D.bandeira(*W.p(xs[2], ys[2] + dins / 2), 2, ang=-45, comp=18)
    D.bandeira(W.px(m["larg"] - m["R"] * 0.293),
               W.py(m["alt"] - m["R"] * 0.293), 3, ang=-30, comp=18)
    D.bandeira(*W.p(sw["x"], m["alt"]), 5, ang=-135, comp=20)
    D.rotulo_vista(W.px(m["larg"] / 2), yb + 38, "VISTA SUPERIOR", "1:1")

    # ---------------- detalhes ----------------
    _detalhe_alivio(D, 468, 92, m)
    _detalhe_coluna(D, 468, 214, par, m["col"], m["prof_ins"], dins, hh)

    # ---------------- notas ----------------
    y = D.notas(COL_DIR, 40, [
        (1, f"PEÇA ÚNICA: painel e corpo fundidos. O painel tem "
            f"{vg(P.PAIN_ESP)} mm maciços e é LISO - não há mais rebaixo de "
            f"capa, e não há furo de fixação nele."),
        (None, f"{len(m['barril'])}x barril {dm(2*m['barril'][0][2])} passante "
               f"e {len(m['led'])}x {dm(2*m['led'][0][2])} sob as capas."),
        (2, f"{len(ins)} colunas {dm(m['col'])} com furo {dm(dins)} x "
            f"{vg(m['prof_ins'])} SÓ NO TOPO - inserto de latão M3 a quente. "
            f"São {len(ins)} insertos, não 12:"),
        (None, "o painel deixou de ser parafusado quando virou parte do "
               "corpo. Coordenadas na tabela abaixo."),
        (3, f"Contorno externo {vg(m['larg'])} x {vg(m['alt'])}, cantos "
            f"R{vg(m['R'])}. Cavidade {vg(m['larg_i'])} x {vg(m['alt_i'])}, "
            f"cantos R{vg(m['Ri'])}, com a mordida das {len(ins)} colunas."),
        (4, f"Alívio de boca {dm(2*m['al_bar'][0][2])} x {vg(m['reb_al'])} nos "
            f"barris e {dm(2*m['al_led'][0][2])} x {vg(m['reb_al'])} nos LEDs. "
            f"É rebaixo reto, não chanfro."),
        (5, f"Estação da chave KCD1 na parede de trás - ver PIBIC-CX-04."),
        (6, f"Fixação da tampa: {len(ins)}x M3 x {L_tampa:.0f} ISO 7380."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=250)

    y = D.notas(COL_DIR, y + 4, [
        (None, f"Altura da caixa montada = {vg(hh)} (peça única) + "
               f"{vg(P.TAMPA_ESP)} (tampa) = {vg(hh + P.TAMPA_ESP)} mm."),
        (None, "ORIENTAÇÃO DE IMPRESSÃO: a face dos botões vai na MESA, a "
               "caixa cresce para cima. É a única orientação possível - de "
               "boca para baixo o painel teria de"),
        (None, f"fazer ponte sobre {vg(m['larg_i'])} x {vg(m['alt_i'])} mm. "
               f"SEM SUPORTE: sem rebaixo de capa, não sobra um milímetro de "
               f"balanço na peça."),
        (None, "A primeira camada é a face VISÍVEL dos botões - a textura da "
               "mesa transfere direto para ela."),
        (None, "As porcas M24 dos dois botões são apertadas POR DENTRO, com a "
               "mão entrando pela boca de baixo. Não dá mais para montar os "
               "botões na bancada."),
        (None, "NÃO há passagem de cabo. Definir com o microcontrolador - de "
               "preferência nesta mesma parede, entre x = 94 e x = 123."),
    ], titulo="OBSERVAÇÕES DE PROJETO", larg=250)

    itens = ([(f"BARRIL {i}", f[0], f[1], 2 * f[2])
              for i, f in enumerate(m["barril"], 1)]
             + [(f"LED {i}", f[0], f[1], 2 * f[2])
                for i, f in enumerate(m["led"], 1)]
             + [(f"COLUNA {i}", f[0], f[1], dins)
                for i, f in enumerate(ins, 1)])
    tabela_furos(D, COL_DIR, y + 14, itens,
                 "FUROS - origem no canto inferior esquerdo", por_coluna=8)
    D.salvar("desenho-caixa-corpo.svg")


def _vista_frontal(D, ox, y_top, larg, hh, par, esp_tampa, xs, dins, prof,
                   sw, esp_pain):
    """
    Elevacao da peca fundida, com a tampa em linha de referencia para dar a
    altura da caixa montada.

    y_top e a face dos BOTOES, que e a que vai na mesa. No 1o diedro a vista
    superior fica abaixo desta, entao a face que aparece aqui e a aresta de
    BAIXO daquela: a parede da FRENTE, y = 0.

    A chave esta na parede de TRAS, y = 130, logo aqui ela e feicao OCULTA e
    sai inteira em tracejado - inclusive o furo. Desenha-la em linha cheia
    diria que ela esta na parede da frente, que e a face que o observador
    desta vista encosta.

    O x nao espelha. Olhando de -y para +y com +z para cima, a direita e +x,
    o mesmo sentido da vista superior - as duas vistas ficam alinhadas.
    """
    y0 = y_top                      # face dos botoes (z = 0)
    y1 = y_top + hh                 # assento da tampa (z = hh)
    y_t = y1 + esp_tampa

    D.ret(ox, y0, larg, hh, L_CONTORNO)
    D.ret(ox, y1, larg, esp_tampa, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + larg + 4, y_t - 1, "TAMPA (ref.)", FONTE_P, anc="start",
          cor=C_REF)

    # limite painel / cavidade
    D.linha(ox + par, y0 + esp_pain, ox + larg - par, y0 + esp_pain,
            L_TRACO, "#555", dash=D_OCULTA)
    for x in (ox + par, ox + larg - par):
        D.linha(x, y0 + esp_pain, x, y1, L_TRACO, "#555", dash=D_OCULTA)
    for x in xs:
        for sg in (-1, 1):
            D.linha(ox + x + sg * dins / 2, y1 - prof,
                    ox + x + sg * dins / 2, y1, L_TRACO, "#555", dash=D_OCULTA)
        D.linha(ox + x - dins / 2, y1 - prof, ox + x + dins / 2, y1 - prof,
                L_TRACO, "#555", dash=D_OCULTA)

    # a chave esta na parede OPOSTA a que esta vista mostra: tudo tracejado
    xc, yc = ox + sw["x"], y0 + sw["z"]
    D.circ(xc, yc, sw["d_furo"] / 2, L_TRACO, cor="#555", dash=D_OCULTA)
    D.circ(xc, yc, sw["d_rebaixo"] / 2, L_TRACO, cor="#555", dash=D_OCULTA)
    D.txt(xc + sw["d_rebaixo"] / 2 + 4, yc - 4,
          "chave na parede de trás (oculta) - ver CX-04", FONTE_P,
          anc="start", cor=C_REF)
    D.centro(xc, yc, sw["d_rebaixo"] / 2 + 4)

    D.cota_v(y0, y1, ox - 14, vg(hh), ox)
    D.cota_v(y0, y0 + esp_pain, ox - 28, vg(esp_pain), ox, tam=FONTE_P)
    D.cota_v(y0, y_t, ox - 42, vg(hh + esp_tampa), ox)
    D.cota_h(ox, xc, y_t + 14, vg(sw["x"]), y_t)
    # z da chave e medido da face dos BOTOES, entao a cota sai de y0 - nao do
    # assento da tampa, que daria 28 desenhados sob um texto de 35
    D.cota_v(y0, yc, ox + larg + 16, vg(sw["z"]), ox + larg)
    D.rotulo_vista(ox + larg / 2, y_t + 30, "VISTA FRONTAL", "1:1")


def _detalhe_alivio(D, ox, oy, m, S=8.0):
    """
    O alivio de boca em corte, ampliado.

    Ele existe porque na orientacao de impressao os furos NASCEM na primeira
    camada, e o pe de elefante os fecharia. E rebaixo reto e nao chanfro por
    causa da conferencia de volume do gerador: chanfro e cone, cone nao tem
    area de poligono, e a malha deixaria de casar com o valor analitico.
    """
    d, da = 2 * m["barril"][0][2], 2 * m["al_bar"][0][2]
    h, ht = m["reb_al"] * S, 3.0 * S
    r, ra = d / 2 * S, da / 2 * S
    W = 46.0
    for sg in (-1, 1):
        D.hachura_poli([(ox + sg * W, oy), (ox + sg * ra, oy),
                        (ox + sg * ra, oy + h), (ox + sg * r, oy + h),
                        (ox + sg * r, oy + ht), (ox + sg * W, oy + ht)])
    D.txt(ox, oy - 8, "face dos botões - vai na MESA", FONTE_P, cor=C_REF)
    D.cota_h(ox - ra, ox + ra, oy - 3, dm(da), oy, tam=FONTE_P)
    D.cota_h(ox - r, ox + r, oy + ht + 12, dm(d), oy + ht, tam=FONTE_P)
    D.cota_v(oy, oy + h, ox - W - 10, vg(m["reb_al"]), ox - W, tam=FONTE_P)
    D.bandeira(ox + ra + 2, oy + h / 2, 4, ang=0, comp=W - ra)
    D.rotulo_vista(ox, oy + ht + 24,
                   "DETALHE - alívio de boca (11x)", f"{S:.0f}:1")

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
          f"furo {dm(dfuro)} x {vg(prof)} SÓ NA PONTA DE CIMA",
          FONTE_P, cor=C_TXT)
    D.txt(cx, cy + R + 28.5,
          "inserto de latão M3 &#216;ext 4,6 x 4,0", FONTE_P, cor=C_TXT)
    D.rotulo_vista(cx, cy + R + 40,
                   "DETALHE - coluna de inserto (6x)", "4:1")

# =====================================================================
# 2. Tampa de servico, com o encaixe da perfboard
# =====================================================================

def _esp_chapa(V, T, zs):
    """
    Espessura da chapa da tampa, medida: a ultima faixa de z em que a secao
    ainda tem a silhueta inteira. Acima dela so existem os pinos, e o contorno
    mais largo passa a ser uma perna.
    """
    for z0, z1 in zip(zs, zs[1:]):
        c, _ = analisar(V, T, (z0 + z1) / 2)
        larg = max(p[0] for p in c[0]) - min(p[0] for p in c[0])
        if larg < P.CX_L / 2:
            return z0
    return zs[-1]


def _centros_pino(V, T, z, tol=8.0):
    """
    Centros dos pinos na altura z, agrupando os pontos da secao por
    proximidade. Acima da chapa so existem as pernas, entao cada aglomerado e
    um pino - as duas metades dele juntas.
    """
    pts = [p for s in secao(V, T, z) for p in s]
    grupos = []
    for q in pts:
        for g in grupos:
            if math.hypot(q[0] - g[0][0], q[1] - g[0][1]) < tol:
                g.append(q)
                break
        else:
            grupos.append([q])
    cs = [((max(x for x, _ in g) + min(x for x, _ in g)) / 2,
           (max(y for _, y in g) + min(y for _, y in g)) / 2) for g in grupos]
    return sorted(cs, key=lambda c: (round(c[1], 1), c[0]))


def _diam_pino(V, T, c, z, r_max=6.0):
    """Diametro externo da perna na altura z - o maior raio em volta de 'c'."""
    rs = [math.hypot(p[0] - c[0], p[1] - c[1])
          for s in secao(V, T, z) for p in s
          if math.hypot(p[0] - c[0], p[1] - c[1]) < r_max]
    return 2 * max(rs) if rs else None


def _fenda_pino(V, T, c, z, r_max=6.0):
    """
    Largura da fenda na altura z. E o dobro da menor distancia em x ate o
    eixo: os pontos da CORDA de cada perna caem todos sobre x = cx +- w/2.
    """
    dx = [abs(p[0] - c[0]) for s in secao(V, T, z) for p in s
          if math.hypot(p[0] - c[0], p[1] - c[1]) < r_max]
    return 2 * min(dx) if dx else None


def desenho_tampa():
    V, T = ler_3mf("caixa-tampa.3mf")
    zs = niveis(V)
    pn = P.pinos_placa()
    pl = P.PLACA
    hreb = zs[1]
    alt_total = zs[-1]
    esp = _esp_chapa(V, T, zs)

    # A chapa: corte a meia espessura do rebaixo e a meia espessura da
    # passagem. z = 0 e a face EXTERNA - a tampa inverteu quando ganhou os
    # pinos, porque ela passou a imprimir com eles para cima.
    c_r, f_r = analisar(V, T, hreb / 2)
    c_p, f_p = analisar(V, T, (hreb + esp) / 2)
    lo = c_r[0]
    larg = max(p[0] for p in lo) - min(p[0] for p in lo)
    alt = max(p[1] for p in lo) - min(p[1] for p in lo)
    R = raio_canto(lo)
    rebaixos, passantes = f_r, f_p
    dp, dr = 2 * passantes[0][2], 2 * rebaixos[0][2]

    # os pinos, MEDIDOS na malha. 'analisar' nao serve aqui: a secao de uma
    # perna e um D (arco + corda), 'eh_circulo' a rejeita e devolveria zero
    # furos em toda altura - uma sonda que sempre concorda.
    centros = _centros_pino(V, T, esp + (pn["z"][1] + pn["z"][2]) / 2)
    perfil = [dict(z0=z0, z1=z1,
                   d=_diam_pino(V, T, centros[0], esp + (z0 + z1) / 2),
                   fenda=_fenda_pino(V, T, centros[0], esp + (z0 + z1) / 2))
              for z0, z1 in zip(pn["z"], pn["z"][1:])]

    bate("tampa: espessura da chapa", esp, P.TAMPA_ESP)
    bate("tampa: n de pinos", len(centros), len(pn["centros"]))
    for i, (c, d) in enumerate(zip(centros, pn["centros"]), 1):
        bate(f"tampa: pino {i} em x", c[0], d[0])
        bate(f"tampa: pino {i} em y", c[1], d[1])
    for pf, d_esp in zip(perfil, [pl["ombro_d"], pl["haste_d"], pl["farpa_d"]]
                         + [d for d, _ in pl["guia"]]):
        bate(f"tampa: pino Ø em z {pf['z0']:.2f}", pf["d"], d_esp)
        bate(f"tampa: fenda em z {pf['z0']:.2f}", pf["fenda"], pl["rasgo_w"])
    bate("tampa: altura total", alt_total, P.TAMPA_ESP + pn["topo"])
    bate("tampa: largura", larg, P.CX_L)
    bate("tampa: profundidade", alt, P.CX_A)
    bate("tampa: raio de canto", R, P.CX_R)
    bate("tampa: rebaixo", hreb, P.REB_TAMPA)
    bate("tampa: Ø de passagem", dp, P.D_PASSAGEM)
    bate("tampa: Ø do rebaixo", dr, P.D_REBAIXO)
    bate("tampa: n de furos", len(rebaixos), 6)
    bate("tampa: topo do pino", alt_total - esp, pn["topo"])

    L = esp - hreb + P.PENETRACAO

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - TAMPA DE SERVIÇO",
                "Vista superior, corte, furo de fixação e pino da perfboard",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-03")
    W = Vista(60, 56, larg, alt)

    contorno(D, lo, W)
    for f in rebaixos:
        furo(D, W, f)
    for f in passantes:
        furo(D, W, f, marca=False, lw=L_TRACO, cor="#555", dash=D_OCULTA)

    # a perfboard em linha fantasma, e os 4 pinos em posicao verdadeira
    D.ret(W.px(pl["x"] - pl["larg"] / 2), W.py(pl["y"] + pl["alt"] / 2),
          pl["larg"], pl["alt"], L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(*W.p(pl["x"], pl["y"] - pl["alt"] / 2 + 6),
          f"perfboard {vg(pl['larg'])} x {vg(pl['alt'])} (ref.)", FONTE_P,
          cor=C_REF)
    for cx, cy in pn["centros"]:
        D.circ(*W.p(cx, cy), pl["ombro_d"] / 2, L_CONTORNO)
        D.circ(*W.p(cx, cy), pl["farpa_d"] / 2, L_FINA, cor="#555",
               dash=D_OCULTA)
        D.centro(*W.p(cx, cy), pl["ombro_d"] / 2 + 2)

    yb = W.py(0)
    xs = sorted({round(f[0], 3) for f in rebaixos})
    ys = sorted({round(f[1], 3) for f in rebaixos})
    px = sorted({round(c[0], 3) for c in pn["centros"]})
    py = sorted({round(c[1], 3) for c in pn["centros"]})
    D.cota_h(W.px(0), W.px(xs[0]), yb + 14, vg(xs[0]), yb)
    D.cota_h(W.px(0), W.px(px[0]), yb + 26, vg(px[0]), yb)
    D.cota_h(W.px(0), W.px(px[1]), yb + 38, vg(px[1]), yb)
    D.cota_h(W.px(0), W.px(larg), yb + 50, vg(larg), yb)
    D.cota_v(W.py(alt), yb, W.px(0) - 14, vg(alt), W.px(0))
    D.cota_v(W.py(py[0]), yb, W.px(larg) + 14, vg(py[0]), W.px(larg))
    D.cota_v(W.py(py[1]), yb, W.px(larg) + 28, vg(py[1]), W.px(larg))

    D.bandeira(*W.p(xs[2], ys[2] + dr / 2), 1, ang=-45, comp=18)
    D.bandeira(W.px(larg - R * 0.293), W.py(alt - R * 0.293), 2, ang=-30,
               comp=18)
    D.bandeira(*W.p(pn["centros"][0][0], pn["centros"][0][1]), 5, ang=-135,
               comp=20)
    D.rotulo_vista(W.px(larg / 2), yb + 62, "VISTA SUPERIOR", "1:1")

    _detalhe_furo(D, 468, 84, esp, hreb, dp, dr, L)
    _detalhe_pino(D, 468, 236, pn, pl, esp)

    y = D.notas(COL_DIR, 40, [
        (1, f"{len(rebaixos)}x {dm(dp)} passante com rebaixo {dm(dr)} x "
            f"{vg(hreb)} para a cabeça do parafuso M3 ISO 7380."),
        (2, f"Silhueta idêntica à do corpo: {vg(larg)} x {vg(alt)}, cantos "
            f"R{vg(R)}."),
        (3, f"Chapa {vg(esp)}; sob a cabeça do parafuso restam "
            f"{vg(esp - hreb)} mm - é a seção mais fina da peça."),
        (4, f"Fixação com {len(rebaixos)}x M3 x {L:.0f} ISO 7380 em inserto de "
            f"latão M3 no topo das colunas do corpo (ver PIBIC-CX-02)."),
        (5, f"{len(pn['centros'])} pinos farpados prendem a perfboard "
            f"{vg(pl['larg'])} x {vg(pl['alt'])} POR ENCAIXE, sem parafuso. "
            f"Altura total da peça {vg(alt_total)}."),
        (6, "Imprimir com os PINOS PARA CIMA. O rebaixo dos parafusos fica "
            "então voltado para baixo, mas são 1,55 mm radiais sobre um vão "
            "de 6,50 - não pede suporte."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=250)

    y = D.notas(COL_DIR, y + 4, [
        (None, f"{dm(pl['furo_d'])} do furo da placa e recuo de "
               f"{vg(pl['furo_inset'])} da borda são PRESUMIDOS."),
        (None, "Meça a placa com o paquímetro antes de imprimir - errar o "
               "recuo põe os 4 pinos no lugar errado de uma vez."),
        (None, f"A placa assenta no ombro e é retida pela face de baixo da "
               f"farpa, com {vg(pl['folga_placa'])} mm de folga. As duas "
               f"metades de cada pino fletem"),
        (None, f"{vg((pl['farpa_d'] - pl['furo_d']) / 2)} mm para a farpa "
               f"passar pelo furo - deformação de flexão de "
               f"{100 * 3 * ((pl['haste_d'] - pl['rasgo_w']) / 2) * ((pl['farpa_d'] - pl['furo_d']) / 2) / (2 * pl['rasgo_h'] ** 2):.2f} %, "
               f"abaixo do escoamento do PLA."),
        (None, "Este é o ponto de desgaste da caixa: encaixar e desencaixar a "
               "placa muitas vezes cansa as farpas."),
    ], titulo="OBSERVAÇÕES DE PROJETO", larg=250)

    itens = (rotulos("FIX ", rebaixos)
             + [(f"PINO {i}", cx, cy, pl["ombro_d"])
                for i, (cx, cy) in enumerate(pn["centros"], 1)])
    tabela_furos(D, COL_DIR, y + 14, itens,
                 "COORDENADAS - origem no canto inferior esquerdo",
                 por_coluna=6)
    D.salvar("desenho-caixa-tampa.svg")


def _detalhe_pino(D, ox, oy, pn, pl, esp, S=8.0):
    """
    O pino da perfboard em corte, ampliado.

    O perfil e escalonado e nao conico de proposito: cone nao tem area de
    poligono, e a conferencia de volume do gerador deixaria de fechar. Dois
    degraus de 0,30 x 0,30 sao 45 graus efetivos para a placa entrar.
    """
    z = pn["z"]
    dd = [pl["ombro_d"], pl["haste_d"], pl["farpa_d"]] + [d for d, _ in pl["guia"]]
    hf = pl["rasgo_w"] / 2 * S
    y0 = oy

    # meia secao de cada lado, com a fenda no meio
    for sg in (-1, 1):
        pts = [(ox + sg * hf, y0)]
        for d, za, zb in zip(dd, z, z[1:]):
            pts += [(ox + sg * d / 2 * S, y0 - za * S),
                    (ox + sg * d / 2 * S, y0 - zb * S)]
        pts += [(ox + sg * dd[-1] / 2 * S, y0 - z[-1] * S),
                (ox + sg * hf, y0 - z[-1] * S)]
        D.hachura_poli(pts)
    # a chapa da tampa, sob o pino
    D.hachura(ox - 40, y0, 80, esp * S)

    # a placa assentada, em linha de referencia
    yp = y0 - z[1] * S
    for sg in (-1, 1):
        D.ret(ox + sg * pl["furo_d"] / 2 * S, yp - pl["esp"] * S,
              sg * (40 - pl["furo_d"] / 2 * S), pl["esp"] * S,
              L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + 44, yp - pl["esp"] * S / 2,
          f"perfboard {vg(pl['esp'])} (ref.)", FONTE_P, anc="start", cor=C_REF)

    D.cota_v(y0 - z[1] * S, y0, ox - 52, vg(z[1]), ox - 40, tam=FONTE_P)
    D.cota_v(y0 - z[2] * S, y0 - z[1] * S, ox - 52, vg(z[2] - z[1]), ox - 40,
             tam=FONTE_P)
    D.cota_v(y0 - z[3] * S, y0 - z[2] * S, ox - 52, vg(z[3] - z[2]), ox - 40,
             tam=FONTE_P)
    D.cota_v(y0 - z[-1] * S, y0, ox - 68, vg(z[-1]), ox - 40, tam=FONTE_P)
    D.cota_h(ox - dd[0] / 2 * S, ox + dd[0] / 2 * S, y0 + 12, dm(dd[0]), y0,
             tam=FONTE_P)
    D.cota_h(ox - dd[2] / 2 * S, ox + dd[2] / 2 * S, y0 - z[-1] * S - 22,
             dm(dd[2]), y0 - z[3] * S, tam=FONTE_P)
    D.cota_h(ox - hf, ox + hf, y0 - z[-1] * S - 10, vg(pl["rasgo_w"]),
             y0 - z[-1] * S, tam=FONTE_P)
    D.txt(ox, y0 - z[-1] * S - 30,
          f"haste {dm(dd[1])} - furo da placa {dm(pl['furo_d'])}", FONTE_P,
          cor=C_TXT)
    D.rotulo_vista(ox, y0 + 26,
                   f"DETALHE - pino da perfboard ({len(pn['centros'])}x)",
                   f"{S:.0f}:1")

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
# 3. Estacao da chave KCD1 - detalhe do mesmo corpo da CX-02
# =====================================================================

def desenho_chave():
    """
    Prancha propria porque a estacao envolve um componente COMPRADO, uma faixa
    de espessura de painel que o desenho do fabricante NAO cota, e uma
    sequencia de montagem. Nada disso cabe numa nota de rodape da CX-02.
    """
    V, T = ler_3mf("caixa-corpo.3mf")
    m = medir_corpo(V, T)
    sw = medir_chave(V, m["hh"])
    k = P.estacao_chave()
    C = P.CHAVE

    bate("chave: x do eixo", sw["x"], k["x"])
    bate("chave: z do eixo", sw["z"], k["z"])
    bate("chave: Ø do furo", sw["d_furo"], k["d_furo"])
    bate("chave: Ø do rebaixo", sw["d_rebaixo"], k["d_rebaixo"])
    bate("chave: profundidade do rebaixo", sw["prof_reb"], k["prof_reb"])
    bate("chave: parede local", sw["parede"], k["parede"])
    bate("chave: face da cavidade", sw["y_cav"], k["y_cav"])
    bate("chave: face externa", sw["y_face"], P.CX_A)

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - ESTAÇÃO DA CHAVE KCD1",
                "Elevação da parede de trás e corte no eixo da chave",
                escala="ver ampliações", codigo="PIBIC-CX-04")

    _chave_elevacao(D, 150, 70, sw, m)
    _chave_corte(D, 150, 250, sw, C)

    y = D.notas(COL_DIR, 40, [
        (1, f"Furo {dm(sw['d_furo'])} = corpo {dm(C['d_corpo'])} + "
            f"{vg(C['folga'])} de folga. Furo de eixo HORIZONTAL fecha mais "
            f"que furo em pé em PLA."),
        (None, f"O aro {dm(C['d_aro'])} cobre "
               f"{vg((C['d_aro'] - sw['d_furo']) / 2)} mm radiais - a folga "
               f"não aparece por fora."),
        (2, f"Rebaixo {dm(sw['d_rebaixo'])} x {vg(sw['prof_reb'])} abre SÓ "
            f"PARA DENTRO. A face externa é lisa."),
        (3, f"Parede local de {vg(sw['parede'])} mm: a chave é snap-in e as "
            f"garras querem painel fino. A parede cheia de {vg(m['par'])} não "
            f"entraria na faixa."),
        (None, "A faixa de espessura que as garras aceitam NÃO consta do "
               "desenho do fabricante - conferir antes de imprimir."),
        (4, "Sem chanfro no furo: por dentro é onde as garras mordem, e por "
            "fora seria cone."),
        (5, f"Posição: parede y = {vg(sw['y_face'])}, x = {vg(sw['x'])}, "
            f"z = {vg(sw['z'])}. x é o meio do único trecho reto livre, entre "
            f"a tangência do R{vg(m['R'])}"),
        (None, f"e a coluna central. Reserva de {vg(C['atras'])} mm atrás da "
               f"parede, ocupando até y = {vg(sw['y_reb'] - C['atras'])}."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=250)

    y = D.notas(COL_DIR, y + 4, [
        (None, "A chave entra POR FORA e trava sozinha nas garras. Não há "
               "cola nem parafuso - o berço colado da revisão anterior, para "
               "a chave deslizante SS12D00G4, foi"),
        (None, "abandonado junto com aquele componente."),
        (None, f"As pontes de impressão são o topo do furo ({vg(sw['d_furo'] / math.sqrt(2))} "
               f"mm) e o topo do rebaixo ({vg(sw['d_rebaixo'] / math.sqrt(2))} mm), "
               f"as duas apoiadas dos dois lados e com só"),
        (None, f"{vg(sw['prof_reb'])} mm de profundidade. PLA faz sem "
               f"suporte."),
    ], titulo="MONTAGEM", larg=250)

    cab = ("COTA", "VALOR [mm]", "ORIGEM")
    linhas = [
        ("corpo no painel", dm(C["d_corpo"]) + " ± 0,20", "fabricante"),
        ("aro visível", dm(C["d_aro"]) + " ± 0,20", "fabricante"),
        ("corpo atrás", dm(C["d_corpo_tras"]) if "d_corpo_tras" in C
         else "&#216;19,30", "fabricante"),
        ("profundidade do corpo", "17,80 ± 0,30", "fabricante"),
        ("total atrás do painel", vg(C["atras"]) + " ± 0,30", "fabricante"),
        ("terminais", "3, passo 7,00, vão 14,00", "fabricante"),
        ("lâmina faston", "4,80 x 0,80", "fabricante"),
        ("furo do painel", dm(sw["d_furo"]), "medido na malha"),
        ("rebaixo", dm(sw["d_rebaixo"]) + " x " + vg(sw["prof_reb"]),
         "medido na malha"),
        ("parede local", vg(sw["parede"]), "medido na malha"),
    ]
    D.txt(COL_DIR, y + 12, "COTAS DO COMPONENTE E DA ESTAÇÃO", 2.8,
          anc="start", peso="bold", cor=C_TXT)
    D.tabela(COL_DIR, y + 14, cab, linhas, (60, 60, 60))
    D.salvar("desenho-caixa-chave.svg")


def _chave_elevacao(D, ox, oy, sw, m, S=3.0):
    """
    A parede de tras vista DE FORA, ampliada. E a vista que decide se o aro
    cobre a borda do furo: e ela que a pessoa olha depois de montado.
    """
    xc, yc = ox, oy + 40
    D.ret(ox - 60, oy, 120, 80, L_FINA, cor="#555", dash=D_OCULTA)
    D.txt(ox, oy - 4, "trecho reto da parede de trás", FONTE_P, cor=C_REF)
    D.circ(xc, yc, sw["d_furo"] / 2 * S, L_CONTORNO)
    D.circ(xc, yc, P.CHAVE["d_aro"] / 2 * S, L_TRACO, cor=C_REF,
           dash=D_FANTASMA)
    D.circ(xc, yc, sw["d_rebaixo"] / 2 * S, L_TRACO, cor="#555", dash=D_OCULTA)
    D.centro(xc, yc, sw["d_rebaixo"] / 2 * S + 6)

    D.cota_h(xc - sw["d_furo"] / 2 * S, xc + sw["d_furo"] / 2 * S, oy + 96,
             dm(sw["d_furo"]), yc, tam=FONTE_P)
    D.cota_h(xc - P.CHAVE["d_aro"] / 2 * S, xc + P.CHAVE["d_aro"] / 2 * S,
             oy + 108, dm(P.CHAVE["d_aro"]) + " aro", yc, tam=FONTE_P)
    D.cota_h(xc - sw["d_rebaixo"] / 2 * S, xc + sw["d_rebaixo"] / 2 * S,
             oy + 120, dm(sw["d_rebaixo"]) + " rebaixo", yc, tam=FONTE_P)
    D.bandeira(xc + sw["d_furo"] / 2 * S * 0.7, yc - sw["d_furo"] / 2 * S * 0.7,
               1, ang=-45, comp=20)
    D.rotulo_vista(xc, oy + 134, "ELEVAÇÃO - parede vista de fora",
                   f"{S:.0f}:1")


def _chave_corte(D, ox, oy, sw, C, S=5.0):
    """
    Corte horizontal no eixo, com a chave montada em linha de referencia.

    E o desenho que mostra o que a elevacao nao mostra: o rebaixo abre para
    DENTRO, e sao os 2 mm que sobram que as garras mordem.
    """
    rr, rf = sw["d_rebaixo"] / 2 * S, sw["d_furo"] / 2 * S
    W = 90.0
    y_cav, y_reb, y_face = oy, oy + sw["prof_reb"] * S, oy + (sw["y_face"] - sw["y_cav"]) * S

    for sg in (-1, 1):
        D.hachura_poli([(ox + sg * W, y_cav), (ox + sg * rr, y_cav),
                        (ox + sg * rr, y_reb), (ox + sg * rf, y_reb),
                        (ox + sg * rf, y_face), (ox + sg * W, y_face)])

    # a chave em linha de referencia: aro por fora, corpo e terminais por dentro
    da, dc = C["d_aro"] / 2 * S, 19.3 / 2 * S
    D.ret(ox - da, y_face, 2 * da, 2.7 * S, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.ret(ox - dc, y_reb - 17.8 * S, 2 * dc, 17.8 * S, L_TRACO, cor=C_REF,
          dash=D_FANTASMA)
    D.ret(ox - 7.0 * S, y_reb - C["atras"] * S, 14.0 * S,
          (C["atras"] - 17.8) * S, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + dc + 6, y_reb - 17.8 * S / 2, "corpo da chave (ref.)", FONTE_P,
          anc="start", cor=C_REF)
    D.txt(ox + 7.0 * S + 6, y_reb - (C["atras"] + 17.8) / 2 * S,
          "terminais faston 4,80 (ref.)", FONTE_P, anc="start", cor=C_REF)
    D.txt(ox, y_face + 2.7 * S + 8, "FORA", FONTE_P, cor=C_TXT)
    D.txt(ox, y_cav - 6, "DENTRO (cavidade)", FONTE_P, cor=C_TXT)

    D.cota_v(y_cav, y_reb, ox - W - 10, vg(sw["prof_reb"]), ox - W,
             tam=FONTE_P)
    D.cota_v(y_reb, y_face, ox - W - 10, vg(sw["parede"]), ox - W,
             tam=FONTE_P)
    D.cota_v(y_cav, y_face, ox - W - 26, vg(sw["y_face"] - sw["y_cav"]),
             ox - W, tam=FONTE_P)
    D.cota_v(y_reb - C["atras"] * S, y_reb, ox + W + 12, vg(C["atras"]),
             ox + W, tam=FONTE_P)
    D.cota_h(ox - rr, ox + rr, y_cav - 16, dm(sw["d_rebaixo"]), y_cav,
             tam=FONTE_P)
    D.cota_h(ox - rf, ox + rf, y_face + 34, dm(sw["d_furo"]), y_face,
             tam=FONTE_P)
    D.bandeira(ox + rr, (y_cav + y_reb) / 2, 2, ang=0, comp=W - rr)
    D.bandeira(ox + rf, (y_reb + y_face) / 2, 3, ang=0, comp=W - rf)
    D.rotulo_vista(ox, y_face + 52, "CORTE A-A - no eixo da chave",
                   f"{S:.0f}:1")


if __name__ == "__main__":
    desenho_corpo()
    desenho_tampa()
    desenho_chave()
    encerrar_conferencia()
    print("conferidos contra gerar_modelo_3mf.py: nenhuma divergencia")
