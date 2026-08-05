# Lista de materiais — PIBIC-CEUB

Levantada a partir da geometria real dos `.3mf` do repositório (215 × 120 mm,
6 pontos de fixação M3, 2 furos Ø26, 9 furos Ø10) e da documentação da caixa.

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
| 1 | Adafruit **Massive Arcade Button 100 mm** — #1185 verm. / #1187 branco / #1188 verde | ✅ | vai no furo Ø26 em (65 ; 60) |
| 1 | Adafruit **Large Arcade Button 60 mm** — #1190 verm. / #1192 branco / #1193 verde | ✅ | vai no furo Ø26 em (170 ; 60) |
| 2 | Microswitch de arcade NO, sobressalente | ✅ | é a peça que morre primeiro num controle de impacto |

> **Não compre porca M24.** Ela vem com o botão, junto com o microswitch e o
> LED interno com resistor embutido. Comprar avulso é desperdício — e porca
> M24 avulsa é cara e difícil de achar no diâmetro/passo certo.

---

## 2. Fixação da tampa (6 pontos)

**Decidido: M3 × 6, mantendo o modelo como está.**

| Qtd | Item | Status | Observação |
|---|---|---|---|
| 6 | Parafuso **M3 × 6 ISO 7380**, cabeça abaulada, sextavado interno 2,0 mm | ✅ | |
| 6 | **Inserto roscado de latão M3**, Ø externo 4,6 × **4,0** mm | ✅ | 4,0 e não 5,0 — ver abaixo |
| — | *alternativa sem inserto:* 6 × porca M3 DIN 934 em bolso sextavado | ❓ | 5,5 mm entre faces × 2,4 de espessura; exige redesenhar o pilar |

Confere com o furo de **5,00 mm** já modelado (z 60 a 65):

```
penetração = 6,00 − (4,00 − 2,00) = 4,00 mm
folga no fundo = 5,00 − 4,00      = 1,00 mm   ✔
```

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

**Estimativa de filamento**, dos volumes reais das malhas:

```
painel (Body1)   214,37 cm3
corpo  (Body2)   309,04 cm3
tampa  (Body3)    92,22 cm3
                 ──────────
sólido           615,63 cm3
```

A 4 perímetros e 30 % de preenchimento giroide, a densidade efetiva fica em
torno de 50 % → **≈ 308 cm³ ≈ 391 g**. Some refugo e uma peça refeita:
**compre 1 kg**.

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

~~Profundidade do furo do inserto~~ — **resolvido: M3 × 6**, modelo mantido.

Os itens ✅ podem ser comprados hoje sem risco de sobrar.
