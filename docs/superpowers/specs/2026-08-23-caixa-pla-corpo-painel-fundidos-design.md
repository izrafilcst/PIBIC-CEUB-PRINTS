# Caixa PIBIC em PLA — corpo e painel fundidos, chave KCD1, encaixe de perfboard

Autor: Rafael Alves de Sousa Costa
Data: 23/08/2026
Estado: IMPLEMENTADA. Os números abaixo foram conferidos contra a malha
gerada; onde a implementação corrigiu a spec, a correção está no texto e o
motivo no parágrafo ao lado.

A §3.5 (encaixe da perfboard) e as regras dos pinos foram removidas pela spec 2026-09-24-tampa-tp4056-design.md.

---

## 1. O que muda e por quê

A caixa deixa de ter três peças e passa a ter duas:

| Antes | Agora |
|---|---|
| `caixa-painel` 178 × 130 × 16, parafusada no corpo | **fundida no corpo** |
| `caixa-corpo` 178 × 130 × 55 | `caixa-corpo` 178 × 130 × **63** (corpo + painel) |
| `caixa-tampa` 178 × 130 × 4, parafusada no corpo | mesma função, **ganha o encaixe da perfboard** |
| 12 insertos de latão M3 | **6** |
| Chave deslizante SS12D00G4 em berço colado | **chave gangorra redonda KCD1**, snap-in |
| PETG na Creality K1C | **PLA na Bambu Lab A1 mini** |

Quatro decisões de projeto, todas com o motivo registrado:

1. **Corpo e painel viram uma peça só.** Elimina a junta mais carregada da caixa
   (a que recebe o soco dos botões) e 6 dos 12 insertos.
2. **O painel fica liso** — acabam os rebaixos de 8,0 e 5,0 mm das capas.
3. **A chave vira KCD1 redonda**, presa pelo encaixe próprio, sem cola.
4. **A perfboard prende na tampa por pinos com farpa**, sem parafuso.

---

## 2. A restrição que governa tudo: orientação de impressão

A peça fundida **só pode ser impressa com a face dos botões na mesa**, a caixa
crescendo para cima.

- *Boca para baixo, painel em cima*: o painel teria de fazer ponte sobre um vão
  de 170 × 122 mm. Não existe.
- *De pé, de lado*: 178 × 130 × 63 apoiada numa face lateral põe todo o resto em
  balanço, e a face visível dos botões sai contra o ar.

Consequência direta e não negociável: **qualquer rebaixo na face dos botões é
uma cavidade voltada para a mesa**, ou seja, um teto impresso no ar. Chanfro não
salva: para um cone auto-sustentado de 45° segurar a capa de Ø98,5 a 5 mm de
profundidade, o painel precisaria de `5 + 98,5/2 − 26/2 = 41,25` mm de
espessura. Ou o rebaixo leva suporte, ou deixa de existir.

**Escolha: deixa de existir.** O painel fica liso e a peça inteira imprime com
**zero suporte**. Ganho colateral: o painel cai de 16,0 para 8,0 mm, porque os
16 mm só existiam para sobrar material sob o rebaixo de 8 mm do botão vermelho.

---

## 3. Geometria

### 3.1 Silhueta (inalterada, comum às duas peças)

`178,00 × 130,00`, quatro cantos em `R55,00`. Mesa da A1 mini 180 × 180 →
1,0 mm de cada lado em X. **Sem brim** — não cabe.

### 3.2 Peça 1 — `caixa-corpo` (corpo + painel)

Origem em `z = 0` na face externa dos botões, que é a face que encosta na mesa.

```
z =  0,00 .. 8,00    painel maciço
z =  8,00 .. 63,00   cavidade, paredes e colunas
z = 63,00            face de assento da tampa
```

**Painel — `PAIN_ESP = 8,00`**

- 2 furos de barril `Ø26,00` passantes, em `(56,00 / 65,00)` e `(140,00 / 65,00)`
- 9 furos `Ø10,00` sob as capas: 6 num círculo `Ø63,00` a 60° em volta do
  vermelho (primeiro a 30°), 3 num `Ø42,00` a 120° em volta do verde (primeiro
  a 90°)
