#!/usr/bin/env python3
"""Fail the build if any IT module exceeds SNESMOD's ARAM budget."""
import re
import subprocess
import sys

MAX_MODULE_BYTES = 44500  # ARAM budget with the combat effects + stream buffer
# SNESMOD data starts at $1A00; spcAllocateSoundRegion(18) reserves the top
# 4608 bytes for streamed character voices, leaving 54016 bytes for module +
# effects.  Fight modules reload five effects (8685 B), so the runtime module
# ceiling is ~45331 B; smconv's reported total runs ~800 B below the SPC
# footprint, hence 44500 B here.  Stage 8's original 46553 B module crossed
# this line and froze the APU handshake while reloading its combat effects.


def main(tool, paths):
    if not paths:
        raise SystemExit("validate_snesmod: no modules supplied")
    failures = []
    for path in paths:
        result = subprocess.run([tool, "-V", path], capture_output=True,
                                text=True)
        report = result.stdout + result.stderr
        match = re.search(r"Total:\s*\[\s*(\d+) bytes\]", report)
        if result.returncode or "module is too big" in report.lower() or not match:
            failures.append(f"{path}: {report.strip()}")
            continue
        size = int(match.group(1))
        if size > MAX_MODULE_BYTES:
            failures.append(
                f"{path}: {size} bytes exceeds {MAX_MODULE_BYTES}-byte runtime budget"
            )
    if failures:
        raise SystemExit("SNESMOD module validation failed:\n" + "\n".join(failures))
    print(f"SNESMOD validation passed: {len(paths)} modules fit ARAM")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: validate_snesmod.py SMCONV MODULE.it [...]")
    main(sys.argv[1], sys.argv[2:])
