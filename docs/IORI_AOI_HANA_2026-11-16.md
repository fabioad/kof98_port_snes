# Iori — Aoi Hana completo (16/11/2026)

Correção de fechamento da v2.0.0 para o **Iori Yagami**.

## Sintoma

O comando **baixo, baixo-trás, trás + soco** (Aoi Hana / 127-shiki) só
executava as duas primeiras partes no port. A terceira parte — o salto com as
duas mãos que derruba o adversário — nunca aparecia.

## Causa

Os estados 1200/1201 e 1210/1211 da fonte marcam a vítima com `fall`/
`air.fall`. O caminho de acerto nativo interpretava isso como nocaute já no
primeiro contato e mandava a vítima para `S_DOWN`. Com a vítima no chão, a
segunda parte não conectava e a terceira (1202/1212) ficava inalcançável.

Além disso, a fonte encadeava as partes automaticamente por `MoveHit`. O
jogo de arcade exige um novo **QCB + soco** em cada parte, podendo alternar
entre fraco e forte.

## Correção

- **Partes 1 e 2 sem nocaute:** sids 61/63/66/68 entram em `slice_no_fall`.
- **Pushback curto:** `gvx`/`grvx` reduzidos para 1 px/tick, mantendo a
  vítima ao alcance da próxima parte.
- **Encadeamento por comando (engine):**
  - novo `CHAINTAB` por personagem com linhas
    `origem, alvo-fraco, alvo-forte, alvo-CPU`;
  - `TransAir` tipo 6 confirma `F_HITDONE` e procura um QCB+P no buffer,
    aceitando apenas os dois alvos da linha;
  - `CmdTryChain` reutiliza o matcher de comandos com filtro de alvo, então
    um QCB+P normal nunca entra no meio de um rekka por engano;
  - o CPU continua encadeando automaticamente pelo alvo-CPU da tabela.
- **Terceira parte:** 1202 (fraco) e 1212 (forte) mantêm `fall=1` e derrubam
  a vítima. A caixa Clsn1 foi reforçada com uma caixa mais baixa para não
  passar por cima da vítima ainda em hitstun.
- **Pouso:** a terceira parte termina em `S_LAND`; o pouso usa a pose
  genérica de recuperação em vez de criar novos sprites para a 1203.

## Entrada

```
Aoi Hana 1: ↓ ↙ ← + soco fraco/forte
Aoi Hana 2: ↓ ↙ ← + soco fraco/forte
Aoi Hana 3: ↓ ↙ ← + soco fraco/forte
```

As partes podem alternar livremente (fraco → forte → fraco, forte → fraco →
forte, etc.). Sem o novo comando, a parte atual termina normalmente.

## Teste

`tools/test_iori_aoi_hana_headless.py` cobre:

- fraco → forte → fraco (61 → 68 → 62) com nocaute na terceira;
- forte → fraco → forte (66 → 63 → 64) com nocaute na terceira;
- sem follow-up, o golpe não avança para as partes 2/3.
