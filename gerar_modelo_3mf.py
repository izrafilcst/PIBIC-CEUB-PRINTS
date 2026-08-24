#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelo parametrico da caixa - PIBIC UniCEUB.
Autor: Rafael Alves de Sousa Costa.

FONTE UNICA da geometria das tres pecas. Escreve

  caixa-painel.3mf   painel dos botoes, 178 x 130 x 16
  caixa-corpo.3mf    corpo,             178 x 130 x 55
  caixa-tampa.3mf    tampa de servico,  178 x 130 x 4

e os .stl correspondentes. Os desenhos tecnicos saem de gerar_desenhos_3mf.py,
que LE estes arquivos e mede a malha - nenhuma cota e digitada duas vezes.

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

2. BOTOES MEIO EMBUTIDOS. Cada botao ganhou um rebaixo circular na face
   externa do painel, com profundidade igual a METADE da altura da capa. O
   flange do botao assenta no fundo do rebaixo, entao o conjunto inteiro
   desce por esse valor:

     vermelho  capa 17,5 alta  ->  rebaixo 8,0  ->  9,5 mm para fora
     verde     capa 10,0 alta  ->  rebaixo 5,0  ->  5,0 mm para fora

   O rebaixo desconta da espessura que a porca M24 aperta. Por isso o painel
   engordou de 10 para 16 mm: o trecho apertado no botao vermelho fica em
   16 - 8 = 8 mm, dentro do maximo de 12,70 mm da especificacao, e sobra
   material para a rosca do barril em vez de faltar.

3. FIXACAO DO PAINEL. O modelo do Fusion tinha os 6 insertos so na ponta da
   tampa; o painel nao tinha como prender no corpo. Aqui as 6 colunas sao
   passantes e recebem inserto nas DUAS pontas - 12 insertos no total.
   Sem isso as tres pecas nao viram uma caixa.

4. PAREDE de 10 para 4 mm, com colunas Ø10 locais nos seis pontos de
   fixacao. Foi o que devolveu o espaco que os 178 mm de silhueta tiraram, e
   de quebra resolve a nota 6 do desenho antigo: interruptor de encaixe
   quer painel de 2 a 5 mm, e 4 mm cai dentro sem rebaixo local.

5. BERCO DO INTERRUPTOR. O corpo ganhou uma estacao para a chave
   deslizante SS12D00G4 na parede y = CX_A, embaixo. E a UNICA parte da
   caixa onde a secao muda com z: tres retangulos encaixados - ressalto,
   bolsa e rasgo - que 'corpo()' resolve por faixas de z.

   O ressalto desce ate z = 0 de proposito. Um bloco solto teria a face de
   baixo em balanco; descendo ate a mesa ele imprime sem uma linha de
   suporte e ainda se apoia na tampa. Sobra um unico trecho sobre o vazio,
   o teto da bolsa, que e uma ponte reta de 12,20 mm.

   As cotas do componente sao NOMINAIS - ver o comentario em INTERRUPTOR.

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
# 'capa'    diametro externo da capa
# 'h_capa'  altura da capa acima do painel quando o flange assenta na face
# 'rebaixo' quanto o conjunto afunda - metade de h_capa, decisao do projeto
# 'led_*'   furos passantes sob a capa, na circunferencia de furacao

BOTOES = [
    dict(nome="vermelho", modelo="Adafruit 1185/1187/1188 - 100 mm",
         x=56.0, y=65.0, capa=98.5, h_capa=17.5, rebaixo=8.0,
         esp_max=12.7, led_n=6, led_r=31.5, led_a0=30.0,
         flange=87.8, abaixo=41.0),
    dict(nome="verde", modelo="Adafruit 1190/1192/1193 - 60 mm",
         x=140.0, y=65.0, capa=60.8, h_capa=10.0, rebaixo=5.0,
         esp_max=12.7, led_n=3, led_r=21.0, led_a0=90.0,
         flange=37.7, abaixo=52.4),
]

