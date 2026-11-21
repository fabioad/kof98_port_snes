# Team Play: paleta do lutador muda após a primeira luta (21/11/2026)

## Sintoma

No Team Play, depois do primeiro combate, o lutador do jogador passa a
aparecer com a paleta de outro personagem: às vezes todo preto, às vezes com
cores erradas. O mesmo trecho também podia desviar a transição de
round/stage (glitches no cenário).

## Causa

`ThrowTechFx` e `LaunchVictim` (em `src/engine/menucore.asm`) rodam com o
acumulador em **16 bits** (`rep #$20` / `.ACCU 16`) e faziam:

```asm
lda #SFX_THROW.b
jsr SfxPlay
```

Como o acumulador está em 16 bits, o assembler gera um imediato de 16 bits
(`A9 0F 20`), consumindo o opcode `JSR` (`$20`) como byte alto. Os bytes que
sobram (`26 84`) são executados como `ROL $84`, uma rotação de 16 bits da
palavra `nextflag/sel1`. Resultado: a cada arremesso (ou tech de arremesso),
`sel1` dobra (`$15 -> $2A -> $54`) e `nextflag` também gira. O `SfxPlay`
nunca era chamado, então o som de impacto do arremesso também sumia.

No Team Play, quando o P2 troca de membro, o `TeamSwap` chama
`LoadCharPals`, que recarrega a paleta dos **dois** lados usando `sel1` e
`sel2`. Com `sel1` dobrado, o P1 sobrevivente recebe a paleta de outro
personagem, embora continue com o `F_CHAR` correto — daí o lutador "mudar de
cor". A rotação de `nextflag` é o que pode desviar a transição e causar o
glitch de stage.

No Single Play o mesmo defeito fazia o round seguinte carregar outro
personagem; o `SAFE1`/`MkSanitizeFar` adicionado em 21/11 restaura o `sel1`
no início da luta, mas não corrige a causa.

## Correção

Antes dos dois `lda #SFX_*.b`, colocar o acumulador em 8 bits:

```asm
sep #$20
.ACCU 8
lda #SFX_GUARD.b
jmp SfxPlay
```

e

```asm
sep #$20
.ACCU 8
lda #SFX_THROW.b
jsr SfxPlay
rts
```

Com isso o imediato ocupa um byte, o `JMP/JSR SfxPlay` executa de verdade e
o `ROL $84` deixa de existir. `StateRet` e `BackThrowReleaseFar` já
restabelecem `A16` na entrada, então o retorno em 8 bits não quebra os
chamadores.

## Verificação

- Watchpoint de escrita em `sel1` (`$1085`) no Mesen, Single VS com Athena
  e rodada longa (a IA arremessa):
  - antes: escritas em `$1085` nos quadros 1396 e 4135, `$15 -> $2A -> $54`,
    com PC `$F2:7FEF`;
  - depois: nenhuma escrita em `$1085` durante a rodada.
- `tools/test_team_swap_palette_headless.py`: PASS.
- `tools/test_team_swap_headless.py`: 6/6 PASS.
- Teste estrutural novo:
  `tools/tests/test_throw_sel1_corruption.py` (2 passed).

Build de verificação no worktree `v2.0.2`:

- `.sfc` SHA-256 `2270f3876c929ea7f6497986…`
- `.msu` SHA-256 `a5e4ea293bb5b0258bf09351…`

> A build do worktree principal precisa ser refeita para incluir a
> correção; o `.sfc` de 01:55 ainda é anterior a ela.
