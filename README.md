# Caixa com botões de arcade meio embutidos — PIBIC-CEUB

Caixa em PETG de três peças para dois botões de arcade M24, derivada dos
desenhos esquemáticos `botao-verde-desenho-esquematico.jpg` e
`botao-vermelho-desenho-esquematico.jpg`.

---

## ⚠ Revisão atual: A1 mini + botões meio embutidos

A caixa foi refeita para a **Bambu Lab A1 mini** (mesa 180 × 180) e os botões
passaram a entrar **meio embutidos** num rebaixo. `gerar_modelo_3mf.py` é agora
a fonte única da geometria das três peças — os `.3mf` e os desenhos saem dele.

| | Antes (K1C) | Agora (A1 mini) |
|---|---|---|
| Silhueta | 215 × 120 | **178 × 130** |
| Painel | 10 mm, botão todo para fora | **16 mm**, rebaixo de 8,00 / 5,00 |
| Parede do corpo | 10 mm | **4 mm** + 6 colunas Ø10 |
| Fixação | 6 insertos, só a tampa | **12 insertos**, painel e tampa |
| Altura montada | 69 mm | **75 mm** |
| Folga entre as capas | 25,35 mm | **4,35 mm** |

Para reproduzir tudo do zero:

```
python gerar_modelo_3mf.py     # parametros -> caixa-*.3mf e caixa-*.stl
python validar_modelo.py       # confere os .3mf gravados
python gerar_desenhos_3mf.py   # .3mf -> desenho-caixa-*.svg
```

### Placa avulsa de 209,30 × 108,50 — REMOVIDA

`desenho-tampa.svg`, `tampa-botoes.scad` e `tampa-botoes.stl` eram a versão
anterior, de antes de a caixa existir: uma chapa de 4 mm com os 2 furos M24 e
os 6 furos de fixação. Foram **apagados**, junto com o código que só servia a
eles (`tampa()` em `gerar_stl.py`, `desenho_tampa()` em `gerar_desenhos.py`,
`checar_tampa()` em `validar_stl.py` e a classe `FuroRebaixado`, que ficou sem
nenhum uso).

O `caixa-painel` faz o que ela fazia e mais: rebaixo de assento das capas,
espessura compatível com a porca M24 e fixação real no corpo. Mantê-la seria
guardar duas placas parecidas e incompatíveis — espaçamento de botões de 119,65
contra 84,00 entre centros — que é o tipo de coisa que se imprime errado.

Está tudo no histórico do git, caso precise.

Os gabaritos (`gabarito-passante`, `gabarito-roscado`) **continuam válidos**:
medem tolerância de furo, não dependem de peça nenhuma e têm 160 × 40 mm.

**O que ficou superado neste README.** As seções abaixo descrevendo a caixa de
**215 × 120**, a parede de 10 mm, os 6 insertos e os parâmetros de impressão da
**Creality K1C** são da revisão anterior. Valem ainda: as cotas dos botões
lidas dos esquemáticos, a memória de cálculo da rosca M24 × 2 e os gabaritos de
tolerância, que independem de impressora. Em caso de conflito, **o modelo
paramétrico manda** — ele se recusa a gerar geometria inconsistente, e
`gerar_desenhos_3mf.py` se recusa a emitir prancha que discorde dele.

---

## Arquivos

| Arquivo | O que é |
|---|---|
| `desenho-gabarito-passante.svg` | Desenho do gabarito de furo liso |
| `desenho-gabarito-roscado.svg` | Desenho do gabarito de rosca interna |
| `desenho-perfil-rosca.svg` | Perfil ISO 68-1 da M24 × 2 ampliado 18:1, com a memória de cálculo |
| `gabarito-passante.stl` | **Imprima primeiro.** 160 × 40 × 8 mm, 5 furos lisos |
| `gabarito-roscado.stl` | **Imprima junto.** 160 × 40 × 8 mm, 5 roscas M24 × 2 reais |
| `LISTA-DE-MATERIAIS.md` | **BOM completa** — botões, ferragens, fiação, solda, filamento, ferramentas |
| `gerar_modelo_3mf.py` | **Fonte única da caixa.** Parâmetros + geometria das 3 peças; grava os `.3mf` e `.stl` |
| `malha.py` | Núcleo de malha: contornos, triangulação com furos, sólido estanque, saída 3MF/STL |
| `validar_modelo.py` | Relê os `.3mf` gravados e confere estanqueidade, mesa, furos e parede |
| `caixa-painel.3mf` / `.stl` | Painel, 178 × 130 × 16, com os 2 rebaixos de assento das capas |
| `caixa-corpo.3mf` / `.stl` | Corpo, 178 × 130 × 55, parede 4 mm, 6 colunas passantes |
| `caixa-tampa.3mf` / `.stl` | Tampa de serviço, 178 × 130 × 4 |
| `desenho-caixa-painel.svg` | PIBIC-CX-01: vista, corte A-A e **detalhe do botão meio embutido** |
| `desenho-caixa-corpo.svg` | PIBIC-CX-02: vistas, corte da parede e detalhe da coluna de inserto |
| `desenho-caixa-tampa.svg` | PIBIC-CX-03: 6 furos rebaixados e detalhe 8:1 |
| `gerar_desenhos_3mf.py` | Gera os três acima **lendo a malha dos `.3mf`** — toda cota é medida, nenhuma digitada, e o resultado é conferido contra `gerar_modelo_3mf.py` |
| `gerar_stl.py` | Gera os `.stl` dos gabaritos de tolerância (Python puro) |
| `gerar_desenhos.py` | Gera os `.svg` dos gabaritos a partir das **mesmas** constantes de `gerar_stl.py` |
| `validar_stl.py` | Verifica estanqueidade, orientação, volume e perfil da rosca dos gabaritos |
| `Projeto PIBIC-caixa.3mf`, `tampa.3mf` | **Superados.** Exportação do Fusion da caixa de 215 × 120 |

