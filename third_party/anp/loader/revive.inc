/* ==================== revive.inc: Dead Men's wounded mercs + adrenaline revive, in Dog Days (13 Oct) ====================
   Included by anp_loader.c after equipassist.inc (uses anp_log, readable, g_dir, g_cscene/g_cmpCs, godmode.inc's
   god_writable / GOD_VAR / GOD_DIFF_VAR, failwatch.inc's fw_world / fw_hpblk, climb.inc's climb_guarded, cl_curT,
   cl_disp_cur, g_clMainTid, v3dist, CL_PLAYER_VT, and squad.inc's sq_call_raw / g_sqEspDelta, sq_rd family, sq_player,
   sq_merc_body, sq_merc, sq_rel, sq_name, sq_busy, sq_hud_state, sq_dev_down, sq_foreground, sq_soldiers, sq_rate,
   sq_cat, g_sqc). Ticked once per gameplay frame from climb.inc's frame hook (anp_rcb_pre), after equipassist_frame().
   Design: work\revive\DESIGN.md, implemented as the critique's VARIANT B (no vptr swap: data writes + guarded calls).

   CEG: no kl2 code byte is changed. Heap writes only (script +0x124, body +0x5cb, DND task +0x14, mask word
   [body+0x54]+0x3a bit 0x4000, P+0xd34 / +0x998 / +0x99c for the duration of one action create, heal action +0x1c,
   body +0x888 when stale, HP block [body+0x5fc] +0x1c/+0x20 = no regen while DOWN / WSTAND, SetHitPoints(1) in WSTAND)
   and calls into kl2's own functions, each inside climb_guarded() and through sq_call_raw()
   (esp checked). A fault or a stack mismatch disables the module for the session ("revive: DISABLED") after a cleanup
   that gives back every write (holds released, mask bits cleared, +0x124 restored, P fields restored; a DEAD merc's
   hold is parked far ahead instead of released, so his DND tail can never stand him up).
   dry (also: no ANP_revive.txt) writes nothing: the only engine calls are the lookups 0x426890 / 0x4c05c0 / 0x59d550
   (the anim RNG dword [[0xdd2640]+0xb30] that 0x59d550 advances is saved and put back around each call) and the room
   test 0x70f330; revive_is_down() answers 0 unless live, so squad.inc / give.inc stay stock.

   Checkpoints: DD's checkpoint saves script +0x124 (load 0x5bf4f3 writes it back), so a checkpoint taken while live
   carries our Force (1) / the buddy's Prevent (2). DD's own value from before our first write is kept per script for
   the whole scene (g_rvOrig) and put back after a reload while not live (dry, off); live re-adopts it as ours.

   ---- Dead Men rule (kaneandlynch.exe) ----
   A merc at 0 HP goes wounded instead of dying, cannot be hurt further, and bleeds out after 60 / 45 / 30 s (difficulty
   records +0xc x 1024). Within 200 cm the player heals him (prompt, use, ZFFActionHealWounded, /Special_moves/Heal_wounded,
   HP = max at 2.0 s). No healing in M01. Bleed-out -> death -> MF_01_MercDead (every merc, Lynch included). The god cheat
   stops the bleed-out.

   ---- Dog Days pieces (kl2.exe, static RE 13 Oct; every address re-read by disassembly for this file) ----
   ZSoldier@CPPScript vt 0xbd0954: slot 51 (+0xcc) = 0x688190 TryDownNotDead(hit, force) thiscall ret 8 -> al:
     [[s+0x6d8]] == 6 -> 0, else jmp 0x70e0e0: body vt+0x654 -> 0; dying task [s+0x4b4]+8 must be 0 or 4;
     0x70f330(DND task) (16-direction room test, thiscall, no args, ret) must be 1; force == 0 only: body+0x5cb != 0 (non-
     buddy, "already downed once", set by DND Run 0x5f4b56) -> 0, attacker distance vs cfg+0x5c, hit+0x28 >= 1000
     (500000 buddy) -> 0; then s+0x124: 1 = Force (go), 2 = Prevent (0); force -> go; else cooldown/random. go: 0x4860e0,
     push DND task (0x6cabf0, prio 0x30dac), body+0x64c = 1, 0x6c75c0(mask, 0.1 s, 0x800). hit == NULL is handled
     (0x70e152, 0x70e1b6, 0x70e2a0 test edi).
   Hit handler (slot 96, 0x8473a0): new HP <= 0 and mask word [body+0x54]+0x3a == 0 (or the buddy) -> slot 51 (force 0)
     (0x847958); mask != 0 -> no HP write (0x8477ae). Death is synchronous inside the hit, hence Variant B:
       (a) every frame: s+0x124 = 1 (Force, what SquadModifier handler 0x803530 writes) and body+0x5cb = 0, so a lethal
           hit that passes the remaining force-0 gates (attacker distance, damage >= 1000) goes down natively;
       (b) HP FLOOR: at HP <= floor x max (0.25) the loader sets mask bit 0x4000 and calls 0x688190(s, NULL, 1), each
           frame until the DND task is current (gates: vehicle, room, dying task, +0x124 == 2).
   ZDownNotDeadNPC@CPPScript vt 0xbcfd24 (script+0x4b8; +4 = script): Start 0x7ea990: +0x14 = now + rand(cfg+0x4c..0x50)
     x 1024 (buddy cfg+0x40..0x44), HP raised to 0.25 x max (0x7eaaf1), body+0x64c = 1. Run 0x5f4ac0 loops while
     +0x14 >= now (0x5f4bc1, 0x5f4c99), then get-up: HP = 0.75 x max, SetLifeState(1). End 0x67fa10: body+0x64c = 0.
     => HOLD = write +0x14 = now + 2048 every frame. Valid DOWN (CHANGE 7): body+0x64c == 1, s+0x74 (current task) ==
     s+0x4b8, task vt 0xbcfd24, task+4 == s; else reset without heal (checkpoint restores un-down natively, slot 12).
   Die = slot 52 (+0xd0) 0x5063e0 -> 0x4bd540, thiscall(float pos[3]*, float dir[3]*, float force, info*) ret 0x10:
     returns at once if the dying task is current; SetHitPoints(0); killer = handle info+0xc (0 = none); dying task
     prio 0x30db3 via 0x4bc0e0 (copies info+0..+0x14); its end calls vt+0x588(0) -> slot 56 -> +0x513 -> MF_01 (0x6d25fa).
   ZFFActionHealWounded vt 0xbb54fc: factory P vt+0x384 = 0x839740(P, 0x12) ret 4 (case 0x83985f: clip = P+0x99c when
     crouched (vt+0x3cc) else P+0x998, target = P+0xd34; ctor 0x907300: +8 P, +0xc target, +0x10 clip, +0x18 = 0, target
     ZActor -> target+0x888 = 1; instant heal (+0x18 = 1, 0x7e75b0) when |dy| > 50 cm or P+0xee4); start P vt+0x370 =
     0x542c00(P, act) ret 4 (Start 0x6244b0: +0x20 = (now + (frames-1)/25 x 1024)/1024 s, +0x1c = (now + 0x1c2)/1024 s,
     float seconds); Update 0x4c7850: now > +0x20 x 1024 -> done; now > +0x1c x 1024 -> +0x18 = 1, 0x7e75b0(P, target)
     = SetHitPoints(GetMaxHitPoints()); End 0x4ea150: target+0x888 = 0, target vt+0x588(1) (life 1, unconditionally).
   Prompt: 0x4c06c0(P, id, inType, float dist, a4, a5, b6, b7) thiscall ret 0x1c writes the PENDING prompt (+0xd00..);
     the use routine commits it to SHOWN (+0xcfc id, +0xd04 input type) at 0x550e3c. Input type 0 = [P+0x818] bit 5
     (0x50a904; mirrors P+0xb90 bit 3, 0x54484a). id 0x1b = UA_HEAL_WOUNDED_COOP_PLAYER. The native use path
     (0x550bee) would start action 0x12 on P+0xd34, but the SP heal scan 0x7aaaf0 writes P+0xd34 = 0 every idle frame
     (0x7aab79; P+0xd30 is not 0 in SP), so the START is ours (CHANGE 1): shown id 0x1b + use edge -> P+0xd34 = body,
     create, start, P+0xd34 cleared at once.
   0x4c05c0(P, name) ret 4 = name -> id (P+0x80, 0x68a730) -> variant 0x59d550 (advances the anim RNG). Bodies: 0x426890
     (body, WORD *id, name) ret 8 + 0x59d550(body, id) ret 4 (called on [script+0x40] bodies by kl2 itself, 0x48f178).
   0x7e72d0(body, state) ret 4 = raw life-state write (state 0: no OnDeath; SetLifeState 0x6cee20 adds slot 56).
   Fail: 0x7864f0(0x156b3b0, const char *key, char 0) ret 8 + 0x8edc40(0x156b3b0, char 0) ret 4 (0x8ce1fb passes a
     literal key; key = kl2's own string 0xb3b014 "AllLevels/Menu/Ingame/MF_01_MercDead").
   Data: merc list [0x1548fd8] / 0x1548fdc[16]; buddy gameMgr+0x4cf0; clock [0xdd2640]+0x48 (1/1024 s, stops while
   paused); difficulty 0x156b5f0 (0..3); god switch 0x1535a2c; state counter [0xe0e644]; DND cfg [0x168d7c0].

   HP regeneration (14 Oct, static RE; the M03B flap): every ZFFActor update (slot 87 0x40ef60, call at 0x40f24d) runs
     0x419570 on the HP block h = [body+0x5fc] (h+4 cur, h+8 max, h+0x24 owner): when h+0x18 (full-regen seconds) >
     1/8192, h+1 (enabled) != 0, h+0 == 0, now > h+0x1c (regen start) and now > h+0x20 (last tick), 0 < cur < max:
     cur += (now - h+0x20)/1024 x max / h+0x18, h+0x20 = now. Every HP write (SetHP 0x61efd0, damage 0x8a7c60) sets
     h+0x1c = h+0x20 = now + 1024 x h+0x14 (delay). DND Start's SetHitPoints(0.25 max) therefore started the regen
     8 s after the down at max/8 per s (log: 220.5 for 8 s, then +110/s to 881.9) - DD's own regen, not DND code.
     DM: a wounded merc does not regen. NO REGEN: while DOWN / WSTAND (live) h+0x1c = now + 2 s and h+0x20 = now every
     frame (data only; it lapses by itself within 2 s of our last write, so nothing needs giving back).

   ---- State machine (per merc) ----
     NORMAL --HP <= floor, every hard gate passes (type 6, +0x64c, dying task, vehicle, room)--> 0x688190(s, NULL, 1)
            accepted --> PENDING (mask; a lost push is retried every 1.5 s; after pend ms -> WSTAND)
     NORMAL --HP <= floor, a hard gate refuses (room, type 6, vehicle, no task, 0x688190 = 0)--> WSTAND (14 Oct,
            critique change 2): mask (no HP loss for a non-buddy, 0x8477ae / 0x847945), HP clamped >= 1 by
            SetHitPoints, no regen, bleed timer running, heal prompt + heal (ZFFActionHealWounded has no DND test:
            ctor 0x907300, Start 0x6244b0, Update 0x4c7850, apply 0x7e75b0 = SetHitPoints(max), End 0x4ea150 =
            +0x888 0 + vt+0x588(1), a no-op on life 1), 0x688190(s, NULL, 1) retried every 2 s (accepted -> PENDING
            -> DOWN keeping the bleed deadline). Dying / already-down gates stay refusals (no mask, backoff 10..160 s).
            No usable mask object -> the old refusal (no WSTAND).
     NORMAL / PENDING / WSTAND --DND task current--> DOWN (mask, hold, no regen, deadline = now + bleed[difficulty] x
            1024, or the deadline he already had (WSTAND / PENDING from WSTAND), or the bleed time left over when he went
            down again within 5 s of a native end; buddy=dm: +0x124 = 2)
     NORMAL --DND task current, but we left DOWN / GETUP with his DND task still pushed less than 10 s ago--> stays
            NORMAL (no re-entry; at most one re-entry per 10 s after we let go, logged once per window)
     DOWN --heal action on him with +0x18 == 1--> GETUP (hold released, mask kept until DND End, then HP = max)
     DOWN --HP changes--> nothing: DD's down-state behaviour (DND Start 0.25 x max, regen) is not a way out (the
            14 Oct RESTORED(external) exit made him flap DOWN/NORMAL once a second and end pinned DOWN at full HP)
     DOWN --DND task pushed but not current (a task on top of it)--> stays DOWN (mask, hold, bleed); no prompt; after
            30 s like that -> NORMAL (logged)
     DOWN --DND task neither current nor pushed (native end)--> NORMAL, mask + hold given back
     DOWN / WSTAND --deadline (no heal on him, god switch 0 or godpause=0)--> BLEED: mask cleared, Die (slot 52) -> DEAD
     WSTAND --heal lands--> NORMAL (mask cleared, HP = max by the heal itself); --HP back to max without our heal (a
            script)--> NORMAL (mask cleared)
     DOWN / GETUP / WSTAND --life byte != 1--> DEAD (mask cleared, never healed; the prompt and heal start need life 1)
     DEAD: hold kept 10 s and while his DND task is still pushed (current, or under the dying task: +0x64c 1); life 1
           again within 2 s of his death, while a heal targets him / +0x888, or 2 s after that heal -> life 0 seen
           before (his OnDeath ran): 0x7e72d0(body, 2) + (body, 0) (unregister, no second OnDeath); life 0 never seen
           (ragdoll set 2 without OnDeath, heal End set 1): SetLifeState 0x6cee20(body, 0) = OnDeath exactly once
     any: DOWN no longer valid -> NORMAL (reset, logged); [0xe0e644] change / same-scene player change / list drop ->
           writes given back (while the objects still validate), records forgotten; scene change -> forgotten.
           Merc list count 0 (cleared by 0x76c915 on a restart; the old objects may be freed) -> records and the
           +0x124 table forgotten with no write.
           A record that finds bit 0x4000 on its own mask object without having set it clears it (after any live).

   Config <DD>\ANP_revive.txt (polled once a second). NO FILE = dry. First bare token = mode, then key=value:
     off | dry | live    dry: everything is read and logged ("would ..."), nothing is written, no engine call that
                         changes state (0x70f330 / name lookups only). live: the rule above.
     buddy=dd|dm         dd (default): Lynch stays stock DD (cfg+0x60: a refused down keeps him at HP 1). dm: Lynch goes
                         down like any merc and can bleed out (MF_01; M05 left to ZLevelCtrlM05's MF_05); while he is
                         DOWN +0x124 = 2 so a hit on him is refused by slot 51 and DD's cfg+0x60 sets HP 1 (0x84797e);
                         refused (logged, Lynch stays stock) when cfg+0x60 is 0
     exclude=M14:Merc_01 Lvl:MercN list (Merc_NN -> +0x6e8 NN+1, Kane = 1, or the raw id); 'none' clears. Excluded mercs
                         get no Force write and no floor (DM eHM_NotHealable; default M14 Merc_01 = id 2)
     floor=0.25          HP fraction that downs a merc (0.05 .. 0.9)
     bleed=60,45,30,30   seconds per DD difficulty 0..3 (Extreme = DM Hard)
     heal=dm|dd          dm: the heal lands at 2.0 s (act+0x1c); dd: DD's 0.44 s
     clip=dm|dd          dm: /Special_moves/Heal_wounded for the player; dd: DD's Heal_Down_not_dead(_Crouch)
     range=200 maxdy=50  cm (DM 0x94159c; above maxdy DD heals instantly; 0 = allow)
     m01=0               1: allow healing in M01 (Dead Men forbids it)
     godpause=1          bleed clock paused while the god switch 0x1535a2c is set
     use=both            flag (P+0x818 bit 5) | key (DIK key= on DD's keyboard device) | both
     key=0x12            DIK of the fallback use key (E)
     pend=3000           ms a PENDING merc may wait for DD's DND before the floor gives up (mask cleared)
     trace=0             1: 1 Hz line per down merc
   Test commands <DD>\ANP_revive_cmd.txt (consumed -> .done, one line per frame):
     down <merc|buddy|nearest|all> | wstand <merc|nearest|all> (WSTAND directly, no gates) | heal [merc|nearest] |
     bleed <merc|all> | state | wait S
   Log lines start with "revive:". */

