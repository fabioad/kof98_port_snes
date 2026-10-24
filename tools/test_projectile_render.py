#!/usr/bin/env python3
"""Check the live spark/projectile OAM cells against their ROM frame records.

Runs the ROM's actual 65816 loader/renderer in Snes9x with a small test boot
in a temporary ROM copy. This bypasses menus, input and SPC handshakes, while
keeping DrawSparks, FxPrepareBoth and all effect assets unchanged. Tests both
owner bits, both animation frames, ordinary sparks and real VRAM contents.
Also checks Power Wave contact, damage, sound selection and impact spark survival.
"""
import struct
import tempfile
import time
from pathlib import Path

import test_fight_remote as t


def symbols():
    result = {}
    for line in (t.ROOT / "kof98-snes.symfull").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and len(fields[0]) == 8:
            try:
                result[fields[1]] = int(fields[0], 16)
            except ValueError:
                pass
    return result


def rom_offset(addr):
    """Convert a WLA symbol address to an ExHiROM file offset.

    Banks $C0-$FF live in the lower 4 MiB of the file, while the upper
    window mirrors $40-$7D at the same numeric offset.  The projectile
    section can land in either window depending on bank pressure.
    """
    return addr - 0xC00000 if addr >= 0xC00000 else addr


def write_ram(ra, address, data):
    for _ in range(8):
        ra.command_no_reply(f"WRITE_CORE_RAM {address:X} " + data.hex(" "))
        if ra.read_ram(address, len(data)) == data:
            return
    raise AssertionError(f"write/readback failed at {address:04X}")


def harness_rom(outdir, syms, original):
    """Only replace reset/BuildOam in a test copy; call the real routines."""
    code = bytearray.fromhex(
        "78 18 FB C2 30 "          # SEI; native mode; A/X/Y 16 bit
        "A9 FF 1F 1B "            # stack $1FFF
        "A9 00 10 5B "            # direct page $1000
        "E2 20 A9 7E 48 AB "      # DBR $7E
        "A9 80 8F 00 21 00 "      # forced blank for VRAM writes
        "A9 03 8F 01 21 00 "      # OBJ sizes 8x8 / 16x16
        "C2 30 9C F0 43 9C F2 43 " # clear request/done words
        "A9 5A A5 8D F4 43 "       # ready word $A55A
    )
    loop = len(code)
    code += bytes.fromhex("AD F0 43 F0 FB C9 02 00 D0 03 20")
    code += struct.pack("<H", syms["ProjSpawn"] & 0xFFFF)
    code += bytes.fromhex("C2 30 AD F0 43 C9 03 00 D0 03 20")
    code += struct.pack("<H", syms["TickSpark"] & 0xFFFF)
    code += bytes.fromhex("C2 30 9C F0 43 64 2A")
    for label in ("FxPrepareBoth", "DrawSparks"):
        assert syms[label] >> 16 == syms["BuildOam"] >> 16
        code += b"\x20" + struct.pack("<H", syms[label] & 0xFFFF)
        if label == "FxPrepareBoth":
            # Read both real PPU effect pages back into WRAM through $2139/A.
            # Each 2 KiB page holds sixteen unique 16x16 cells.
            code += bytes.fromhex("C2 30")
            for vram, dest in ((0x6C00, 0x5000), (0x7C00, 0x5800)):
                code += b"\xA9" + struct.pack("<H", vram)
                # PPU reads are buffered: discard the first word after seek.
                code += bytes.fromhex("8F 16 21 00 AF 39 21 00 A2 00 00")
                read_loop = len(code)
                code += bytes.fromhex("AF 39 21 00 9D") + struct.pack("<H", dest)
                code += bytes.fromhex("E8 E8 E0 00 08")
                code += bytes((0xD0, (read_loop - len(code) - 2) & 255))
    code += bytes.fromhex("C2 30 A9 01 00 8D F2 43")
    code += b"\x4c" + struct.pack("<H", (syms["BuildOam"] + loop) & 0xFFFF)
    rom = bytearray(original)
    target = syms["BuildOam"]
    offset = rom_offset(target)
    rom[offset:offset + len(code)] = code
    # ExHiROM bank 00:$8000 maps to the upper 4 MiB reset trampoline.
    rom[0x408000:0x408004] = bytes((0x5C, target & 255,
                                   (target >> 8) & 255, (target >> 16) & 255))
    for header in (0xFFDC, 0x40FFDC):
        rom[header:header + 4] = b"\xff\xff\0\0"
    checksum = sum(rom) & 0xFFFF
    for header in (0xFFDC, 0x40FFDC):
        struct.pack_into("<HH", rom, header, checksum ^ 0xFFFF, checksum)
    path = outdir / "projectile-render.sfc"
    path.write_bytes(rom)
    return path


