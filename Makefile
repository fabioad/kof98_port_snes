# SNES boot ROM: solid-color backdrop + mario.mid through the SPC700 driver.
#   make            # boot-blue.sfc
#   make COLOR=red  # boot-red.sfc
#   make COLOR=black
#   make colors     # all three

WLA     ?= $(firstword $(wildcard tools/bin/wla-65816) $(shell command -v wla-65816 2>/dev/null))
WLALINK ?= $(firstword $(wildcard tools/bin/wlalink) $(shell command -v wlalink 2>/dev/null))
WLA_SPC ?= $(firstword $(wildcard tools/bin/wla-spc700) $(shell command -v wla-spc700 2>/dev/null))

COLOR   ?= blue
ROM     := build/boot-$(COLOR).sfc
OBJ     := build/boot-$(COLOR).o
FOBJ    := build/fight.o
LINK    := build/link-$(COLOR)

FIGHT_GEN := build/gen_fight/iori.chr build/gen_fight/iori_pal.bin \
	build/gen_fight/runtime_abi.inc \
	build/gen_fight/iori_spr.inc build/gen_fight/kyo.chr \
	build/gen_fight/kyo_pal.bin build/gen_fight/kyo_spr.inc \
	build/gen_fight/hud.inc \
	build/gen_fight/portraits.chr build/gen_fight/portraits.inc \
	build/gen_fight/portrait_pal.bin \
	build/gen_fight/stage.chr build/gen_fight/stage.map \
	build/gen_fight/stage_pal.bin build/gen_fight/hud.chr \
	build/gen_fight/hud_pal.bin build/gen_fight/spark.chr \
	build/gen_fight/spark_pal.bin build/gen_fight/spark.inc \
	build/gen_fight/stages.inc build/gen_fight/stages_tab.inc \
	build/gen_fight/survival_msu.inc build/gen_fight/survival_msu_defs.inc \
	build/gen_fight/quote_strings_en.inc build/gen_fight/quote_strings_pt.inc \
	build/gen_fight/quote_strings_es.inc build/gen_fight/quote_strings_fr.inc \
	build/gen_fight/quote_tables.inc build/gen_fight/char_names.inc

MIDI    ?= assets/music/mario.mid
TIMBRE_BANK ?= assets/music/spc_brr_melhora_timbres.bin
NG_BANK ?= work/neogeo/ngbank/ngbank.json

TIMBRE_ARG := $(if $(wildcard $(TIMBRE_BANK)),--timbre-bank $(TIMBRE_BANK))
NG_ARG := $(if $(wildcard $(NG_BANK)),--neogeo-bank $(NG_BANK))

SPC_GEN := build/gen_neogeo/spc_brr.bin build/gen_neogeo/spc_dir.bin \
	build/gen_neogeo/spc_pitch.bin build/gen_neogeo/spc_perc.inc \
	build/gen_neogeo/spc_sfxframes.inc build/gen_neogeo/song_mario.bin \
	build/gen_neogeo/spc_songmeta.inc

ifeq ($(COLOR),black)
	COLOR_FLAG := -D BACKDROP_LO=0 -D BACKDROP_HI=0
else ifeq ($(COLOR),blue)
	COLOR_FLAG := -D BACKDROP_LO=0 -D BACKDROP_HI=124
else ifeq ($(COLOR),red)
	COLOR_FLAG := -D BACKDROP_LO=31 -D BACKDROP_HI=0
else
	$(error COLOR must be black, blue, or red)
endif

.PHONY: all colors clean verify pvsnes pvsnes-verify pvsnes-clean

all: $(ROM)

$(SPC_GEN): tools/build_mario_spc.py tools/build_spc_neogeo.py $(MIDI) $(wildcard $(TIMBRE_BANK)) $(wildcard $(NG_BANK))
	python3 tools/build_mario_spc.py --midi $(MIDI) --out build/gen_neogeo $(TIMBRE_ARG) $(NG_ARG)

build/spc.o: src/audio/neogeo_spc.asm $(SPC_GEN)
	@mkdir -p build
	$(WLA_SPC) -o $@ -I build src/audio/neogeo_spc.asm

build/gen/spc_boot.bin build/gen/spc_size.inc: build/spc.o tools/pack_spc_boot.py
	@mkdir -p build/gen
	@printf '[objects]\n%s\n' build/spc.o > build/link-spc
	$(WLALINK) -b build/link-spc build/spc_raw.bin
	python3 tools/pack_spc_boot.py build/spc_raw.bin build/gen/spc_boot.bin build/gen/spc_size.inc

$(OBJ): src/boot/boot.asm build/gen/spc_boot.bin build/gen/spc_size.inc build/gen_neogeo/song_mario.bin build/gen_neogeo/spc_songmeta.inc
	@mkdir -p build
	$(WLA) -o $@ -I build $(COLOR_FLAG) src/boot/boot.asm

$(FIGHT_GEN): $(wildcard tools/calibration/*.py assets/calibration/*.json assets/characters/*/*_SNES.cns assets/characters/*/*_SNES.cmd assets/characters/*/*.air assets/data/quotes/*.json)

$(FIGHT_GEN): tools/build_fight.py tools/runtime_abi.py assets/runtime_abi.json tools/build_stages.py tools/sff.py tools/build_endings.py $(wildcard assets/survival_ending/*.png) assets/characters/Iori-KOF98/Iori.sff assets/characters/Iori-KOF98/Iori.air assets/characters/Iori-KOF98/Iori_SNES.cns assets/characters/Iori-KOF98/Iori_SNES.cmd assets/characters/Kyo-KOF98/Kyo.sff assets/characters/Kyo-KOF98/Kyo.air assets/characters/Kyo-KOF98/Kyo_SNES.cns assets/characters/Kyo-KOF98/Kyo_SNES.cmd assets/stages/stage0.sff assets/stages/stage0.def assets/data/fightfx.sff assets/data/fightfx.air assets/kof98data/Lifebar/fight.def assets/kof98data/Lifebar/fight.sff assets/kof98data/Lifebar/Lifebar_Font/Life\ Names.fnt assets/kof98data/Lifebar/Lifebar_Font/Life\ Names\ Simul.fnt $(wildcard assets/kof98data/Lifebar/Lifebar_Font/*.def assets/kof98data/Lifebar/Lifebar_Font/*.sff assets/stages/*.def assets/stages/*.sff)
	python3 tools/build_fight.py

$(FOBJ): src/engine/fight.asm $(FIGHT_GEN)
	@mkdir -p build
	$(WLA) -o $@ -I build -I src src/engine/fight.asm

$(LINK): $(OBJ) $(FOBJ)
	@mkdir -p build
	@printf '[objects]\n%s\n%s\n' $(OBJ) $(FOBJ) > $@

$(ROM): $(LINK)
	$(WLALINK) -S $(LINK) $@

colors:
	$(MAKE) COLOR=black
	$(MAKE) COLOR=red
	$(MAKE) COLOR=blue

verify: $(ROM)
	python3 tools/verify_boot_rom.py $(ROM)

clean:
	rm -f build/*.o build/*.sfc build/*.sym build/spc_raw.bin build/link-*

pvsnes:
	$(MAKE) -f Makefile.pvsnes

pvsnes-verify:
	$(MAKE) -f Makefile.pvsnes verify

pvsnes-clean:
	$(MAKE) -f Makefile.pvsnes clean
