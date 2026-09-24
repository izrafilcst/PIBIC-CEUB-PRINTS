#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelo parametrico da caixa - PIBIC UniCEUB.
Autor: Rafael Alves de Sousa Costa.

FONTE UNICA da geometria das duas pecas. Escreve

  caixa-corpo.3mf    corpo, com o painel dos botoes fundido,  178 x 130 x 63
  caixa-tampa.3mf    tampa de servico,                        178 x 130 x 4

e os .stl correspondentes. Os desenhos tecnicos saem de gerar_desenhos_3mf.py,
que LE estes arquivos e mede a malha - nenhuma cota e digitada duas vezes.

Material: PLA.

O QUE MUDOU EM RELACAO AO MODELO DO FUSION
------------------------------------------
1. MESA. O modelo antigo tinha 215 x 120 e foi feito para a Creality K1C
   (220 x 220). A Bambu Lab A1 mini tem 180 x 180: 215 nao cabe em nenhuma
   orientacao - a 45 graus um retangulo 215 x 120 pede 236,8 mm de mesa.
   A silhueta passou a 178 x 130.

   Os botoes continuam lado a lado no mesmo eixo, que era o pedido, e isso
   custa folga: as capas ficam a 4,35 mm uma da outra contra 25,35 mm antes.
   Nao ha como melhorar mantendo os dois no mesmo eixo - so as capas ja somam
   159,3 mm e cada parede leva mais 4.

2. PAINEL FUNDIDO NO CORPO, E LISO. As tres pecas do modelo anterior viraram
   duas: o painel deixou de existir como peca propria e passou a ser as
   camadas z = 0,00 a 8,00 mm do corpo, pela face que encosta na MESA. E a
   UNICA orientacao possivel - de boca para baixo o painel faria ponte sobre
   170 x 122 mm; de lado tudo vira balanco. E o que torna o painel LISO
   obrigatorio: qualquer rebaixo nele seria teto no ar, sem suporte.

   Os furos dos botoes e dos LEDs nascem na PRIMEIRA CAMADA, encostados na
   mesa, e por isso ganham um alivio de 0,50 mm de profundidade na boca -
   rebaixo RETO, nao chanfro (chanfro e cone, e 'conferir' casa volume por
   area de poligono em 1e-9) - para nao levar o pe de elefante da primeira
   camada.

3. FIXACAO SO NO TOPO. Com o painel fundido ao corpo, as colunas perderam a
   razao de ter inserto nas duas pontas: sobrou 1 inserto M3 por coluna, em
   cima, so para prender a tampa - 6 no total, contra 12 no desenho anterior.

4. PAREDE de 10 para 4 mm, com colunas Ø10 locais nos seis pontos de
   fixacao. Foi o que devolveu o espaco que os 178 mm de silhueta tiraram, e
   de quebra resolve a nota 6 do desenho antigo: interruptor de encaixe
   quer painel de 2 a 5 mm, e 4 mm cai dentro sem rebaixo local.