Os SVG abrem em qualquer navegador e estão em escala 1:1 em milímetros
(1 unidade SVG = 1 mm), então podem ser impressos em papel e medidos com régua.

> **Obsoletos:** `gabarito-tolerancia.scad` e `gabarito-tolerancia.stl` são da
> primeira versão (4 mm, 180 × 45). Foram substituídos pelo par
> passante/roscado de 8 mm. Pode apagar os dois — não imprima por engano.

---

## Cotas extraídas dos desenhos

### Botão verde — arcade 60 mm

| Cota | Valor (mm) |
|---|---|
| Rosca | M24 (P = 2) |
| Ø capa / bezel | 60,8 |
| Ø flange do corpo (apoia sobre o painel) | 37,7 |
| Espessura do flange | 4,4 |
| Altura acima do painel | 10,0 |
| Barril roscado abaixo do painel | 30,5 |
| Corpo do microswitch | 21,9 |
| Altura total | 62,4 |
| Anti-rotação | 2 × Ø3,3 |

**Verificação de consistência:** 10,0 + 30,5 + 21,9 = 62,4 ✔ — as cotas
fecham exatamente com a altura total, o que confirma a leitura do desenho.

### Botão vermelho — domo 100 mm

| Cota | Valor (mm) |
|---|---|
| Rosca | M24 × P2 |
| Ø domo externo | 98,5 |
| Ø anel interno | 87,8 |
| Altura acima do painel | 17,5 |
| Etapas do corpo | 6,5 / 21 / 10,5 / 3 |
| Anti-rotação | 2 × R3 |

### Consequência prática

Os dois botões usam **M24 × 2**, então o furo do painel é **idêntico** para
ambos — só muda o espaço livre ao redor. E o barril de 30,5 mm do verde
(o mais curto dos dois) deixa ~26 mm de rosca livre numa tampa de 4 mm,
folga mais que suficiente para a porca.

---

## Memória de cálculo

### 1. Distância entre os botões

`4 cm entre os botões` foi interpretado como **folga livre borda-a-borda**,
não centro-a-centro. Centro-a-centro de 40 mm é fisicamente impossível: só os
raios das capas somam 49,25 + 30,40 = **79,65 mm** — as capas se sobreporiam
em 39,65 mm antes mesmo de existir folga.

```
centro-a-centro = Ø_vermelho/2 + folga + Ø_verde/2
                = 98,5/2 + 40,00 + 60,8/2
                = 49,25  + 40,00 + 30,40
                = 119,65 mm
```

### 2. Tamanho da placa

```
largura = margem + Ø_verm/2 + 119,65 + Ø_verde/2 + margem
        = 5 + 49,25 + 119,65 + 30,40 + 5 = 209,30 mm
altura  = margem + Ø_verm + margem = 5 + 98,5 + 5 = 108,50 mm

x do furo vermelho = 5 + 49,25            =  54,25 mm
x do furo verde    = 54,25 + 119,65       = 173,90 mm
y de ambos         = 108,50 / 2           =  54,25 mm
```

`margem = 5` foi escolhida pela mesa da K1C: 209,30 numa mesa de 220 deixa
5,35 mm de cada lado em X — o suficiente para o skirt e para a sondagem de
nivelamento. Com `margem = 8` (o valor inicial) a peça ia a 215,30 e sobravam
2,35 mm por lado, o que não cabe. Acima de `margem = 7` o skirt não passa.

### 3. Perfil da rosca ISO 68-1 (M24 × 2)

Todos os valores vêm de duas constantes: `D = 24` e `P = 2`.

```
H  = P·√3/2 = 2 · 0,8660254 = 1,7320508 mm      (altura do triângulo gerador)
5H/8 = 1,0825318 mm                              (profundidade radial do filete)

D1 = D − 2·(5H/8) = 24 − 2,1650635 = 21,8349365 mm   → tabela ISO: 21,835 ✔
D2 = D − 0,649519·P = 24 − 1,299038 = 22,7009619 mm  → tabela ISO: 22,701 ✔
```

Decomposição de **um passo** ao longo do eixo, que é o que o gerador de malha
percorre:

```
plano da crista   P/4    = 0,500
flanco            5P/16  = 0,625
plano da raiz     P/8    = 0,250
flanco            5P/16  = 0,625
                  ─────────────
                  16P/16 = 2,000 = P   ✔ fecha exatamente
```

O comprimento axial do flanco sai do ângulo de 60° do perfil:

```
flanco = (5H/8) · tan30° = (5/8)·(P√3/2) · (1/√3) = 5P/16
```

Essa forma fechada importa: usando o literal arredondado `0,5412659·P` o
fechamento do passo errava por 2,6 × 10⁻⁸ mm e o teste de ângulo de flanco
falhava. Com `5P/16` o fechamento é exato em ponto flutuante binário
(P/4 + 5P/16 + P/8 + 5P/16 = P sem erro), e a validação passa.

No `desenho-perfil-rosca.svg` o triângulo gerador está desenhado com o **ápice
no meio do plano da crista**, a `H/4` além de D1, e os cantos da base a `H/8`
além de D — que é a truncagem da norma (`H − H/8 − H/4 = 5H/8`, batendo com
D1 = D − 2·5H/8). Por isso os flancos do triângulo caem exatamente sobre os
flancos do perfil.

### 4. Por que δ de 0,10 a 0,50

`δ` é a **folga radial** somada ao perfil ISO: desloca `Rmaj` e `Rmin` juntos
para fora, o que aumenta os dois diâmetros em `2δ` sem alterar o passo, o
ângulo de flanco nem a decomposição axial acima.

| δ | D maior | D1 menor | folga no Ø |
|---|---|---|---|
| 0,10 | 24,20 | 22,03 | +0,20 |
| 0,20 | 24,40 | 22,23 | +0,40 |
| 0,30 | 24,60 | 22,43 | +0,60 |
| 0,40 | 24,80 | 22,63 | +0,80 |
| 0,50 | 25,00 | 22,83 | +1,00 |

A faixa cobre de 0,20 a 1,00 mm no diâmetro porque é onde cai o erro típico de
FDM em PETG: 0,3–0,5 mm de fechamento por camada de parede, e uma rosca é
essencialmente uma sequência de paredes finas concêntricas, onde o efeito é
maior que num furo liso. Abaixo de δ = 0,10 a rosca sai travada; acima de
δ = 0,50 ela gira folgada e não segura o botão. O passo de 0,10 corresponde a
0,20 mm no diâmetro — abaixo disso a diferença some dentro da própria
variação da impressora e o teste deixa de discriminar.

### 5. Por que 8 mm de profundidade

```
8 mm ÷ P 2 mm = 4 passos completos de engate
```

Quatro filetes é o mínimo prático para que o teste signifique alguma coisa:

- com **1 ou 2 filetes** (o gabarito antigo de 4 mm) a rosca entra em quase
  qualquer folga, porque não há comprimento suficiente para o desalinhamento
  acumular. O teste passava mesmo com δ errado.
- com **4 filetes** o erro de passo acumulado ao longo do engate aparece, e a
  conicidade do furo — que na FDM sempre existe, porque as primeiras camadas
  saem mais largas — também.
- 8 mm também é o dobro da espessura da tampa (4 mm), então o gabarito é
  **mais severo** que a peça final. Se o botão passa no gabarito, passa na tampa.

Para o furo **passante** os mesmos 8 mm servem para revelar atrito real e
conicidade, que um furo de 4 mm mascara.

### 6. Tamanho e passo do gabarito

```
passo entre furos = 29 mm
material entre furos = 29 − 25,0 = 4,0 mm  (usando o maior Ø, 25,0)
largura = 4 × 29 + folga nas pontas = 160 mm
altura  = 40 mm  →  (40 − 25,0)/2 = 7,5 mm de material acima e abaixo
```

Os 4 mm entre furos são o mínimo para caberem 4 perímetros de 0,4 mm de cada
lado (4 × 0,4 × 2 = 3,2 mm) sem que as paredes se fundam. O chanfro 8 × 8 no
canto superior esquerdo marca o lado do **menor** furo/folga, para não
depender de contar da esquerda.

### 7. Compensação do furo da tampa

O PETG sai com **furo subdimensionado**. Duas causas somadas:

1. **Inchamento do extrudado** — o filamento expande ao sair do bico, e em
   curvas côncavas (parede interna de furo) esse material sobra para dentro.
2. **Contração térmica** — PETG encolhe ~0,3–0,5 % ao resfriar, e o furo
   encolhe junto.

O efeito líquido típico é 0,3 a 0,5 mm a menos que o diâmetro modelado, mas o
valor exato depende de impressora, bico, temperatura e fluxo. Daí o valor de
partida `24,7 = 24,0 + 0,7`, que é o meio da faixa dos furos passantes do
gabarito — **e é justamente o que o gabarito existe para substituir**.

---

## Layout