D_BARRIL   = 26.0      # passagem do barril M24 (especificacao Adafruit)
D_LED      = 10.0      # furos sob a capa
FOLGA_CAPA = 0.8       # diametral, entre a capa e a parede do rebaixo

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
    folga=0.4,         # diametral - furo deitado fecha mais que furo em pe
    d_rebaixo=25.0,    # rebaixo por dentro, onde as garras trabalham
    parede=2.0,        # parede local que sobra sob o rebaixo
    atras=25.7,        # reserva atras da parede: corpo + terminal
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
SEG_CAPA   = 128
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


def r_rebaixo(b):
    return (b["capa"] + FOLGA_CAPA) / 2


# =====================================================================
# Conferencias de projeto - rodam antes de qualquer malha
# =====================================================================

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

    if msgs:
        raise AssertionError("projeto inconsistente:\n  - " + "\n  - ".join(msgs))

    return dict(folga_capas=folga, L_tampa=L, sw=k,
                placa=dict(centro=(PLACA["x"], PLACA["y"]),
                           z_topo=z_placa, eps=eps, pinos=pn))


# =====================================================================
# 1. Painel dos botoes
# =====================================================================

def painel():
    """
    z = 0 e a face INTERNA (encosta no corpo); z = PAIN_ESP e a face de cima,
    onde ficam os rebaixos das capas e as cabecas dos parafusos.

    Impressao: face interna na mesa. Todo rebaixo abre para cima, entao nao ha
    um unico milimetro de suporte na peca.
    """
    S = M.Solido("painel")
    ext = silhueta()
    fix = pontos_fixacao()

    bv, bg = BOTOES
    z_v = PAIN_ESP - bv["rebaixo"]          # fundo do rebaixo vermelho
    z_g = PAIN_ESP - bg["rebaixo"]          # fundo do rebaixo verde
    z_cb = PAIN_ESP - REB_PAINEL            # fundo do rebaixo dos parafusos
    assert z_v < z_g < z_cb, "a ordem das alturas do painel mudou"

    reb_v = M.circulo(bv["x"], bv["y"], r_rebaixo(bv), SEG_CAPA)
    reb_g = M.circulo(bg["x"], bg["y"], r_rebaixo(bg), SEG_CAPA)
    bar_v = M.circulo(bv["x"], bv["y"], D_BARRIL / 2, SEG_BARRIL)
    bar_g = M.circulo(bg["x"], bg["y"], D_BARRIL / 2, SEG_BARRIL)
    led_v = [M.circulo(x, y, D_LED / 2, SEG_PEQ) for x, y in leds(bv)]
    led_g = [M.circulo(x, y, D_LED / 2, SEG_PEQ) for x, y in leds(bg)]
    pas = [M.circulo(x, y, D_PASSAGEM / 2, SEG_PEQ) for x, y in fix]
    cbo = [M.circulo(x, y, D_REBAIXO / 2, SEG_PEQ) for x, y in fix]

    # --- faces horizontais ---
    S.face(ext, [reb_v, reb_g] + cbo, PAIN_ESP, cima=True)
    S.face(reb_v, [bar_v] + led_v, z_v, cima=True)
    S.face(reb_g, [bar_g] + led_g, z_g, cima=True)
    for p, c in zip(pas, cbo):
        S.coroa(p, c, z_cb, cima=True)
    S.face(ext, [bar_v, bar_g] + led_v + led_g + pas, 0.0, cima=False)

    # --- paredes ---
    S.parede(ext, 0.0, PAIN_ESP, fora=True)
    S.parede(reb_v, z_v, PAIN_ESP, fora=False)
    S.parede(reb_g, z_g, PAIN_ESP, fora=False)
    S.parede(bar_v, 0.0, z_v, fora=False)
    S.parede(bar_g, 0.0, z_g, fora=False)
    for c in led_v:
        S.parede(c, 0.0, z_v, fora=False)
    for c in led_g:
        S.parede(c, 0.0, z_g, fora=False)
    for p, c in zip(pas, cbo):
        S.parede(c, z_cb, PAIN_ESP, fora=False)
        S.parede(p, 0.0, z_cb, fora=False)

    # volume esperado, camada a camada, com as areas dos MESMOS poligonos
    A = M.area_assinada
    a_ext = A(ext)
    a_pas, a_cbo = A(pas[0]), A(cbo[0])
    a_led, a_bar = A(led_v[0]), A(bar_v)
    esperado = (
        (a_ext - 2 * a_bar - 9 * a_led - 6 * a_pas) * (z_v - 0.0)
        + (a_ext - A(reb_v) - a_bar - 3 * a_led - 6 * a_pas) * (z_g - z_v)
        + (a_ext - A(reb_v) - A(reb_g) - 6 * a_pas) * (z_cb - z_g)
        + (a_ext - A(reb_v) - A(reb_g) - 6 * a_cbo) * (PAIN_ESP - z_cb))
    return S, esperado


