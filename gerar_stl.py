#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de STL binario - PIBIC-CEUB
Gabaritos de tolerancia do furo M24 x 2.

Sem dependencias externas: so a biblioteca padrao. Existe porque nao ha
OpenSCAD/FreeCAD instalado nesta maquina.

A placa avulsa de 209,30 x 108,50 que este script gerava foi removida: quem
faz o papel dela agora e o painel da caixa (gerar_modelo_3mf.py), que tem
rebaixo de assento das capas e prende no corpo. Os gabaritos continuam aqui
porque medem tolerancia de furo, nao dependem de peca nenhuma e cabem em
qualquer mesa - tem 160 x 40 mm.

Pecas geradas
-------------
  gabarito-passante.stl   5 furos lisos, folgas 24,4 a 25,0 - testa o
                          furo de passagem (botao preso por porca)
  gabarito-roscado.stl    5 furos com rosca ISO M24x2, folgas radiais
                          0,10 a 0,50 - testa o engate real da rosca

METODO DE MALHA
---------------
Tudo e um prisma reto: placa plana com furos passantes.

1. Faces: a placa e dividida em faixas convexas com um furo cada. O
   contorno do furo e o contorno da faixa sao dois aneis ordenados
   angularmente em torno do eixo do furo, costurados por caminhamento
   angular. A costura NAO inventa vertices no contorno da faixa, entao
   faixas vizinhas compartilham exatamente os mesmos vertices na linha de
   corte e nao surgem juncoes-T.

2. Parede de furo liso: quads verticais sobre o circulo.

3. Parede de furo roscado: a superficie helicoidal e um campo de alturas
   sobre o cilindro - o raio em (theta, z) depende so da fase
   (z - P*theta/2pi) mod P. Para cada theta amostra-se z exatamente nos
   pontos de quebra do perfil ISO (onde a inclinacao muda), e colunas
   vizinhas sao costuradas por ordem de z. Como a fase avanca exatamente
   um passo por volta, a coluna 0 fecha com a ultima sem emenda.

4. Parede externa: levantada apenas das arestas que pertencem a uma unica
   faixa (as arestas de corte interno aparecem em duas e sao ignoradas).

