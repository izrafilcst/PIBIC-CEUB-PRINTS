# Tampa da caixa PIBIC — entrada USB-C para o carregador TP4056

Autor: Rafael Alves de Sousa Costa
Data: 24/09/2026
Estado: APROVADA, não implementada. Parte do estado deixado pela spec
`2026-08-23-caixa-pla-corpo-painel-fundidos-design.md`.

---

## 1. O que muda e por quê

Só a `caixa-tampa` muda. O `caixa-corpo` já está impresso e **não pode mudar
um vértice** — a pessoa quer reimprimir apenas a peça menor.

| Antes | Agora |
|---|---|
| 4 pinos farpados prendem a perfboard 90 × 70 | **pinos removidos**; a caixa deixa de fixar a perfboard |
| tampa lisa por baixo | tampa lisa por baixo, com **uma janela para o plugue USB-C** |
| — | **berço de encaixe** para um módulo TP4056 tipo C, em pé |

O módulo carrega uma bateria de lítio pela USB-C. A caixa carrega **deitada de
lado**: não há pés, e a face externa da tampa continua sendo a que pisa na
mesa no uso normal.

---

## 2. As restrições que decidem a geometria

### 2.1 O plugue entra de baixo para cima, logo o módulo fica em pé

O conector USB-C do TP4056 é **paralelo à placa**: o plugue entra pela borda,
não pela face. Para o plugue subir na vertical através da tampa, a placa tem
de ficar perpendicular a ela, com a borda do USB para baixo. Deitado, o
conector apontaria para o lado e exigiria um furo na parede do corpo — que não
pode ser reimpresso.

Em pé, o módulo sobe 28 mm cavidade adentro, e isso elimina quase toda a
tampa. Sob o botão vermelho sobram 22,0 mm em z; sob o verde, 10,6 mm; o miolo
tem os componentes dos botões. O único bolsão longe do centro que comporta o
módulo é a **borda direita**, entre o envelope do botão verde e a parede.

### 2.2 O modelo da tampa é um REFLEXO da peça física

A tampa é modelada com o (x, y) do corpo e `z = 0` na face externa, ou seja,
`z_corpo = 67 − z_tampa`. Essa transformação tem determinante −1: é um
espelhamento, não uma rotação. A peça impressa só casa com o corpo, depois de
virada, se for **simétrica em y = 65** (virada em torno do eixo x, que leva
y em 130 − y).

Até hoje isso não fazia diferença, porque tudo na tampa era simétrico em y. O
berço também é (a placa fica centrada em y = 65 e o deslocamento do conector é
em x). A regra 9 da §5 transforma a coincidência em exigência.

### 2.3 A tampa passa a ter lado certo

Os 6 furos de fixação são simétricos nos dois eixos, então a tampa também
parafusa girada 180° no plano. Nessa posição o berço vai para x ≈ 10, sob o
envelope do botão vermelho, que desce até z = 41 — o módulo bate 6 mm antes
de a tampa fechar. Não há como impedir isso só com a geometria da tampa; a
**janela do USB serve de marca**, e a prancha e a montagem dizem: *"janela do
lado do botão VERDE"*.

---

## 3. Geometria

Coordenadas em x, y do corpo; z da tampa (`z = 0` face externa, `z = 4` face
interna, que encosta no corpo).

### 3.1 Chapa

Silhueta 178 × 130 R55, espessura 4,00, os 6 furos Ø3,40 com rebaixo
Ø6,50 × 2,00 — **inalterados**. Os 4 pinos saem.

### 3.2 Módulo TP4056 tipo C — valores PRESUMIDOS

Dimensões variam de vendedor para vendedor. A pessoa não tinha o módulo à mão;
os valores abaixo são típicos da placa com proteção (DW01 + 8205A) e vão para a
prancha marcados como PRESUMIDOS, com aviso para medir antes de imprimir.

| cota | presumido |
|---|---|
| placa (comprimento × largura × espessura) | 28,00 × 17,00 × 1,60 |
| conector USB-C (largura × altura sobre a placa) | 9,00 × 3,30 |
| balanço do conector além da borda da placa | 0,80 |
| componente mais alto além do USB | 1,80, no lado do CI |
| verso | liso |
| capa do plugue (máximo da norma USB-C) | 12,35 × 6,50 |

**Orientação:** lado dos componentes virado para a cavidade (−x), verso liso
para a parede (+x). O CI chega a 70–90 °C carregando a 1 A, e o PLA amolece
por volta de 55–60 °C. O berço só encosta nas bordas da placa.

Posição: plano médio da placa em **x = 168,00**, centro em **y = 65,00**.

### 3.3 Janela do plugue

Retângulo passante **13,00 × 7,20** (y × x), centrado em y = 65,00 e
x = 165,55 — o centro do conector: `168,00 − 1,60/2 − 3,30/2`. Ocupa
x 161,95..169,15, y 58,50..71,50, e fica a 8,85 mm da borda de fora.

- Dimensionada pela **capa do plugue, não pelo conector**: 12,35 + 0,65 e
  6,50 + 0,70. A capa entra na janela, então o plugue alcança o conector
  qualquer que seja o balanço real dele, de 0 a 4 mm.
