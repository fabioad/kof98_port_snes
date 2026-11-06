# Correção dos 100 casos de agarrão comum — 06/11/2026

## Escopo e status

Correção **no código-fonte**, cobrindo os 100 casos da auditoria:
50 personagens × agarrão para frente/trás. Os 19 personagens com dano de
1–2 HP receberam reparos; os outros 31 permanecem sob regressão.

O autor confirmou que as adaptações de golpes são intencionais e que o
port está no limite de recursos. O objetivo desta etapa é corrigir falhas
funcionais e evitar glitches; preservar essas adaptações, sem expandir arte
ou exigir fidelidade integral aos pacotes MUGEN.

**Sem build de ROM ou geração de assets nesta alteração.** A auditoria
headless anterior continua descrevendo a ROM antiga. Os testes desta correção
validam dados/timelines em memória; a execução dos 100 casos no SNES fica para
depois de uma compilação futura. Não se trata de 100 golpes diferentes.

## O que mudou

- `tools/normal_throws.py` restaura as fases de captura/impacto dentro do
  slot 75, onde o motor mantém a vítima presa. Não acrescenta slots nativos
  nem sprites; reaproveita as poses de agarrão já selecionadas pelo gerador.
- Kyo/Nests/Ash e Shermie têm timelines longas o suficiente para alcançar
  seus eventos de dano, sem trocar o índice do impacto por um quadro inicial.
- Vice, Kensou, Chang e Brian têm dano calibrado para 200 HP, dentro de um
  byte com sinal. A emissão de dano de agarrão fora dessa faixa agora falha
  explicitamente, em vez de transformar o valor em cura.
- Andy e Ryo incluem o follow-up `811`; Lucky inclui `311 → 312 × 8 → 313`;
  Rugal mantém oito contatos antes da finalização.
- Leona usa a timeline do agarrão normal `805`, em vez da mecânica do super
  `3305`; Mai usa o HitDef terrestre `800` e a fase `801`, preservando o
  comando já ligado ao slot 74.
- Athena usa a fase normal `810`; o impacto de Chizuru/Mature e o dano dos
  victim states de Billy/Omega são representados por eventos de vida do
  atacante, pois o motor não executa esses victim states MUGEN completos.
- O retorno ao neutro passa pela soltura existente, incluindo a direção do
  back throw. Turns de origem não desfazem a escolha frente/trás.
- `StThrow` respeita o VelSet autoral quando há o bit de movimento, em vez
  de zerar VX a cada tick. Fases achatadas conservam o reset de velocidade
  de entrada, como o finalizador de Ryo.
- Os Makefiles incluem o módulo novo entre as dependências dos dados de luta.

Continuam sendo adaptações nativas: poses já residentes, holds limitados e
loops com número fixo de contatos. Isso corrige os contratos de agarrão/dano
identificados, sem declarar equivalência visual integral ao MUGEN.

## Dano dos eventos corrigidos

Valores no fonte, sem contar o contato inicial da captura; **não são novas
medições na ROM**:

- Kyo/Nests/Ash e Ryo: 40 HP.
- Rugal: oito contatos de 6 HP, total 48.
- Omega Rugal: oito contatos de 3 HP + 5 no final, total 29.
- Leona: 22 HP.
- Mature, Chang e Billy: 30 HP.
- Vice e Kensou: 28 HP.
- Andy: 24 + 12 HP, total 36.
- Athena: 15 HP.
- Mai e Chizuru: 20 HP.
- Shermie: 26 HP.
- Lucky: oito contatos de 4 HP, total 32.
- Brian: 29 HP.

## Pads

O padrão vale para os 50 personagens: **Y=WP, X=SP, B=WK, A=SK**;
**L=esquiva normal, L+trás=esquiva para trás, L+frente=esquiva para frente,
R=blowback**. A correção preserva as rotas e macros existentes. A regressão
confere os quatro ataques em pé, agachados e no ar para todas as entradas.

## Validação e reprodução

Resultado desta alteração: **295 testes passaram**, incluindo os contratos
dos 100 casos e a regressão do padrão de pads dos 50 personagens.
`git diff --check` também passou.

```sh
python3 -W ignore::ResourceWarning -m unittest tools.tests.test_normal_throw_repairs
python3 -W ignore::ResourceWarning -m unittest discover -s tools/tests
```

A cobertura dos 100 casos verifica roteamento da captura, dano com byte
assinado em 100/200 HP, alcance dos eventos dentro da animação, duração
limitada, binds nas duas orientações, saída para neutro, ausência de Turn
indevido, ausência de novos sprites/slots e preservação dos outros 31.
São contratos de fonte, não execução do processador 65816.

`tools/audit_release_throws_headless.py` agora exige **dano final** suficiente,
sem aumento de HP durante o golpe e com os flags de agarrão limpos. Assim,
um golpe que causa dano e depois cura, ou que só captura/solta, não passa.

Depois de uma compilação futura, executar:

```sh
python3 tools/audit_release_throws_headless.py
python3 tools/audit_release_throws_headless.py --chars vice kensou chang shermie brian --hp 100 --out build/release_audit_20261105/throw_healing_after_fix.json
python3 tools/test_back_throw_headless.py
```

As pendências de especiais/supers da
[auditoria original](RELEASE_MOVE_AUDIT_2026-11-05.md) permanecem separadas
destes 100 casos de agarrão comum.
