/* off-game check of klonline_read.h's pure helpers: cl klonline_read_test.c */
#include <stdio.h>
#include <string.h>
#include <windows.h>
struct klb_snap { int x; };
#include "klonline_read.h"
int main(void){ int l=-1,f=0;
 f+=klor_killer_latch(&l,0,3,16)!=-1; f+=klor_killer_latch(&l,1,3,16)!=3; f+=klor_killer_latch(&l,1,-1,16)!=3; f+=klor_killer_latch(&l,0,-1,16)!=-1;
 f+=!klor_round_ok(1,10); f+=klor_round_ok(11,10); f+=klor_round_ok(0,0);
 f+=klor_loot_share(100,40)<0.59f; f+=klor_loot_share(0,0)!=0; f+=!klor_flags_dead(4); f+=klor_flags_dead(0x40);
 { char s[8]="J.c."; klor_upper(s); f+=strcmp(s,"J.C.")!=0; }
 printf("klonline_read_test: %s\n", f?"FAIL":"ok"); return f; }