- O conector presumido sobra 2,00 mm por lado em y e 1,95 em x dentro da
  janela, então um erro de até ~2 mm na posição real do USB ainda passa.
- **Alívio de boca** na face da mesa, como os furos do painel: 14,00 × 8,20 ×
  0,50 (`FOLGA_ALIVIO` somado a cada dimensão, `REB_ALIVIO` de fundo). A
  janela nasce na primeira camada, e o pé de elefante estreitaria justo a
  passagem da capa. É prisma reto, não chanfro, pelo motivo de sempre: a
  conferência de volume.
- A placa apoia as duas pontas na chapa, **2,00 de cada lado da janela**
  (y 56,50..58,50 e 71,50..73,50). O puxão de desplugar vai para a chapa.

### 3.4 Berço — duas colunas em U com garra

Uma coluna em cada ponta da placa, simétricas em y = 65. Cada uma, em planta,
é um retângulo **4,40 (x) × 3,20 (y)**, com um canal aberto para o centro:

| parâmetro | valor | de onde vem |
|---|---|---|
| folga de encaixe (PLA, por lado) | 0,20 | |
| canal | 2,00 × 1,20 de fundo | placa 1,60 + 2 × 0,20 |
| fundo do canal a partir de y = 65 | 8,70 | 17,00/2 + 0,20 |
| ponta das abas a partir de y = 65 | 7,50 | 8,70 − 1,20 |
| face de fora a partir de y = 65 | 10,70 | alma de 2,00 |
| abas (espessura em x) | 1,20 cada | |
| coluna em x | 165,80..170,20 | 168,00 ± 2,20 |
| coluna em y | 54,30..57,50 e 72,50..75,70 | |

Perfil em z (da tampa), de baixo para cima:

| trecho | z | seção |
|---|---|---|
| canal | 4,00..32,20 | U, canal de 1,20 |
| garra | 32,20..33,40 | **retângulo cheio** — o canal fecha |
| degrau 1 | 33,40..33,80 | U, canal de 0,40 |
| degrau 2 | 33,80..34,20 | U, canal de 0,80 |

A face de baixo da garra fica em 4,00 + 28,00 + 0,20: a placa assenta na chapa
com 0,20 de folga vertical sob a garra. A garra cobre **1,00** da borda de cima
da placa (fundo do canal 8,70 − ponta da aba 7,50 − folga 0,20).

A entrada é **escalonada, não rampa**: os dois degraus de 0,40 × 0,40 dão 45°
efetivos para a placa entrar, e mantêm tudo como prisma em z. É o mesmo
argumento da guia do pino.

Altura total da tampa: **34,20**.

**Deformação ao encaixar.** Quem flete é a coluna inteira, em y, como viga
engastada na chapa. Com a deflexão δ = 1,20 (pior caso: a placa encostada no fundo
deste canal, e a garra inteira tendo de sair da frente), braço L = 28,80 (da chapa ao meio da garra) e seção U com linha
neutra calculada (c = 1,805 do lado mais distante), a deformação é
`ε = 3·δ·c / L² = 0,78 %`, abaixo do limite de 1,00 % usado no pino. A carga
de flexão atravessa as camadas — é a direção fraca do PLA —, por isso o
limite é o mesmo.

**Retenção.** O empurrão do plugue (5–20 N pela norma) sobe pela placa e
chega à face de baixo das garras. A garra resiste como balanço horizontal curto,
com as camadas na direção da tração.

### 3.5 Folgas conferidas

| entre | folga |
|---|---|
| coluna × face interna da parede do corpo | 3,77 |
| envelope do módulo (x 163,90..168,80) × envelope do botão verde | 5,05 |
| coluna × coluna de inserto mais próxima | 29,91 |
| topo do módulo em z do corpo | 35,0, contra 52,4 do botão verde — mas não se cruzam em planta |

---

## 4. Núcleo de malha

**Nenhuma primitiva nova.** A janela, o alívio e as colunas são prismas em z
com contorno poligonal: `face`, `parede` e `coroa` bastam.

Um cuidado de emenda, o mesmo da corda do pino: na altura da garra a seção
passa de U para retângulo, e o retângulo tem de carregar **vértices colineares
extras** na boca do canal (em x = 167,00 e 169,00), senão a aresta única do
retângulo encontra as três do U e a malha abre. A lista sai dos próprios
parâmetros, para os dois contornos não descasarem se o canal mudar.

**Saem**, porque só os pinos usavam: `perna`, `degrau_da_perna`,
`_arco_cortado` e `_corda`, com seus 2 testes. **Ficam** `tubo` e
`face_vertical` — o corpo usa as duas.

O volume esperado da tampa é escrito à parte, só com `area_assinada` de
polígonos: chapa menos furos e rebaixos (como hoje), menos janela e alívio,
mais as duas colunas trecho a trecho. A conferência continua em `tol_rel=1e-9`.

---

## 5. Conferências novas em `conferir_projeto()`

Cada uma ganha um teste de perturbação: o teste estraga um parâmetro e exige
que `conferir_projeto()` reprove com a mensagem certa.