#define RV_SCRIPT_VT   0xbd0954   /* ZSoldier@CPPScript */
#define RV_DND_VT      0xbcfd24   /* ZDownNotDeadNPC@CPPScript */
#define RV_HEAL_VT     0xbb54fc   /* ZFFActionHealWounded */
#define RV_F_TRYDOWN   0x688190   /* script slot 51 */
#define RV_F_DIE       0x5063e0   /* script slot 52 */
#define RV_F_CANDOWN   0x70f330   /* DND task room test */
#define RV_F_OFFER     0x4c06c0   /* ZFFPlayer offer prompt */
#define RV_F_PCLIP     0x4c05c0   /* ZFFPlayer clip by name */
#define RV_F_NAMEID    0x426890   /* actor name -> id */
#define RV_F_VARIANT   0x59d550   /* actor id -> clip variant */
#define RV_F_SETHP     0x792bc0   /* ZFFActor vt+0x670 */
#define RV_F_LIFE      0x7e72d0   /* raw life state */
#define RV_F_SETLIFE   0x6cee20   /* ZFFActor vt+0x588 SetLifeState: (0) = 0x7e72d0(2), slot 56 OnDeath, 0x7e72d0(0) */
#define RV_F_KILL      0x8af4b0   /* ZFFActor vt+0x5e4 */
#define RV_F_FAILTXT   0x7864f0
#define RV_F_FAIL      0x8edc40
#define RV_F_CREATE    0x839740   /* ZFFPlayer vt+0x384 */
#define RV_F_START     0x542c00   /* ZFFPlayer vt+0x370 */
#define RV_FAILOBJ     0x156b3b0
#define RV_KEY_MF01    0xb3b014
#define RV_CFG         0x168d7c0
#define RV_MERCS       0x1548fd8
#define RV_GS          0xe0e644
#define RV_MASK        0x4000
#define RV_PROMPT_ID   0x1b
#define RV_MAXM        20
#define RV_F_ISDOWN    0x410a30   /* ZFFActor vt+0x654 (the 0x70e0f8 gate): mov al,[ecx+0x64c]; ret */
#define RV_ACTOR_VT    0xbb3bac   /* ZFFActor (merc bodies) */
#define RV_CLOCK       0xdd2640   /* [RV_CLOCK]+0x48 game time, +0xb30 anim RNG (0x59d550 advances it) */
#define RV_PARK        0x4000000  /* DND hold left on a DEAD merc when we let go (about 18 h of game time) */
#define RV_MAXEXCL     8
#define RV_F_REGEN     0x419570   /* HP block regen tick (ZFFActor slot 87 calls it on [body+0x5fc]); read only, never called */
#define RV_NOREENT     10240      /* 10 s: no native re-entry into DOWN after we let go of a still-pushed DND task */
#define RV_WS_RETRY    2048       /* 2 s: WSTAND retries 0x688190(s, NULL, 1) */
#define RV_SUSP_MAX    30720      /* 30 s: DOWN with the DND task pushed but not current, then NORMAL */

enum { RV_OFF, RV_DRY, RV_LIVE };
static const char *const RV_MODE[] = {"off", "dry", "live"};
enum { RS_NORMAL, RS_PENDING, RS_DOWN, RS_GETUP, RS_DEAD, RS_WSTAND, RS_EXCL };
static const char *const RS_NAME[] = {"NORMAL", "PENDING", "DOWN", "GETUP", "DEAD", "WSTAND", "EXCLUDED"};
enum { RVU_FLAG = 1, RVU_KEY = 2, RVU_BOTH = 3 };
/* hard refusals of 0x688190(s, NULL, force 1): with force 1 and +0x124 != 2 these are the only gates (0x688199,
   0x70e0f8, 0x70e10e, 0x70e121 -> 0x70f330 incl. its vehicle test 0x70f348); checked BEFORE the mask is set */
enum { RG_TYPE6, RG_ISDOWN, RG_DYING, RG_VEHICLE, RG_ROOM, RG_NOTASK, RG_REFUSED, RG_NOSTART, RG_N };
static const char *const RV_GATE[RG_N] = {
    "gate type 6 ([[s+0x6d8]] == 6, 0x688199)", "body+0x64c already set (vt+0x654 = 0x410a30, 0x70e0f8)",
    "dying task state not 0/4 (0x70e10e)", "in a vehicle (body+0x774, 0x70f348)", "room test 0x70f330 = 0",
    "no valid DND task at s+0x4b8", "0x688190 refused although every known gate passed", "DD never started the DND task"};

typedef struct { char sc[8]; int id; } RvExcl;     /* exclude=Lvl:MercN: no Force write, left to DD (DM NotHealable) */
typedef struct {
    int mode, buddyDm, healDm, clipDm, m01, godpause, use, key, trace, pendMs;
    float floor, range, maxdy;
    int bleed[4];
    int nexcl; RvExcl excl[RV_MAXEXCL];
} RvCfg;
/* default exclusion: M14 Merc_01 (Shelly; DM node 897 eHM_NotHealable). Converted data (work\out_rel4\M14, node 1000
   ZSoldier speaker 'Shelly' = 'Merc_01'; dd_enums EIsMercenary Merc_01 = 2) -> script +0x6e8 = 2 */
#define RV_CFG_DEFAULT {RV_DRY, 0, 1, 1, 0, 1, RVU_BOTH, 0x12, 0, 3000, 0.25f, 200.0f, 50.0f, {60, 45, 30, 30}, 1, {{"M14", 2}}}
static RvCfg g_rvc = RV_CFG_DEFAULT;
static int g_rvcPresent = -1; static FILETIME g_rvcTime; static DWORD g_rvcPoll;
static int g_rvDead, g_rvBuild = -1, g_rvLines, g_rvEverLive;

typedef struct {
    BYTE *s, *body, *maskObj; int merc, buddy, st, used;
    int stT, deadline, coolT, dieT, deathT, killT, getupT, staleT, lastTryT, tryOk, tries;
    int orig124, wrote124, wrote2, maskSet, hold, clipsOk, maskOk, healSeen, healOnSeen, bledDry, deferLogged, lowLogged, failDone;
    int undeadN, healEndT, gateLogged, gateBackoff, leftT, leftBleed, staleMaskN;
    int saw0;                                         /* DEAD: life 0 seen = SetLifeState(0) ran, so his OnDeath ran (0x6cee96) */
    int noReentUntil, reentLogged;                    /* FIX 1: no native re-entry into DOWN right after we let go */
    int suspT, suspLogged, hpRiseLogged, regenLogged; /* FIX 1: DND suspended under another task; HP rise / regen notes */
    int keepDl, wsRetryT, wsTries, clampN;            /* FIX 2: WSTAND (keep the bleed deadline into DOWN, retries, HP clamps) */
    float baseHp, lastHp; int lastLife, lastDnd; DWORD traceT;
    char name[40];
} RvMerc;
static RvMerc g_rvm[RV_MAXM]; static int g_rvn;
/* +0x124 before our first write, per script, for the whole scene: a checkpoint saves our Force (1) / buddy Prevent (2)
   with the script (load 0x5bf4f3 writes it back), so a reload must not take the saved value for DD's own */
static struct { BYTE *s; int merc, orig, had2; } g_rvOrig[RV_MAXM]; static int g_rvOrigN; static DWORD g_rvOrigGs; static char g_rvOrigScene[8];
static struct {
    BYTE *P; char scene[8]; int lastT, gsSeen, preflight, levelOk, logged, prevUse, promptUp, healStarts;
    DWORD gs, t0, cmdPoll, waitUntil;
    BYTE *dmClip, *offerBody, *kb, *sys; int offerT;
} g_rv;
static char g_rvQ[16][96]; static int g_rvQh, g_rvQn;
static struct { BYTE *P, *d34, *c998, *c99c; } g_rvPfix;   /* player fields saved around the heal create */

/* ---------- logging, calls ---------- */
static void rv_log(const char *fmt, ...) {
    if (g_rvLines > 6000) return;
    if (++g_rvLines == 6000) { anp_log("revive: log line cap reached, revive logging stops"); return; }
    char b[1600]; va_list ap; va_start(ap, fmt); _vsnprintf(b, sizeof b - 1, fmt, ap); va_end(ap); b[sizeof b - 1] = 0;
    anp_log("revive: %s", b);
}
static void rv_kill(const char *where, const char *why) {
    if (!g_rvDead) anp_log("revive: DISABLED for this session (%s in %s) - restart the game before testing again", why, where);
    g_rvDead = 1;
}
static DWORD rv_call(const char *what, DWORD fn, void *self, int n, const DWORD *a) {
    if (g_rvDead) return 0;
    g_sqEspDelta = 0;
    DWORD r = sq_call_raw(fn, self, n, a, 0);
    if (g_sqEspDelta) { anp_log("revive: esp mismatch after %s (fn %08lx, delta %d)", what, fn, g_sqEspDelta); rv_kill(what, "stack mismatch"); }
    return r;
}
static DWORD rv_call0(const char *w, DWORD fn, void *self) { return rv_call(w, fn, self, 0, NULL); }
static DWORD rv_call1(const char *w, DWORD fn, void *self, DWORD a0) { DWORD a[1] = {a0}; return rv_call(w, fn, self, 1, a); }
static DWORD rv_call2(const char *w, DWORD fn, void *self, DWORD a0, DWORD a1) { DWORD a[2] = {a0, a1}; return rv_call(w, fn, self, 2, a); }
static DWORD rv_vf(void *o, int off) { return rd32((BYTE*)rd32(o) + off); }
static int rv_live(void) { return g_rvc.mode == RV_LIVE && g_rvBuild == 1 && g_rv.levelOk == 1 && !g_rvDead; }

/* this kl2 build: prologues of every function called, the code the design depends on, the vtable slots (read only) */
static int rv_check_build(void) {
    static const struct { DWORD a; BYTE n, b[12]; } t[] = {
        {RV_F_TRYDOWN, 12, {0x55, 0x8b, 0xec, 0x8b, 0x81, 0xd8, 0x06, 0x00, 0x00, 0x83, 0x38, 0x06}},
        {RV_F_DIE,      8, {0x55, 0x8b, 0xec, 0x83, 0xec, 0x14, 0x53, 0x56}},
        {RV_F_CANDOWN,  8, {0x55, 0x8b, 0xec, 0x83, 0xec, 0x34, 0x56, 0x8b}},
        {RV_F_OFFER,    8, {0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c, 0x57, 0x8b}},
        {RV_F_PCLIP,    8, {0x51, 0x56, 0x8b, 0xf1, 0x8b, 0x4c, 0x24, 0x0c}},
        {RV_F_NAMEID,   8, {0x8b, 0x54, 0x24, 0x08, 0x56, 0x8b, 0x74, 0x24}},
        {RV_F_VARIANT, 12, {0x83, 0xec, 0x0c, 0xa1, 0x40, 0x26, 0xdd, 0x00, 0x8b, 0x90, 0x30, 0x0b}},   /* +0xb30 anim RNG */
        {RV_F_ISDOWN,   7, {0x8a, 0x81, 0x4c, 0x06, 0x00, 0x00, 0xc3}},
        {0x70e0ee,     12, {0x8b, 0x90, 0x54, 0x06, 0x00, 0x00, 0xff, 0xd2, 0x84, 0xc0, 0x0f, 0x85}},   /* body vt+0x654 gate */
        {0x70e0fe,     11, {0x8b, 0x86, 0xb4, 0x04, 0x00, 0x00, 0x8b, 0x40, 0x08, 0x85, 0xc0}},          /* dying task state */
        {0x70e109,      6, {0x74, 0x09, 0x83, 0xf8, 0x04, 0x0f}},                                    /* ... 0 or 4 */
        {0x70f348,      7, {0x83, 0xb9, 0x74, 0x07, 0x00, 0x00, 0x00}},                              /* vehicle test */
        {0x7e72f9,     10, {0x8b, 0x06, 0x8b, 0x90, 0x0c, 0x06, 0x00, 0x00, 0x6a, 0x00}},              /* life 2 branch */
        {RV_F_SETHP,    8, {0xd9, 0x44, 0x24, 0x04, 0x51, 0x8b, 0x89, 0xfc}},
        {RV_F_LIFE,     8, {0x53, 0x8b, 0x5c, 0x24, 0x08, 0x56, 0x8b, 0xf1}},
        {RV_F_SETLIFE, 12, {0x81, 0xec, 0x80, 0x00, 0x00, 0x00, 0x56, 0x8b, 0xf1, 0x8a, 0x8e, 0x76}},   /* SetLifeState: cl = +0x576 */
        {0x6cee3a,      4, {0x3b, 0xc7, 0x74, 0x7c}},                                              /* same state -> return */
        {0x6cee7e,     10, {0x8b, 0x11, 0x8b, 0x82, 0xe0, 0x00, 0x00, 0x00, 0xff, 0xd0}},          /* script slot 56 OnDeath */
        {0x6cee93,      8, {0x57, 0x8b, 0xce, 0xe8, 0x35, 0x84, 0x11, 0x00}},                      /* 0x7e72d0(0): the only life 0 */
        {RV_F_KILL,     8, {0x56, 0x8b, 0xf1, 0xe8, 0x78, 0x49, 0xb6, 0xff}},
        {RV_F_FAILTXT,  8, {0x8a, 0x44, 0x24, 0x08, 0x8b, 0x54, 0x24, 0x04}},
        {RV_F_FAIL,    11, {0x83, 0xec, 0x0c, 0x53, 0x55, 0x56, 0x0f, 0xbe, 0x74, 0x24, 0x1c}},
        {RV_F_CREATE,   7, {0x6a, 0xff, 0x68, 0x9b, 0xbf, 0xac, 0x00}},
        {RV_F_START,    8, {0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c, 0x8b, 0x07}},
        /* code the design reads its data from */
        {0x5f4bc1, 11, {0x8b, 0x56, 0x14, 0xa1, 0x40, 0x26, 0xdd, 0x00, 0x3b, 0x50, 0x48}},    /* DND hold: task+0x14 >= now */
        {0x70e1e8,  9, {0x8b, 0x86, 0x24, 0x01, 0x00, 0x00, 0x83, 0xe8, 0x01}},                  /* s+0x124 Force/Prevent */
        {0x70e13f, 10, {0x8b, 0x46, 0x40, 0x80, 0xb8, 0xcb, 0x05, 0x00, 0x00, 0x00}},            /* body+0x5cb gate */
        {0x70e2e0,  7, {0xc6, 0x81, 0x4c, 0x06, 0x00, 0x00, 0x01}},                              /* body+0x64c = 1 */
        {0x8477ae,  5, {0x66, 0x83, 0x79, 0x3a, 0x00}},                                          /* mask word gate */
        {0x83988f, 12, {0x8b, 0x8e, 0x9c, 0x09, 0x00, 0x00, 0x8b, 0x96, 0x34, 0x0d, 0x00, 0x00}}, /* factory: +0x99c, +0xd34 */
        {0x9073a3,  7, {0xc6, 0x87, 0x88, 0x08, 0x00, 0x00, 0x01}},                              /* ctor: target+0x888 = 1 */
        {0x4ea1ad,  7, {0xc6, 0x81, 0x88, 0x08, 0x00, 0x00, 0x00}},                              /* End: target+0x888 = 0 */
        {0x6245fc,  3, {0xd9, 0x5e, 0x20}}, {0x624618, 3, {0xd9, 0x5e, 0x1c}},                   /* Start: +0x20 / +0x1c */
        {0x4c7883,  3, {0xd8, 0x4e, 0x1c}},                                                      /* Update: x +0x1c */
        {0x50a904,  9, {0x8b, 0x81, 0x18, 0x08, 0x00, 0x00, 0xc1, 0xe8, 0x05}},                  /* input type 0 = P+0x818 bit 5 */
        /* HP regen (no-regen hold): ZFFActor update -> 0x419570([body+0x5fc]); now > h+0x1c, then dt from h+0x20 */
        {0x40f247, 11, {0x8b, 0x8e, 0xfc, 0x05, 0x00, 0x00, 0xe8, 0x1e, 0xa3, 0x00, 0x00}},
        {0x4195a2, 12, {0x8b, 0x48, 0x48, 0x3b, 0x4e, 0x1c, 0x0f, 0x8e, 0xc1, 0x00, 0x00, 0x00}},
        {0x4195ae,  3, {0x8b, 0x56, 0x20}},
        {0x847945,  4, {0x66, 0x39, 0x78, 0x3a}},                                                /* mask: no death for a non-buddy */
    };
    for (unsigned i = 0; i < sizeof t / sizeof t[0]; i++)
        if (!readable((void*)t[i].a, t[i].n) || memcmp((void*)t[i].a, t[i].b, t[i].n)) { anp_log("revive: kl2 build mismatch at %08lx - revive stays dry", t[i].a); return 0; }
    static const struct { DWORD vt, off, v; } s[] = {
        {RV_SCRIPT_VT, 0xcc, RV_F_TRYDOWN}, {RV_SCRIPT_VT, 0xd0, RV_F_DIE},
        {RV_DND_VT, 4, 0x7ea990}, {RV_DND_VT, 8, 0x5f4ac0}, {RV_DND_VT, 12, 0x67fa10},
        {RV_HEAL_VT, 8, 0x6244b0}, {RV_HEAL_VT, 16, 0x4c7850}, {RV_HEAL_VT, 20, 0x4ea150},
        {CL_PLAYER_VT, 0x370, RV_F_START}, {CL_PLAYER_VT, 0x384, RV_F_CREATE},
        {0x83a6b0 + (0x12 - 4) * 4, 0, 0x83985f},                                                  /* factory case 0x12 */
        {0x50a968, 0, 0x50a904},                                                                    /* input type 0 case */
        {RV_ACTOR_VT, 0x654, RV_F_ISDOWN}, {RV_ACTOR_VT, 0x588, RV_F_SETLIFE},
    };
    for (unsigned i = 0; i < sizeof s / sizeof s[0]; i++)
        if (!readable((void*)(s[i].vt + s[i].off), 4) || *(DWORD*)(s[i].vt + s[i].off) != s[i].v) {
            anp_log("revive: kl2 table mismatch at %08lx+%lx (want %08lx) - revive stays dry", s[i].vt, s[i].off, s[i].v); return 0;
        }
    if (!readable((void*)RV_KEY_MF01, 37) || memcmp((void*)RV_KEY_MF01, "AllLevels/Menu/Ingame/MF_01_MercDead", 37)) { anp_log("revive: MF_01 key string moved - revive stays dry"); return 0; }
    return 1;
}