Uso:  python gerar_modelo_3mf.py
"""

import math

import malha as M

# =====================================================================
# Impressora
# =====================================================================

MESA = (180.0, 180.0, 180.0)      # Bambu Lab A1 mini

# =====================================================================
# Silhueta comum as tres pecas
# =====================================================================

CX_L = 178.0        # largura
CX_A = 130.0        # profundidade
CX_R = 55.0         # raio dos quatro cantos

# =====================================================================
# Botoes de arcade Adafruit, barril M24 x 2
# =====================================================================
# 'capa'    diametro externo da capa, do lado de fora
# 'flange'  diametro do flange que assenta na face externa, plana
# 'abaixo'  quanto o corpo do botao avanca para dentro da cavidade, medido
#           da face externa - usado para conferir folga com a placa
# 'led_*'   furos passantes sob a capa, na circunferencia de furacao

BOTOES = [
    dict(nome="vermelho", modelo="Adafruit 1185/1187/1188 - 100 mm",
         x=56.0, y=65.0, capa=98.5,
         esp_max=12.7, led_n=6, led_r=31.5, led_a0=30.0,
         flange=87.8, abaixo=41.0),
    dict(nome="verde", modelo="Adafruit 1190/1192/1193 - 60 mm",
         x=140.0, y=65.0, capa=60.8,
         esp_max=12.7, led_n=3, led_r=21.0, led_a0=90.0,
         flange=37.7, abaixo=52.4),
]

D_BARRIL   = 26.0      # passagem do barril M24 (especificacao Adafruit)
D_LED      = 10.0      # furos sob a capa

# =====================================================================
# Espessuras
# =====================================================================
# O painel encolheu de 16 para 8: os 16 so existiam para sobrar material sob
# o rebaixo de 8 mm da capa vermelha, e o rebaixo acabou. Com a peca fundida
# a face dos botoes vai para a MESA, e todo rebaixo nela viraria teto no ar.

PAIN_ESP  = 8.0        # painel liso
CAVIDADE  = 55.0       # da face interna do painel ao assento da tampa
CORPO_H   = PAIN_ESP + CAVIDADE      # 63.0 - altura da peca fundida
CORPO_PAR = 4.0
TAMPA_ESP = 4.0

LINHA     = 0.42       # largura de extrusao com bico 0,4 - paredes sao multiplos
PONTE_PLA = 20.0       # maior ponte reta admitida em PLA, apoiada dos dois lados

# Alivio na boca dos furos do painel. Eles nascem na PRIMEIRA CAMADA agora, e
# o pe de elefante os fecharia. E rebaixo RETO, nao chanfro: chanfro e cone,
# cone nao tem area de poligono, e 'conferir' casa volume em 1e-9 usando area
# de poligono. A porca M24 cobre o alivio do barril.
REB_ALIVIO   = 0.5
FOLGA_ALIVIO = 1.0     # diametral, alivio = furo + isto

# =====================================================================
# Fixacao - 6 colunas, inserto M3 SO no topo
# =====================================================================
# Eram 12 insertos porque o painel tambem parafusava. O painel virou parte do
# corpo; sobraram os 6 da tampa.

FIX_INSET    = 6.0
COL_D        = 10.0
D_INSERTO    = 4.2
PROF_INSERTO = 5.0
D_PASSAGEM   = 3.4
D_REBAIXO    = 6.5
REB_TAMPA    = 2.0
PENETRACAO   = 4.0

# =====================================================================
# Chave gangorra redonda KCD1 - snap-in na parede de tras
# =====================================================================
# Cotas do desenho cotado do fabricante (nao do PDF escaneado que travou o
# berco da SS12D00G4):
#     corpo que atravessa o painel   19,80 +/- 0,20
#     aro visivel                    23,00 +/- 0,20   cobre a borda do furo
#     corpo atras do painel          19,30
#     profundidade do corpo          17,80 +/- 0,30
#     total atras do painel          25,70 +/- 0,30   corpo + terminal
#     3 terminais, passo 7,00, lamina faston 4,80 x 0,80
#
# A chave prende sozinha nas garras e para isso quer parede FINA. A parede do
# corpo tem 4,00, entao o rebaixo circular abre SO PARA DENTRO e deixa 2,00 de
# parede local. A face externa continua lisa.
#
# x = 69,50 e o meio do unico trecho reto livre: de x = 55 (tangencia do R55)
# a x = 84 (inicio da coluna central). O rebaixo Ø25 ocupa [57,00 - 82,00].
#
# NAO ha chanfro no furo. Por dentro e onde as garras mordem; por fora seria
# cone. Os 0,40 de folga ja dao a entrada.
#
# d_rebaixo = 25,0, nao 26,0: o rebaixo circular e mais largo que o antigo
# ressalto retangular que ele substitui e encostava na coluna central em
# (89, 124) - folga diagonal de so 1,80 mm contra o minimo de 2,00. D25,0
# ainda deixa 2,4 mm de assento anular alem do furo Ø20,2 (folgado para as
# garras) e abre a folga da coluna para 2,28 mm.

CHAVE = dict(
    modelo="KCD1 redonda 3T",
    x=69.5,            # centro, ao longo da parede y = CX_A
    z=35.0,            # eixo, medido da face dos botoes (a mesa)
    d_corpo=19.8,      # o que atravessa o painel
    d_aro=23.0,        # aro visivel
    d_corpo_tras=19.3, # corpo atras do painel
    folga=0.4,         # diametral - furo deitado fecha mais que furo em pe
    d_rebaixo=25.0,    # rebaixo por dentro, onde as garras trabalham
    parede=2.0,        # parede local que sobra sob o rebaixo
    prof_corpo=17.8,   # so o corpo, sem terminal
    atras=25.7,        # reserva atras da parede: corpo + terminal
    saliencia_aro=2.7, # quanto o aro sobra para fora da face
    n_term=3, passo_term=7.0, vao_term=14.0,
    lamina=4.8, esp_lamina=0.8,
    x_face=(55.0, 84.0),   # trecho da parede que a face_vertical assume
)

# =====================================================================
# Perfboard 7 x 9 - encaixe por pino farpado na tampa
# =====================================================================
# ATENCAO: 'furo_d' e 'furo_inset' sao PRESUMIDOS. Meca a placa com o
# paquimetro antes de imprimir a tampa - sao 4 pinos, e errar o recuo poe
# todos no lugar errado de uma vez.
#
# Centro em (73, 65) nao e estetica: e o que sobrou entre as 4 colunas de
# canto, as 2 do meio e o flange Ø37,7 do botao verde.
#
# O rasgo de 6,50 e dimensionado. Duas pernas de 0,80 fletindo 0,30 (a
# interferencia da farpa Ø3,60 sobre o furo Ø3,00) num braco de 6,50:
#     eps = 3*t*y / (2*L^2) = 3*0,80*0,30 / (2*42,25) = 0,85 %
# Com rasgo so na haste (1,80 de braco) daria 11 % e a perna quebraria na
# primeira montagem.
#
# A guia de entrada e ESCALONADA, nao conica - mesma razao do alivio dos
# furos do painel.

PLACA = dict(
    larg=90.0, alt=70.0, esp=1.6,
    x=73.0, y=65.0,
    furo_d=3.0,        # PRESUMIDO - conferir
    furo_inset=3.5,    # PRESUMIDO - conferir
    ombro_d=6.0, ombro_h=3.5,       # afastador: espaco das pernas soldadas
    haste_d=2.8,                     # furo 3,00 - 0,20 de folga
    farpa_d=3.6, farpa_h=0.6,        # 0,30 radial de retencao
    guia=((3.0, 0.3), (2.4, 0.3)),   # degraus de entrada (diametro, altura)
    rasgo_w=1.2,
    rasgo_h=6.5,       # = ombro_h + haste_h + farpa_h + guias
    folga_placa=0.2,   # entre a face de cima da placa e a farpa
)

ALT_COMPONENTE = 10.0  # altura livre minima sob a placa, para componente de pe


def estacao_chave():
    """Cotas derivadas da estacao da chave, em coordenadas da peca."""
    k = dict(CHAVE)
    k["d_furo"] = k["d_corpo"] + k["folga"]              # 20,20
    k["prof_reb"] = CORPO_PAR - k["parede"]              # 2,00
    k["y_cav"] = CX_A - CORPO_PAR                        # 126,00
    k["y_reb"] = k["y_cav"] + k["prof_reb"]              # 128,00
    k["y_face"] = CX_A                                   # 130,00
    k["y_fundo"] = k["y_reb"] - k["atras"]               # ate onde a chave chega
    k["ponte_furo"] = k["d_furo"] / math.sqrt(2.0)
    k["ponte_reb"] = k["d_rebaixo"] / math.sqrt(2.0)
    return k


# =====================================================================
# Carregador TP4056 tipo C - berco de encaixe na tampa
# =====================================================================
# ATENCAO: as cotas do modulo sao PRESUMIDAS - valores tipicos da placa com
# protecao (DW01 + 8205A), que variam de vendedor para vendedor. Meca antes de
# imprimir: 'comp' decide a folga sob a garra e 'larg' a folga do canal.
#
# O modulo fica EM PE: o USB-C e paralelo a placa, entao para o plugue subir
# de baixo para cima a placa tem de ficar perpendicular a tampa. Deitado, o
# conector apontaria para a parede do corpo, que nao pode ser reimpresso.
#
# Borda direita, entre o envelope do botao verde e a parede: e o unico bolsao
# longe do centro com 28 mm livres em z. Lado dos componentes para -x, a
# cavidade: o CI chega a 70-90 C carregando a 1 A e o PLA amolece a 55-60.
#
# 'y' e parametro, e nao CX_A/2, de proposito. A tampa e modelada espelhada
# (z invertido com o x, y do corpo), entao tudo nela tem de ser simetrico em
# y = CX_A/2 - e so um parametro livre deixa a conferencia provar isso.

CARREGADOR = dict(
    modelo="TP4056 tipo C, com protecao",
    comp=28.0, larg=17.0, esp=1.6,     # placa - PRESUMIDOS
    usb_l=9.0, usb_h=3.3,              # conector: largura e altura - PRESUMIDOS
    alt_comp=1.8,                      # mais alto alem do USB - PRESUMIDO
    capa=(12.35, 6.5),                 # capa do plugue, maximo da norma USB-C
    x=168.0, y=65.0,                   # plano medio da placa e centro dela
    folga=0.2,                         # encaixe em PLA, por lado
    prof_canal=1.2, aba=1.2, alma=2.0,
    garra_h=1.2,
    degraus=((0.4, 0.4), (0.8, 0.4)),  # entrada: (fundo do canal, altura)
    janela=(13.0, 7.2),                # (ao longo de y, ao longo de x)
)


def estacao_carregador():
    """
    Cotas derivadas do berco. x, y da peca; z da TAMPA (0 na face externa).

    Em planta cada coluna e um retangulo 2*u_meia (x) por w_fora - w_ponta
    (y), com um canal de largura canal_w aberto para o centro. 'w' e a
    distancia a y = yc: a ponta das abas fica em w_ponta, o fundo do canal em
    w_ponta + g. O perfil em z e a lista (z0, z1, g), de baixo para cima; na
    garra g = 0 e o canal fecha.
    """
    c = dict(CARREGADOR)
    c["yc"] = c["y"]
    c["canal_w"] = c["esp"] + 2 * c["folga"]                  # 2,00
    c["w_fundo"] = c["larg"] / 2 + c["folga"]                 # 8,70
    c["w_ponta"] = c["w_fundo"] - c["prof_canal"]             # 7,50
    c["w_fora"] = c["w_fundo"] + c["alma"]                    # 10,70
    c["u_meia"] = c["canal_w"] / 2 + c["aba"]                 # 2,20
    c["x_usb"] = c["x"] - c["esp"] / 2 - c["usb_h"] / 2       # 165,55
    c["x_mod"] = (c["x"] - c["esp"] / 2 - max(c["usb_h"], c["alt_comp"]),
                  c["x"] + c["esp"] / 2)
    c["z_garra"] = TAMPA_ESP + c["comp"] + c["folga"]         # 32,20
    perfil = [(TAMPA_ESP, c["z_garra"], c["prof_canal"]),
              (c["z_garra"], c["z_garra"] + c["garra_h"], 0.0)]
    z = c["z_garra"] + c["garra_h"]
    for g, h in c["degraus"]:
        perfil.append((z, z + h, g))
        z += h
    c["perfil"], c["topo"] = perfil, z                        # topo 34,20
    c["niveis"] = sorted({g for _, _, g in perfil if g > 0})
    c["cobre"] = c["prof_canal"] - c["folga"]                 # 1,00
    c["alivio"] = (c["janela"][0] + FOLGA_ALIVIO,
                   c["janela"][1] + FOLGA_ALIVIO)
    c["envelope"] = (min(c["x_mod"][0], c["x"] - c["u_meia"]),
                     c["yc"] - c["w_fora"],
                     max(c["x_mod"][1], c["x"] + c["u_meia"]),
                     c["yc"] + c["w_fora"])
    # topo do berco em z do CORPO: a face interna da tampa encosta em CORPO_H
    c["z_topo_corpo"] = CORPO_H + TAMPA_ESP - c["topo"]       # 32,80

    # Deformacao ao encaixar: a coluna inteira flete em y, engastada na
    # chapa. Secao U - alma de 'alma' mais duas abas de 'aba' x 'prof_canal'
    # - com a linha neutra calculada; c e a fibra mais distante dela. A
    # deflexao e a garra inteira (placa encostada no fundo DESTE canal).
    A_alma = 2 * c["u_meia"] * c["alma"]
    A_aba = 2 * c["aba"] * c["prof_canal"]
    ln = ((A_alma * c["alma"] / 2
           + A_aba * (c["alma"] + c["prof_canal"] / 2)) / (A_alma + A_aba))
    c["c_fibra"] = max(ln, c["alma"] + c["prof_canal"] - ln)
    c["braco"] = c["z_garra"] + c["garra_h"] / 2 - TAMPA_ESP  # 28,80
    c["eps"] = 3 * c["prof_canal"] * c["c_fibra"] / c["braco"] ** 2
    return c


def _coluna_local(e, g):
    """
    Contorno da coluna de cima em (u, w) locais: u = x - e['x'],
    w = y - yc. Anti-horario.

    O lado do canal recebe um vertice em CADA nivel mais raso que g. Sem
    isso a aresta unica de uma secao encontraria as varias da vizinha na
    emenda, e a malha abriria - o mesmo T da corda do pino.
    """
    hc, um = e["canal_w"] / 2, e["u_meia"]
    wp, wf = e["w_ponta"], e["w_fora"]
    lados = [d for d in e["niveis"] if d < g]
    pts = [(-um, wp), (-hc, wp)]
    if g > 0:
        pts += [(-hc, wp + d) for d in lados] + [(-hc, wp + g), (hc, wp + g)]
        pts += [(hc, wp + d) for d in reversed(lados)]
    pts += [(hc, wp), (um, wp), (um, wf), (-um, wf)]
    return pts


def _no_lugar(e, pts, lado):
    """(u, w) locais -> (x, y) da peca. lado = -1 espelha em y = yc."""
    return M.antihorario([(e["x"] + u, e["yc"] + lado * w) for u, w in pts])


def secao_coluna(e, g, lado):
    """Secao em planta de uma coluna do berco, com canal de fundo g."""
    return _no_lugar(e, _coluna_local(e, g), lado)


def ranhura(e, g0, g1, lado):
    """
    Faixa do canal entre as profundidades g0 < g1: a face horizontal que
    aparece onde a secao da coluna muda de um trecho para o seguinte.
    """
    hc, wp = e["canal_w"] / 2, e["w_ponta"]
    meio = [d for d in e["niveis"] if g0 < d < g1]
    pts = ([(-hc, wp + g0), (hc, wp + g0)] + [(hc, wp + d) for d in meio]
           + [(hc, wp + g1), (-hc, wp + g1)]
           + [(-hc, wp + d) for d in reversed(meio)])
    return _no_lugar(e, pts, lado)


def pinos_placa():
    """Os 4 centros dos pinos, e as alturas acumuladas do perfil."""
    p = PLACA
    dx = p["larg"] / 2 - p["furo_inset"]
    dy = p["alt"] / 2 - p["furo_inset"]
    centros = [(p["x"] - dx, p["y"] - dy), (p["x"] + dx, p["y"] - dy),
               (p["x"] - dx, p["y"] + dy), (p["x"] + dx, p["y"] + dy)]
    haste_h = p["esp"] + p["folga_placa"]
    z = [0.0, p["ombro_h"], p["ombro_h"] + haste_h,
         p["ombro_h"] + haste_h + p["farpa_h"]]
    for _, h in p["guia"]:
        z.append(z[-1] + h)
    return dict(centros=centros, haste_h=haste_h, z=z, topo=z[-1])

# =====================================================================
# Segmentacao das curvas
# =====================================================================

SEG_CANTO  = 24        # por arco de 90 graus da silhueta
SEG_BARRIL = 64
SEG_MEDIO  = 48
SEG_PEQ    = 32
MAX_ARESTA = 3.0


# =====================================================================
# Contornos derivados
# =====================================================================

def silhueta(reducao=0.0):
    """Silhueta comum, opcionalmente encolhida 'reducao' mm para dentro."""
    r = reducao
    return M.densificar(
        [(x + r, y + r) for x, y in
         M.retangulo_arredondado(CX_L - 2 * r, CX_A - 2 * r, CX_R - r,
                                 seg=SEG_CANTO)],
        MAX_ARESTA)


def pontos_fixacao():
    """
    Os seis centros de fixacao, sobre a silhueta deslocada FIX_INSET para
    dentro: um no meio de cada aresta reta longa e um em cada canto, a 45
    graus. Sao os unicos lugares onde cabem - o rebaixo do botao vermelho
    ocupa quase toda a faixa central da peca.
    """
    d = CX_R - FIX_INSET
    k = d * math.sqrt(2) / 2
    return [
        (CX_L / 2, FIX_INSET),
        (CX_L / 2, CX_A - FIX_INSET),
        (CX_R - k, CX_R - k),
        (CX_L - CX_R + k, CX_R - k),
        (CX_R - k, CX_A - CX_R + k),
        (CX_L - CX_R + k, CX_A - CX_R + k),
    ]


def leds(b):
    """Centros dos furos Ø10 sob a capa do botao 'b'."""
    return [(b["x"] + b["led_r"] * math.cos(math.radians(b["led_a0"] + 360.0 * i / b["led_n"])),
             b["y"] + b["led_r"] * math.sin(math.radians(b["led_a0"] + 360.0 * i / b["led_n"])))
            for i in range(b["led_n"])]


# =====================================================================
# Conferencias de projeto - rodam antes de qualquer malha
# =====================================================================

def _dist_poligono(p, poly):
    """Menor distancia do ponto p ao contorno fechado poly."""
    melhor = float("inf")
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy)
                         / (dx * dx + dy * dy)))
        melhor = min(melhor, math.hypot(p[0] - a[0] - t * dx,
                                        p[1] - a[1] - t * dy))
    return melhor


def conferir_projeto():
    """
    Cada regra aqui e uma coisa que, se estiver errada, so apareceria depois
    de 6 horas de impressao. Falhar cedo e de graca.
    """
    fix = pontos_fixacao()
    bv, bg = BOTOES
    msgs = []

    def exigir(cond, msg):
        if not cond:
            msgs.append(msg)

    # ---- mesa ----
    exigir(CX_L <= MESA[0] and CX_A <= MESA[1],
           f"silhueta {CX_L} x {CX_A} nao cabe na mesa {MESA[0]} x {MESA[1]}")
    for nome, h in (("painel", PAIN_ESP), ("corpo", CORPO_H), ("tampa", TAMPA_ESP)):
        exigir(h <= MESA[2], f"{nome} com {h} mm passa da altura da mesa")

    # ---- botoes: capa contra capa e capa contra a borda ----
    d = math.dist((bv["x"], bv["y"]), (bg["x"], bg["y"]))
    folga = d - bv["capa"] / 2 - bg["capa"] / 2
    exigir(folga > 3.0, f"folga entre as capas {folga:.2f} mm - capas encostam")

    sil = silhueta()
    for b in BOTOES:
        rr = b["capa"] / 2
        borda = min(math.dist((b["x"], b["y"]), p) for p in sil) - rr
        exigir(borda > 3.0,
               f"rebaixo do botao {b['nome']} a {borda:.2f} mm da borda")
        for p in leds(b):
            exigir(math.dist((b["x"], b["y"]), p) + D_LED / 2 < rr - 1.0,
                   f"furo Ø{D_LED} do botao {b['nome']} sai do rebaixo")
        exigir(b["capa"] / 2 > D_BARRIL / 2,
               f"capa do botao {b['nome']} menor que o furo do barril")

    # ---- coluna de inserto contra a parede ----
    exigir(COL_D / 2 > D_INSERTO / 2 + 2.0, "coluna fina demais em volta do inserto")
    exigir(FIX_INSET + COL_D / 2 > CORPO_PAR,
           "coluna nao avanca sobre a cavidade - subtrair_discos vai falhar")
    exigir(FIX_INSET - COL_D / 2 < CORPO_PAR,
           "coluna nao encosta na parede - ficaria solta no meio da cavidade")

    # ---- botao: espessura apertada pela porca, agora sem rebaixo ----
    for b in BOTOES:
        exigir(PAIN_ESP <= b["esp_max"],
               f"botao {b['nome']} aperta {PAIN_ESP:.2f} mm, maximo {b['esp_max']}")
        exigir(PAIN_ESP >= 5.0,
               f"botao {b['nome']} aperta so {PAIN_ESP:.2f} mm - material de menos")
    exigir(PAIN_ESP / 2.0 >= 3.0,
           f"painel de {PAIN_ESP:.2f} da menos de 3 filetes de M24 x 2")

    # ---- peca fundida na mesa ----
    exigir(CORPO_H <= MESA[2], f"peca fundida com {CORPO_H:.2f} passa da mesa")

    # ---- parafuso da tampa ----
    L = (TAMPA_ESP - REB_TAMPA) + PENETRACAO
    exigir(TAMPA_ESP - REB_TAMPA >= 1.5,
           f"tampa: so {TAMPA_ESP-REB_TAMPA:.2f} mm de material sob a cabeca "
           f"do parafuso - minimo 1,50")
    exigir(PROF_INSERTO > PENETRACAO, "parafuso encosta no fundo do inserto")
    exigir(abs(L - round(L)) < 1e-9, f"tampa pede M3 x {L:.2f}, fora de catalogo")

    # ---- estacao da chave ----
    k = estacao_chave()
    xa, xb = k["x_face"]
    r = k["d_rebaixo"] / 2
    exigir(CX_R <= xa and xb <= CX_L - CX_R,
           f"trecho reto da face_vertical [{xa}, {xb}] sai do trecho reto da parede")
    exigir(xa + 1.0 <= k["x"] - r and k["x"] + r <= xb - 1.0,
           f"rebaixo da chave em [{k['x']-r:.2f}, {k['x']+r:.2f}] nao cabe no "
           f"trecho reto [{xa:.2f}, {xb:.2f}]")
    exigir(k["z"] - r > PAIN_ESP and k["z"] + r < CORPO_H,
           f"rebaixo da chave em z [{k['z']-r:.2f}, {k['z']+r:.2f}] sai da parede")
    for i, (cx, cy) in enumerate(fix, 1):
        d = math.hypot(max(k["x"] - r - cx, 0.0, cx - k["x"] - r),
                       max(k["y_cav"] - cy, 0.0, cy - CX_A))
        exigir(d - COL_D / 2 >= 2.0,
               f"rebaixo da chave a {d-COL_D/2:.2f} mm da coluna {i} - minimo 2,00")
    exigir(1.6 <= k["parede"] <= 3.0,
           f"parede local da chave {k['parede']:.2f} fora da faixa de snap")
    exigir(k["parede"] < CORPO_PAR, "parede local mais grossa que a parede cheia")
    exigir(k["ponte_furo"] <= PONTE_PLA and k["ponte_reb"] <= PONTE_PLA,
           f"ponte de {max(k['ponte_furo'], k['ponte_reb']):.2f} mm passa do "
           f"limite de {PONTE_PLA:.2f} em PLA")
    exigir(k["y_fundo"] > CORPO_PAR,
           f"a chave chega a y={k['y_fundo']:.2f} e bate na parede oposta")

    # ---- perfboard ----
    pl, pn = PLACA, pinos_placa()
    x0, x1 = pl["x"] - pl["larg"] / 2, pl["x"] + pl["larg"] / 2
    y0, y1 = pl["y"] - pl["alt"] / 2, pl["y"] + pl["alt"] / 2
    for i, (cx, cy) in enumerate(fix, 1):
        d = math.hypot(max(x0 - cx, 0.0, cx - x1), max(y0 - cy, 0.0, cy - y1))
        exigir(d - COL_D / 2 >= 2.0,
               f"placa a {d-COL_D/2:.2f} mm da coluna {i} - minimo 2,00")
        for j, (px, py) in enumerate(pn["centros"], 1):
            g = math.dist((px, py), (cx, cy)) - COL_D / 2 - pl["ombro_d"] / 2
            exigir(g >= 2.0, f"pino {j} a {g:.2f} mm da coluna {i}")
    z_placa = CORPO_H - pl["ombro_h"] - pl["esp"]     # face de cima da placa

    # A placa passa POR BAIXO do botao vermelho de proposito: e o unico jeito
    # de 90 x 70 caber entre as seis colunas. Entao a folga com cada botao
    # pode ser NO PLANO ou NA ALTURA, e basta uma das duas. Onde ela passa por
    # baixo, o que sobra em z tem de dar para um componente de pe - e e essa
    # regra que segura a placa longe do botao verde, que desce muito mais.
    for b in BOTOES:
        d = math.hypot(max(x0 - b["x"], 0.0, b["x"] - x1),
                       max(y0 - b["y"], 0.0, b["y"] - y1)) - b["flange"] / 2
        if d >= 2.0:
            continue
        sobra = z_placa - b["abaixo"]
        exigir(sobra >= ALT_COMPONENTE,
               f"placa passa sob o botao {b['nome']} com {d:.2f} mm no plano "
               f"e so {sobra:.2f} mm em z - minimo {ALT_COMPONENTE:.2f}")

    exigir(pl["ombro_h"] >= 2.5,
           f"ombro de {pl['ombro_h']:.2f} nao deixa espaco para as pernas soldadas")
    t = (pl["haste_d"] - pl["rasgo_w"]) / 2
    y = (pl["farpa_d"] - pl["furo_d"]) / 2
    eps = 3 * t * y / (2 * pl["rasgo_h"] ** 2)
    exigir(eps <= 0.010,
           f"deformacao de flexao da perna do pino {eps*100:.2f} % - maximo 1,00")
    exigir(abs(pl["rasgo_h"] - pn["topo"]) < 1e-9,
           f"rasgo de {pl['rasgo_h']:.2f} nao atravessa o pino de {pn['topo']:.2f}")
    exigir(pl["farpa_d"] > pl["furo_d"] > pl["haste_d"],
           "a farpa nao retem: diametros fora de ordem")

    # ---- estacao do carregador (TP4056) ----
    e = estacao_carregador()
    ex0, ey0, ex1, ey1 = e["envelope"]

    # 1. Contra cada botao: folga no plano OU em z, como a placa fazia.
    for b in BOTOES:
        d = math.hypot(max(ex0 - b["x"], 0.0, b["x"] - ex1),
                       max(ey0 - b["y"], 0.0, b["y"] - ey1)) - b["flange"] / 2
        dz = e["z_topo_corpo"] - b["abaixo"]
        exigir(d >= 2.0 or dz >= 2.0,
               f"carregador a {d:.2f} mm do botao {b['nome']} no plano e "
               f"{dz:.2f} mm em z - minimo 2,00")

    # 2. Tudo dentro da cavidade, a 1,00 da parede. A cavidade e convexa,
    #    entao basta conferir os cantos do envelope e do alivio.
    cav = silhueta(CORPO_PAR)
    ay_, ax_ = e["alivio"]
    cantos = ([(ex0, ey0), (ex1, ey0), (ex1, ey1), (ex0, ey1)]
              + [(e["x_usb"] + sx * ax_ / 2, e["yc"] + sy * ay_ / 2)
                 for sx in (-1, 1) for sy in (-1, 1)])
    for p in cantos:
        g = _dist_poligono(p, cav) * (1 if M.dentro(p, cav) else -1)
        exigir(g >= 1.0, f"berco do carregador a {g:.2f} mm da parede do "
                         f"corpo - minimo 1,00")

    # 3. Contra as colunas de inserto.
    for i, (cx, cy) in enumerate(fix, 1):
        d = math.hypot(max(ex0 - cx, 0.0, cx - ex1),
                       max(ey0 - cy, 0.0, cy - ey1)) - COL_D / 2
        exigir(d >= 2.0, f"berco do carregador a {d:.2f} mm da coluna {i} - "
                         f"minimo 2,00")

    # 4. A janela passa a capa do plugue, nao so o conector.
    jy, jx = e["janela"]
    cy_, cx_ = e["capa"]
    exigir(jy >= cy_ + 0.6 and jx >= cx_ + 0.6,
           f"janela {jy:.2f} x {jx:.2f} nao passa a capa do plugue "
           f"{cy_:.2f} x {cx_:.2f} com 0,30 por lado")

    # 5. O conector presumido tem margem dentro da janela.
    sobra = min((jy - e["usb_l"]) / 2, (jx - e["usb_h"]) / 2)
    exigir(sobra >= 1.0, f"conector sobra so {sobra:.2f} mm dentro da "
                         f"janela - minimo 1,00")

    # 6. As pontas da placa apoiam na chapa: e ela que leva o puxao.
    apoio = (e["larg"] - jy) / 2
    exigir(apoio >= 1.5, f"a placa apoia so {apoio:.2f} mm em cada ponta da "
                         f"janela - minimo 1,50")

    # 7. Deformacao da coluna ao encaixar.
    exigir(e["eps"] <= 0.010, f"deformacao da coluna do berco "
                              f"{e['eps']*100:.2f} % - maximo 1,00")

    # 8. A garra retem, e a entrada sobe do raso para o fundo.
    gs = [g for g, _ in e["degraus"]]
    exigir(e["cobre"] > 0 and all(0 < g < e["prof_canal"] for g in gs)
           and gs == sorted(set(gs)),
           f"a garra nao retem: cobre {e['cobre']:.2f} mm da placa, "
           f"degraus {gs}")

    # 9. Simetria em y: a tampa e modelada espelhada (spec, secao 2.2).
    exigir(abs(e["y"] - CX_A / 2) < 1e-9,
           f"berco em y = {e['y']:.2f}: a tampa e modelada espelhada e tudo "
           f"nela tem de ser simetrico em y = {CX_A / 2:.2f}")

    if msgs:
        raise AssertionError("projeto inconsistente:\n  - " + "\n  - ".join(msgs))

    return dict(folga_capas=folga, L_tampa=L, sw=k,
                placa=dict(centro=(PLACA["x"], PLACA["y"]),
                           z_topo=z_placa, eps=eps, pinos=pn),
                carregador=e)


# =====================================================================
# 1. Corpo (fundido: painel + corpo)
# =====================================================================

def corpo():
    """
    Peca fundida: painel + corpo.

    z = 0 e a face EXTERNA dos botoes, que e a face que encosta na MESA. Essa
    e a unica orientacao possivel - de boca para baixo o painel teria de fazer
    ponte sobre 170 x 122, e de lado tudo vira balanco. E e o que torna o
    painel liso obrigatorio: qualquer rebaixo nele seria teto no ar.

        z = 0,00 .. 0,50    alivio da boca dos furos (pe de elefante)
        z = 0,50 .. 8,00    painel
        z = 8,00 .. 63,00   cavidade, paredes e colunas

    A parede de tras carrega a ESTACAO DA CHAVE, o unico furo da caixa com
    eixo HORIZONTAL. No trecho x [55, 84] ela deixa de ser parede e vira
    chapa plana com furo: tres 'face_vertical' e dois 'tubo', em vez de
    'parede'.
    """
    S = M.Solido("corpo")
    ext = silhueta()
    fix = pontos_fixacao()
    cav = M.subtrair_discos(silhueta(CORPO_PAR),
                            [(x, y, COL_D / 2, SEG_MEDIO) for x, y in fix])

    k = estacao_chave()
    xa, xb = k["x_face"]
    # no trecho da chave a parede deixa de ser parede: vira chapa plana com
    # furo, e quem emite e 'face_vertical'. 'entalhar' com perfil vazio apaga
    # os vertices de densificacao do trecho, deixando UMA aresta - que e o que
    # a face vertical vai compartilhar, sem junta em T.
    ext = M.entalhar(ext, CX_A, xb, xa, [])
    cav = M.entalhar(cav, k["y_cav"], xb, xa, [])

    # cada furo aparece duas vezes: o alivio (boca) e o furo util
    bar = [M.circulo(b["x"], b["y"], D_BARRIL / 2, SEG_BARRIL) for b in BOTOES]
    bar_al = [M.circulo(b["x"], b["y"], (D_BARRIL + FOLGA_ALIVIO) / 2, SEG_BARRIL)
              for b in BOTOES]
    led, led_al = [], []
    for b in BOTOES:
        for x, y in leds(b):
            led.append(M.circulo(x, y, D_LED / 2, SEG_PEQ))
            led_al.append(M.circulo(x, y, (D_LED + FOLGA_ALIVIO) / 2, SEG_PEQ))
    ins = [M.circulo(x, y, D_INSERTO / 2, SEG_PEQ) for x, y in fix]
    z_ins = CORPO_H - PROF_INSERTO

    # ---- faces horizontais ----
    S.face(ext, bar_al + led_al, 0.0, cima=False)          # face dos botoes
    for a, f in zip(bar_al + led_al, bar + led):
        S.coroa(f, a, REB_ALIVIO, cima=False)              # fundo do alivio
        S.parede(a, 0.0, REB_ALIVIO, fora=False)
        S.parede(f, REB_ALIVIO, PAIN_ESP, fora=False)
    S.face(cav, bar + led, PAIN_ESP, cima=True)            # piso da cavidade
    S.face(ext, [cav] + ins, CORPO_H, cima=True)           # assento da tampa
    for c in ins:
        S.face(c, [], z_ins, cima=True)                    # fundo do inserto
        S.parede(c, z_ins, CORPO_H, fora=False)

    # ---- paredes ----
    # 'faixa' em vez de 'parede': o trecho [xa, xb] da parede de tras fica de
    # fora, porque quem fecha aquele pedaco e a estacao da chave, abaixo.
    S.faixa(M.trecho(ext, (xa, CX_A), (xb, CX_A)), 0.0, CORPO_H)
    S.faixa(M.trecho(list(reversed(cav)), (xb, k["y_cav"]), (xa, k["y_cav"])),
            PAIN_ESP, CORPO_H)

    # ---- estacao da chave ----
    c_reb = M.circulo(k["x"], k["z"], k["d_rebaixo"] / 2, SEG_MEDIO)
    c_fur = M.circulo(k["x"], k["z"], k["d_furo"] / 2, SEG_MEDIO)
    anel = lambda c, y: [(p[0], y, p[1]) for p in c]

    ret_ext = [(xa, 0.0), (xb, 0.0), (xb, CORPO_H), (xa, CORPO_H)]
    ret_cav = [(xa, PAIN_ESP), (xb, PAIN_ESP), (xb, CORPO_H), (xa, CORPO_H)]

    S.face_vertical(ret_ext, [c_fur], k["y_face"], frente=True)
    S.face_vertical(ret_cav, [c_reb], k["y_cav"], frente=False)
    S.face_vertical(c_reb, [c_fur], k["y_reb"], frente=False)
    S.tubo(anel(c_reb, k["y_cav"]), anel(c_reb, k["y_reb"]), inverter=False)
    S.tubo(anel(c_fur, k["y_reb"]), anel(c_fur, k["y_face"]), inverter=False)

    A = M.area_assinada
    a_ext, a_cav = A(ext), A(cav)
    esperado = (
        (a_ext - sum(A(c) for c in bar_al + led_al)) * REB_ALIVIO
        + (a_ext - sum(A(c) for c in bar + led)) * (PAIN_ESP - REB_ALIVIO)
        + (a_ext - a_cav) * (CORPO_H - PAIN_ESP)
        - 6 * A(ins[0]) * PROF_INSERTO
        - A(c_reb) * k["prof_reb"]
        - A(c_fur) * k["parede"])
    return S, esperado


# =====================================================================
# 2. Tampa de servico
# =====================================================================

def tampa():
    """
    z = 0 e a face EXTERNA (rebaixo dos parafusos), que vai na mesa; os pinos
    da perfboard crescem para cima a partir de z = TAMPA_ESP.

    Imprime com os pinos PARA CIMA. O rebaixo Ø6,50 sobre o furo Ø3,40 fica
    voltado para baixo, mas sao 1,55 mm radiais sobre um vao de 6,50 - nao
    pede suporte.
    """
    S = M.Solido("tampa")
    ext = silhueta()
    fix = pontos_fixacao()
    pl, pn = PLACA, pinos_placa()

    pas = [M.circulo(x, y, D_PASSAGEM / 2, SEG_PEQ) for x, y in fix]
    cbo = [M.circulo(x, y, D_REBAIXO / 2, SEG_PEQ) for x, y in fix]

    # perfil do pino, de baixo para cima: (raio, z base, z topo)
    hf = pl["rasgo_w"] / 2
    raios = ([(pl["ombro_d"] / 2, pn["z"][0], pn["z"][1]),
              (pl["haste_d"] / 2, pn["z"][1], pn["z"][2]),
              (pl["farpa_d"] / 2, pn["z"][2], pn["z"][3])]
             + [(d / 2, pn["z"][3 + i], pn["z"][4 + i])
                for i, (d, _) in enumerate(pl["guia"])])

    # A corda de TODAS as secoes cai na mesma reta. Sem estes vertices extras
    # a secao larga teria uma aresta unica ali onde a estreita tem tres, e a
    # malha abriria na emenda. Derivar a lista dos proprios raios mantem as
    # duas coisas casadas se o perfil mudar.
    ys = [math.sqrt(r * r - hf * hf) for r, _, _ in raios]

    def perna_em(cx, cy, r, lado):
        return [(x + cx, y + cy)
                for x, y in M.perna(r, hf, SEG_PEQ, lado, ys)]

    def degrau_em(cx, cy, r_int, r_ext, lado):
        return [(x + cx, y + cy)
                for x, y in M.degrau_da_perna(r_int, r_ext, hf, SEG_PEQ,
                                              lado, ys)]

    bases = [perna_em(cx, cy, raios[0][0], lado)
             for cx, cy in pn["centros"] for lado in (1, -1)]

    # ---- chapa ----
    S.face(ext, cbo, 0.0, cima=False)
    for p, c in zip(pas, cbo):
        S.coroa(p, c, REB_TAMPA, cima=False)
        S.parede(c, 0.0, REB_TAMPA, fora=False)
        S.parede(p, REB_TAMPA, TAMPA_ESP, fora=False)
    S.face(ext, pas + bases, TAMPA_ESP, cima=True)
    S.parede(ext, 0.0, TAMPA_ESP, fora=True)

    # ---- pinos ----
    for cx, cy in pn["centros"]:
        for lado in (1, -1):
            for i, (r, z0, z1) in enumerate(raios):
                S.parede(perna_em(cx, cy, r, lado),
                         TAMPA_ESP + z0, TAMPA_ESP + z1, fora=True)
                if i + 1 < len(raios):
                    r_prox = raios[i + 1][0]
                    if r_prox < r:          # afina: face exposta para cima
                        S.face(degrau_em(cx, cy, r_prox, r, lado), [],
                               TAMPA_ESP + z1, cima=True)
                    else:                   # engorda: face exposta para baixo
                        S.face(degrau_em(cx, cy, r, r_prox, lado), [],
                               TAMPA_ESP + z1, cima=False)
            S.face(perna_em(cx, cy, raios[-1][0], lado), [],
                   TAMPA_ESP + raios[-1][2], cima=True)

    A = M.area_assinada
    v_meia = sum(abs(A(M.perna(r, hf, SEG_PEQ, 1, ys))) * (z1 - z0)
                 for r, z0, z1 in raios)
    esperado = ((A(ext) - 6 * A(cbo[0])) * REB_TAMPA
                + (A(ext) - 6 * A(pas[0])) * (TAMPA_ESP - REB_TAMPA)
                + 8 * v_meia)
    return S, esperado


# =====================================================================

PECAS = [("caixa-corpo", corpo, CORPO_H),
         ("caixa-tampa", tampa, TAMPA_ESP)]


def main():
    info = conferir_projeto()
    print(f"silhueta {CX_L:.0f} x {CX_A:.0f} x R{CX_R:.0f}  "
          f"mesa {MESA[0]:.0f} x {MESA[1]:.0f} (A1 mini)")
    print(f"folga livre entre as capas   {info['folga_capas']:.2f} mm")
    print(f"parafuso tampa M3 x {info['L_tampa']:.0f}")
    for b in BOTOES:
        print(f"botao {b['nome']:9s} capa {b['capa']:.1f}  flange {b['flange']:.1f}  "
              f"apertado {PAIN_ESP:.1f} (max {b['esp_max']})")
    e = info["sw"]
    print(f"chave {e['modelo']}  parede y={CX_A:.0f}  x={e['x']:.1f}  z={e['z']:.1f}")
    print(f"  furo Ø{e['d_furo']:.2f}  rebaixo Ø{e['d_rebaixo']:.1f} "
          f"prof {e['prof_reb']:.2f}  parede local {e['parede']:.2f}  "
          f"atras {e['atras']:.1f}")
    pl = info["placa"]
    print(f"placa centro {pl['centro']}  topo z={pl['z_topo']:.2f}  "
          f"deformacao da perna {pl['eps']*100:.2f} %")
    print()

    total = 0.0
    for nome, fn, h in PECAS:
        S, esperado = fn()
        vol = S.conferir(esperado, tol_rel=1e-9)
        total += vol
        M.salvar_3mf(f"{nome}.3mf", S, titulo=nome)
        M.salvar_stl(f"{nome}.stl", S)
        print(f"{nome:14s} {len(S.v):6d} vertices {len(S.t):6d} triangulos  "
              f"{vol/1000:8.2f} cm3  altura {h:.0f} mm")
    print(f"{'solido total':14s} {'':21s}{total/1000:14.2f} cm3")


if __name__ == "__main__":
    main()