- **rebaixo de alívio na boca (`z = 0`) dos 11 furos**: `Ø27,00 × 0,50` nos dois
  barris e `Ø11,00 × 0,50` nos nove furos de LED. Eles nascem na primeira camada
  e o pé de elefante os fecharia; a porca M24 cobre o alívio do barril.
  **É rebaixo reto, não chanfro**, e a razão é a conferência de volume: chanfro
  é cone, cone não tem área de polígono, e `Solido.conferir()` casa o volume da
  malha com o analítico em 1e-9 justamente porque usa as áreas dos polígonos de
  32 lados. Rebaixo reto é prismático e a conferência continua fechando.
  Nenhum furo tinha isso antes porque em PETG nenhum nascia na mesa.
- **nenhum furo de fixação** — o painel não é mais parafusado
- aperto da porca M24 = 8,00 mm, dentro da faixa Adafruit `[5,00 – 12,70]`

**Paredes e colunas**

- parede `4,00` (10 linhas de 0,42)
- 6 colunas `Ø10,00` de `z = 8,00` a `z = 63,00`, nos pontos de fixação
- furo de inserto `Ø4,20 × 5,00` **cego, só no topo**, de `z = 58,00` a `63,00`,
  abrindo para cima — imprime sem ponte
- parafuso `M3 × 6 ISO 7380`: `L = (4,00 − 2,00) + 4,00 = 6,00` ✔

Pontos de fixação (inalterados; `FIX_INSET = 6,00`, `k = (55−6)·√2/2 = 34,648`):

| # | X | Y |
|---|---|---|
| 1 | 89,000 | 6,000 |
| 2 | 89,000 | 124,000 |
| 3 | 20,352 | 20,352 |
| 4 | 157,648 | 20,352 |
| 5 | 20,352 | 109,648 |
| 6 | 157,648 | 109,648 |

### 3.3 Estação da chave KCD1

Cotas do componente, lidas de desenho cotado do fabricante — não de PDF
escaneado. É a diferença em relação ao berço da SS12D00G4, cujas cotas eram
nominais e nunca foram confirmadas.

| Cota | Valor |
|---|---|
| Corpo que atravessa o painel | Ø19,80 ± 0,20 |
| Aro visível (bezel) | Ø23,00 ± 0,20 |
| Corpo atrás do painel | Ø19,30 |
| Profundidade do corpo | 17,80 ± 0,30 |
| Total atrás do painel (corpo + terminal) | 25,70 ± 0,30 |
| Terminais | 3, passo 7,00, vão 14,00 ± 0,10, lâmina 4,80 × 0,80 |

Posição: parede de trás `y = 130`, `x = 69,50`, eixo em `z = 35,00`.

```
y = 126,00 .. 128,00   rebaixo Ø25,00, aberto só para DENTRO
y = 128,00 .. 130,00   parede local de 2,00 mm, furo Ø20,20
y = 130,00             face externa, lisa
```

- **`x = 69,50`** é o meio do único trecho reto livre da parede: de `x = 55`
  (tangência do R55) a `x = 84` (início da coluna central Ø10). O rebaixo Ø25
  ocupa `[57,00 – 82,00]` — 2,00 mm de sobra de cada lado, e 2,28 mm até a
  coluna central. Com Ø26 sobrava 1,80 mm da coluna, abaixo do mínimo de 2,00
  da própria conferência: o rebaixo circular é mais largo que o ressalto
  retangular da SS12D00G4 que ele substitui.
- **`z = 35,00`** põe o rebaixo em `[22,00 – 48,00]`, dentro da faixa útil
  `[8,00 – 63,00]`.
- **Parede local de 2,00 mm** existe porque a chave é snap-in e as garras querem
  painel fino; a parede cheia de 4,00 não entra na faixa.
- **Furo Ø20,20** = corpo real Ø19,80 + 0,40 de folga. Furo de eixo horizontal fecha mais
  que furo em pé em PLA, e o aro Ø23 cobre 1,40 mm radiais — a folga não
  aparece por fora.
- **Nenhum chanfro no furo**, nem por dentro nem por fora. Por dentro é onde as
  garras mordem; por fora seria cone, e vale a mesma restrição de volume
  analítico da nota do painel. Os 0,40 mm de folga já dão a entrada.
- Reserva atrás da parede: 25,70 mm, ocupando até `y = 102,30`, em cavidade
  livre.
