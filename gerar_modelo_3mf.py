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
         esp_max=12.7, led_n=6, led_r=31.5, led_a0=30.0),
    dict(nome="verde", modelo="Adafruit 1190/1192/1193 - 60 mm",
         x=140.0, y=65.0, capa=60.8, h_capa=10.0, rebaixo=5.0,
         esp_max=12.7, led_n=3, led_r=21.0, led_a0=90.0),
]

D_BARRIL   = 26.0      # passagem do barril M24 (especificacao Adafruit)
D_LED      = 10.0      # furos sob a capa
FOLGA_CAPA = 0.8       # diametral, entre a capa e a parede do rebaixo

# =====================================================================
# Espessuras
# =====================================================================

PAIN_ESP  = 16.0
CORPO_H   = 55.0
CORPO_PAR = 4.0
TAMPA_ESP = 4.0

# =====================================================================
# Fixacao - 6 colunas, inserto M3 nas duas pontas
# =====================================================================

FIX_INSET   = 6.0      # centro da coluna, medido da face externa
COL_D       = 10.0     # diametro externo da coluna
D_INSERTO   = 4.2      # furo do inserto de latao M3 (Ø ext 4,6 x 4,0)
PROF_INSERTO = 5.0
D_PASSAGEM  = 3.4      # furo de passagem do M3
D_REBAIXO   = 6.5      # rebaixo da cabeca ISO 7380
REB_TAMPA   = 2.0      # profundidade do rebaixo na tampa
REB_PAINEL  = 4.0      # profundidade do rebaixo no painel

# Comprimento de parafuso que cada peca pede:
#   L = (espessura - rebaixo) + penetracao no inserto
PENETRACAO  = 4.0      # = altura util do inserto de 4,0 mm

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
        rr = r_rebaixo(b)
        borda = min(math.dist((b["x"], b["y"]), p) for p in sil) - rr
        exigir(borda > 3.0,
               f"rebaixo do botao {b['nome']} a {borda:.2f} mm da borda")
        for p in leds(b):
            exigir(math.dist((b["x"], b["y"]), p) + D_LED / 2 < rr - 1.0,
                   f"furo Ø{D_LED} do botao {b['nome']} sai do rebaixo")
        exigir(b["capa"] / 2 > D_BARRIL / 2,
               f"capa do botao {b['nome']} menor que o furo do barril")

    # ---- rebaixo contra rebaixo ----
    entre = d - r_rebaixo(bv) - r_rebaixo(bg)
    exigir(entre > 3.0, f"nervura entre os rebaixos {entre:.2f} mm")

    # ---- fixacao livre dos rebaixos ----
    for i, p in enumerate(fix, 1):
        for b in BOTOES:
            g = math.dist(p, (b["x"], b["y"])) - r_rebaixo(b) - D_REBAIXO / 2
            exigir(g > 2.0, f"fixacao {i} a {g:.2f} mm do rebaixo do "
                            f"botao {b['nome']}")
        exigir(min(math.dist(p, q) for q in sil) - D_REBAIXO / 2 > 2.0,
               f"fixacao {i} perto demais da borda")

    # ---- botao: espessura apertada pela porca ----
    for b in BOTOES:
        ap = PAIN_ESP - b["rebaixo"]
        exigir(ap <= b["esp_max"],
               f"botao {b['nome']} aperta {ap:.2f} mm, maximo {b['esp_max']}")
        exigir(ap >= 5.0,
               f"botao {b['nome']} aperta so {ap:.2f} mm - material de menos")
        exigir(b["rebaixo"] < PAIN_ESP - 4.0,
               f"rebaixo do botao {b['nome']} deixa o painel fino demais")

    # ---- parafusos: penetram sem bater no fundo ----
    for nome, esp, reb in (("tampa", TAMPA_ESP, REB_TAMPA),
                           ("painel", PAIN_ESP, REB_PAINEL)):
        L = (esp - reb) + PENETRACAO
        sobra = PROF_INSERTO - PENETRACAO
        exigir(sobra > 0, f"{nome}: parafuso encosta no fundo do furo")
        exigir(esp - reb >= 1.5, f"{nome}: so {esp-reb:.2f} mm sob a cabeca")
        exigir(abs(L - round(L)) < 1e-9, f"{nome}: pede M3 x {L:.2f}, "
                                         f"comprimento fora de catalogo")

    # ---- coluna de inserto contra a parede ----
    exigir(COL_D / 2 > D_INSERTO / 2 + 2.0, "coluna fina demais em volta do inserto")
    exigir(FIX_INSET + COL_D / 2 > CORPO_PAR,
           "coluna nao avanca sobre a cavidade - subtrair_discos vai falhar")
    exigir(FIX_INSET - COL_D / 2 < CORPO_PAR,
           "coluna nao encosta na parede - ficaria solta no meio da cavidade")

    if msgs:
        raise AssertionError("projeto inconsistente:\n  - " + "\n  - ".join(msgs))

    return dict(folga_capas=folga, entre_rebaixos=entre,
                L_tampa=(TAMPA_ESP - REB_TAMPA) + PENETRACAO,
                L_painel=(PAIN_ESP - REB_PAINEL) + PENETRACAO)


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
    """
    S = M.Solido("corpo")
    ext = silhueta()
    fix = pontos_fixacao()

    cav = M.subtrair_discos(silhueta(CORPO_PAR),
                            [(x, y, COL_D / 2, SEG_MEDIO) for x, y in fix])
    ins = [M.circulo(x, y, D_INSERTO / 2, SEG_PEQ) for x, y in fix]
    z_alto = CORPO_H - PROF_INSERTO

    S.face(ext, [cav] + ins, CORPO_H, cima=True)
    S.face(ext, [cav] + ins, 0.0, cima=False)
    for c in ins:
        S.face(c, [], z_alto, cima=True)        # fundo do furo de cima
        S.face(c, [], PROF_INSERTO, cima=False)  # teto do furo de baixo
        S.parede(c, z_alto, CORPO_H, fora=False)
        S.parede(c, 0.0, PROF_INSERTO, fora=False)
    S.parede(ext, 0.0, CORPO_H, fora=True)
    S.parede(cav, 0.0, CORPO_H, fora=False)

    A = M.area_assinada
    anel = A(ext) - A(cav)
    a_ins = A(ins[0])
    esperado = (anel * CORPO_H) - 2 * (6 * a_ins * PROF_INSERTO)
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
