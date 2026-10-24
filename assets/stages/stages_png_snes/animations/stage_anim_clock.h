/* Portable timing only. No VRAM/OAM addresses are allocated here. */
#ifndef STAGE_ANIM_CLOCK_H
#define STAGE_ANIM_CLOCK_H
typedef unsigned char StageAnimU8;
typedef unsigned short StageAnimU16;
typedef struct { StageAnimU8 pose, ticks60; } StageAnimStep;
typedef struct {
    StageAnimU8 pose_count, step_count, phase60;
    StageAnimStep steps[4];
} StageAnimDef;
typedef struct {
    StageAnimU8 step, remaining60, fraction;
} StageAnimState;

void stage_anim_init(StageAnimState *state, const StageAnimDef *def);
/* One logical 1/60 s tick; return 1 when the desired pose changes. */
StageAnimU8 stage_anim_tick60(StageAnimState *state, const StageAnimDef *def);
/* One video frame at 50 or 60 Hz. Pause freezes the fractional clock too. */
StageAnimU8 stage_anim_video_tick(StageAnimState *state, const StageAnimDef *def,
                               StageAnimU8 refresh_hz, StageAnimU8 paused);
StageAnimU8 stage_anim_pose(const StageAnimState *state, const StageAnimDef *def);
#endif