- Pontes: o topo do furo (14,28 mm) e o topo do rebaixo (17,68 mm) são pontes
  apoiadas dos dois lados, ambas com só 2,00 mm de profundidade. PLA faz.

### 3.4 Peça 2 — `caixa-tampa`

`178 × 130 × 4,00`, silhueta idêntica.

- 6 × `Ø3,40` passante + rebaixo `Ø6,50 × 2,00` na face externa (inalterado)
- **novo:** 4 pinos de encaixe da perfboard na face interna

**Impressão: pinos para CIMA.** O rebaixo Ø6,50 sobre o furo Ø3,40 fica então
voltado para baixo, mas são 1,55 mm radiais de balanço sobre um vão de 6,50 mm —
não pede suporte.

> **Assimetria conhecida, deixada de propósito.** Os 6 rebaixos Ø6,50 nascem na
> primeira camada, exatamente como os 11 furos do painel — e não ganharam
> alívio de boca. A causa é a mesma e o tratamento é diferente. Foi decisão:
> a cabeça ISO 7380 tem Ø5,70, então sobram 0,40 mm radiais de margem, e o pé
> de elefante teria de comer isso tudo para atrapalhar. Se na prática o
> parafuso não assentar, o alívio é o mesmo `REB_ALIVIO`/`FOLGA_ALIVIO` do
> painel aplicado aqui — mas mexe na geometria e na conta de volume da tampa.

### 3.5 Encaixe da perfboard

Placa genérica **90 × 70 × 1,60**, 4 furos de canto `Ø3,00` a **3,50 mm de cada
borda**. ⚠ **As duas cotas são presumidas** — conferir no paquímetro antes de
imprimir a tampa. Ficam como parâmetro no topo de `gerar_modelo_3mf.py`.

**Posição: centro em `(73,00 / 65,00)`**, ocupando `x [28 – 118]`,
`y [30 – 100]`. Foi o que sobrou depois de quatro obstáculos:

| Obstáculo | Onde | Folga |
|---|---|---|
| Colunas Ø10 dos cantos | (20,35 / 20,35) e (20,35 / 109,65) | 2,65 em x |
| Colunas Ø10 do meio | (89 / 6) e (89 / 124) | 19,00 em y |
| Flange do botão verde Ø37,70 | (140 / 65) | 3,15 em x |
| Terminais do KCD1 | `y ≥ 102,30`, mas em `z ≈ 35` | 23,00 em z |

**Folga vertical**, com o piso da cavidade (face interna da tampa) em `z = 63`:

```
botão vermelho  corpo 41,00 abaixo da face → desce a z = 41,00 → 22,00 livres
botão verde     corpo 52,40 abaixo da face → desce a z = 52,40 → 10,60 livres
placa           afastador 3,50 + FR4 1,60  → face de cima em z = 57,90
componente mais alto admissível sob o vermelho: 57,90 − 41,00 = 16,90
```

É por causa dos 10,60 mm do botão verde que a placa foge dele em `x`.

**Pinos**, em `(31,50 / 33,50)`, `(114,50 / 33,50)`, `(31,50 / 96,50)`,
`(114,50 / 96,50)`. Perfil de baixo para cima, medido da face interna da tampa:

```
0,00 .. 3,50   ombro   Ø6,00   afastador; base larga contra o momento
3,50 .. 5,30   haste   Ø2,80   placa 1,60 + 0,20 de folga
5,30 .. 5,90   farpa   Ø3,60   aresta de retenção plana; 0,30 radial sobre o furo Ø3,00
5,90 .. 6,20   guia 1  Ø3,00
6,20 .. 6,50   guia 2  Ø2,40
rasgo central 1,20 de largura, de z = 0,00 a 6,50, atravessando tudo
```

Os 3,50 mm de ombro não são folga sobrando: são o espaço das pernas soldadas por
baixo da placa.

**A guia de entrada é escalonada, não cônica** — dois degraus de 0,30 × 0,30, que
é 45° efetivo para a placa e prismático para o gerador. Pela mesma razão do
alívio dos furos do painel: cone quebraria a conferência de volume em 1e-9.

O rasgo é dimensionado, não escolhido. Duas pernas de 0,80 mm fletindo 0,30 mm
(a interferência da farpa Ø3,60 sobre o furo Ø3,00) num braço de 6,50 mm:

