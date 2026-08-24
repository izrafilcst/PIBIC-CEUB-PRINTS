# Lista de materiais — PIBIC-CEUB

> **Revisão A1 mini + botões embutidos.** Levantada a partir da geometria real
> dos `.3mf` gerados por `gerar_modelo_3mf.py` — **178 × 130 mm**, 6 colunas de
> fixação com inserto **só no topo**, 2 furos Ø26 e 9 furos Ø10 no painel liso.
> Substitui o levantamento de 215 × 120 feito para a Creality K1C.
>
> O que mudou para a compra nesta revisão: **6 insertos** em vez de 12, **um**
> comprimento de parafuso em vez de dois, **PLA** em vez de PETG, a chave
> **KCD1** no lugar da SS12D00G4, e uma **perfboard 7 × 9**.

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
| 1 | Adafruit **Massive Arcade Button 100 mm** — #1185 verm. / #1187 branco / #1188 verde | ✅ | furo Ø26 em (56 ; 65), com alívio de boca Ø27,00 × 0,50 |
| 1 | Adafruit **Large Arcade Button 60 mm** — #1190 verm. / #1192 branco / #1193 verde | ✅ | furo Ø26 em (140 ; 65), mesmo alívio |
| 2 | Microswitch de arcade NO, sobressalente | ✅ | é a peça que morre primeiro num controle de impacto |

> **Não compre porca M24.** Ela vem com o botão, junto com o microswitch e o
> LED interno com resistor embutido. Comprar avulso é desperdício — e porca
> M24 avulsa é cara e difícil de achar no diâmetro/passo certo.

**Os botões assentam direto na face, sem rebaixo.** O painel é liso.

| Botão | Capa | Fica para fora | Painel apertado pela porca | Desce na cavidade |
|---|---|---|---|---|
| 100 mm | Ø98,5 × 17,5 | 17,50 | **8,00** | 33,00 |
| 60 mm | Ø60,8 × 10,0 | 10,00 | **8,00** | 44,40 |

Os 8,00 mm são a espessura do painel, e são os mesmos nos dois botões — ficam
dentro dos 12,70 mm máximos que o botão admite e acima dos 5,00 mínimos.

> **Os botões meio embutidos foram abandonados nesta revisão.** Com o painel
> fundido no corpo, a peça só imprime com a face dos botões na mesa, e ali
> qualquer rebaixo vira teto no ar. Não há corpo de prova de rebaixo para
> imprimir, e a folga de 0,80 diametral da capa deixou de existir.

> **Anti-rotação:** o pino do flange não está cotado pelo fabricante. Com o
> painel liso não há rebaixo onde abrir rasgo; se o botão girar, resolva com
> cola quente entre o flange e a face.

**A coluna "desce na cavidade"** é o que decide a folga da perfboard: o botão
verde desce 44,40 mm dos 55,00 de cavidade, e é por isso que a placa foge dele
em x. Ver seção 5b.

---

## 2. Fixação — 6 colunas, inserto só no topo

As 6 colunas do corpo levam furo Ø4,20 × 5,00 **só na ponta de cima**, onde a
tampa prende. Eram 12 insertos porque o painel também parafusava; o painel
virou parte do corpo e **a metade de baixo da ferragem desapareceu**.

| Qtd | Item | Status | Observação |
|---|---|---|---|
| 6 | Parafuso **M3 × 6 ISO 7380**, cabeça abaulada, sextavado interno 2,0 mm | ✅ | **tampa**, que tem 4 mm |
| **6** | **Inserto roscado de latão M3**, Ø externo 4,6 × **4,0** mm | ✅ | eram 12 |
| — | *alternativa sem inserto:* 6 × porca M3 DIN 934 em bolso sextavado | ❓ | 5,5 mm entre faces × 2,4 de espessura; exige redesenhar a coluna |

~~6 × Parafuso M3 × 16~~ — **não compre.** Eram os do painel.

As duas contas fecham no mesmo furo de 5,00 mm e no mesmo inserto de 4,0:

```
tampa    penetração     =  6,00 − ( 4,00 − 2,00) = 4,00 mm
         folga no fundo = 5,00 − 4,00            = 1,00 mm   ✔
```

