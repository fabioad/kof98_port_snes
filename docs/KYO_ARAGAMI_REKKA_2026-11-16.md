# Kyo — Aragami/Dokugami completo (16/11/2026)

Correção de fechamento da v2.0.0 para o **Kyo Kusanagi** (e as formas
Nests/Ash).

## Sintoma

O comando **baixo, baixo-frente, frente + soco** (Aragami/Dokugami) parava
na segunda parte. A terceira parte — Kyo agarra o adversário com a mão,
levanta e derruba com uma explosão de fogo — não existia no port.

Além disso, a fonte encadeava as partes automaticamente por `MoveHit`. O
jogo de arcade exige um novo **QCF + soco** em cada parte, podendo alternar
entre fraco e forte.

## Causa

- Os estados 1600/1700 e 1605/1710 da fonte auto-encadeavam por `MoveHit`;
  o jogador não precisava (nem conseguia) repetir o comando.
- O estado 1605 marca `fall=1`, então a vítima caía já na segunda parte e a
  terceira ficava inalcançável.
- O terceiro estado (1630 → 1631) não tinha slot/runtime no port: o golpe
  de agarrar e explodir nunca era compilado.

## Correção

- **Partes 1 e 2 sem nocaute:** sids 61/63/66/68 entram em `slice_no_fall`.
- **Pushback curto:** `gvx`/`grvx` reduzidos para 1 px/tick para manter a
  vítima ao alcance da próxima parte.
- **Encadeamento por comando (engine):**
  - `CHAINTAB` com linhas `origem, alvo-fraco, alvo-forte, alvo-CPU`;
  - `TransAir` tipo 6 confirma `F_HITDONE` e procura um QCF+P no buffer,
    aceitando apenas os alvos da linha;
  - `CmdTryChain` filtra os alvos, então um QCF+P normal nunca entra no meio
    do rekka por engano;
  - o CPU continua encadeando automaticamente pelo alvo-CPU.
- **Terceira parte (1630/1631):** os estados foram ligados aos sids 115/116
  e reutilizam a animação 1405 (Koto Tsuki You), cujos cels do grupo 1400 já
  estão no banco ROM do Kyo. O HitDef de 1630 é tratado como acerto normal
  com redirecionamento da vítima para o slot segurado (76), porque o gate de
  throw nativo recusa vítimas em hitstun. Em 1631, o `TargetBind` levanta a
  vítima, o `TargetLifeAdd` aplica o dano e dois `Explod` compartilhados
  (`MagicBurst`/`FlameRise`) desenham a explosão; no elemento seguinte a
  vítima é liberada no slot de arremesso (77) e cai.

## Entrada

```
Aragami 1: ↓ ↘ → + soco fraco/forte
Aragami 2: ↓ ↘ → + soco fraco/forte
Aragami 3: ↓ ↘ → + soco fraco/forte (agarra + explosão de fogo)
```

As partes podem alternar livremente (fraco → forte → fraco, forte → fraco →
forte, etc.). Sem o novo comando, a parte atual termina normalmente.

## Teste

`tools/test_kyo_aragami_headless.py` cobre:

- fraco → forte → agarrão (61 → 68 → 115/116) com a vítima segurada,
  arremessada e caída;
- forte → fraco → agarrão (66 → 63 → 115/116);
- sem follow-up, o golpe não avança para as partes 2/3.
