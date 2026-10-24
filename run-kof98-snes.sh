#!/bin/bash
# Runs the SNES port (NOT the Neo Geo original used by run-kof98.sh).
cd "$(dirname "$0")"

ROM="kof98-snes.sfc"
MSU="kof98-snes.msu"
CORE="/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"

if [ ! -f "$ROM" ]; then
  echo "ROM not found: $ROM (run 'make pvsnes' first)" >&2
  exit 1
fi
if [ ! -f "$MSU" ]; then
  echo "Warning: $MSU not found; streamed characters/audio will not load." >&2
fi

if command -v retroarch >/dev/null 2>&1; then
  exec retroarch -L "$CORE" "$ROM"
fi
if command -v snes9x-gtk >/dev/null 2>&1; then
  exec snes9x-gtk "$ROM"
fi
echo "Install RetroArch (snes9x core) or Snes9x to run $ROM." >&2
exit 1
