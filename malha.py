#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nucleo de malha - PIBIC UniCEUB.
Autor: Rafael Alves de Sousa Costa.

So biblioteca padrao. Existe porque nao ha OpenSCAD/FreeCAD/trimesh nesta
maquina e as pecas da caixa sao todas prismas: contornos planos extrudados,
com furos escalonados coaxiais.

O QUE ESTE MODULO GARANTE
-------------------------
Uma peca e descrita como um conjunto de FACES horizontais (poligono com
buracos, numa altura z) e PAREDES verticais (um contorno fechado, de z0 a
z1). A estanqueidade nao depende de sorte:

  1. Todo vertice passa por 'Solido._id', que arredonda a coordenada em
     TOL_VERT e devolve o mesmo indice para pontos coincidentes. Duas
     superficies que compartilham uma aresta compartilham os vertices, bit
     a bit, porque recebem a MESMA lista de pontos.

  2. Cada furo e desenhado uma vez (a lista de pontos do circulo) e essa
     mesma lista alimenta a face que o contorna e a parede que o fecha.

  3. 'Solido.conferir' fecha o ciclo: toda aresta tem de aparecer em
     exatamente dois triangulos, com orientacoes opostas. Se qualquer uma
     das regras acima falhar, isso aparece aqui e o script para.

TRIANGULACAO
------------
Poligono com buracos por ear clipping. Cada buraco e ligado ao contorno
externo por uma ponte (aresta dupla, ida e volta), transformando a regiao
num poligono simples; depois o ear clipping usa lista duplamente ligada e
so testa os vertices REFLEXOS dentro da orelha candidata, que e o que
mantem o custo praticavel em Python puro.

Aneis concentricos (rebaixo de parafuso, fundo de furo cego) nao passam
por ai: 'Solido.coroa' costura os dois circulos diretamente, o que e exato
e muito mais barato.

PECA QUE NAO E PRISMA INTEIRA
-----------------------------
O berco do interruptor quebrou a hipotese de que a secao nao muda com z.
Tres primitivas resolvem o caso sem abandonar o resto:

  'entalhar'         troca um trecho de aresta reta de um contorno por
                     outro perfil - e assim que a mesma cavidade ganha, ou
                     nao, o ressalto, conforme a faixa de z
  'Solido.faixa'     parede sobre polilinha ABERTA, porque um rasgo
                     INTERROMPE a parede e um contorno fechado nao sabe
                     pular pedaco ('parede' virou um caso particular dela)
  'Solido.costura'   fecha a emenda entre um trecho que vale a altura toda
                     e um que muda de perfil, sem propagar a subdivisao
                     pelo contorno inteiro

