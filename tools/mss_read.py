#!/usr/bin/env python3
"""Read Mesen2 .mss state fields without launching the emulator."""
import struct
import sys
import zlib


def load(path):
    data = open(path, "rb").read()
    assert data[:3] == b"MSS", "not Mesen .mss"
    emu = struct.unpack_from("<I", data, 3)[0]
    fmt = struct.unpack_from("<I", data, 7)[0]
    console = struct.unpack_from("<I", data, 11)[0]
    fb_size, w, h, scale, comp = struct.unpack_from("<IIIII", data, 15)
    off = 35 + comp
    nlen = struct.unpack_from("<I", data, off)[0]
    off += 4
    rom = data[off:off + nlen].decode("utf-8", "replace")
    off += nlen
    is_comp = data[off]
    off += 1
    dec_size, comp_size = struct.unpack_from("<II", data, off)
    off += 8
    state = zlib.decompress(data[off:off + comp_size])
    assert len(state) == dec_size
    entries = {}
    i = 0
    while i < len(state):
        end = state.index(0, i)
        key = state[i:end].decode("ascii")
        i = end + 1
        sz = struct.unpack_from("<I", state, i)[0]
        i += 4
        entries[key] = state[i:i + sz]
        i += sz
    return {"emu": emu, "fmt": fmt, "console": console, "rom": rom,
            "entries": entries}


def u16(e, k):
    b = e[k]
    return struct.unpack("<H", b)[0]


def u32(e, k):
    return struct.unpack("<I", e[k])[0]


def main():
    st = load(sys.argv[1])
    e = st["entries"]
    print(f"rom={st['rom']} fmt={st['fmt']} keys={len(e)}")
    for k in ("cpu.pc", "cpu.k", "cpu.sp", "cpu.d", "cpu.dbr", "cpu.ps",
              "cpu.a", "cpu.x", "cpu.y", "cpu.emulationMode",
              "memoryManager.workRam", "ppu.scanline",
              "internalRegisters.enableNmi", "internalRegisters.vCounter"):
        if k in e:
            v = e[k]
            if len(v) == 1:
                print(f"{k:28s} = {v[0]:02X}")
            elif len(v) == 2:
                print(f"{k:28s} = {u16(e,k):04X}")
            elif len(v) == 4:
                print(f"{k:28s} = {u32(e,k):08X}")
            else:
                print(f"{k:28s} = {len(v)} bytes")
    wram = e["memoryManager.workRam"]
    def rd(a):
        return wram[a] | (wram[a + 1] << 8)
    print(f"WRAM gs={wram[0x1020]:02X} framecnt={wram[0x1024]:02X} "
          f"huddirty={wram[0x1026]:02X} pause={wram[0x1073]:02X} "
          f"p1state={wram[0x4008]:02X} p1frame={wram[0x400A]:02X} "
          f"p2state={wram[0x4048]:02X} p2frame={wram[0x404A]:02X}")
    sp = u16(e, "cpu.sp")
    print("stack:", " ".join(f"{wram[(sp+1+i)&0x1fff]:02X}" for i in range(12)))
    print("keys:", " ".join(sorted(e)))


if __name__ == "__main__":
    main()
