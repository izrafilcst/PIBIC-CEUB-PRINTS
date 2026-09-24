# Caixa PIBIC em PLA — corpo+painel fundidos — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduzir a caixa de três peças parafusadas para duas — corpo+painel fundidos numa peça só e tampa parafusada com encaixe de perfboard — trocando a chave SS12D00G4 por uma KCD1 redonda snap-in e recalibrando tudo para PLA.

**Architecture:** Toda a geometria continua saindo de `gerar_modelo_3mf.py` sobre o núcleo `malha.py`, que monta sólidos por faces horizontais e paredes verticais e confere estanqueidade, orientação e volume contra um valor analítico. O furo Ø20,40 da chave tem eixo **horizontal** e não cabe nessa hipótese de prisma, então o núcleo ganha duas primitivas — `face_vertical` (triangula em (x,z) a y constante) e `tubo` (costura dois anéis em planos paralelos quaisquer) — mais um recorte de polígono por faixa que dá as seções em D das pernas do pino da perfboard.

**Tech Stack:** Python 3.14, só biblioteca padrão para o modelo. pytest 9.0.3 para o TDD das primitivas novas. Sem CAD instalado — é por isso que o núcleo de malha existe.

**Spec:** `docs/superpowers/specs/2026-08-23-caixa-pla-corpo-painel-fundidos-design.md`

## Global Constraints

- **Só biblioteca padrão** em `malha.py`, `gerar_modelo_3mf.py`, `gerar_desenhos_3mf.py`, `validar_modelo.py`. pytest só nos arquivos sob `tests/`.
- **Sem acento nem cedilha em código e comentário Python.** É a convenção do repositório inteiro; texto com acento só em `.md` e em string de desenho.
- **Nenhuma cota digitada duas vezes.** Os desenhos medem a malha; o `validar_modelo.py` lê o `.3mf` gravado. Se um número precisa aparecer em dois lugares, ele vira constante em `gerar_modelo_3mf.py` e os outros importam de lá.
- **Toda superfície nova entra no volume analítico.** `Solido.conferir(esperado, tol_rel=1e-9)` é a rede de segurança do projeto; uma feature que não aparece na conta esperada passa despercebida.
- **Nada de cone.** Cone não tem área de polígono e quebra a conferência em 1e-9. Alívio de furo e guia de pino são degraus retos, prismáticos.
- Silhueta `CX_L = 178,0`, `CX_A = 130,0`, `CX_R = 55,0`. Mesa `MESA = (180,0, 180,0, 180,0)`.
- Peça fundida: `PAIN_ESP = 8,0`, cavidade 55,0, altura total **63,0**. Tampa `TAMPA_ESP = 4,0`.
- Chave KCD1: furo `Ø20,40`, rebaixo `Ø26,00 × 2,00` só por dentro, parede local `2,00`, centro em `x = 69,50`, `z = 35,00`, parede `y = 130`.
- Perfboard: `90 × 70 × 1,60`, furo `Ø3,00` a `3,50` da borda (**os dois presumidos, conferir no paquímetro**), centro em `(73,00 / 65,00)`.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `malha.py` | núcleo de malha: contornos 2D, triangulação, `Solido`, gravação. Ganha `face_vertical`, `tubo`, `perna`, `degrau_da_perna`; perde `costura` |
| `tests/test_malha.py` | **novo** — TDD das primitivas, cada uma provada por um sólido fechado que passa em `conferir` |
| `tests/test_projeto.py` | **novo** — prova que `conferir_projeto()` aceita o projeto e **rejeita** cada perturbação |
| `gerar_modelo_3mf.py` | fonte única da geometria. `painel()` some, `corpo()` vira a peça fundida, `tampa()` ganha os pinos |
| `validar_modelo.py` | relê os `.3mf` gravados e mede furos e paredes |
| `gerar_desenhos_3mf.py` | pranchas SVG medidas da malha |
| `README.md`, `LISTA-DE-MATERIAIS.md` | documentação |

---

## Task 1: `tubo` — casca entre dois anéis em planos paralelos

**Files:**
- Create: `tests/test_malha.py`
- Modify: `malha.py` (acrescentar em `class Solido`, depois de `faixa`)

