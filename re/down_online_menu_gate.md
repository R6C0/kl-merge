# Online get-up mash: a "menu / pause / shop / chat open" gate (offline research, 2026-10-26)

Nothing was run in the game, nothing was written to a game folder. Read-only disassembly of Dog Days kl2.exe
(capstone + pefile, scratch scripts only).

## Answer

The flag is the menu window system's open-window count:

    ws    = [[[0xdd265c] + 0x824] + 4]           ZXMLGUISystem, vtable 0xbaf2fc (check [ws] == 0xbaf2fc)
    mgr   = [[0xdd265c] + 0x824]                 ZMercsMenuElements, vtable 0xbb7dc8 (check [mgr] == 0xbb7dc8)
    count = DWORD [ws + 0x328]                   0 = no window open
    top   = DWORD [ws + 0x32c + 4 * count]       (windows are 1-based, top last; name = vtable slot 3, kls_win_name)

`count > 0` means "a menu page is open", and that covers the pause menu, the between-rounds weapon shop and the other
in-level pages. It is the same read klslot.c kls_menu_watch, klqol2.c kqb_top_is_arcade and klserver.c already do, so it is
a known-safe read (no game call, no write).

## Evidence

1. Push / pop code (read off the disassembly, ZXMLGUISystem methods):
   - open window 0x6bee50 (thiscall: name, 3 bools) queues; the real push is 0x6bf368..0x6bf375:
     `mov [esi+edx*4+0x330], ebx` (new window at index count+1) then `inc dword [esi+0x328]`.
   - close: 0x6bf281 `call 0x643ce0` then 0x6bf286 `add dword [esi+0x328], -1`; close-all: 0x6bf319 `mov [esi+0x328], ecx` (0).
   - the input router at 0x6beefa `cmp dword [esi+0x328], 0 / jle` and 0x6bef1c / 0x6bef5d read the top window the same way:
     with the count 0 the game does not route input to a window, with it above 0 the top window gets it.
2. Which windows are real windows on this stack: online.xml pages are opened by name through 0x6bee50. In kl2.exe the names
   `IngamePauseFA` (0xb5c530; refs 0x420988, 0x496ffc, 0x7040ca, 0x7ea150), `IngamePauseHeist` (0xb37108; 0x7040de, 0x7ea135),
   `FARespawn` (0xb5aa20; 0x704156), `FAStatus` (0xb17d68; 0x497120, 0x7041ce), `FABuyWeaponsNew` (0xb47ea4; 0x7558ce, the
   between-rounds shop, opened by code from MercsFAStatusReady) are all named in code. 0x7040a0-0x7042b3 is one function that
   strcmp-walks that list of window names (0x45ebf0 = name compare) and then calls 0x4aaf00: a "close these windows" routine.
   re/menus.md 4.2 lists the in-level pages (FAStatus, FARespawn, FADead, FARoundOverMenu, FABuyWeaponsNew / Category / Weapon).
3. Live logs in the repo (klauto's `windows: N [..]` line, logged when the stack changes, forced at script lines):
   `windows: 0 []` mid-round in build/claude_stage/run_T22brope.txt, run_T22rope.txt, run_v71_T1H.txt, run_v71_T1I.txt (F06 Arcade,
   the player is in a live round); `windows: 1 [HeistStatusLeaderboard]` / `[HeistStatusLeaderboard_EndGame]` at the round end;
   `windows: 2 [HeistStatusLeaderboard > QuitGameMenu]` (a pause-type dialog on top). So an ordinary round has count 0 and the
   HUD is not a window.
4. Not observed in any repo log: a pause window or the shop on the stack in a round (no run opened them). That the shop and
   pause are windows follows from points 1 and 2 (they are XML pages opened by name), not from a seen `windows:` line.

## Chat

I found no in-round text chat in stock Dog Days. The `Chat` strings are voice chat: `StatusChat` (0x74b7c4, ref 0x58c0b9) and
`LobbyChat` (0x77f42c, ref 0x58c1fa) are element names in one status-element update routine (0x58c0a0..) that asks the voice
service (vtable slots via [0x168e9e4] / session 0x168e598) whether a player is talking; `Online_Voice_Chat`, `Audio_Volume_VoiceChat`
are options. There is no ZEditControl user in code (the string at 0xb26778 has one ref, 0xae699d = RTTI). The exe imports
ToUnicode / GetKeyboardState (0x7d860c, 0x8cd098), i.e. text entry exists, but only inside menu windows (name entry, search
box) - those are on the window stack, so count > 0 covers them. If the owner's "chat box" is the Steam overlay chat or
Windows' own IME / text-input host, the game's data does not know about it: GetAsyncKeyState still reports the key, the
foreground window is still the game's, and no flag exists in kl2.exe. Only a check outside the game (GameOverlayUI.exe window
in front, `[Down] MashIgnoreOverlay`) could help; not researched. Confidence for chat = a game-side text box: high (covered by
count > 0); for the Steam / OS overlay: nothing readable.

## Confidence