```
ε = 3·t·y / (2·L²) = 3 × 0,80 × 0,30 / (2 × 42,25) = 0,85 %
```

abaixo do escoamento do PLA impresso. Com rasgo só na haste (1,80 mm de braço)
daria 11 % e a perna quebraria na primeira montagem. Vira **regra do
`conferir_projeto()`**, com teto em 1,00 %.

Com o ombro em 3,50, a placa fica com a face de cima em `z = 57,90` montada, e a

Com o ombro em 3,50, a placa fica com a face de cima em `z = 57,90` montada, e
a folga sob o botão verde cai de 10,60 para **5,50 mm**.

> **Atenção à leitura dessa folga.** Ela não é o que segura a placa longe do
> verde. Com o centro em `(73 / 65)` a placa **desvia do verde no plano**, com
> 3,15 mm — e a regra 11 se dá por satisfeita antes de olhar o z. Os 5,50 mm
> só passariam a ser avaliados se alguém deslocasse a placa para debaixo do
> verde, e aí eles reprovariam contra os 10,00 de `ALT_COMPONENTE`. É assim
> que a regra segura: pelo plano primeiro, pela altura se o plano falhar.


⚠ **Ponto de desgaste conhecido:** encaixar e desencaixar a placa muitas vezes
cansa as farpas. Se o uso previsto exigir isso, a mitigação é trocar dois dos
quatro pinos por pinos lisos de localização.

---

## 4. Núcleo de malha — duas primitivas novas

O `malha.py` assume *prisma*: contornos em (x,y) extrudados em z. O furo Ø20,20
do KCD1 tem eixo em **y** e não cabe nessa hipótese. Duas primitivas resolvem:

**`face_vertical(externo, buracos, y, frente)`** — triangula uma região plana no
plano (x,z) a `y` constante, reaproveitando o `triangular()` que já existe; é
troca de eixos, não motor novo.

**`tubo(anel_a, anel_b, inverter)`** — costura dois anéis fechados de mesma contagem
de pontos em dois planos paralelos quaisquer.

`tubo` sozinho resolve três coisas: o cilindro Ø20,20 de eixo horizontal, os dois
cilindros concentricos do rebaixo da chave e o escalonamento Ø25 → Ø20,20
entre eles.

**Como a parede de trás passa a ser emitida:**

| Superfície | Antes | Agora |
|---|---|---|
| Face externa `y = 130`, trecho reto | `parede(ext)` | `face_vertical` com furo Ø20,20 |
| Face interna `y = 126`, trecho reto | `parede(cav)` | `face_vertical` com furo Ø25,00 |
| Anel em `y = 128` | — | `face_vertical`, Ø25,00 com furo Ø20,20 |
| Cilindros Ø25,00 e Ø20,20 | — | `tubo` |

A emenda entre o trecho de `face_vertical` e o `parede` vizinho fecha sem junta
em T: as arestas verticais em `x = x_a` e `x = x_b` vão de `z = 0` a `z = 63` sem
subdivisão intermediária dos dois lados.

**Código que fica órfão e sai: só `costura`.** Ela existia para emendar uma
parede de altura cheia com uma parede que muda de perfil com z — situação que
some junto com o berço da SS12D00G4, porque a parede volta a ser uniforme em z.
Com ela sai o laço de faixas por z do `corpo()`, hoje a parte mais difícil de ler
do arquivo.

**`entalhar` e `trecho` ficam**, e ficam por um motivo novo: são eles que
recortam o trecho `x ∈ [55 – 84]` da parede para o `face_vertical` assumir.
`entalhar(ext, 130, 84, 55, [])` apaga os vértices de densificação do trecho,
deixando uma aresta única que a face vertical compartilha sem junta em T; e
`trecho` devolve o resto do contorno, que continua saindo por `faixa`.

**Terceira primitiva pequena, exigida pelo pino da perfboard:** um recorte de
polígono por faixa (`perna` / `degrau_da_perna`), que devolve a seção em D de
cada perna e o polígono simples do degrau entre dois diâmetros. Sem ele o degrau
farpa↔haste viraria "face com buraco encostado na borda", que o ear clipping não
tritura.