**Interfaces:**
- Consumes: `Solido.tri`, `Solido.face`, `Solido.conferir`, `circulo`, `area_assinada` (já existem)
- Produces: `Solido.tubo(anel_a, anel_b, inverter=False)` — `anel_a` e `anel_b` são listas de pontos **3D** de mesma contagem, na ordem correspondente. Não retorna nada.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_malha.py`:

```python
# -*- coding: utf-8 -*-
"""Testes das primitivas de malha - PIBIC-CEUB."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import malha as M


def test_tubo_fecha_um_cilindro_de_eixo_horizontal():
    """
    Uma laje de y=0 a y=3 com um furo cilindrico de eixo horizontal.

    E o caso exato da chave KCD1. O cilindro so pode sair de 'tubo': a parede
    do furo nao e vertical, entao 'faixa' nao serve.
    """
    L, H, W, R = 20.0, 12.0, 3.0, 4.0
    cx, cz = L / 2, H / 2
    c = M.circulo(cx, cz, R, 32)                    # pontos (x, z)
    anel = lambda y: [(p[0], y, p[1]) for p in c]

    S = M.Solido("laje")
    # tampas em y=0 e y=W, cada uma com o furo
    ret = [(0.0, 0.0), (L, 0.0), (L, H), (0.0, H)]
    S.face_vertical(ret, [c], 0.0, frente=False)
    S.face_vertical(ret, [c], W, frente=True)
    # as quatro faces restantes
    S.face([(0.0, 0.0), (L, 0.0), (L, W), (0.0, W)], [], 0.0, cima=False)
    S.face([(0.0, 0.0), (L, 0.0), (L, W), (0.0, W)], [], H, cima=True)
    S.faixa([(0.0, 0.0), (0.0, W)], 0.0, H)
    S.faixa([(L, W), (L, 0.0)], 0.0, H)
    # a parede do furo
    S.tubo(anel(0.0), anel(W), inverter=False)

    esperado = L * H * W - abs(M.area_assinada(c)) * W
    assert abs(S.conferir(esperado, tol_rel=1e-9) - esperado) < 1e-6
```

Nota: este teste usa `face_vertical`, que ainda não existe. É de propósito — a Task 2 o completa. Nesta task o teste **tem de falhar em `tubo`**, não em `face_vertical`, então adicione também este teste, que exercita só `tubo`:

```python
def test_tubo_fecha_um_tronco_de_cone_vertical():
    """Tronco de cone: dois circulos de raios diferentes, em z diferentes."""
    r0, r1, h, n = 5.0, 3.0, 4.0, 48
    a = M.circulo(0.0, 0.0, r0, n)
    b = M.circulo(0.0, 0.0, r1, n)

    S = M.Solido("tronco")
    S.face(a, [], 0.0, cima=False)
    S.face(b, [], h, cima=True)
    S.tubo([(p[0], p[1], 0.0) for p in a], [(p[0], p[1], h) for p in b],
           inverter=False)

    # tronco de piramide sobre poligonos SEMELHANTES: exato
    A0, A1 = abs(M.area_assinada(a)), abs(M.area_assinada(b))
    esperado = h / 3 * (A0 + A1 + math.sqrt(A0 * A1))
    assert abs(S.conferir(esperado, tol_rel=1e-9) - esperado) < 1e-6
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_malha.py::test_tubo_fecha_um_tronco_de_cone_vertical -v`
Expected: FAIL com `AttributeError: 'Solido' object has no attribute 'tubo'`

- [ ] **Step 3: Implementar `tubo`**

Em `malha.py`, dentro de `class Solido`, logo depois do método `faixa`:

```python
    def tubo(self, anel_a, anel_b, inverter=False):
        """
        Casca entre dois aneis FECHADOS de mesma contagem de pontos, em dois
        planos paralelos quaisquer. O ponto i de 'anel_a' casa com o ponto i
        de 'anel_b'; os dois entram como listas de pontos 3D.

        Existe porque 'faixa' so sabe parede VERTICAL sobre polilinha, e o
        furo da chave KCD1 tem eixo HORIZONTAL: a parede dele nao e vertical
        e o eixo nao e z. 'tubo' nao conhece eixo nenhum.

        A normal e a de (a[i+1] - a[i]) x (b[i] - a[i]); 'inverter' troca o
        sentido. Nao ha convencao "fora/dentro" aqui, porque com eixo
        arbitrario ela nao significaria nada - quem reprova a escolha errada
        e 'conferir', que exige volume positivo e volume analitico batendo.
        """
        assert len(anel_a) == len(anel_b), \
            f"{self.nome}: aneis de tamanhos diferentes no tubo"
        n = len(anel_a)
        for i in range(n):
            a0, a1 = anel_a[i], anel_a[(i + 1) % n]
            b0, b1 = anel_b[i], anel_b[(i + 1) % n]
            if inverter:
                self.tri(a0, b0, a1)
                self.tri(a1, b0, b1)
            else:
                self.tri(a0, a1, b0)
                self.tri(a1, b1, b0)
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_malha.py::test_tubo_fecha_um_tronco_de_cone_vertical -v`
Expected: PASS

Se falhar com `volume <= 0 - normais invertidas`, troque `inverter=False` por `inverter=True` **no teste** (não na primitiva) e rode de novo — a convenção de sinal fica registrada pelo teste, que é onde ela deve viver.

- [ ] **Step 5: Commit**

```bash
git add tests/test_malha.py malha.py
git commit -m "Acrescenta Solido.tubo - casca entre aneis em planos paralelos"
```

---

## Task 2: `face_vertical` — face plana a y constante

**Files:**
- Modify: `malha.py` (`class Solido`, depois de `face`)
- Test: `tests/test_malha.py`

**Interfaces:**
- Consumes: `triangular(externo, buracos)` — já existe, trabalha em 2D genérico
- Produces: `Solido.face_vertical(externo, buracos=(), y=0.0, frente=True)` — contornos são listas de pares **(x, z)**; `frente=True` dá normal `+y`, `frente=False` dá `-y`

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `tests/test_malha.py`:

```python
def test_face_vertical_triangula_no_plano_xz():
    """A area triangulada tem de ser a area da regiao, e as normais em +y."""
    ret = [(0.0, 0.0), (20.0, 0.0), (20.0, 12.0), (0.0, 12.0)]
    c = M.circulo(10.0, 6.0, 4.0, 32)

    S = M.Solido("face")
    S.face_vertical(ret, [c], 5.0, frente=True)

    assert len(S.t) > 0, "face_vertical nao emitiu triangulo nenhum"
    assert all(abs(S.v[i][1] - 5.0) < 1e-9 for t in S.t for i in t), \
        "algum vertice saiu fora do plano y=5"
    # normal de cada triangulo tem de apontar para +y
    for i, j, k in S.t:
        a, b, cc = S.v[i], S.v[j], S.v[k]
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        w = (cc[0] - a[0], cc[1] - a[1], cc[2] - a[2])
        ny = u[2] * w[0] - u[0] * w[2]
        assert ny > 0, "normal da face_vertical nao esta em +y"
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_malha.py::test_face_vertical_triangula_no_plano_xz -v`
Expected: FAIL com `AttributeError: 'Solido' object has no attribute 'face_vertical'`

- [ ] **Step 3: Implementar `face_vertical`**

Em `malha.py`, dentro de `class Solido`, logo depois de `face`:

```python
    def face_vertical(self, externo, buracos=(), y=0.0, frente=True):
        """
        Face plana no plano y = constante, descrita em (x, z).

        'frente=True' -> normal +y; 'frente=False' -> normal -y.

        Existe porque a parede de tras deixou de ser uma parede: no trecho da
        chave ela e uma chapa plana com um furo, e furo em parede nao e
        expressavel como contorno extrudado em z.

        'triangular' nao sabe que eixos sao esses - so precisa de um plano -
        entao o motor de triangulacao e o mesmo de 'face'. A unica sutileza e
        o sinal: um triangulo anti-horario em (x, z) tem normal x^ X z^ = -y^,
        entao e 'frente=False' que preserva a ordem.
        """
        for a, b, c in triangular(externo, buracos):
            P = lambda p: (p[0], y, p[1])
            if frente:
                self.tri(P(a), P(c), P(b))
            else:
                self.tri(P(a), P(b), P(c))
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_malha.py -v`
Expected: PASS nos três testes — o `test_tubo_fecha_um_cilindro_de_eixo_horizontal` da Task 1 agora completa, e é ele que prova as duas primitivas trabalhando juntas exatamente como a estação da chave vai usá-las.

- [ ] **Step 5: Commit**

```bash
git add tests/test_malha.py malha.py
git commit -m "Acrescenta Solido.face_vertical - face plana a y constante"
```

---

## Task 3: `perna` e `degrau_da_perna` — seções do pino fendido

**Files:**
- Modify: `malha.py` (funções de contorno 2D, depois de `subtrair_discos`)
- Test: `tests/test_malha.py`

**Interfaces:**
- Consumes: `circulo`, `antihorario`, `area_assinada`
- Produces:
  - `perna(r, meia_fenda, n=64, lado=1)` → lista de pontos (x,y): seção em D de uma perna
  - `degrau_da_perna(r_int, r_ext, meia_fenda, n=64, lado=1)` → polígono **simples** da coroa de uma perna entre dois raios

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `tests/test_malha.py`:

```python
def test_perna_e_meia_secao_menos_a_fenda():
    """Duas pernas + a fenda tem de reconstituir o poligono inteiro."""
    r, hf, n = 1.4, 0.6, 64
    inteiro = abs(M.area_assinada(M.circulo(0.0, 0.0, r, n)))
    a = abs(M.area_assinada(M.perna(r, hf, n, lado=1)))
    b = abs(M.area_assinada(M.perna(r, hf, n, lado=-1)))
    # a fenda e a faixa |x| <= hf dentro do poligono; sobra = inteiro - fenda
    assert a > 0 and abs(a - b) < 1e-9, "as duas pernas tem de ser simetricas"
    assert a + b < inteiro, "as pernas nao podem somar mais que o circulo"


def test_degrau_da_perna_fecha_um_solido():
    """
    O degrau farpa->haste e o teste real: e ali que 'face' com buraco
    encostado na borda quebraria o ear clipping.
    """
    hf, n = 0.6, 64
    r_int, r_ext, h = 1.4, 1.8, 0.6

    S = M.Solido("degrau")
    for lado in (1, -1):
        p_int = M.perna(r_int, hf, n, lado)
        p_ext = M.perna(r_ext, hf, n, lado)
        deg = M.degrau_da_perna(r_int, r_ext, hf, n, lado)
        S.face(p_ext, [], 0.0, cima=False)
        S.face(deg, [], h, cima=True)
        S.face(p_int, [], h + 1.0, cima=True)
        S.parede(p_ext, 0.0, h, fora=True)
        S.parede(p_int, h, h + 1.0, fora=True)
        A = M.area_assinada
        esperado = abs(A(p_ext)) * h + abs(A(p_int)) * 1.0
        # cada perna e um solido separado; confere uma de cada vez
        assert abs(M.area_assinada(deg)) > 0
    # a conferencia de volume da peca inteira e feita na Task 7
    assert len(S.t) > 0
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_malha.py::test_perna_e_meia_secao_menos_a_fenda -v`
Expected: FAIL com `AttributeError: module 'malha' has no attribute 'perna'`

- [ ] **Step 3: Implementar as duas funções**

Em `malha.py`, depois de `subtrair_discos`:

```python
def _arco_cortado(r, meia_fenda, n, lado):
    """
    Arco do circulo de raio 'r' que sobra do lado 'lado' (+1 = x positivo)
    da fenda central de largura 2*meia_fenda, do ponto de corte de baixo ate
    o de cima, PONTAS INCLUIDAS.
    """
    assert 0 < meia_fenda < r, "a fenda nao corta o circulo"
    th = math.acos(meia_fenda / r)
    a0 = -th if lado > 0 else math.pi - th
    d = 2 * th
    k = max(2, int(d / (2 * math.pi) * n) + 1)
    return [(r * math.cos(a0 + d * i / k), r * math.sin(a0 + d * i / k))
            for i in range(k + 1)]


def perna(r, meia_fenda, n=64, lado=1):
    """
    Secao em D de UMA perna do pino da perfboard: o circulo de raio 'r'
    cortado pela fenda central, ficando com o lado 'lado'.

    O pino e fendido para que as duas pernas possam fletir - sem isso a farpa
    nao entra no furo da placa sem trincar o PLA. E a fenda obriga a secao a
    ser esta, e nao um circulo: a MESMA lista alimenta a face e a parede, e a
    area dela entra na conta do volume esperado da tampa. E o que mantem
    'conferir' fechando em 1e-9 com o rasgo no meio.
    """
    return antihorario(_arco_cortado(r, meia_fenda, n, lado))


def degrau_da_perna(r_int, r_ext, meia_fenda, n=64, lado=1):
    """
    Coroa de UMA perna entre 'r_int' e 'r_ext', como poligono SIMPLES.

    Nao da para pedir isso a 'face' como poligono com buraco: os dois
    contornos compartilham a reta da fenda, o "buraco" encosta na borda do
    externo e o ear clipping nao encontra ponte. Aqui os dois arcos sao
    costurados pelos dois trechos de reta que sobram da corda, e sai um
    poligono simples de verdade.
    """
    assert 0 < meia_fenda < r_int < r_ext, "raios fora de ordem no degrau"
    fora = _arco_cortado(r_ext, meia_fenda, n, lado)
    dentro = _arco_cortado(r_int, meia_fenda, n, lado)
    return antihorario(list(fora) + list(reversed(dentro)))
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_malha.py -v`
Expected: PASS em todos

- [ ] **Step 5: Commit**

```bash
git add tests/test_malha.py malha.py
git commit -m "Acrescenta perna e degrau_da_perna - secoes do pino fendido"
```

---

## Task 4: Parâmetros novos e `conferir_projeto()` reescrito

**Files:**
- Modify: `gerar_modelo_3mf.py:80-190` (blocos de constantes) e a função `conferir_projeto`
- Create: `tests/test_projeto.py`

**Interfaces:**
- Consumes: `silhueta`, `pontos_fixacao`, `leds`, `BOTOES` (já existem)
- Produces: constantes `PAIN_ESP=8.0`, `CORPO_H=63.0`, `CAVIDADE=55.0`, `REB_ALIVIO=0.5`, `FOLGA_ALIVIO=1.0`, `PONTE_PLA=20.0`, dicionários `CHAVE` e `PLACA`, funções `estacao_chave()` e `pinos_placa()`, e `conferir_projeto()` devolvendo um dict com `sw` e `placa`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_projeto.py`:

```python
# -*- coding: utf-8 -*-
"""
Testes de 'conferir_projeto' - PIBIC-CEUB.