A alternativa - emitir o contorno completo uma vez por faixa de z - e
correta e foi o primeiro rascunho, mas dobrava a contagem de triangulos do
corpo por causa de 17 mm de parede.
"""

import math
import struct
import zipfile
from collections import defaultdict

TOL_VERT = 1e-6      # mm - dois vertices mais proximos que isto sao o mesmo
EPS      = 1e-12


# =====================================================================
# Contornos 2D
# =====================================================================

def circulo(cx, cy, r, n=64):
    """Circulo anti-horario com n lados, primeiro ponto em angulo zero."""
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def retangulo_arredondado(larg, alt, raio, seg=24):
    """
    Retangulo larg x alt com os quatro cantos em 'raio', anti-horario,
    origem no canto inferior esquerdo.

    Os quatro trechos retos entram so pelos pontos de tangencia; os arcos
    trazem 'seg' segmentos cada. Nao ha vertice repetido nas emendas.
    """
    r = raio
    assert 2 * r <= min(larg, alt), "raio maior que a metade do menor lado"
    centros = [(larg - r, alt - r, 0.0),        # canto superior direito
               (r,        alt - r, 90.0),       # superior esquerdo
               (r,        r,       180.0),      # inferior esquerdo
               (larg - r, r,       270.0)]      # inferior direito
    pts = []
    for cx, cy, a0 in centros:
        for i in range(seg + 1):
            a = math.radians(a0 + 90.0 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    # o ultimo ponto de um arco coincide com o primeiro do seguinte
    saida = []
    for p in pts:
        if not saida or math.dist(p, saida[-1]) > TOL_VERT:
            saida.append(p)
    if math.dist(saida[0], saida[-1]) <= TOL_VERT:
        saida.pop()
    return saida


def densificar(poly, max_len=2.0):
    """
    Insere vertices nas arestas longas, sem mexer nas existentes.

    Serve a dois propositos: melhora a forma dos triangulos das faces e,
    principalmente, garante que 'subtrair_discos' enxergue os discos - os
    trechos retos do retangulo arredondado so tem vertice nas tangencias, e
    uma coluna de 10 mm no meio de uma aresta de 68 mm passaria despercebida.
    """
    saida = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        saida.append(a)
        k = int(math.ceil(math.dist(a, b) / max_len))
        for j in range(1, k):
            saida.append((a[0] + (b[0] - a[0]) * j / k,
                          a[1] + (b[1] - a[1]) * j / k))
    return saida


def area_assinada(poly):
    n = len(poly)
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % n][1] -
                     poly[(i + 1) % n][0] * poly[i][1] for i in range(n))


def antihorario(poly):
    return poly if area_assinada(poly) > 0 else list(reversed(poly))


def horario(poly):
    return poly if area_assinada(poly) < 0 else list(reversed(poly))


def dentro(p, poly):
    """Ponto em poligono, por cruzamentos (ray casting para +x)."""
    x, y = p
    n = len(poly)
    d = False
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                d = not d
    return d


def subtrair_discos(poly, discos):
    """
    Remove de 'poly' (anti-horario) a parte coberta por cada disco de
    'discos' = [(cx, cy, r, n_seg)], devolvendo um unico contorno.

    E o caso das colunas de inserto do corpo, que nascem na parede e avancam
    sobre a cavidade: cada disco morde o contorno num unico arco. A funcao
    exige exatamente isso - dois cruzamentos por disco, arco unico - e
    levanta erro se a geometria sair dessa hipotese, em vez de devolver um
    contorno errado em silencio.
    """
    pts = list(poly)
    for cx, cy, r, nseg in discos:
        n = len(pts)
        dist = [math.hypot(p[0] - cx, p[1] - cy) for p in pts]
        fora = [d > r for d in dist]
        if all(fora):
            raise ValueError(f"disco ({cx:.2f},{cy:.2f},r={r}) nao toca o contorno")
        if not any(fora):
            raise ValueError(f"disco ({cx:.2f},{cy:.2f},r={r}) engole o contorno")

        # inicio do trecho de dentro: indice i com fora[i] e not fora[i+1]
        entradas = [i for i in range(n) if fora[i] and not fora[(i + 1) % n]]
        saidas   = [i for i in range(n) if not fora[i] and fora[(i + 1) % n]]
        if len(entradas) != 1 or len(saidas) != 1:
            raise ValueError(
                f"disco ({cx:.2f},{cy:.2f},r={r}) cruza o contorno "
                f"{len(entradas)}x - a hipotese de arco unico nao vale")
        ie, isa = entradas[0], saidas[0]

        def cruzar(a, b):
            """Ponto onde o segmento a-b corta o circulo (uma raiz em [0,1])."""
            dx, dy = b[0] - a[0], b[1] - a[1]
            fx, fy = a[0] - cx, a[1] - cy
            A = dx * dx + dy * dy
            B = 2 * (fx * dx + fy * dy)
            C = fx * fx + fy * fy - r * r
            disc = B * B - 4 * A * C
            if disc < 0:
                raise ValueError("segmento nao corta o circulo")
            s = math.sqrt(disc)
            for t in ((-B - s) / (2 * A), (-B + s) / (2 * A)):
                if -EPS <= t <= 1 + EPS:
                    return (a[0] + t * dx, a[1] + t * dy)
            raise ValueError("raiz fora do segmento")

        p_ent = cruzar(pts[ie], pts[(ie + 1) % n])       # entra no disco
        p_sai = cruzar(pts[isa], pts[(isa + 1) % n])     # sai do disco

        # Arco do circulo entre p_ent e p_sai. Dos dois arcos possiveis vale o
        # que esta DENTRO do contorno original - e esse o pedaco de borda que
        # o disco passa a ocupar. Nao da para decidir por "o menor": quando o
        # centro do disco cai dentro do contorno (coluna de inserto avancando
        # sobre a cavidade) o arco correto e o maior, e a escolha errada soma
        # area em vez de subtrair. O teste do ponto medio acerta nos dois casos.
        a0 = math.atan2(p_ent[1] - cy, p_ent[0] - cx)
        a1 = math.atan2(p_sai[1] - cy, p_sai[0] - cx)
        pos = (a1 - a0) % (2 * math.pi)
        d_ang = pos
        meio = (cx + r * math.cos(a0 + pos / 2), cy + r * math.sin(a0 + pos / 2))
        if not dentro(meio, pts):
            d_ang = pos - 2 * math.pi
        k = max(2, int(abs(d_ang) / (2 * math.pi) * nseg) + 1)
        arco = [(cx + r * math.cos(a0 + d_ang * i / k),
                 cy + r * math.sin(a0 + d_ang * i / k)) for i in range(1, k)]

        # remonta: do ponto seguinte a saida ate a entrada, + entrada/arco/saida
        manter = []
        i = (isa + 1) % n
        while True:
            manter.append(pts[i])
            if i == ie:
                break
            i = (i + 1) % n
        pts = manter + [p_ent] + arco + [p_sai]
    return pts


def _arco_cortado(r, meia_fenda, n, lado):
    """
    Arco do circulo de raio 'r' que sobra do lado 'lado' (+1 = x positivo) da
    fenda central de largura 2*meia_fenda, do ponto de corte de baixo ate o de
    cima, PONTAS INCLUIDAS.
    """
    assert 0 < meia_fenda < r, "a fenda nao corta o circulo"
    th = math.acos(meia_fenda / r)
    a0 = -th if lado > 0 else math.pi - th
    d = 2 * th
    k = max(2, int(d / (2 * math.pi) * n) + 1)
    return [(r * math.cos(a0 + d * i / k), r * math.sin(a0 + d * i / k))
            for i in range(k + 1)]


def _corda(x, lado, ys, y_lim, y_min=0.0):
    """
    Vertices extras sobre a corda, em DOIS trechos: o que sai do fim do arco
    externo e o que chega no comeco dele. Separados porque em
    'degrau_da_perna' o arco interno entra entre os dois.

    Existem por causa da junta em T. O pino da perfboard e uma pilha de secoes
    em D de raios diferentes e a corda de todas cai na mesma reta; se a secao
    larga tiver uma aresta unica ali onde a estreita tem tres, 'conferir'
    acusa aresta fora de dois triangulos. Passando a MESMA lista de |y| a
    todas as secoes, as cordas saem subdivididas igual e as emendas fecham.
    Vertice colinear nao muda area, entao o volume analitico continua exato.
    """
    e = sorted({abs(v) for v in ys
                if y_min + TOL_VERT < abs(v) < y_lim - TOL_VERT})
    return ([(x, lado * v) for v in reversed(e)],
            [(x, -lado * v) for v in e])


def perna(r, meia_fenda, n=64, lado=1, ys=()):
    """
    Secao em D de UMA perna do pino da perfboard: o circulo de raio 'r'
    cortado pela fenda central, ficando com o lado 'lado'.

    O pino e fendido para que as duas pernas possam fletir - sem isso a farpa
    nao entra no furo da placa sem trincar o PLA. A fenda obriga a secao a ser
    esta, e nao um circulo: a MESMA lista alimenta a face e a parede, e a area
    dela entra na conta do volume esperado da tampa. E o que mantem 'conferir'
    fechando em 1e-9 com a fenda no meio.
    """
    x = lado * meia_fenda
    y_lim = math.sqrt(r * r - meia_fenda * meia_fenda)
    a, b = _corda(x, lado, ys, y_lim)
    return antihorario(_arco_cortado(r, meia_fenda, n, lado) + a + b)


def degrau_da_perna(r_int, r_ext, meia_fenda, n=64, lado=1, ys=()):
    """
    Coroa de UMA perna entre 'r_int' e 'r_ext', como poligono SIMPLES.

    Nao da para pedir isso a 'face' como poligono com buraco: os dois
    contornos compartilham a reta da fenda, o "buraco" encosta na borda do
    externo e o ear clipping nao encontra ponte. Aqui os dois arcos sao
    costurados pelos dois trechos de corda que sobram, e sai um poligono
    simples de verdade.
    """
    assert 0 < meia_fenda < r_int < r_ext, "raios fora de ordem no degrau"
    x = lado * meia_fenda
    yi = math.sqrt(r_int * r_int - meia_fenda * meia_fenda)
    ye = math.sqrt(r_ext * r_ext - meia_fenda * meia_fenda)
    fora = _arco_cortado(r_ext, meia_fenda, n, lado)
    dentro = _arco_cortado(r_int, meia_fenda, n, lado)
    a, b = _corda(x, lado, ys, ye, yi)
    return antihorario(list(fora) + a + list(reversed(dentro)) + b)


def inserir_ponto(poly, p, tol=TOL_VERT):
    """
    Devolve 'poly' com um vertice em 'p'; se 'p' ja e vertice, devolve como
    esta. Levanta erro se 'p' nao cai sobre nenhuma aresta - que e o sintoma
    de uma cota escrita fora do trecho onde ela faz sentido, e o lugar certo
    de descobrir isso e aqui, nao no visualizador.
    """
    pts = [tuple(q) for q in poly]
    if any(math.dist(q, p) <= tol for q in pts):
        return pts
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L <= tol:
            continue
        t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (L * L)
        if not (tol / L < t < 1 - tol / L):
            continue
        if math.dist(p, (a[0] + t * dx, a[1] + t * dy)) <= tol:
            return pts[:i + 1] + [tuple(p)] + pts[i + 1:]
    raise ValueError(f"ponto {p} nao esta sobre nenhuma aresta do contorno")


def entalhar(poly, y_face, x_ini, x_fim, perfil, tol=TOL_VERT):
    """
    Troca, na aresta reta y = y_face de 'poly', o trecho que vai de x_ini ate
    x_fim pelo 'perfil' - a lista de pontos do entalhe, PONTAS EXCLUIDAS.

    'poly' vem anti-horario, e nessa orientacao a aresta de cima e percorrida
    com x DECRESCENDO; dai a exigencia x_ini > x_fim. Um perfil vazio nao e
    caso degenerado: e como se apagam os vertices de densificacao de um
    trecho que vai virar uma aresta unica, compartilhada com uma face.
    """
    assert x_ini > x_fim, "o percurso anti-horario vai do maior x para o menor"
    pts = inserir_ponto(inserir_ponto(poly, (x_ini, y_face), tol),
                        (x_fim, y_face), tol)

    def achar(xq):
        for i, q in enumerate(pts):
            if abs(q[1] - y_face) <= tol and abs(q[0] - xq) <= tol:
                return i
        raise ValueError(f"vertice ({xq}, {y_face}) nao encontrado no contorno")

    i0, i1 = achar(x_ini), achar(x_fim)
    saida = [pts[i0]] + [tuple(q) for q in perfil] + [pts[i1]]
    i = (i1 + 1) % len(pts)
    while i != i0:
        saida.append(pts[i])
        i = (i + 1) % len(pts)
    return saida


def trecho(poly, p_ini, p_fim, tol=TOL_VERT):
    """
    Polilinha ABERTA que sai de 'p_ini' e caminha pelo contorno, no sentido
    em que ele esta escrito, ate 'p_fim'. O que fica de fora e exatamente a
    aresta de p_fim para p_ini - e assim que um rasgo interrompe uma parede.
    """
    pts = [tuple(q) for q in poly]
    n = len(pts)

    def achar(q):
        for i, r in enumerate(pts):
            if math.dist(r, q) <= tol:
                return i
        raise ValueError(f"ponto {q} nao e vertice do contorno")

    i, j = achar(p_ini), achar(p_fim)
    saida = [pts[i]]
    while i != j:
        i = (i + 1) % n
        saida.append(pts[i])
    return saida


# =====================================================================
# Triangulacao de poligono com buracos
# =====================================================================

def _cruz(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _no_triangulo(p, a, b, c):
    d1 = _cruz(a, b, p)
    d2 = _cruz(b, c, p)
    d3 = _cruz(c, a, p)
    return d1 >= 0 and d2 >= 0 and d3 >= 0


def _segmentos_cruzam(p1, p2, p3, p4):
    """Cruzamento proprio de dois segmentos (toque nas pontas nao conta)."""
    d1 = _cruz(p3, p4, p1)
    d2 = _cruz(p3, p4, p2)
    d3 = _cruz(p1, p2, p3)
    d4 = _cruz(p1, p2, p4)
    return ((d1 > EPS and d2 < -EPS) or (d1 < -EPS and d2 > EPS)) and \
           ((d3 > EPS and d4 < -EPS) or (d3 < -EPS and d4 > EPS))


def _ligar_buraco(ext, bur):
    """
    Costura o buraco 'bur' (horario) no contorno 'ext' (anti-horario) por
    uma ponte dupla, devolvendo um poligono simples anti-horario.

    A ponte sai do vertice de maior x do buraco e procura, entre os vertices
    de 'ext' a direita dele e por ordem de distancia, o primeiro que enxerga
    esse ponto sem atravessar nenhuma aresta ja existente.
    """
    m = max(range(len(bur)), key=lambda i: bur[i][0])
    M = bur[m]
    arestas = [(ext[i], ext[(i + 1) % len(ext)]) for i in range(len(ext))] + \
              [(bur[i], bur[(i + 1) % len(bur)]) for i in range(len(bur))]

    cands = sorted((i for i in range(len(ext)) if ext[i][0] > M[0] - EPS),
                   key=lambda i: math.dist(ext[i], M))
    for i in cands:
        P = ext[i]
        if any(_segmentos_cruzam(M, P, a, b) for a, b in arestas):
            continue
        meio = ((M[0] + P[0]) / 2, (M[1] + P[1]) / 2)
        if not dentro(meio, ext) or dentro(meio, bur):
            continue
        rot = bur[m:] + bur[:m]
        return ext[:i + 1] + rot + [M, P] + ext[i + 1:]
    raise ValueError("nenhuma ponte visivel para o buraco")


def triangular(externo, buracos=()):
    """
    Triangulos (a, b, c) anti-horarios da regiao entre 'externo' e os
    'buracos'. Todos os contornos entram como listas de pontos 2D; a
    orientacao e normalizada aqui dentro.
    """
    ext = antihorario(list(externo))
    burs = sorted((horario(list(b)) for b in buracos),
                  key=lambda b: -max(p[0] for p in b))
    for b in burs:
        ext = _ligar_buraco(ext, b)

    n = len(ext)
    prox = [(i + 1) % n for i in range(n)]
    ant  = [(i - 1) % n for i in range(n)]
    vivo = [True] * n

    def convexo(i):
        return _cruz(ext[ant[i]], ext[i], ext[prox[i]]) > EPS

    reflexos = {i for i in range(n) if not convexo(i)}

    def orelha(i):
        if i in reflexos:
            return False
        a, b, c = ext[ant[i]], ext[i], ext[prox[i]]
        for j in reflexos:
            if j == ant[i] or j == i or j == prox[i]:
                continue
            if _no_triangulo(ext[j], a, b, c):
                return False
        return True

    tris = []
    i = 0
    restam = n
    giros = 0
    while restam > 3:
        if not vivo[i] or not orelha(i):
            i = prox[i]
            giros += 1
            if giros > 4 * restam:
                raise ValueError("ear clipping travou - contorno degenerado")
            continue
        tris.append((ext[ant[i]], ext[i], ext[prox[i]]))
        vivo[i] = False
        reflexos.discard(i)
        a, b = ant[i], prox[i]
        prox[a], ant[b] = b, a
        for j in (a, b):
            if convexo(j):
                reflexos.discard(j)
            else:
                reflexos.add(j)
        restam -= 1
        giros = 0
        i = a
    ultimos = [i, prox[i], prox[prox[i]]]
    tris.append(tuple(ext[k] for k in ultimos))

    # conferencia barata: a area triangulada tem de bater com a area da regiao
    alvo = abs(area_assinada(antihorario(list(externo)))) - \
        sum(abs(area_assinada(list(b))) for b in buracos)
    soma = sum(_cruz(*t) / 2 for t in tris)
    if abs(soma - alvo) > max(1e-4, 1e-6 * alvo):
        raise ValueError(f"area triangulada {soma:.6f} != regiao {alvo:.6f}")
    return tris


# =====================================================================
# Solido
# =====================================================================

class Solido:
    """Malha triangular fechada, montada por faces horizontais e paredes."""

    def __init__(self, nome):
        self.nome = nome
        self.v = []
        self._idx = {}
        self.t = []

    def _id(self, x, y, z):
        k = (round(x / TOL_VERT), round(y / TOL_VERT), round(z / TOL_VERT))
        i = self._idx.get(k)
        if i is None:
            i = len(self.v)
            self._idx[k] = i
            self.v.append((x, y, z))
        return i

    def tri(self, p, q, r):
        a, b, c = self._id(*p), self._id(*q), self._id(*r)
        if a != b and b != c and c != a:
            self.t.append((a, b, c))

    # ---------- superficies ----------

    def face(self, externo, buracos=(), z=0.0, cima=True):
        """Face horizontal em z. 'cima' -> normal +z; senao -z."""
        for a, b, c in triangular(externo, buracos):
            if cima:
                self.tri((a[0], a[1], z), (b[0], b[1], z), (c[0], c[1], z))
            else:
                self.tri((a[0], a[1], z), (c[0], c[1], z), (b[0], b[1], z))

    def face_vertical(self, externo, buracos=(), y=0.0, frente=True):
        """
        Face plana no plano y = constante, descrita em (x, z).

        'frente=True' -> normal +y; 'frente=False' -> normal -y.

        Existe porque a parede de tras deixou de ser uma parede: no trecho da
        chave ela e uma chapa plana com um furo, e furo em parede nao e
        expressavel como contorno extrudado em z.

        'triangular' nao sabe que eixos sao esses - so precisa de um plano -
        entao o motor de triangulacao e o mesmo de 'face'. A unica sutileza e
        o sinal: um triangulo anti-horario em (x, z) tem normal x^ X z^ = -y^,
        entao e 'frente=False' que preserva a ordem.
        """
        for a, b, c in triangular(externo, buracos):
            P = lambda p: (p[0], y, p[1])
            if frente:
                self.tri(P(a), P(c), P(b))
            else:
                self.tri(P(a), P(b), P(c))

    def coroa(self, interno, externo, z, cima=True):
        """
        Anel plano entre dois circulos concentricos de MESMA contagem de
        pontos e mesmos angulos. Exato e sem ear clipping.
        """
        assert len(interno) == len(externo)
        n = len(interno)
        for i in range(n):
            a, b = interno[i], interno[(i + 1) % n]
            A, B = externo[i], externo[(i + 1) % n]
            for p, q, r in (((a, A, B)), ((a, B, b))):
                P = (p[0], p[1], z)
                Q = (q[0], q[1], z)
                R = (r[0], r[1], z)
                self.tri(P, Q, R) if cima else self.tri(P, R, Q)

    def parede(self, pts, z0, z1, fora=True):
        """
        Parede vertical sobre o contorno fechado 'pts', de z0 a z1.

        'fora=True'  -> normal para FORA do laco  (contorno externo da peca)
        'fora=False' -> normal para DENTRO do laco (parede de furo)
        """
        p = antihorario(list(pts))
        if not fora:
            p = list(reversed(p))
        self.faixa(p + [p[0]], z0, z1)

    def faixa(self, pts, z0, z1):
        """
        Parede vertical sobre a POLILINHA ABERTA 'pts', de z0 a z1.

        A normal sai para a DIREITA de quem caminha de pts[0] para pts[-1] -
        a mesma convencao de 'parede', porque e la que fica o lado de fora
        quando o contorno vem anti-horario. Existe porque um rasgo
        INTERROMPE a parede: o trecho vazado nao pode receber triangulo, e um
        contorno fechado nao sabe pular pedaco. 'parede' agora e o caso
        particular em que a polilinha fecha sobre si mesma.
        """
        for a, b in zip(pts, pts[1:]):
            a0, b0 = (a[0], a[1], z0), (b[0], b[1], z0)
            a1, b1 = (a[0], a[1], z1), (b[0], b[1], z1)
            self.tri(a0, b0, b1)
            self.tri(a0, b1, a1)

    def tubo(self, anel_a, anel_b, inverter=False):
        """
        Casca entre dois aneis FECHADOS de mesma contagem de pontos, em dois
        planos paralelos quaisquer. O ponto i de 'anel_a' casa com o ponto i
        de 'anel_b'; os dois entram como listas de pontos 3D.

        Existe porque 'faixa' so sabe parede VERTICAL sobre polilinha, e o
        furo da chave KCD1 tem eixo HORIZONTAL: a parede dele nao e vertical
        e o eixo nao e z. 'tubo' nao conhece eixo nenhum.

        A normal e a de (a[i+1] - a[i]) x (b[i] - a[i]); 'inverter' troca o
        sentido. Nao ha convencao "fora/dentro" aqui, porque com eixo
        arbitrario ela nao significaria nada - quem reprova a escolha errada
        e 'conferir', que exige volume positivo e volume analitico batendo.
        """
        assert len(anel_a) == len(anel_b), \
            f"{self.nome}: aneis de tamanhos diferentes no tubo"
        n = len(anel_a)
        for i in range(n):
            a0, a1 = anel_a[i], anel_a[(i + 1) % n]
            b0, b1 = anel_b[i], anel_b[(i + 1) % n]
            if inverter:
                self.tri(a0, b0, a1)
                self.tri(a1, b0, b1)
            else:
                self.tri(a0, a1, b0)
                self.tri(a1, b1, b0)

    def costura(self, a, b, za, zb):
        """
        Parede sobre o segmento a-b quando as duas arestas VERTICAIS estao
        divididas de formas diferentes: 'za' e 'zb' sao as listas crescentes
        de z de cada ponta, com o mesmo primeiro e o mesmo ultimo valor.

        Existe por causa da junta em T. Uma parede que vale a altura inteira
        encontra, na emenda, uma parede que muda de perfil com z: de um lado
        ha uma aresta longa, do outro varias curtas, e 'conferir' acusa malha
        aberta - com razao, porque os triangulos nao compartilham vertice.
        O ziper abaixo consome as duas listas ao mesmo tempo e fecha a emenda
        sem exigir que a subdivisao se propague pelo contorno todo, que era o
        que dobrava o tamanho da peca.

        Com za == zb de dois valores, produz exatamente os dois triangulos de
        'faixa' - e o caso geral, nao um caso a parte.
        """
        assert za[0] == zb[0] and za[-1] == zb[-1], \
            "as duas pontas da costura tem de comecar e terminar no mesmo z"
        A = lambda z: (a[0], a[1], z)
        B = lambda z: (b[0], b[1], z)
        i = j = 0
        while i < len(za) - 1 or j < len(zb) - 1:
            pa = za[i + 1] if i < len(za) - 1 else float("inf")
            pb = zb[j + 1] if j < len(zb) - 1 else float("inf")
            if pb <= pa:
                self.tri(A(za[i]), B(zb[j]), B(pb))
                j += 1
            else:
                self.tri(A(za[i]), B(zb[j]), A(pa))
                i += 1

    # ---------- conferencia ----------

    def volume(self):
        """Volume por divergencia. Positivo se as normais apontam para fora."""
        s = 0.0
        for i, j, k in self.t:
            a, b, c = self.v[i], self.v[j], self.v[k]
            s += (a[0] * (b[1] * c[2] - c[1] * b[2])
                  - b[0] * (a[1] * c[2] - c[1] * a[2])
                  + c[0] * (a[1] * b[2] - b[1] * a[2]))
        return s / 6.0

    def conferir(self, volume_esperado=None, tol_rel=2e-3):
        """
        Estanqueidade, orientacao e volume. Levanta AssertionError com a
        contagem de arestas defeituosas - que e o sintoma util quando uma
        face e uma parede deixam de compartilhar vertices.
        """
        cont = defaultdict(int)
        for i, j, k in self.t:
            for a, b in ((i, j), (j, k), (k, i)):
                cont[(a, b) if a < b else (b, a)] += 1
        ruins = [e for e, c in cont.items() if c != 2]
        assert not ruins, (f"{self.nome}: {len(ruins)} arestas fora de 2 "
                           f"triangulos (malha aberta ou nao-manifold)")

        dirig = defaultdict(int)
        for i, j, k in self.t:
            for a, b in ((i, j), (j, k), (k, i)):
                dirig[(a, b)] += 1
        assert all(c == 1 for c in dirig.values()), \
            f"{self.nome}: arestas dirigidas repetidas - orientacao inconsistente"

        vol = self.volume()
        assert vol > 0, f"{self.nome}: volume {vol:.1f} <= 0 - normais invertidas"

        if volume_esperado is not None:
            erro = abs(vol - volume_esperado) / volume_esperado
            assert erro < tol_rel, (
                f"{self.nome}: volume da malha {vol:.1f} mm3 diverge do "
                f"analitico {volume_esperado:.1f} mm3 em {erro*100:.3f}%")
        return vol


# =====================================================================
# Saida
# =====================================================================

_CT = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
       '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
       '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
       '</Types>')

_RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n'
         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
         'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
         '</Relationships>')


def salvar_3mf(caminho, solido, titulo=""):
    """
    3MF do nucleo (core spec 2015/02), unidade milimetro, um objeto de id 1.
    E o que o Bambu Studio, o Orca e o PrusaSlicer importam direto.
    """
    # 9 digitos significativos, nao 6: com 6 uma coordenada como 157,6482
    # sai "157,648" e a peca chega ao slicer com 0,5 micron de ruido nos
    # vertices. Nao atrapalha a impressao, mas quebra qualquer conferencia
    # que compare a malha com o contorno nominal.
    v = "".join(f'<vertex x="{x:.9g}" y="{y:.9g}" z="{z:.9g}"/>'
                for x, y, z in solido.v)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>'
                for a, b, c in solido.t)
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Title">{titulo or solido.nome}</metadata>'
        '<metadata name="Designer">Rafael Alves de Sousa Costa</metadata>'
        '<metadata name="Description">PIBIC UniCEUB</metadata>'
        '<resources><object id="1" type="model" name="'
        f'{solido.nome}"><mesh><vertices>{v}</vertices>'
        f'<triangles>{t}</triangles></mesh></object></resources>'
        '<build><item objectid="1"/></build></model>')

    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("3D/3dmodel.model", model)


def salvar_stl(caminho, solido):
    """STL binario, para quem preferir conferir no visualizador de sempre."""
    with open(caminho, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(solido.t)))
        for i, j, k in solido.t:
            a, b, c = solido.v[i], solido.v[j], solido.v[k]
            u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
            w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
            nx = u[1] * w[2] - u[2] * w[1]
            ny = u[2] * w[0] - u[0] * w[2]
            nz = u[0] * w[1] - u[1] * w[0]
            m = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            f.write(struct.pack("<12fH", nx / m, ny / m, nz / m,
                                *a, *b, *c, 0))
