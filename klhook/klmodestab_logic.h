/*
 * klmodestab_logic.h - PURE part of [Keys] ModesTab / RoundHints (wk-modestab-1102; NOT RUN IN THE GAME; no windows.h, tested off game by klmodestab_test.c).
 *
 * ModesTab: the MOD CONTROLS shop page (klshoppage.c) gets a second view, BOTS AND MODES, one row per host / gamemode feature that has no key of its own
 * (they are ini switches, so they were a secret). kmt_state() turns the raw ini values the owning module reads (same keys, same defaults, same prerequisites) into
 * 0 OFF / 1 ON / 2 DRY (log only); kmt_row() / kmt_desc() build the row and description text.
 * RoundHints: kmt_hint_build() joins the keyed features that are ON into one announce line; kmt_host_text() names a host toggle's new state.
 */
#ifndef KLMODESTAB_LOGIC_H
#define KLMODESTAB_LOGIC_H
#include <stdio.h>
#include <string.h>

enum { KMT_TACTICS, KMT_DROPTAKE, KMT_DOORHOLD, KMT_BANK, KMT_VOICE, KMT_TRIGGERS, KMT_ESCORT, KMT_SHIELD, KMT_SWAP, KMT_CLOCK, KMT_N };
enum { KMT_OFF = 0, KMT_ON = 1, KMT_DRY = 2 };

static const struct kmt_def {
    const char *shortn;                  /* the row name, <= 12 characters so name + ' OFF' / ' ON' / ' DRY' fits the 16 the shop row takes (klshoppage.c SHOTS3 note) */
    const char *label;                   /* the description's first line */
    const char *ini;                     /* the ini line, for the description */
    const char *scope;                   /* "online host" / "Arcade" / "both" */
    const char *desc;
} kmt_def[KMT_N] = {
    { "BOT TACTICS",  "Bot tactics",        "[BotFill] OnlineTactics",                     "online host", "The host drives the AI heisters like Arcade: loot, doors, escape. Needs [BotFill] OnlineHost=1." },
    { "DROP TAKE",    "Drop take",          "[BotFill] OnlineDropTake",                    "online host", "AI heisters pick up the loot the cops drop. Needs Bot tactics AND [BotFill] OnlineTacticsTake=2 (else it only walks, takes nothing)." },
    { "DOOR HOLD",    "Door hold",          "[BotFill] OnlineDoorHold",                    "online host", "AI heisters wait for a vault door to open before they rush the stacks. Needs Bot tactics AND [BotFill] OnlineSkipDoorStacks=1 (the default)." },
    { "BANK CREDIT",  "Bank credit",        "[BotFill] OnlineBank / OnlineBankCredit",     "online host", "Loot the AI heisters carry is banked and credited to the team as in Arcade. Needs Bot tactics AND [BotFill] OnlineTacticsTake=1 or 2." },
    { "BOT VOICE",    "Bot voice",          "[BotFill] OnlineVoice",                       "online host", "AI heisters speak their lines on every seat. (The crew banter of human players is [Voice] OnlineTalk, a different switch.)" },
    { "COP TRIGGERS", "Bots trigger cops",  "[BotFill] OnlineTriggers",                    "online host", "AI heisters set off the cop waves by walking into trigger boxes, as in Arcade." },
    { "ESCORT",       "Escort",             "[Bots] OnlineEscort",                         "online host", "AI heisters escort a player who carries loot to the van." },
    { "HOSTAGE SHLD", "Hostage shield",     "[Shield] Online",                             "both",        "Grab a hostage as a shield; the hit is taken by the hostage. Arcade: [Shield] Enable=1 (the default). Online: [Shield] Online=1 (host)." },
    { "SHOP SWAP",    "Shop swap",          "[Shop] OnlineSwap",                           "online host", "Online: the Dead Men guns replace shop rows; needs [Shop] Enable=1 and ([ShopPage] Enable=1 or [Shop] OnlineSwapArm=1). Arcade uses [Shop] Swap with Enable=1, not this switch." },
    { "ROUND CLOCK",  "Round clock",        "[Lobby] TimeAuto",                            "online host", "The lobby's round time is set by itself (minutes)." },
};

