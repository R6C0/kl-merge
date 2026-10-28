# Keybinds + discoverability UI (T1, 2026-10-28)

Static research only. Marks: CERTAIN = read in code/ini this session, GUESS = not benched or inferred.
Week plan names re/keybinds.md; this task's file is re/keybinds_ui_1028.md.

## 1. Key inventory (every key the hook reads)

All via user32 GetAsyncKeyState (looked up at run time), foreground-window gated, edge detected, not consumed. CERTAIN.

| Key (default) | File:line | Feature | Ini | Default | Arcade / online |
|---|---|---|---|---|---|
| F6 (live ini: P) | klshoppage.c:988 | Buy Weapons page I/II | [ShopPage] Key, Hint | Enable=1 live | Arcade + online (OnlineLook/Apply) |
| F12 | klshoppage.c:980 | Hire a heister page | [Hire] PageKey, Page=1, Confirm | Page OFF live (key absent) | Arcade + online (klhro_set) |
| F5 | klucc.c:182 | Undercover cop ping/accuse | [Ucc] Key, Pings, Accuse | off | online |
| Insert | klucchide.c:322 | UCC reveal | [Ucc] RevealKey | off | online |
| F7 | klunstick.c:143 | Unstick (back to last free place) | [Unstick] Key, Enable, Auto | on live | offline only (online returns early) |
| F7 | klhostopt.c:257 | Host: cycle map set | [HostOpts] KeyMap, Keys=1 | Enable=1 live | host/lobby; GUESS fires in-round too (no gate found) |
| F8 | klhostopt.c:258 | Host: AI heisters toggle | [HostOpts] KeyAI | same | same |
| Delete | klhostopt.c:259 | Host: cycle map pool | [HostOpts] KeyPool, [MapPool] | same | same |
| F8 | klinv.c:186 | Gun shelf | [Inv] Key, Enable | Enable=0 | Arcade offline only |
| F9 (Shift reverses) | klcharonline.c:439 | Online character cycle | [CharOnline] KeyChar, Keys | Enable=1 live | online only; ignored with hire on |
| F11 (Ctrl = outfit) | klcharonline.c:440 | Online mask cycle | [CharOnline] KeyMask | same | online only |
| E + W | klfreeclimb.c:669 | Free climb at ledges | [Climb] Key, Enable | on live | only where level .ANM has clips; not online gated |
| none | klclimb.c:1397 | Edge climb (dwell) | [EdgeClimb] Key=0 | n/a | |
| E (hold) | kladren.c:1262 | Adrenaline: help downed AI heister | [Adrenaline] UseKey, NeedUse | on live | |
| C | kldown.c:2952 | Down: mash to get up | [Down] MashKey, MashPad | | |
| G | klgrenade.c:278 | Grenade throw | [Grenade] Key, Throw=1 | on live | |
| F / G / H | klcopsquad.c:88 | Local cop squad orders (follow/hold/attack) | [CopSquad] KeyFollow/KeyHold/KeyAttack | off, NOT run live | local squad only |
| J | klsabotage.c:47 | Van hold (UCC host) | [Sabotage] Key, VanHold | 0 | |
| 0 (off) | klqol2.c:395 | Heist-mode menu 5 DOWN taps | [QoL2] HeisterKey | off | menu only |
| Tab | klhud.c:1626 | Scoreboard while held | [HUD] TabList | hard-coded | |
| Alt+F4 | klhook.c:1197 | FastExit | hard-coded | | |
| various | klcam.c:106 | Log-only diagnostics (X, mouse, C, LShift, F9 MARK) | | | not a feature |
| TEST only | klauto.c | DIK scripting, kla_key_held | | | not shipped |

Not keys: [Net] BuildKey (lobby key), kltalk KeyGap.

## 2. Stock Dog Days binds (CERTAIN, compiled GameplayInput string, kl2.exe file offset 0x74ff1d; re/camera.md R2.1)

Mouse L fire / R aim / wheel. E use, LCtrl crouch, C cover, G grenade, Y point of interest, T teammate info, P pillpopping, X pulse check, R reload, F close combat, Q cycle weapon, LShift+Space sprint/escape, B briefing, Esc, Return, O objective, WASD, CapsLock walk, Tab scores. No stock F-keys, Insert, Delete, H, J, Home.

## 3. Clashes

CERTAIN unless marked.
1. F7: Unstick + HostOpts KeyMap + ReShade PresetShortcutKeys 118 (live ReShade.ini `118,0,0,0,119,0,0,0`). Three actions on one press.
2. F8: Inv + HostOpts KeyAI + ReShade preset 119. KL_MOD_SETTINGS.txt documents F7/F8 as looks and is stale about the hook uses.
3. F10: Neural/Uplift vs ReShade EnableKey=121. Home/Print/`'` also ReShade.
4. CopSquad F = stock close combat, G = stock grenade AND [Grenade] Key. Real clashes (feature is off by default).
5. F12 may be the Steam screenshot key (GUESS).
6. By design, not bugs: E shared by Climb/Adrenaline/stock use; C mash = stock cover; ShopPage P = pillpop but shop-mode only; CopSquad H vs QoL2 HeisterKey H are in disjoint contexts (round vs menu).
7. HostOpts keys poll every 30 ms with no lobby gate found (GUESS that they fire in-round offline; the loop reads: window front and role not client).

Context groups: shop-only (F6/P, F12), menu-only (HeisterKey), in-round (Climb, Adren, Mash, Grenade, Unstick, Inv, CopSquad, Sabotage), host/lobby (F7, F8, Delete), online-only (F9, F11, F5, Insert).

## 4. UI surfaces we control (CERTAIN they exist)

