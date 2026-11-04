# Ralf: mount do Running Super e travamento da demo — 03/11/2026

## 1. Dois Ralfs no Running Super

O primeiro HitDef do Running Super (sids 87/88 e o grab do sid 103) não
estava marcado como throw. Sem esse bit, o caminho nativo gravava
`F_GRAB = 0x3` na vítima, ou seja, ela usava os próprios sprites **e** a
fonte de animação do Ralf (`ChangeAnim2`). O resultado era o Ralf montado
sobre um segundo Ralf.

A correção marca os três HitDefs como throw em `tools/build_fight.py`
(`hitdef_override`). A vítima passa a ficar com `F_GRAB = 0x1`: é presa pelo
mount, mas continua desenhada com os próprios quadros. A sequência completa
continua funcionando (12 socos + arremesso final, dano e retorno do Ralf ao
estado 0).

## 2. Travamento na demo CPU vs CPU (Ralf Kick)

A causa não era o Ralf Kick em si. Em `AI_ScanMove` (o seletor de golpes da
CPU), o deslocamento da linha da tabela (`idx*6 + 12`) era calculado com o
acumulador em 8 bits. O byte alto (B) do acumulador fica com lixo depois de
`LDA`/`ADC` de 8 bits, e o `TAY` seguinte roda com os registradores de índice
em 16 bits: ele copiava esse lixo para o byte alto de Y. A leitura
`[sptr],y` saía da tabela e trazia um byte qualquer como "sid".

Quando o byte sorteado era 52/53, a CPU executava o Ralf Kick normal — o
golpe que aparecia na demo. Quando era um valor fora da faixa (o caso
reproduzido devolvia 164), o `EnterState` indexava fora da `StateTab` e
saltava para código/ROM não relacionado: o jogo travava de vez.

Correções:

- `AI_scan_loop` calcula `idx*6 + 12` em 16 bits antes do `tay` e volta para
  8 bits só na leitura do byte. Isso elimina o lixo em B e mantém a leitura
  dentro da tabela.
- `EnterState` ganhou uma checagem de faixa: qualquer estado acima de
  `S_EXT_LAST` (111) cai em `S_STAND` em vez de indexar fora da `StateTab`.
  É uma proteção de segurança para futuras regressões; com a correção acima
  nenhum estado inválido é mais pedido.

## Verificação

- `test_ralf_mount_headless`: a vítima entra em `S_VHELD` com
  `F_GRAB = 0x1`, os socos causam dano (199 → 177) e o Ralf volta ao estado 0.
- `test_ai_headless`: PASS. Antes falhava em `aaf=0`; com a leitura correta da
  tabela a CPU volta a usar o antiáreo em jump-in (`aaf=2` no nível 9).
- 12 Ralf Kicks (fraco/forte, oponente no chão/guardando/pulando): nenhum
  travamento.
- 4 lutas CPU vs CPU de 8000 frames (Ralf vs Kyo/Iori, Kyo vs Ralf): nenhum
  stall de `framecnt`.
- `test_attract_demo_headless`: PASS, inclusive com Ralf sorteado na demo
  (primeiro par Leona/Ralf) e no caso sem `.msu`.
- `test_team_swap_headless` (6), `test_team_vs_start_headless`,
  `test_team_banner_headless` (4), `test_team_swap_palette_headless`,
  `test_single_campaign_headless`, `test_midfight_join_headless`,
  `test_benimaru_antiair_headless`, `test_msu_chr_visibility_headless`
  (960 páginas) e `test_super_stage_vram_headless`: PASS.
- `pytest -q tools/tests`: 269 passed (4260 subtests). Inclui o novo
  `test_ai_tables.py` (sids das tabelas de IA sempre dentro da faixa e
  cálculo de offset em 16 bits) e o teste de clamp de página, agora
  independente do índice exato do sprite.

## Build

`build/teamfix_benimaru_20261103/`

- checksum **`$C316`**
- layout MSU **`0x3061`**
- `.sfc` SHA-256 `bb2105b4…bfe99`
- `.msu` SHA-256 `4ab3f94c…2c8fe` (novo; copie os dois juntos)