```
        209,30
 ┌─────────────────────────────────────────────────┐
 │      ___                                        │
 │    /     \                                      │   108,50
 │   | VERM  |          40,0        _____          │
 │   | Ø98,5 |<------- folga ---->/ VERDE \        │
 │    \ ___ /                     | Ø60,8 |        │
 │      ⊙ x=54,25                  \ _⊙_ /         │
 └─────────────────────────────────────────────────┘        x=173,90
        |<------------ 119,65 centro-a-centro ---->|

 Furos M24: (54,25 ; 54,25) e (173,90 ; 54,25) — Ø24,7
```

**Distâncias mínimas entre centros** (para as capas não colidirem):

| Par | Mínimo absoluto | Recomendado |
|---|---|---|
| verde ↔ verde | 60,8 | 65 |
| vermelho ↔ vermelho | 98,5 | 105 |
| verde ↔ vermelho | 79,65 | 82 |

---

## A caixa modelada no Fusion (`.3mf`)

Os dois `.3mf` do repositório são a peça real do projeto. **A geometria deles
não é a da tampa paramétrica** de `gerar_stl.py` — são projetos distintos, e o
do Fusion é o que vale.

| | `Projeto PIBIC-caixa.3mf` | `tampa.3mf` |
|---|---|---|
| Body1 — painel dos botões | 215 × 120 × 10, z 0–10 | |
| Body2 — corpo | 215 × 120 × 55, z 10–65 | |
| Body3 — tampa | | 215 × 120 × 4, z 65–69 |

Silhueta comum: retângulo 215 × 120 com **R55,00** nos quatro cantos (quase um
estádio — sobram só 10 mm de trecho reto nas laterais curtas). Caixa montada:
**69,00 mm** de altura.

`gerar_desenhos_3mf.py` corta a malha em planos Z, encadeia os segmentos em
contornos fechados e classifica cada um como círculo ou perfil. **Toda cota dos
três desenhos é medida na malha**, nenhuma foi digitada — então desenho e
modelo não podem divergir.

### O que a medição encontrou

**1. O parafuso M3 × 10 não cabe.** O furo do inserto no corpo tem **5,00 mm**
(z 60 a 65). Com tampa de 4,00 e rebaixo de 2,00:

```
penetração  = 10,00 − (4,00 − 2,00)          = 8,00 mm
necessário  =  8,00 + 1,00 de folga no fundo = 9,00 mm
interferência                                = 3,00 mm
```

O parafuso encosta no fundo antes de a cabeça assentar no rebaixo. Está
desenhado em escala 4:1 no DETALHE de `desenho-caixa-corpo.svg`. Corrigir para
**9,00 mm** de profundidade (a parede tem 55 mm de altura, espaço sobra) ou
usar **M3 × 6**.

**2. O furo de passagem da tampa é Ø4,20, não Ø3,40.** Ø4,20 é o diâmetro do
furo do *inserto* — parece o mesmo esboço reaproveitado nas duas peças. A
consequência é dimensional: a cabeça ISO 7380 (dk 5,7) passa a assentar numa
coroa de **0,75 mm** de largura em vez de 1,15 mm, e crava no PETG ao apertar.
A tampa também ganha 0,80 mm de folga lateral que não precisa ter.

**3. Furo dos botões Ø26,00** — você seguiu a especificação Adafruit, não os
24,70 calculados. É defensável (é o número do fabricante) e resolve de vez o
risco da aba anti-rotação. Em troca são 1,0 mm de folga radial: o botão é
centrado à mão e a porca M24 é quem cobre a folga — ela cobre com sobra.

**4. Folga entre as capas: 25,35 mm**, não os 40 mm do escopo inicial.

```
105,00 (entre centros) − 98,5/2 − 60,8/2 = 25,35 mm
```

Nada quebra por causa disso — as capas não se tocam e as duas cabem na placa.
Só registro que a cota mudou em relação ao que foi pedido no começo.

**5. O contorno interno tem R47,50 e não é offset uniforme do R55,00 externo.**
A parede varia de **9,87 a 11,06 mm** ao longo do perímetro. Nos seis furos de
inserto ela vale ~10, então **não afeta a fixação** — é só uma inconsistência
de esboço.

**6. Não há passagem de cabo** no modelo. O corpo é fechado nos quatro lados e
não tem recorte para o USB.

### Os 9 furos Ø10,00

Seis num círculo de furação **Ø63,00** (a 60°) em volta do botão de 100 mm e
três num **Ø42,00** (a 120°) em volta do de 60 mm. Todos caem **sob as capas**,
fora do flange do corpo do botão.

A posição é compatível com **LED Ø10 iluminando a capa por baixo**, o que
resolveria exatamente a queixa registrada na documentação da caixa — de que o
LED interno concentra o brilho no centro. Mas **a geometria não prova a
função**, então os LEDs entraram na lista de materiais como item pendente.

---

## Caixa, fechamento e fixação

Especificação vinda da documentação da caixa. Os botões são os **Adafruit
gigantes**: *Large Arcade Button* 60 mm (#1190 vermelho, #1192 branco, #1193
verde) e *Massive Arcade Button* 100 mm (#1185 vermelho, #1187 branco, #1188
verde). Os dois compartilham o mesmo bocal traseiro **M24**, o que confirma a
leitura dos JPG.

