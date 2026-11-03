# Música do WINNER sem loop (03/11/2026)

O tema de vitória (`SONG_WIN` / W.mid) é um módulo SNESMOD. O player SPC
reinicia o módulo quando a sequência chega ao fim (`Module_ChangePosition`
trata a ordem 255 como "volta ao início"), então o W.mid podia recomeçar
se a tela de vencedor permanecesse além de uma passagem.

O `TitleTick` já encerra a tela de vencedor após 420 frames (7 s). Nesse
ponto ele agora salta para `StopWinnerMusic` (banco 50, `$0FB0`), que
envia `SPC_MUS_STOP` via `SfxPlay` e só então continua para `TT_start`.
Assim o W.mid para antes de a próxima tela carregar a música dela; não há
reinício/loop.

- `test_team_banner_headless`: PASS nos quatro casos (P1/P2, Team Play e
  Team Versus).
- `test_single_campaign_headless`: PASS em cinco vitórias consecutivas.

Build: `build/teamfix_benimaru_20261103/`, checksum **`$EE3A`**, layout
**`0xC276`**. Copie `.sfc` e `.msu` juntos.
