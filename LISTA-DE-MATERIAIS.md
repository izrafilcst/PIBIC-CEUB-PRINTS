# Lista de materiais — PIBIC-CEUB

> **Revisão A1 mini + botões embutidos.** Levantada a partir da geometria real
> dos `.3mf` gerados por `gerar_modelo_3mf.py` — **178 × 130 mm**, 6 colunas de
> fixação com inserto nas **duas** pontas, 2 furos Ø26, 9 furos Ø10, 2 rebaixos
> de assento de capa. Substitui o levantamento de 215 × 120 feito para a
> Creality K1C.
>
> O que mudou para a compra: **12 insertos** em vez de 6, e **dois**
> comprimentos de parafuso em vez de um.

Legenda da coluna **Status**:

| | |
|---|---|
| ✅ | definido, pode comprar |
| ⚠️ | precisa de uma confirmação sua antes de comprar |
| ❓ | depende de decisão de projeto ainda não tomada |

---

## 1. Botões

| Qtd | Item | Status | Observação |
|---|---|---|---|
| 1 | Adafruit **Massive Arcade Button 100 mm** — #1185 verm. / #1187 branco / #1188 verde | ✅ | furo Ø26 em (56 ; 65), rebaixo Ø99,30 × 8,00 |
| 1 | Adafruit **Large Arcade Button 60 mm** — #1190 verm. / #1192 branco / #1193 verde | ✅ | furo Ø26 em (140 ; 65), rebaixo Ø61,60 × 5,00 |
| 2 | Microswitch de arcade NO, sobressalente | ✅ | é a peça que morre primeiro num controle de impacto |

> **Não compre porca M24.** Ela vem com o botão, junto com o microswitch e o
> LED interno com resistor embutido. Comprar avulso é desperdício — e porca
> M24 avulsa é cara e difícil de achar no diâmetro/passo certo.

**Os botões agora entram meio embutidos.** O flange assenta no fundo de um
rebaixo, e o conjunto inteiro desce por essa profundidade:

| Botão | Capa | Rebaixo | Fica para fora | Painel apertado pela porca |
|---|---|---|---|---|
| 100 mm | Ø98,5 × 17,5 | 8,00 | 9,50 | 8,00 |
| 60 mm | Ø60,8 × 10,0 | 5,00 | 5,00 | 11,00 |

O trecho apertado pela porca é a espessura do painel **menos** o rebaixo — os
dois ficam dentro dos 12,70 mm máximos que o botão admite. Foi por isso que o
painel passou de 10 para 16 mm.

> **Antes de imprimir o painel inteiro, imprima um corpo de prova** com os dois
> rebaixos (Ø99,30 e Ø61,60) e teste a capa. A folga de 0,80 diametral é
> estimada; é ajuste aparente, e um painel de 16 mm errado custa ~6 h de
> impressão.

> **Anti-rotação:** o pino do flange não está cotado na documentação do
> fabricante, então o rebaixo é liso. Meça no botão físico se quiser abrir o
> rasgo, ou mantenha a cola quente.

---

## 2. Fixação — 6 colunas, inserto nas duas pontas

As 6 colunas do corpo são **passantes** e levam furo Ø4,20 × 5,00 em cada
ponta: em cima prendem o painel, embaixo a tampa. No modelo do Fusion só a
tampa tinha fixação e o painel não tinha como prender — as três peças não
fechavam uma caixa.

| Qtd | Item | Status | Observação |
|---|---|---|---|
| 6 | Parafuso **M3 × 16 ISO 7380**, cabeça abaulada, sextavado interno 2,0 mm | ✅ | **painel**, que tem 16 mm |
| 6 | Parafuso **M3 × 6 ISO 7380**, cabeça abaulada, sextavado interno 2,0 mm | ✅ | **tampa**, que tem 4 mm |
| **12** | **Inserto roscado de latão M3**, Ø externo 4,6 × **4,0** mm | ✅ | 4,0 e não 5,0 — ver abaixo. **Dobrou:** 2 por coluna |
| — | *alternativa sem inserto:* 12 × porca M3 DIN 934 em bolso sextavado | ❓ | 5,5 mm entre faces × 2,4 de espessura; exige redesenhar a coluna |

