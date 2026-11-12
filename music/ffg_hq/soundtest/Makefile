PVSNESLIB_HOME ?= /run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6
export PVSNESLIB_HOME

# modules prepared by ../tools/make_soundtest.py (n* = NOVA, a* = ATUAL)
AUDIOFILES := $(sort $(wildcard it/n*.it)) $(sort $(wildcard it/a*.it))
export SOUNDBANK := res/soundbank

export ROMNAME := soundtest
ROMTITLE := KOF98FFGSOUNDTEST
# size written by ../tools/make_soundtest.py
-include romsize.mk

include $(PVSNESLIB_HOME)/devkitsnes/snes_rules

.PHONY: bitmaps all

SMCONVFLAGS := -s -o $(SOUNDBANK) -V -b 5
musics: $(SOUNDBANK).obj

all: musics bitmaps $(ROMNAME).sfc

clean: cleanBuildRes cleanRom cleanGfx cleanAudio

pvsneslibfont.pic: pvsneslibfont.bmp
	$(GFXCONV) -s 8 -o 2 -u 16 -p -e 1 -t bmp -i $<

bitmaps: pvsneslibfont.pic