Uso:  python gerar_stl.py
"""

import math
import struct
from collections import defaultdict

SEG        = 128    # segmentos por circulo liso
SEG_ROSCA  = 120    # colunas angulares por rosca
MAX_ARESTA = 10.0   # mm - subdivisao do contorno, melhora a forma dos triangulos

TAN30 = math.tan(math.radians(30.0))   # 0.5773503
COT30 = 1.0 / TAN30                    # 1.7320508 = raiz(3)


# =====================================================================
# Perfil de rosca ISO 68-1
# =====================================================================

class RoscaISO:
    """
    Perfil basico ISO 68-1 para rosca INTERNA (porca).

    Para M24 x 2:
        H  = P * raiz(3)/2            = 1,7320508 mm  (altura do triangulo)
        D  = 24,000 mm                 diametro maior  = RAIZ da rosca interna
        D2 = D - 0,649519*P = 22,701    diametro primitivo
        D1 = D - 1,082532*P = 21,835    diametro menor = CRISTA da rosca interna

    'delta' e a folga radial de impressao, somada aos dois raios. Como ela
    desloca o perfil inteiro para fora, a decomposicao axial nao muda.
    """

    def __init__(self, D=24.0, P=2.0, delta=0.0):
        self.D, self.P, self.delta = D, P, delta
        self.H    = P * math.sqrt(3) / 2       # altura do triangulo gerador
        self.dr   = 5 * self.H / 8             # truncagem: 1,0825318 mm p/ P=2
        self.Rmaj = D / 2 + delta              # raiz do filete interno
        self.Rmin = D / 2 - self.dr + delta    # crista do filete interno

        # Comprimento axial do flanco. Vale exatamente 5P/16:
        #   flanco = dr * tan(30) = (5H/8)/raiz(3) = (5/8)(P raiz3/2)/raiz3 = 5P/16
        # Usar a forma fechada evita erro de arredondamento e faz as quebras
        # fecharem o passo exatamente (0,5 + 0,625 + 0,25 + 0,625 = 2).
        self.flanco = 5 * P / 16

        # quebras axiais ao longo de um passo:
        #   crista plana (P/4) | flanco | raiz plana (P/8) | flanco
        self.b = [0.0,
                  P / 4,
                  P / 4 + self.flanco,
                  P / 4 + self.flanco + P / 8,
                  P]

    def raio(self, p):
        """Raio do perfil na fase axial p (0 <= p < P)."""
        p = p % self.P
        b = self.b
        if p < b[1]:
            return self.Rmin
        if p < b[2]:                                            # flanco subindo
            return self.Rmin + (p - b[1]) / self.flanco * self.dr
        if p < b[3]:
            return self.Rmaj
        return self.Rmaj - (p - b[3]) / self.flanco * self.dr   # flanco descendo

    def conferir(self):
        """Consistencia do perfil. Levanta AssertionError se algo nao fecha."""
        assert self.b[4] == self.P, "as quebras nao fecham um passo"
        # o flanco de 60 graus: a razao axial/radial tem de ser tan(30)
        assert abs(self.flanco / self.dr - TAN30) < 1e-12, "angulo de flanco != 60"
        assert abs(self.raio(self.b[2]) - self.Rmaj) < 1e-12
        assert abs(self.raio(self.P - 1e-12) - self.Rmin) < 1e-9
        return True


# =====================================================================
# Geometria 2D
# =====================================================================

def circulo(cx, cy, r, n=SEG):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def subdividir(poly, max_len=MAX_ARESTA):
    """
    Insere vertices nas arestas longas. A ordem canonica dos extremos garante
    que uma aresta compartilhada por duas faixas receba pontos identicos bit a
    bit nas duas - e isso que mantem a malha estanque.
    """
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        out.append(a)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = int(math.ceil(L / max_len))
        if k > 1:
            inv = a > b
            p, q = (b, a) if inv else (a, b)
            pts = [(p[0] + (q[0] - p[0]) * t / k,
                    p[1] + (q[1] - p[1]) * t / k) for t in range(1, k)]
            if inv:
                pts.reverse()
            out.extend(pts)
    return out


def anel(cx, cy, dentro, poly):
    """
    Costura o contorno interno 'dentro' (ja ordenado no sentido anti-horario
    por angulo em torno de cx,cy) ao contorno externo 'poly', por caminhamento
    angular. Retorna triangulos 2D anti-horarios. Nao cria vertices em 'poly'.
    """
    ang_d = [math.atan2(p[1] - cy, p[0] - cx) % (2 * math.pi) for p in dentro]
    fora  = sorted(poly, key=lambda p: math.atan2(p[1] - cy, p[0] - cx) % (2 * math.pi))
    ang_f = [math.atan2(p[1] - cy, p[0] - cx) % (2 * math.pi) for p in fora]

    nd, nf = len(dentro), len(fora)
    ad = ang_d + [ang_d[0] + 2 * math.pi]
    af = ang_f + [ang_f[0] + 2 * math.pi]

    tris = []
    i = j = 0
    while i < nd or j < nf:
        if i < nd and (j >= nf or ad[i + 1] <= af[j + 1]):
            tris.append((dentro[i % nd], fora[j % nf], dentro[(i + 1) % nd]))
            i += 1
        else:
            tris.append((dentro[i % nd], fora[j % nf], fora[(j + 1) % nf]))
            j += 1
    return tris


# =====================================================================
# Furos
# =====================================================================

def parede_cilindro(pts, z0, z1):
    """
    Parede vertical sobre a curva fechada 'pts' (anti-horaria), de z0 a z1.
    A curva e percorrida invertida, entao a normal aponta PARA o eixo, ou
    seja, para fora do material.
    """
    tris = []
    pts = list(reversed(pts))
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        a0, b0 = (a[0], a[1], z0), (b[0], b[1], z0)
        a1, b1 = (a[0], a[1], z1), (b[0], b[1], z1)
        tris.append((a0, b0, b1))
        tris.append((a0, b1, a1))
    return tris


def coroa(interno, externo, z, para_cima=True):
    """
    Anel plano entre duas curvas concentricas de MESMA contagem e mesmos
    angulos, na altura z. 'para_cima' -> normal +z.
    """
    tris = []
    n = len(interno)
    for i in range(n):
        a, b = interno[i], interno[(i + 1) % n]
        A, B = externo[i], externo[(i + 1) % n]
        t = [((a[0], a[1], z), (A[0], A[1], z), (B[0], B[1], z)),
             ((a[0], a[1], z), (B[0], B[1], z), (b[0], b[1], z))]
        tris.extend(t if para_cima else [(p, s, q) for p, q, s in t])
    return tris


class FuroLiso:
    """Furo cilindrico passante."""

    def __init__(self, cx, cy, diametro):
        self.cx, self.cy, self.d = cx, cy, diametro
        self._c = circulo(cx, cy, diametro / 2)

    def contorno(self, z):
        return self._c

    def parede(self, esp):
        return parede_cilindro(self._c, 0.0, esp)


class FuroRoscado:
    """Furo com rosca interna ISO, helice a direita."""

    def __init__(self, cx, cy, rosca, esp, n=SEG_ROSCA):
        self.cx, self.cy, self.r, self.esp = cx, cy, rosca, esp
        self.n = n
        self.cols = [self._coluna(2 * math.pi * i / n) for i in range(n)]

    def _coluna(self, th):
        """Cadeia de vertices em z para um angulo fixo, cortada nas quebras."""
        P, r = self.r.P, self.r
        base = P * th / (2 * math.pi)          # deslocamento da helice
        zs = {0.0, self.esp}
        k0 = int(math.floor((0.0 - base) / P)) - 1
        k1 = int(math.ceil((self.esp - base) / P)) + 1
        for k in range(k0, k1 + 1):
            for bb in r.b[:-1]:
                z = bb + base + k * P
                if 1e-7 < z < self.esp - 1e-7:
                    zs.add(z)
        col = []
        for z in sorted(zs):
            rad = r.raio((z - base) % P)
            col.append((self.cx + rad * math.cos(th),
                        self.cy + rad * math.sin(th), z))
        return col

    def contorno(self, z):
        """Secao do furo na altura z (curva fechada, nao circular)."""
        idx = -1 if z > self.esp / 2 else 0
        return [(p[0], p[1]) for p in (c[idx] for c in self.cols)]

    def parede(self, esp):
        tris = []
        n = self.n
        for i in range(n):
            A, B = self.cols[i], self.cols[(i + 1) % n]
            ia = ib = 0
            while ia < len(A) - 1 or ib < len(B) - 1:
                if ib >= len(B) - 1 or (ia < len(A) - 1 and A[ia + 1][2] <= B[ib + 1][2]):
                    tris.append((A[ia], A[ia + 1], B[ib]))     # normal p/ o eixo
                    ia += 1
                else:
                    tris.append((A[ia], B[ib + 1], B[ib]))
                    ib += 1
        return tris


# =====================================================================
# Montagem do solido
# =====================================================================

def placa(faixas, furos, esp):
    """
    faixas : lista de (poligono_anti_horario, indice_do_furo); indice None
             para uma faixa cheia, sem furo nenhum
    furos  : lista de FuroLiso / FuroRoscado
    esp    : espessura em mm
    """
    faixas = [(subdividir(p), idx) for p, idx in faixas]
    tris = []

    # --- faces superior e inferior ---
    for poly, idx in faixas:
        if idx is None:
            # leque a partir do centroide: nao acrescenta vertice no contorno,
            # entao as faixas vizinhas continuam casando aresta a aresta, e nao
            # gera triangulo degenerado como um leque a partir de um canto.
            gx = sum(p[0] for p in poly) / len(poly)
            gy = sum(p[1] for p in poly) / len(poly)
            for i in range(len(poly)):
                a, b = poly[i], poly[(i + 1) % len(poly)]
                tris.append(((gx, gy, esp), (a[0], a[1], esp), (b[0], b[1], esp)))
                tris.append(((gx, gy, 0.0), (b[0], b[1], 0.0), (a[0], a[1], 0.0)))
            continue
        f = furos[idx]
        for (p, q, s) in anel(f.cx, f.cy, f.contorno(esp), poly):
            tris.append(((p[0], p[1], esp), (q[0], q[1], esp), (s[0], s[1], esp)))
        for (p, q, s) in anel(f.cx, f.cy, f.contorno(0.0), poly):
            tris.append(((p[0], p[1], 0.0), (s[0], s[1], 0.0), (q[0], q[1], 0.0)))

    # --- parede externa: so arestas de uma unica faixa ---
    Q = 1e7
    ch = lambda v: (round(v[0] * Q), round(v[1] * Q))
    cont = defaultdict(int)
    dirigidas = []
    for poly, _ in faixas:
        m = len(poly)
        for i in range(m):
            a, b = poly[i], poly[(i + 1) % m]
            cont[frozenset((ch(a), ch(b)))] += 1
            dirigidas.append((a, b))
    for a, b in dirigidas:
        if cont[frozenset((ch(a), ch(b)))] == 1:
            a0, b0 = (a[0], a[1], 0.0), (b[0], b[1], 0.0)
            a1, b1 = (a[0], a[1], esp), (b[0], b[1], esp)
            tris.append((a0, b0, b1))
            tris.append((a0, b1, a1))

    # --- paredes dos furos ---
    for f in furos:
        tris.extend(f.parede(esp))

    return tris


def gravar_stl(caminho, tris, titulo):
    with open(caminho, "wb") as f:
        f.write(titulo.encode("ascii", "replace")[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            m = math.sqrt(nx * nx + ny * ny + nz * nz)
            if m > 1e-12:
                nx, ny, nz = nx / m, ny / m, nz / m
            f.write(struct.pack("<12fH", nx, ny, nz, *a, *b, *c, 0))
    return len(tris)


def faixas_em_linha(larg, alt, xs, chanfro=0.0):
    """Divide a placa em faixas verticais, uma por furo, cortando no meio."""
    n = len(xs)
    cortes = [0.0] + [(xs[i] + xs[i + 1]) / 2 for i in range(n - 1)] + [larg]
    faixas = []
    for i in range(n):
        xa, xb = cortes[i], cortes[i + 1]
        if i == 0 and chanfro > 0:
            poly = [(chanfro, 0.0), (xb, 0.0), (xb, alt), (0.0, alt), (0.0, chanfro)]
        else:
            poly = [(xa, 0.0), (xb, 0.0), (xb, alt), (xa, alt)]
        faixas.append((poly, i))
    return faixas


# =====================================================================
# Pecas
# =====================================================================

ESP_GABARITO = 8.0     # 4 passos de P=2 -> engate de 4 filetes
LARG_GAB     = 160.0
ALT_GAB      = 40.0
PASSO_GAB    = 29.0
CHANFRO      = 8.0

DIAM_PASSANTE = [24.4, 24.6, 24.7, 24.8, 25.0]   # mm
DELTA_ROSCA   = [0.10, 0.20, 0.30, 0.40, 0.50]   # mm de folga radial


def _centros_gabarito(n):
    x0 = LARG_GAB / 2 - (n - 1) * PASSO_GAB / 2
    return [x0 + i * PASSO_GAB for i in range(n)]


def gabarito_passante():
    xs = _centros_gabarito(len(DIAM_PASSANTE))
    yc = ALT_GAB / 2
    furos = [FuroLiso(x, yc, d) for x, d in zip(xs, DIAM_PASSANTE)]
    faixas = faixas_em_linha(LARG_GAB, ALT_GAB, xs, CHANFRO)
    tris = placa(faixas, furos, ESP_GABARITO)
    q = gravar_stl("gabarito-passante.stl", tris,
                   "Gabarito furo passante M24 PLA - PIBIC-CEUB")
    print(f"gabarito-passante.stl  {LARG_GAB:.0f} x {ALT_GAB:.0f} x {ESP_GABARITO:.0f} mm"
          f"   {q} triangulos")
    print("   diametros (chanfro = menor): " + ", ".join(str(d) for d in DIAM_PASSANTE))


def gabarito_roscado():
    xs = _centros_gabarito(len(DELTA_ROSCA))
    yc = ALT_GAB / 2
    furos = []
    for x, dl in zip(xs, DELTA_ROSCA):
        r = RoscaISO(24.0, 2.0, dl)
        r.conferir()
        furos.append(FuroRoscado(x, yc, r, ESP_GABARITO))
    faixas = faixas_em_linha(LARG_GAB, ALT_GAB, xs, CHANFRO)
    tris = placa(faixas, furos, ESP_GABARITO)
    q = gravar_stl("gabarito-roscado.stl", tris,
                   "Gabarito rosca interna M24x2 PLA - PIBIC-CEUB")
    r0 = RoscaISO(24.0, 2.0, 0.0)
    print(f"gabarito-roscado.stl   {LARG_GAB:.0f} x {ALT_GAB:.0f} x {ESP_GABARITO:.0f} mm"
          f"   {q} triangulos")
    print(f"   M24x2: H={r0.H:.4f}  D1={2*r0.Rmin:.3f}  D2={24-0.649519*2:.3f}"
          f"  flanco={r0.flanco:.3f} mm")
    print(f"   engate: {ESP_GABARITO/2:.0f} filetes")
    print("   folgas radiais (chanfro = menor): " + ", ".join(f"{d:.2f}" for d in DELTA_ROSCA))


if __name__ == "__main__":
    gabarito_passante()
    gabarito_roscado()