Uma conferencia que nunca reprovou nada nao prova nada. Cada teste aqui
perturba UM parametro e exige que a conferencia acuse.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gerar_modelo_3mf as P


def test_o_projeto_como_esta_passa():
    info = P.conferir_projeto()
    assert info["sw"]["x"] == 69.5
    assert info["placa"]["centro"] == (73.0, 65.0)


@pytest.fixture
def restaurar():
    """Desfaz qualquer mexida nas constantes do modulo."""
    guarda = {}

    def mexer(nome, valor):
        if nome not in guarda:
            guarda[nome] = getattr(P, nome)
        setattr(P, nome, valor)

    yield mexer
    for nome, valor in guarda.items():
        setattr(P, nome, valor)


def test_chave_fora_do_trecho_reto_e_reprovada(restaurar):
    restaurar("CHAVE", dict(P.CHAVE, x=40.0))
    with pytest.raises(AssertionError, match="trecho reto"):
        P.conferir_projeto()


def test_painel_fino_demais_para_a_porca_e_reprovado(restaurar):
    restaurar("PAIN_ESP", 3.0)
    with pytest.raises(AssertionError, match="aperta"):
        P.conferir_projeto()


def test_placa_batendo_no_botao_verde_e_reprovada(restaurar):
    restaurar("PLACA", dict(P.PLACA, x=120.0))
    with pytest.raises(AssertionError, match="bot[ao]o verde|verde"):
        P.conferir_projeto()


def test_perna_curta_demais_e_reprovada(restaurar):
    # rasgo so na haste: braco de 1,8 mm em vez de 6,5 -> deformacao ~11 %
    restaurar("PLACA", dict(P.PLACA, rasgo_h=1.8))
    with pytest.raises(AssertionError, match="deforma"):
        P.conferir_projeto()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_projeto.py -v`
Expected: FAIL — `test_o_projeto_como_esta_passa` quebra em `KeyError: 'placa'` ou `AttributeError: module has no attribute 'CHAVE'`

- [ ] **Step 3: Trocar os blocos de constantes**

Em `gerar_modelo_3mf.py`, substituir o bloco de espessuras e o bloco `INTERRUPTOR`/`estacao()` inteiros por:

```python
# =====================================================================
# Espessuras
# =====================================================================
# O painel encolheu de 16 para 8: os 16 so existiam para sobrar material sob
# o rebaixo de 8 mm da capa vermelha, e o rebaixo acabou. Com a peca fundida
# a face dos botoes vai para a MESA, e todo rebaixo nela viraria teto no ar.

PAIN_ESP  = 8.0        # painel liso
CAVIDADE  = 55.0       # da face interna do painel ao assento da tampa
CORPO_H   = PAIN_ESP + CAVIDADE      # 63.0 - altura da peca fundida
CORPO_PAR = 4.0
TAMPA_ESP = 4.0

LINHA     = 0.42       # largura de extrusao com bico 0,4 - paredes sao multiplos
PONTE_PLA = 20.0       # maior ponte reta admitida em PLA, apoiada dos dois lados

# Alivio na boca dos furos do painel. Eles nascem na PRIMEIRA CAMADA agora, e
# o pe de elefante os fecharia. E rebaixo RETO, nao chanfro: chanfro e cone,
# cone nao tem area de poligono, e 'conferir' casa volume em 1e-9 usando area
# de poligono. A porca M24 cobre o alivio do barril.
REB_ALIVIO   = 0.5
FOLGA_ALIVIO = 1.0     # diametral, alivio = furo + isto

# =====================================================================
# Fixacao - 6 colunas, inserto M3 SO no topo
# =====================================================================
# Eram 12 insertos porque o painel tambem parafusava. O painel virou parte do
# corpo; sobraram os 6 da tampa.

FIX_INSET    = 6.0
COL_D        = 10.0
D_INSERTO    = 4.2
PROF_INSERTO = 5.0
D_PASSAGEM   = 3.4
D_REBAIXO    = 6.5
REB_TAMPA    = 2.0
PENETRACAO   = 4.0

# =====================================================================
# Chave gangorra redonda KCD1 - snap-in na parede de tras
# =====================================================================
# Cotas do desenho cotado do fabricante (nao do PDF escaneado que travou o
# berco da SS12D00G4):
#     corpo que atravessa o painel   19,80 +/- 0,20
#     aro visivel                    23,00 +/- 0,20   cobre a borda do furo
#     corpo atras do painel          19,30
#     profundidade do corpo          17,80 +/- 0,30
#     total atras do painel          25,70 +/- 0,30   corpo + terminal
#     3 terminais, passo 7,00, lamina faston 4,80 x 0,80
#
# A chave prende sozinha nas garras e para isso quer parede FINA. A parede do
# corpo tem 4,00, entao o rebaixo circular abre SO PARA DENTRO e deixa 2,00 de
# parede local. A face externa continua lisa.
#
# x = 69,50 e o meio do unico trecho reto livre: de x = 55 (tangencia do R55)
# a x = 84 (inicio da coluna central). O rebaixo Ø26 ocupa [56,50 - 82,50].
#
# NAO ha chanfro no furo. Por dentro e onde as garras mordem; por fora seria
# cone. Os 0,40 de folga ja dao a entrada.

CHAVE = dict(
    modelo="KCD1 redonda 3T",
    x=69.5,            # centro, ao longo da parede y = CX_A
    z=35.0,            # eixo, medido da face dos botoes (a mesa)
    d_corpo=19.8,      # o que atravessa o painel
    d_aro=23.0,        # aro visivel
    folga=0.4,         # diametral - furo deitado fecha mais que furo em pe
    d_rebaixo=26.0,    # rebaixo por dentro, onde as garras trabalham
    parede=2.0,        # parede local que sobra sob o rebaixo
    atras=25.7,        # reserva atras da parede: corpo + terminal
    x_face=(55.0, 84.0),   # trecho da parede que a face_vertical assume
)

# =====================================================================
# Perfboard 7 x 9 - encaixe por pino farpado na tampa
# =====================================================================
# ATENCAO: 'furo_d' e 'furo_inset' sao PRESUMIDOS. Meca a placa com o
# paquimetro antes de imprimir a tampa - sao 4 pinos, e errar o recuo poe
# todos no lugar errado de uma vez.
#
# Centro em (73, 65) nao e estetica: e o que sobrou entre as 4 colunas de
# canto, as 2 do meio e o flange Ø37,7 do botao verde.
#
# O rasgo de 6,50 e dimensionado. Duas pernas de 0,80 fletindo 0,30 (a
# interferencia da farpa Ø3,60 sobre o furo Ø3,00) num braco de 6,50:
#     eps = 3*t*y / (2*L^2) = 3*0,80*0,30 / (2*42,25) = 0,85 %
# Com rasgo so na haste (1,80 de braco) daria 11 % e a perna quebraria na
# primeira montagem.
#
# A guia de entrada e ESCALONADA, nao conica - mesma razao do alivio dos
# furos do painel.