/* v[0..4] = the raw ini values of the module's own keys (kspg_m_state in klshoppage.c); 0 OFF, 1 ON, 2 DRY. Prerequisites are the ones the owning module checks (klbotfill.c, klshield.c, klshop.c) */
#define KMT_NV 5
static int kmt_mode12(int v) { return v == 1 ? KMT_ON : v == 2 ? KMT_DRY : KMT_OFF; }
static int kmt_state(int id, const int *v, int online)
{
    switch (id) {
    case KMT_TACTICS:  return v[0] && v[1] ? KMT_ON : KMT_OFF;                       /* v0 OnlineHost, v1 OnlineTactics */
    case KMT_DROPTAKE: return v[0] && v[1] && v[2] && v[3] == 2 ? KMT_ON : KMT_OFF;   /* v0 OnlineHost, v1 OnlineTactics, v2 OnlineDropTake, v3 OnlineTacticsTake (klbotfill.c: without 2 it only retargets, takes nothing) */
    case KMT_DOORHOLD: return v[0] && v[1] && v[2] && v[3] ? KMT_ON : KMT_OFF;        /* v3 OnlineSkipDoorStacks (default 1; DoorHold only acts while it counts shut stacks) */
    case KMT_BANK:     return !v[0] || !v[1] || !v[2] ? KMT_OFF : v[0] == 1 && v[1] == 1 ? KMT_ON : KMT_DRY;   /* v0 OnlineBank, v1 OnlineBankCredit, v2 OnlineTacticsTake != 0 (klbotfill.c: no credit without take 1/2); a dry ledger or dry credit = dry */
    case KMT_SHIELD:   return online ? (v[0] == 1 ? KMT_ON : v[0] == 2 ? KMT_DRY : KMT_OFF) : (v[1] ? KMT_ON : KMT_OFF);   /* v0 [Shield] Online, v1 [Shield] Enable (Arcade part, default 1); wk-modestab 1102 fix: online the shield works only with Online=1/2 (klshield.c: klsh.on = arc || online, but the Arcade gate is false online), so Enable=1 alone no longer reads ON there; offline only Enable counts. Enable is not required online (klshield.c keeps the part on with Online alone) */
    case KMT_SWAP:     return !v[1] || !v[2] ? KMT_OFF : kmt_mode12(v[0]);            /* v0 [Shop] OnlineSwap, v1 [Shop] Enable, v2 [ShopPage] Enable or [Shop] OnlineSwapArm (klshop.c:382) */
    case KMT_VOICE: case KMT_TRIGGERS: case KMT_ESCORT: return kmt_mode12(v[0]);      /* BOT VOICE = BotFill OnlineVoice only; [Voice] OnlineTalk is the human crew's banter (kltalk.c) */
    case KMT_CLOCK:    return v[0] >= 1 && v[0] <= 20 ? KMT_ON : KMT_OFF;           /* v0 TimeAuto minutes (kllobbyopt.c: 1..20 else 0; kllo_init has no enable key of its own) */
    }
    return KMT_OFF;
}
/* rows whose feature acts on the HOST only: a client seat can set the ini switch but nothing happens on its machine. Read from the code: klbotfill.c (tactics / take / door hold / bank / voice send / triggers / escort: 'HOST only', role 2),
 * klshield.c Online (the host's own player), kllobbyopt.c TimeAuto (host only). SHOP SWAP acts on every seat's own shop, so it is not marked */
static int kmt_host_only(int id)
{
    return id == KMT_TACTICS || id == KMT_DROPTAKE || id == KMT_DOORHOLD || id == KMT_BANK || id == KMT_VOICE || id == KMT_TRIGGERS || id == KMT_ESCORT || id == KMT_SHIELD || id == KMT_CLOCK;
}
static const char *kmt_state_name(int s) { return s == KMT_ON ? "ON" : s == KMT_DRY ? "DRY" : "OFF"; }