---

## 5. Parâmetros de PLA

### 5.1 Folgas

| Feature | Nominal | Modelado | Motivo |
|---|---|---|---|
| Furo do KCD1 (eixo horizontal) | Ø19,80 (corpo) | **Ø20,20** | furo deitado fecha mais; aro Ø23 cobre 1,40 radiais |
| Barril M24 (eixo vertical) | Ø26,00 | Ø26,00 | já é a folga da Adafruit |
| Haste do pino × furo da placa | Ø3,00 | Ø2,80 | 0,20 diametral |
| Farpa do pino | — | Ø3,60 | 0,30 radial de retenção sobre o furo Ø3,00 |
| Parede local da chave | — | 2,00 (5 linhas) | faixa de snap do KCD1 |
| Furo do inserto M3 | Ø4,20 | Ø4,20 | inserto entra por calor, não por folga |

### 5.2 Impressão (substitui a tabela PETG / K1C do README)

| Parâmetro | Valor | Motivo |
|---|---|---|
| Bico | 0,40 / linha 0,42 | paredes são múltiplos: 4,00 = 10 linhas, 2,00 = 5 |
| Camada | 0,20 | |
| Bico / mesa | 210–220 °C / 55–60 °C | |
| Perímetros | 4 | |
| Preenchimento | **20 % giroide** | era 30 % em PETG; PLA é mais rígido |
| Brim | **não** | 178 numa mesa de 180 não deixa |
| Suporte | **zero nas duas peças** | |

Some o aviso de soltura PETG × PEI: PLA solta sozinho quando a mesa esfria.

Entra um aviso novo: **a primeira camada da peça fundida é a face visível dos
botões.** A textura da mesa transfere direto para ela — PEI liso dá acabamento
brilhante, texturizado dá fosco. Não é detalhe cosmético opcional: é a face que
a pessoa olha.

### 5.3 Volume

```
caixa-corpo (fundida)     279,13 cm3     era 233,93 + 130,26 = 364,19
caixa-tampa                81,98 cm3     era  81,64
                          ─────────
sólido                    361,11 cm3     era 445,83   (−19 %)
```

A 4 perímetros e 20 % giroide, densidade efetiva ~50 % → ≈ 181 cm³ → **≈ 224 g
de PLA**. Com refugo e uma peça refeita, 1 kg continua sendo a compra certa.

Os números acima são os medidos por `validar_modelo.py` na malha gravada, e
substituíram a estimativa analítica que esta seção trazia antes. A estimativa
errava por 0,4 % no corpo.

---

## 6. Montagem

A ordem muda, e essa é a contrapartida de fundir o painel no corpo: **as porcas
M24 dos dois botões passam a ser apertadas por dentro**, com a mão entrando pela
boca de baixo (170 × 122 × 55). Deixa de dar para montar os botões na bancada e
depois fechar.

1. Insertos de latão M3 nas 6 colunas, por calor, pelo topo
2. Chave KCD1 encaixada por fora na parede de trás, até clicar
3. Botões pelo lado de fora; porca M24 apertada por dentro
4. Fiação: faston 4,80 na chave, fios dos microswitches
5. Perfboard encaixada nos 4 pinos da tampa
6. Tampa fechada com 6 × M3 × 6 ISO 7380

---

## 7. Arquivos

| Arquivo | O que acontece |
|---|---|
| `malha.py` | + `face_vertical`, + `tubo`, + `perna` / `degrau_da_perna`; − `costura` |
| `tests/test_malha.py` | novo: TDD das primitivas, com sólidos-teste fechados |
| `gerar_modelo_3mf.py` | `painel()` e `corpo()` fundem em `corpo()`; `tampa()` ganha os pinos; `INTERRUPTOR` → `CHAVE`; + bloco `PLACA`; `conferir_projeto()` reescrito; `PECAS` perde `caixa-painel` |
| `gerar_desenhos_3mf.py` | CX-01 aposentado; CX-02 vira a caixa fundida; CX-03 ganha o detalhe do pino; CX-04 vira a estação do KCD1 |
| `validar_modelo.py` | passa a esperar 2 peças |
| `README.md` | PLA, A1 mini, 2 peças, KCD1, perfboard; sai a seção do berço da SS12D00G4 |
| `LISTA-DE-MATERIAIS.md` | PLA no lugar de PETG; KCD1 no lugar de SS12D00G4; 6 insertos; + perfboard; sai a cola quente do berço |
| `caixa-painel.3mf` / `.stl`, `desenho-caixa-painel.svg`, `desenho-caixa-berco.svg` | apagados |