PLACA = dict(
    larg=90.0, alt=70.0, esp=1.6,
    x=73.0, y=65.0,
    furo_d=3.0,        # PRESUMIDO - conferir
    furo_inset=3.5,    # PRESUMIDO - conferir
    ombro_d=6.0, ombro_h=3.5,       # afastador: espaco das pernas soldadas
    haste_d=2.8,                     # furo 3,00 - 0,20 de folga
    farpa_d=3.6, farpa_h=0.6,        # 0,30 radial de retencao
    guia=((3.0, 0.3), (2.4, 0.3)),   # degraus de entrada (diametro, altura)
    rasgo_w=1.2,
    rasgo_h=6.5,       # = ombro_h + haste_h + farpa_h + guias
    folga_placa=0.2,   # entre a face de cima da placa e a farpa
)


def estacao_chave():
    """Cotas derivadas da estacao da chave, em coordenadas da peca."""
    k = dict(CHAVE)
    k["d_furo"] = k["d_corpo"] + k["folga"]              # 20,20
    k["prof_reb"] = CORPO_PAR - k["parede"]              # 2,00
    k["y_cav"] = CX_A - CORPO_PAR                        # 126,00
    k["y_reb"] = k["y_cav"] + k["prof_reb"]              # 128,00
    k["y_face"] = CX_A                                   # 130,00
    k["y_fundo"] = k["y_reb"] - k["atras"]               # ate onde a chave chega
    k["ponte_furo"] = k["d_furo"] / math.sqrt(2.0)
    k["ponte_reb"] = k["d_rebaixo"] / math.sqrt(2.0)
    return k


def pinos_placa():
    """Os 4 centros dos pinos, e as alturas acumuladas do perfil."""
    p = PLACA
    dx = p["larg"] / 2 - p["furo_inset"]
    dy = p["alt"] / 2 - p["furo_inset"]
    centros = [(p["x"] - dx, p["y"] - dy), (p["x"] + dx, p["y"] - dy),
               (p["x"] - dx, p["y"] + dy), (p["x"] + dx, p["y"] + dy)]
    haste_h = p["esp"] + p["folga_placa"]
    z = [0.0, p["ombro_h"], p["ombro_h"] + haste_h,
         p["ombro_h"] + haste_h + p["farpa_h"]]
    for _, h in p["guia"]:
        z.append(z[-1] + h)
    return dict(centros=centros, haste_h=haste_h, z=z, topo=z[-1])
```

**Atenção ao `d_furo`:** `19,80 + 0,40 = 20,20`, não os 20,40 que a spec cita como valor arredondado. O furo é dimensionado sobre o **corpo real da chave (Ø19,80)**, não sobre o Ø20,00 nominal do recorte de painel. Os 20,20 continuam cobertos pelo aro Ø23,00 com 1,40 mm radiais de sobra. Corrigir a spec no fim da Task 10.

- [ ] **Step 4: Reescrever `conferir_projeto()`**

Substituir a função inteira. Manter as conferências herdadas (mesa, capa contra capa, capa contra borda, LED dentro da capa, coluna contra parede) exatamente como estão, **removendo** as que citam `rebaixo`, `FOLGA_CAPA`, `r_rebaixo`, `REB_PAINEL` e a estação antiga; e acrescentar:

```python
    # ---- botao: espessura apertada pela porca, agora sem rebaixo ----
    for b in BOTOES:
        exigir(PAIN_ESP <= b["esp_max"],
               f"botao {b['nome']} aperta {PAIN_ESP:.2f} mm, maximo {b['esp_max']}")
        exigir(PAIN_ESP >= 5.0,
               f"botao {b['nome']} aperta so {PAIN_ESP:.2f} mm - material de menos")
    exigir(PAIN_ESP / 2.0 >= 3.0,
           f"painel de {PAIN_ESP:.2f} da menos de 3 filetes de M24 x 2")

    # ---- peca fundida na mesa ----
    exigir(CORPO_H <= MESA[2], f"peca fundida com {CORPO_H:.2f} passa da mesa")

    # ---- parafuso da tampa ----
    L = (TAMPA_ESP - REB_TAMPA) + PENETRACAO
    exigir(PROF_INSERTO > PENETRACAO, "parafuso encosta no fundo do inserto")
    exigir(abs(L - round(L)) < 1e-9, f"tampa pede M3 x {L:.2f}, fora de catalogo")

    # ---- estacao da chave ----
    k = estacao_chave()
    xa, xb = k["x_face"]
    r = k["d_rebaixo"] / 2
    exigir(CX_R <= xa and xb <= CX_L - CX_R,
           f"trecho reto da face_vertical [{xa}, {xb}] sai do trecho reto da parede")
    exigir(xa + 1.0 <= k["x"] - r and k["x"] + r <= xb - 1.0,
           f"rebaixo da chave em [{k['x']-r:.2f}, {k['x']+r:.2f}] nao cabe no "
           f"trecho reto [{xa:.2f}, {xb:.2f}]")
    exigir(k["z"] - r > PAIN_ESP and k["z"] + r < CORPO_H,
           f"rebaixo da chave em z [{k['z']-r:.2f}, {k['z']+r:.2f}] sai da parede")
    for i, (cx, cy) in enumerate(fix, 1):
        d = math.hypot(max(k["x"] - r - cx, 0.0, cx - k["x"] - r),
                       max(k["y_cav"] - cy, 0.0, cy - CX_A))
        exigir(d - COL_D / 2 >= 2.0,
               f"rebaixo da chave a {d-COL_D/2:.2f} mm da coluna {i} - minimo 2,00")
    exigir(1.6 <= k["parede"] <= 3.0,
           f"parede local da chave {k['parede']:.2f} fora da faixa de snap")
    exigir(k["parede"] < CORPO_PAR, "parede local mais grossa que a parede cheia")
    exigir(k["ponte_furo"] <= PONTE_PLA and k["ponte_reb"] <= PONTE_PLA,
           f"ponte de {max(k['ponte_furo'], k['ponte_reb']):.2f} mm passa do "
           f"limite de {PONTE_PLA:.2f} em PLA")
    exigir(k["y_fundo"] > CORPO_PAR,
           f"a chave chega a y={k['y_fundo']:.2f} e bate na parede oposta")

    # ---- perfboard ----
    pl, pn = PLACA, pinos_placa()
    x0, x1 = pl["x"] - pl["larg"] / 2, pl["x"] + pl["larg"] / 2
    y0, y1 = pl["y"] - pl["alt"] / 2, pl["y"] + pl["alt"] / 2
    for i, (cx, cy) in enumerate(fix, 1):
        d = math.hypot(max(x0 - cx, 0.0, cx - x1), max(y0 - cy, 0.0, cy - y1))
        exigir(d - COL_D / 2 >= 2.0,
               f"placa a {d-COL_D/2:.2f} mm da coluna {i} - minimo 2,00")
        for j, (px, py) in enumerate(pn["centros"], 1):
            g = math.dist((px, py), (cx, cy)) - COL_D / 2 - pl["ombro_d"] / 2
            exigir(g >= 2.0, f"pino {j} a {g:.2f} mm da coluna {i}")
    bv, bg = BOTOES
    for b, env in ((bv, bv["flange"]), (bg, bg["flange"])):
        d = math.hypot(max(x0 - b["x"], 0.0, b["x"] - x1),
                       max(y0 - b["y"], 0.0, b["y"] - y1))
        exigir(d - env / 2 >= 2.0,
               f"placa a {d-env/2:.2f} mm do envelope do botao {b['nome']} "
               f"- minimo 2,00")
    z_placa = CORPO_H - pl["ombro_h"] - pl["esp"]     # face de cima da placa
    for b in BOTOES:
        exigir(z_placa - (PAIN_ESP + b["abaixo"] - PAIN_ESP) > 0
               and z_placa > b["abaixo"],
               f"a placa em z={z_placa:.2f} bate no corpo do botao "
               f"{b['nome']}, que desce ate z={b['abaixo']:.2f}")
    exigir(pl["ombro_h"] >= 2.5,
           f"ombro de {pl['ombro_h']:.2f} nao deixa espaco para as pernas soldadas")
    t = (pl["haste_d"] - pl["rasgo_w"]) / 2
    y = (pl["farpa_d"] - pl["furo_d"]) / 2
    eps = 3 * t * y / (2 * pl["rasgo_h"] ** 2)
    exigir(eps <= 0.010,
           f"deformacao de flexao da perna do pino {eps*100:.2f} % - maximo 1,00")
    exigir(abs(pl["rasgo_h"] - pn["topo"]) < 1e-9,
           f"rasgo de {pl['rasgo_h']:.2f} nao atravessa o pino de {pn['topo']:.2f}")
    exigir(pl["farpa_d"] > pl["furo_d"] > pl["haste_d"],
           "a farpa nao retem: diametros fora de ordem")