As duas contas fecham no mesmo furo de 5,00 mm e no mesmo inserto de 4,0:

```
painel   penetração     = 16,00 − (16,00 − 4,00) = 4,00 mm
         folga no fundo = 5,00 − 4,00            = 1,00 mm   ✔
tampa    penetração     =  6,00 − ( 4,00 − 2,00) = 4,00 mm
         folga no fundo = 5,00 − 4,00            = 1,00 mm   ✔
```

O rebaixo do painel tem 4,00 mm de profundidade (o da tampa, 2,00) justamente
para o parafuso cair num comprimento de catálogo. Com rebaixo de 2,00 o painel
pediria um M3 × 18, que quase não se acha.

> **Peça o inserto de 4,0 mm, não o de 5,0.** Um inserto de 5,0 num furo de
> 5,00 não deixa vazio nenhum embaixo, e o PETG derretido na instalação não
> tem para onde ir — ele sobe em volta e empurra o inserto para fora, o que
> impede a tampa de assentar. Com 4,0 sobra 1,00 mm de folga no fundo, e o
> M3 × 6 penetra exatamente os 4,0 mm do latão.
>
> Se só achar o de 5,0 mm, dá para usar: aprofunde o furo para 6,00 mm no
> Fusion antes de imprimir.

---

## 3. Fiação e solda