| Cota do fabricante | Valor | Situação neste projeto |
|---|---|---|
| Rosca traseira | M24 | ✔ bate com os desenhos |
| Espessura máx. do painel | 12,7 mm | ✔ tampa de 4 mm passa folgado |
| Furo de passagem recomendado | 26 mm | ⚠ ver abaixo |
| Microswitch | NO, LED opcional até 12 V | fora do escopo mecânico |

### ⚠ Conflito: furo de 26 mm × furo de 24,70 mm

A especificação diz "26 mm (1 polegada)" — 1" são 25,4 mm, então a própria
linha se contradiz. Mais importante: **26 mm é uma medida para painel de
MDF/acrílico furado com serra copo**, que só existe em medidas polegada e corta
com borda irregular. Em impressão 3D o furo é controlado em ±0,1 mm, e 26 mm
dariam **1,0 mm de folga radial** — o botão assenta descentrado e a cota de
119,65 mm centro-a-centro passa a ter ±1 mm de incerteza.

Existe porém **um cenário em que os 26 mm são obrigatórios**: se o elemento
anti-rotação for uma **aba no barril**, e não um pino sob o flange. Nesse caso
nada abaixo de 26 mm aceita o botão — e é a explicação mais provável para a
especificação folgada da Adafruit. É exatamente a medida que falta na
Pendência 1.

**Isso é decidível com o gabarito, sem paquímetro:** se o botão **não passar
nem no furo Ø25,00** (o último, no lado *sem* chanfro), há material além de
Ø24 no barril e o furo tem de ir para 26 mm. Se passar, vale o resultado normal
do gabarito em torno de 24,70. Ver passo 2-b da calibração.

### Fechamento: tampa parafusada com insertos por calor

6 pontos de fixação. Ferragens:

- 6 × parafuso **M3 × 10 ISO 7380** (cabeça abaulada, sextavado interno 2,0 mm)
- 6 × inserto roscado de latão M3, **Ø externo 4,6 mm × 5,0 mm**

| Feature | Onde | Ø | Profundidade |
|---|---|---|---|
| Furo do inserto | caixa (pilar) | 4,2 mm | **9,0 mm** (ver correção) |
| Ø externo do pilar | caixa | **≥ 10,0 mm** | altura ≥ 11,0 mm |
| Furo de passagem | tampa | 3,4 mm | passante |
| Rebaixo da cabeça | tampa | 6,5 mm | 2,0 mm |

### ⚠ Correção: profundidade do furo do inserto

A regra "comprimento do inserto + 1,0 mm" considera só o inserto, mas **o
parafuso é mais longo que ele**. Com rebaixo de 2,0 mm numa tampa de 4,0 mm, o
corpo do parafuso começa a 2,0 mm da superfície, não na face inferior:

```
penetração no pilar = L_parafuso − (esp_tampa − prof_rebaixo)
                    = L − (4,00 − 2,00)
                    = L − 2,00
```

| Parafuso | Penetra | Furo necessário | Furo pela regra antiga | Resultado |
|---|---|---|---|---|
| M3 × 8 | 6,00 | 7,00 | 6,00 | falta 1,00 mm |
| **M3 × 10** | **8,00** | **9,00** | **6,00** | **falta 3,00 mm** |
| M3 × 12 | 10,00 | 11,00 | 6,00 | falta 5,00 mm |

Nas três opções o parafuso **toca o fundo do furo antes de a cabeça assentar no
rebaixo**: a tampa não fecha, o aperto vira tração no pilar e o PETG racha na
base. Daí o furo de **9,0 mm** e o M3 × 10 fixado como padrão — dão 5,0 mm de
engate no latão (1,67 × D) mais 3,0 mm de PETG cru abaixo, que serve de reserva
se o inserto afundar demais na instalação.

Dois números que a especificação não trazia e que importam:

- **Ø externo do pilar ≥ 10,0 mm.** O inserto de 4,6 mm desloca material
  derretido para os lados; com menos de ~2,5 mm de parede o pilar abre. `4,6 +
  2 × 2,5 = 9,6 → 10`.
- **Sob o rebaixo sobram 2,0 mm de tampa** (`4,0 − 2,0`), e é a seção mais fina
  da peça, justamente onde entra a carga de aperto. Se o resultado ficar frágil,
  engrosse a tampa localmente para 6 mm nos 6 pontos em vez de aumentar o
  rebaixo.

> **Furo de 4,2 mm:** funciona, mas é o extremo folgado. Os insertos M3 mais
> comuns (Ruthex / CNC Kitchen, 4,6 × 5,0) especificam **4,0 mm**. Se o inserto
> girar depois de instalado, refaça com 4,0.

### Posição dos 6 pontos de fixação

A capa vermelha Ø98,5 centrada em `y = 54,25` ocupa de `y = 5,0` a `y = 103,5`
— **a altura inteira da tampa**. Não existe posição de parafuso ao lado dela.
Sobram 6 pontos, os 4 cantos mais os 2 meios das bordas longas:

| # | X | Y | folga até a capa mais próxima |
|---|---|---|---|
| P1 | 8,00 | 8,00 | 12,91 (vermelho) |
| P2 | 104,65 | 8,00 | 15,90 (vermelho) |
| P3 | 201,30 | 8,00 | 20,11 (verde) |
| P4 | 8,00 | 100,50 | 12,91 (vermelho) |
| P5 | 104,65 | 100,50 | 15,90 (vermelho) |
| P6 | 201,30 | 100,50 | 20,11 (verde) |

Critério: distância do centro do parafuso ao centro do botão ≥ `raio da capa +
3,25` (metade do rebaixo Ø6,5). Com 8,00 mm de recuo das bordas sobram 4,75 mm
de PETG maciço entre o rebaixo e a borda da placa.

**Limitação conhecida:** os vãos ficam em 96,65 mm em X e **92,50 mm em Y sem
nenhum apoio intermediário**. Numa tampa de 4 mm que recebe impacto, a região
central das bordas curtas vai fletir.

Cheguei a considerar **aumentar a altura da placa** para abrir espaço de
parafuso ao lado do botão vermelho, e **as contas não sustentam a ideia**:

- para o rebaixo Ø6,5 caber entre a borda da capa e a borda da placa **com
  acesso para a chave allen** (folga de 5 mm), a altura teria de ir a
  **131 mm**, não os ~122 que eu tinha estimado;
- e ao crescer a placa **os parafusos de canto se afastam** do botão vermelho.
  Hoje os quatro apoios mais próximos estão a 65,4 / 68,4 mm. Com 131 mm
  ficariam a 57,0 / 73,4 mm — dois melhoram, dois pioram.

O ganho líquido é quase nulo para 20 % a mais de material e de tempo de
impressão. **A placa fica em 209,30 × 108,50.**

Se a rigidez ainda incomodar depois de montado, o caminho eficaz **não é mais
parafuso, é mais seção**: a rigidez à flexão cresce com `t³`. Passar a tampa de
4 para 6 mm multiplica a rigidez por `6³/4³ = 3,4` sem mexer em layout nenhum,
e o botão aceita painel de até 12,7 mm. O custo é 50 % mais material e recalcular
a profundidade do furo do inserto (`10 − (6 − 2) + 1 = 7,0 mm`).

---

## Modelando no Autodesk Fusion

Todos os números abaixo estão nos SVG; esta seção é só o roteiro.

### Painel, corpo e tampa — não precisam mais de Fusion

Esta seção descrevia como modelar à mão a placa avulsa de 209,30 × 108,50, que
foi removida. As três peças da caixa agora saem prontas de
`gerar_modelo_3mf.py`, com `.3mf` e `.stl` para abrir direto no slicer — e o
desenho é medido delas, não digitado.

Se quiser mexer na geometria, mexa nos parâmetros no topo daquele arquivo e
rode a pipeline de três comandos da seção inicial. `conferir_projeto()` valida
antes de gerar qualquer malha: folga entre capas, distância dos rebaixos à
borda e aos parafusos, espessura apertada pela porca contra o máximo do botão,
comprimento de parafuso de catálogo e coluna de inserto contra a parede. Cada
uma dessas regras é uma coisa que, se estiver errada, só apareceria depois de
seis horas de impressão.

Continua valendo: **não modele rosca no painel.** Com 8 mm apertados você teria
4 filetes, e o botão é preso pela porca dele.

### Pilares de inserto na caixa

Um pilar em cada uma das 6 coordenadas acima, medidas a partir do **mesmo
canto** que a tampa (senão espelha):

1. Círculo Ø`10,0` na face interna do fundo, `Extrude` até `≥ 11,0 mm` de
   altura, *Join*.
2. `Create ▸ Hole` simples, Ø`4,2 mm`, profundidade **`9,0 mm`**, a partir do
   topo do pilar. Não use *Through All*.
3. `Fillet 2 mm` na base do pilar contra a parede/fundo — é onde a carga de
   aperto concentra e o PETG é sensível a entalhe.

Imprima o pilar **na vertical, junto com a caixa**, para que as camadas fiquem
perpendiculares ao eixo do parafuso.

### Gabarito passante (`desenho-gabarito-passante.svg`)

1. Retângulo `160 × 40`, chanfro `8 × 8` no canto superior esquerdo.
2. Cinco círculos em `y = 20`, `x = 22 / 51 / 80 / 109 / 138`.
3. Diâmetros, nessa ordem: `24,40 / 24,60 / 24,70 / 24,80 / 25,00`.
4. **Extrude 8 mm.**

### Gabarito roscado (`desenho-gabarito-roscado.svg`)

Mesma placa; os furos viram rosca. No Fusion:

1. Furo liso de Ø igual ao **D1** da coluna, extrudado 8 mm.
2. `Create ▸ Thread`, marcar **Modeled** (senão a rosca é só cosmética e não
   sai no STL), tipo `ISO Metric profile`, tamanho `24 mm`, designação
   `M24x2`, classe qualquer, **Internal**.