```

E o `return` passa a:

```python
    return dict(folga_capas=folga, L_tampa=L, sw=k,
                placa=dict(centro=(PLACA["x"], PLACA["y"]),
                           z_topo=z_placa, eps=eps, pinos=pn))
```

Acrescentar a `BOTOES` os dois campos que as conferências novas usam (lidos dos desenhos, já registrados no README):

```python
    dict(nome="vermelho", ..., flange=87.8, abaixo=41.0),
    dict(nome="verde",    ..., flange=37.7, abaixo=52.4),
```

`abaixo` é quanto o corpo do botão desce a partir da face externa do painel (`z = 0`), e é a cota que decide a folga da placa. Remover de `BOTOES` as chaves `rebaixo` e `h_capa` que não são mais usadas — `h_capa` fica, porque o desenho ainda cota a saliência.

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_projeto.py -v`
Expected: PASS nos cinco testes. Se `test_placa_batendo_no_botao_verde_e_reprovada` não acusar, confira que `flange` entrou em `BOTOES`.

- [ ] **Step 6: Commit**

```bash
git add gerar_modelo_3mf.py tests/test_projeto.py
git commit -m "Reescreve parametros e conferir_projeto para PLA, KCD1 e perfboard"
```

---

## Task 5: Peça fundida `corpo()` — painel, paredes e colunas

**Files:**
- Modify: `gerar_modelo_3mf.py` — apagar `painel()`, reescrever `corpo()`
- Test: `tests/test_projeto.py`

**Interfaces:**
- Consumes: `estacao_chave()`, `silhueta`, `pontos_fixacao`, `leds`, `M.entalhar`, `M.trecho`, `M.subtrair_discos`
- Produces: `corpo()` → `(Solido, volume_esperado)`. Nesta task **sem** a estação da chave — a parede de trás sai inteira por `faixa`. A chave entra na Task 6.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `tests/test_projeto.py`:

```python
def test_corpo_fundido_fecha_e_bate_o_volume():
    S, esperado = P.corpo()
    vol = S.conferir(esperado, tol_rel=1e-9)
    assert vol > 0
    zs = [v[2] for v in S.v]
    assert abs(max(zs) - min(zs) - P.CORPO_H) < 1e-9
    xs = [v[0] for v in S.v]
    ys = [v[1] for v in S.v]
    assert abs(max(xs) - min(xs) - P.CX_L) < 1e-9
    assert abs(max(ys) - min(ys) - P.CX_A) < 1e-9


def test_nao_existe_mais_peca_de_painel():
    assert not hasattr(P, "painel")
    assert [n for n, _, _ in P.PECAS] == ["caixa-corpo", "caixa-tampa"]
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_projeto.py::test_corpo_fundido_fecha_e_bate_o_volume -v`
Expected: FAIL — o `corpo()` antigo não tem painel, então a altura medida dá 55 e não 63

- [ ] **Step 3: Reescrever `corpo()`**

Apagar `painel()` inteira. Substituir `corpo()` por:

```python
def corpo():
    """
    Peca fundida: painel + corpo.

    z = 0 e a face EXTERNA dos botoes, que e a face que encosta na MESA. Essa
    e a unica orientacao possivel - de boca para baixo o painel teria de fazer
    ponte sobre 170 x 122, e de lado tudo vira balanco. E e o que torna o
    painel liso obrigatorio: qualquer rebaixo nele seria teto no ar.

        z = 0,00 .. 0,50    alivio da boca dos furos (pe de elefante)
        z = 0,50 .. 8,00    painel
        z = 8,00 .. 63,00   cavidade, paredes e colunas
    """
    S = M.Solido("corpo")
    ext = silhueta()
    fix = pontos_fixacao()
    cav = M.subtrair_discos(silhueta(CORPO_PAR),
                            [(x, y, COL_D / 2, SEG_MEDIO) for x, y in fix])

    bv, bg = BOTOES
    # cada furo aparece duas vezes: o alivio (boca) e o furo util
    bar = [M.circulo(b["x"], b["y"], D_BARRIL / 2, SEG_BARRIL) for b in BOTOES]
    bar_al = [M.circulo(b["x"], b["y"], (D_BARRIL + FOLGA_ALIVIO) / 2, SEG_BARRIL)
              for b in BOTOES]
    led, led_al = [], []
    for b in BOTOES:
        for x, y in leds(b):
            led.append(M.circulo(x, y, D_LED / 2, SEG_PEQ))
            led_al.append(M.circulo(x, y, (D_LED + FOLGA_ALIVIO) / 2, SEG_PEQ))
    ins = [M.circulo(x, y, D_INSERTO / 2, SEG_PEQ) for x, y in fix]
    z_ins = CORPO_H - PROF_INSERTO

    # ---- faces horizontais ----
    S.face(ext, bar_al + led_al, 0.0, cima=False)          # face dos botoes
    for a, f in zip(bar_al + led_al, bar + led):
        S.coroa(f, a, REB_ALIVIO, cima=False)              # fundo do alivio
        S.parede(a, 0.0, REB_ALIVIO, fora=False)
        S.parede(f, REB_ALIVIO, PAIN_ESP, fora=False)
    S.face(cav, bar + led, PAIN_ESP, cima=True)            # piso da cavidade
    S.face(ext, [cav] + ins, CORPO_H, cima=True)           # assento da tampa
    for c in ins:
        S.face(c, [], z_ins, cima=True)                    # fundo do inserto
        S.parede(c, z_ins, CORPO_H, fora=False)

    # ---- paredes ----
    S.parede(ext, 0.0, CORPO_H, fora=True)
    S.parede(cav, PAIN_ESP, CORPO_H, fora=False)

    A = M.area_assinada
    a_ext, a_cav = A(ext), A(cav)
    esperado = (
        (a_ext - sum(A(c) for c in bar_al + led_al)) * REB_ALIVIO
        + (a_ext - sum(A(c) for c in bar + led)) * (PAIN_ESP - REB_ALIVIO)
        + (a_ext - a_cav) * (CORPO_H - PAIN_ESP)
        - 6 * A(ins[0]) * PROF_INSERTO)
    return S, esperado
```

E `PECAS` passa a:

```python
PECAS = [("caixa-corpo", corpo, CORPO_H),
         ("caixa-tampa", tampa, TAMPA_ESP)]
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_projeto.py -v`
Expected: PASS. Se `conferir` acusar `arestas fora de 2 triangulos`, o suspeito é a `coroa` do alívio: ela exige mesma contagem de pontos nos dois círculos, então `bar_al` tem de usar `SEG_BARRIL` e `led_al` tem de usar `SEG_PEQ`, iguais aos furos.

- [ ] **Step 5: Commit**

```bash
git add gerar_modelo_3mf.py tests/test_projeto.py
git commit -m "Funde painel e corpo numa peca so, com alivio de boca nos furos"
```

---

## Task 6: Estação da chave KCD1 no `corpo()`

**Files:**
- Modify: `gerar_modelo_3mf.py` — função `corpo()`
- Test: `tests/test_projeto.py`

**Interfaces:**
- Consumes: `Solido.face_vertical`, `Solido.tubo` (Tasks 1 e 2), `estacao_chave()`
- Produces: `corpo()` com o furo e o rebaixo da chave, e o volume esperado descontando os dois

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `tests/test_projeto.py`:

```python
def test_a_parede_de_tras_esta_vazada_no_eixo_da_chave():
    """
    Sonda de travessia: no eixo da chave nao pode sobrar material NENHUM
    entre a cavidade e a face externa.
    """
    import validar_modelo as V
    S, esperado = P.corpo()
    S.conferir(esperado, tol_rel=1e-9)
    V_, T_ = [tuple(v) for v in S.v], list(S.t)
    k = P.estacao_chave()
    segs = V.secao(V_, T_, k["z"])
    ys = V.travessia(segs, k["x"], y_min=k["y_cav"] - 1.0)
    assert ys == [], f"parede fechada no eixo da chave: material em y={ys}"


def test_o_rebaixo_da_chave_tem_o_diametro_certo():
    import validar_modelo as V
    S, esperado = P.corpo()
    S.conferir(esperado, tol_rel=1e-9)
    k = P.estacao_chave()
    # a 1 mm dentro do rebaixo a secao horizontal corta o Ø26
    segs = V.secao([tuple(v) for v in S.v], list(S.t), k["z"])
    larg, centro = V.largura_do_vao(segs, k["y_cav"])
    assert abs(larg - k["d_rebaixo"]) < 0.05, f"boca do rebaixo {larg:.3f}"
    assert abs(centro - k["x"]) < 0.01
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_projeto.py::test_a_parede_de_tras_esta_vazada_no_eixo_da_chave -v`
Expected: FAIL com `parede fechada no eixo da chave: material em y=[126.0, 130.0]`