| # | regra | o teste estraga |
|---|---|---|
| 1 | envelope do módulo × envelope de cada botão: ≥ 2,00 no plano **ou** folga em z ≥ 2,00 | empurra o berço para o botão verde |
| 2 | colunas × face interna da parede ≥ 1,00 (distância ao contorno real da cavidade) | encosta o berço na parede |
| 3 | colunas × colunas de inserto ≥ 2,00 | — (sobram 29,91; fica como guarda) |
| 4 | janela ≥ capa máxima do plugue + 0,30 por lado | encolhe a janela |
| 5 | conector dentro da janela com ≥ 1,00 por lado | alarga o conector presumido |
| 6 | cada ponta da placa apoia ≥ 1,50 na chapa | alarga a janela |
| 7 | deformação da coluna ≤ 1,00 % | aprofunda a garra |
| 8 | a garra retém: cobre a placa (fundo do canal − folga > 0) | zera a interferência |
| 9 | todo o berço e a janela simétricos em y = CX_A/2 (§2.2) | desloca o berço em y |

**Saem** com os pinos: `PLACA`, `pinos_placa()`, `ALT_COMPONENTE` e as três
regras da placa (placa × colunas, placa × botões, flexão do pino).

---

## 6. Validador (`validar_modelo.py`)

`conferir_pinos` sai; entra `conferir_berco`, que relê o `.3mf` da tampa e
corta a malha em alturas escolhidas:

| corte em z | espera |
|---|---|
| 3,00 (entre o fundo do rebaixo, em 2,00, e a face interna) | um laço retangular 13,00 × 7,20 centrado em (165,55; 65,00) |
| 0,25 (alívio) | o retângulo 14,00 × 8,20 |
| 18,10 (meio da coluna) | dois laços em U: canal de 2,00, fundos a 17,40 um do outro |
| 32,80 (garra) | dois retângulos 4,40 × 3,20, sem canal |
| 33,60 e 34,00 (degraus) | canais de 0,40 e 0,80 |
| topo | 34,20 |

Cada sonda é **testada por mutação** antes de ser dada como boa: a sonda do
pino que concordava com tudo porque `eh_circulo` rejeitava a seção em D não
pode se repetir.

---

## 7. Prancha CX-03

- O detalhe do pino dá lugar ao **corte do berço** no plano médio da placa
  (x = 168,00): chapa, janela, alívio e as duas colunas — canal, garra e
  degraus —, com a placa em linha de referência.
- A planta do berço fica na **vista superior 1:1** (os dois U, a janela, o
  alívio e o envelope do módulo em referência). Um detalhe ampliado em
  planta não cabe na faixa livre da folha retrato. A vista é de +z, a face
  interna como a peça sai da mesa: rebaixo e alívio saem ocultos, e passa
  a valer para os furos de fixação também, que a prancha anterior tinha
  invertidos.
- A vista superior mostra a janela, o alívio e as duas colunas, e a tabela de
  coordenadas os lista.
- Notas: valores PRESUMIDOS com aviso de medir; *"janela do lado do botão
  VERDE"*; os riscos da §10.
- A conferência de layout (`Blocos`) segura sobreposição e moldura, como nas
  outras pranchas.

---

## 8. Documentação

- **README e lista de materiais**: entra o TP4056 tipo C; sai a fixação da
  perfboard; a caixa carrega deitada de lado; reimprimir só a tampa.
- **Nota térmica** na lista de materiais: se o módulo esquentar demais dentro
  da caixa fechada, trocar o resistor R_PROG reduz a corrente de carga.

---

## 9. Verificação

1. `pytest` verde, com os testes novos de perturbação e sem os 6 dos pinos.
2. Tampa: malha fechada e volume conferido em `tol_rel=1e-9` — 81,97 cm³ no
   protótipo feito antes do plano.
3. **O corpo não muda.** Um hash da malha do `caixa-corpo.3mf` (vértices e
   triângulos, sem metadados) tirado antes da primeira mudança tem de ser
   idêntico ao do final. "Só reimprimir a tampa" é um fato verificado, não uma
   promessa.
4. `validar_modelo.py` verde, com as sondas do berço mutadas uma a uma.
5. `gerar_desenhos_3mf.py`: conferência de cota e de layout sem divergência.

---

## 10. Riscos e fora de escopo, registrados

- **Medidas presumidas.** Comprimento da placa decide a folga vertical da
  garra; largura decide a folga do canal. Medir antes de imprimir.
- **A garra pode encostar nas ilhas de solda** dos cantos, se a placa tiver
  ilha a menos de 1,00 da borda lateral. Aparar a garra com estilete resolve,
  sem reimprimir.
- **LEDs de carga invisíveis** com a caixa fechada. Um guia de luz fica fora
  de escopo.
- **Tampa montada girada 180°** colide com o botão vermelho (§2.3). A marca é
  a janela.
- **A perfboard fica solta** na caixa; fixá-la em outro lugar é fora de
  escopo.
- **Posição da bateria** e passagem dos fios da bateria e da saída: fora de
  escopo.