/* the shop row: 'BOT TACTICS ON', cut to the bare name if longer than 16 */
static void kmt_row(int id, int state, char *o, size_t cap)
{
    char r[48];
    if (id < 0 || id >= KMT_N) { snprintf(o, cap, "-"); return; }
    snprintf(r, sizeof r, "%s %s", kmt_def[id].shortn, kmt_state_name(state));
    if (strlen(r) > 16) snprintf(r, sizeof r, "%s", kmt_def[id].shortn);
    snprintf(o, cap, "%s", r);
}
static void kmt_desc(int id, int state, char *o, size_t cap)
{
    if (id < 0 || id >= KMT_N) { if (cap) o[0] = 0; return; }
    snprintf(o, cap, "%s\n%s.  Now: %s in the ini.  Works in: %s.\nSwitch: %s in KLHook.ini or Mod Options.%s\nInformation page: BUY does nothing.",
             kmt_def[id].desc, kmt_def[id].label, kmt_state_name(state), kmt_def[id].scope, kmt_def[id].ini,
             state == KMT_DRY ? "\nDRY = it only writes the log, it changes nothing." : "");
}

/* the description with the client note: client = this seat is online and not the host; a host-only row then gets " (host only: you are a client)" at the end of its first line */
static void kmt_desc_ex(int id, int state, int client, char *o, size_t cap)
{
    char t[640]; char *nl;
    kmt_desc(id, state, t, sizeof t);
    if (client && kmt_host_only(id) && (nl = strchr(t, '\n')) != NULL) {
        size_t head = (size_t)(nl - t);
        snprintf(o, cap, "%.*s (host only: you are a client)%s", (int)head, t, nl);
    } else snprintf(o, cap, "%s", t);
}

/* RoundHints: 'F2 shop pages  E+W climb  G grenade'. keys[i] empty / on[i] 0 = left out. The result is cut at a whole entry within cap-1 characters. Returns the entry count */
static int kmt_hint_build(const char *const *keys, const char *const *what, const int *on, int n, char *o, size_t cap)
{
    int i, k = 0; size_t l = 0;
    if (!cap) return 0;
    o[0] = 0;
    for (i = 0; i < n; i++) {
        char e[64]; size_t el;
        if (!on[i] || !keys[i] || !keys[i][0] || !what[i] || !what[i][0]) continue;
        el = (size_t)snprintf(e, sizeof e, "%s%s %s", k ? "  " : "", keys[i], what[i]);
        if (el >= sizeof e || l + el >= cap) break;
        memcpy(o + l, e, el + 1); l += el; k++;
    }
    return k;
}

/* the shop page cycle (klshoppage.c kspg_next / kspg_cycle): pages 0 stock, 1 page II, 2 hire, 3 controls, 4 bots and modes. avail[p] != 0 = page p can be opened.
 * The next available page after cur in order; cur when none. With avail[4] == 0 (ModesTab off) it is the old 4-page cycle */
static int kmt_next(int cur, const int *avail)
{
    int i, p; for (i = 1; i <= 5; i++) { p = (cur + i) % 5; if (p != cur && avail[p]) return p; }
    return cur;
}
/* hPendPg: the early key press's target: 0 hire, 1 controls, 2 bots and modes (only pages 2..4 wait for the selector). kmt_pend_of(nxt) encodes, kmt_pend_ctl_mode(p) is the view it opens */
static int kmt_pend_of(int nxt) { return nxt == 4 ? 2 : nxt == 3 ? 1 : 0; }
static int kmt_pend_ctl_mode(int pend) { return pend == 2; }

/* a host toggle's announce text. which 0 map set (value 0 Dog Days, 1 Dead Men, else Both), 1 AI heisters (bit 0), 2 map pool (0 off, 1 Dead Men, 2 Dog Days, 3 Mix) */
static void kmt_host_text(int which, int value, char *o, size_t cap)
{
    static const char *const pool[4] = { "OFF", "Dead Men", "Dog Days", "Mix" };
    if (which == 0) snprintf(o, cap, "MAP SET: %s", value == 0 ? "Dog Days" : value == 1 ? "Dead Men" : "Both");
    else if (which == 1) snprintf(o, cap, "AI HEISTERS: %s", (value & 1) ? "ON" : "OFF");
    else snprintf(o, cap, "MAP POOL: %s", pool[value & 3]);
}
#endif /* KLMODESTAB_LOGIC_H */