# =====================================================================
# 2. Corpo
# =====================================================================

def corpo():
    """
    Anel de parede CORPO_PAR com seis colunas Ø COL_D que nascem na parede e
    avancam sobre a cavidade. Cada coluna e passante e leva um furo de inserto
    nas duas pontas: em cima prende o painel, embaixo a tampa.

    A parede y = CX_A ainda carrega a ESTACAO DO INTERRUPTOR, que e o unico
    lugar da caixa onde a secao muda com z. Ela nasce de tres retangulos
    encaixados, todos centrados em INTERRUPTOR['x']:

      ressalto  engrossa a parede por dentro, de z = 0 ate z_topo
      bolsa     vazia o ressalto, e a boca por onde o interruptor entra
      rasgo     atravessa os 2 mm de fundo que sobraram, so para a haste

    O ressalto desce ate z = 0 de proposito. Um bloco solto teria a face de
    baixo em balanco; descendo ate a mesa ele imprime sem uma linha de
    suporte e ainda se apoia na tampa depois de montado. O unico trecho em
    balanco que sobra e o teto da bolsa, uma ponte reta de bolsa_l.
    """
    S = M.Solido("corpo")
    ext = silhueta()
    fix = pontos_fixacao()
    e = estacao()

    xr0, xr1 = e["x_res"]
    xb0, xb1 = e["x_bolsa"]
    xs0, xs1 = e["x_rasgo"]
    yf, yb, yr, yc = e["y_face"], e["y_bolsa"], e["y_res"], e["y_cav"]
    zb0, zb1 = e["z_bolsa"]
    zs0, zs1 = e["z_rasgo"]
    z_topo = e["z_topo"]

    # ---- contornos ----
    # No trecho do rasgo a silhueta perde os vertices de densificacao: aquela
    # aresta passa a ser compartilhada com a face do rasgo, e as duas tem de
    # ser subdivididas igual, senao a malha abre.
    ext = M.entalhar(ext, yf, xs1, xs0, [])

    cav = M.subtrair_discos(silhueta(CORPO_PAR),
                            [(x, y, COL_D / 2, SEG_MEDIO) for x, y in fix])
    cav = M.entalhar(cav, yc, xr1, xr0, [])       # aresta unica sob o ressalto

    # cav_r: cavidade com o ressalto macico (abaixo e acima da bolsa)
    cav_r = M.entalhar(cav, yc, xr1, xr0,
                       [(xr1, yr), (xb1, yr), (xb0, yr), (xr0, yr)])
    # cav_b: cavidade na altura da bolsa - o ressalto aberto ate o fundo
    cav_b = M.entalhar(cav, yc, xr1, xr0,
                       [(xr1, yr), (xb1, yr), (xb1, yb), (xs1, yb),
                        (xs0, yb), (xb0, yb), (xb0, yr), (xr0, yr)])

    ins = [M.circulo(x, y, D_INSERTO / 2, SEG_PEQ) for x, y in fix]
    z_alto = CORPO_H - PROF_INSERTO

    # As faces do berco. Cada uma e a diferenca entre a secao de baixo e a de
    # cima, e por isso repete, vertice a vertice, a subdivisao dos contornos
    # que encosta nela.
    f_bolsa = [(xb0, yr), (xb1, yr), (xb1, yb), (xs1, yb), (xs0, yb), (xb0, yb)]
    f_rasgo = [(xs0, yb), (xs1, yb), (xs1, yf), (xs0, yf)]
    f_res = [(xr0, yr), (xb0, yr), (xb1, yr), (xr1, yr), (xr1, yc), (xr0, yc)]

    # ---- faces horizontais ----
    S.face(ext, [cav] + ins, CORPO_H, cima=True)
    S.face(ext, [cav_r] + ins, 0.0, cima=False)
    S.face(f_bolsa, [], zb0, cima=True)      # fundo do vao da bolsa
    S.face(f_bolsa, [], zb1, cima=False)     # teto da bolsa - a ponte
    S.face(f_rasgo, [], zs0, cima=True)
    S.face(f_rasgo, [], zs1, cima=False)
    S.face(f_res, [], z_topo, cima=True)     # topo do ressalto
    for c in ins:
        S.face(c, [], z_alto, cima=True)         # fundo do furo de cima
        S.face(c, [], PROF_INSERTO, cima=False)  # teto do furo de baixo
        S.parede(c, z_alto, CORPO_H, fora=False)
        S.parede(c, 0.0, PROF_INSERTO, fora=False)

    # ---- paredes ----
    # A secao so muda com z no trecho do berco. Emitir o contorno INTEIRO uma
    # vez por faixa custaria 5 mil triangulos a mais - o corpo dobraria de
    # tamanho por causa de 17 mm de parede. Entao cada contorno sai em duas
    # partes: o trecho LONGE do berco, que vale de z = 0 ao topo e e emitido
    # uma unica vez, e o perfil LOCAL, esse sim faixa por faixa.
    #
    # 'parede(fora=False)' percorre o contorno ao contrario; os perfis locais
    # da cavidade saem ja nessa ordem, senao as normais invertem.
    z_cheio = [0.0, CORPO_H]
    z_rasgo = [0.0, zs0, zs1, CORPO_H]
    z_est = [0.0, zb0, zs0, zs1, zb1, z_topo, CORPO_H]

    longe = M.trecho(ext, (xs0, yf), (xs1, yf))
    S.faixa(longe[1:-1], 0.0, CORPO_H)
    S.costura(longe[0], longe[1], z_rasgo, z_cheio)
    S.costura(longe[-2], longe[-1], z_cheio, z_rasgo)
    S.faixa([(xs1, yf), (xs0, yf)], 0.0, zs0)       # soleira do rasgo
    S.faixa([(xs1, yf), (xs0, yf)], zs1, CORPO_H)   # verga do rasgo

    longe = M.trecho(list(reversed(cav)), (xr1, yc), (xr0, yc))
    S.faixa(longe[1:-1], 0.0, CORPO_H)
    S.costura(longe[0], longe[1], z_est, z_cheio)
    S.costura(longe[-2], longe[-1], z_cheio, z_est)

    loc_r = [(xr0, yc), (xr0, yr), (xb0, yr), (xb1, yr), (xr1, yr), (xr1, yc)]
    loc_b = [(xr0, yc), (xr0, yr), (xb0, yr), (xb0, yb), (xs0, yb),
             (xs1, yb), (xb1, yb), (xb1, yr), (xr1, yr), (xr1, yc)]
    i = loc_b.index((xs0, yb))
    S.faixa(loc_r, 0.0, zb0)                 # ressalto macico, abaixo da bolsa
    S.faixa(loc_b, zb0, zs0)
    S.faixa(loc_b[:i + 1], zs0, zs1)         # no rasgo o fundo da bolsa some
    S.faixa(loc_b[i + 1:], zs0, zs1)
    S.faixa(loc_b, zs1, zb1)
    S.faixa(loc_r, zb1, z_topo)              # ressalto macico, acima da bolsa
    S.faixa([(xr0, yc), (xr1, yc)], z_topo, CORPO_H)   # parede lisa de novo

    S.faixa([(xs0, yb), (xs0, yf)], zs0, zs1)    # flanco esquerdo do rasgo
    S.faixa([(xs1, yf), (xs1, yb)], zs0, zs1)    # flanco direito

    A = M.area_assinada
    a_ins = A(ins[0])
    esperado = (
        (A(ext) - A(cav_r)) * zb0
        + (A(ext) - A(cav_b)) * (zb1 - zb0)
        + (A(ext) - A(cav_r)) * (z_topo - zb1)
        + (A(ext) - A(cav)) * (CORPO_H - z_topo)
        - INTERRUPTOR["rasgo_l"] * INTERRUPTOR["fundo"] * (zs1 - zs0)
        - 2 * (6 * a_ins * PROF_INSERTO))
    return S, esperado