Numeração das pranchas: **CX-01 fica aposentada** em vez de renumerar tudo, para
não invalidar as referências cruzadas que já existem no README.

---

## 8. Conferências (`conferir_projeto()`)

Cada regra falha antes de gerar malha, e cada uma corresponde a uma coisa que só
apareceria depois de horas de impressão.

**Herdadas e mantidas** — silhueta na mesa; folga entre as capas; capa contra a
borda; furos Ø10 dentro da capa; coluna contra a parede.

**Reescritas**

1. Aperto da porca = `PAIN_ESP` ∈ `[5,00 – 12,70]` para os dois botões
2. Engate da rosca M24 no painel liso: `PAIN_ESP / P ≥ 3` filetes
   (8,00 / 2,00 = 4 ✔) — era garantido de graça pelos 16 mm, agora não é
3. Parafuso da tampa: `L = (4 − 2) + 4` inteiro, e penetração < profundidade do
   inserto
4. Altura total da peça fundida ≤ Z da mesa

**Novas — chave**

5. Rebaixo Ø25 contido no trecho reto `[55 – 84]` da parede
6. Rebaixo livre das 6 colunas por ≥ 2,00 mm
7. Parede local da chave ∈ `[1,60 – 3,00]` e menor que a parede cheia
8. Vãos de ponte (14,28 no furo, 17,68 no rebaixo) ≤ `PONTE_PLA = 20,00`
9. Reserva de 25,70 mm atrás da parede cabe na cavidade

**Novas — perfboard**

10. Placa livre das 6 colunas por ≥ 2,00 mm
11. Folga da placa com cada botão **no plano OU na altura** — basta uma. Onde
    ela passa por baixo (folga no plano < 2,00), o que sobra em z tem de dar
    `ALT_COMPONENTE = 10,00` mm para um componente de pé
12. *(fundida na regra 11)* — a formulação anterior exigia folga no plano dos
    **dois** botões e reprovava por construção: a placa passa sob o vermelho de
    propósito, e a distância no plano dá zero
13. Ombro do pino ≥ 2,50 mm (pernas soldadas)
14. Deformação de flexão das pernas do pino ≤ 1,00 % (projeto: 0,85 %)
15. Pinos livres das colunas

---

## 9. Verificação

O projeto já tem o mecanismo certo, e ele continua valendo:

- `Solido.conferir()` — toda aresta em exatamente 2 triângulos com orientações
  opostas, volume positivo, e volume da malha batendo com o **volume analítico
  calculado à parte**, camada a camada, com tolerância relativa de 1e-9. As duas
  primitivas novas entram nessa conta como qualquer outra superfície: se
  `face_vertical` ou `tubo` deixarem de compartilhar vértice com o vizinho, a
  contagem de arestas acusa.
- `conferir_projeto()` roda antes de qualquer malha.
- `validar_modelo.py` relê os `.3mf` gravados.
- Os desenhos saem de `gerar_desenhos_3mf.py`, que **mede a malha** — nenhuma
  cota é digitada duas vezes, então um desenho que bate é evidência de que o
  modelo bate.

Conferência nova a acrescentar: o volume analítico do **pino da perfboard**
(ombro + haste + farpa + as duas guias, menos o rasgo) tem de ser escrito à mão
na conta esperada da tampa. Como todo o perfil ficou prismático, cada trecho é
área de polígono vezes altura, e a conferência fecha em 1e-9 como no resto.

---

## 10. Fora de escopo, registrado

- **Passagem de cabo USB.** A caixa continua fechada nos quatro lados. Com a
  perfboard dentro, o cabo do microcontrolador não tem por onde sair. Cabe na
  mesma parede de trás, em `x [94 – 123]`, e com `face_vertical` pronto custa
  pouco. Ficou de fora desta revisão por decisão explícita.
- **Função dos 9 furos Ø10** — pendente desde a revisão anterior.
- **Microcontrolador** — continua sem decisão registrada.