O rebaixo da tampa tem 2,00 mm de profundidade justamente para o parafuso cair
num comprimento de catálogo: `(4,00 − 2,00) + 4,00 = 6,00`.

> **Peça o inserto de 4,0 mm, não o de 5,0.** Um inserto de 5,0 num furo de
> 5,00 não deixa vazio nenhum embaixo, e o PLA derretido na instalação não
> tem para onde ir — ele sobe em volta e empurra o inserto para fora, o que
> impede a tampa de assentar. Com 4,0 sobra 1,00 mm de folga no fundo, e o
> M3 × 6 penetra exatamente os 4,0 mm do latão.
>
> Se só achar o de 5,0 mm, dá para usar: aumente `PROF_INSERTO` para 6,00 em
> `gerar_modelo_3mf.py` e regere. Não há Fusion no caminho — a geometria toda
> sai daquele arquivo.

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

## 5. Interruptor geral — chave gangorra redonda KCD1

| Qtd | Item | Status | Observação |
|---|---|---|---|
| **1** | **Chave gangorra redonda KCD1**, snap-in, furo de painel Ø20 | ⚠ | 3 terminais faston 4,80; 6 A / 250 V CA |
| 3 | Terminal faston fêmea 4,80 mm | ⚠ | crimpado nos fios |

Vai **encaixada** na parede de trás do corpo (`y = 130`), eixo em `x = 69,50`
e `z = 35,00`. Prancha **PIBIC-CX-04**. A parede é rebaixada por dentro
(Ø25,00 × 2,00) para sobrar 2,00 mm locais — a chave é snap-in e as garras
querem painel fino. **Não há cola nem parafuso.**

Cotas do componente, de desenho cotado do fabricante:

| Cota | Valor |
|---|---|
| Corpo que atravessa o painel | Ø19,80 ± 0,20 |
| Aro visível | Ø23,00 ± 0,20 |
| Corpo atrás do painel | Ø19,30 |
| Profundidade do corpo | 17,80 ± 0,30 |
| Total atrás do painel | 25,70 ± 0,30 |
| Terminais | 3, passo 7,00, vão 14,00, lâmina 4,80 × 0,80 |

> **⚠ O que o desenho do fabricante NÃO cota** é a faixa de espessura de painel
> que as garras aceitam. O projeto arbitrou 2,00 mm, que é o valor seguro da
> família. Meça a garra com o paquímetro antes de imprimir o corpo.

> **Corrente.** 6 A / 250 V CA é folgado para chavear a alimentação de um
> microcontrolador ou uma fita de LED. A chave anterior, a SS12D00G4, dava
> 0,3 A / 30 V CC e era o gargalo.

**A SS12D00G4 saiu do projeto**, e com ela o berço colado e a cola quente que
o prendia. Se você já comprou a deslizante, ela não serve: o berço não existe
mais.

---

### 5b. Perfboard e o encaixe dela

| Qtd | Item | Status | Observação |
|---|---|---|---|
| 1 | **Perfboard 7 × 9 cm** genérica, furos de canto Ø3,0 | ⚠ | 4 furos de canto são requisito |

Prende na tampa por **4 pinos farpados, sem parafuso**. A placa assenta no
ombro Ø6,00 e trava sob a farpa Ø3,60.

> **⚠ Ø3,00 do furo e recuo de 3,50 da borda são PRESUMIDOS.** Meça a placa
> antes de imprimir a tampa — errar o recuo põe os 4 pinos no lugar errado de
> uma vez. Os dois valores são parâmetro no topo de `gerar_modelo_3mf.py`.

## 6. Eletrônica de controle

❓ **Ainda não há decisão registrada no projeto.** Duas rotas usuais:

| Item | Quando escolher |
|---|---|
| **Arduino Pro Micro** (ATmega32U4) | vira joystick/teclado USB nativo, sem driver — rota mais curta |
| **Raspberry Pi Pico** | mais I/O e mais barato, mas exige firmware HID |

