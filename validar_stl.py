#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validacao das malhas geradas por gerar_stl.py - PIBIC-CEUB.

Rode sempre que alterar parametros e regerar os STL. Verifica:

  1. Estanqueidade   - cada aresta pertence a exatamente 2 triangulos.
  2. Orientacao      - cada aresta dirigida aparece uma unica vez, ou seja,
                       as normais sao consistentes e apontam para fora.
  3. Volume          - positivo (normais nao invertidas) e batendo com o
                       calculo analitico independente.
  4. Diametros       - medidos direto na malha.
  5. Rosca           - diametro maior/menor conferidos contra ISO 68-1, e
                       passo/sentido conferidos pela fase das cristas.

Uso:  python validar_stl.py
"""

import math
import struct
from collections import defaultdict

import gerar_stl as G


def ler_stl(caminho):
    with open(caminho, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        return [struct.unpack("<12fH", f.read(50))[3:12] for _ in range(n)]


def topologia(tris):
    Q = 1e6
    k = lambda x, y, z: (round(x * Q), round(y * Q), round(z * Q))
    nao_pareadas = defaultdict(int)
    dirigidas = defaultdict(int)
    vol = 0.0
    xs = ys = zs = None
    for t in tris:
        a, b, c = t[0:3], t[3:6], t[6:9]
        ka, kb, kc = k(*a), k(*b), k(*c)
        for u, v in ((ka, kb), (kb, kc), (kc, ka)):
            nao_pareadas[frozenset((u, v))] += 1
            dirigidas[(u, v)] += 1
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
        for v in (a, b, c):
            if xs is None:
                xs = [v[0], v[0]]; ys = [v[1], v[1]]; zs = [v[2], v[2]]
            xs[0] = min(xs[0], v[0]); xs[1] = max(xs[1], v[0])
            ys[0] = min(ys[0], v[1]); ys[1] = max(ys[1], v[1])
            zs[0] = min(zs[0], v[2]); zs[1] = max(zs[1], v[2])
    abertas = sum(1 for c in nao_pareadas.values() if c != 2)
    invertidas = sum(1 for c in dirigidas.values() if c != 1)
    return abertas, invertidas, vol, (xs, ys, zs)


def area_poligonal(r, n):
    """Area do poligono regular de n lados inscrito no circulo de raio r."""
    return 0.5 * n * r * r * math.sin(2 * math.pi / n)


def area_secao_rosca(rosca, n):
    """
    Area da secao do vazio de um furo roscado, em qualquer altura z.

    E constante em z: para z fixo, quando theta percorre uma volta a fase
    (z - P*theta/2pi) percorre exatamente um passo. Logo a secao e sempre o
    mesmo poligono, apenas girado.
    """
    ang = [2 * math.pi * i / n for i in range(n)]
    rr = [rosca.raio((-rosca.P * a / (2 * math.pi)) % rosca.P) for a in ang]
    s = 0.0
    for i in range(n):
        s += rr[i] * rr[(i + 1) % n]
    return 0.5 * s * math.sin(2 * math.pi / n)


def ok(cond):
    return "OK" if cond else "FALHA"


def bloco(nome, tris, vol_esperado=None):
    ab, inv, vol, (xs, ys, zs) = topologia(tris)
    print(f"\n=== {nome} ===")
    print(f"  triangulos                     : {len(tris)}")
    print(f"  bbox                           : {xs[1]-xs[0]:.2f} x {ys[1]-ys[0]:.2f} "
          f"x {zs[1]-zs[0]:.2f} mm")
    print(f"  arestas abertas                : {ab}  {ok(ab == 0)}")
    print(f"  arestas mal orientadas         : {inv}  {ok(inv == 0)}")
    print(f"  volume da malha                : {vol/1000:.3f} cm3  {ok(vol > 0)}")
    if vol_esperado is not None:
        erro = abs(vol - vol_esperado) / vol_esperado * 100
        print(f"  volume analitico independente  : {vol_esperado/1000:.3f} cm3")
        print(f"  divergencia                    : {erro:.4f} %  {ok(erro < 0.05)}")
    return vol


# ---------------------------------------------------------------------

def checar_passante():
    esp, larg, alt = G.ESP_GABARITO, G.LARG_GAB, G.ALT_GAB
    area = larg * alt - G.CHANFRO ** 2 / 2
    for d in G.DIAM_PASSANTE:
        area -= area_poligonal(d / 2, G.SEG)
    bloco("gabarito-passante.stl", ler_stl("gabarito-passante.stl"), area * esp)

    print("\n  diametros modelados vs. medidos na malha:")
    tris = ler_stl("gabarito-passante.stl")
    pts = {(round(t[i], 6), round(t[i + 1], 6))
           for t in tris for i in (0, 3, 6) if abs(t[i + 2] - esp) < 1e-6}
    xs = G._centros_gabarito(len(G.DIAM_PASSANTE))
    for cx, d in zip(xs, G.DIAM_PASSANTE):
        rr = [math.hypot(x - cx, y - alt / 2) for x, y in pts
              if math.hypot(x - cx, y - alt / 2) < 14]
        print(f"    D{d:>5}  ->  medido {2*max(rr):.4f} mm  {ok(abs(2*max(rr)-d) < 1e-3)}")


def checar_roscado():
    esp, larg, alt = G.ESP_GABARITO, G.LARG_GAB, G.ALT_GAB
    area = larg * alt - G.CHANFRO ** 2 / 2
    roscas = [G.RoscaISO(24.0, 2.0, dl) for dl in G.DELTA_ROSCA]
    for r in roscas:
        area -= area_secao_rosca(r, G.SEG_ROSCA)
    bloco("gabarito-roscado.stl", ler_stl("gabarito-roscado.stl"), area * esp)

    # --- conferencia do perfil contra a norma ---
    r0 = G.RoscaISO(24.0, 2.0, 0.0)
    print("\n  perfil ISO 68-1 para M24 x 2 (delta = 0):")
    tab = {"H": (r0.H, 1.7320508), "D1 menor": (2 * r0.Rmin, 21.835),
           "D2 primitivo": (24 - 0.649519 * 2, 22.701), "D maior": (2 * r0.Rmaj, 24.000)}
    for nome, (calc, ref) in tab.items():
        print(f"    {nome:<14} calculado {calc:.4f}   tabela {ref:.4f}   "
              f"{ok(abs(calc-ref) < 5e-4)}")
    soma = r0.P / 4 + r0.flanco + r0.P / 8 + r0.flanco
    print(f"    soma axial     {soma:.4f} = passo {r0.P:.4f}   {ok(abs(soma-r0.P) < 1e-9)}")

    # --- raios e fase das cristas, medidos na malha ---
    tris = ler_stl("gabarito-roscado.stl")
    xs = G._centros_gabarito(len(G.DELTA_ROSCA))
    print("\n  raios medidos na malha e fase das cristas:")
    for cx, dl, r in zip(xs, G.DELTA_ROSCA, roscas):
        v = set()
        for t in tris:
            for i in (0, 3, 6):
                x, y, z = t[i], t[i + 1], t[i + 2]
                if math.hypot(x - cx, y - alt / 2) < 13.5:
                    v.add((round(x, 6), round(y, 6), round(z, 6)))
        rad = [math.hypot(x - cx, y - alt / 2) for x, y, z in v]
        rmin, rmax = min(rad), max(rad)
        # fase das cristas: deve cair na faixa plana [0, P/4]
        fases = []
        for x, y, z in v:
            rr = math.hypot(x - cx, y - alt / 2)
            if abs(rr - r.Rmin) < 1e-6:
                th = math.atan2(y - alt / 2, x - cx) % (2 * math.pi)
                f = (z - r.P * th / (2 * math.pi)) % r.P
                # o modulo devolve P-epsilon onde deveria devolver 0; traz de volta
                fases.append(f - r.P if f > r.P / 2 else f)
        dentro = all(-1e-6 <= f <= r.P / 4 + 1e-6 for f in fases) if fases else False
        print(f"    delta {dl:.2f}: Rmin {rmin:.4f} (esp. {r.Rmin:.4f}) {ok(abs(rmin-r.Rmin)<1e-4)}"
              f" | Rmaj {rmax:.4f} (esp. {r.Rmaj:.4f}) {ok(abs(rmax-r.Rmaj)<1e-4)}"
              f" | passo/sentido {ok(dentro)}")


if __name__ == "__main__":
    checar_passante()
    checar_roscado()
    print()
