#include "stage_anim_clock.h"

StageAnimU8 stage_anim_pose(const StageAnimState *state, const StageAnimDef *def)
{
    return def->steps[state->step].pose;
}

StageAnimU8 stage_anim_tick60(StageAnimState *state, const StageAnimDef *def)
{
    StageAnimU8 before = stage_anim_pose(state, def);
    if (--state->remaining60 == 0) {
        ++state->step;
        if (state->step == def->step_count) state->step = 0;
        state->remaining60 = def->steps[state->step].ticks60;
    }
    return before != stage_anim_pose(state, def);
}

void stage_anim_init(StageAnimState *state, const StageAnimDef *def)
{
    StageAnimU8 i;
    state->step = 0;
    state->remaining60 = def->steps[0].ticks60;
    state->fraction = 0;
    for (i = 0; i < def->phase60; ++i) stage_anim_tick60(state, def);
}

StageAnimU8 stage_anim_video_tick(StageAnimState *state, const StageAnimDef *def,
                               StageAnimU8 refresh_hz, StageAnimU8 paused)
{
    StageAnimU8 before;
    if (paused || (refresh_hz != 50 && refresh_hz != 60)) return 0;
    before = stage_anim_pose(state, def);
    state->fraction += 60;
    while (state->fraction >= refresh_hz) {
        state->fraction -= refresh_hz;
        stage_anim_tick60(state, def);
    }
    return before != stage_anim_pose(state, def);
}