- count > 0 = a page open (pause / shop / in-level menu / text entry in a menu): HIGH for the mechanism (push/pop code read,
  three other hook modules read it live), MEDIUM-HIGH that pause and shop are on it in an ONLINE round (not seen live, see 4).
- Risk: an online round may keep a non-modal page on the stack the whole time (an ONLINE-only HUD-like window), which would
  switch the mash off for good. Offline Arcade shows count 0 mid-round; online is unmeasured. Mitigation in the patch: log the
  top window's name the first time the gate blocks, and give the gate an ini kill-switch.

## Minimal patch suggestion (NOT applied) for klhook/kldown.c kld_o_keydown (about line 2283, before reading any key)

```c
/* a menu page is open (pause, shop, in-level menu, a text entry inside one): the Cover key / pad A belong to the page, not the mash.
   [[[0xdd265c]+0x824]+4] = ZXMLGUISystem (vtable 0xbaf2fc), +0x328 = open windows (re/down_online_menu_gate.md) */
static int kld_o_menu_open(void)
{
    DWORD gd, mgr, w, n;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c))) || !(mgr = klh_rd32(gd + 0x824)) || klh_rd32(mgr) != KLS_MENUMGR_VT) return 0;   /* unreadable: do not gate */
    if (!(w = klh_rd32(mgr + 4)) || klh_rd32(w) != KLS_WSYS_VT) return 0;
    n = klh_rd32(w + 0x328);
    return n > 0 && n <= 24;
}
```

and in kld_o_keydown, right after the `pid != GetCurrentProcessId()` test:

```c
    if (kld_o_menu_open()) return 0;      /* no press counts while a menu page is up (and the XInput read below is skipped too) */
```

kldown.c needs KLS_MENUMGR_VT / KLS_WSYS_VT (they are `#define`s in klslot.c at lines 149-150; klqol2.c already uses them, so copy
or share the same definitions). Both reads are plain klh_rd32 (guarded, no call into the game), safe off the game thread like the
other keydown reads. Optional: `[Down] MashMenuGate=1` (recommended on) per the every-feature-a-toggle rule.

One more point for the owner's pause-menu case: if the game thread is where kld_o_keydown runs, the stack is consistent; if
it runs on the fallback thread, a torn read gives n at worst one step stale, which is harmless.

## Verified from an existing ONLINE log (scheduled check-in, 2026-10-26 ~19:00 UTC; nothing run)

The risk above ("an online round may keep a page on the stack the whole time") is answered by the owner's game-folder
`KLHook.old.log` (10-25, the SL2 run of the 21:26 note: System Link, host alone with `[Lobby] MinPlayers=1`, DM01 in F01,
TEST build with klauto's `windows:` line, logged on every stack change and at script lines). Three online rounds, read-only:

    22:02:38.187  session: state 0x18 -> 0x19          (round 1 up)
    22:02:38.503  windows: 1 [FAWaitForPlayers]        (the online wait page, pushed at 0x17)
    22:02:38.680  windows: 0 []  x3                    (popped 0.5 s into the round)
    22:03:21.423  session: state 0x19 -> 0x1f          (round over)
    22:03:29.434  windows: 2 [FAStatus > StatusMoney]  (state 0x20 = the 30 s between-rounds status page)
    22:03:59.464  session: state 0x18 -> 0x19          (round 2)
    22:04:21.775  windows: 0 []  x4                    (script samples mid-round)
    22:05:30.361  windows: 2 [FAStatus > StatusMoney]  (state 0x20 again)
    22:06:00.405  session: state 0x18 -> 0x19          (round 3)
    22:06:00.883  windows: 0 []  x3

So in an online FA round the count is 0 while the round runs (every mid-round sample, three rounds, and no stack change was
logged inside a round), the pages the gate must see are on the stack when they are up (`FAStatus > StatusMoney` between
rounds; `FAWaitForPlayers > FAStatus_HostDisconnect` in the 21:25-21:50 host-alone runs that ended in 0x29), and the only
window that overlaps state 0x19 is `FAWaitForPlayers` for ~0.5 s at the round's start, before anyone can be down. The
"permanent non-zero count online" risk does not happen in System Link FA; the kill-switch `[Down] MashMenuGate=0` stays for
the unmeasured cases. Still not seen on the stack in any log: `IngamePauseFA` (nobody paused in a bench) and `FARespawn`;
their push goes through the same 0x6bee50 path, so they count the same way. Not measured: a round with 2+ humans (the wait
page stays up until every peer has loaded, still before any down) and the Steam / overlay cases of the Chat section.

0f8a924 left out the once-only log the mitigation above asked for; added by this check-in: the first time the gate stops a key read
in a hold, `down: online: mash presses ignored while the menu page '<top window>' is open (N on the stack; ...)` (kls_win_name of
`[ws + 0x32c + 4 * count]`, as klauto's `windows:` line; call-free). A page the player opened there is right; a HUD-like name would
mean the gate is wrong on that build. GCC type check 0 errors; not MSVC-built, not run.
