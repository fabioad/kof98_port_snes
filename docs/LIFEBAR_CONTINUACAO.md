# Continuação da lifebar do KOF98

## Pedido

Implementar a lifebar do KOF98 a partir dos arquivos de `assets/kof98data/Lifebar`. O pedido mencionou `ssf`, mas os arquivos de sprites nessa pasta usam a extensão `.sff`. As ações AIR estão embutidas em `fight.def` como seções `[Begin Action N]`; não há um `.air` separado nessa pasta.

## Estado em 18/10/2026

A lifebar já foi integrada ao gerador e à rotina de luta, e a ROM compila e passa pela verificação. Uma captura em emulador mostrou moldura superior, barras verdes de vida, nomes, texto `WIN`, rótulos e barras de `POW` na parte inferior. **O relógio no centro da moldura superior ainda está ausente ou instável.** Não considerar a implementação concluída antes de corrigir e conferir esse ponto no emulador.

### Arquivos alterados nesta tarefa

- `tools/build_fight.py`: leitura de `fight.def`, das ações AIR embutidas, de SFF e FNT; extração seletiva dos sprites grandes; geração dos tiles, paletas, mapas e constantes do HUD. A barra agora tem 88 pixels, com variantes de preenchimento e moldura vazia. O HUD gerado usa 365 tiles 2bpp dos 512 disponíveis na área de BG3.
- `src/engine/fight.asm`: logo de `ROUND` na transição; mapas superior e inferior do HUD; nomes, barras de vida e poder, contadores, marcas de vitória, combo e relógio durante a luta.
- `Makefile` e `Makefile.pvsnes`: dependências dos arquivos `.def`, `.sff` e `.fnt` da pasta Lifebar. Os espaços em `Life Names.fnt` e `Life Names Simul.fnt` precisam permanecer escapados nas dependências.

O gerador escreve `build/gen_fight/hud.chr`, `hud.inc` e `hud_pal.bin`. Ele também reconstrói outros arquivos gerados do combate. Há várias modificações preexistentes e arquivos não rastreados no repositório; não usar `git reset` ou descarte geral para limpar esta tarefa. O `linkfile` foi restaurado depois do build porque o PVSnesLib reescreve seus caminhos.

## Verificação executada

Estes comandos passaram:

```sh
python3 tools/build_fight.py
tools/bin/wla-65816 -o /tmp/kof98-hud.o -I build -I src src/engine/fight.asm
python3 -m py_compile tools/build_fight.py
git diff --check
make -f Makefile.pvsnes verify PVSNESLIB_HOME=/run/media/fabio/Dados/.Trash-1000/files/sneskit/pvsneslib
```

`verify` produziu `kof98-snes.sfc` (8 MiB) com checksum válido e `kof98-snes.msu`. O caminho do SDK acima foi o encontrado nesta máquina; conferir sua existência ao retomar. Rodar o build novamente altera `linkfile` com os caminhos locais do SDK, então conferir e restaurar apenas esse arquivo se a alteração for incidental.

Uma captura de execução ficou em `/tmp/lb_actual.png`. O script temporário `/tmp/capture_kof98_lifebar.py` abre RetroArch, navega até a luta, salva a captura e imprime estado da RAM. Arquivos em `/tmp` podem desaparecer entre sessões. O script usa `tools/test_fight_remote.py` e `tools/snap_frame.py`; se ainda existir, execute `python3 /tmp/capture_kof98_lifebar.py`. Na captura, a luta chegou a `gamestate=1`, com vida `200/200`.

## Relógio: diagnóstico e correção (resolvido)

`DrawTimer` em `src/engine/fight.asm` desenha os dígitos nas colunas 15 e 16 da linha 2 do `HUDMAP` (`$479E`/`$47A0`). O código de máquina da rotina estava correto (`adc #$61` = `BIGD0`, `sta $4700,x`); as células mostravam lixo porque **outra rotina as sobrescrevia**: `WriteBlock`.

### Causa raiz

Em `WriteBlock` (desenha os logos `ROUND`/`K.O.`/`FIGHT!` na linha 9, cols 12–19):

```asm
lda [scr2]      ; word: w no byte baixo, h no byte alto
sta scr4        ; grava w->$18 (scr4) e h->$19
...
dec scr5        ; MAS scr5 = $1A, nao $19!
bne WB_row
```

`scr4=$18` e `scr5=$1A` são defines separados. O `sta scr4` de 16 bits coloca `h` no byte `$19` — que **não é** `scr5`. O `dec scr5`/`bne` decrementava lixo em `$1A`, então cada chamada desenhava `[$1A]+1` linhas em vez de `h`: uma faixa vertical de 8 colunas com `ATT_YEL` ($34) que pisava nas células do timer (e em WRAM além do `HUDMAP` quando `scr0` avançava). Os valores `0034/3E34/5534/FC34` observados eram o stream de tiles do ponteiro `scr2` sendo varrido além do fim do bloco.

A amostragem da pilha durante a paralisação mostrava `IntroTick -> WriteBlock` e os regs `scr0=$6F18, scr2=$9BDC, scr5=$4D` — 77 linhas em vez de 2.

### Correção em `src/engine/fight.asm`

Depois do `sta scr4`, copiar `scr4+1` (o byte `h`) para `scr5`, e limitar `w`/`h` a ≤31 com `and #$1F` + `beq WB_bail`, para que um ponteiro `scr2` inválido não produza escritas desenfreadas. `WB_bail` cai no `rep #$20`/`rts` final.

### Verificação

- `python3 tools/build_fight.py`, `wla-65816` e `make -f Makefile.pvsnes verify PVSNESLIB_HOME=/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6` — todos OK; `linkfile` restaurado após o build.
- Probe de RAM (RetroArch/Snes9x): sem stall na entrada da luta; `row2` mostra `ac30 ad30 | 272d | 7334 7334 | 2839 | ad70 ac70` — lifebars, ornamentos do `HudTopMap` e dígitos do timer (`99`→`98`→`97`…) corretos e estáveis.
- Capturas `/tmp/kof_fight_70.png` e `/tmp/kof_fight_later.png`: **"97"** e **"90"** visíveis em dourado no centro da moldura superior, decrementando 1/s em tempo real; lifebars verdes, `WIN`, `POW` — sem faixa de corrupção nem bloco preto/ciano.

Mesen headless (`--testRunner`) segue sem validação: o binário local segfaulta (exit 139). A correção foi validada em Snes9x (tanto via RetroArch quanto via libretro em-processo); conferir no Mesen GUI se necessário.

### Observação sobre o limite de tiles do HUD

`tools/build_fight.py` já rejeita `hud.chr` > 384 tiles 2bpp (`$2000-$2BFF`, antes de `STGACHR=$2C00`). HUD atual: 365 tiles.
