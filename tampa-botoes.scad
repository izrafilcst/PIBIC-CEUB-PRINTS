// =====================================================================
// TAMPA COM ENCAIXE PARA BOTOES DE ARCADE - PIBIC-CEUB
//
// Botao VERMELHO (domo 98,5 mm) a esquerda
// Botao VERDE   (arcade 60,8 mm) a direita
// Folga livre entre as bordas das capas: 40 mm
//
// Ambos os botoes usam rosca M24 x P2, portanto o furo do painel e
// IDENTICO para os dois. O que muda e apenas o espaco livre ao redor.
//
// ANTES DE IMPRIMIR: rode o gabarito-tolerancia.scad e ajuste
// 'folga_m24' abaixo com o valor que encaixou.
// =====================================================================

// ---------------------- COTAS DOS BOTOES (dos desenhos) --------------
// Botao vermelho (domo 100 mm)
BV_cap_d      = 98.5;   // diametro externo do domo
BV_anel_d     = 87.8;   // anel interno
BV_altura     = 17.5;   // altura acima do painel

// Botao verde (arcade 60 mm)
BG_cap_d      = 60.8;   // diametro externo da capa/bezel
BG_flange_d   = 37.7;   // flange do corpo que APOIA sobre o painel
BG_flange_h   = 4.4;    // espessura desse flange
BG_altura     = 10.0;   // altura acima do painel
BG_barril     = 30.5;   // comprimento abaixo do painel
BG_total      = 62.4;   // altura total do conjunto

// Rosca comum aos dois
ROSCA_d       = 24.0;   // M24 nominal

// ---------------------- FIXACAO DA TAMPA -----------------------------
// 6x parafuso M3 x 10 ISO 7380 (cabeca abaulada, dk 5,7 / k 1,65) em
// inserto de latao M3 (D ext 4,6 x 5,0) instalado a quente na caixa.
PARAF_d_pass  = 3.4;    // ISO 273 media para M3
PARAF_d_reb   = 6.5;    // rebaixo: folga sobre dk 5,7 + entrada da chave
PARAF_h_reb   = 2.0;    // > k 1,65, entao a cabeca fica submersa
PARAF_recuo   = 8.0;    // do centro do parafuso ate a borda da placa

// ---------------------- PARAMETROS AJUSTAVEIS ------------------------

folga_m24     = 24.7;   // <<< AJUSTE COM O RESULTADO DO GABARITO
folga_borda   = 40;     // mm - espaco livre entre as bordas das capas
espessura     = 4;      // mm - espessura da tampa
margem        = 5;      // mm - borda de material ao redor das capas
                        //      5 => placa 209,3 x 108,5, cabe na Creality K1C
                        //      (220x220) com ~5,3 mm de folga por lado

mostrar_botoes   = false;  // preview dos botoes montados (nao exporta)
gravar_contorno  = false;  // grava o contorno das capas na face superior
prof_gravacao    = 0.4;

$fn = 128;              // NAO reduzir: afeta o diametro real dos furos

// ---------------------- GEOMETRIA DERIVADA ---------------------------

// Centro-a-centro = soma dos raios das capas + folga livre desejada
dist_centros = BV_cap_d/2 + BG_cap_d/2 + folga_borda;   // = 119.65

largura = BV_cap_d/2 + dist_centros + BG_cap_d/2 + 2*margem;
altura  = BV_cap_d + 2*margem;

cx_vermelho = margem + BV_cap_d/2;
cx_verde    = cx_vermelho + dist_centros;
cy          = altura/2;

// Os 6 parafusos: cantos + meio das bordas longas. Nao ha posicao possivel
// ao lado do botao vermelho: a capa de 98,5 ocupa de y=5 a y=103,5, ou seja,
// toda a altura util da placa.
xs_paraf = [PARAF_recuo, largura/2, largura - PARAF_recuo];
ys_paraf = [PARAF_recuo, altura  - PARAF_recuo];

echo(str("Distancia entre centros: ", dist_centros, " mm"));
echo(str("Placa: ", largura, " x ", altura, " x ", espessura, " mm"));
echo(str("Material sob a cabeca do parafuso: ", espessura - PARAF_h_reb, " mm"));
// Profundidade que o furo do inserto precisa ter na CAIXA (peca separada):
echo(str("Furo do inserto na caixa: D", 4.2, " x ",
         10 - (espessura - PARAF_h_reb) + 1, " mm de profundidade"));

// ---------------------- CONSTRUCAO -----------------------------------

module tampa() {
    difference() {
        cube([largura, altura, espessura]);

        // furo da rosca M24 - botao vermelho
        translate([cx_vermelho, cy, -1])
            cylinder(h = espessura + 2, d = folga_m24);

        // furo da rosca M24 - botao verde
        translate([cx_verde, cy, -1])
            cylinder(h = espessura + 2, d = folga_m24);

        // 6x furo de fixacao com rebaixo para a cabeca abaulada.
        // O rebaixo abre na face de CIMA (z = espessura).
        for (px = xs_paraf, py = ys_paraf) {
            translate([px, py, -1])
                cylinder(h = espessura + 2, d = PARAF_d_pass);
            translate([px, py, espessura - PARAF_h_reb])
                cylinder(h = PARAF_h_reb + 1, d = PARAF_d_reb);
        }

        if (gravar_contorno) {
            translate([cx_vermelho, cy, espessura - prof_gravacao])
                difference() {
                    cylinder(h = prof_gravacao + 1, d = BV_cap_d);
                    translate([0,0,-1])
                        cylinder(h = prof_gravacao + 3, d = BV_cap_d - 1.2);
                }
            translate([cx_verde, cy, espessura - prof_gravacao])
                difference() {
                    cylinder(h = prof_gravacao + 1, d = BG_cap_d);
                    translate([0,0,-1])
                        cylinder(h = prof_gravacao + 3, d = BG_cap_d - 1.2);
                }
        }
    }
}

// ---------------------- PREVIEW DOS BOTOES ---------------------------

module preview_vermelho() {
    color("red", 0.55) {
        translate([0,0,espessura])
            cylinder(h = BV_altura, d1 = BV_cap_d, d2 = BV_anel_d*0.55);
        translate([0,0,-32]) cylinder(h = 32, d = ROSCA_d);
    }
}

module preview_verde() {
    color("green", 0.55) {
        translate([0,0,espessura])
            cylinder(h = BG_flange_h, d = BG_flange_d);
        translate([0,0,espessura + BG_flange_h])
            cylinder(h = BG_altura - BG_flange_h, d1 = BG_cap_d, d2 = 51.9);
        translate([0,0,-BG_barril]) cylinder(h = BG_barril, d = ROSCA_d);
    }
}

tampa();

if (mostrar_botoes) {
    translate([cx_vermelho, cy, 0]) preview_vermelho();
    translate([cx_verde,    cy, 0]) preview_verde();
}