# =====================================================================
# 3. Tampa de servico
# =====================================================================

def tampa():
    """z = 0 encosta no corpo; z = TAMPA_ESP e a face de fora, com o rebaixo."""
    S = M.Solido("tampa")
    ext = silhueta()
    fix = pontos_fixacao()
    pas = [M.circulo(x, y, D_PASSAGEM / 2, SEG_PEQ) for x, y in fix]
    cbo = [M.circulo(x, y, D_REBAIXO / 2, SEG_PEQ) for x, y in fix]
    z_cb = TAMPA_ESP - REB_TAMPA

    S.face(ext, cbo, TAMPA_ESP, cima=True)
    S.face(ext, pas, 0.0, cima=False)
    for p, c in zip(pas, cbo):
        S.coroa(p, c, z_cb, cima=True)
        S.parede(c, z_cb, TAMPA_ESP, fora=False)
        S.parede(p, 0.0, z_cb, fora=False)
    S.parede(ext, 0.0, TAMPA_ESP, fora=True)

    A = M.area_assinada
    esperado = ((A(ext) - 6 * A(pas[0])) * z_cb
                + (A(ext) - 6 * A(cbo[0])) * REB_TAMPA)
    return S, esperado


# =====================================================================

PECAS = [("caixa-painel", painel, PAIN_ESP),
         ("caixa-corpo", corpo, CORPO_H),
         ("caixa-tampa", tampa, TAMPA_ESP)]