/* ---------- config ---------- */
/* exclude=M14:Merc_01,M05:3,none ... : Merc_NN / MercNN = DD EIsMercenary NN + 1, Kane / buddy = 1, a number = the raw
   script +0x6e8 value; 'none' clears the list (the default M14:Merc_01 included) */
static void rv_parse_excl(RvCfg *c, const char *v) {
    char b[256]; _snprintf(b, sizeof b, "%s", v); b[sizeof b - 1] = 0;
    for (char *p = b, *e; p && *p; p = e) {
        e = strchr(p, ','); if (e) *e++ = 0;
        if (!_stricmp(p, "none")) { c->nexcl = 0; continue; }
        char *col = strchr(p, ':');
        if (!col || col == p || col - p > 7) { anp_log("revive: config exclude '%s' ignored (want Lvl:MercN)", p); continue; }
        *col = 0; const char *w = col + 1; int id = -1;
        if (!_stricmp(w, "kane") || !_stricmp(w, "buddy")) id = 1;
        else if (!_strnicmp(w, "merc", 4)) { const char *d = w + 4; if (*d == '_') d++; if (*d >= '0' && *d <= '9') id = atoi(d) + 1; }
        else if (*w >= '0' && *w <= '9') id = atoi(w);
        if (id < 1 || id > 13) { anp_log("revive: config exclude '%s:%s' ignored (merc unknown)", p, w); continue; }
        if (c->nexcl >= RV_MAXEXCL) { anp_log("revive: config exclude list full (%d)", RV_MAXEXCL); break; }
        _snprintf(c->excl[c->nexcl].sc, 8, "%s", p); c->excl[c->nexcl].sc[7] = 0; c->excl[c->nexcl].id = id; c->nexcl++;
    }
}
static void rv_excl_str(const RvCfg *c, char *o, int n) {
    int k = 0; o[0] = 0;
    for (int i = 0; i < c->nexcl && k < n - 16; i++) k += _snprintf(o + k, n - k, "%s%s:%d", i ? "," : "", c->excl[i].sc, c->excl[i].id);
    if (!c->nexcl) _snprintf(o, n, "none");
    o[n - 1] = 0;
}
static int rv_excluded(const char *scene, int merc) {
    for (int i = 0; i < g_rvc.nexcl; i++) if (g_rvc.excl[i].id == merc && !_stricmp(g_rvc.excl[i].sc, scene)) return 1;
    return 0;
}
static void rv_cfg_poll(void) {
    DWORD now = GetTickCount();
    if (g_rvcPresent >= 0 && now - g_rvcPoll < 1000) return;
    g_rvcPoll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_revive.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (present == g_rvcPresent && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_rvcTime) == 0)) return;
    g_rvcPresent = present;
    if (present) g_rvcTime = fa.ftLastWriteTime;
    RvCfg c = RV_CFG_DEFAULT;
    const char *note = present ? "" : " (no ANP_revive.txt: dry)";
    if (present) {
        char buf[1024] = "";
        static int unreadLogged;
        FILE *f = fopen(fn, "r");
        if (!f) {                                     /* held by an editor / the helper: keep the previous config, retry next poll */
            memset(&g_rvcTime, 0, sizeof g_rvcTime);
            if (!unreadLogged) { unreadLogged = 1; anp_log("revive: ANP_revive.txt unreadable - previous config kept, retry"); }
            return;
        }
        unreadLogged = 0;
        size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
        for (char *p = buf; (p = strchr(p, '#')); ) while (*p && *p != '\n') *p++ = ' ';
        int known = 0;                                /* an explicit known mode word was seen */
        for (char *t = strtok(buf, " \t\r\n;"); t; t = strtok(NULL, " \t\r\n;")) {
            char *eq = strchr(t, '='); const char *k = t, *v = "";
            if (eq) { *eq = 0; v = eq + 1; } else { v = t; k = "mode"; }
            if (!_stricmp(k, "mode")) {
                int m = -1; for (int i = 0; i < 3; i++) if (!_stricmp(v, RV_MODE[i])) m = i;
                if (m < 0) { c.mode = (known && c.mode == RV_OFF) ? RV_OFF : RV_DRY; anp_log("revive: config mode '%s' unknown (unknown mode word: %s)", v, c.mode == RV_OFF ? "off kept" : "dry"); }
                else { c.mode = m; known = 1; }
            }
            else if (!_stricmp(k, "buddy")) c.buddyDm = !_stricmp(v, "dm");
            else if (!_stricmp(k, "heal")) c.healDm = _stricmp(v, "dd") != 0;
            else if (!_stricmp(k, "clip")) c.clipDm = _stricmp(v, "dd") != 0;
            else if (!_stricmp(k, "floor")) { float x = (float)atof(v); if (x >= 0.05f && x <= 0.9f) c.floor = x; }
            else if (!_stricmp(k, "range")) { float x = (float)atof(v); if (x >= 50.0f && x <= 1000.0f) c.range = x; }
            else if (!_stricmp(k, "maxdy")) { float x = (float)atof(v); if (x >= 0.0f && x <= 500.0f) c.maxdy = x; }
            else if (!_stricmp(k, "m01")) c.m01 = atoi(v) != 0;
            else if (!_stricmp(k, "godpause")) c.godpause = atoi(v) != 0;
            else if (!_stricmp(k, "use")) c.use = !_stricmp(v, "flag") ? RVU_FLAG : !_stricmp(v, "key") ? RVU_KEY : RVU_BOTH;
            else if (!_stricmp(k, "key")) c.key = (int)strtol(v, NULL, 0) & 0xff;
            else if (!_stricmp(k, "trace")) c.trace = atoi(v) != 0;
            else if (!_stricmp(k, "pend")) { int x = atoi(v); c.pendMs = x < 500 ? 500 : x > 20000 ? 20000 : x; }
            else if (!_stricmp(k, "exclude")) { c.nexcl = 0; rv_parse_excl(&c, v); }   /* replaces the default list */
            else if (!_stricmp(k, "bleed")) {
                const char *p = v;
                for (int i = 0; i < 4 && *p; i++) {
                    char *e; long x = strtol(p, &e, 0); if (e == p) break;
                    c.bleed[i] = x < 3 ? 3 : x > 600 ? 600 : (int)x;
                    for (int j = i + 1; j < 4; j++) c.bleed[j] = c.bleed[i];   /* a short list repeats its last value */
                    p = (*e == ',') ? e + 1 : e;
                }
            }
            else anp_log("revive: config key '%s' unknown", k);
        }
    }
    g_rvc = c;
    char ex[128]; rv_excl_str(&c, ex, sizeof ex);
    anp_log("revive: config mode=%s buddy=%s floor=%.2f bleed=%d,%d,%d,%d heal=%s clip=%s range=%.0f maxdy=%.0f m01=%d godpause=%d use=%s key=%02x pend=%d trace=%d exclude=%s%s",
            RV_MODE[c.mode], c.buddyDm ? "dm" : "dd", (double)c.floor, c.bleed[0], c.bleed[1], c.bleed[2], c.bleed[3], c.healDm ? "dm" : "dd",
            c.clipDm ? "dm" : "dd", (double)c.range, (double)c.maxdy, c.m01, c.godpause, c.use == RVU_FLAG ? "flag" : c.use == RVU_KEY ? "key" : "both",
            c.key, c.pendMs, c.trace, ex, note);
}

/* ---------- reads ---------- */
static int rv_hp(BYTE *body, float *cur, float *mx) { return fw_hpblk(body, 0x5fc, cur, mx); }
static BYTE *rv_task(BYTE *s) {                         /* the DND task, validated (vt, owner) */
    BYTE *t = (BYTE*)rd32(s + 0x4b8);
    return (sq_rd(t, 0x18) && *(DWORD*)t == RV_DND_VT && *(BYTE**)(t + 4) == s) ? t : 0;
}
static int rv_dnd_current(BYTE *s, BYTE *body) {      /* CHANGE 7: a valid DOWN */
    BYTE *t = rv_task(s);
    return t && rd8(body + 0x64c) == 1 && rd32(s + 0x74) == (DWORD)t;
}
static int rv_dnd_pushed(BYTE *s, BYTE *body) {       /* the DND task is still pushed (current, or under the dying task):
                                                         its tail (HP 0.75, SetLifeState(1)) could still run */
    return rv_task(s) && rd8(body + 0x64c) == 1;
}
static BYTE *rv_heal_act(BYTE *P) {                   /* the player's current action if it is a heal, else 0 */
    BYTE *a = P ? cl_disp_cur(P) : 0;
    return (a && a != (BYTE*)1 && sq_rd(a, 0x24) && *(DWORD*)a == RV_HEAL_VT && *(BYTE**)(a + 8) == P) ? a : 0;
}
static int rv_scene_is(const char *id) { return !_stricmp(g_rv.scene, id); }
static int rv_anp_level(void) { return g_rv.scene[0] == 'M' && g_rv.scene[1] >= '0' && g_rv.scene[1] <= '9'; }
static int rv_gate_type(BYTE *s) { BYTE *p = (BYTE*)rd32(s + 0x6d8); return sq_rd(p, 4) ? (int)*(DWORD*)p : -1; }   /* 0x688190: 6 refuses */
static RvMerc *rv_find_body(const BYTE *b) { for (int i = 0; i < g_rvn; i++) if (g_rvm[i].body == b) return &g_rvm[i]; return 0; }
static int rv_still(RvMerc *m) {                     /* the record still names a live soldier script + body */
    return sq_merc_body(m->s) == m->body || (m->buddy && sq_rd(m->s, 0x740) && rd32(m->s) == RV_SCRIPT_VT && rd32(m->s + 0x40) == (DWORD)m->body && rd32(m->body + 0x77c) == (DWORD)m->s);
}
static int rv_now(void) { return cl_curT(); }

/* ---------- writes (live only; each one checked) ---------- */
static void rv_mask(RvMerc *m, int on) {
    BYTE *o = (BYTE*)rd32(m->body + 0x54);
    if (on) {
        if (!m->maskOk) return;
        if (!o || o != m->maskObj || !god_writable(o + 0x3a, 2)) return;
        *(WORD*)(o + 0x3a) |= RV_MASK; m->maskSet = 1;
    } else if (m->maskSet) {
        if (o && o == m->maskObj && god_writable(o + 0x3a, 2)) *(WORD*)(o + 0x3a) &= (WORD)~RV_MASK;
        m->maskSet = 0;
    }
}
static void rv_hold(RvMerc *m, int T) {
    BYTE *t = rv_task(m->s);
    if (t && god_writable(t + 0x14, 4)) { *(int*)(t + 0x14) = T + 2048; m->hold = 1; }
}
static void rv_release_hold(RvMerc *m, int T) {
    BYTE *t = rv_task(m->s);
    if (m->hold && t && god_writable(t + 0x14, 4) && *(int*)(t + 0x14) > T) *(int*)(t + 0x14) = T;
    m->hold = 0;
}
/* FIX 1: no regen while DOWN / WSTAND (live). h = [body+0x5fc] (owner h+0x24 checked by fw_hpblk). Push the regen
   start h+0x1c to now + 2 s and the last tick h+0x20 to the same time (DD's own convention, 0x61effb..0x61f004), so
   0x419570 never adds HP and the first tick after we stop has a small dt. Lapses by itself 2 s after the last write: nothing to give back. */