def verify_vram(ra, syms, rom, label, side, frame, projectile):
    name = label.removesuffix("ProjFxAnim")
    if projectile:
        offset = rom_offset(syms[name + "ProjFxChr"]) + frame * 2048
    else:
        offset = rom_offset(syms["SparkChr"])
    dest = 0x5000 + side * 2048
    actual = b"".join(ra.read_ram(dest + i, 128) for i in range(0, 2048, 128))
    assert actual == rom[offset:offset + 2048], (label, side, frame, "VRAM mismatch")


def run(ra):
    syms = symbols()
    rom = t.ROM.read_bytes()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            if ra.read_ram(0x43F4, 2) == b"\x5a\xa5":
                break
        except RuntimeError:
            pass
        time.sleep(0.1)
    else:
        raise AssertionError("test ROM did not reach renderer harness")
    write_ram(ra, 0x1000, bytes(0xE9))
    write_ram(ra, 0x4000, bytes(128))
    write_ram(ra, 0x4230, bytes(4))
    write_ram(ra, 0x102E, bytes(((syms["CharTerry"] >> 16) & 255,)))
    for base, name in ((0x4000, "CharTerry"), (0x4040, "CharYuri")):
        write_ram(ra, base + 44, struct.pack("<H", syms[name] & 0xFFFF))

    cases = []
    for name in ("terry", "yuri", "kyo", "iori"):
        anim = rom_offset(syms[name + "ProjFxAnim"])
        nframes = rom[anim]
        cases += [(name + "ProjFxAnim", side, frame, True)
                  for side in (0, 1) for frame in range(nframes)]
    cases += [("SparkHit", side, 0, False) for side in (0, 1)]
    for label, side, frame, projectile in cases:
        addr = syms[label]
        # WLA's SNES symbols use bank C0+file_bank, including ExHiROM banks.
        offset = rom_offset(addr)
        ptr = struct.unpack_from("<H", rom, offset + 1 + frame * 2)[0]
        record = (offset & ~0xFFFF) | ptr
        count = rom[record + 1]
        expected = []
        for i in range(count):
            dx, dy, tile = struct.unpack_from("<bbH", rom, record + (5 if projectile else 2) + i * 4)
            if side:
                tile |= 0x100
            attr = 0x34 | (tile >> 8)
            expected.append(bytes(((120 + dx) & 255, (100 + dy) & 255,
                                   tile & 255, attr)))
        effect = bytearray(36)
        struct.pack_into("<HHHBBhhhBBBB", effect, side * 18,
                         120, 100, addr & 0xFFFF, frame, 200,
                         0, 0, 0, 200,
                         (0x80 | side * 0x40) if projectile else 0x34,
                         (addr >> 16) & 255, 0)
        write_ram(ra, 0x4200, effect)
        write_ram(ra, 0x1A00, bytes(32))
        write_ram(ra, 0x43F2, b"\0\0")
        write_ram(ra, 0x43F0, b"\1\0")
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            ra.command_no_reply("FRAMEADVANCE")
            time.sleep(0.25)
            if ra.read_ram(0x43F2, 2) == b"\1\0":
                break
        else:
            raise AssertionError("renderer harness did not finish")
        oam = ra.read_ram(0x1800, count * 4)
        actual = [oam[i:i + 4] for i in range(0, len(oam), 4)]
        assert actual == expected, (label, side, frame,
                                    [v.hex() for v in expected],
                                    [v.hex() for v in actual])
        hi = ra.read_ram(0x1A00, (count + 3) // 4)
        assert all((hi[i // 4] >> ((i % 4) * 2)) & 2
                   for i in range(count)), "effect cells must be 16x16"
        verify_vram(ra, syms, rom, label, side, frame, projectile)
        print(f"OK {label} P{side + 1} frame {frame}: "
              f"{count} cells, tiles {[v[2] | ((v[3] & 1) << 8) for v in actual]}",
              flush=True)
    for name in ("Terry", "Kyo", "Iori", "Yuri"):
        write_ram(ra, 0x4200, bytes(36))
        write_ram(ra, 0x402C, struct.pack("<H", syms["Char" + name] & 0xFFFF))
        write_ram(ra, 0x4000, struct.pack("<HH", 80 << 8, 0))
        write_ram(ra, 0x400E, b"\1\0")
        write_ram(ra, 0x1010, struct.pack("<HH", 0x0300, 14))
        write_ram(ra, 0x101C, b"\0\0")
        write_ram(ra, 0x43F2, b"\0\0")
        write_ram(ra, 0x43F0, b"\2\0")
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            ra.command_no_reply("FRAMEADVANCE")
            time.sleep(0.25)
            if ra.read_ram(0x43F2, 2) == b"\1\0":
                break
        else:
            raise AssertionError("spawn harness did not finish")
        x, y = struct.unpack("<HH", ra.read_ram(0x4200, 4))
        assert (x, y) == (94, 150 if name == "Yuri" else 190), (name, x, y)
        print(f"OK {name} projectile spawn: x={x}, y={y}", flush=True)
    # Reproduce first-contact hits, misses, and stale renderer scratch flags.
    for side, distance, hit in ((0, 42, True), (1, 42, True),
                                (0, 44, False), (1, 44, False),
                                (0, 256, False)):
        victim = 0x4040 if side == 0 else 0x4000
        target_x = 160 if side == 0 else 80
        origin_x = target_x - distance if side == 0 else target_x + distance
        for base in (0x4000, 0x4040):
            fighter = bytearray(64)
            struct.pack_into("<H", fighter, 0, target_x << 8)
            struct.pack_into("<H", fighter, 14, 1)
            struct.pack_into("<H", fighter, 16, 144)
            struct.pack_into("<H", fighter, 44, syms["CharIori"] & 65535)
            fighter[46] = (syms["ioriSprOfs"] >> 16) & 255
            write_ram(ra, base, fighter)
        effect = bytearray(36)
        addr = syms["terryProjFxAnim"]
        struct.pack_into("<hhHBBhhhBBBB", effect, side * 18,
                         origin_x, 190, addr & 65535, 0, 20,
                         0x0300 if side == 0 else -0x0300, 0, 0x050E,
                         90, 0x80 | side * 0x40, (addr >> 16) & 255, 0)
        write_ram(ra, 0x4200, effect)
        write_ram(ra, 0x1032, b"\0")  # no SPC handshake in this harness
        write_ram(ra, 0x1031, b"\xff")
        write_ram(ra, 0x1035, b"\x80")  # stale scr6 high byte from renderer
        write_ram(ra, 0x43F2, bytes(2))
        write_ram(ra, 0x43F0, b"\3\0")
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            ra.command_no_reply("FRAMEADVANCE")
            time.sleep(0.25)
            if ra.read_ram(0x43F2, 2) == b"\1\0":
                break
        else:
            raise AssertionError(("contact harness did not finish", "DP", ra.read_ram(0x1000, 80).hex(), "fighters", ra.read_ram(0x4000,128).hex(), "stack", ra.read_ram(0x1fc0,64).hex()))
        hp = struct.unpack("<H", ra.read_ram(victim + 16, 2))[0]
        assert hp == (130 if hit else 144), (side, distance, hp)
        slots = ra.read_ram(0x4200, 36)
        if hit:
            sparks = [struct.unpack_from("<H", slots, i + 4)[0]
                      for i in (0, 18) if slots[i + 15] == 0x34]
            assert syms["SparkHit"] & 65535 in sparks, "impact spark was erased"
            assert ra.read_ram(0x1031, 1) == b"\5", "wrong impact sound"
        print(f"OK Power Wave P{side + 1} distance={distance}: HP={hp}, hit={hit}", flush=True)
    print(f"PASS: {len(cases)} rendering cases + VRAM + ground spawns + 5 contact cases", flush=True)


def main():
    outdir = Path(tempfile.mkdtemp(prefix="projectile_render_", dir=t.ROOT / "build"))
    original_rom = t.ROM
    t.ROM = harness_rom(outdir, symbols(), original_rom.read_bytes())
    ra = t.RetroArch()
    try:
        ra.launch("retroarch", t.CORE)
        run(ra)
    finally:
        ra.close()


if __name__ == "__main__":
    main()
