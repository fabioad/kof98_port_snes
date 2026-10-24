#include <assert.h>
#include <stdio.h>
#include "stage_anim_data.h"

int main(void)
{
    unsigned int clip, i, duration;
    StageAnimState a, b;
    const StageAnimDef *d;
    for (clip=0; clip<STAGE_ANIM_COUNT; ++clip) {
        d=&stage_anim_defs[clip];
        assert(d->pose_count>=2 && d->pose_count<=3);
        assert(d->step_count>=2 && d->step_count<=4);
        duration=0;
        for(i=0;i<d->step_count;++i) {
            assert(d->steps[i].pose<d->pose_count && d->steps[i].ticks60>0);
            duration+=d->steps[i].ticks60;
        }
        stage_anim_init(&a,d); b=a;
        for(i=0;i<duration;++i) stage_anim_tick60(&a,d);
        assert(a.step==b.step && a.remaining60==b.remaining60);
        /* Ten seconds on PAL and NTSC must produce identical clock state. */
        stage_anim_init(&a,d); stage_anim_init(&b,d);
        for(i=0;i<600;++i) stage_anim_video_tick(&a,d,60,0);
        for(i=0;i<500;++i) stage_anim_video_tick(&b,d,50,0);
        assert(a.step==b.step && a.remaining60==b.remaining60 && a.fraction==b.fraction);
        for(i=0;i<100;++i) assert(!stage_anim_video_tick(&b,d,50,1));
        assert(a.step==b.step && a.remaining60==b.remaining60 && a.fraction==b.fraction);
    }
    d=&stage_anim_defs[STAGE_ANIM_CHINA_REMADOR];
    stage_anim_init(&a,d);
    for(i=0;i<23;++i) assert(!stage_anim_tick60(&a,d));
    assert(stage_anim_pose(&a,d)==0);
    assert(stage_anim_tick60(&a,d) && stage_anim_pose(&a,d)==1);
    puts("PASS: 8 clips, pose limits, cycle wrap, exact boundary, PAL/NTSC and pause.");
    return 0;
}
