; ExHiROM boot trampolines.  CPU interrupt/reset vectors are fetched from
; $00:FFxx, which under ExHiROM maps to file bank 64 (the upper 4 MiB
; half).  All real code lives in the first half at $C0+, so these stubs
; sit in bank 64 (CPU $00:8000+ window) and JML to the actual handlers.

.MEMORYMAP
  SLOTSIZE $10000
  DEFAULTSLOT 0
  SLOT 0 $0000
  SLOT 1 $0 $2000
  SLOT 2 $2000 $E000
  SLOT 3 $0 $10000
  SLOT 4 $6000
.ENDME

.ROMBANKSIZE $10000
.ROMBANKS 128
.EXHIROM
.FASTROM
.BASE $C0

.BANK 64 SLOT 0
.ORGA $8000
.SECTION "Boot64" FORCE

StubReset:  jml tcc__start                    ; RESET
StubNMI:    jml VBlank                        ; NMI
StubEmpty:  rti                               ; COP/BRK/IRQ/ABORT

.ENDS
