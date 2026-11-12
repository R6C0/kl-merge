/* klfresh_logic.h - pure decision for [Memory] FreshRestart (klfresh.c). No game access, no Windows; tested by klfresh_test.c.
 *
 * Why: kl2.exe is a 32-bit program without the large-address flag (2 GB). Every level load cuts the address space smaller (the largest free piece
 * falls from 512 MB at start to about 25 MB at the menu after ONE match, KLHook.log 2026-11-10 00:23) and after a few levels the game crawls
 * (the gray screen at 1.4 fps, DM06B 00:27). Nothing the hook can free comes back as one piece, but a NEW PROCESS starts with 1931 MB free.
 * So: when the game sits idle at the main menu and the session has loaded enough levels (or the address space is already too cut up), restart
 * kl2.exe cleanly instead of letting the next load go gray.
 *
 * The decision is a pure function of a snapshot; klfresh.c fills the snapshot from the game and acts on the answer. */
#ifndef KLFRESH_LOGIC_H
#define KLFRESH_LOGIC_H
#include <string.h>

struct klfh_cfg {
    int enable;            /* [Memory] FreshRestart */
    int every_levels;      /* FreshLevels: restart at the menu once this many level loads happened in this process (0 = never by count) */
    int min_piece_mb;      /* FreshMinPieceMB: or when the largest free piece is under this (0 = off) */
    int min_free_mb;       /* FreshMinFreeMB: or when the total free address space is under this (0 = off) */
    unsigned stable_ms;    /* FreshStableMs: the idle menu must have looked the same this long (a save, a click in progress) */
    unsigned min_up_ms;    /* FreshMinUpMs: never in the first seconds of a process (a restart loop can not form) */
    int max_chain;         /* FreshMax: at most this many restarts in a chain of children (the env counter) */
};

struct klfh_in {
    int test_run;          /* the command line / [Auto] says this is a scripted run (AutoExit, DefaultScene): never restart */
    int online;            /* kl_online(): a network session exists */
    int at_menu;           /* the frontend scene is loaded, the menu manager and a window stack are there */
    int start_pending;     /* StartGame was accepted: a load is about to begin */
    unsigned menu_ms;      /* how long at_menu has been true without a change of the window stack */
    unsigned up_ms;        /* process age */
    int levels;            /* level loads seen in this process */
    int chain;             /* restarts that led to this process */
    unsigned largest_mb;   /* largest free piece, MB (only needed when min_piece_mb is set; 0xffffffff = not measured) */
    unsigned free_mb;      /* total free address space, MB (same) */
};

enum { KLFH_NO, KLFH_LEVELS, KLFH_PIECE, KLFH_FREE };      /* 0 = do nothing; else the reason, for the log line */

static const char *klfh_why(int r)
{
    return r == KLFH_LEVELS ? "enough level loads" : r == KLFH_PIECE ? "largest free piece too small" : r == KLFH_FREE ? "free address space too small" : "no";
}

/* 1 = the gate is open (the state is one where a restart is safe), whatever the memory says */
static int klfh_gate(const struct klfh_cfg *c, const struct klfh_in *s)
{
    if (!c->enable || s->test_run || s->online || !s->at_menu || s->start_pending) return 0;
    if (s->menu_ms < c->stable_ms || s->up_ms < c->min_up_ms) return 0;
    if (c->max_chain >= 0 && s->chain >= c->max_chain) return 0;
    return 1;
}

/* does the memory (or the level count) ask for a restart? only meaningful with the gate open; needs levels >= 1 (a fresh process at the menu
   with a small piece cannot be helped by a restart) */
static int klfh_decide(const struct klfh_cfg *c, const struct klfh_in *s)
{
    if (!klfh_gate(c, s) || s->levels < 1) return KLFH_NO;
    if (c->every_levels > 0 && s->levels >= c->every_levels) return KLFH_LEVELS;
    if (c->min_piece_mb > 0 && s->largest_mb != 0xffffffffu && s->largest_mb < (unsigned)c->min_piece_mb) return KLFH_PIECE;
    if (c->min_free_mb > 0 && s->free_mb != 0xffffffffu && s->free_mb < (unsigned)c->min_free_mb) return KLFH_FREE;
    return KLFH_NO;
}

/* does decide() need the (costly) address space walk? only when the count rule does not already say yes and a threshold is set */
static int klfh_needs_walk(const struct klfh_cfg *c, const struct klfh_in *s)
{
    if (!klfh_gate(c, s) || s->levels < 1) return 0;
    if (c->every_levels > 0 && s->levels >= c->every_levels) return 0;
    return c->min_piece_mb > 0 || c->min_free_mb > 0;
}

/* level-load counter: feed it the scene kind every tick (1 = a level scene, 0 = the frontend, -1 = unknown/nothing); counts each entry into a level
   scene once. *last is the previous kind (start at -1). */
static int klfh_count(int *last, int kind, int *levels)
{
    if (kind < 0) return 0;                         /* between scenes: keep the previous kind */
    if (kind == 1 && *last != 1) { (*levels)++; *last = 1; return 1; }
    *last = kind;
    return 0;
}

/* the child's wait: what to do when the handles answer. ev = go event signalled, parent_dead = parent process ended.
   returns 1 = go on and start the game, 0 = the parent died without saying go (the player closed the game himself): the child must quit. */
static int klfh_child_go(int ev, int parent_dead)
{
    if (ev) return 1;
    return parent_dead ? 0 : -1;                    /* -1 = keep waiting */
}

/* the command line of the child: the parent's, unless it is a scripted one (then no restart, decided by test_run). Returns 1 when kept as is. */
static int klfh_cmd_is_test(const char *cmd)
{
    char low[2048]; int i;
    if (!cmd) return 0;
    for (i = 0; cmd[i] && i < (int)sizeof low - 1; i++) low[i] = (char)(cmd[i] >= 'A' && cmd[i] <= 'Z' ? cmd[i] + 32 : cmd[i]);
    low[i] = 0;
    return strstr(low, "autoexit") != 0 || strstr(low, "defaultscene") != 0 || strstr(low, "disablesplashscreens") != 0;
}

#endif
