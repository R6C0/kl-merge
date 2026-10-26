/* klucchide_test.c - OFF-GAME check of klucchide_logic.h: who may see the Undercover Cop, the host's reveal, the client's mirror of the host
 * state across rounds, the bounty choice, the packets, the kill-feed key route and the key edge of [UccHide]. Pure numbers; the game reads
 * and the network are klucchide.c's (NOT run here).
 *   cl /nologo /W4 klucchide_test.c      or      tools/run_harness_linux.sh klucchide_test */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "klucchide_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static void lobby(struct klucc_state *s, int host)
{   /* 6 players: 0 heister (host), 1 UCC, 2 heister, 3 police (dead heister back as a cop), 4 second UCC, 5 dirty cop; 6.. unused */
    memset(s, 0, sizeof *s);
    s->n = 8; s->on = 1; s->host = host; s->me = 0;
    s->used[0] = s->used[1] = s->used[2] = s->used[3] = s->used[4] = s->used[5] = 1;
    s->flags[1] = KLUCC_F_UCC; s->flags[3] = KLUCC_F_POLICE; s->flags[4] = KLUCC_F_UCC | KLUCC_F_UCC2; s->flags[5] = KLUCC_F_DIRTY;
}

int main(void)
{
    struct klucc_state s, c; char b[96]; const char *r; unsigned long e, a, x; struct klucc_key k;
    lobby(&s, 1);
    /* who is a UCC */
    CHECK(klucc_is_ucc(&s, 1)); CHECK(klucc_is_ucc(&s, 4)); CHECK(!klucc_is_ucc(&s, 0)); CHECK(!klucc_is_ucc(&s, 3));
    CHECK(!klucc_is_ucc(&s, 6)); CHECK(!klucc_is_ucc(&s, -1)); CHECK(!klucc_is_ucc(&s, 99));
    CHECK(klucc_ucc_mask(&s) == 0x12);
    CHECK(klucc_hidden(&s, 1) && klucc_hidden(&s, 4)); CHECK(klucc_any_hidden(&s));
    /* who sees him: heisters no; himself, the other UCC, police and dirty cops yes; an unknown viewer no */
    CHECK(!klucc_sees(&s, 0, 1)); CHECK(!klucc_sees(&s, 2, 1)); CHECK(!klucc_sees(&s, 2, 4));
    CHECK(klucc_sees(&s, 1, 1)); CHECK(klucc_sees(&s, 4, 1)); CHECK(klucc_sees(&s, 1, 4));      /* two UCCs know each other */
    CHECK(klucc_sees(&s, 3, 1)); CHECK(klucc_sees(&s, 5, 1));
    CHECK(!klucc_sees(&s, -1, 1)); CHECK(!klucc_sees(&s, 7, 1));                                /* unknown / unused viewer: hidden */
    CHECK(klucc_sees(&s, 0, 2)); CHECK(klucc_sees(&s, 0, 3));                                   /* a non-UCC target: nothing to hide */
    /* the flag dword a viewer's list gets */
    CHECK(klucc_view(&s, 0, 1, 0x80) == 0); CHECK(klucc_view(&s, 0, 4, 0x40080) == 0);
    CHECK(klucc_view(&s, 0, 1, 0x84) == 0x4);                                                   /* dead UCC: 'dead' stays, 0x80 goes */
    CHECK(klucc_view(&s, 1, 1, 0x80) == 0x80); CHECK(klucc_view(&s, 4, 1, 0x80) == 0x80); CHECK(klucc_view(&s, 3, 1, 0x80) == 0x80);
    CHECK(klucc_view(&s, 0, 3, 0x8) == 0x8); CHECK(klucc_view(&s, 0, 1, 0xffffffffu) == 0xffffffffu);
    s.on = 0; CHECK(klucc_view(&s, 0, 1, 0x80) == 0x80); s.on = 1;                              /* module off: the game's dword */
    /* bounty: 200k while any is hidden, 400k once all revealed */
    CHECK(klucc_bounty(&s, 200000, 400000) == 200000);
    /* host reveal: only a hidden UCC, only in the current epoch */
    s.epoch = 3;
    CHECK(!klucc_host_reveal(&s, 3, 0));                     /* a heister cannot 'reveal' */
    CHECK(!klucc_host_reveal(&s, 3, 3));                     /* police neither */
    CHECK(!klucc_host_reveal(&s, 2, 1));                     /* stale epoch */
    CHECK(klucc_host_reveal(&s, 3, 1)); CHECK(s.revealed == 0x2);
    CHECK(!klucc_host_reveal(&s, 3, 1));                     /* twice: no change */
    CHECK(klucc_sees(&s, 0, 1)); CHECK(klucc_view(&s, 2, 1, 0x80) == 0x80);   /* revealed: everybody sees him */
    CHECK(!klucc_sees(&s, 0, 4));                            /* the other one stays hidden */
    CHECK(klucc_bounty(&s, 200000, 400000) == 200000);
    CHECK(klucc_host_reveal(&s, 3, 4)); CHECK(!klucc_any_hidden(&s)); CHECK(klucc_bounty(&s, 200000, 400000) == 400000);
    klucc_host_new_round(&s); CHECK(s.epoch == 4 && s.revealed == 0 && klucc_any_hidden(&s));
    s.host = 0; CHECK(!klucc_host_reveal(&s, 4, 1)); s.host = 1;                                /* a client never decides */
    /* client mirror */
    lobby(&c, 0);
    CHECK(klucc_client_apply(&c, 4, 0x12, 0x2, 1000)); CHECK(c.epoch == 4 && c.revealed == 0x2);
    CHECK(!klucc_client_apply(&c, 3, 0x12, 0x12, 1100));    /* older epoch refused */
    CHECK(c.revealed == 0x2);
    CHECK(klucc_client_apply(&c, 4, 0x12, 0x3, 1200)); CHECK(c.revealed == 0x2);    /* bit 0 is no UCC here: dropped */
    /* new round seen by the client right after it adopted (host was first): kept */
    klucc_client_new_round(&c, 2000); CHECK(c.revealed == 0x2 && c.min_epoch == 0);
    /* new round seen long after: cleared, the old epoch no longer accepted */
    klucc_client_new_round(&c, 9000); CHECK(c.revealed == 0 && c.min_epoch == 5);
    CHECK(!klucc_client_apply(&c, 4, 0x12, 0x2, 9100)); CHECK(c.revealed == 0);
    CHECK(klucc_client_apply(&c, 5, 0x12, 0x0, 9200)); CHECK(c.revealed == 0 && c.epoch == 5);
    CHECK(klucc_client_apply(&c, 5, 0x12, 0x10, 9300)); CHECK(c.revealed == 0x10);
    c.host = 1; CHECK(!klucc_client_apply(&c, 6, 0x12, 0x12, 9400)); c.host = 0;              /* the host never mirrors */
    /* packets */
    klucc_fmt_state(b, sizeof b, 7, 0x12, 0x2); CHECK(!strcmp(b, "S;7;12;2"));
    CHECK(klucc_parse(b, &e, &a, &x) == 'S' && e == 7 && a == 0x12 && x == 0x2);
    klucc_fmt_req(b, sizeof b, 7, 4); CHECK(!strcmp(b, "R;7;4"));
    CHECK(klucc_parse(b, &e, &a, &x) == 'R' && e == 7 && a == 4);
    CHECK(!klucc_parse("R;7;16", &e, &a, &x)); CHECK(!klucc_parse("R;7;-1", &e, &a, &x));
    CHECK(!klucc_parse("R;7;4x", &e, &a, &x)); CHECK(!klucc_parse("S;7;12", &e, &a, &x));
    CHECK(!klucc_parse("S;7;10000;0", &e, &a, &x));  /* a mask past 16 clients */
    CHECK(!klucc_parse("i1c2m0o0", &e, &a, &x)); CHECK(!klucc_parse(0, &e, &a, &x)); CHECK(!klucc_parse("X;1;2", &e, &a, &x));
    /* kill-feed route */
    r = klucc_route_key("AllLevels/Interface/Online/Announcements/FA_Killed_UCC", b, sizeof b);
    CHECK(r && !strcmp(r, "AllLevels/Interface/Online/Announcements/FA_Killed_Merc"));
    r = klucc_route_key("FA_Killed_UCC", b, sizeof b); CHECK(r && !strcmp(r, "FA_Killed_Merc"));
    r = klucc_route_key("FA_NoFriendlyFireUCC", b, sizeof b); CHECK(r && !strcmp(r, "FA_NoFriendlyFire"));
    r = klucc_route_key("Online/FA_NoFriendlyFireUCC", b, sizeof b); CHECK(r && !strcmp(r, "Online/FA_NoFriendlyFire"));
    CHECK(!klucc_route_key("FA_Killed_Merc", b, sizeof b)); CHECK(!klucc_route_key("FA_NoFriendlyFire", b, sizeof b));
    CHECK(!klucc_route_key("XFA_Killed_UCC", b, sizeof b)); CHECK(!klucc_route_key("FA_UCC_FailedMission", b, sizeof b));
    CHECK(!klucc_route_key(0, b, sizeof b)); CHECK(!klucc_route_key("FA_Killed_UCC", b, 10));  /* no room: keep the game's key */
    /* return address window of the stock list routine */
    CHECK(klucc_ra_is_list(0x572086, 0x572050, 0x5721c1)); CHECK(!klucc_ra_is_list(0x572050, 0x572050, 0x5721c1));
    CHECK(!klucc_ra_is_list(0x4eb300, 0x572050, 0x5721c1)); CHECK(!klucc_ra_is_list(0x5721c1, 0x572050, 0x5721c1));
    /* key edge with debounce */
    memset(&k, 0, sizeof k);
    CHECK(!klucc_edge(&k, 0, 100, 150)); CHECK(klucc_edge(&k, 1, 130, 150)); CHECK(!klucc_edge(&k, 1, 160, 150));
    CHECK(!klucc_edge(&k, 0, 190, 150)); CHECK(!klucc_edge(&k, 1, 200, 150));                  /* bounce inside 150 ms */
    CHECK(!klucc_edge(&k, 0, 400, 150)); CHECK(klucc_edge(&k, 1, 420, 150));
    /* round change */
    CHECK(klucc_round_changed(10.0f, 300.0f, 0x2, 0x2, 1, 1));       /* clock jumped up */
    CHECK(!klucc_round_changed(300.0f, 299.9f, 0x2, 0x2, 1, 1));
    CHECK(klucc_round_changed(100.0f, 99.0f, 0x2, 0x4, 1, 1));       /* another index picked */
    CHECK(!klucc_round_changed(100.0f, 99.0f, 0x6, 0x4, 1, 1));      /* a UCC lost the flag: no new round */
    CHECK(!klucc_round_changed(100.0f, 99.0f, 0x2, 0x0, 1, 1));
    CHECK(klucc_round_changed(100.0f, 99.0f, 0x2, 0x2, 0, 1));       /* back into the round window */
    { float z = 0.0f, nan = z / z; CHECK(!klucc_round_changed(nan, 300.0f, 0x2, 0x2, 1, 1)); }
    printf("klucchide_test: %d checks, %d failed - %s\n", checks, fails, fails ? "FAIL" : "ALL PASS");
    return fails != 0;
}
