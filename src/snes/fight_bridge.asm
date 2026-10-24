.INCLUDE "hdr.asm"

.DEFINE PVSNESLIB 1

; Keep the engine's direct-page scratch away from 816-tcc's imaginary
; registers and PVSnesLib's own low-RAM allocations.
.RAMSECTION ".fight_dp" BANK 0 SLOT 1 ORGA $1000 FORCE
FightDirectPage dsb $E9
.ENDS

; The original engine used the bank-$00 WRAM mirror.  In the hybrid build the
; fighter state, OAM shadow and HUD tilemap live in an explicitly reserved
; area of bank $7E.
.RAMSECTION ".fight_ram" BANK $7E SLOT 2 ORGA $4000 FORCE
FightRam dsb $0F00
.ENDS

; intro/title/menu/select state + scratch (see engine/menucore.asm).
.RAMSECTION ".menu_vars" BANK $7E SLOT 2 ORGA $F000 FORCE
MenuVarsRam dsb $180
.ENDS

; SURVIVOR opponent order + carried HP live in the menu-vars window above.
; PRACTICE command-list state follows them in the same free page.
.RAMSECTION ".fight_cmdlist" BANK $7E SLOT 2 ORGA $4F40 FORCE
FightCommandListRam dsb $80
.ENDS

; P1/P2 combo counters; must not alias campaign/team vars at $10C0+.
.RAMSECTION ".fight_combo" BANK $7E SLOT 2 ORGA $4FC0 FORCE
FightComboRam dsb $82
.ENDS

; Bounded MSU voice queue/cache metadata and runtime telemetry.
.RAMSECTION ".fight_streaming" BANK $7E SLOT 2 ORGA $5100 FORCE
FightStreamingRam dsb $0700
.ENDS
; Per-side AI jump-in state.  Sits in the free gap between the combo
; counters and the streaming queue, away from the C stack/stream buffer.
.RAMSECTION ".fight_ai" BANK $7E SLOT 2 ORGA $5042 FORCE
FightAiRam dsb $10
.ENDS
; FUSION juggle/dizzy/MAX/carry state.  The engine addresses it at $5052;
; keep the reservation adjacent so the free 0xAE-byte gap is not reused.
.RAMSECTION ".fight_fusion" BANK $7E SLOT 2 ORGA $5052 FORCE
FightFusionRam dsb $80
.ENDS
.RAMSECTION ".oam_cache" BANK $7E SLOT 2 ORGA $3800 FORCE
OamCacheRam dsb $0800
.ENDS
.RAMSECTION ".fight_stream_cache" BANK $7F SLOT 3 ORGA $0000 FORCE
FightStreamingCache dsb $3000
.ENDS

.INCLUDE "engine/fight.asm"
.INCLUDE "engine/voice_queue.asm"       ; incremental MSU voice loader
.INCLUDE "engine/menus.asm"
.INCLUDE "engine/options.asm"
