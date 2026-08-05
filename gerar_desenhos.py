#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desenhos tecnicos em SVG - PIBIC UniCEUB.
Autor: Rafael Alves de Sousa Costa.

Gera quatro pranchas cotadas a partir das MESMAS constantes usadas em
gerar_stl.py, de modo que desenho e modelo nao possam divergir:

  desenho-tampa.svg               tampa: distancias entre botoes, diametros
  desenho-gabarito-passante.svg   gabarito de furo liso
  desenho-gabarito-roscado.svg    gabarito de rosca interna
  desenho-perfil-rosca.svg        perfil ISO 68-1 da M24 x 2, ampliado 18x

Unidades em milimetros; 1 unidade SVG = 1 mm. Abra em qualquer navegador.

Uso:  python gerar_desenhos.py
"""

import datetime
import math

import gerar_stl as G

# espessuras de linha (mm), conforme uso tecnico
L_CONTORNO = 0.45
L_FINA     = 0.16
L_TRACO    = 0.20
FONTE      = 3.0
FONTE_P    = 2.4

# tracejados normalizados
D_OCULTA   = "3,1.5"              # linha tracejada  - aresta invisivel
D_CENTRO   = "4,1.2,0.6,1.2"      # traco-ponto      - linha de centro/eixo
D_FANTASMA = "7,1.5,1,1.5,1,1.5"  # traco-ponto-ponto - contorno de referencia

# identificacao unica de todas as pranchas (legenda)
MARGEM  = 8.0
PROJETO = "PIBIC UniCEUB"
AUTOR   = "Rafael Alves de Sousa Costa"
DATA    = datetime.date.today().strftime("%d/%m/%Y")

# cores
C_COTA = "#1a5276"
C_REF  = "#7f8c8d"
C_TXT  = "#333"
C_ATEN = "#c0392b"


class Desenho:
    """Prancha SVG simples com cotas, linhas de centro e hachura."""

    def __init__(self, larg, alt, titulo, subtitulo="", material="PETG",
                 escala="1:1", codigo="", folha="1/1"):
        self.w, self.h = larg, alt
        self.el = []
        self.titulo, self.subtitulo = titulo, subtitulo
        self.material, self.escala = material, escala
        self.codigo, self.folha = codigo, folha

    # ---------- primitivas ----------

    def linha(self, x1, y1, x2, y2, w=L_CONTORNO, cor="#111", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.el.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
                       f'stroke="{cor}" stroke-width="{w}"{d}/>')

    def ret(self, x, y, w, h, lw=L_CONTORNO, fill="none", cor="#111", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.el.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
                       f'fill="{fill}" stroke="{cor}" stroke-width="{lw}"{d}/>')

    def circ(self, cx, cy, r, lw=L_CONTORNO, fill="none", cor="#111", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.el.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{fill}" '
                       f'stroke="{cor}" stroke-width="{lw}"{d}/>')

    def poli(self, pts, lw=L_CONTORNO, fill="none", cor="#111", fechar=False):
        s = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        tag = "polygon" if fechar else "polyline"
        self.el.append(f'<{tag} points="{s}" fill="{fill}" stroke="{cor}" stroke-width="{lw}"/>')

    def txt(self, x, y, s, tam=FONTE, anc="middle", cor="#111", ang=0, peso="normal"):
        t = f' transform="rotate({ang} {x:.3f} {y:.3f})"' if ang else ""
        self.el.append(f'<text x="{x:.3f}" y="{y:.3f}" font-family="DejaVu Sans, Arial, '
                       f'sans-serif" font-size="{tam}" font-weight="{peso}" fill="{cor}" '
                       f'text-anchor="{anc}"{t}>{s}</text>')

    def centro(self, cx, cy, r):
        """Linha de centro traco-ponto."""
        e = r + 3
        for x1, y1, x2, y2 in ((cx - e, cy, cx + e, cy), (cx, cy - e, cx, cy + e)):
            self.linha(x1, y1, x2, y2, L_TRACO, "#c0392b", dash="4,1.2,0.6,1.2")

    def seta(self, x, y, ang, L=2.4, W=0.9):
        dx, dy = math.cos(ang), math.sin(ang)
        px, py = -dy, dx
        p1 = (x - L * dx + W / 2 * px, y - L * dy + W / 2 * py)
        p2 = (x - L * dx - W / 2 * px, y - L * dy - W / 2 * py)
        self.el.append(f'<polygon points="{x:.3f},{y:.3f} {p1[0]:.3f},{p1[1]:.3f} '
                       f'{p2[0]:.3f},{p2[1]:.3f}" fill="#111"/>')

    # ---------- cotas ----------

    def cota_h(self, x1, x2, y, txt, ext_de=None, tam=FONTE):
        """Cota horizontal entre x1 e x2 na altura y."""
        if ext_de is not None:
            for x in (x1, x2):
                self.linha(x, ext_de, x, y + (2 if y > ext_de else -2), L_FINA, "#1a5276")
        self.linha(x1, y, x2, y, L_FINA, "#1a5276")
        if abs(x2 - x1) > 10:
            self.seta(x1, y, math.pi); self.seta(x2, y, 0)
        else:
            self.seta(x1, y, 0, L=-2.4); self.seta(x2, y, math.pi, L=-2.4)
        self.txt((x1 + x2) / 2, y - 1.4, txt, tam, cor="#1a5276")

    def cota_v(self, y1, y2, x, txt, ext_de=None, tam=FONTE):
        if ext_de is not None:
            for y in (y1, y2):
                self.linha(ext_de, y, x + (2 if x > ext_de else -2), y, L_FINA, "#1a5276")
        self.linha(x, y1, x, y2, L_FINA, "#1a5276")
        self.seta(x, y1, -math.pi / 2); self.seta(x, y2, math.pi / 2)
        self.txt(x - 1.6, (y1 + y2) / 2, txt, tam, anc="middle", cor="#1a5276", ang=-90)

    def chamada(self, cx, cy, r, txt, ang=-45, comp=16, tam=FONTE):
        """Linha de chamada saindo do circulo para um rotulo."""
        a = math.radians(ang)
        x1, y1 = cx + r * math.cos(a), cy + r * math.sin(a)
        x2, y2 = cx + (r + comp) * math.cos(a), cy + (r + comp) * math.sin(a)
        x3 = x2 + (7 if math.cos(a) >= 0 else -7)
        self.linha(x1, y1, x2, y2, L_FINA, "#1a5276")
        self.linha(x2, y2, x3, y2, L_FINA, "#1a5276")
        self.seta(x1, y1, a + math.pi)
        self.txt(x3 + (1 if math.cos(a) >= 0 else -1), y2 - 1.2, txt, tam,
                 anc="start" if math.cos(a) >= 0 else "end", cor="#1a5276")

    def hachura(self, x, y, w, h, passo=2.0):
        cid = f"h{len(self.el)}"
        self.el.append(
            f'<defs><pattern id="{cid}" width="{passo}" height="{passo}" '
            f'patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
            f'<line x1="0" y1="0" x2="0" y2="{passo}" stroke="#111" stroke-width="0.18"/>'
            f'</pattern></defs>'
            f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
            f'fill="url(#{cid})" stroke="#111" stroke-width="{L_CONTORNO}"/>')

    def hachura_poli(self, pts, passo=2.0):
        """Como hachura(), mas sobre um poligono qualquer (perfis escalonados)."""
        cid = f"hp{len(self.el)}"
        s = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        self.el.append(
            f'<defs><pattern id="{cid}" width="{passo}" height="{passo}" '
            f'patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
            f'<line x1="0" y1="0" x2="0" y2="{passo}" stroke="#111" stroke-width="0.18"/>'
            f'</pattern></defs>'
            f'<polygon points="{s}" fill="url(#{cid})" stroke="#111" '
            f'stroke-width="{L_CONTORNO}"/>')

    def nota(self, x, y, linhas, tam=FONTE_P):
        for i, s in enumerate(linhas):
            self.txt(x, y + i * (tam + 1.1), s, tam, anc="start", cor="#555")

    # ---------- rotulos, notas indexadas e tabelas ----------

    def rotulo_vista(self, x, y, nome, escala=None):
        """Titulo de vista, centrado em x e sublinhado."""
        s = nome if escala is None else f"{nome}    escala {escala}"
        self.txt(x, y, s, 3.2, peso="bold", cor=C_TXT)
        w = len(s) * 0.95
        self.linha(x - w, y + 1.5, x + w, y + 1.5, 0.25, C_TXT)

    def bandeira(self, x, y, n, ang=-45, comp=14, r=2.4):
        """Chamada numerada: seta na feature, numero no fim da linha."""
        a = math.radians(ang)
        x2, y2 = x + comp * math.cos(a), y + comp * math.sin(a)
        self.linha(x, y, x2, y2, L_FINA, C_COTA)
        self.seta(x, y, a + math.pi)
        self.circ(x2, y2, r, L_FINA, fill="#fff", cor=C_COTA)
        self.txt(x2, y2 + 0.9, str(n), 2.6, cor=C_COTA)

    def notas(self, x, y, itens, titulo="NOTAS", larg=0.0, tam=FONTE_P,
              passo=4.6):
        """
        Bloco de notas indexadas. 'itens' e uma lista de (n, texto); n=None
        continua a nota anterior (linha sem numero, alinhada com o texto).
        Devolve o y logo abaixo do bloco.
        """
        self.txt(x, y, titulo, 2.8, anc="start", peso="bold", cor=C_TXT)
        self.linha(x, y + 1.5, x + (larg or 60), y + 1.5, 0.25, C_TXT)
        yy = y + 7.0
        for n, s in itens:
            if n is not None:
                self.circ(x + 2.4, yy - 0.9, 2.4, L_FINA, fill="#fff", cor=C_COTA)
                self.txt(x + 2.4, yy, str(n), 2.4, cor=C_COTA)
            self.txt(x + 7.2, yy, s, tam, anc="start", cor=C_TXT)
            yy += passo
        return yy

    def tabela(self, x, y, cols, linhas, larguras, titulo=None, tam=FONTE_P):
        """Tabela com grade; devolve o y logo abaixo."""
        h = 5.6
        if titulo:
            self.txt(x, y - 2.4, titulo, 2.8, anc="start", peso="bold", cor=C_TXT)
        yy = y
        for i, linha in enumerate([cols] + list(linhas)):
            xx = x
            for v, w in zip(linha, larguras):
                self.ret(xx, yy, w, h, L_FINA, cor="#888")
                self.txt(xx + w / 2, yy + h - 1.8, str(v),
                         2.3 if i == 0 else tam,
                         peso="bold" if i == 0 else "normal", cor=C_TXT)
                xx += w
            yy += h
        return yy

    # ---------- legenda (selo) ----------

    def _cel(self, x, y, w, h, rot, val, tam=2.8, peso="normal", cor="#111"):
        self.ret(x, y, w, h, L_FINA, cor="#888")
        if rot:
            self.txt(x + 1.8, y + 3.2, rot, 1.9, anc="start", cor="#777")
        if val:
            self.txt(x + 1.8, y + h - 2.4, val, tam, anc="start", peso=peso, cor=cor)

    def simbolo_diedro(self, x, y, s=2.6):
        """
        Simbolo ISO de projecao no 1o diedro: o tronco de cone visto de lado
        (extremidade menor a esquerda) e, a DIREITA, a vista pela esquerda -
        os dois circulos concentricos.
        """
        d1, d2, L = s, 2 * s, 2.6 * s
        self.poli([(x, y - d1 / 2), (x + L, y - d2 / 2),
                   (x + L, y + d2 / 2), (x, y + d1 / 2)], L_TRACO, fechar=True)
        cx = x + L + 1.4 * s + d2 / 2
        self.circ(cx, y, d2 / 2, L_TRACO)
        self.circ(cx, y, d1 / 2, L_TRACO)
        self.linha(x - 0.8 * s, y, cx + d2 / 2 + 0.8 * s, y, L_FINA, "#111",
                   dash=D_CENTRO)

    def selo(self):
        """Moldura da prancha e legenda normalizada."""
        m, W, H = MARGEM, self.w - 2 * MARGEM, 28.0
        y0 = self.h - m - H
        self.ret(m, m, W, self.h - 2 * m, 0.35)
        self.ret(m, y0, W, H, 0.35)

        w1, w2 = round(W * 0.44, 2), round(W * 0.30, 2)
        w3 = W - w1 - w2
        x1, x2, x3 = m, m + w1, m + w1 + w2

        # coluna 1 - identificacao da peca
        self.ret(x1, y0, w1, 17.0, L_FINA, cor="#888")
        self.txt(x1 + 2.6, y0 + 3.4, "PEÇA", 1.9, anc="start", cor="#777")
        self.txt(x1 + 2.6, y0 + 10.2, self.titulo, 5.0, anc="start", peso="bold")
        self.txt(x1 + 2.6, y0 + 14.8, self.subtitulo, FONTE_P, anc="start",
                 cor="#555")
        for i, (rot, val) in enumerate((("MATERIAL", self.material),
                                        ("ESCALA", self.escala),
                                        ("COTAS", "milímetros"))):
            self._cel(x1 + i * w1 / 3, y0 + 17.0, w1 / 3, 11.0, rot, val)

        # coluna 2 - projeto e autoria
        for i, (rot, val) in enumerate((("PROJETO", PROJETO),
                                        ("AUTOR", AUTOR),
                                        ("DATA", DATA))):
            self._cel(x2, y0 + i * H / 3, w2, H / 3, rot, val, tam=2.7)

        # coluna 3 - identificacao do desenho
        self._cel(x3, y0, w3, 10.0, "DESENHO Nº", self.codigo, tam=3.0,
                  peso="bold")
        self._cel(x3, y0 + 10.0, w3, 8.0, "FOLHA", self.folha, tam=2.7)
        self._cel(x3, y0 + 18.0, w3, 10.0, "PROJEÇÃO", "1º diedro", tam=2.7)
        self.simbolo_diedro(x3 + w3 - 25.0, y0 + 24.0)

    def salvar(self, caminho):
        self.selo()
        corpo = "\n".join(self.el)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" '
               f'height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">\n'
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>\n{corpo}\n</svg>\n')
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"  {caminho}")


# =====================================================================
# 1. Tampa
# =====================================================================

def _detalhe_rebaixo(D, ox, oy, esp):
    """
    Detalhe ampliado 6:1 do furo de fixacao M3: corte pelo eixo, mostrando
    rebaixo, furo de passagem e a cabeca ISO 7380 embutida.
    """
    S = 6.0
    rr = G.PARAF_D_REBAIXO / 2 * S
    rp = G.PARAF_D_PASSAGEM / 2 * S
    hr = G.PARAF_H_REBAIXO * S
    ht = esp * S
    sob = ht - hr                      # material sob a cabeca
    W = 62.0                           # meia largura do trecho mostrado

    for sg in (-1, 1):
        D.hachura_poli([(ox + sg * W, oy), (ox + sg * rr, oy),
                        (ox + sg * rr, oy + hr), (ox + sg * rp, oy + hr),
                        (ox + sg * rp, oy + ht), (ox + sg * W, oy + ht)])

    # Cabeca abaulada ISO 7380 (dk 5,7 / k 1,65) alojada no rebaixo.
    # O ponto de controle vai a oy-k para que o APICE da quadratica caia
    # exatamente em oy: (P0 + 2C + P2)/4 = oy. Assim a cabeca fica rente a
    # superficie, que e o objetivo do rebaixo.
    dk, k = 5.7 * S / 2, 1.65 * S
    D.el.append(f'<path d="M {ox-dk:.2f} {oy+k:.2f} Q {ox:.2f} {oy-k:.2f} '
                f'{ox+dk:.2f} {oy+k:.2f} Z" fill="none" stroke="#7f8c8d" '
                f'stroke-width="{L_TRACO}" stroke-dasharray="3,1.5"/>')
    for sg in (-1, 1):
        D.linha(ox + sg * 1.5 * S, oy + k, ox + sg * 1.5 * S, oy + ht + 8,
                L_TRACO, "#7f8c8d", dash="3,1.5")
    D.txt(ox + rr + 8, oy - 2, "M3 x 10 ISO 7380 (ref.)", FONTE_P,
          anc="start", cor="#7f8c8d")
    D.linha(ox + rr + 7, oy - 3, ox + dk * 0.6, oy + k * 0.45, L_FINA, "#7f8c8d")

    D.cota_h(ox - rr, ox + rr, oy - 9, "&#216;6,50", oy, tam=FONTE_P)
    D.cota_h(ox - rp, ox + rp, oy + ht + 13, "&#216;3,40", oy + ht, tam=FONTE_P)
    D.cota_v(oy, oy + hr, ox - W - 9, "2,00", ox - W, tam=FONTE_P)
    D.cota_v(oy + hr, oy + ht, ox - W - 9, "2,00", ox - W, tam=FONTE_P)
    D.cota_v(oy, oy + ht, ox - W - 24, "4,00", ox - W, tam=FONTE_P)

    D.txt(ox + W + 4, oy + hr + sob / 2 + 1,
          "2,00 sob a cabeca - secao mais fina da tampa",
          FONTE_P, anc="start", cor="#c0392b")
    D.linha(ox + rp + 5, oy + hr + sob / 2, ox + W + 3, oy + hr + sob / 2,
            L_FINA, "#c0392b")
    D.seta(ox + rp + 5, oy + hr + sob / 2, math.pi, L=2.0, W=0.8)
    D.txt(ox, oy + ht + 24, "DETALHE B - furo de fixacao (6x)   ampliacao 6:1",
          FONTE_P, cor="#555")


def desenho_tampa():
    esp, d = 4.0, 24.7
    BV, BG = 98.5, 60.8
    folga_borda, margem = 40.0, 5.0
    dist = BV / 2 + BG / 2 + folga_borda
    larg = BV / 2 + dist + BG / 2 + 2 * margem
    alt = BV + 2 * margem
    cxv, cxg, cy = margem + BV / 2, margem + BV / 2 + dist, alt / 2

    rec = G.PARAF_RECUO
    xs_p = [rec, larg / 2, larg - rec]
    ys_p = [rec, alt - rec]

    OX, OY = 48, 52
    D = Desenho(larg + 110, alt + 296, "TAMPA COM ENCAIXE PARA BOTÕES DE ARCADE",
                "Vista superior, corte A-A e detalhe do rebaixo",
                escala="1:1 (ver ampliações)", codigo="PIBIC-TP-01")

    D.ret(OX, OY, larg, alt)

    # --- 6 furos de fixacao M3 ---
    for yp in ys_p:
        for xp in xs_p:
            D.circ(OX + xp, OY + yp, G.PARAF_D_REBAIXO / 2)
            D.circ(OX + xp, OY + yp, G.PARAF_D_PASSAGEM / 2, L_TRACO,
                   cor="#555", dash="2,1")
            D.centro(OX + xp, OY + yp, G.PARAF_D_REBAIXO / 2)
    for cx, cap, nome in ((cxv, BV, "VERMELHO"), (cxg, BG, "VERDE")):
        D.circ(OX + cx, OY + cy, cap / 2, L_TRACO, cor="#7f8c8d", dash="5,2")
        D.circ(OX + cx, OY + cy, d / 2)
        # marca de centro no FURO (nao na capa), senao a linha de centro
        # atravessa os rotulos colocados dentro do circulo da capa
        D.centro(OX + cx, OY + cy, d / 2)
        D.txt(OX + cx, OY + cy + cap / 2 - 8, nome, FONTE_P, cor="#7f8c8d")
        D.txt(OX + cx, OY + cy + cap / 2 - 4,
              f"&#216;{cap:.1f} capa (ref.)".replace(".", ","),
              FONTE_P, cor="#7f8c8d")

    # cotas horizontais, em tres niveis
    D.cota_h(OX + cxv, OX + cxg, OY - 12, "119,65  entre centros", OY + cy)
    D.cota_h(OX + cxv + BV / 2, OX + cxg - BG / 2, OY - 24, "40,00  folga livre",
             OY + cy - 8)
    D.cota_h(OX, OX + larg, OY + alt + 34, "209,30", OY + alt)
    D.cota_h(OX, OX + cxv, OY + alt + 22, "54,25", OY + alt)
    D.cota_h(OX, OX + cxg, OY + alt + 12, "173,90", OY + alt)
    D.cota_v(OY, OY + cy, OX - 12, "54,25", OX)
    D.cota_v(OY, OY + alt, OX - 24, "108,50", OX)

    # cotas dos parafusos: recuo de 8,00 nos dois eixos e a coluna do meio.
    # Ficam em niveis proprios (-36 e OX-36) para nao cruzarem as cotas dos
    # botoes, que ocupam -12 e -24.
    D.cota_h(OX, OX + xs_p[0], OY - 12, "8,00", OY)
    D.cota_h(OX, OX + xs_p[1], OY - 36, "104,65", OY)
    D.cota_v(OY, OY + ys_p[0], OX - 36, "8,00", OX)

    # linhas de chamada, apontadas para fora da placa
    D.chamada(OX + cxg, OY + cy, d / 2, "2x &#216;24,70  (furo de passagem M24)",
              ang=35, comp=30, tam=FONTE_P)
    # sai do parafuso superior direito para a area livre acima e a direita;
    # do de baixo a chamada cairia em cima da cota 173,90
    D.chamada(OX + xs_p[2], OY + ys_p[0], G.PARAF_D_REBAIXO / 2,
              "6x &#216;3,40 + rebaixo &#216;6,50 x 2,00",
              ang=-35, comp=22, tam=FONTE_P)

    # corte lateral
    ys = OY + alt + 52
    D.hachura(OX, ys, larg, esp * 4)
    for cx in (cxv, cxg):
        D.ret(OX + cx - d / 2, ys, d, esp * 4, L_CONTORNO, fill="#fff")
    D.cota_v(ys, ys + esp * 4, OX - 12, "4,00", OX)
    D.txt(OX + larg / 2, ys + esp * 4 + 8,
          "CORTE A-A pelos eixos dos botoes   (escala vertical 4:1)",
          FONTE_P, cor="#555")

    _detalhe_rebaixo(D, D.w / 2, ys + esp * 4 + 44, esp)

    D.nota(OX, ys + esp * 4 + 100, [
        "Centro-a-centro dos botoes = 98,5/2 + 60,8/2 + 40,00 = 119,65 mm",
        "Furo &#216;24,70 = M24 nominal + 0,70 de compensacao PETG (validar no gabarito)",
        "Botao preso por porca; a tampa nao e roscada.",
        "",
        "FIXACAO - 6x M3 x 10 ISO 7380 em inserto de latao M3 (&#216;ext 4,6 x 5,0):",
        "  centros (x ; y):  (8,00 ; 8,00)   (104,65 ; 8,00)   (201,30 ; 8,00)",
        "                    (8,00 ; 100,50) (104,65 ; 100,50) (201,30 ; 100,50)",
        "  furo do inserto na caixa: &#216;4,20 x 9,00 de profundidade, pilar &#216;ext 10,00",
        "  9,00 = L_parafuso 10,00 &#8722; (esp 4,00 &#8722; rebaixo 2,00) + 1,00 de folga no fundo",
    ])
    D.salvar("desenho-tampa.svg")


# =====================================================================
# 2 e 3. Gabaritos
# =====================================================================

def _desenho_gabarito(nome_arq, titulo, sub, rotulos, raios, chamada_txt, notas,
                      codigo=""):
    larg, alt, esp = G.LARG_GAB, G.ALT_GAB, G.ESP_GABARITO
    xs = G._centros_gabarito(len(rotulos))
    ch = G.CHANFRO
    OX, OY = 40, 42

    D = Desenho(larg + 110, alt + 196, titulo, sub,
                escala="1:1 (corte 3:1 na vertical)", codigo=codigo)

    D.poli([(OX + ch, OY), (OX + larg, OY), (OX + larg, OY + alt),
            (OX, OY + alt), (OX, OY + ch)], fechar=True)
    for x, r, (rot, sub2) in zip(xs, raios, rotulos):
        D.circ(OX + x, OY + alt / 2, r)
        D.centro(OX + x, OY + alt / 2, r)
        D.txt(OX + x, OY + alt + 7, rot, FONTE, peso="bold", cor="#c0392b")
        D.txt(OX + x, OY + alt + 11.5, sub2, FONTE_P, cor="#555")

    D.cota_h(OX + xs[0], OX + xs[1], OY - 10, "29,00", OY + alt / 2)
    D.cota_h(OX, OX + larg, OY + alt + 30, f"{larg:.0f},00", OY + alt)
    # extensao comeca ABAIXO dos rotulos, senao a linha corta o texto do 1o furo
    D.cota_h(OX, OX + xs[0], OY + alt + 20, f"{xs[0]:.0f},00", OY + alt + 14)
    D.cota_v(OY, OY + alt, OX - 12, f"{alt:.0f},00", OX)
    # rotulo do chanfro fora da placa, a esquerda, sem pisar no primeiro furo
    D.txt(OX + ch - 1, OY - 3, "chanfro 8x8", FONTE_P, anc="end", cor="#555")
    D.chamada(OX + xs[-1], OY + alt / 2, raios[-1], chamada_txt,
              ang=-55, comp=20, tam=FONTE_P)

    ys = OY + alt + 44
    D.hachura(OX, ys, larg, esp * 3)
    for x, r in zip(xs, raios):
        D.ret(OX + x - r, ys, 2 * r, esp * 3, L_CONTORNO, fill="#fff")
    D.cota_v(ys, ys + esp * 3, OX - 12, f"{esp:.0f},00", OX)
    D.txt(OX + larg / 2, ys + esp * 3 + 8, "CORTE   (escala vertical 3:1)",
          FONTE_P, cor="#555")
    D.nota(OX, ys + esp * 3 + 16, notas)
    D.salvar(nome_arq)


def desenho_gabarito_passante():
    _desenho_gabarito(
        "desenho-gabarito-passante.svg",
        "GABARITO DE TOLERÂNCIA - FURO PASSANTE",
        "5 diâmetros de folga | espessura 8 mm",
        [(f"&#216;{d:.2f}".replace(".", ","), f"+{d-24:.2f}".replace(".", ","))
         for d in G.DIAM_PASSANTE],
        [d / 2 for d in G.DIAM_PASSANTE],
        "furos passantes, sem rosca",
        ["Testa o furo de passagem: o barril M24 do botao atravessa e a porca aperta.",
         "Escolher o menor furo em que o botao entra com leve pressao dos dedos.",
         "Profundidade 8 mm reproduz o atrito real e revela conicidade do furo.",
         "O chanfro 8x8 identifica o canto do MENOR furo (&#216;24,40)."],
        codigo="PIBIC-GB-01")


def desenho_gabarito_roscado():
    r = [G.RoscaISO(24.0, 2.0, dl) for dl in G.DELTA_ROSCA]
    _desenho_gabarito(
        "desenho-gabarito-roscado.svg",
        "GABARITO DE TOLERÂNCIA - ROSCA INTERNA M24 x 2",
        "5 folgas radiais | espessura 8 mm = 4 filetes",
        [(f"&#948; {d:.2f}".replace(".", ","),
          f"D {2*x.Rmaj:.2f} / D1 {2*x.Rmin:.2f}".replace(".", ","))
         for d, x in zip(G.DELTA_ROSCA, r)],
        [x.Rmaj for x in r],
        "rosca ISO M24x2, helice a direita",
        ["Testa o engate real da rosca: o botao e parafusado direto na placa.",
         "&#948; e a folga radial somada ao perfil ISO; D = 24 + 2&#948;, D1 = 21,835 + 2&#948;.",
         "8 mm de espessura = 4 passos completos de engate.",
         "O chanfro 8x8 identifica o canto da MENOR folga (&#948; = 0,10).",
         "Antes de adotar rosca na tampa final, confirmar que o botao tem",
         "comprimento roscado suficiente (ver pendencias no README)."],
        codigo="PIBIC-GB-02")


# =====================================================================
# 4. Perfil da rosca
# =====================================================================

def desenho_perfil_rosca():
    r = G.RoscaISO(24.0, 2.0, 0.0)
    P, H, dr, fl = r.P, r.H, r.dr, r.flanco
    S = 18.0                       # ampliacao uniforme (angulos ficam verdadeiros)
    OX, OY = 45, 42                # OY = linha da RAIZ (r = D/2 = 12)

    npass = 3
    D = Desenho(P * npass * S + 130, 186, "PERFIL DA ROSCA INTERNA M24 x 2",
                "ISO 68-1, perfil básico", material="—", escala="18:1",
                codigo="PIBIC-RS-01")

    yraiz = OY
    ycrista = OY + dr * S          # crista fica mais perto do eixo => mais abaixo

    def px(p):  return OX + p * S
    def py(rr): return yraiz + (r.Rmaj - rr) * S

    # perfil ao longo de 3 passos
    pts = []
    for i in range(npass * 400 + 1):
        p = i * P * npass / (npass * 400)
        pts.append((px(p), py(r.raio(p))))
    D.poli(pts, L_CONTORNO)

    # material acima do perfil (hachura leve)
    D.el.append('<defs><pattern id="mat" width="2.4" height="2.4" '
                'patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
                '<line x1="0" y1="0" x2="0" y2="2.4" stroke="#999" stroke-width="0.15"/>'
                '</pattern></defs>')
    poly = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    D.el.append(f'<polygon points="{poly} {px(P*npass):.2f},{yraiz-26:.2f} '
                f'{px(0):.2f},{yraiz-26:.2f}" fill="url(#mat)" stroke="none"/>')
    D.txt(px(P * npass / 2), yraiz - 20, "MATERIAL DA PLACA", FONTE_P, cor="#666")

    # linhas de referencia.
    # py() recebe RAIO; os diametros de tabela viram raio dividindo por 2.
    for yy, rot, cor in ((yraiz, "D = 24,000  (raiz do filete interno)", "#1a5276"),
                         (py(12 - 0.649519 * P / 2), "D2 = 22,701  (primitivo)", "#7f8c8d"),
                         (ycrista, "D1 = 21,835  (crista do filete interno)", "#1a5276")):
        D.linha(px(-0.35), yy, px(P * npass + 0.35), yy, L_FINA, cor, dash="6,2")
        D.txt(px(P * npass + 0.6), yy + 1.0, rot, FONTE_P, anc="start", cor=cor)
    D.txt(px(P * npass + 0.6), ycrista + 12, "VAZIO (furo)", FONTE_P,
          anc="start", cor="#666")

    # Triangulo gerador sobre o segundo passo.
    # O apice fica no MEIO DO PLANO DA CRISTA (p = P/8 dentro do passo), a H/4
    # alem de D1; os cantos da base ficam a H/8 alem de D e caem no meio dos
    # planos de raiz (p = apice +- P/2). Assim os flancos do triangulo
    # coincidem exatamente com os flancos do perfil.
    apex_p = P + P / 8
    r_apex = r.Rmin - H / 4        # crista truncada em H/4
    r_base = r.Rmaj + H / 8        # raiz  truncada em H/8
    D.poli([(px(apex_p - P / 2), py(r_base)),
            (px(apex_p), py(r_apex)),
            (px(apex_p + P / 2), py(r_base))],
           L_TRACO, cor="#c0392b")
    # 60 graus e o angulo do APICE do triangulo gerador
    D.txt(px(apex_p), py(r_apex) - 10, "60&#176;", FONTE_P, cor="#c0392b")
    D.linha(px(apex_p), py(r_apex), px(apex_p + 0.5), py(r_apex) + 6,
            L_FINA, "#c0392b")
    D.txt(px(apex_p + 0.55), py(r_apex) + 7,
          "triangulo gerador  H = P&#183;&#8730;3/2 = 1,7321  (apice truncado H/4, base H/8)",
          FONTE_P, anc="start", cor="#c0392b")

    # cotas axiais
    D.cota_h(px(0), px(P), yraiz - 32, "P = 2,000  (passo)", yraiz)
    D.cota_h(px(0), px(P / 4), ycrista + 10, "P/4 = 0,500", ycrista)
    D.cota_h(px(P / 4), px(P / 4 + fl), ycrista + 20, "flanco 5P/16 = 0,625", ycrista)
    D.cota_h(px(P / 4 + fl), px(P / 4 + fl + P / 8), ycrista + 30, "P/8 = 0,250", yraiz)
    D.cota_v(yraiz, ycrista, px(-0.55), "5H/8 = 1,0825  (radial)", None)

    D.nota(OX, 106, [
        "MEMORIA:",
        "H  = P&#183;&#8730;3/2 = 2 &#183; 0,8660 = 1,73205 mm",
        "D1 = D &#8722; 2&#183;(5H/8) = 24 &#8722; 2,16506 = 21,83494 mm   (tabela: 21,835)",
        "D2 = D &#8722; 0,649519&#183;P = 24 &#8722; 1,29904 = 22,70096 mm   (tabela: 22,701)",
        "flanco = (5H/8)&#183;tan30&#176; = (5/8)(P&#8730;3/2)/&#8730;3 = 5P/16 = 0,625 mm  (exato)",
        "fechamento do passo:  P/4 + 5P/16 + P/8 + 5P/16 = 16P/16 = P   &#10003;",
        "",
        "A folga de impressao &#948; desloca TODO o perfil para fora (Rmaj e Rmin somam &#948;),",
        "por isso a decomposicao axial acima nao muda com &#948;.",
    ])
    D.salvar("desenho-perfil-rosca.svg")


if __name__ == "__main__":
    print("desenhos gerados:")
    desenho_tampa()
    desenho_gabarito_passante()
    desenho_gabarito_roscado()
    desenho_perfil_rosca()