static void rv_noregen(RvMerc *m, int T) {
    float c, x; if (!rv_hp(m->body, &c, &x)) return;
    BYTE *h = (BYTE*)rd32(m->body + 0x5fc);
    if (!god_writable(h + 0x1c, 8)) return;
    if (!m->regenLogged) {
        m->regenLogged = 1;
        rv_log("merc=%d '%s': no regen while %s - HP block %p regen delay +0x14 %.2f s, full regen +0x18 %.2f s, enabled +1 %d, start +0x1c - now %d (0x419570 held off)",
               m->merc, m->name, RS_NAME[m->st], h, (double)*(float*)(h + 0x14), (double)*(float*)(h + 0x18), h[1], *(int*)(h + 0x1c) - T);
    }
    if (*(int*)(h + 0x1c) < T + 2048) *(int*)(h + 0x1c) = T + 2048;
    *(int*)(h + 0x20) = *(int*)(h + 0x1c);
}
/* FIX 2: WSTAND keeps him at HP >= 1 (SetHitPoints 0x792bc0 = DD's own setter; the mask already stops hit damage) */
static void rv_hp_floor1(RvMerc *m, float hp) {
    if (hp >= 1.0f || rd8(m->body + 0x576) != 1) return;
    if (rv_vf(m->body, 0x670) != RV_F_SETHP) return;
    rv_call1("SetHitPoints 1 0x792bc0", RV_F_SETHP, m->body, fbits(1.0f));
    if (!g_rvDead && ++m->clampN <= 3) rv_log("merc=%d '%s': WSTAND: HP %.1f clamped to 1 (SetHitPoints, clamp %d)", m->merc, m->name, (double)hp, m->clampN);
}
static void rv_restore124(RvMerc *m) {
    DWORD v = sq_rd(m->s + 0x124, 4) ? *(DWORD*)(m->s + 0x124) : 0xffffffff;
    if (m->wrote124 && (v == 1 || (v == 2 && m->wrote2)) && god_writable(m->s + 0x124, 4)) *(DWORD*)(m->s + 0x124) = (DWORD)m->orig124;
    m->wrote124 = 0; m->wrote2 = 0;
}
/* the per-scene +0x124 table (CHANGE 9b) */
static int rv_orig_idx(const BYTE *s) { for (int i = 0; i < g_rvOrigN; i++) if (g_rvOrig[i].s == s) return i; return -1; }
static void rv_orig_note(RvMerc *m) {                 /* call after wrote124 / wrote2 became 1 */
    int i = rv_orig_idx(m->s);
    if (i < 0) {
        if (g_rvOrigN >= RV_MAXM) return;
        i = g_rvOrigN++; g_rvOrig[i].s = m->s; g_rvOrig[i].merc = m->merc; g_rvOrig[i].orig = m->orig124; g_rvOrig[i].had2 = 0;
    }
    if (m->wrote2) g_rvOrig[i].had2 = 1;
}
static int rv_listed_script(const BYTE *s) {          /* s is in DD's merc list now, or is the buddy's script */
    int nl = (int)rd32((void*)RV_MERCS); if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (int i = 0; i < nl; i++) if ((const BYTE*)rd32((void*)(RV_MERCS + 4 + 4 * i)) == s) return 1;
    BYTE *gm = (BYTE*)rd32((void*)0xdd265c), *bb = (BYTE*)rd32(gm + 0x4cf0);
    return bb && sq_rd(bb, 0x780) && (const BYTE*)rd32(bb + 0x77c) == s;
}
/* a reload while we are not live: put DD's own +0x124 back where the checkpoint brought ours back */
static void rv_orig_fix_all(const char *why) {
    for (int i = 0; i < g_rvOrigN; i++) {
        BYTE *s = g_rvOrig[i].s;
        if (!rv_listed_script(s) || !sq_rd(s, 0x740) || rd32(s) != RV_SCRIPT_VT || sq_merc(s) != g_rvOrig[i].merc) continue;
        DWORD v = rd32(s + 0x124);
        if (v == (DWORD)g_rvOrig[i].orig || !(v == 1 || (v == 2 && g_rvOrig[i].had2)) || !god_writable(s + 0x124, 4)) continue;
        *(DWORD*)(s + 0x124) = (DWORD)g_rvOrig[i].orig;
        rv_log("merc=%d: +0x124 = %lu came back with the checkpoint (saved from our live write; load 0x5bf4f3) - DD's own %d restored (%s)",
               g_rvOrig[i].merc, v, g_rvOrig[i].orig, why);
    }
}
/* CHANGE 1b: bit 0x4000 on the merc's OWN mask object that no live record of ours set: left by a record that was
   forgotten (player change, list drop). godmode.inc sets 0x4000 only on the player's object; rv_mask_check refuses a
   merc whose object is the player's or shared. Cleared only once revive has been live this session (else not ours). */
static void rv_stale_mask(RvMerc *m, const char *where) {
    BYTE *o = m->maskObj;
    if (m->maskSet || !m->maskOk || !o || (BYTE*)rd32(m->body + 0x54) != o || !sq_rd(o + 0x3a, 2)) return;
    WORD w = *(WORD*)(o + 0x3a);
    if (!(w & RV_MASK)) return;
    int clr = g_rvEverLive && god_writable(o + 0x3a, 2);
    if (clr) *(WORD*)(o + 0x3a) &= (WORD)~RV_MASK;
    if (m->staleMaskN < 3 && (clr || !m->staleMaskN)) {
        m->staleMaskN++;
        rv_log("merc=%d '%s': mask bit 0x4000 set on his own mask object %p (word %04x, %s) with no record of ours holding it - %s", m->merc, m->name, o, w, where,
               clr ? "cleared (left by a forgotten record)" : "left (revive has not been live this session: not ours)");
    }
}
/* give back every write on one merc (only while the record still names a live soldier) */
static void rv_giveback(RvMerc *m, int T, const char *why) {
    if (!m->maskSet && !m->hold && !m->wrote124 && !m->wrote2) return;
    if (!rv_still(m)) { m->maskSet = m->hold = m->wrote124 = m->wrote2 = 0; return; }
    int had = m->maskSet | (m->hold << 1) | ((m->wrote124 | m->wrote2) << 2), parked = 0;
    rv_mask(m, 0);
    if (m->st == RS_DEAD) {                           /* CHANGE 3: never let a dead merc's DND tail run (HP 0.75, life 1) */
        BYTE *t = rv_task(m->s);
        /* pushed, not just current: while his dying task is current DND sits underneath with +0x64c = 1 */
        /* DEAD: park whenever the DND task object is still valid - ZBecomeRagdoll Start clears +0x64c (0x67727b), so
           "pushed" goes false exactly when the dying task ragdolls him (review 13 Oct); the hold does nothing to a corpse */
        if (t && (m->st == RS_DEAD || rv_dnd_pushed(m->s, m->body)) && god_writable(t + 0x14, 4)) { *(int*)(t + 0x14) = T + RV_PARK; parked = 1; }
        m->hold = 0;
    } else rv_release_hold(m, T);
    rv_restore124(m);
    rv_log("merc=%d '%s': writes given back (%s; mask %d hold %d +0x124 %d)%s", m->merc, m->name, why, had & 1, (had >> 1) & 1, (had >> 2) & 1,
           parked ? " - DEAD: his DND hold is parked, not released" : "");
}
static void rv_giveback_all(const char *why) {
    int T = rv_now();
    for (int i = 0; i < g_rvn; i++) rv_giveback(&g_rvm[i], T, why);
    if (g_rvPfix.P && sq_rd(g_rvPfix.P, 0x2e00) && *(DWORD*)g_rvPfix.P == CL_PLAYER_VT && god_writable(g_rvPfix.P + 0x998, 8) && god_writable(g_rvPfix.P + 0xd34, 4)) {
        BYTE *Q = g_rvPfix.P;                         /* a fault inside the action create: put the player fields back */
        *(BYTE**)(Q + 0xd34) = g_rvPfix.d34; *(BYTE**)(Q + 0x998) = g_rvPfix.c998; *(BYTE**)(Q + 0x99c) = g_rvPfix.c99c;
        anp_log("revive: player P+0xd34 / +0x998 / +0x99c restored after a fault in the heal create");
    }
    g_rvPfix.P = 0;
    BYTE *P = g_rv.P;
    if (P && g_rv.offerBody && sq_rd(P, 0x2e00) && *(DWORD*)P == CL_PLAYER_VT && rd32(P + 0xd34) == (DWORD)g_rv.offerBody && god_writable(P + 0xd34, 4)) *(DWORD*)(P + 0xd34) = 0;
    g_rv.offerBody = 0; g_rv.promptUp = 0;
}
static void rv_setstate(RvMerc *m, int st, int T, const char *why) {
    float hp = -1, mx = -1; rv_hp(m->body, &hp, &mx);
    BYTE *t = rv_task(m->s);
    rv_log("merc=%d '%s'%s %s -> %s (%s) hp=%.1f/%.1f life=%d task+14-now=%d deadline-now=%.1fs +0x513=%d +0x124=%ld diff=%ld scene=%s",
           m->merc, m->name, m->buddy ? " (buddy)" : "", RS_NAME[m->st], RS_NAME[st], why, (double)hp, (double)mx, rd8(m->body + 0x576),
           t ? *(int*)(t + 0x14) - T : 0, m->deadline ? (m->deadline - T) / 1024.0f : 0.0f, rd8(m->s + 0x513), (long)rd32(m->s + 0x124), god_difficulty(), g_rv.scene);
    m->st = st; m->stT = T;
}

/* ---------- per level: pre-flight (CHANGE 6), config / merc census (CHANGE 9) ---------- */
static const char *const RV_DND_CLIPS[] = {"/Damage/Down_Not_Dead/Down_Not_Dead_Get_Down", "/Damage/Down_Not_Dead/Down_Not_Dead",
                                           "/Damage/Down_Not_Dead/Down_Not_Dead_Get_Up"};
static int rv_clip_frames(BYTE *c) { return sq_rd(c, 0x68) ? (int)*(short*)(c + 2) : -1; }
/* CHANGE 6b: 0x59d550 advances kl2's anim RNG ([[0xdd2640]+0xb30] = x * 0x10dcd + 1, 0x59d553-0x59d56a), and 0x4c05c0
   calls it too; the dword is saved before and put back after each lookup, so even dry leaves no trace */
static DWORD *rv_rng(void) { BYTE *g = (BYTE*)rd32((void*)RV_CLOCK); return (g && god_writable(g + 0xb30, 4)) ? (DWORD*)(g + 0xb30) : 0; }
static int rv_merc_clips(RvMerc *m) {                /* the merc's DB resolves DD's DND clips: 1 ok, 0 missing */
    DWORD *rng = rv_rng();
    if (!rng) { rv_log("merc=%d '%s': anim RNG [[0xdd2640]+0xb30] not writable - clip check skipped, not managed", m->merc, m->name); return 0; }
    for (unsigned i = 0; i < sizeof RV_DND_CLIPS / sizeof RV_DND_CLIPS[0]; i++) {
        WORD id = 0xFFFF;
        rv_call2("name id 0x426890", RV_F_NAMEID, m->body, (DWORD)&id, (DWORD)RV_DND_CLIPS[i]);
        if (g_rvDead) return 0;
        BYTE *c = 0;
        if ((short)id >= 0) {                         /* 0x426890 leaves 0xffff when the name is unknown; 0x5c2f60 refuses id < 0 */
            DWORD sv = *rng;
            c = (BYTE*)rv_call1("variant 0x59d550", RV_F_VARIANT, m->body, id);
            *rng = sv;
            if (g_rvDead) return 0;
        }
        if (rv_clip_frames(c) < 1) { rv_log("merc=%d '%s': DB lacks %s (id %d, clip %p) - not managed", m->merc, m->name, RV_DND_CLIPS[i], (int)(short)id, c); return 0; }
    }
    return 1;
}
static void rv_preflight(BYTE *P) {
    BYTE *c8 = (BYTE*)rd32(P + 0x998), *cc = (BYTE*)rd32(P + 0x99c);
    int f8 = rv_clip_frames(c8), fc = rv_clip_frames(cc);
    g_rv.dmClip = 0;
    DWORD *rng = rv_rng(), sv = rng ? *rng : 0;
    BYTE *dm = rng ? (BYTE*)rv_call1("player clip 0x4c05c0", RV_F_PCLIP, P, (DWORD)"/Special_moves/Heal_wounded") : 0;
    if (rng) *rng = sv;
    if (g_rvDead) return;
    int fd = rv_clip_frames(dm);
    if (fd >= 2) g_rv.dmClip = dm;
    const char *why = 0;
    if (f8 < 2 || fc < 2) why = "player heal clips P+0x998/+0x99c missing or < 2 frames (Start reads frames-1)";
    g_rv.levelOk = why ? 0 : 1;
    rv_log("pre-flight %s: P+0x998 %p (%d fr) P+0x99c %p (%d fr) Heal_wounded %p (%d fr)%s -> %s%s", g_rv.scene, c8, f8, cc, fc, dm, fd,
           g_rvc.clipDm && fd < 2 ? " [clip=dm falls back to dd]" : "", why ? "REFUSED (live acts as dry in this level): " : "ok", why ? why : "");
}
static void rv_level_log(BYTE *P) {
    BYTE *cfg = (BYTE*)rd32((void*)RV_CFG);
    if (sq_rd(cfg + 0x40, 0x24))
        rv_log("level %s: DND cfg [0x168d7c0]=%p +40 %.2f +44 %.2f (buddy down s) +4c %.2f +50 %.2f (merc down s) +54 %.2f +58 %.2f (cooldowns) +5c %.1f (attacker dist) +60 %d (buddy HP-1 rule) | diff=%ld god=%ld gs=%lu P=%p d30=%08lx",
               g_rv.scene, cfg, (double)*(float*)(cfg + 0x40), (double)*(float*)(cfg + 0x44), (double)*(float*)(cfg + 0x4c), (double)*(float*)(cfg + 0x50),
               (double)*(float*)(cfg + 0x54), (double)*(float*)(cfg + 0x58), (double)*(float*)(cfg + 0x5c), cfg[0x60], god_difficulty(),
               (long)rd32((void*)GOD_VAR), rd32((void*)RV_GS), P, rd32(P + 0xd30));
    else rv_log("level %s: DND cfg [0x168d7c0] unreadable (%p)", g_rv.scene, cfg);
}
/* mask object [body+0x54] must belong to this body alone (not the player's, no other soldier's) */
static int rv_mask_check(RvMerc *m, BYTE *P) {
    BYTE *o = (BYTE*)rd32(m->body + 0x54);
    if (!sq_rd(o, 0x44)) { rv_log("merc=%d '%s': mask object %p unreadable - no mask (hits while down are not blocked)", m->merc, m->name, o); return 0; }
    if (P && o == (BYTE*)rd32(P + 0x54)) { rv_log("merc=%d '%s': mask object %p is the PLAYER's - no mask", m->merc, m->name, o); return 0; }
    static SqSol sol[256]; int n = sq_soldiers(sol, 256);
    for (int i = 0; i < n; i++)
        if (sol[i].body != m->body && (BYTE*)rd32(sol[i].body + 0x54) == o) {
            char nm[40]; sq_name(sol[i].body, nm, sizeof nm);
            rv_log("merc=%d '%s': mask object %p is shared with soldier '%s' (merc %d) - no mask", m->merc, m->name, o, nm, sol[i].merc); return 0;
        }
    m->maskObj = o;
    return 1;
}
static void rv_merc_line(RvMerc *m, const char *why) {
    float hp = -1, mx = -1; rv_hp(m->body, &hp, &mx);
    BYTE *t = rv_task(m->s);
    rv_log("merc=%d '%s'%s (%s): s=%p vt=%08lx body=%p rel=%d life=%d hp=%.1f/%.1f +6d8 type=%d +124=%ld +5cb=%d +512=%d +513=%d +64c=%d +888=%d "
           "dnd task=%p%s cur=%08lx mask obj=%p word=%04x (%s) clips=%d state=%s",
           m->merc, m->name, m->buddy ? " (buddy)" : "", why, m->s, rd32(m->s), m->body, sq_rel(m->body), rd8(m->body + 0x576), (double)hp, (double)mx,
           rv_gate_type(m->s), (long)rd32(m->s + 0x124), rd8(m->body + 0x5cb), rd8(m->s + 0x512), rd8(m->s + 0x513), rd8(m->body + 0x64c), rd8(m->body + 0x888),
           t, t ? "" : " (INVALID)", rd32(m->s + 0x74), m->maskObj, sq_rd((BYTE*)rd32(m->body + 0x54) + 0x3a, 2) ? *(WORD*)((BYTE*)rd32(m->body + 0x54) + 0x3a) : 0xffff,
           m->maskOk ? "own" : "NOT usable", m->clipsOk, RS_NAME[m->st]);
}

/* ---------- merc list ---------- */
/* buddy=dm needs DD's cfg+0x60 rule: a refused slot 51 on the buddy then sets HP 1 (0x84797e-0x84799a); with
   cfg+0x60 == 0 the refusal falls through to his death (0x8479a5), so a downed Lynch could be killed by any hit */