3. O Fusion não aceita δ diretamente. Duas saídas:
   - **Offset:** aplique a rosca M24 × 2 padrão e depois `Modify ▸ Offset
     Face` de `+δ` na face da rosca (0,10 / 0,20 / 0,30 / 0,40 / 0,50).
   - **Ou** edite `ISO Metric profile.xml` na biblioteca de roscas do Fusion
     e adicione as cinco classes. Mais trabalhoso, mas fica reutilizável.

Diâmetros por coluna (esquerda → direita):

| # | δ | D maior | D1 menor |
|---|---|---|---|
| 1 | 0,10 | 24,20 | 22,03 |
| 2 | 0,20 | 24,40 | 22,23 |
| 3 | 0,30 | 24,60 | 22,43 |
| 4 | 0,40 | 24,80 | 22,63 |
| 5 | 0,50 | 25,00 | 22,83 |

Se preferir não brigar com a biblioteca de roscas, **imprima direto os STL
prontos** (`gabarito-passante.stl` e `gabarito-roscado.stl`) e modele no
Fusion só a tampa final. Os STL já estão validados.

---

## Procedimento de calibração

1. **Imprima os dois gabaritos** (~32 e ~34 cm³) com **exatamente** os
   parâmetros que usará na tampa final — bico, altura de camada, temperatura,
   fluxo e velocidade. Trocar qualquer um invalida o teste.

2. **Passante:** teste o barril M24 dos dois botões em cada furo, do menor
   para o maior. O canto chanfrado marca o furo #1 (Ø24,40). O furo bom é o
   **primeiro em que o botão entra com leve pressão dos dedos**, sem folga
   lateral perceptível e sem forçar.

2-b. **Teste do Ø25,00 — decide os 26 mm da Adafruit.** Se o botão **não
   passar nem no último furo** (Ø25,00, lado sem chanfro), existe material
   além de Ø24 no barril — quase certamente a aba anti-rotação. Nesse caso
   abandone o 24,70 e use **26,00 mm**, como a Adafruit especifica, e meça a
   aba com paquímetro para confirmar. Se passar, siga com o resultado do
   passo 2.

3. **Roscado:** parafuse o botão em cada furo. O δ bom é o **menor em que o
   botão rosqueia até o fim sem ferramenta e sem raspar**. Este resultado só
   é necessário se você quiser depois uma peça com rosca integrada — para a
   tampa de 4 mm, o resultado que importa é o do passante.

4. **Leve o valor do passante para o modelo.** Hoje o painel usa
   `D_BARRIL = 26.0` em `gerar_modelo_3mf.py` (especificação Adafruit). Se o
   gabarito mostrar que um furo menor serve, altere lá e rode
   `python gerar_modelo_3mf.py && python gerar_desenhos_3mf.py` — modelo e
   desenho saem juntos.

5. **Imprima o corpo de prova dos rebaixos** (Ø99,30 e Ø61,60) e teste as
   capas antes do painel inteiro.

### Parâmetros de impressão — PETG na Creality K1C

A K1C é uma CoreXY rápida e fechada, com bico de aço endurecido e ventoinha
auxiliar potente. Os perfis de fábrica são otimizados para **velocidade**, não
para precisão dimensional — e este projeto depende de precisão num furo.

| Parâmetro | Valor | Por quê |
|---|---|---|
| Bico / camada | 0,4 mm / 0,2 mm | padrão |
| Temperatura bico | **245–250 °C** | o bico de aço endurecido da K1C conduz pior que latão; +5 a 10 °C |
| Mesa | **70 °C** (não mais) | ver aviso da placa PEI abaixo |
| Perímetros | **4** | define diretamente a parede do furo |
| Preenchimento | **30 % giroide** | giroide é isotrópico — a caixa recebe impacto de todas as direções |
| **Velocidade parede externa** | **30–40 mm/s** | o padrão da K1C (>150 mm/s) distorce o furo |
| **Aceleração** | **≤ 5000 mm/s²** | o padrão (20000) faz cantos e furos incharem |
| **Ventoinha auxiliar** | **0–20 %** | a lateral da K1C é forte demais e delamina PETG |
| Ventoinha do modelo | 30–50 % | PETG precisa de bem menos que PLA |
| Suportes | não | peças planas |

**Avisos específicos da K1C:**

- **Placa PEI + PETG grudam quimicamente.** É o risco prático real aqui: o
  PETG pode arrancar lascas do PEI. Passe **bastão de cola como agente de
  soltura** (não de adesão) e **espere a placa esfriar totalmente** antes de
  remover a peça. Manter a mesa em 70 °C em vez de 85 °C também ajuda muito.
- **Câmara fechada:** deixe a tampa superior entreaberta. O PETG não precisa
  de câmara quente e a K1C passa fácil de 50 °C em peças grandes.
- **Calibre fluxo e pressure advance antes do gabarito.** Numa impressora
  rápida, fluxo descalibrado é a maior fonte de erro no diâmetro do furo. O
  Orca Slicer tem perfil de K1C e a suíte de calibração pronta — recomendo em
  vez do Creality Print por isso.
