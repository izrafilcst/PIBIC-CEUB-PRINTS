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

Pranchas em A2 RETRATO (420 x 594 mm), projecao no 1o diedro: a vista
superior fica ABAIXO da vista frontal e, nela, a face frontal da peca e a
aresta de baixo. As vistas e as ampliacoes ficam na metade de cima da folha,
o texto na de baixo com a largura inteira.

Alem da conferencia de cota, o script confere o LAYOUT: mede no SVG emitido a
caixa que cada bloco realmente ocupa e para se dois se sobrepuserem ou se um
sair da moldura. Cota nenhuma enxerga onde o desenho CAI na folha - foi assim
que as ampliacoes passaram a imprimir por cima das notas sem nada acusar.

Uso:  python gerar_desenhos_3mf.py
"""

import math
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict

import gerar_modelo_3mf as P
from gerar_desenhos import (Desenho, MARGEM, L_CONTORNO, L_FINA, L_TRACO,
                            D_OCULTA, D_CENTRO, D_FANTASMA,
                            FONTE, FONTE_P, C_COTA, C_REF, C_TXT, C_ATEN)
from validar_modelo import medir_berco

NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"

# Prancha em A2 RETRATO. A folha girou porque a paisagem obrigava vista e
# texto a dividirem a largura, e era dai que vinha a sobreposicao: as
# ampliacoes cresciam para a direita ate entrar na coluna de notas, que
# comeca sempre no mesmo x. Em retrato as vistas ocupam a metade de cima da
# folha inteira e o texto a de baixo, cada um com a largura toda.
FOLHA_W, FOLHA_H = 420.0, 594.0

# MARGEM vem de gerar_desenhos, que e quem desenha a moldura. SELO_H repete
# a altura da legenda declarada la em selo(); se uma mudar sem a outra, a
# conferencia de layout acusa - a area util encolhe e algum bloco cai fora.
SELO_H = 28.0
COL_DIR = MARGEM + 4.0             # texto comeca na margem, nao a meia folha
LARG_TEXTO = FOLHA_W - 2 * COL_DIR + 4.0
Y_TEXTO = 402.0                    # topo da faixa de texto, abaixo das vistas


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
    para dentro. Num arco de 7 graus da 0,01 mm, o bastante para a coluna de
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
_desarranjos = []


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
    if _desarranjos:
        raise AssertionError(
            "a prancha esta ilegivel - dois blocos ocupam o mesmo papel, ou "
            "um deles saiu da moldura. Reposicione em gerar_desenhos_3mf.py; "
            "o modelo nao tem nada a ver com isto:\n  - "
            + "\n  - ".join(_desarranjos))


# =====================================================================
# Conferencia de LAYOUT: caixa envolvente medida no SVG emitido
# =====================================================================
#
# As cotas ja sao conferidas contra o modelo, mas nenhuma delas enxerga onde
# o desenho CAI na folha - foi assim que as ampliacoes passaram a imprimir
# por cima das notas sem nada acusar. Estas funcoes leem de volta os
# elementos que o Desenho acabou de emitir e medem a area que cada bloco
# realmente ocupa. Nao ha valor digitado: a caixa sai da mesma string que vai
# para o arquivo.

_TAGS = re.compile(r"<(line|rect|circle|polygon|polyline|text|path)\s([^>]*?)/?>"
                   r"(?:([^<]*)</text>)?")
_ATR = re.compile(r'([\w:-]+)="([^"]*)"')
_NUM = re.compile(r"-?\d+(?:\.\d+)?")

# largura media de um caractere em DejaVu Sans, em fracao do corpo da fonte.
# Serve para dar largura ao <text>, que em SVG nao tem caixa declarada.
_LARG_CHAR = 0.60


def _caixa_texto(a, conteudo):
    x, y = float(a["x"]), float(a["y"])
    tam = float(a.get("font-size", FONTE))
    # entidades (&#216;) contam como um caractere so
    n = len(re.sub(r"&#\d+;", "0", conteudo or ""))
    w = n * tam * _LARG_CHAR
    anc = a.get("text-anchor", "start")
    x0 = x if anc == "start" else (x - w if anc == "end" else x - w / 2)
    if a.get("transform"):                      # texto girado (cotas verticais)
        return (x - tam, y - w / 2, x + tam * 0.3, y + w / 2)
    return (x0, y - tam * 0.8, x0 + w, y + tam * 0.25)


def caixa(elementos):
    """
    Uniao das caixas envolventes de uma fatia de Desenho.el.

    O conteudo de <defs> e descartado: a hachura declara ali um padrao de
    2 x 2 mm que NAO esta em coordenadas de folha, e some-lo puxaria toda
    caixa para a origem.
    """
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for el in elementos:
        for m in _TAGS.finditer(re.sub(r"<defs>.*?</defs>", "", el, flags=re.S)):
            tag, atrs, conteudo = m.group(1), m.group(2), m.group(3)
            a = dict(_ATR.findall(atrs))
            if tag == "line":
                pts = [(float(a["x1"]), float(a["y1"])),
                       (float(a["x2"]), float(a["y2"]))]
            elif tag == "rect":
                x, y = float(a["x"]), float(a["y"])
                pts = [(x, y), (x + float(a["width"]), y + float(a["height"]))]
            elif tag == "circle":
                cx, cy, r = float(a["cx"]), float(a["cy"]), float(a["r"])
                pts = [(cx - r, cy - r), (cx + r, cy + r)]
            elif tag in ("polygon", "polyline"):
                pts = [tuple(map(float, par.split(",")))
                       for par in a["points"].split()]
            elif tag == "path":
                v = [float(t) for t in _NUM.findall(a["d"])]
                pts = list(zip(v[0::2], v[1::2]))
            else:
                bx = _caixa_texto(a, conteudo)
                pts = [(bx[0], bx[1]), (bx[2], bx[3])]
            for px, py in pts:
                x0, y0 = min(x0, px), min(y0, py)
                x1, y1 = max(x1, px), max(y1, py)
    return None if x0 == float("inf") else (x0, y0, x1, y1)


class Blocos:
    """
    Registra a caixa de cada bloco da prancha conforme ele e desenhado.

    Uso:  with B("vista superior"): ...desenha...
    """

    def __init__(self, D, prancha):
        self.D, self.prancha, self.cx = D, prancha, {}

    def __call__(self, nome):
        pai = self

        class _Ctx:
            def __enter__(s):
                s.i = len(pai.D.el)
                return s

            def __exit__(s, *_):
                b = caixa(pai.D.el[s.i:])
                if b is not None:
                    pai.cx[nome] = b
                return False

        return _Ctx()

    def abre(self, nome):
        """Para blocos longos demais para caber num 'with' sem reindentar."""
        self._aberto = (nome, len(self.D.el))

    def fecha(self):
        nome, i = self._aberto
        b = caixa(self.D.el[i:])
        if b is not None:
            self.cx[nome] = b

    def conferir(self, folga=1.0):
        util = (MARGEM, MARGEM, self.D.w - MARGEM,
                self.D.h - MARGEM - SELO_H)
        for nome, (x0, y0, x1, y1) in sorted(self.cx.items()):
            if (x0 < util[0] - folga or y0 < util[1] - folga
                    or x1 > util[2] + folga or y1 > util[3] + folga):
                _desarranjos.append(
                    f"{self.prancha}: '{nome}' sai da area util - ocupa "
                    f"({x0:.1f}, {y0:.1f}) a ({x1:.1f}, {y1:.1f}), util vai "
                    f"ate ({util[2]:.1f}, {util[3]:.1f})")
        itens = sorted(self.cx.items())
        for i, (na, ca) in enumerate(itens):
            for nb, cb in itens[i + 1:]:
                w = min(ca[2], cb[2]) - max(ca[0], cb[0])
                h = min(ca[3], cb[3]) - max(ca[1], cb[1])
                if w > folga and h > folga:
                    _desarranjos.append(
                        f"{self.prancha}: '{na}' e '{nb}' se sobrepoem em "
                        f"{w:.1f} x {h:.1f} mm")


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
        # o 4o campo e diametro, ou ja o texto da medida (a janela e retangulo)
        linhas = [(n, vg(cx), vg(cy),
                   dm(d) if isinstance(d, (int, float)) else d)
                  for n, cx, cy, d in bloco]
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

    Restam tres indexacoes por posicao em 'zs' - a primeira quebra e as duas
    ultimas. Elas valem porque nada mora abaixo do alivio nem entre o furo do
    inserto e o topo, e nao porque a peca seja prismatica. Se alguma feicao
    nascer nessas faixas, e aqui que quebra.
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

    Tres filtros isolam o que interessa, e vale saber qual faz o que. O de z
    descarta as cotas do painel e do topo, onde vivem os contornos
    prismaticos. O de y restringe a parede de tras. Quem de fato rejeita os
    circulos dos furos de inserto e o TERCEIRO, 'len(pts) < 8': eles caem em
    planos de y como 126,06 por causa da coluna em (89, 124), passam pelo
    filtro de y e sao poucos pontos por plano. Se SEG_PEQ crescer, eles
    passam a ter 8 e o assert dispara - falha segura, mas o diagnostico esta
    aqui.
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
    # estes viram cota na prancha, entao tem de ser conferidos como as outras
    bate("corpo: largura da cavidade", m["larg_i"], P.CX_L - 2 * P.CORPO_PAR)
    bate("corpo: profundidade da cavidade", m["alt_i"], P.CX_A - 2 * P.CORPO_PAR)
    bate("corpo: raio da cavidade", m["Ri"], P.CX_R - P.CORPO_PAR)
    for b, spec in zip(m["botoes"], sorted(P.BOTOES, key=lambda s: s["x"])):
        bate(f"corpo: circulo de furacao do {spec['nome']}", b["rf"],
             spec["led_r"])
    bate("chave: x do eixo", sw["x"], k["x"])
    bate("chave: z do eixo", sw["z"], k["z"])
    bate("chave: Ø do rebaixo", sw["d_rebaixo"], k["d_rebaixo"])
    bate("chave: Ø do furo", sw["d_furo"], k["d_furo"])
    bate("chave: parede local", sw["parede"], k["parede"])

    L_tampa = P.TAMPA_ESP - P.REB_TAMPA + P.PENETRACAO

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - CORPO E PAINEL",
                "Peça única. Vista frontal, vista superior e detalhes",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-02")

    B = Blocos(D, "CX-02")

    # ---------------- vista frontal ----------------
    OX = 56.0
    with B("vista frontal"):
        _vista_frontal(D, OX, 30.0, m["larg"], hh, par, P.TAMPA_ESP,
                       sorted({round(f[0], 3) for f in ins}), dins,
                       m["prof_ins"], sw, P.PAIN_ESP)

    # A coluna cabe ao lado da elevacao. O alivio desce para o lado da vista
    # superior e vai a 4:1, nao 8:1: ampliado 8x, um furo de barril M24 da
    # 202 mm de papel - mais largo que a folha util inteira menos a vista.
    # A 4:1 o rebaixo de 0,50 ainda sai com 2 mm, que e o que o detalhe
    # precisa mostrar - que ele e degrau reto e abre para a face da mesa.
    with B("detalhe da coluna"):
        _detalhe_coluna(D, 312, 44, par, m["col"], m["prof_ins"], dins, hh)

    # ---------------- vista superior ----------------
    B.abre("vista superior")
    W = Vista(OX, 175, m["larg"], m["alt"])
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

    # A chave, na parede de tras. Em PLANTA um furo de eixo HORIZONTAL sao
    # duas linhas ocultas, nao um circulo: desenhar o circulo o faria
    # transbordar 9 mm para fora do contorno da peca.
    for s in (-1, 1):
        D.linha(W.px(sw["x"] + s * sw["d_furo"] / 2), W.py(m["alt"]),
                W.px(sw["x"] + s * sw["d_furo"] / 2),
                W.py(m["alt"] - sw["parede"]), L_TRACO, "#555", dash=D_OCULTA)
        D.linha(W.px(sw["x"] + s * sw["d_rebaixo"] / 2),
                W.py(m["alt"] - sw["parede"]),
                W.px(sw["x"] + s * sw["d_rebaixo"] / 2),
                W.py(m["alt"] - m["par"]), L_TRACO, "#555", dash=D_OCULTA)
    D.centro(*W.p(sw["x"], m["alt"] - m["par"] / 2), sw["d_rebaixo"] / 2 + 3)

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
    D.bandeira(*W.p(xs[0], ys[0] - dins / 2), 6, ang=-135, comp=18)
    D.rotulo_vista(W.px(m["larg"] / 2), yb + 38, "VISTA SUPERIOR", "1:1")
    B.fecha()

    with B("detalhe do alivio"):
        _detalhe_alivio(D, 324, 262, m, S=4.0)

    # ---------------- notas, na faixa de baixo, com a folha inteira -------
    B.abre("notas")
    y = D.notas(COL_DIR, Y_TEXTO, [
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
    ], titulo="NOTAS DE FABRICAÇÃO", larg=LARG_TEXTO)

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
    ], titulo="OBSERVAÇÕES DE PROJETO", larg=LARG_TEXTO)

    itens = ([(f"BARRIL {i}", f[0], f[1], 2 * f[2])
              for i, f in enumerate(m["barril"], 1)]
             + [(f"LED {i}", f[0], f[1], 2 * f[2])
                for i, f in enumerate(m["led"], 1)]
             + [(f"COLUNA {i}", f[0], f[1], dins)
                for i, f in enumerate(ins, 1)])
    tabela_furos(D, COL_DIR, y + 14, itens,
                 "FUROS - origem no canto inferior esquerdo", por_coluna=9)
    B.fecha()

    B.conferir()
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
# 2. Tampa de servico, com o berco do carregador TP4056
# =====================================================================

def _esp_chapa(V, T, zs):
    """
    Espessura da chapa da tampa, medida: a ultima faixa de z em que a secao
    ainda tem a silhueta inteira. Acima dela so existem as colunas do berco,
    e o contorno mais largo passa a ser uma delas.
    """
    for z0, z1 in zip(zs, zs[1:]):
        c, _ = analisar(V, T, (z0 + z1) / 2)
        larg = max(p[0] for p in c[0]) - min(p[0] for p in c[0])
        if larg < P.CX_L / 2:
            return z0
    return zs[-1]


def _prof_rebaixo(V, T, zs, esp):
    """
    Fundo do rebaixo dos parafusos, MEDIDO: a primeira faixa de z em que o
    furo de fixacao muda de raio. Nao da para usar zs[1] - o alivio da janela
    poe um nivel em 0,50 antes do fundo do rebaixo.
    """
    r0 = None
    for z0, z1 in zip(zs, zs[1:]):
        if z1 > esp:
            break
        _, f = analisar(V, T, (z0 + z1) / 2)
        r = max(x[2] for x in f)
        if r0 is None:
            r0 = r
        elif abs(r - r0) > 0.01:
            return z0
    return None


def _caixa(lo):
    xs, ys = [p[0] for p in lo], [p[1] for p in lo]
    return min(xs), min(ys), max(xs), max(ys)


def desenho_tampa():
    V, T = ler_3mf("caixa-tampa.3mf")
    zs = niveis(V)
    e = P.estacao_carregador()
    r = medir_berco(V, T)
    esp = _esp_chapa(V, T, zs)
    hreb = _prof_rebaixo(V, T, zs, esp)
    alt_total = zs[-1]

    # A chapa: corte a meia espessura do rebaixo e a meia espessura da
    # passagem. z = 0 e a face EXTERNA. No segundo corte a janela e o
    # segundo contorno nao circular - o primeiro e a silhueta.
    c_r, f_r = analisar(V, T, hreb / 2)
    c_p, f_p = analisar(V, T, (hreb + esp) / 2)
    lo = c_r[0]
    larg = max(p[0] for p in lo) - min(p[0] for p in lo)
    alt = max(p[1] for p in lo) - min(p[1] for p in lo)
    R = raio_canto(lo)
    rebaixos, passantes = f_r, f_p
    dp, dr = 2 * passantes[0][2], 2 * rebaixos[0][2]
    jx0, jy0, jx1, jy1 = _caixa(c_p[1])
    ax0, ay0, ax1, ay1 = _caixa(analisar(V, T, P.REB_ALIVIO / 2)[0][1])
    xj, yj = (jx0 + jx1) / 2, (jy0 + jy1) / 2
    z_canal = (e["perfil"][0][0] + e["perfil"][0][1]) / 2
    colunas = analisar(V, T, z_canal)[0]
    zb = [z for z in zs if z > esp + 1e-9]          # niveis do berco

    s0, s1 = r["secoes"][0], r["secoes"][1]
    q = lambda l, i, j: l[i] - l[j] if len(l) == 4 else None
    bate("tampa: espessura da chapa", esp, P.TAMPA_ESP)
    bate("tampa: largura", larg, P.CX_L)
    bate("tampa: profundidade", alt, P.CX_A)
    bate("tampa: raio de canto", R, P.CX_R)
    bate("tampa: rebaixo", hreb, P.REB_TAMPA)
    bate("tampa: Ø de passagem", dp, P.D_PASSAGEM)
    bate("tampa: Ø do rebaixo", dr, P.D_REBAIXO)
    bate("tampa: n de furos", len(rebaixos), 6)
    bate("tampa: janela em y", jy1 - jy0, e["janela"][0])
    bate("tampa: janela em x", jx1 - jx0, e["janela"][1])
    bate("tampa: x da janela", xj, e["x_usb"])
    bate("tampa: y da janela", yj, e["yc"])
    bate("tampa: alivio em y", ay1 - ay0, e["alivio"][0])
    bate("tampa: alivio em x", ax1 - ax0, e["alivio"][1])
    bate("tampa: n de colunas do berco", len(colunas), 2)
    bate("berco: canal", q(s0["xs"][0], 2, 1), e["canal_w"])
    bate("berco: vao entre os fundos", q(s0["ys"], 2, 1), 2 * e["w_fundo"])
    bate("berco: largura total", q(s0["ys"], 3, 0), 2 * e["w_fora"])
    bate("berco: boca na garra", q(s1["ys"], 2, 1), 2 * e["w_ponta"])
    bate("berco: face de baixo da garra", zb[0], e["z_garra"])
    bate("berco: face de cima da garra", zb[1], e["z_garra"] + e["garra_h"])
    bate("tampa: altura total", alt_total, e["topo"])

    L = esp - hreb + P.PENETRACAO

    D = Desenho(FOLHA_W, FOLHA_H, "CAIXA - TAMPA DE SERVIÇO",
                "Vista superior, furo de fixação e berço do carregador TP4056",
                escala="1:1 (ver ampliações)", codigo="PIBIC-CX-03")
    B = Blocos(D, "CX-03")

    # As duas ampliacoes empilham na faixa livre a direita da vista superior;
    # o texto fica com a folha inteira embaixo.
    with B("detalhe do furo"):
        _detalhe_furo(D, 334, 110, esp, hreb, dp, dr, L)
    with B("detalhe do berço"):
        _detalhe_berco(D, 334, 360, e, esp)

    # Vista de +z, a FACE INTERNA, como a peca sai da mesa: passagem, janela
    # e berco visiveis; rebaixo e alivio da janela, que ficam na face da
    # mesa, ocultos.
    B.abre("vista superior")
    W = Vista(46, 110, larg, alt)
    contorno(D, lo, W)
    for f in passantes:
        furo(D, W, f)
    for f in rebaixos:
        furo(D, W, f, marca=False, lw=L_TRACO, cor="#555", dash=D_OCULTA)
    contorno(D, c_p[1], W)
    D.ret(W.px(ax0), W.py(ay1), ax1 - ax0, ay1 - ay0, L_TRACO, cor="#555",
          dash=D_OCULTA)
    for lo_c in colunas:
        contorno(D, lo_c, W)
    D.ret(W.px(e["x_mod"][0]), W.py(e["yc"] + e["larg"] / 2),
          e["x_mod"][1] - e["x_mod"][0], e["larg"], L_TRACO, cor=C_REF,
          dash=D_FANTASMA)
    D.txt(W.px(e["x_mod"][0]) - 3, W.py(e["yc"] + e["larg"] / 2) - 2,
          "TP4056 (ref.)", FONTE_P, anc="end", cor=C_REF)

    yb = W.py(0)
    xs = sorted({round(f[0], 3) for f in rebaixos})
    ys = sorted({round(f[1], 3) for f in rebaixos})
    D.cota_h(W.px(0), W.px(xs[0]), yb + 14, vg(xs[0]), yb)
    D.cota_h(W.px(0), W.px(xj), yb + 26, vg(xj), yb)
    D.cota_h(W.px(0), W.px(larg), yb + 38, vg(larg), yb)
    D.cota_v(W.py(alt), yb, W.px(0) - 14, vg(alt), W.px(0))
    D.cota_v(W.py(yj), yb, W.px(larg) + 14, vg(yj), W.px(larg))
    D.bandeira(*W.p(xs[2], ys[2] + dr / 2), 1, ang=-45, comp=18)
    D.bandeira(W.px(larg - R * 0.293), W.py(alt - R * 0.293), 2, ang=-30,
               comp=18)
    D.bandeira(*W.p(xs[0], ys[0] - dr / 2), 4, ang=-135, comp=18)
    D.bandeira(*W.p(jx0, yj), 5, ang=-160, comp=22)
    D.bandeira(*W.p(e["x"], e["yc"] + e["w_fora"]), 6, ang=-120, comp=20)
    D.rotulo_vista(W.px(larg / 2), yb + 50,
                   "VISTA SUPERIOR - face interna, como sai da mesa", "1:1")
    B.fecha()

    B.abre("notas")
    y = D.notas(COL_DIR, Y_TEXTO, [
        (1, f"{len(rebaixos)}x {dm(dp)} passante com rebaixo {dm(dr)} x "
            f"{vg(hreb)} para a cabeça do parafuso M3 ISO 7380. O rebaixo "
            f"fica na face da mesa - oculto nesta vista."),
        (2, f"Silhueta idêntica à do corpo: {vg(larg)} x {vg(alt)}, cantos "
            f"R{vg(R)}."),
        (3, f"Chapa {vg(esp)}; sob a cabeça do parafuso restam "
            f"{vg(esp - hreb)} mm - é a seção mais fina da peça."),
        (4, f"Fixação com {len(rebaixos)}x M3 x {L:.0f} ISO 7380 em inserto de "
            f"latão M3 no topo das colunas do corpo (ver PIBIC-CX-02)."),
        (5, f"Janela do plugue USB-C {vg(jy1 - jy0)} x {vg(jx1 - jx0)} "
            f"passante, centro em x = {vg(xj)}, y = {vg(yj)}, com alívio de "
            f"boca {vg(ay1 - ay0)} x {vg(ax1 - ax0)} x {vg(P.REB_ALIVIO)} na "
            f"face da mesa."),
        (None, "MONTE COM A JANELA DO LADO DO BOTÃO VERDE. Girada 180°, a "
               "tampa ainda parafusa, mas o módulo bate no botão vermelho."),
        (6, f"Berço do TP4056: 2 colunas em U, canal {vg(e['canal_w'])} x "
            f"{vg(e['prof_canal'])}; a garra cobre {vg(e['cobre'])} da borda "
            f"de cima da placa, com {vg(e['folga'])} de folga."),
        (None, f"Entrada em {len(e['degraus'])} degraus retos de "
               f"{vg(e['degraus'][0][1])}, sem rampa. Altura total da peça "
               f"{vg(alt_total)}."),
        (7, f"Imprimir com a face externa NA MESA e o berço para cima. O "
            f"rebaixo dos parafusos ({vg((dr - dp) / 2)} radial sobre "
            f"{vg(dr)}) e o alívio da janela não pedem suporte."),
    ], titulo="NOTAS DE FABRICAÇÃO", larg=LARG_TEXTO)

    y = D.notas(COL_DIR, y + 4, [
        (None, f"As cotas do TP4056 são PRESUMIDAS: placa {vg(e['comp'])} x "
               f"{vg(e['larg'])} x {vg(e['esp'])}, USB-C {vg(e['usb_l'])} x "
               f"{vg(e['usb_h'])}. Meça antes de imprimir."),
        (None, "O comprimento da placa decide a folga sob a garra; a largura, "
               "a folga do canal."),
        (None, f"Para encaixar, cada coluna flete {vg(e['prof_canal'])} mm - "
               f"deformação de {e['eps'] * 100:.2f} %, abaixo do limite de "
               f"1,00 % adotado para o PLA."),
        (None, "A garra pode encostar nas ilhas de solda dos cantos da placa. "
               "Se atrapalhar, apare com estilete - não precisa reimprimir."),
        (None, "Com a caixa fechada os LEDs de carga não ficam visíveis. "
               "Carregue com a caixa deitada de lado: não há pés."),
        (None, "A tampa não fixa mais a perfboard - os 4 pinos saíram nesta "
               "revisão."),
    ], titulo="OBSERVAÇÕES DE PROJETO", larg=LARG_TEXTO)

    itens = (rotulos("FIX ", rebaixos)
             + [("JANELA", xj, yj, f"{vg(jy1 - jy0)} x {vg(jx1 - jx0)}")])
    tabela_furos(D, COL_DIR, y + 14, itens,
                 "COORDENADAS - origem no canto inferior esquerdo",
                 por_coluna=4)
    B.fecha()

    B.conferir()
    D.salvar("desenho-caixa-tampa.svg")


def _detalhe_berco(D, ox, oy, e, esp, S=4.0):
    """
    O berco em corte, no plano medio da placa (x = e['x']), ampliado.

    O plano passa pelo meio do canal, entao a coluna aparece do fundo do
    canal ate a face de fora - e na garra, da boca fechada. Chapa e coluna
    saem num poligono so por lado: separados, uma linha de contorno
    atravessaria material continuo.

    A placa entra em linha de referencia: as cotas dela sao PRESUMIDAS, nao
    medidas. Os degraus de 0,40 somem a 4:1 (1,6 mm de papel) e vao para a
    nota em vez de cota.
    """
    wp, wf = e["w_ponta"], e["w_fora"]
    jh, ah, ra = e["janela"][0] / 2, e["alivio"][0] / 2, P.REB_ALIVIO
    ctx = 15.0                          # quanto de chapa aparece de cada lado

    def X(sg, w):
        return ox + sg * w * S

    def Y(z):
        return oy - z * S

    for sg in (-1, 1):
        pts = [(jh, esp), (wp + e["perfil"][0][2], esp)]
        for z0, z1, g in e["perfil"]:
            pts += [(wp + g, z0), (wp + g, z1)]
        pts += [(wf, e["topo"]), (wf, esp), (ctx, esp), (ctx, 0.0),
                (ah, 0.0), (ah, ra), (jh, ra)]
        D.hachura_poli([(X(sg, w), Y(z)) for w, z in pts])

    D.ret(ox - e["larg"] / 2 * S, Y(esp + e["comp"]), e["larg"] * S,
          e["comp"] * S, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox, Y(esp + e["comp"] / 2), "placa TP4056", FONTE_P, cor=C_REF)
    D.txt(ox, Y(esp + e["comp"] / 2) + 4, "(ref., PRESUMIDA)", FONTE_P,
          cor=C_REF)

    wg = wp + e["prof_canal"]
    D.cota_h(X(-1, wg), X(1, wg), Y(12.0), vg(2 * wg), tam=FONTE_P)
    D.cota_h(X(-1, wf), X(1, wf), Y(e["topo"]) - 10, vg(2 * wf),
             Y(e["topo"]), tam=FONTE_P)
    D.cota_h(X(-1, jh), X(1, jh), oy + 10, vg(2 * jh), oy, tam=FONTE_P)
    D.cota_h(X(-1, ah), X(1, ah), oy + 20, vg(2 * ah), oy, tam=FONTE_P)
    xd = X(1, wf)
    D.cota_v(Y(e["z_garra"]), Y(esp), xd + 10, vg(e["z_garra"] - esp), xd,
             tam=FONTE_P)
    D.cota_v(Y(e["topo"]), Y(0.0), xd + 22, vg(e["topo"]), X(1, ctx),
             tam=FONTE_P)
    D.cota_v(Y(esp + e["comp"]), Y(esp), X(-1, wf) - 12, vg(e["comp"]),
             X(-1, e["larg"] / 2), tam=FONTE_P)
    D.bandeira(X(1, wp), Y(e["z_garra"] + e["garra_h"] / 2), 6, ang=-150,
               comp=16)
    D.rotulo_vista(ox, oy + 32,
                   f"CORTE - berço no plano da placa (x = {vg(e['x'])})",
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

    B = Blocos(D, "CX-04")

    # Elevacao (120 mm) e corte (224 mm) cabem lado a lado na largura util do
    # retrato; o texto fica com a folha inteira embaixo.
    with B("elevação"):
        _chave_elevacao(D, 78, 105, sw, m)
    with B("corte A-A"):
        _chave_corte(D, 282, 258, sw, C)

    B.abre("notas")
    y = D.notas(COL_DIR, Y_TEXTO, [
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
    ], titulo="NOTAS DE FABRICAÇÃO", larg=LARG_TEXTO)

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
    ], titulo="MONTAGEM", larg=LARG_TEXTO)

    cab = ("COTA", "VALOR [mm]", "ORIGEM")
    linhas = [
        ("corpo no painel", dm(C["d_corpo"]) + " ± 0,20", "fabricante"),
        ("aro visível", dm(C["d_aro"]) + " ± 0,20", "fabricante"),
        ("corpo atrás", dm(C["d_corpo_tras"]), "fabricante"),
        ("profundidade do corpo", vg(C["prof_corpo"]) + " ± 0,30", "fabricante"),
        ("total atrás do painel", vg(C["atras"]) + " ± 0,30", "fabricante"),
        ("terminais", f"{C['n_term']}, passo {vg(C['passo_term'])}, "
         f"vão {vg(C['vao_term'])}", "fabricante"),
        ("lâmina faston", f"{vg(C['lamina'])} x {vg(C['esp_lamina'])}",
         "fabricante"),
        ("furo do painel", dm(sw["d_furo"]), "medido na malha"),
        ("rebaixo", dm(sw["d_rebaixo"]) + " x " + vg(sw["prof_reb"]),
         "medido na malha"),
        ("parede local", vg(sw["parede"]), "medido na malha"),
    ]
    D.txt(COL_DIR, y + 12, "COTAS DO COMPONENTE E DA ESTAÇÃO", 2.8,
          anc="start", peso="bold", cor=C_TXT)
    D.tabela(COL_DIR, y + 14, cab, linhas, (60, 60, 60))
    B.fecha()

    B.conferir()
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
    da, dc = C["d_aro"] / 2 * S, C["d_corpo_tras"] / 2 * S
    pc, vt = C["prof_corpo"], C["vao_term"]
    D.ret(ox - da, y_face, 2 * da, C["saliencia_aro"] * S, L_TRACO, cor=C_REF,
          dash=D_FANTASMA)
    D.ret(ox - dc, y_reb - pc * S, 2 * dc, pc * S, L_TRACO, cor=C_REF,
          dash=D_FANTASMA)
    D.ret(ox - vt / 2 * S, y_reb - C["atras"] * S, vt * S,
          (C["atras"] - pc) * S, L_TRACO, cor=C_REF, dash=D_FANTASMA)
    D.txt(ox + dc + 6, y_reb - pc * S / 2, "corpo da chave (ref.)", FONTE_P,
          anc="start", cor=C_REF)
    D.txt(ox + vt / 2 * S + 6, y_reb - (C["atras"] + pc) / 2 * S,
          f"terminais faston {vg(C['lamina'])} (ref.)", FONTE_P, anc="start", cor=C_REF)
    D.txt(ox, y_face + C["saliencia_aro"] * S + 8, "FORA", FONTE_P, cor=C_TXT)
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