static int rv_buddy_dm_ok(void) {
    BYTE *cfg = (BYTE*)rd32((void*)RV_CFG);
    return sq_rd(cfg + 0x60, 1) && cfg[0x60] != 0;
}
static RvMerc *rv_add(BYTE *s, BYTE *body, int buddy, BYTE *P, int T, int live) {
    RvMerc *m = rv_find_body(body);
    if (m) { m->used = 1; if (m->s != s) m->s = s; return m; }
    if (g_rvn >= RV_MAXM) return 0;
    m = &g_rvm[g_rvn++]; memset(m, 0, sizeof *m);
    m->s = s; m->body = body; m->buddy = buddy; m->merc = sq_merc(s); m->used = 1; m->st = RS_NORMAL; m->stT = T;
    m->clipsOk = -1; m->orig124 = (int)rd32(s + 0x124); m->lastLife = rd8(body + 0x576); m->lastDnd = rv_dnd_current(s, body);
    float mx; rv_hp(body, &m->lastHp, &mx);
    sq_name(body, m->name, sizeof m->name);
    m->maskOk = rv_mask_check(m, P);
    int oi = rv_orig_idx(s);                          /* CHANGE 9b: DD's own +0x124 from before our first write this scene */
    if (oi >= 0 && g_rvOrig[oi].merc == m->merc) {
        DWORD v = rd32(s + 0x124);
        m->orig124 = g_rvOrig[oi].orig;
        if (live && v != (DWORD)m->orig124 && (v == 1 || (v == 2 && g_rvOrig[oi].had2))) {
            m->wrote124 = 1; m->wrote2 = v == 2;
            rv_log("merc=%d '%s': +0x124 = %lu is ours (back with a checkpoint, 0x5bf4f3) - DD's own %d remembered", m->merc, m->name, v, m->orig124);
        }
    }
    rv_stale_mask(m, "new record");                   /* CHANGE 1b */
    int rel = sq_rel(body);
    if (rel != 0 && rel != 2) { rv_log("merc=%d '%s': relation %d is not friendly - not managed", m->merc, m->name, rel); m->st = RS_EXCL; }
    else if (buddy && !g_rvc.buddyDm) m->st = RS_EXCL;   /* buddy=dd: Lynch stays stock (re-checked when the config changes) */
    else if (buddy && !rv_buddy_dm_ok()) {            /* CHANGE 8 */
        BYTE *cfg = (BYTE*)rd32((void*)RV_CFG);
        rv_log("merc=%d '%s' (buddy): buddy=dm REFUSED - DND cfg [0x168d7c0]=%p +0x60 = %d (no HP-1 rule: a hit on him while down would kill him at 0x8479a5); he stays stock DD",
               m->merc, m->name, cfg, sq_rd(cfg + 0x60, 1) ? cfg[0x60] : -1);
        m->st = RS_EXCL;
    }
    else if (rv_excluded(g_rv.scene, m->merc)) {      /* CHANGE 5: DM NotHealable (default M14 Merc_01) */
        rv_log("merc=%d '%s': excluded in %s (exclude=, DM eHM_NotHealable) - no Force write, no floor, left to DD", m->merc, m->name, g_rv.scene);
        m->st = RS_EXCL;
    }
    return m;
}
static void rv_collect(BYTE *P, int T, int live) {
    for (int i = 0; i < g_rvn; i++) g_rvm[i].used = 0;
    BYTE *gm = (BYTE*)rd32((void*)0xdd265c), *bb = (BYTE*)rd32(gm + 0x4cf0);
    int nl = (int)rd32((void*)RV_MERCS); if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (int i = 0; i < nl; i++) {
        BYTE *s = (BYTE*)rd32((void*)(RV_MERCS + 4 + 4 * i)), *b = s ? sq_merc_body(s) : 0;
        if (b) rv_add(s, b, b == bb, P, T, live);
    }
    if (bb && sq_rd(bb, 0x780)) {                     /* the buddy, in case he is not listed */
        BYTE *s = (BYTE*)rd32(bb + 0x77c);
        if (sq_rd(s, 0x740) && rd32(s) == RV_SCRIPT_VT && rd32(s + 0x40) == (DWORD)bb) rv_add(s, bb, 1, P, T, live);
    }
    for (int i = 0; i < g_rvn; ) {                    /* gone: give back while he still validates (rv_still), then forget */
        if (!g_rvm[i].used) {
            RvMerc *m = &g_rvm[i];
            rv_giveback(m, T, "left the merc list");  /* CHANGE 1: no write when the objects no longer validate */
            if (m->st != RS_EXCL) rv_log("merc=%d '%s': left the merc list (state %s) - forgotten", m->merc, m->name, RS_NAME[m->st]);
            g_rvm[i] = g_rvm[--g_rvn];
        } else i++;
    }
}

/* ---------- engine actions (live) ---------- */
static int rv_try_down(RvMerc *m, const char *why) {
    DWORD r = rv_call2("TryDownNotDead 0x688190", RV_F_TRYDOWN, m->s, 0, 1) & 0xff;
    if (g_rvDead) return 0;
    m->tries++;
    if (m->tries <= 3 || r) rv_log("merc=%d '%s': 0x688190(s, NULL, force 1) = %lu (%s, try %d)", m->merc, m->name, r, why, m->tries);
    return (int)r;
}
static int rv_can_down(RvMerc *m) {                  /* 0x70f330 on the DND task (room test, read only): 1/0, -1 no task */
    BYTE *t = rv_task(m->s);
    if (!t) return -1;
    int r = (int)(rv_call0("DND room test 0x70f330", RV_F_CANDOWN, t) & 0xff);
    return g_rvDead ? -1 : r;
}
/* CHANGE 7: the hard gates of 0x688190 with force 1, in the engine's order; -1 = all pass (it will push the DND task) */
static int rv_hard_gate(RvMerc *m) {
    if (rv_gate_type(m->s) == 6) return RG_TYPE6;
    if (rv_vf(m->body, 0x654) == RV_F_ISDOWN && rd8(m->body + 0x64c)) return RG_ISDOWN;   /* other vt: left to the call */
    DWORD ds = rd32((BYTE*)rd32(m->s + 0x4b4) + 8);
    if (ds != 0 && ds != 4) return RG_DYING;
    if (!rv_task(m->s)) return RG_NOTASK;
    if (rd32(m->body + 0x774)) return RG_VEHICLE;
    int room = rv_can_down(m);
    if (g_rvDead) return -1;
    return room < 0 ? RG_NOTASK : !room ? RG_ROOM : -1;
}
/* a hard refusal: no mask, no PENDING; floor retried after 10 s, doubling up to 160 s; one line per reason per record */
static void rv_refuse(RvMerc *m, int T, int g, const char *src) {
    m->gateBackoff = m->gateBackoff ? (m->gateBackoff >= 81920 ? 163840 : m->gateBackoff * 2) : 10240;
    m->coolT = T + m->gateBackoff;
    if (!(m->gateLogged & (1 << g))) {
        m->gateLogged |= 1 << g;
        float hp = -1, mx = -1; rv_hp(m->body, &hp, &mx);
        rv_log("merc=%d '%s': %s: down refused - %s (hp %.1f/%.1f, +6d8 type %d, +0x64c %d, dying state %ld, vehicle %08lx) - no mask, no PENDING; "
               "retried in %d s, doubling up to 160 s (this reason is logged once)", m->merc, m->name, src, RV_GATE[g], (double)hp, (double)mx,
               rv_gate_type(m->s), rd8(m->body + 0x64c), (long)rd32((BYTE*)rd32(m->s + 0x4b4) + 8), rd32(m->body + 0x774), m->gateBackoff / 1024);
    }
}
/* FIX 2: gates that leave a merc to WSTAND (alive, standing, wounded). Not: already down (+0x64c: his DND task is
   pushed, the DND path takes him) or dying (the dying task runs: he is dead already) */
static int rv_gate_wstand(int g) { return g != RG_ISDOWN && g != RG_DYING && g != RG_VEHICLE; }   /* review: Die on a seated merc is unproven */
static void rv_enter_wstand(RvMerc *m, int T, const char *why) {
    int full = 1024 * g_rvc.bleed[god_difficulty() & 3];
    int kept = m->keepDl;                             /* review: a kept deadline stays kept even if it passed during PENDING */
    if (!kept) m->deadline = T + full;
    else if (m->deadline < T + 1024) m->deadline = T + 1024;
    m->keepDl = 1;                                    /* a down from WSTAND keeps this deadline */
    m->wsRetryT = T; m->wsTries = 0; m->clampN = 0; m->healSeen = 0; m->healOnSeen = 0; m->deferLogged = 0; m->bledDry = 0; m->regenLogged = 0;
    rv_mask(m, 1);
    float hp = -1, mx = -1; rv_hp(m->body, &hp, &mx);
    m->baseHp = hp < 1.0f ? 1.0f : hp;                /* "HP back to max" exit only after a real rise from here */
    rv_noregen(m, T);
    char w[240]; _snprintf(w, sizeof w, "%s - wounded standing: mask, HP >= 1, no regen, heal prompt, DND retried every 2 s%s", why,
                           kept ? "; bleed deadline kept" : ""); w[sizeof w - 1] = 0;
    rv_setstate(m, RS_WSTAND, T, w);
    if (!g_rvDead) rv_hp_floor1(m, hp);
}
/* the floor (or 'down' command), live: gates first, the mask only once 0x688190 accepted.
   1 = PENDING, 2 = WSTAND (refused but kept alive), 0 = refused (no mask) */
static int rv_floor_down(RvMerc *m, int T, const char *src) {
    int g = rv_hard_gate(m);
    if (g_rvDead) return 0;
    if (g < 0) {
        m->tries = 0; m->tryOk = rv_try_down(m, src); m->lastTryT = T;
        if (g_rvDead) return 0;
        if (m->tryOk) {
            m->keepDl = 0;                            /* a fresh down: a fresh bleed time */
            rv_mask(m, 1);
            rv_setstate(m, RS_PENDING, T, src);
            return 1;
        }
        g = RG_REFUSED;
    }
    if (rv_gate_wstand(g) && m->maskOk && rd8(m->body + 0x576) == 1) {
        char w[200]; _snprintf(w, sizeof w, "%s: down refused - %s", src, RV_GATE[g]); w[sizeof w - 1] = 0;
        m->keepDl = 0;
        rv_enter_wstand(m, T, w);
        return g_rvDead ? 0 : 2;
    }
    rv_refuse(m, T, g, src);
    return 0;
}
/* CHANGE 10: a merc who went down again within 5 s of a reset without heal keeps what was left of his bleed time */
static void rv_left_down(RvMerc *m, int T) { m->leftT = T ? T : 1; m->leftBleed = m->deadline - T > 0 ? m->deadline - T : 0; }
static void rv_enter_down(RvMerc *m, int T, float hp, int live, const char *why) {
    int full = 1024 * g_rvc.bleed[god_difficulty() & 3], dl = full, kept = 0;
    if (m->keepDl) { dl = m->deadline - T; if (dl < 1024) dl = 1024; kept = 2; }   /* FIX 2: from WSTAND (or PENDING from WSTAND) */
    else if (m->leftT && T - m->leftT < 5120 && m->leftBleed < full) { dl = m->leftBleed < 1024 ? 1024 : m->leftBleed; kept = 1; }
    m->leftT = 0; m->keepDl = 0;
    m->deadline = T + dl; m->baseHp = hp; m->healSeen = 0; m->healOnSeen = 0; m->deferLogged = 0; m->tries = 0; m->gateBackoff = 0; m->bledDry = 0;
    m->suspT = 0; m->suspLogged = 0; m->hpRiseLogged = 0; m->regenLogged = 0;
    if (live) { rv_mask(m, 1); rv_hold(m, T); rv_noregen(m, T); }
    char w[220]; _snprintf(w, sizeof w, "%s%s", why, kept == 2 ? "; the WSTAND bleed deadline is kept" :
                           kept ? "; down again within 5 s of a native end: the remaining bleed time is kept" : ""); w[sizeof w - 1] = 0;
    rv_setstate(m, RS_DOWN, T, w);
}
/* FIX 1: we leave DOWN / GETUP for NORMAL: if his DND task is still pushed, no native re-entry for 10 s */
static void rv_note_left(RvMerc *m, int T) {
    if (rv_dnd_pushed(m->s, m->body)) { m->noReentUntil = T + RV_NOREENT; m->reentLogged = 0; }
}
/* CHANGE 8: buddy=dm, DOWN: +0x124 = 2 (Prevent) so slot 51 refuses him (0x70e1fa) and DD's cfg+0x60 HP-1 rule applies */
static void rv_buddy_prevent(RvMerc *m) {
    DWORD v = rd32(m->s + 0x124);
    if (v == 2 || !god_writable(m->s + 0x124, 4)) return;
    if (!m->wrote124) { m->orig124 = (int)v; m->wrote124 = 1; }
    *(DWORD*)(m->s + 0x124) = 2;
    if (!m->wrote2) { m->wrote2 = 1; rv_orig_note(m); }
}
static void rv_sethp_max(RvMerc *m) {
    float hp, mx; if (!rv_hp(m->body, &hp, &mx) || mx <= 0) return;
    DWORD f = rv_vf(m->body, 0x670);
    if (f != RV_F_SETHP) { rv_log("merc=%d '%s': body vt+0x670 = %08lx (not 0x792bc0) - HP left at %.1f", m->merc, m->name, f, (double)hp); return; }
    rv_call1("SetHitPoints 0x792bc0", RV_F_SETHP, m->body, fbits(mx));
}
static void rv_force_fail(RvMerc *m) {
    if (rd8((void*)(RV_FAILOBJ + 0x20)) || rd8((void*)(RV_FAILOBJ + 0x21))) { rv_log("merc=%d '%s': a fail window is already open - no extra fail", m->merc, m->name); return; }
    rv_call2("fail text 0x7864f0", RV_F_FAILTXT, (void*)RV_FAILOBJ, RV_KEY_MF01, 0);
    if (g_rvDead) return;
    rv_call1("mission failed 0x8edc40", RV_F_FAIL, (void*)RV_FAILOBJ, 0);
    if (!g_rvDead) rv_log("merc=%d '%s': buddy bled out with +0x513 = 0 - MF_01_MercDead forced (0x7864f0 + 0x8edc40)", m->merc, m->name);
}
static void rv_bleed_out(RvMerc *m, int T) {
    float pos[3], dir[3] = {0, 0, 1};
    static DWORD info[0x14];                          /* 0x50 bytes; 0x4bc0e0 copies +0..+0x14 */
    memset(info, 0, sizeof info); info[4] = 2;        /* +0x10 = 2 as the hit handler writes (0x8479e2); +0xc killer 0 */
    if (!fw_body_pos(m->body, pos)) { pos[0] = pos[1] = pos[2] = 0; }
    rv_mask(m, 0);                                    /* the dying task's own hits stay stock; the hold stays (no get-up tail) */
    DWORD a[4] = {(DWORD)pos, (DWORD)dir, fbits(0.0f), (DWORD)info};
    rv_call("Die 0x5063e0", RV_F_DIE, m->s, 4, a);
    if (g_rvDead) return;
    m->dieT = T; m->deathT = 0; m->killT = 0; m->failDone = 0; m->undeadN = 0; m->healEndT = 0; m->saw0 = 0;
    rv_setstate(m, RS_DEAD, T, "bled out: Die (slot 52)");
}
/* the heal: P+0xd34 = body, create (vt+0x384) and start (vt+0x370) action 0x12, P+0xd34 back at once (CHANGE 1) */
static void rv_start_heal(BYTE *P, RvMerc *m, int T, const char *src) {
    /* CHANGE 2: never heal a dead / not-down merc. FIX 2: a WSTAND merc (standing, alive) is healable: the heal action
       has no DND test (ctor 0x907300, Start 0x6244b0, Update 0x4c7850, apply 0x7e75b0, End 0x4ea150) */
    if (rd8(m->body + 0x576) != 1 || (m->st != RS_WSTAND && !rv_dnd_current(m->s, m->body))) {
        rv_log("%s heal merc=%d: refused - life %d, DND current %d, state %s", src, m->merc, rd8(m->body + 0x576), rv_dnd_current(m->s, m->body), RS_NAME[m->st]); return;
    }
    if (cl_disp_cur(P) != 0) { rv_log("%s heal merc=%d: the player already runs an action - skipped", src, m->merc); return; }
    BYTE *s8 = (BYTE*)rd32(P + 0x998), *sc = (BYTE*)rd32(P + 0x99c), *d34 = (BYTE*)rd32(P + 0xd34);
    int dm = g_rvc.clipDm && g_rv.dmClip;
    if (!god_writable(P + 0x998, 8) || !god_writable(P + 0xd34, 4)) { rv_log("%s heal: player fields not writable", src); return; }
    g_rvPfix.P = P; g_rvPfix.d34 = d34; g_rvPfix.c998 = s8; g_rvPfix.c99c = sc;   /* restored by the cleanup if create faults */
    if (dm) { *(BYTE**)(P + 0x998) = g_rv.dmClip; *(BYTE**)(P + 0x99c) = g_rv.dmClip; }
    *(BYTE**)(P + 0xd34) = m->body;
    BYTE *act = (BYTE*)rv_call1("create action 0x839740", RV_F_CREATE, P, 0x12);
    *(BYTE**)(P + 0xd34) = d34; *(BYTE**)(P + 0x998) = s8; *(BYTE**)(P + 0x99c) = sc;   /* given back at once */
    g_rvPfix.P = 0;
    if (g_rvDead) return;
    if (!sq_rd(act, 0x24) || *(DWORD*)act != RV_HEAL_VT || *(BYTE**)(act + 8) != P || *(BYTE**)(act + 0xc) != m->body) {
        rv_log("%s heal merc=%d: create returned %p (vt %08lx owner %08lx target %08lx) - not started", src, m->merc, act, rd32(act), rd32(act + 8), rd32(act + 0xc));
        return;
    }
    int instant = act[0x18];
    if (instant) m->healSeen = 1;                     /* healed in the ctor already (DD's |dy| > 50 cm rule) */
    rv_call1("start action 0x542c00", RV_F_START, P, (DWORD)act);
    if (g_rvDead) return;
    BYTE *cur = cl_disp_cur(P);
    float t1c = sq_rd(act, 0x24) ? *(float*)(act + 0x1c) : 0, t20 = sq_rd(act, 0x24) ? *(float*)(act + 0x20) : 0;
    const char *how = "dd 0.44 s";
    if (cur == act && g_rvc.healDm && !act[0x18]) {
        float want = (float)(T + 0x800) / 1024.0f;        /* DM: HP = max at 2.0 s */
        if (t20 * 1024.0f > (float)(T + 0x800) && god_writable(act + 0x1c, 4)) { *(float*)(act + 0x1c) = want; how = "dm 2.0 s"; }
        else how = "dd 0.44 s (the clip ends before 2.0 s)";
    }
    g_rv.healStarts++;
    rv_log("%s heal merc=%d '%s': action %p clip %p (%s, %d fr) %s; +0x1c %.3f -> %.3f s, +0x20 %.3f s, now %.3f s, heal %s, body+0x888=%d",
           src, m->merc, m->name, act, rd32(act + 0x10), dm ? "DM Heal_wounded" : "DD", rv_clip_frames((BYTE*)rd32(act + 0x10)),
           cur == act ? "running" : instant ? "INSTANT (|dy| > 50 cm: healed in the ctor)" : "NOT current after start", (double)t1c,
           (double)(sq_rd(act, 0x24) ? *(float*)(act + 0x1c) : 0), (double)t20, (double)(T / 1024.0f), how, rd8(m->body + 0x888));
}

