/* klsteamside.h: the PURE logic of the [Net] SideChannelSteam log-only probe (klsteamprobe.c; re/side_channel_steam.md). No windows.h, no Steam call.
   Checked off-game by klsteamside_test.c. */
#ifndef KLSTEAMSIDE_H
#define KLSTEAMSIDE_H
#include <string.h>

/* Interface versions tried, in order (SteamNetworking005 first, 004 as the fallback). 003 is the game's own and is never asked for here. */
#define KLSS_NVER 2
static const char *klss_ver(int k)
{
    static const char *const v[KLSS_NVER] = { "SteamNetworking005", "SteamNetworking004" };
    return (k >= 0 && k < KLSS_NVER) ? v[k] : 0;
}

/* ISteamClient::GetISteamNetworking, READ in steam_api.dll (SteamAPI_Init, 2026-10-29): "mov edx,[eax+0x44]; push str; push esi(pipe); push edi(user); call edx"
   with ecx = the client object: vtable byte offset 0x44 = index 17, thiscall, args (hUser, hPipe, const char *version). */
#define KLSS_GETNET_VOFF 0x44

/* The game's peer table entry (16 bytes, re/netcode.md 3.4): Steam ID u64 at +1 (unaligned), byte +9 = "the game has sent here" (a soft hint, NOT "session open"). */
typedef struct { unsigned long id_lo, id_hi; int flag9; } klss_peer;
static int klss_peer_parse(const unsigned char *e, klss_peer *p)
{
    if (!e || !p) return 0;
    memcpy(&p->id_lo, e + 1, 4); memcpy(&p->id_hi, e + 5, 4);
    p->flag9 = e[9];
    return (p->id_lo | p->id_hi) != 0;      /* an all-zero id is an empty slot */
}

/* The peer table sanity: count 1..4096 and a table pointer. */
static int klss_table_ok(unsigned long tab, unsigned long cnt) { return tab != 0 && cnt != 0 && cnt <= 4096; }

/* Rate limit of the periodic peer-table log: one dump per PERIOD_MS, at most MAX_LINES lines a session. Returns how many lines a dump may print now
   (0 = not yet / budget spent); the caller then adds that to *used and *last = now. Wrap-safe for a 32-bit millisecond clock. */
#define KLSS_PERIOD_MS 60000UL
#define KLSS_MAX_LINES 20
static int klss_dump_budget(unsigned long now, unsigned long last, int have_last, int used, int want)
{
    int left = KLSS_MAX_LINES - used;
    if (left <= 0 || want <= 0) return 0;
    if (have_last && (unsigned long)(now - last) < KLSS_PERIOD_MS) return 0;
    return want < left ? want : left;
}
#endif