def main():
    info = conferir_projeto()
    print(f"silhueta {CX_L:.0f} x {CX_A:.0f} x R{CX_R:.0f}  "
          f"mesa {MESA[0]:.0f} x {MESA[1]:.0f} (A1 mini)")
    print(f"folga livre entre as capas   {info['folga_capas']:.2f} mm")
    print(f"nervura entre os rebaixos    {info['entre_rebaixos']:.2f} mm")
    print(f"parafusos  tampa M3 x {info['L_tampa']:.0f}   "
          f"painel M3 x {info['L_painel']:.0f}")
    for b in BOTOES:
        print(f"botao {b['nome']:9s} rebaixo {b['rebaixo']:.1f}  "
              f"para fora {b['h_capa']-b['rebaixo']:.1f}  "
              f"apertado {PAIN_ESP-b['rebaixo']:.1f} (max {b['esp_max']})")
    e = info["sw"]
    print(f"interruptor {e['modelo']}  parede y={CX_A:.0f}  x={e['x']:.1f}  "
          f"z={e['z']:.1f}")
    print(f"  bolsa {e['bolsa_l']:.2f} x {e['bolsa_h']:.2f} x {e['bolsa_p']:.2f}"
          f"   ressalto {e['res_l']:.2f} avancando {e['saliencia']:.2f}"
          f"   rasgo {e['rasgo_l']:.2f} x {e['rasgo_h']:.2f}"
          f"   haste para fora {e['haste_fora']:.2f}")
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
