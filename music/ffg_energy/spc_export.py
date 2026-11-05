"""Repair standalone SPC placement in PVSnesLib 4.6 smconv.
MakeSPC uses stale module_base=0x18ca, while driver and pointer tables use
MODULE_BASE=0x1a00. The larger compiled driver ends at 0x19aa, so the old
ZeroFill length is negative and the module starts immediately after it.
Relocate only the exported data block; leave driver, notes and samples intact.
"""
from pathlib import Path
import json

def repair(spc,it):
    file=Path(spc);d=bytearray(file.read_bytes());module=Path(it).read_bytes()
    assert len(d)==66048 and d[:33]==b'SNES-SPC700 Sound File Data v0.30'
    r=d[256:65792];signature=bytes([module[48],module[51],module[50]])
    choices=[];p=0x1800
    while True:
        p=r.find(signature,p)
        if p<0:break
        # First order entries follow the 32-byte module header.
        count=int.from_bytes(module[32:34],'little');orders=module[192:192+min(count,8)]
        if r[p+32:p+32+len(orders)]==orders:choices.append(p)
        p+=1
    assert len(choices)==1,(file,choices)
    start=choices[0];target=0x1a00
    if start!=target:
        assert start<target and start>=0x1900,(file,start)
        delta=target-start
        assert not any(r[65536-delta:]),'relocation would truncate data'
        d[256+target:65792]=r[start:65536-delta]
        d[256+start:256+target]=bytes(delta)
        file.write_bytes(d)
    return dict(fromAddress=hex(start),toAddress=hex(target),bytesShifted=target-start)