/* ---------- per merc tick ---------- */
static void rv_to_dead(RvMerc *m, int T, const char *why) {
    rv_mask(m, 0); m->hold = 0;                       /* DEAD re-holds while his DND task is still pushed (CHANGE 3) */
    m->dieT = T; m->deathT = T ? T : 1; m->killT = 0; m->failDone = 0; m->undeadN = 0; m->healEndT = 0; m->saw0 = 0;
    rv_setstate(m, RS_DEAD, T, why);
}
static void rv_merc_tick(RvMerc *m, BYTE *P, int T, int live) {
    float hp = -1, mx = -1; int okHp = rv_hp(m->body, &hp, &mx);
    int life = rd8(m->body + 0x576), dnd = rv_dnd_current(m->s, m->body);
    BYTE *act = rv_heal_act(P); int healOn = act && *(BYTE**)(act + 0xc) == m->body;
    if (m->st == RS_EXCL) {                          /* buddy=dd, excluded or hostile: still logged in dry/live for native events */
        if (dnd != m->lastDnd) rv_log("merc=%d '%s' (not managed): native DND %s, hp=%.1f/%.1f life=%d", m->merc, m->name, dnd ? "started" : "ended", (double)hp, (double)mx, life);
        if (life != m->lastLife) rv_log("merc=%d '%s' (not managed): life %d -> %d", m->merc, m->name, m->lastLife, life);
        m->lastDnd = dnd; m->lastLife = life; return;
    }
    if (!live && (m->st == RS_PENDING || m->st == RS_WSTAND)) {   /* left live (writes already given back) */
        if (m->maskSet) rv_giveback(m, T, "not live");     /* never leave our mask behind */
        m->st = RS_NORMAL; m->keepDl = 0;
    }
    if (m->clipsOk < 0 && g_rv.preflight) {
        m->clipsOk = rv_merc_clips(m); if (g_rvDead) return;
        if (!m->clipsOk) { rv_giveback(m, T, "DB lacks the DND clips"); m->st = RS_EXCL; return; }
    }
    /* CHANGE 8: the buddy's Prevent (+0x124 = 2) lasts only while he is DOWN; back to our Force (1) otherwise */
    if (m->wrote2 && m->st != RS_DOWN && live && rd32(m->s + 0x124) == 2 && god_writable(m->s + 0x124, 4)) { *(DWORD*)(m->s + 0x124) = 1; m->wrote2 = 0; }
    /* CHANGE 5: stale +0x888 (set by the heal ctor, cleared by End) with no heal action on him */
    if (rd8(m->body + 0x888) && !healOn) {
        if (!m->staleT) m->staleT = T;
        else if (T - m->staleT > 1024) {
            if (live && god_writable(m->body + 0x888, 1)) { m->body[0x888] = 0; rv_log("merc=%d '%s': stale +0x888 cleared (no heal action on him for 1 s)", m->merc, m->name); }
            else if (!live) rv_log("merc=%d '%s': dry: +0x888 stale for 1 s - would clear", m->merc, m->name);
            m->staleT = 0;
        }
    } else m->staleT = 0;
    /* CHANGE 2: a merc whose life byte left 1 (dying 2 / dead 0) is never healed or held up as DOWN */
    if ((m->st == RS_DOWN || m->st == RS_GETUP || m->st == RS_WSTAND) && life != 1)
        rv_to_dead(m, T, m->st == RS_DOWN ? "life != 1 while DOWN (DoT / script kill) - mask cleared, no heal" :
                         m->st == RS_WSTAND ? "life != 1 while WSTAND (DoT / script kill) - mask cleared, no heal" : "life != 1 while GETUP - mask cleared");

    switch (m->st) {
    case RS_NORMAL: {
        rv_stale_mask(m, "NORMAL");                   /* CHANGE 1b */
        if (live && rd32(m->s + 0x124) != 2) {        /* (a) Force + not-downed-before, every frame */
            if (rd32(m->s + 0x124) != 1 && god_writable(m->s + 0x124, 4)) {
                if (!m->wrote124) { m->orig124 = (int)rd32(m->s + 0x124); m->wrote124 = 1; rv_orig_note(m); }
                *(DWORD*)(m->s + 0x124) = 1;
            }
            if (rd8(m->body + 0x5cb) && god_writable(m->body + 0x5cb, 1)) m->body[0x5cb] = 0;
        }
        if (rd32(m->s + 0x124) == 2) {                /* Prevent (a level's NotHealable / SquadModifier): native death */
            if (!m->lowLogged) { m->lowLogged = 1; rv_log("merc=%d '%s': +0x124 = 2 (Prevent / not healable) - left to DD", m->merc, m->name); }
            break;
        }
        if (dnd) {                                    /* a lethal hit went down natively (or a level script) */
            if (T < m->noReentUntil) {                /* FIX 1: we just let go of this very DND task - no flap */
                if (!m->reentLogged) {
                    m->reentLogged = 1;
                    rv_log("merc=%d '%s': native DND current, but we left DOWN/GETUP %.1f s ago with his DND task still pushed - not re-entered for %.1f s (DD's own DND runs)",
                           m->merc, m->name, (RV_NOREENT - (m->noReentUntil - T)) / 1024.0f, (m->noReentUntil - T) / 1024.0f);
                }
                break;
            }
            m->noReentUntil = 0;
            rv_enter_down(m, T, hp, live, live ? "native DND current" : "dry: native DND seen (would hold + bleed)");
            break;
        }
        if (okHp && life == 1 && mx > 0 && hp > 0 && hp <= g_rvc.floor * mx && T >= m->coolT && (live || !m->lowLogged)) {
            if (!live) {
                m->lowLogged = 1;
                int g = rv_hard_gate(m); if (g_rvDead) return;
                rv_log("merc=%d '%s': dry: hp %.1f/%.1f <= floor %.2f - %s%s%s (+6d8 type %d, +0x64c %d, dying task state %ld, vehicle %08lx, +0x124=%ld)",
                       m->merc, m->name, (double)hp, (double)mx, (double)g_rvc.floor, g < 0 ? "would down (0x688190(s, NULL, 1))" : "would be refused: ",
                       g < 0 ? "" : RV_GATE[g], g >= 0 && rv_gate_wstand(g) && m->maskOk ? " -> live: WSTAND" : "",
                       rv_gate_type(m->s), rd8(m->body + 0x64c), (long)rd32((BYTE*)rd32(m->s + 0x4b4) + 8), rd32(m->body + 0x774),
                       (long)rd32(m->s + 0x124));
                break;
            }
            rv_floor_down(m, T, "HP floor");          /* CHANGE 7: hard gates first, the mask only once accepted */
            if (g_rvDead) return;
        } else if (okHp && mx > 0 && hp > g_rvc.floor * mx) { m->lowLogged = 0; m->gateBackoff = 0; }
        if (m->lastLife == 1 && life != 1) rv_log("merc=%d '%s': DIED while %s (life %d, hp %.1f): a lethal hit DD would not down (force-0 gates: attacker distance cfg+0x5c, damage >= 1000, room, vehicle)",
                                                  m->merc, m->name, RS_NAME[m->st], life, (double)hp);
        break;
    }
    case RS_PENDING: {                                /* live only: 0x688190 accepted, waiting for the DND task */
        rv_mask(m, 1);
        if (m->keepDl) rv_noregen(m, T);              /* review: PENDING from a WSTAND retry - still no regen */
        if (dnd) { rv_enter_down(m, T, hp, 1, "DND current after the floor"); break; }
        if (life != 1) { rv_mask(m, 0); m->keepDl = 0; rv_setstate(m, RS_NORMAL, T, "died while pending"); break; }
        if (T - m->stT > g_rvc.pendMs * 1024 / 1000) {
            if (m->maskOk) {                          /* FIX 2; the next DND retry only after 10 s (no 5 s PENDING loop) */
                rv_enter_wstand(m, T, "PENDING: DD never started the DND task"); m->wsRetryT = T + 8192; break;
            }
            rv_mask(m, 0); rv_refuse(m, T, RG_NOSTART, "PENDING");
            rv_setstate(m, RS_NORMAL, T, "DD never started DND - mask cleared, floor backed off");
            break;
        }
        /* push again only when the first push got lost (+0x64c back to 0) and every gate still passes */
        if (T - m->lastTryT > 1536 && !rd8(m->body + 0x64c)) {
            m->lastTryT = T;
            int g = rv_hard_gate(m); if (g_rvDead) return;
            if (g >= 0) {
                if (rv_gate_wstand(g) && m->maskOk) {   /* FIX 2 */
                    char w[160]; _snprintf(w, sizeof w, "PENDING: a hard gate closed - %s", RV_GATE[g]); w[sizeof w - 1] = 0;
                    rv_enter_wstand(m, T, w); break;
                }
                rv_mask(m, 0); rv_refuse(m, T, g, "PENDING"); m->keepDl = 0;
                rv_setstate(m, RS_NORMAL, T, "a hard gate closed while pending - mask cleared"); break;
            }
            m->tryOk = rv_try_down(m, "retry"); if (g_rvDead) return;
        }
        break;
    }
    case RS_WSTAND: {                                 /* FIX 2: live only (left live -> NORMAL above) */
        if (dnd) { rv_enter_down(m, T, hp, 1, "DND current while WSTAND"); break; }
        rv_mask(m, 1); rv_noregen(m, T);
        if (okHp) { rv_hp_floor1(m, hp); if (g_rvDead) return; }
        if (healOn && act[0x18]) m->healSeen = 1;
        if (healOn) m->healOnSeen = 1;
        else if (m->healOnSeen) {
            m->healOnSeen = 0;
            if (okHp && mx > 0 && hp >= 0.99f * mx) m->healSeen = 1;
            else rv_log("merc=%d '%s': heal action ended without the heal (hp %.1f/%.1f) - stays WSTAND", m->merc, m->name, (double)hp, (double)mx);
        }
        if (m->healSeen) {
            rv_mask(m, 0); m->keepDl = 0; m->healSeen = 0; m->coolT = T + 2048;
            rv_setstate(m, RS_NORMAL, T, "healed by the player while standing: mask cleared (HP = max by the heal)");
            break;
        }
        if (okHp && mx > 0 && hp >= 0.99f * mx && hp > m->baseHp + 1.0f && !healOn && !rd8(m->body + 0x888)) {
            rv_mask(m, 0); m->keepDl = 0; m->coolT = T + 2048;
            rv_setstate(m, RS_NORMAL, T, "HP back to max without our heal (script / checkpoint) - mask cleared");
            break;
        }
        if (g_rvc.godpause && rd32((void*)GOD_VAR)) { m->deadline += T - g_rv.lastT; }
        if (T >= m->deadline) {
            if (healOn || rd8(m->body + 0x888)) {
                if (!m->deferLogged) { m->deferLogged = 1; rv_log("merc=%d '%s': bleed-out deferred - a heal targets him (+0x888=%d, action %p)", m->merc, m->name, rd8(m->body + 0x888), act); }
                break;
            }
            m->keepDl = 0;
            rv_bleed_out(m, T);
            break;
        }
        if (T - m->wsRetryT >= RV_WS_RETRY && !healOn && !rd8(m->body + 0x888)) {   /* DND retry: he may have moved off the wall */
            m->wsRetryT = T;
            int g = rv_hard_gate(m); if (g_rvDead) return;
            if (g < 0) {
                m->wsTries++;
                int r = rv_try_down(m, "WSTAND retry"); if (g_rvDead) return;
                if (r) { m->tryOk = 1; m->lastTryT = T; rv_setstate(m, RS_PENDING, T, "WSTAND retry accepted (bleed deadline kept)"); break; }
            } else if (!rv_gate_wstand(g)) {
                if (!(m->gateLogged & (1 << g))) { m->gateLogged |= 1 << g; rv_log("merc=%d '%s': WSTAND retry: %s", m->merc, m->name, RV_GATE[g]); }
            }
        }
        if (g_rvc.trace && GetTickCount() - m->traceT >= 1000) {
            m->traceT = GetTickCount();
            rv_log("trace merc=%d '%s' WSTAND hp=%.1f/%.1f bleed in %.1fs mask=%04x +888=%d +124=%ld heal=%p dnd tries %d room=%d",
                   m->merc, m->name, (double)hp, (double)mx, (m->deadline - T) / 1024.0f,
                   sq_rd((BYTE*)rd32(m->body + 0x54) + 0x3a, 2) ? *(WORD*)((BYTE*)rd32(m->body + 0x54) + 0x3a) : 0xffff, rd8(m->body + 0x888),
                   (long)rd32(m->s + 0x124), healOn ? act : 0, m->wsTries, rv_task(m->s) ? rv_can_down(m) : -1);
            if (g_rvDead) return;
        }
        break;
    }
    case RS_DOWN: {
        int susp = 0;
        if (rd32(m->s + 0x4b4) && rd32(m->s + 0x74) == rd32(m->s + 0x4b4)) {   /* review: DD's dying task on top of DND */
            rv_to_dead(m, T, "dying task current while DOWN (DoT / script kill) - mask cleared, no hold");
            break;
        }
        if (!dnd) {                                    /* CHANGE 7 (design): not a valid DOWN any more (life is 1, checked above) */
            int pushed = rv_dnd_pushed(m->s, m->body);
            if (pushed && (!m->suspT || T - m->suspT < RV_SUSP_MAX)) {   /* FIX 1: a task on top of his DND: still down */
                if (!m->suspT) m->suspT = T ? T : 1;
                if (!m->suspLogged) {
                    m->suspLogged = 1;
                    rv_log("merc=%d '%s': DND task pushed but not current (current %08lx, DND %08lx) - stays DOWN (mask, hold, bleed; no heal prompt) for up to %d s",
                           m->merc, m->name, rd32(m->s + 0x74), rd32(m->s + 0x4b8), RV_SUSP_MAX / 1024);
                }
                susp = 1;
            } else {
                if (live) { rv_mask(m, 0); if (pushed) rv_release_hold(m, T); else m->hold = 0; }
                if (pushed) rv_note_left(m, T);
                rv_left_down(m, T);
                m->coolT = T + 2048; m->suspT = 0;
                rv_setstate(m, RS_NORMAL, T, pushed ? "DND task suspended (not current) for 30 s - hold and mask given back, no re-entry for 10 s"
                                                    : "DND task no longer pushed (native end / cutscene / order) - reset without heal, mask given back");
                break;
            }
        } else if (m->suspT) {
            rv_log("merc=%d '%s': DND task current again after %.1f s suspended - still DOWN", m->merc, m->name, (T - m->suspT) / 1024.0f);
            m->suspT = 0; m->suspLogged = 0;
        }
        if (live) { rv_mask(m, 1); rv_hold(m, T); rv_noregen(m, T); if (m->buddy) rv_buddy_prevent(m); }
        if (T - m->stT < 1024 && hp > m->baseHp) m->baseHp = hp;   /* DND Start raises HP to 0.25 x max */
        if (healOn && act[0x18]) m->healSeen = 1;      /* CHANGE 4: the heal landed (0x7e75b0) */
        if (healOn) m->healOnSeen = 1;
        else if (m->healOnSeen) {                      /* the action ended between two frames: healed if HP reached max */
            m->healOnSeen = 0;
            if (okHp && mx > 0 && hp >= 0.99f * mx) m->healSeen = 1;
            else rv_log("merc=%d '%s': heal action ended without the heal (hp %.1f/%.1f) - stays DOWN", m->merc, m->name, (double)hp, (double)mx);
        }
        if (m->healSeen) {
            if (live) rv_release_hold(m, T);
            m->getupT = T;
            rv_setstate(m, RS_GETUP, T, live ? "healed by the player: hold released" : "dry: healed (would release the hold)");
            break;
        }
        /* FIX 1: an HP rise while DOWN is DD's own down-state behaviour (DND Start 0.25 x max, regen 0x419570 - held
           off above while live), never a way out: the old RESTORED(external) exit flapped DOWN/NORMAL once a second.
           Logged once per down. */
        if (okHp && T - m->stT >= 1024 && hp > m->baseHp + 1.0f && !healOn && !m->healOnSeen && !m->hpRiseLogged) {
            m->hpRiseLogged = 1;
            rv_log("merc=%d '%s': HP rose while DOWN without our heal (%.1f -> %.1f / %.1f) - stays DOWN (DD's down state; bleed continues)",
                   m->merc, m->name, (double)m->baseHp, (double)hp, (double)mx);
        }
        if (g_rvc.godpause && rd32((void*)GOD_VAR)) { m->deadline += T - g_rv.lastT; }   /* DM: the god cheat stops the bleed-out */
        if (T >= m->deadline) {
            if (healOn || rd8(m->body + 0x888)) {    /* CHANGE 3: never while a heal targets him */
                if (!m->deferLogged) { m->deferLogged = 1; rv_log("merc=%d '%s': bleed-out deferred - a heal targets him (+0x888=%d, action %p)", m->merc, m->name, rd8(m->body + 0x888), act); }
                break;
            }
            if (!live) { if (!m->bledDry) { m->bledDry = 1; rv_log("merc=%d '%s': dry: would bleed out now (Die slot 52)", m->merc, m->name); } break; }
            rv_bleed_out(m, T);
            break;
        }
        if (g_rvc.trace && GetTickCount() - m->traceT >= 1000) {
            m->traceT = GetTickCount();
            BYTE *t = rv_task(m->s);
            BYTE *hb = (BYTE*)rd32(m->body + 0x5fc);
            rv_log("trace merc=%d '%s' DOWN%s hp=%.1f/%.1f bleed in %.1fs task+14-now=%d mask=%04x +888=%d +124=%ld heal=%p regen+1c-now=%d",
                   m->merc, m->name, susp ? " (DND suspended)" : "", (double)hp, (double)mx, (m->deadline - T) / 1024.0f, t ? *(int*)(t + 0x14) - T : 0,
                   sq_rd((BYTE*)rd32(m->body + 0x54) + 0x3a, 2) ? *(WORD*)((BYTE*)rd32(m->body + 0x54) + 0x3a) : 0xffff, rd8(m->body + 0x888),
                   (long)rd32(m->s + 0x124), healOn ? act : 0, sq_rd(hb + 0x1c, 4) ? *(int*)(hb + 0x1c) - T : 0);
        }
        break;
    }
    case RS_GETUP: {
        if (live) rv_mask(m, 1);
        if (!dnd || T - m->getupT > 8192) {            /* DND End ran (get-up done), or 8 s */
            if (live) { rv_sethp_max(m); if (g_rvDead) return; rv_mask(m, 0); }
            rv_note_left(m, T);                        /* FIX 1: DND task still pushed (timeout) -> no re-entry for 10 s */
            m->coolT = T + 2048; m->healSeen = 0;
            rv_setstate(m, RS_NORMAL, T, !dnd ? (live ? "up again: HP = max (DM), mask cleared" : "dry: up again") : "get-up timeout (8 s) - mask cleared");
        }
        break;
    }
    case RS_DEAD: {
        int dying = rd32(m->s + 0x74) == rd32(m->s + 0x4b4);
        int healing = healOn || rd8(m->body + 0x888);
        if (healing) m->healEndT = T ? T : 1;
        /* CHANGE 3: no DND get-up tail on a dead merc: hold 10 s after Die and for as long as his DND task is still
           pushed (current, or suspended under the dying task with +0x64c still 1 - End 0x67fa10 clears it) */
        if (live && (T - m->dieT < 10240 || rv_dnd_pushed(m->s, m->body) || rv_task(m->s))) rv_hold(m, T); else m->hold = 0;   /* task valid: see the park note */
        if (life != 1 && !m->deathT) m->deathT = T ? T : 1;
        if (life == 0) m->saw0 = 1;                   /* only SetLifeState(0) writes life 0 (0x6cee96), after its OnDeath */
        /* CHANGE 3: post-death guard: 2 s after his death, while a heal targets him / +0x888 is set, and 2 s after that */
        int guard = m->deathT && (T - m->deathT < 2048 || healing || (m->healEndT && T - m->healEndT < 2048));
        if (live && life == 1 && guard && m->undeadN < 4) {
            m->undeadN++;
            const char *cause = healing ? "a heal targets him" : (m->healEndT && T - m->healEndT < 2048) ? "a heal on him just ended" : "heal End / DND tail";
            if (!m->saw0) {
                /* life went 1 -> 2 without OnDeath (ZBecomeRagdoll slot 2 0x6772a7: vt+0x588(2)) and back to 1 (heal End
                   0x4ea1bf: vt+0x588(1)) before DD's own SetLifeState(0): that later call returns at once (0x6cee3c) once
                   life is 0, so a raw (2),(0) here would swallow his only OnDeath (slot 56 -> +0x513 -> MF_01). Run DD's
                   SetLifeState(0) itself: 0x7e72d0(2) (unregister), slot 56 OnDeath, 0x7e72d0(0) - OnDeath exactly once */
                DWORD f = rv_vf(m->body, 0x588);
                if (f != RV_F_SETLIFE || !rv_still(m)) {
                    rv_log("merc=%d '%s': life came back to 1 after his death (%s) before his OnDeath ran, but body vt+0x588 = %08lx (want 0x6cee20) or the "
                           "record no longer validates - left to DD (try %d/4)", m->merc, m->name, cause, f, m->undeadN);
                } else {
                    rv_call1("SetLifeState(0) 0x6cee20", RV_F_SETLIFE, m->body, 0);
                    if (g_rvDead) return;
                    if (rd8(m->body + 0x576) == 0) m->saw0 = 1;
                    rv_log("merc=%d '%s': life came back to 1 after his death (%s) before his OnDeath ran - SetLifeState(0) 0x6cee20: unregistered, OnDeath "
                           "(slot 56) once, dead (life now %d, +0x513=%d, guard %d/4)", m->merc, m->name, cause, rd8(m->body + 0x576), rd8(m->s + 0x513), m->undeadN);
                }
            } else {
                /* CHANGE 4: OnDeath already ran (life 0 was seen). 0x7e72d0(2) = the unregister branch (vt+0x60c(0),
                   0x7ee3d0([0x1535c70], body, 4), vt+0x1f0(0), then [+0x50c] vt+0xd0 and vt+0x374; 0x7e72f9-0x7e7321),
                   then (0) = 0x5cf740(0) + the same tail: SetLifeState(0) without its slot 56 OnDeath, so no second fail
                   and no kill credit */
                rv_call1("life 2 (unregister) 0x7e72d0", RV_F_LIFE, m->body, 2);
                if (g_rvDead) return;
                rv_call1("life 0 (no OnDeath) 0x7e72d0", RV_F_LIFE, m->body, 0);
                if (g_rvDead) return;
                rv_log("merc=%d '%s': life came back to 1 after his death (%s) - 0x7e72d0(2) then (0): unregistered and dead again, no second OnDeath (life now %d, guard %d/4)",
                       m->merc, m->name, cause, rd8(m->body + 0x576), m->undeadN);
            }
        }
        if (live && life == 1 && !m->deathT && !dying && !m->killT && T - m->dieT > 3072) {   /* Die did not take: Kill */
            m->killT = T;
            DWORD f = rv_vf(m->body, 0x5e4);
            if (rv_vf(m->body, 0x670) == RV_F_SETHP) rv_call1("SetHitPoints 0", RV_F_SETHP, m->body, fbits(0.0f));
            if (!g_rvDead && f == RV_F_KILL) rv_call0("Kill 0x8af4b0", RV_F_KILL, m->body);
            if (!g_rvDead) rv_log("merc=%d '%s': still alive, dying task not current 3 s after Die (current %08lx, dying %08lx) - Kill (vt+0x5e4 %08lx)",
                                  m->merc, m->name, rd32(m->s + 0x74), rd32(m->s + 0x4b4), f);
        }
        /* the fail: DD's own (slot 56 -> +0x513 -> MF_01). CHANGE 8: the buddy with +0x513 = 0 must still fail
           (unless squad critical=clear, or M05 where ZLevelCtrlM05 fails with MF_05) */
        if (live && !m->failDone && m->deathT && T - m->deathT > 1536 && life != 1) {
            m->failDone = 1;
            int crit = rd8(m->s + 0x513), clr = g_sqc.critClear && g_sqc.mode != SQ_OFF;
            if (crit) rv_log("merc=%d '%s'%s: dead, +0x513 = 1 - DD's own MF_01_MercDead (slot 56 -> 0x6d25fa); fail window open=%d", m->merc, m->name,
                             m->buddy ? " (buddy)" : "", rd8((void*)(RV_FAILOBJ + 0x20)));
            else if (clr) rv_log("merc=%d '%s'%s: dead, +0x513 = 0 by squad critical=clear - no fail (as configured)", m->merc, m->name, m->buddy ? " (buddy)" : "");
            else if (!m->buddy) rv_log("merc=%d '%s': dead, +0x513 = 0 (DD's own rule for this merc) - no fail", m->merc, m->name);
            else if (rv_scene_is("M05")) rv_log("merc=%d '%s': buddy dead in M05 - left to ZLevelCtrlM05 (MF_05_LynchDied, 0x72048b), no second fail", m->merc, m->name);
            else rv_force_fail(m);
        }
        break;
    }
    }
    m->lastLife = life; m->lastDnd = dnd; m->lastHp = hp;
}

