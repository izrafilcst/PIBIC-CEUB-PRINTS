// =====================================================================
// GABARITO DE TOLERANCIA - furo M24 para botoes de arcade em PETG
// PIBIC-CEUB
//
// Objetivo: descobrir empiricamente qual diametro modelado produz o
// encaixe correto da rosca M24 dos dois botoes, compensando a
// contracao do PETG e a sobreposicao de extrusao da sua impressora.
//
// COMO USAR:
//   1. Imprima com EXATAMENTE os mesmos parametros que usara na tampa
//      final (bico, altura de camada, temperatura, fluxo, velocidade).
//   2. Teste a rosca de cada botao em cada furo, do menor para o maior.
//   3. O furo bom e o primeiro em que o botao entra com leve pressao
//      dos dedos, sem folga lateral e sem forcar.
//   4. Anote o valor e use em gerar_modelo_3mf.py (parametro D_BARRIL).
//
// O canto chanfrado marca o furo #1 (o MENOR).
// =====================================================================

// ---------------------- PARAMETROS ----------------------------------

espessura   = 4;                                    // mm - igual ao da tampa final
diametros   = [24.4, 24.6, 24.7, 24.8, 25.0];       // mm - diametros a testar
passo       = 32;                                   // mm - distancia entre centros
largura     = 180;                                  // mm
altura      = 45;                                   // mm
chanfro     = 8;                                    // mm - marca o inicio da sequencia

gravar_texto     = true;   // grava o diametro ao lado de cada furo
prof_gravacao    = 0.6;    // mm
tam_texto        = 5;      // mm

$fn = 128;                 // resolucao dos circulos (nao reduzir: afeta o diametro real)

// ---------------------- CONSTRUCAO ----------------------------------

n   = len(diametros);
x0  = largura/2 - (n-1)*passo/2;   // x do primeiro furo
yc  = altura/2 + 3;                // furos levemente acima do centro (espaco p/ texto)

module placa() {
    linear_extrude(espessura)
        polygon([
            [chanfro, 0],
            [largura, 0],
            [largura, altura],
            [0,       altura],
            [0,       chanfro]
        ]);
}

module furos() {
    for (i = [0 : n-1])
        translate([x0 + i*passo, yc, -1])
            cylinder(h = espessura + 2, d = diametros[i]);
}

module rotulos() {
    for (i = [0 : n-1])
        translate([x0 + i*passo, 6, espessura - prof_gravacao])
            linear_extrude(prof_gravacao + 1)
                text(str(diametros[i]),
                     size = tam_texto,
                     halign = "center",
                     valign = "center",
                     font = "Liberation Sans:style=Bold");
}

difference() {
    placa();
    furos();
    if (gravar_texto) rotulos();
}