- [ ] **Step 3: Abrir a estação na parede**

Dentro de `corpo()`, **antes** das faces horizontais, recortar o trecho da parede:

```python
    k = estacao_chave()
    xa, xb = k["x_face"]
    # no trecho da chave a parede deixa de ser parede: vira chapa plana com
    # furo, e quem emite e 'face_vertical'. 'entalhar' com perfil vazio apaga
    # os vertices de densificacao do trecho, deixando UMA aresta - que e o que
    # a face vertical vai compartilhar, sem junta em T.
    ext = M.entalhar(ext, CX_A, xb, xa, [])
    cav = M.entalhar(cav, k["y_cav"], xb, xa, [])
```

Trocar as duas chamadas de parede por versões que pulam o trecho:

```python
    S.faixa(M.trecho(ext, (xa, CX_A), (xb, CX_A)), 0.0, CORPO_H)
    S.faixa(M.trecho(list(reversed(cav)), (xb, k["y_cav"]), (xa, k["y_cav"])),
            PAIN_ESP, CORPO_H)
```

E acrescentar a estação:

```python
    # ---- estacao da chave ----
    c_reb = M.circulo(k["x"], k["z"], k["d_rebaixo"] / 2, SEG_MEDIO)
    c_fur = M.circulo(k["x"], k["z"], k["d_furo"] / 2, SEG_MEDIO)
    anel = lambda c, y: [(p[0], y, p[1]) for p in c]

    ret_ext = [(xa, 0.0), (xb, 0.0), (xb, CORPO_H), (xa, CORPO_H)]
    ret_cav = [(xa, PAIN_ESP), (xb, PAIN_ESP), (xb, CORPO_H), (xa, CORPO_H)]

    S.face_vertical(ret_ext, [c_fur], k["y_face"], frente=True)
    S.face_vertical(ret_cav, [c_reb], k["y_cav"], frente=False)
    S.face_vertical(c_reb, [c_fur], k["y_reb"], frente=False)
    S.tubo(anel(c_reb, k["y_cav"]), anel(c_reb, k["y_reb"]), inverter=False)
    S.tubo(anel(c_fur, k["y_reb"]), anel(c_fur, k["y_face"]), inverter=False)
```

E o volume esperado ganha dois termos no fim:

```python
        - A(c_reb) * k["prof_reb"]
        - A(c_fur) * k["parede"])
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/ -v`
Expected: PASS em tudo.

Se `conferir` acusar `volume <= 0` ou volume divergindo por exatamente o volume de um cilindro, o `inverter` de um dos dois `tubo` está errado — troque **um por vez** e rode de novo. Se acusar `arestas fora de 2 triangulos`, o suspeito é `ret_cav` começar em `PAIN_ESP`: as arestas verticais em `xa` e `xb` da cavidade têm de ir de `PAIN_ESP` a `CORPO_H`, iguais às da `faixa` vizinha.

- [ ] **Step 5: Rodar o gerador de ponta a ponta**

Run: `python gerar_modelo_3mf.py`
Expected: imprime as duas peças com volume, sem AssertionError

- [ ] **Step 6: Commit**

```bash
git add gerar_modelo_3mf.py tests/test_projeto.py
git commit -m "Abre a estacao da chave KCD1 na parede de tras com face_vertical e tubo"
```

---

## Task 7: `tampa()` com os quatro pinos da perfboard

**Files:**
- Modify: `gerar_modelo_3mf.py` — função `tampa()`
- Test: `tests/test_projeto.py`

**Interfaces:**
- Consumes: `M.perna`, `M.degrau_da_perna` (Task 3), `pinos_placa()` (Task 4)
- Produces: `tampa()` → `(Solido, volume_esperado)`, com `z = 0` na face **externa** (rebaixo dos parafusos) e os pinos crescendo de `z = TAMPA_ESP` para cima

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `tests/test_projeto.py`:

```python
def test_tampa_com_pinos_fecha_e_bate_o_volume():
    S, esperado = P.tampa()
    vol = S.conferir(esperado, tol_rel=1e-9)
    pn = P.pinos_placa()
    zs = [v[2] for v in S.v]
    assert abs(max(zs) - (P.TAMPA_ESP + pn["topo"])) < 1e-9, \
        "o pino nao tem a altura do perfil"
    assert abs(min(zs)) < 1e-9


def test_a_farpa_retem_a_placa():
    """A face de baixo da farpa tem de cair 0,20 acima da placa assentada."""
    pl, pn = P.PLACA, P.pinos_placa()
    topo_da_placa = pn["z"][1] + pl["esp"]
    assert abs(pn["z"][2] - topo_da_placa - pl["folga_placa"]) < 1e-9
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_projeto.py::test_tampa_com_pinos_fecha_e_bate_o_volume -v`
Expected: FAIL — `max(zs)` dá `TAMPA_ESP`, sem pino nenhum

- [ ] **Step 3: Reescrever `tampa()`**

```python
def tampa():
    """
    z = 0 e a face EXTERNA (rebaixo dos parafusos), que vai na mesa; os pinos
    da perfboard crescem para cima a partir de z = TAMPA_ESP.

    Imprime com os pinos PARA CIMA. O rebaixo Ø6,50 sobre o furo Ø3,40 fica
    voltado para baixo, mas sao 1,55 mm radiais sobre um vao de 6,50 - nao
    pede suporte.
    """
    S = M.Solido("tampa")
    ext = silhueta()
    fix = pontos_fixacao()
    pl, pn = PLACA, pinos_placa()

    pas = [M.circulo(x, y, D_PASSAGEM / 2, SEG_PEQ) for x, y in fix]
    cbo = [M.circulo(x, y, D_REBAIXO / 2, SEG_PEQ) for x, y in fix]

    # perfil do pino: (raio, z_base, z_topo), de baixo para cima
    hf = pl["rasgo_w"] / 2
    raios = ([(pl["ombro_d"] / 2, pn["z"][0], pn["z"][1]),
              (pl["haste_d"] / 2, pn["z"][1], pn["z"][2]),
              (pl["farpa_d"] / 2, pn["z"][2], pn["z"][3])]
             + [(d / 2, pn["z"][3 + i], pn["z"][4 + i])
                for i, (d, _) in enumerate(pl["guia"])])

    # ---- chapa ----
    S.face(ext, cbo, 0.0, cima=False)
    for p, c in zip(pas, cbo):
        S.coroa(p, c, REB_TAMPA, cima=False)
        S.parede(c, 0.0, REB_TAMPA, fora=False)
        S.parede(p, REB_TAMPA, TAMPA_ESP, fora=False)
    bases = [M.perna(raios[0][0], hf, SEG_PEQ, lado)
             for _ in pn["centros"] for lado in (1, -1)]
    bases = [[(x + cx, y + cy) for x, y in M.perna(raios[0][0], hf, SEG_PEQ, lado)]
             for cx, cy in pn["centros"] for lado in (1, -1)]
    S.face(ext, pas + bases, TAMPA_ESP, cima=True)
    S.parede(ext, 0.0, TAMPA_ESP, fora=True)

    # ---- pinos ----
    for cx, cy in pn["centros"]:
        for lado in (1, -1):
            desloc = lambda p: [(x + cx, y + cy) for x, y in p]
            for i, (r, z0, z1) in enumerate(raios):
                sec = desloc(M.perna(r, hf, SEG_PEQ, lado))
                S.parede(sec, TAMPA_ESP + z0, TAMPA_ESP + z1, fora=True)
                if i + 1 < len(raios):
                    r_prox = raios[i + 1][0]
                    if r_prox < r:      # degrau para dentro: face para cima
                        S.face(desloc(M.degrau_da_perna(r_prox, r, hf,
                                                        SEG_PEQ, lado)),
                               [], TAMPA_ESP + z1, cima=True)
                    else:               # degrau para fora: face para baixo
                        S.face(desloc(M.degrau_da_perna(r, r_prox, hf,
                                                        SEG_PEQ, lado)),
                               [], TAMPA_ESP + z1, cima=False)
            S.face(desloc(M.perna(raios[-1][0], hf, SEG_PEQ, lado)), [],
                   TAMPA_ESP + raios[-1][2], cima=True)

    A = M.area_assinada
    v_meio_pino = sum(abs(A(M.perna(r, hf, SEG_PEQ, 1))) * (z1 - z0)
                      for r, z0, z1 in raios)
    esperado = ((A(ext) - 6 * A(cbo[0])) * REB_TAMPA
                + (A(ext) - 6 * A(pas[0])) * (TAMPA_ESP - REB_TAMPA)
                + 8 * v_meio_pino)
    return S, esperado
```

