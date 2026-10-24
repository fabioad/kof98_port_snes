#!/bin/bash
# Roda KOF '98 (Neo Geo / MAME)
cd "$(dirname "$0")"

# MAME precisa enxergar as roms da pasta atual
/usr/games/mame -rompath "$PWD" -window -nomaximize kof98

# Alternativa fullscreen:
# /usr/games/mame -rompath "$PWD" -fullscreen kof98

# Alternativa via RetroArch (finalburn neo core):
# retroarch -L /usr/lib/libretro/fbneo_libretro.so "$PWD/kof98.zip"