| Qtd | Item | Status | Observação |
|---|---|---|---|
| 1 | **Estanho 60/40 com fluxo, Ø0,8 mm** — rolo de 100 g | ✅ | 0,8 mm é o diâmetro certo para eletrônica; 1,0 mm já é grosso demais para LED |
| 1 | **Fluxo** em pasta ou caneta | ✅ | o do estanho não basta para faston e fio estanhado |
| 3 m | **Cabo flexível estanhado 22 AWG** (0,33 mm²), 2 cores | ✅ | sinal dos microswitches |
| 2 m | **Cabo flexível estanhado 20 AWG** (0,5 mm²), 2 cores | ❓ | só se houver LEDs externos — ver seção 4 |
| 4 | **Terminal faston fêmea pré-isolado 4,8 mm** (0,187") | ⚠️ | 2 por botão (COM + NO). **Meça o terminal do switch antes** — parte dos microswitches de arcade usa 2,8 mm. Compre 10: crimpagem estraga um ou dois |
| 1 | Espaguete termorretrátil, sortido Ø2 e Ø3 mm | ✅ | |
| 1 | Conector destacável (JST-XH ou Dupont) entre tampa e painel | ✅ | sem isso você solda e dessolda toda vez que abrir a caixa |
| 1 | Malha dessoldadora ou sugador | ✅ | |

---

## 4. Iluminação — os 9 furos Ø10

❓ **Item inteiro pendente de confirmação.** O modelo tem **9 furos Ø10,00
passantes** no painel: 6 num círculo de furação Ø63 em volta do botão de
100 mm e 3 num Ø42 em volta do de 60 mm. Eles caem **sob as capas**, fora do
flange do corpo do botão.

A posição é compatível com **LED Ø10 mm iluminando a capa por baixo** — e isso
resolveria justamente a queixa da sua documentação, de que o LED interno
"concentra o brilho no centro devido à profundidade da carcaça". Mas **a
geometria não prova a função**. Se for isso:

| Qtd | Item | Observação |
|---|---|---|
| 9 | LED Ø10 mm difuso | cor à sua escolha |
| 9 | Suporte/aro plástico para LED Ø10 | opcional, melhora o acabamento no furo |
| 9 | Resistor limitador | valor depende da tensão de alimentação e do Vf do LED |

Se **não** for iluminação, me diga o que são e eu recoto o desenho.

---

## 5. Eletrônica de controle

❓ **Ainda não há decisão registrada no projeto.** Duas rotas usuais:

| Item | Quando escolher |
|---|---|
| **Arduino Pro Micro** (ATmega32U4) | vira joystick/teclado USB nativo, sem driver — rota mais curta |
| **Raspberry Pi Pico** | mais I/O e mais barato, mas exige firmware HID |

Em qualquer uma: 1 × cabo USB e 1 × passa-cabo ou recorte na caixa (**não
existe no modelo atual** — o corpo é fechado nos 4 lados).

---

## 6. Consumíveis de impressão

| Qtd | Item | Status |
|---|---|---|
| 1 kg | **Filamento PETG** | ✅ |
| 1 | Bastão de cola escolar | ✅ agente de **soltura** no PEI, não de adesão |
| 1 | Álcool isopropílico | ✅ |

**Estimativa de filamento**, dos volumes reais das malhas (`validar_modelo.py`):

```
caixa-painel     233,93 cm3     era 214,37 - engordou de 10 para 16 mm
caixa-corpo      130,26 cm3     era 309,04 - parede de 10 para 4 mm
caixa-tampa       81,64 cm3     era  92,22 - silhueta menor
                 ──────────
sólido           445,83 cm3     era 615,63
```

A 4 perímetros e 30 % de preenchimento giroide, a densidade efetiva fica em
torno de 50 % → **≈ 223 cm³ ≈ 283 g**. Some refugo, o corpo de prova dos
rebaixos e uma peça refeita: **compre 1 kg**.

A caixa saiu **mais leve** que a versão de 215 × 120, apesar do painel mais
grosso: a parede de 4 mm economiza mais do que os 6 mm de painel custam.

### Impressão na A1 mini

As três peças têm 178 × 130 mm numa mesa de 180 × 180 — sobra **1,0 mm de cada
lado em X**. Isso tem consequência prática:

- **Centralize na mesa** e confira antes de fatiar. Não é margem para
  improvisar posição.
- **Não use brim.** Não cabe. O projeto já trata o PETG no PEI como problema de
  *soltura*, não de aderência, então o brim não faz falta — mas conte com isso
  na hora de fatiar, e não descubra depois.
- Nenhuma das três peças pede suporte, desde que impressas na orientação
  modelada: painel com a face interna na mesa (os rebaixos abrem para cima),
  corpo em pé, tampa com o rebaixo para cima.

---

## 7. Ferramentas

| Item | Para quê | Status |
|---|---|---|
| **Ferro de solda com controle de temperatura** | 220–240 °C para os insertos; sem controle você queima o PETG | ✅ |
| Ponta cônica dedicada aos insertos | latão sujo estraga a ponta de eletrônica | ✅ |
| Chave allen 2,0 mm | cabeça dos M3 ISO 7380 | ✅ |
| **Paquímetro** | resolve as duas pendências abertas do projeto | ✅ |
| Alicate de crimpar faston | crimpar torto é o defeito nº 1 em fiação de arcade | ✅ |
| Pistola de cola quente | alívio de tração dos fios e anti-rotação dos botões | ✅ |

---

## O que trava a compra agora

1. **Largura do terminal do microswitch** — 4,8 mm ou 2,8 mm. Define o faston.
2. **Função dos 9 furos Ø10** — define se entram LEDs, suportes e resistores.
3. **Microcontrolador** — define cabo, conector e recorte de saída na caixa.

~~Profundidade do furo do inserto~~ — **resolvido: M3 × 6 na tampa e M3 × 16 no
painel**, os dois no mesmo inserto de 4,0 mm.

~~Fixação do painel~~ — **resolvido:** as colunas viraram passantes e recebem
inserto nas duas pontas.

Os itens ✅ podem ser comprados hoje sem risco de sobrar.

## Ainda por confirmar na bancada (não trava compra)

- **Folga do rebaixo da capa (0,80 diametral).** Estimada. Corpo de prova antes
  do painel.
- **Posição do pino anti-rotação do flange.** Não cotada pelo fabricante.