/* ---------- prompt + use (CHANGE 1) ---------- */
static int rv_player_free(BYTE *P, const char **why) {
    *why = 0;
    if (!(rd8(P + 0x2720) & 2)) *why = "not the local human";
    else if (sq_busy(P)) *why = "busy / HUD state";
    else if (rd8(P + 0x2728) || rd32(P + 0x2760)) *why = "gameplay input blocked";
    else if (rd32(P + 0xed0) & 0x80) *why = "input blocked (P+ed0)";
    else if (rd8(P + 0xd29)) *why = "use action running";
    else if (rd32(P + 0xd44) || rd32(P + 0xd50)) *why = "seat / carrier";
    else if (cl_disp_cur(P) != 0) *why = "action running";
    else if (g_cl.active) *why = "climbing";
    else if (rd32(P + 0x6b0) != (DWORD)(P + 0xdb0)) *why = "movement table (MiniScene)";
    else {
        BYTE *mov = (BYTE*)rd32(P + 0x6b4); int id = sq_rd(mov + 0x44, 4) ? *(int*)(mov + 0x44) : -1;
        BYTE *rm = (BYTE*)rd32(P + 0xdf0);            /* rappel prompt up (climb.inc's test): E belongs to the rappel */
        if (id != 2 && id != 3) *why = "movement not Stand/BaseMove (cover, vehicle ...)";
        else if (sq_rd(rm, 0x1f70) && *(BYTE**)(rm + 0x38) == P && rm[0x1f6c] && !rm[0x1f6d] && *(BYTE**)(rm + 0x1f68)) *why = "inside a rappel point";
    }
    return *why == 0;
}
static int rv_key_down(void) {
    if (!g_rvc.key) return 0;
    if (!g_rv.kb || rd32(g_rv.kb) != SQ_KB_VT || g_rv.sys != (BYTE*)rd32((void*)0xddb958)) {
        BYTE *sys = (BYTE*)rd32((void*)0xddb958); g_rv.kb = 0; g_rv.sys = sys;
        int n = sq_rd(sys, 0x94) ? (int)*(DWORD*)(sys + 0x90) : 0;
        for (int i = 0; i < n && i < 16; i++) { BYTE *dv = (BYTE*)rd32(sys + 4 + 4 * i); if (sq_rd(dv, 0x34) && *(DWORD*)dv == SQ_KB_VT) { g_rv.kb = dv; break; } }
    }
    return g_rv.kb ? sq_dev_down(g_rv.kb, g_rvc.key) : 0;
}
static void rv_prompt(BYTE *P, int T, int live) {
    int wasUp = g_rv.promptUp; BYTE *offered = g_rv.offerBody;
    g_rv.promptUp = 0; g_rv.offerBody = 0;
    int useNow = 0;
    if (g_rvc.use & RVU_FLAG) useNow |= (rd32(P + 0x818) >> 5) & 1;
    if (g_rvc.use & RVU_KEY) useNow |= sq_foreground() && rv_key_down();
    int edge = useNow && !g_rv.prevUse; g_rv.prevUse = useNow;
    if (!rv_anp_level() || (rv_scene_is("M01") && !g_rvc.m01)) return;   /* DM: no healing in M01 */
    const char *why;
    if (!rv_player_free(P, &why)) return;
    float pp[3]; BYTE *pn = (BYTE*)rd32(P + 4);
    if (!pn || !fw_world(pn, pp)) return;
    RvMerc *best = 0; float bd = 1e30f, bdy = 0;
    for (int i = 0; i < g_rvn; i++) {
        RvMerc *m = &g_rvm[i];
        if ((m->st != RS_DOWN && m->st != RS_WSTAND) || rd8(m->body + 0x888) || rd8(m->body + 0x576) != 1) continue;   /* CHANGE 2: alive only */
        if (m->st == RS_DOWN && !rv_dnd_current(m->s, m->body)) continue;   /* FIX 1: DND suspended: the heal start would refuse */
        float bp[3]; BYTE *bn = (BYTE*)rd32(m->body + 4);
        if (!bn || !fw_world(bn, bp)) continue;
        float d = v3dist(pp, bp), dy = bp[1] - pp[1];
        if (d > g_rvc.range || (g_rvc.maxdy > 0 && fabsf(dy) > g_rvc.maxdy)) continue;
        if (d < bd) { bd = d; bdy = dy; best = m; }
    }
    if (!best) return;
    if (!live) {
        static DWORD lastDry;
        if (sq_rate(&lastDry, 2000)) rv_log("dry: would offer the heal prompt (0x4c06c0 id 0x1b) for merc=%d '%s' d=%.0f dy=%.0f", best->merc, best->name, (double)bd, (double)bdy);
        return;
    }
    /* trigger: our prompt is the shown one (committed from last frame's offer) + a use edge */
    int shown = rd32(P + 0xcfc) == RV_PROMPT_ID;
    if (edge && wasUp && offered == best->body && shown) {
        rv_log("use: prompt 0x1b shown (input type %ld), use edge (flag %lu key %d) - starting the heal on merc=%d '%s' d=%.0f dy=%.0f",
               (long)rd32(P + 0xd04), (rd32(P + 0x818) >> 5) & 1, (g_rvc.use & RVU_KEY) ? rv_key_down() : -1, best->merc, best->name, (double)bd, (double)bdy);
        rv_start_heal(P, best, T, "use");
        return;
    }
    DWORD a[7] = {RV_PROMPT_ID, 0, fbits(bd), 0, 0, 0, 0};
    DWORD ok = rv_call("offer prompt 0x4c06c0", RV_F_OFFER, P, 7, a) & 0xff;
    if (g_rvDead) return;
    if (offered != best->body) rv_log("prompt: offered 0x1b for merc=%d '%s' d=%.0f dy=%.0f -> %s (shown now %08lx)", best->merc, best->name, (double)bd, (double)bdy,
                                      ok ? "pending" : "refused by 0x4c06c0 (0x6349a0 gate / action / higher prompt)", rd32(P + 0xcfc));
    g_rv.promptUp = ok || shown; g_rv.offerBody = best->body; g_rv.offerT = T;   /* promptUp: climb.inc leaves E to us */
}