- **Use o mesmo perfil nas duas impressões.** Se o gabarito sair no modo
  rápido e a tampa no modo padrão, o resultado do teste não vale.

### Instalação dos insertos de latão

Ferro de solda a **220–240 °C** (abaixo disso o PETG não flui; acima ele
degrada e solta fumo).

1. Apoie o inserto reto sobre o furo de 4,2 mm, sem forçar.
2. Encoste a ponta do ferro no latão **sem fazer pressão** — quem afunda o
   inserto é o calor conduzido, não a força. Pressionar entorta o eixo.
3. Deixe descer até ficar rente à face do pilar, ou **0,5 mm abaixo** dela.
   Nunca acima: um inserto saliente impede a tampa de assentar.
4. Retire o ferro e encoste uma superfície metálica plana sobre o topo
   enquanto o PETG esfria — é isso que garante a rosca ortogonal.

Faça um pilar de teste avulso antes dos 6 definitivos. Se o inserto girar sob
torque depois de frio, o furo está grande: refaça com 4,0 mm.

> **Mesa:** a tampa tem 209,30 × 108,50 mm. Na K1C (220 × 220) sobram ~5,3 mm
> de cada lado em X — o suficiente para o skirt e para a sondagem do
> nivelamento. Se quiser mais borda, aumente `margem`, mas não passe de 7.

---

## Pendências — preciso de duas medidas suas

1. **Posição dos furos anti-rotação.** Os desenhos dão o diâmetro
   (2 × Ø3,3 no verde, 2 × R3 no vermelho) mas **não cotam a distância do
   eixo da rosca até o centro desses elementos**. Por isso eles foram
   **deliberadamente omitidos** do modelo.

   Na prática isso raramente incomoda: as duas capas são circulares e
   simétricas, então a rotação não afeta a aparência, e uma porca bem apertada
   segura o botão. Se ainda assim quiser os furos, meça com paquímetro a
   distância **centro da rosca → centro do pino** e me passe.

   **Ganhou peso** depois da especificação Adafruit: se o anti-rotação for uma
   aba *no barril* em vez de um pino sob o flange, ele muda o furo principal de
   24,70 para 26,00 mm. O passo 2-b da calibração resolve isso sem paquímetro.

2. **Comprimento roscado útil do botão vermelho.** As cotas 6,5 / 21 / 10,5 / 3
   do corpo estão em fonte pequena no JPG e não deixam claro qual trecho é
   rosca. Isso não afeta a tampa de 4 mm com porca, mas **limita a espessura
   máxima de uma tampa roscada**, caso você opte por essa via depois do
   gabarito roscado. Meça o comprimento da rosca com paquímetro antes de
   decidir.

---

## Nota técnica sobre a geração das malhas

`gerar_stl.py` não usa biblioteca de CAD. A face da placa é dividida em faixas
convexas com um furo cada; o círculo e o contorno da faixa são costurados por
caminhamento angular, sem inventar vértices no contorno. Isso faz faixas
vizinhas compartilharem exatamente os mesmos vértices na linha de corte, o que
elimina junções-T. As paredes são levantadas só das arestas que pertencem a uma
única faixa.

A rosca é gerada como campo de altura sobre o cilindro: o raio em (θ, z)
depende só da fase `(z − P·θ/2π) mod P`, então a parede helicoidal é malhável
numa grade (θ, z) e as colunas são amostradas exatamente nas quebras do perfil.

`validar_stl.py` confere tudo. Resultado atual:

```
gabarito-passante.stl   160 x 40 x 8 mm    2796 triangulos   31,784 cm3  (0,0000 % divergencia)
gabarito-roscado.stl    160 x 40 x 8 mm   21816 triangulos   33,753 cm3  (0,0005 % divergencia)

arestas nao pareadas: 0    arestas mal orientadas: 0
ISO: H 1,7321 | D1 21,8349 (tabela 21,835) | D2 22,7010 | D 24,0000 | soma axial = passo  OK
raios e fase das cristas: OK para delta 0,10 ... 0,50
```

Os furos rebaixados obrigaram duas extensões no gerador. A placa da tampa
deixou de ser uma fita por furo e virou uma **grade 5 × 3** com no máximo um
furo por célula — as linhas de corte caem no meio dos vãos medidos de **borda a
borda** das features, não de centro a centro, senão a boca de um furo cruzaria
o corte. Sete das quinze células ficam sem furo nenhum e são trianguladas por
leque **a partir do centroide**: um leque a partir de um canto geraria
triângulos degenerados sobre os pontos colineares que `subdividir()` insere nas
arestas longas. E o furo rebaixado virou três superfícies (cilindro do rebaixo,
coroa plana do fundo, cilindro de passagem) em vez de uma.

O volume de malha é comparado com um cálculo analítico independente (área do
polígono regular inscrito e área da seção helicoidal, ambas fechadas), e não
com outra medição da mesma malha — senão o teste não provaria nada.