Em qualquer uma: 1 × cabo USB e 1 × passa-cabo ou recorte na caixa (**não
existe no modelo atual**). O furo Ø20,20 da parede de trás é da chave KCD1 e
fica cheio por ela. Sugestão: mesma parede, entre `x = 94` e `x = 123`, que é o
resto do trecho reto livre — a chave ocupa até x = 82.

---

## 7. Consumíveis de impressão

| Qtd | Item | Status |
|---|---|---|
| 1 kg | **Filamento PLA** | ✅ |
| 1 | Álcool isopropílico | ✅ |

**Estimativa de filamento**, dos volumes reais das malhas (`validar_modelo.py`):

```
caixa-corpo      279,13 cm3     painel + corpo fundidos
caixa-tampa       81,98 cm3     com os 4 pinos da perfboard
                 ──────────
sólido           361,11 cm3     era 445,83   (-19 %)
```

A 4 perímetros e 20 % de preenchimento giroide, a densidade efetiva fica em
torno de 50 % → **≈ 181 cm³ ≈ 224 g** de PLA (densidade 1,24 g/cm³). Some
refugo e uma peça refeita: **compre 1 kg**.

A caixa saiu **muito mais leve**: a parede de 4 mm, o painel liso de 8 mm e a
fusão das duas peças tiraram 19 % do sólido.

### Impressão na A1 mini

As duas peças têm 178 × 130 mm numa mesa de 180 × 180 — sobra **1,0 mm de cada
lado em X**. Isso tem consequência prática:

- **Centralize na mesa** e confira antes de fatiar. Não é margem para
  improvisar posição.
- **Não use brim.** Não cabe. Em PLA ele não faz falta — mas conte com isso na
  hora de fatiar, e não descubra depois.
- **Nenhuma das duas peças pede suporte**, desde que impressas na orientação
  modelada: o corpo com a **face dos botões na mesa**, a tampa com os **pinos
  para cima**.
- A primeira camada do corpo é a face **visível** dos botões. A textura da mesa
  transfere direto para ela.

---

## 8. Ferramentas

| Item | Para quê | Status |
|---|---|---|
| **Ferro de solda com controle de temperatura** | 220–240 °C para os insertos; sem controle você queima o PLA | ✅ |
| Ponta cônica dedicada aos insertos | latão sujo estraga a ponta de eletrônica | ✅ |
| Chave allen 2,0 mm | cabeça dos M3 ISO 7380 | ✅ |
| **Paquímetro** | resolve as duas pendências abertas do projeto | ✅ |
| Alicate de crimpar faston | crimpar torto é o defeito nº 1 em fiação de arcade | ✅ |
| Pistola de cola quente | alívio de tração dos fios e anti-rotação dos botões (entre o flange e a face) | ✅ |

---

## O que trava a compra agora

1. **Largura do terminal do microswitch** — 4,8 mm ou 2,8 mm. Define o faston.
2. **Função dos 9 furos Ø10** — define se entram LEDs, suportes e resistores.
3. **Microcontrolador** — define cabo, conector e recorte de saída na caixa.
4. **Ø do furo e recuo da borda da perfboard** — presumidos em 3,00 e 3,50.
   Definem a posição dos 4 pinos da tampa; errar põe os quatro errados de uma
   vez.

~~Profundidade do furo do inserto~~ — **resolvido: M3 × 6 na tampa**, inserto de
4,0 mm.

~~Fixação do painel~~ — **resolvido de outro jeito:** o painel virou parte do
corpo e deixou de precisar de fixação.

~~Nº de posições do interruptor~~ — **resolvido:** a SS12D00G4 saiu do projeto.

Os itens ✅ podem ser comprados hoje sem risco de sobrar.

## Ainda por confirmar na bancada (não trava compra)

- **Faixa de espessura de painel das garras da KCD1.** O desenho do fabricante
  não cota. O projeto arbitrou 2,00 mm. Meça a garra antes de imprimir o corpo.
- **Ø e recuo do furo da perfboard.** Presumidos em 3,00 e 3,50.
- **Posição do pino anti-rotação do flange.** Não cotada pelo fabricante.

~~Folga do rebaixo da capa~~ — **sem objeto:** o rebaixo de capa deixou de
existir quando o painel ficou liso.