/* ---------- test commands ---------- */
static RvMerc *rv_pick(const char *w, BYTE *P) {
    if (!w || !*w || !_stricmp(w, "nearest")) {
        float pp[3]; BYTE *pn = (BYTE*)rd32(P + 4); if (!pn || !fw_world(pn, pp)) return 0;
        RvMerc *b = 0; float bd = 1e30f;
        for (int i = 0; i < g_rvn; i++) { float bp[3]; if (g_rvm[i].st == RS_EXCL || !fw_body_pos(g_rvm[i].body, bp)) continue; float d = v3dist(pp, bp); if (d < bd) { bd = d; b = &g_rvm[i]; } }
        return b;
    }
    if (!_stricmp(w, "buddy")) { for (int i = 0; i < g_rvn; i++) if (g_rvm[i].buddy) return &g_rvm[i]; return 0; }
    int id = atoi(w);
    for (int i = 0; i < g_rvn; i++) if (g_rvm[i].merc == id) return &g_rvm[i];
    return 0;
}
static void rv_cmd_poll(void) {
    DWORD now = GetTickCount();
    if (now - g_rv.cmdPoll < 250) return;
    g_rv.cmdPoll = now;
    char fn[MAX_PATH], dn[MAX_PATH];
    _snprintf(fn, sizeof fn, "%s\\ANP_revive_cmd.txt", g_dir); _snprintf(dn, sizeof dn, "%s\\ANP_revive_cmd.done", g_dir);
    if (GetFileAttributesA(fn) == INVALID_FILE_ATTRIBUTES) return;
    char buf[1024] = ""; FILE *f = fopen(fn, "r");
    if (!f) return;
    size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
    if (!n) return;
    if (!MoveFileExA(fn, dn, MOVEFILE_REPLACE_EXISTING) && !DeleteFileA(fn)) { rv_log("cmd: cannot consume ANP_revive_cmd.txt (error %lu)", GetLastError()); return; }
    for (char *l = strtok(buf, "\r\n"); l; l = strtok(NULL, "\r\n")) {
        while (*l == ' ' || *l == '\t') l++;
        if (!*l || *l == '#' || g_rvQn >= 16) continue;
        _snprintf(g_rvQ[(g_rvQh + g_rvQn) % 16], 96, "%s", l); g_rvQ[(g_rvQh + g_rvQn) % 16][95] = 0; g_rvQn++;
    }
}
static void rv_cmd_exec(const char *line, BYTE *P, int T, int live) {
    char b[96]; _snprintf(b, sizeof b, "%s", line); b[95] = 0;
    char *tok[3] = {0, 0, 0}; int nt = 0;
    for (char *t = strtok(b, " \t"); t && nt < 3; t = strtok(NULL, " \t")) tok[nt++] = t;
    if (!nt) return;
    rv_log("cmd '%s'", line);
    if (!_stricmp(tok[0], "state")) { for (int i = 0; i < g_rvn; i++) rv_merc_line(&g_rvm[i], "cmd state"); rv_log("state: P=%p shown prompt %08lx promptUp=%d heal starts %d levelOk=%d mode=%s", P, rd32(P + 0xcfc), g_rv.promptUp, g_rv.healStarts, g_rv.levelOk, RV_MODE[g_rvc.mode]); return; }
    if (!live) { rv_log("cmd '%s': not live (mode %s, build %d, level pre-flight %d) - nothing done", line, RV_MODE[g_rvc.mode], g_rvBuild, g_rv.levelOk); return; }
    int all = nt > 1 && !_stricmp(tok[1], "all");
    if (!g_rvn) { rv_log("cmd '%s': no mercs", line); return; }
    for (int i = 0; i < g_rvn; i++) {
        RvMerc *m = all ? &g_rvm[i] : rv_pick(nt > 1 ? tok[1] : 0, P);
        if (!m) { rv_log("cmd '%s': no such merc", line); return; }
        if (all && m->st == RS_EXCL) continue;
        if (!_stricmp(tok[0], "down")) {
            if (m->st != RS_NORMAL) rv_log("cmd down merc=%d: state %s - skipped", m->merc, RS_NAME[m->st]);
            else { m->gateLogged = 0; if (!rv_floor_down(m, T, "cmd down") && !g_rvDead) rv_log("cmd down merc=%d: refused (see the line above)", m->merc); }
        } else if (!_stricmp(tok[0], "wstand")) {     /* FIX 2 test: WSTAND directly, no gates */
            if (m->st != RS_NORMAL) rv_log("cmd wstand merc=%d: state %s - skipped", m->merc, RS_NAME[m->st]);
            else if (!m->maskOk || rd8(m->body + 0x576) != 1) rv_log("cmd wstand merc=%d: mask object not usable (%d) or life %d - skipped", m->merc, m->maskOk, rd8(m->body + 0x576));
            else { m->keepDl = 0; rv_enter_wstand(m, T, "cmd wstand"); }
        } else if (!_stricmp(tok[0], "bleed")) {
            if (m->st == RS_DOWN || m->st == RS_WSTAND) { m->deadline = T; rv_log("cmd bleed merc=%d: deadline = now", m->merc); } else rv_log("cmd bleed merc=%d: state %s - skipped", m->merc, RS_NAME[m->st]);
        } else if (!_stricmp(tok[0], "heal")) {
            if (m->st == RS_DOWN || m->st == RS_WSTAND) rv_start_heal(P, m, T, "cmd"); else rv_log("cmd heal merc=%d: state %s - skipped", m->merc, RS_NAME[m->st]);
        } else { rv_log("cmd '%s' unknown (down|wstand|heal|bleed <merc|buddy|nearest|all>, state, wait S)", tok[0]); return; }
        if (!all || g_rvDead) return;
    }
}

/* ---------- per-frame tick ---------- */
static int revive_tick_body(void *unused) {
    (void)unused;
    sq_rd_reset();
    int prevMode = g_rvc.mode, prevBuddy = g_rvc.buddyDm, prevNex = g_rvc.nexcl;
    RvExcl prevEx[RV_MAXEXCL]; memcpy(prevEx, g_rvc.excl, sizeof prevEx);
    rv_cfg_poll();
    if (g_rvBuild < 0) { g_rvBuild = rv_check_build(); anp_log("revive: kl2 build check %s", g_rvBuild ? "ok" : "FAILED (dry only)"); }
    if (g_rvn && rd32((void*)RV_MERCS) == 0) {        /* merc list emptied (see below): no give-back on the config changes */
        rv_log("merc list emptied (0x76c915, same-scene restart): %d record(s) forgotten, no write (the objects may be freed)", g_rvn);
        g_rvn = 0;
    }
    if (prevMode == RV_LIVE && g_rvc.mode != RV_LIVE) rv_giveback_all("mode left live");
    if (prevBuddy != g_rvc.buddyDm) {                /* buddy rule changed: re-evaluate the buddy record */
        for (int i = 0; i < g_rvn; i++) if (g_rvm[i].buddy) { rv_giveback(&g_rvm[i], rv_now(), "buddy rule changed"); g_rvm[i] = g_rvm[--g_rvn]; break; }
    }
    if (prevNex != g_rvc.nexcl || memcmp(prevEx, g_rvc.excl, sizeof prevEx)) {   /* exclusions changed: re-evaluate every record */
        if (g_rvn) { rv_giveback_all("exclude list changed"); g_rvn = 0; }
    }
    char scene[8];
    EnterCriticalSection(&g_cmpCs); memcpy(scene, g_cscene, sizeof scene); LeaveCriticalSection(&g_cmpCs);
    scene[sizeof scene - 1] = 0;
    DWORD gs = rd32((void*)RV_GS);
    if (strcmp(scene, g_rvOrigScene)) { g_rvOrigN = 0; memcpy(g_rvOrigScene, scene, sizeof scene); g_rvOrigGs = gs; }   /* scripts freed */
    if (g_rvc.mode == RV_OFF) {                       /* CHANGE 9b: a reload while off can still bring our +0x124 back */
        if (rd32((void*)RV_MERCS) == 0) { g_rvn = 0; g_rvOrigN = 0; }   /* same-scene restart while off: objects may be freed (review) */
        if (gs != g_rvOrigGs && g_rvOrigN) rv_orig_fix_all("checkpoint reload while off");
        g_rvOrigGs = gs; g_rv.promptUp = 0; return 0;
    }
    /* merc list emptied: 0x76c915 (call 0x676480 on 0x1548fd8) is its only clearer, on a same-scene restart that keeps
       g_cscene. The scripts / bodies the records and the +0x124 table name may be freed (and their addresses reused),
       so forget them with no write. Every friendly soldier, the buddy included, is appended at 0x615e42 before
       gameMgr+0x4cf0 is set (0x615e5d), so while the list is empty a buddy pointer is stale: no collect then either */
    int listEmpty = rd32((void*)RV_MERCS) == 0;
    if (listEmpty && (g_rvn || g_rvOrigN)) {
        rv_log("merc list emptied (0x76c915, same-scene restart): %d record(s) and %d +0x124 entr%s forgotten, no write (the objects may be freed)",
               g_rvn, g_rvOrigN, g_rvOrigN == 1 ? "y" : "ies");
        g_rvn = 0; g_rvOrigN = 0;
    }
    BYTE *P = sq_player();
    int T = rv_now();
    /* new level, or a new player object. P == NULL (teardown / loading) alone does not reset, so no give-back runs on
       objects being destroyed; the records just wait (the tick returns below) */
    if ((P && P != g_rv.P) || strcmp(scene, g_rv.scene)) {
        if (!strcmp(scene, g_rv.scene) && g_rvn && !listEmpty)   /* CHANGE 1: same scene, new player: the mercs may live on - give back */
            rv_giveback_all("player changed");        /* (each write only while rv_still() validates the merc; list count 0 = forgotten above) */
        g_rvn = 0; g_rvQn = 0;                        /* new scene: the old objects may be freed - forget, no write */
        memset(&g_rv, 0, sizeof g_rv); g_rv.P = P; memcpy(g_rv.scene, scene, sizeof scene); g_rv.lastT = T; g_rv.t0 = GetTickCount();
        g_rv.gs = gs; g_rv.gsSeen = 1; g_rv.levelOk = -1; g_rv.prevUse = 1;
        if (P && rv_anp_level()) rv_log("level %s: player %p mode %s buddy=%s - pre-flight in 2 s", scene, P, RV_MODE[g_rvc.mode], g_rvc.buddyDm ? "dm" : "dd");
    }
    if (!P || !rv_anp_level()) { g_rv.promptUp = 0; return 0; }
    if (gs != g_rv.gs) {                              /* checkpoint reload / restart: our bits off, states forgotten */
        rv_log("game-state counter %lu -> %lu (checkpoint reload / restart): our writes given back, states forgotten", g_rv.gs, gs);
        rv_giveback_all("state change"); g_rvn = 0; g_rv.gs = gs;
        if (!rv_live() && g_rvOrigN) rv_orig_fix_all("checkpoint reload, not live");   /* CHANGE 9b */
    }
    g_rvOrigGs = gs;
    if (T == g_rv.lastT) return 0;                    /* paused */
    if (!g_rv.preflight && GetTickCount() - g_rv.t0 >= 2000) {
        g_rv.preflight = 1;
        if (g_rvBuild == 1) rv_preflight(P); else g_rv.levelOk = 0;
        if (g_rvDead) return 0;
        rv_level_log(P);
    }
    int live = rv_live();
    if (live) g_rvEverLive = 1;
    if (!listEmpty) rv_collect(P, T, live);           /* empty list: nothing to manage, and +0x4cf0 may be stale (above) */
    if (g_rv.preflight == 1) {                        /* census once, after the pre-flight */
        g_rv.preflight = 2;
        for (int i = 0; i < g_rvn; i++) rv_merc_line(&g_rvm[i], "level census");
        if (!g_rvn) rv_log("level %s: no friendly mercs listed yet (merc list count %ld)", g_rv.scene, (long)rd32((void*)RV_MERCS));
    }
    for (int i = 0; i < g_rvn && !g_rvDead; i++) rv_merc_tick(&g_rvm[i], P, T, live);
    if (g_rvDead) return 0;
    if (g_rv.preflight) rv_prompt(P, T, live);
    if (g_rvDead) return 0;
    rv_cmd_poll();
    DWORD now = GetTickCount();
    if (g_rvQn && now >= g_rv.waitUntil) {
        char line[96]; memcpy(line, g_rvQ[g_rvQh], sizeof line); g_rvQh = (g_rvQh + 1) % 16; g_rvQn--;
        if (!_strnicmp(line, "wait", 4) && (line[4] == ' ' || line[4] == '\t' || !line[4])) {
            float sec = (float)atof(line + 4); if (sec < 0) sec = 0; if (sec > 120) sec = 120;
            g_rv.waitUntil = now + (DWORD)(sec * 1000.0f);
            rv_log("cmd 'wait %.1f'", (double)sec);
        } else rv_cmd_exec(line, P, T, live);
    }
    g_rv.lastT = T;
    return 0;
}
static int revive_cleanup_body(void *unused) { (void)unused; rv_giveback_all("module disabled"); return 0; }
static void revive_frame(void) {
    if (g_rvDead || !g_clMainTid || GetCurrentThreadId() != g_clMainTid) return;
    if (climb_guarded("revive tick", revive_tick_body, 0) < 0) rv_kill("tick", "fault (see 'climb: FAULT ... in revive tick' above)");
    if (g_rvDead) {                                   /* give every write back once (guarded on its own) */
        if (climb_guarded("revive cleanup", revive_cleanup_body, 0) < 0) anp_log("revive: cleanup faulted - some merc may keep mask bit 0x4000 / a hold until the next checkpoint");
        g_rvn = 0;
    }
}
/* shared with give.inc / squad.inc / climb.inc (declared in anp_loader.c) */
static int revive_is_down(const BYTE *body) {
    if (!rv_live()) return 0;                         /* CHANGE 6: dry / off / refused build or level = squad and give stay stock */
    RvMerc *m = body ? rv_find_body(body) : 0;
    if (m && (m->st == RS_PENDING || m->st == RS_DOWN || m->st == RS_GETUP)) return 1;
    if (!body || !sq_rd(body, 0x780) || rd8(body + 0x64c) != 1) return 0;   /* native DND, any mode */
    BYTE *s = (BYTE*)rd32(body + 0x77c);
    return sq_rd(s, 0x740) && rd32(s) == RV_SCRIPT_VT && rv_dnd_current(s, (BYTE*)body);
}
static int revive_prompt_up(void) { return g_rv.promptUp; }
