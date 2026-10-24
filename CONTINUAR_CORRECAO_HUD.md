# Continuação: artefato preto e cores das barras — CONCLUÍDO

Data: 2026-10-18. Captura original: `/home/fabio/Imagens/Screenshots/Screenshot from 2026-10-18 06-50-07.png`.

## Pedido e pista do usuário

Na luta do KOF98 SNES aparece um bloco preto/ciano cobrindo o centro da tela. As barras de energia também mudam de cor conforme o cenário. O usuário informou que o bloco apareceu depois da implementação de fontes novas.

## Alterações feitas

- `tools/build_stages.py`: mapas e tiles animados de BG1 agora usam a paleta 2 (`STAGE_BG_PALETTE = 2`). Isso reserva CGRAM 0–31 para as paletas de 2 bpp do HUD de BG3.
- `src/engine/fight.asm`: `PpuInit` limpa CGRAM a partir do índice 32 e `StagePick` carrega as 3 paletas do cenário a partir do índice 32. Antes, o cenário era carregado em CGRAM 0–47 e sobrescrevia as cores do HUD (índices 12–31). Essa é a causa identificada das cores variáveis nas barras.
- `tools/build_fight.py`: `hud.chr` agora falha o build acima de **384 tiles** (era 512). BG3CHR=$2000 e STGACHR=$2C00 em words VRAM → só $C00 words = 6144 B = 384 tiles de 2 bpp cabem; acima disso o HUD invadiria os tiles animados do cenário. hud.chr atual: 365 tiles (19 de folga).

## Verificação (concluída)

- `python3 tools/build_fight.py` + `make -f Makefile.pvsnes verify PVSNESLIB_HOME=/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6`: build e verify OK (msu copiado). `MIDI2TRACKER=/home/fabio/Applications/MIDIToTracker/.venv/bin/midi2tracker` exportado por precaução.
- Snes9x via libretro (sessão anterior): ROM com `.msu` ao lado, 400+ frames no estágio 7 — sem bloco, barras verdes.
- **Mesen 2.1.1 (testRunner, sem .msu): CONFIRMADO.** Probe `/tmp/kof_mesen_probe.lua` dirigiu menus até a luta em `stage=7` (KYO vs IORI). Frame 60 limpo: `/tmp/kof_mesen_fight.png` — sem bloco preto/ciano, barras verdes. Dumps: `kof_mesen_vram.bin` (mapa BG3 32×32 $5000: rows 0–6 HUD, **rows 7–21 vazios**, 22+ POW), `kof_mesen_cgram.bin` (verde do lifebar no idx 18 `40,160,48`; paletas do cenário a partir do idx 32), `kof_mesen_oam.bin` (só 36 sprites dos lutadores, sem sprite fantasma).
- Cenário+MSU na GUI: não testável por script (ver bug abaixo). Irrelevante para o HUD: MSU só alimenta tiles de chars externos via `$2001`; Kyo/Iori estão na ROM e BG3/CGRAM não tocam MSU.

## Bug do Mesen 2.1.1 encontrado (segfault testRunner/Lua + MSU-1)

`mesen rom.sfc --testRunner script.lua` **segfaulta (139) quando `kof98-snes.msu` existe ao lado da ROM**, mesmo com script vazio/inexistente. Sem o `.msu`, funciona. Na GUI, o jogo roda normal — o crash só ocorre quando um contexto de script/debug é criado com MSU presente.

Cadeia do crash (gdb): managed → `Debugger::GetAbsoluteAddress(AddressInfo)` → `MemoryMappings::GetAbsoluteAddress(0x1008)` → `GetHandler()` retorna `0x0606060606060606` (objeto envenenado/não inicializado) → deref em `mov (rax),rdx`. O mapping object para o memType consultado existe mas sua tabela de handlers nunca foi populada — provavelmente o domínio MSU-1 não registra handlers no caminho testRunner/script.

Workarounds: (a) rodar testRunner num diretório sem o `.msu`; (b) o segundo controle SNES se configura com `emu.setInput(input, 0, 1)` — o `subPort` é o índice do controle, o `port` colapsa no hub (testado: ports 1–5 todos caem em JOY1).

Notas de input do select (versus, item menu 1 → `G_MODE=0`): `lock1/2`=$8E/$8F (WRAM+$1000), `cpu2`=$91 (em versus P2 é humano, sem auto-lock), stage fixo via `rng`=$88=14 + `framecnt`=$24=111 → stage 7. Em single/team (`G_MODE!=0`) o pad 2 é ignorado.

**Atenção:** o projeto já tinha muitas modificações não commitadas antes desta sessão. Não usar `git reset`/`git restore` indiscriminadamente. Sem commit.
