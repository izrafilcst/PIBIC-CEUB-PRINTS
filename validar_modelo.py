#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conferencia dos .3mf da caixa - PIBIC UniCEUB.
Autor: Rafael Alves de Sousa Costa.

gerar_modelo_3mf.py ja confere a malha ANTES de gravar. Este script confere o
que saiu do arquivo, que e coisa diferente: indice de vertice truncado,
precisao perdida no '%.6g', zip mal formado. E o que o slicer vai ler.

Cada peca passa por:
  estanqueidade    toda aresta em exatamente 2 triangulos
  orientacao       volume por divergencia > 0
  mesa             contorno dentro do envelope da A1 mini
  furos            diametro de cada furo medido na secao, contra o esperado
  parede           menor espessura de material no plano medio

Uso:  python validar_modelo.py
"""

import math
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict

import gerar_modelo_3mf as P

NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"

falhas = 0


def ok(cond, texto, detalhe=""):
    global falhas
    if not cond:
        falhas += 1
    print(f"  [{'ok ' if cond else 'FALHA'}] {texto}"
          + (f"   {detalhe}" if detalhe else ""))


def ler_3mf(caminho):
    root = ET.fromstring(zipfile.ZipFile(caminho).read("3D/3dmodel.model"))
    assert root.get("unit") == "millimeter", "unidade do 3MF nao e milimetro"
    o = root.find(NS + "resources").find(NS + "object")
    m = o.find(NS + "mesh")
    V = [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
         for v in m.find(NS + "vertices")]
    T = [(int(t.get("v1")), int(t.get("v2")), int(t.get("v3")))
         for t in m.find(NS + "triangles")]
    return V, T


def topologia(V, T):
    assert all(0 <= i < len(V) for t in T for i in t), "indice de vertice fora da faixa"
    cont = defaultdict(int)
    for i, j, k in T:
        for a, b in ((i, j), (j, k), (k, i)):
            cont[(a, b) if a < b else (b, a)] += 1
    return sum(1 for c in cont.values() if c != 2)


def volume(V, T):
    s = 0.0
    for i, j, k in T:
        a, b, c = V[i], V[j], V[k]
        s += (a[0] * (b[1] * c[2] - c[1] * b[2])
              - b[0] * (a[1] * c[2] - c[1] * a[2])
              + c[0] * (a[1] * b[2] - b[1] * a[2]))
    return s / 6.0


def secao(V, T, z):
    """Segmentos da interseccao da malha com o plano z."""
    segs = []
    for tri in T:
        Pt = [V[i] for i in tri]
        pts = []
        for i in range(3):
            a, b = Pt[i], Pt[(i + 1) % 3]
            if (a[2] - z) * (b[2] - z) < 0:
                t = (z - a[2]) / (b[2] - a[2])
                pts.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
            elif abs(a[2] - z) < 1e-9:
                pts.append((a[0], a[1]))
        pts = list(dict.fromkeys([(round(x, 6), round(y, 6)) for x, y in pts]))
        if len(pts) == 2:
            segs.append(tuple(pts))
    return segs


def diametro(segs, cx, cy, d_esp, banda=1.5):
    """
    Diametro do furo centrado em (cx,cy), medido nos pontos da secao que caem
    numa banda em volta do raio esperado.

    A banda nao e complacencia: sem ela a medida pega o que estiver por perto -
    o contorno externo da peca, o furo de LED vizinho - e devolve um numero
    grande que nao e diametro de nada. Fora da banda o furo e dado como nao
    encontrado, que e o diagnostico correto para um diametro grosseiramente
    errado. A conferencia fina do tamanho fica com o volume analitico do
    gerador; aqui se confere que o furo existe, esta redondo e esta no lugar.
    """
    r_esp = d_esp / 2
    rs = [math.hypot(x - cx, y - cy) for s in segs for x, y in s]
    rs = [r for r in rs if abs(r - r_esp) < banda]
    if len(rs) < 8:
        return None
    # o furo e um poligono INSCRITO: os vertices estao sobre o circulo real,
    # entao o raio verdadeiro e o maximo, nunca a media
    return 2 * max(rs)


def travessia(segs, x0, y_min=0.0, tol=1e-6):
    """
    Onde a reta vertical x = x0 corta a secao, listado em y crescente.

    E a medida certa para a estacao do interruptor: la a secao muda com z, e
    o que interessa nao e diametro nenhum, e ONDE COMECA E ONDE ACABA o
    material ao longo da espessura da parede. Dois pontos, parede cheia;
    nenhum, parede vazada naquela altura.

    A regra e SEMIABERTA - conta o cruzamento quando x0 esta em [ax, bx) ou
    em [bx, ax) - e nao o cruzamento estrito. Sem isso a medida erra sempre
    que x0 cai em cima de um vertice, e ele cai: a secao de uma parede
    retangular parte no meio da diagonal dos dois triangulos, ou seja
    exatamente no ponto medio da aresta, que e onde qualquer sonda escrita
    como media de duas cotas vai parar. A regra semiaberta conta uma vez o
    contorno que atravessa e nenhuma o que so encosta.
    """
    ys = []
    for (ax, ay), (bx, by) in segs:
        if (ax <= x0 < bx) or (bx <= x0 < ax):
            ys.append(ay + (x0 - ax) / (bx - ax) * (by - ay))
    return sorted(y for y in ys if y >= y_min)


def largura_do_vao(segs, y0, tol=1e-6):
    """Maior intervalo SEM material na aresta y = y0 da secao, e onde fica."""
    xs = sorted({round(x, 6) for s in segs for x, y in s if abs(y - y0) <= tol})
    if len(xs) < 2:
        return None, None
    a, b = max(zip(xs, xs[1:]), key=lambda p: p[1] - p[0])
    return b - a, (a + b) / 2


def dist_ate_poligono(p, poly):
    melhor = float("inf")
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx +
                                                   (p[1] - a[1]) * dy) / L2))
        melhor = min(melhor, math.hypot(p[0] - (a[0] + t * dx),
                                        p[1] - (a[1] + t * dy)))
    return melhor


def conferir(nome, arquivo, altura, furos_esperados):
    print(f"\n{arquivo}")
    V, T = ler_3mf(arquivo)
    ok(topologia(V, T) == 0, "estanque - toda aresta em 2 triangulos")
    vol = volume(V, T)
    ok(vol > 0, "normais para fora", f"volume {vol/1000:.2f} cm3")

    xs = [p[0] for p in V]
    ys = [p[1] for p in V]
    zs = [p[2] for p in V]
    larg, prof, alt = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
    ok(larg <= P.MESA[0] and prof <= P.MESA[1] and alt <= P.MESA[2],
       "cabe na mesa da A1 mini",
       f"{larg:.2f} x {prof:.2f} x {alt:.2f} em {P.MESA[0]:.0f} x "
       f"{P.MESA[1]:.0f} x {P.MESA[2]:.0f}")
    ok(abs(alt - altura) < 1e-6, f"altura {altura:.2f} mm", f"medida {alt:.4f}")
    ok(abs(larg - P.CX_L) < 1e-6 and abs(prof - P.CX_A) < 1e-6,
       f"silhueta {P.CX_L:.0f} x {P.CX_A:.0f}")

    for z, cx, cy, d_esp, rotulo in furos_esperados:
        d = diametro(secao(V, T, z), cx, cy, d_esp)
        ok(d is not None and abs(d - d_esp) < 0.02, rotulo,
           f"esperado {d_esp:.2f}  medido {d:.3f}" if d else "furo nao achado")


def conferir_interruptor(V, T):
    """
    A estacao do interruptor, lida do arquivo.

    Nao da para conferir por diametro nem por bounding box: o berco esta
    inteiro DENTRO da silhueta, e o unico furo que ele abre para fora tem
    6 x 3 mm. Confere-se por travessia - a lista de onde comeca e onde acaba
    o material ao longo da espessura da parede, em pontos escolhidos para
    passar um por cada feicao.
    """
    e = P.estacao()
    print("\ncaixa-corpo.3mf - estacao do interruptor")

    yf, yb, yr, yc = e["y_face"], e["y_bolsa"], e["y_res"], e["y_cav"]
    xr0, xr1 = e["x_res"]
    xb0, xb1 = e["x_bolsa"]
    zb0, zb1 = e["z_bolsa"]

    sondas = [
        # x, z, y esperados, o que a sonda prova
        # no eixo da haste nao sobra material NENHUM: bolsa por dentro e
        # rasgo por fora se encontram, e e por ai que a haste sai
        (e["x"], e["z"], [], "no eixo da haste a parede esta vazada de lado a lado"),
        (e["x"], zb0 / 2, [yr, yf], "abaixo da bolsa o ressalto e macico"),
        (e["x"], (zb1 + e["z_topo"]) / 2, [yr, yf],
         "acima da bolsa o ressalto e macico"),
        (e["x"], e["z_topo"] + 3.0, [yc, yf],
         "acima do ressalto volta a parede de {:.2f}".format(P.CORPO_PAR)),
        ((xb0 + e["x_rasgo"][0]) / 2, e["z"], [yb, yf],
         "ao lado do rasgo sobra o fundo de {:.2f}".format(e["fundo"])),
        ((xr0 + xb0) / 2, e["z"], [yr, yf], "flanco da bolsa e macico"),
        ((xb1 + xr1) / 2, e["z"], [yr, yf], "flanco oposto tambem"),
        (xr1 + 1.0, e["z"], [yc, yf], "fora do ressalto a parede e a normal"),
    ]
    for x, z, esp, texto in sondas:
        m = travessia(secao(V, T, z), x, y_min=yr - 1.0)
        bate = len(m) == len(esp) and all(abs(a - b) < 0.01 for a, b in zip(m, esp))
        ok(bate, f"x={x:.2f} z={z:.2f}: {texto}",
           "esperado y " + " e ".join(f"{v:.2f}" for v in esp) +
           "   medido " + (" e ".join(f"{v:.2f}" for v in m) if m else "nada"))

    segs = secao(V, T, e["z"])
    larg, centro = largura_do_vao(segs, yf)
    ok(larg is not None and abs(larg - e["rasgo_l"]) < 0.01
       and abs(centro - e["x"]) < 0.01,
       f"rasgo na face externa: {e['rasgo_l']:.2f} centrado em {e['x']:.2f}",
       f"medido {larg:.3f} centrado em {centro:.3f}" if larg else "nao achado")

    larg, centro = largura_do_vao(secao(V, T, (zb0 + P.INTERRUPTOR['z']) / 2), yr)
    ok(larg is not None and abs(larg - e["bolsa_l"]) < 0.01
       and abs(centro - e["x"]) < 0.01,
       f"boca da bolsa: {e['bolsa_l']:.2f} centrada em {e['x']:.2f}",
       f"medida {larg:.3f} centrada em {centro:.3f}" if larg else "nao achada")

    # o ressalto nao pode encostar em coluna nenhuma
    g = min(math.hypot(max(xr0 - cx, 0.0, cx - xr1), max(yr - cy, 0.0, cy - yf))
            - P.COL_D / 2 for cx, cy in P.pontos_fixacao())
    ok(g >= 2.0, "ressalto livre das 6 colunas", f"folga minima {g:.2f} mm")

    # e tem de caber no trecho reto da parede, senao sai obliquo
    ok(xr0 >= P.CX_R and xr1 <= P.CX_L - P.CX_R,
       f"ressalto no trecho reto da parede [{P.CX_R:.2f}, {P.CX_L-P.CX_R:.2f}]",
       f"ocupa [{xr0:.2f}, {xr1:.2f}]")


def main():
    fix = P.pontos_fixacao()
    bv, bg = P.BOTOES

    # --- painel ---
    f = []
    for b in (bv, bg):
        z_meio = (P.PAIN_ESP - b["rebaixo"]) / 2
        f.append((z_meio, b["x"], b["y"], P.D_BARRIL,
                  f"barril M24 do botao {b['nome']}: Ø{P.D_BARRIL:.2f}"))
        f.append((P.PAIN_ESP - b["rebaixo"] / 2, b["x"], b["y"],
                  b["capa"] + P.FOLGA_CAPA,
                  f"rebaixo da capa {b['nome']}: Ø{b['capa']+P.FOLGA_CAPA:.2f}"))
        f.append((z_meio, *P.leds(b)[0], P.D_LED,
                  f"furo de LED do botao {b['nome']}: Ø{P.D_LED:.2f}"))
    f.append((1.0, *fix[0], P.D_PASSAGEM, f"passagem M3: Ø{P.D_PASSAGEM:.2f}"))
    f.append((P.PAIN_ESP - 1.0, *fix[0], P.D_REBAIXO,
              f"rebaixo da cabeca: Ø{P.D_REBAIXO:.2f}"))
    conferir("painel", "caixa-painel.3mf", P.PAIN_ESP, f)

    # --- corpo ---
    f = [(P.CORPO_H - 1.0, *fix[0], P.D_INSERTO,
          f"inserto no topo: Ø{P.D_INSERTO:.2f}"),
         (1.0, *fix[0], P.D_INSERTO, f"inserto na base: Ø{P.D_INSERTO:.2f}")]
    conferir("corpo", "caixa-corpo.3mf", P.CORPO_H, f)

    # Parede do corpo no plano medio: menor distancia entre o contorno da
    # cavidade e o contorno externo. Nao da para medir num x escolhido a dedo -
    # nos seis pontos de fixacao a coluna avanca sobre a cavidade e ali a
    # "parede" tem 11 mm. As colunas so ACRESCENTAM material, entao o minimo
    # sobre todo o perimetro e a parede nominal, e e o numero que decide se um
    # interruptor de encaixe (2 a 5 mm de painel) serve na face frontal.
    V, T = ler_3mf("caixa-corpo.3mf")
    ext = P.silhueta()
    pts = {p for s in secao(V, T, P.CORPO_H / 2) for p in s}
    # o corte separa em dois lacos: o externo cai sobre 'ext' (distancia ~0) e
    # o da cavidade fica a 4 mm ou mais. 1,0 mm separa os dois com folga de
    # sobra para os dois lados, sem depender da precisao do arquivo.
    cav = [p for p in pts if dist_ate_poligono(p, ext) > 1.0]
    par = min(dist_ate_poligono(p, ext) for p in cav) if cav else None
    ok(par is not None and abs(par - P.CORPO_PAR) < 0.05,
       f"parede do corpo {P.CORPO_PAR:.2f} mm (minimo do perimetro)",
       f"medida {par:.3f} em {len(cav)} pontos da cavidade" if par else "nao medida")

    conferir_interruptor(V, T)

    # --- tampa ---
    f = [(1.0, *fix[0], P.D_PASSAGEM, f"passagem M3: Ø{P.D_PASSAGEM:.2f}"),
         (P.TAMPA_ESP - 1.0, *fix[0], P.D_REBAIXO,
          f"rebaixo da cabeca: Ø{P.D_REBAIXO:.2f}")]
    conferir("tampa", "caixa-tampa.3mf", P.TAMPA_ESP, f)

    print()
    if falhas:
        print(f"{falhas} conferencia(s) falharam")
        sys.exit(1)
    print("todas as conferencias passaram")


if __name__ == "__main__":
    main()
