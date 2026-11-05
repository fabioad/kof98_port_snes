# Entrada do próximo membro no Team Play / Team Versus — 03/11/2026

## Comportamento

Depois que um membro é derrotado, o próximo integrante do time:

1. começa **fora do quadro visível**, oculto na borda mais próxima do ponto
   de entrada;
2. entra num **pulo lateral** até a **distância da intro** — o mesmo vão de
   96 px usado no começo do round, preservando a posição do sobrevivente;
3. aterrissa, faz a **intro** normal do personagem (`S_INTRO`, anim 191) e
   só então o FIGHT/round começa.

A câmera fica congelada no enquadramento da intro (sobrevivente + ponto de
entrada) enquanto o novo membro está no ar; o BG não persegue o pulo.

Isso vale apenas para **Team Play** e **Team Versus**. Single Play, Single
Versus, SURVIVOR e PRACTICE continuam com a intro normal, sem pulo.

## Implementação

- `TeamSwap` guarda o alvo de cada lado em `T_ENTERX`/`T_ENTERX2`, enquadra a
  câmera com os alvos e chama `TeamJumpSetup`.
- `TeamJumpSetup`/`TeamJumpOne` colocam o(s) novo(s) membro(s) na borda mais
  próxima do alvo, no chão, com `vx = delta*9` (8.8/tick) e `vy = -6
  px/tick`. Os 5 primeiros ticks ficam sem sprite (`F_META=0`) para o
  membro surgir de fora do quadro já no ar.
- O estado 43 (`S_TJUMP`, antes um slot de AnimTab não despachado) usa a
  animação de pulo para frente do personagem (sid 15) e integra a posição
  manualmente — sem `AddXClamped`, para a posição fora da tela sobreviver.
  Ao aterrissar, encaixa em `T_ENTERX`/`T_ENTERX2` e entra em `S_INTRO`.
- `T_ENTERFLAG` (bit0 P1, bit1 P2) congela o `camx` em `ShakeScroll` até o
  último membro aterrissar. `StartFight` e o fim da intro limpam a flag.
- Como o estado 43 passou a ter código e a animação de pulo entrou no
  conjunto de CHR, o `.msu` foi regerado. O layout (`0x3E20`) mudou junto
  com o novo conjunto de CHR; copie `.sfc` e `.msu` deste build juntos.

## Verificação

- `test_team_swap_headless` (6 casos, agora esperando o pouso): PASS —
  entradas de P1/P2 a partir de sobreviventes em 24/80/100/176/190/232.
- `test_team_vs_start_headless`: P1 e P2 escolhem, luta 1 inicia, KO do P2
  leva à luta 2 com o pulo/entrada — PASS.
- Team Versus com P1 perdendo o primeiro membro e com KO duplo (os dois
  times entram): PASS.
- `test_team_banner_headless` (4 casos), `test_team_swap_palette_headless`,
  `test_round_banner_headless`, `test_single_campaign_headless`,
  `test_midfight_join_headless`: PASS.
- `test_msu_chr_visibility_headless` (960 páginas) e
  `test_super_stage_vram_headless`: PASS.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$DAE7`**
- layout MSU **`0x3E20`**
- `.sfc` SHA-256 `3bcd1a54…25ed0a`
- `.msu` SHA-256 `285ef936…5b279d` (copie os dois juntos)

> O ROM mudou depois desta correção (mount do Ralf e AI_ScanMove). Este é o
> par atual; veja `docs/RALF_MOUNT_AI_FREEZE_2026-11-03.md`.