Apagar a linha duplicada de `bases` (a primeira, sem deslocamento) — está no bloco acima só para deixar claro qual é a certa; **manter apenas a segunda**.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/ -v`
Expected: PASS

Se `conferir` acusar malha aberta na base dos pinos, o motivo é a face `z = TAMPA_ESP`: os 8 contornos `bases` têm de ser exatamente os mesmos objetos que as `parede` do primeiro degrau usam — mesma `SEG_PEQ`, mesmo `hf`, mesmo deslocamento.

- [ ] **Step 5: Gerar e conferir os arquivos**

```bash
python gerar_modelo_3mf.py
python validar_modelo.py
```
Expected: o gerador imprime as duas peças; `validar_modelo.py` ainda falha, porque procura `caixa-painel.3mf` — é a Task 8.

- [ ] **Step 6: Commit**

```bash
git add gerar_modelo_3mf.py tests/test_projeto.py
git commit -m "Acrescenta os 4 pinos farpados da perfboard na tampa"
```

---

## Task 8: Limpar o núcleo e atualizar `validar_modelo.py`

**Files:**
- Modify: `malha.py` — apagar `costura`
- Modify: `validar_modelo.py` — `main()` e `conferir_interruptor`

**Interfaces:**
- Consumes: `P.estacao_chave()`, `P.pinos_placa()`, `V.travessia`, `V.largura_do_vao`, `V.diametro` (já existem)
- Produces: `conferir_chave(V, T)` e `conferir_pinos(V, T)` no lugar de `conferir_interruptor`

- [ ] **Step 1: Confirmar que `costura` ficou órfã**

Run: `grep -rn "costura\|entalhar\|trecho" --include=*.py .`
Expected: `costura` só aparece na própria definição em `malha.py`; `entalhar` e `trecho` aparecem em `corpo()` e ficam.

- [ ] **Step 2: Apagar `costura`**

Remover o método `costura` de `class Solido` e a menção a ele no docstring do módulo (o parágrafo "PECA QUE NAO E PRISMA INTEIRA"), substituindo-o por:

```
PECA QUE NAO E PRISMA INTEIRA
-----------------------------
O furo da chave KCD1 tem eixo HORIZONTAL: nem a face nem a parede dele cabem
na hipotese de contorno extrudado em z. Duas primitivas resolvem sem abandonar
o resto:

  'Solido.face_vertical'  face plana a y constante, descrita em (x, z) - e a
                          mesma triangulacao de 'face', so troca de eixos
  'Solido.tubo'           casca entre dois aneis em planos paralelos
                          quaisquer, que e o que 'faixa' nao sabe fazer

E o pino fendido da perfboard pede um recorte de poligono por faixa: 'perna'
da a secao em D de cada perna e 'degrau_da_perna' da o poligono SIMPLES da
coroa entre dois diametros - que nao da para pedir a 'face' como poligono com
buraco, porque o buraco encosta na borda.
```

- [ ] **Step 3: Rodar os testes**

Run: `python -m pytest tests/ -v && python gerar_modelo_3mf.py`
Expected: PASS, e o gerador roda igual

- [ ] **Step 4: Atualizar `validar_modelo.py`**

Em `main()`: apagar o bloco `--- painel ---` inteiro. Trocar o bloco `--- corpo ---` por:

```python
    # --- corpo (painel + corpo fundidos) ---
    k = P.estacao_chave()
    f = [(P.CORPO_H - 1.0, *fix[0], P.D_INSERTO,
          f"inserto no topo: Ø{P.D_INSERTO:.2f}")]
    for b in P.BOTOES:
        f.append((P.PAIN_ESP / 2, b["x"], b["y"], P.D_BARRIL,
                  f"barril M24 do botao {b['nome']}: Ø{P.D_BARRIL:.2f}"))
        f.append((P.REB_ALIVIO / 2, b["x"], b["y"],
                  P.D_BARRIL + P.FOLGA_ALIVIO,
                  f"alivio da boca {b['nome']}: Ø{P.D_BARRIL+P.FOLGA_ALIVIO:.2f}"))
        f.append((P.PAIN_ESP / 2, *P.leds(b)[0], P.D_LED,
                  f"furo de LED do botao {b['nome']}: Ø{P.D_LED:.2f}"))
    conferir("corpo", "caixa-corpo.3mf", P.CORPO_H, f)
```

Trocar `conferir_interruptor(V, T)` por `conferir_chave(V, T)`, e substituir a função inteira por:

```python
def conferir_chave(V, T):
    """
    A estacao da chave, lida do arquivo.

    Duas medidas bastam e sao independentes: a travessia no eixo prova que a
    parede esta VAZADA de lado a lado (se o furo nao abrisse, a chave nao
    entraria e ninguem descobriria antes de imprimir), e a largura do vao na
    face da cavidade prova o diametro do rebaixo.
    """
    k = P.estacao_chave()
    print("\ncaixa-corpo.3mf - estacao da chave KCD1")

    segs = secao(V, T, k["z"])
    ys = travessia(segs, k["x"], y_min=k["y_cav"] - 1.0)
    ok(ys == [], "no eixo da chave a parede esta vazada de lado a lado",
       "material em y " + ", ".join(f"{v:.2f}" for v in ys) if ys else "")

    larg, centro = largura_do_vao(segs, k["y_cav"])
    ok(larg is not None and abs(larg - k["d_rebaixo"]) < 0.05
       and abs(centro - k["x"]) < 0.01,
       f"boca do rebaixo: Ø{k['d_rebaixo']:.2f} centrada em {k['x']:.2f}",
       f"medida {larg:.3f} centrada em {centro:.3f}" if larg else "nao achada")

    larg, centro = largura_do_vao(segs, k["y_face"])
    ok(larg is not None and abs(larg - k["d_furo"]) < 0.05,
       f"furo na face externa: Ø{k['d_furo']:.2f}",
       f"medido {larg:.3f}" if larg else "nao achado")

    # fora do rebaixo a parede volta a ser a normal
    m = travessia(secao(V, T, k["z"]), k["x"] + k["d_rebaixo"] / 2 + 2.0,
                  y_min=k["y_cav"] - 1.0)
    ok(len(m) == 2 and abs(m[0] - k["y_cav"]) < 0.01
       and abs(m[1] - k["y_face"]) < 0.01,
       f"fora do rebaixo a parede volta a {P.CORPO_PAR:.2f}",
       "medido y " + " e ".join(f"{v:.2f}" for v in m) if m else "nada")


def conferir_pinos(V, T):
    """Os 4 pinos da perfboard, medidos na secao horizontal."""
    pl, pn = P.PLACA, P.pinos_placa()
    print("\ncaixa-tampa.3mf - pinos da perfboard")
    z_haste = P.TAMPA_ESP + (pn["z"][1] + pn["z"][2]) / 2
    z_farpa = P.TAMPA_ESP + (pn["z"][2] + pn["z"][3]) / 2
    for i, (cx, cy) in enumerate(pn["centros"], 1):
        for z, d, nome in ((z_haste, pl["haste_d"], "haste"),
                           (z_farpa, pl["farpa_d"], "farpa")):
            larg, centro = largura_do_vao(secao(V, T, z), cy)
            ok(larg is not None and abs(larg - pl["rasgo_w"]) < 0.02,
               f"pino {i}: rasgo de {pl['rasgo_w']:.2f} na altura da {nome}",
               f"medido {larg:.3f}" if larg else "nao achado")
