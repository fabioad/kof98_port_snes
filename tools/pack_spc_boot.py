#!/usr/bin/env python3
"""Cut the linked SPC image down to the bytes that belong at ARAM $0200.

wlalink -b emits from the first used address, so file offset 0 is already
ARAM $0200 (the driver). Do not skip 0x200 or the CPU uploads garbage.
"""
from pathlib import Path
import sys

raw_path = Path(sys.argv[1] if len(sys.argv) > 1 else "build/spc_raw.bin")
out_bin = Path(sys.argv[2] if len(sys.argv) > 2 else "build/gen/spc_boot.bin")
out_inc = Path(sys.argv[3] if len(sys.argv) > 3 else "build/gen/spc_size.inc")
# --pad=N is retained for callers that intentionally reserve bytes before the
# linked image.  The normal IPL upload stores its first byte at the requested
# destination, so images assembled for $0200 must not be padded.
pad = 0
for arg in sys.argv[4:]:
    if arg.startswith("--pad"):
        pad = int(arg[6:] or "1") if arg.startswith("--pad=") else 1
data = raw_path.read_bytes()
if len(data) < 16:
    raise SystemExit(f"spc image too small: {len(data)}")
end = len(data)
while end > 16 and data[end - 1] in (0x00,):
    end -= 1
blob = (b"\x00" * pad) + data[:end]
driver = blob[pad:]
# Driver starts CLRP / MOV X,#$EF (or MOV X,#$EF if CLRP is omitted).
if driver[:3] != bytes((0x20, 0xCD, 0xEF)) and driver[:2] != bytes((0xCD, 0xEF)):
    raise SystemExit(f"spc_boot does not start with driver (got {driver[:8].hex()})")
# The fight ROM keeps this blob in 32 KiB banks; split at the bank edge.
out_bin2 = out_bin.with_name(out_bin.stem + "2.bin")
part1, part2 = blob[:32768], blob[32768:]
out_bin.write_bytes(part1)
out_bin2.write_bytes(part2 if part2 else b"\0")
out_inc.write_text(
    f".DEFINE SPC_BOOT_SIZE {len(blob)}\n"
    f".DEFINE SPC_BOOT_SPLIT {len(part1)}\n")
print(f"spc_boot {len(blob)} bytes (ARAM $0200-${0x200+end:04X}, "
      f"split at {len(part1)})")
if len(part1) > 32768 or len(part2) > 32768:
    raise SystemExit("spc_boot exceeds two 32 KiB banks")