- Hire page, klshoppage.c: kspg_text_hire (tab names "DOG DAYS CREW" / "DEAD MEN CREW"), kspg_h_desc, kspg_h_keyname (F1-F24, A-Z, 0-9), kspg_h_ch, kspg_hire_press, kspg_hire_tick (key edge, 250 ms gate), kspg_gate_x(hire). Caption hints appended in kspg_text: "  [%s] page II", "  [%s] hire" (caption key BuyWeapons_Title: used by code, GUESS that it is the only caption).
- Page II: [ShopPage] Hint/TabNames, KLShopPage.ini [Tabs], private ring kspg_ring.
- In-game "Mod settings" window klset.c: 8 ToggleText rows + KLSAdren/KLSNext/KLSHMap/KLSHOpt. FULL: the window is at the 9-row guard max and the menu manager has 5096 slots with a 5000 budget (re/hud_menu.md 1.1). Do not add menu windows.
- External Tk tool tools/kl_mod_options.py (rows labelled "(recommended on/off)", --check-rec, --check-ini; re/mod_options.md; kl_mod_options_test.py).
- HUD: klhud*.c; centre announce klhud_popup.c.
- Game announce primitive 0x468430(elem, text, seconds), thiscall ret 8, elem = [[gamedata+0x15dc]]+0x10a8 (ZFAAnnouncementDisplay), code head `56 57 8b 7c 24 0c 8b c7` checked with klu_same_code. Three copies exist: kluc_show_now (klucc.c, with queue/busy), kladren.c KAD_ANNOUNCE, klhud_popup.c KLPU_ANNOUNCE.
- Beeps in klhostopt / klcharonline; KL_MOD_SETTINGS.txt in the DD folder (stale).

## 5. Design

### 5.1 [Keys] section (GUESS: not built)
New klkeys.c, `klkeys_init()` called early in the klh_tick init order (before kus_init/klho_init/klinv_init; modules are #included in klhook.c lines 701-767, ticked 1242-1287). It reads once with GetPrivateProfileIntA, exposes `int klkeys_get(const char* name, int def)`. Each module keeps its own [Section] Key= as an override: precedence = module key if present, else [Keys], else default. Accepts decimal or 0x hex (as klqol2 does) and a name parser reusing kspg_h_keyname in reverse.

Proposed default map (avoids stock keys and ReShade F7/F8/F10/Home/Print/`'`):

| Feature | Old | New default |
|---|---|---|
| Page II | F6 | F6 (unchanged; live ini P stays) |
| Hire page | F12 | F12 (owner may move if Steam overlay clashes) |
| MOD CONTROLS page | new | F4 |
| Unstick | F7 | Backspace-free: U |
| Host map set | F7 | PgUp |
| Host AI heisters | F8 | PgDn |
| Host map pool | Delete | Delete (unchanged) |
| Gun shelf | F8 | End |
| UCC ping | F5 | F5 |
| UCC reveal | Insert | Insert |
| Char / Mask online | F9 / F11 | unchanged |
| Sabotage | J | J |
| CopSquad | F/G/H | Z / V / B (GUESS; free in stock) |
| Climb / Adrenaline / Mash / Grenade | E/E/C/G | unchanged (stock-shared by design) |

Plus: HostOpts keys act only when in lobby/pre-round (needs a state read; GUESS where) or with Ctrl held. Optional owner bat (never written by me) to move ReShade F7/F8 shortcuts.

### 5.2 Boot clash detector (GUESS)
After all inits, klkeys_check(): for every enabled feature collect VK + context group, klog a WARN when two enabled features in the same context share a VK, and when a VK matches a stock bind list or ReShade.ini shortcut (read-only parse of ReShade.ini PresetShortcutKeys/EnableKey). Log only; never changes behaviour.

### 5.3 MOD CONTROLS page (GUESS; never benched)
A third carrier state next to page II and hire: `kspg.ctl`. Reuse hire machinery in klshoppage.c: toggle by a key edge in kspg_hire_tick (new `[Keys] ControlsKey`, default F4, ControlsPage=1 "(recommended on)"), gate with kspg_gate_x, add `kspg_text_ctl` dispatched from kspg_text (caption "  [%s] controls" appended next to the existing hints) and its description in kspg_h_desc style, through the same kspg_ring. Row table (static array, 8 rows per tab, 2 tabs: "IN ROUND", "HOST / ONLINE"): name = "<Feature>  [KEY]", desc = what it does, Arcade/online scope, state "ON/OFF (ini [Section] Key)". State from each module's enable flag (klho_get etc.; online via kl_online()). Pressing BUY is swallowed via the existing BuyWeapon/BuyWeaponDialogVoodoo intercept (informational). Offline-only features shown "Arcade only", online-only "Online only". Works anywhere the Buy Weapons shop opens (9 stock maps, Dead Men grafts, online host/client) because it is the same carrier as page II; client must run the carrier (OnlineLook path).

### 5.4 One-line hints (GUESS)
Factor one `klmsg_say(text, seconds)` from the three announce copies (kluc_show_now is the most complete: pending queue + busy check). First time a feature becomes usable per session, say once: "F6 page II  F12 hire  F4 controls". Gate with `[Keys] Hints=1 (recommended on)`.

### 5.5 Toggles (CERTAIN rule)
New toggles: [Keys] ControlsPage, Hints, ClashLog. Add Mod Options rows in tools/kl_mod_options.py with matching defaults so --check-rec and --check-ini agree; document in re/mod_options.md and KLHook.ini; regenerate KL_MOD_SETTINGS.txt from the same table.

## 6. Implementation plan
See ranked steps in the structured result. Verify: build, kl_mod_options --check-rec/--check-ini, debug/check.py, then one bench per surface (Arcade F01 slot, online host, online client). Nothing here was run.