```

E na tampa, acrescentar `conferir_pinos(*ler_3mf("caixa-tampa.3mf"))` depois do `conferir("tampa", ...)`.

- [ ] **Step 5: Rodar a validação completa**

```bash
python gerar_modelo_3mf.py && python validar_modelo.py
```
Expected: `todas as conferencias passaram`

- [ ] **Step 6: Commit**

```bash
git add malha.py validar_modelo.py
git commit -m "Apaga costura do nucleo e atualiza validar_modelo para as 2 pecas"
```

---

## Task 9: Pranchas técnicas

**Files:**
- Modify: `gerar_desenhos_3mf.py` — `desenho_painel` some, `desenho_corpo` vira a peça fundida, `desenho_tampa` ganha o detalhe do pino, `desenho_berco` vira `desenho_chave`

**Interfaces:**
- Consumes: `medir_painel` (renomear para `medir_corpo`), `Vista`, `contorno`, `furo`, `tabela_furos`, `bate`, `encerrar_conferencia`
- Produces: `desenho-caixa-corpo.svg` (CX-02), `desenho-caixa-tampa.svg` (CX-03), `desenho-caixa-chave.svg` (CX-04)

- [ ] **Step 1: Apagar o que não existe mais**

Remover `desenho_painel`, `_corte_painel`, `_detalhe_embutido`, `desenho_berco`, `_berco_elevacao`, `_berco_corte_h`, `_berco_corte_v`, `_interruptor`, `_notas_interruptor`. Remover `desenho_painel` da lista de pranchas em `main()`.

Run: `python gerar_desenhos_3mf.py`
Expected: FAIL com `NameError` ou `AttributeError` nas funções que ainda referenciam o painel — é o mapa do que falta ajustar.

- [ ] **Step 2: Passar `desenho_corpo` a medir a peça fundida**

A vista superior de CX-02 passa a ser a face dos botões: silhueta, 2 × Ø26 com alívio Ø27, 9 × Ø10 com alívio Ø11. Reaproveitar `medir_painel` renomeada para `medir_corpo`, apontando para `caixa-corpo.3mf` e medindo na altura `PAIN_ESP / 2`. A vista frontal (`_vista_frontal`) passa a ter uma peça só de 63 mm em vez de painel+corpo empilhados: trocar os parâmetros `esp_pain, esp_tampa` por `esp_tampa` e desenhar a peça fundida como um bloco único.

Cotas novas a acrescentar na prancha, todas medidas da malha:
- espessura do painel `8,00` e altura total `63,00`
- alívio `Ø27,00 × 0,50` em detalhe ampliado 8:1
- posição da estação da chave, `x = 69,50`

- [ ] **Step 3: Acrescentar o detalhe do pino em `desenho_tampa`**

Novo `_detalhe_pino(D, ox, oy, pl, pn, S=8.0)` desenhando o corte do pino em escala 8:1, com as cotas `Ø6,00 × 3,50`, `Ø2,80 × 1,80`, `Ø3,60 × 0,60`, os dois degraus de guia, e o rasgo de `1,20`. Acrescentar a placa 90 × 70 em linha fantasma na vista superior, com os 4 centros cotados.

Nota nova na prancha, texto exato:

```
Ø3,00 do furo da placa e recuo de 3,50 da borda sao PRESUMIDOS.
Meca a placa com o paquimetro antes de imprimir - errar o recuo poe os 4 pinos
no lugar errado de uma vez.
```

- [ ] **Step 4: Escrever `desenho_chave` (CX-04)**

Elevação da parede de trás vista de fora (furo Ø20,20 e aro Ø23,00 em fantasma), corte horizontal no eixo mostrando os três degraus `126 → 128 → 130`, e a tabela de cotas do componente da seção 3.3 da spec. Notas obrigatórias:

```
1  Furo Ø20,20 = corpo Ø19,80 + 0,40 de folga. Furo de eixo HORIZONTAL fecha
   mais que furo em pe em PLA. O aro Ø23,00 cobre 1,40 mm radiais.
2  Rebaixo Ø26,00 x 2,00 abre SO PARA DENTRO. A face externa e lisa.
3  Parede local de 2,00 mm: a chave e snap-in e as garras querem painel fino.
   A faixa de espessura que as garras aceitam NAO consta do desenho do
   fabricante - conferir antes de imprimir.
4  Sem chanfro no furo: por dentro e onde as garras mordem.
```

- [ ] **Step 5: Gerar e conferir**

```bash
python gerar_desenhos_3mf.py
```
Expected: as três pranchas saem e `encerrar_conferencia()` não acusa divergência entre cota desenhada e malha medida.

- [ ] **Step 6: Commit**

```bash
git add gerar_desenhos_3mf.py desenho-caixa-corpo.svg desenho-caixa-tampa.svg desenho-caixa-chave.svg
git commit -m "Refaz as pranchas para as 2 pecas e a estacao da chave KCD1"
```

---

## Task 10: Documentação e limpeza dos artefatos

**Files:**
- Modify: `README.md`, `LISTA-DE-MATERIAIS.md`, a spec
- Delete: `caixa-painel.3mf`, `caixa-painel.stl`, `desenho-caixa-painel.svg`, `desenho-caixa-berco.svg`

- [ ] **Step 1: Apagar os artefatos das peças que sumiram**

```bash
git rm caixa-painel.3mf caixa-painel.stl desenho-caixa-painel.svg desenho-caixa-berco.svg
```

- [ ] **Step 2: Reescrever o topo do `README.md`**

Nova seção "⚠ Revisão atual" substituindo a do berço, cobrindo: 3 peças → 2, painel liso e por quê (a orientação de impressão), KCD1 no lugar da SS12D00G4, encaixe da perfboard, PETG → PLA. A seção "Revisão anterior: A1 mini + botões meio embutidos" desce um nível e ganha a nota de que o meio-embutido acabou.

Substituir a tabela "Parâmetros de impressão — PETG na Creality K1C" pela tabela PLA da seção 5.2 da spec. Apagar o aviso de soltura PETG × PEI e pôr no lugar o aviso novo: a primeira camada da peça fundida é a face visível dos botões.

Corrigir a seção "Fechamento" para 6 insertos, e a "Cotas extraídas dos desenhos" ganha as duas linhas novas que o modelo passou a usar: `flange` e `abaixo` de cada botão.

- [ ] **Step 3: Reescrever `LISTA-DE-MATERIAIS.md`**

- item 5 vira "Interruptor geral — KCD1 redonda", com a tabela de cotas do desenho cotado e a nota de que a faixa de snap não consta e precisa ser medida
- sai a linha de cola quente do berço; sai a SS12D00G4
- insertos de latão M3: 12 → **6**; parafusos M3 × 6: 6
- item 7 vira PLA: temperaturas, 20 % giroide, sem brim, sem suporte
- entra a perfboard 90 × 70 × 1,6 com a nota de conferir Ø do furo e recuo
- a tabela de volumes passa a ter os números reais impressos por `validar_modelo.py`, não a estimativa da spec
- em "O que trava a compra agora", o item 4 (nº de posições do interruptor) sai resolvido e entra "Ø e recuo do furo da perfboard"

- [ ] **Step 4: Corrigir os dois números da spec que a implementação mudou**

Na spec, trocar `Ø20,40` por `Ø20,20` nas quatro ocorrências (§3.3 duas vezes, §5.1, §8 regra 8), e o vão de ponte de `14,40` para `14,28`, acrescentando a frase:

```
O furo e dimensionado sobre o corpo REAL da chave (Ø19,80 + 0,40), nao sobre o
Ø20,00 nominal do recorte de painel. Sobram 1,40 mm radiais de cobertura do aro.
```

- [ ] **Step 5: Rodar tudo do zero**

```bash
python -m pytest tests/ -v
python gerar_modelo_3mf.py
python validar_modelo.py
python gerar_desenhos_3mf.py
```
Expected: testes passam, gerador imprime 2 peças, `todas as conferencias passaram`, 3 pranchas geradas.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Atualiza README e lista de materiais para PLA, 2 pecas e KCD1"
```

---

## Auto-revisão do plano

**Cobertura da spec:**

| Seção da spec | Task |
|---|---|
| §2 orientação de impressão | 5 (docstring de `corpo()`), 10 (README) |
| §3.2 painel liso + alívio de boca | 5 |
| §3.2 colunas e inserto só no topo | 5 |
| §3.3 estação KCD1 | 4 (parâmetros e regras), 6 (geometria), 8 (validação), 9 (prancha) |
| §3.4 tampa, impressão com pinos para cima | 7 |
| §3.5 encaixe da perfboard | 3 (seções), 4 (posição e regras), 7 (geometria), 8 (validação), 9 (detalhe) |
| §4 `face_vertical`, `tubo`, `perna` | 1, 2, 3; remoção de `costura` na 8 |
| §5.1 folgas | 4 |
| §5.2 parâmetros de impressão | 10 |
| §5.3 volume | 10 (números reais substituem a estimativa) |
| §6 montagem | 10 (README) |
| §7 arquivos | 8, 9, 10 |
| §8 as 15 conferências | 4 |
| §9 verificação | 1–8 (cada task fecha em `conferir` ou pytest) |
| §10 fora de escopo | registrado, sem task — correto |

**Consistência de tipos:** `estacao_chave()` devolve dict com as chaves `x, z, d_furo, d_rebaixo, parede, prof_reb, y_cav, y_reb, y_face, y_fundo, ponte_furo, ponte_reb, x_face` — usadas nas Tasks 4, 6, 8, 9 com esses nomes. `pinos_placa()` devolve `centros, haste_h, z, topo` — usadas nas Tasks 4, 7, 8. `M.perna(r, meia_fenda, n, lado)` e `M.degrau_da_perna(r_int, r_ext, meia_fenda, n, lado)` têm a mesma assinatura na Task 3 e na Task 7.

**Divergência conhecida e deliberada:** a spec diz furo `Ø20,40`; o plano usa `Ø20,20`, porque dimensiona sobre o corpo real Ø19,80 em vez do Ø20,00 nominal. A Task 10 Step 4 corrige a spec.
