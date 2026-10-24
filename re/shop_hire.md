# Hire tab in the buy shop - research (2026-10-24, read only, NOT BUILT)

Nothing here was run or built. Facts come from exe disassembly (kl2.exe, base 0x400000), the repo and F02_Main.zip. Inference is marked GUESS.
Spot-checked by the synthesizer: shop_plan.md:5-11 (wish), online.xml lines 3152-3153 / 3394-3395 / 3683-3684 (dead ZW_TAB SendMessage
aimed at FABuyWeaponToggler, which does not exist), klfedkit.c:395 (`KLFK_S_TOTAL 0x38`, the shop buys from it, 0x8eaa4a).

## 1. Owner wish (2026-10-24 ~14:45, re/shop_plan.md:5-11)
"people can buy their heister dependent on their rank e.g. go as kane but it costs them money to 'hire' them to be that guy for the
heist" - "character screen as in the buy shop screen". Now asked for as a SEPARATE "Hire" tab in the buy shop. Open from the wish: free
default heister, price/rank table, bots, online.

## 2. What exists today
**Shop page (data, per level).** `Menu/online.xml` in each level zip: FABuyWeaponsNew (line 3010), ...Category (3160), ...Weapon (3414),
BuyWeaponDialog (256). The file is byte-identical in F01-F09 (289201 bytes, md5 e20b2764); element table 5096 slots, overflow = int3 at
0x7fad8d (re/menus.md 2.5; headroom NOT established, kl_expansion.py:1114). A new window needs no code (re/menus.md:215-218).
**Categories are code.** Range, row bases and text keys are hard-coded in hashed .text/.rdata: 0x534530 (init), 0x7d2db0 + table
0x7d2f00 (clamps), 0x7e4c30 (category -> row base 0/11/17/28), 0x50c630 + 0x50d2d8 ('Weapon%d' keys, bounds 11/17/28/36). A 5th
category cannot be added in a SHIP build.
**Rows.** 36 x 24 bytes {item, ammo, price, rank, tier, DLC} at 0xbd1f68 (.rdata, hashed); readers 0x6a5260 price, 0x8a3e40 rank, 0x6a9d50
DLC, 0x808220 IsLocked (re/shop_plan.md:28-31, 33-70). Suits: float table 0xbd22cc, prices 0/60k/120k/160k, no rank (0x8736f0).
**Buy chain.** selector 0x7f73d0 (already owned -> DLC/rank 0x7f74f6 -> price 0x7f7551 -> 0x808220 -> BuyWeaponDialog 0x6bee50) ->
handler 0x76b840 case 8 -> RMCBuyWeaponPack (id read from the selector object) -> Arcade server 0x8ea990. It is weapon-only; data cannot
point the confirm at another action (0x76b8b9).
**Money.** Arcade (session +0x5c==4, +0x54 not 2/3, gate 0x7f6850): ONE dword `[[rules+0x5f8]+0x38]` (banked total). Read 0x7f7434, spent
0x8eaa3f..0x8eaa4a (`cmp`, `jg` skip silently if short, `sub`). Not the carried loot. Heap data, so the hook may write it (precedent
klfedkit.c:716,738 `klh_data(score+0x38,...)`; live status of that write is NOT PROVEN, re/fed_kit.md:9).
Online / private match is a different store: server 0x55d3e0 spends per-client replicated arrays (0x622e10 + 0x639c10, setters
0x6b1910 / 0x7f6950); UI money = rules vtbl slot 53 (0x5556f0). `[score+0x38]` is not the shop money there (re/netcode.md:219-223).
**Rank.** FA experience rank 0..7 of the local profile, not the in-round hero rank: 0x1686e60 -> 0x4d04c0(0) -> vtbl+0x140 -> 0x78a8b0
(+0x15b8+idx*0xc8) -> word +0x90 ExperiencePoints_FA -> `0x5103e0(xp)` (cdecl). Thresholds {25,100,400,700,1500,2100,2800}, else 7
(returns 7 under the 'HiddenDemo' test). The hook has no rank reader today (grep klhook found none).
**Heister page / wardrobe (hook, SHIP-safe).** klchar.c wraps the options object (private heap vtable over stock 0xbb7dec; slots 2 Get
0x504b40, 5 Set 0x472450, 9 IsEnabled 0x4b4560; slot 10 must stay unwrapped) and exposes KLChar 0..16 (1..8 Dog Days, 9..16 Dead Men
FA crew), KLMask, KLOutfit (klchar.c:9-35,116-190; re/wardrobe.md). Apply = write heroes[] at rules+0x208, byte rules+0x33d, call slot
137 (0x8f5e90), look via 0x88c810; gated Arcade + ZGameRulesHeist (0xbd3514) + local player type 2 and not busy; retry cap `klc_tries` 3,
reset only when rules/player changes. The rules object and player persist across rounds of one load (states 0x20 -> 0x23..25 -> 0x16 ->
0x18 -> 0x19; KLHook.log 23955-24342; re/fa_round.md:444-445), so a change at the score page applies for the next heist.
**Pictures.** Menu pictures are scene entities (ZWINPIC) named by `Graphic=`, not files. The level online.xml has no heister portrait
entity; the 16 portraits (kl_portraits.py) live in the FRONTEND overlay (Overlay\Scenes\kaneandlynch.zip), not the level (re/menus.md 2.7).
**Peer work.** kl_shop_cards v3 repaints only .TEX/.LOC of the existing tiles (staged, not installed); keep Hire off FAStatus_Weapon*,
WeaponShop* tiles and Weapon0..35 LOC leaves.

## 3. Options
**A. 5th category bar on FABuyWeaponsNewCategory.** Needs patching the hashed range/base/key code above. REJECTED: SHIP builds refuse
it, and the 36-row table cannot grow, so a category would have no rows anyway. Effort n/a. Risk: certain tamper refusal.

**B. Separate "Hire" window opened from the Buy page (XML) + hook-served option.**
- XML/data: a new Window in each level's online.xml; reach it by turning the dead ZW_TAB SendMessage pair (3153+3154, 3395+3396,
  3684+3685; CRITIC: BOTH lines are dead, 3154's receivers FABWHeader* do not exist either, and they sit inside <Platform PC_KEYBOARD>
  only, so a gamepad (PC_GC) has no route) into an OpenWindow, or add a visible button. CRITIC: the only stock `OpenWindow ... ActivateButton=`
  is inside an XML comment (online.xml:2429), so a live ActivateButton OpenWindow on this page has NO precedent; use the visible-button
  pattern (BuyWeaponsButton_PC / main-menu OpenWindow with FocusGraphic) as the first attempt. Rows are ToggleText/ToggleImages bound to an Option served by klchar's existing private
  vtable (the number of `<Text>` children sets the range). Names/prices as literal texts. Text-only first (no portraits).
- Hook code (CRITIC: klc_names/klc_upper/klc_value/klc_keys are fixed 3-element arrays and klc_which tests i<3, klchar.c:118-121,
  so KLHire means editing those; klc_set persists every set to ini [Character] and clamps to klc_upper, so a hire must NOT go through
  klc_set or it overwrites the owner's Heister-page pick). New option (KLHire) in the Set wrapper: rank test (call 0x5103e0), afford test, deduct `[score+0x38]`, set `klc_char`,
  log every charge. Price/rank table in an ini (not hashed). Reset `klc_tries` per round.
- SHIP-safe: yes (heap data writes, calls to game routines; keep klc_same_code check on 0x5103e0/0x8f5e90/0x88c810).
- Stock maps: online.xml identical in F01-F09 (CRITIC re-checked: 9 zips, 289201 bytes, md5 e20b2764, all equal), but the INSTALLED
  KLExpansion zips are two other variants (DD01-09/T01/DM05A/DM06B/DM11B/DM01B 289299 bytes 7c8828ec; DM01/02/03/06/09* 292873
  bytes 9aa3e4b6), so the bake is per variant, not one file. One bake per level zip (kl_hud_menu level/check-level) or Patch01 `Menu/online.xml`
  (override precedence only ASSUMED). Private match: needs a route to the rules object (not verified).
- Effort: medium (XML window + option + gate). Risk: element-table headroom unknown; whether an OpenWindow fires while
  MercsFASelectorWeaponsPC owns input (GUESS, live test); options vtable is null on a `-o DefaultScene` boot until the menu creates it
  (re/menus.md:620), so the autotest cannot reach it without a menu visit; ONLY change existing elements if the ~4-slot margin
  (hud_menu.md 1.1) is the real limit.

**C. Hook-drawn overlay card (shop_plan Stage 4).** Hook draws a list and takes a key in state 0x20, does the whole transaction.
- XML/data: none. Hook: draw hook + input capture + the B logic. SHIP-safe: yes if it only draws and writes data.
- Stock maps: independent of the level XML, so uniform on all maps. Effort: high. Blocked by re/hud_board_b.md B-P1 (does the HUD draw
  and take input in state 0x20; never run). Risk: stale FATotal/PackagePrice text after a hook write (GUESS).

**D. Carrier rows (money authority stays the game's).** Rebadge N existing gun rows (rank r>=0, prices 2k..245k, shop_plan table) as
heisters via .LOC/.TEX; the stock selector gives stars, locks, afford test, dialog and the server subtraction free. The hook observes
the commit (rec[3]/rec[4] or bytes 0xced638/0xced639 become a carrier row while money fell by its price), then restores the gun
(needs a free pool object else int3 at 0x538f02) and sets klc_char. It is NOT a separate tab (rows live in gun categories), eats gun
rows, and has a revert race. Works online for money. Effort medium, risk medium; keep as fallback / online money path.

## 4. Recommendation and staged plan
Recommend **B** (separate Hire window), with C as the fallback if the live gate fails, D only if online money is wanted early.
- **Stage 0 (offline, free):** read the element-table usage statically for a stock level; decide the window's element count.
  DONE 2026-10-24 (scheduled check-in, `re/menu_count.md`, `tools/kl_menu_count.py`): a level set (Patch01 ingame.xml +
  the level's online.xml, Arcade or FA) is ~2775 of 5096 entries, so an in-level Hire window has ~2200 entries of room;
  templates 319 of 512. The FRONTEND is the tight one (live 4793 keyboard / 4990 gamepad, 502 of 512 templates): keep
  Hire out of frontend.xml. ESTIMATE until K0 reads the live count. Also: the tokenizer is not XML - no text between tags,
  no `<?xml`, first `-->` closes a comment, first duplicate attribute wins (`re/menu_count.md` 3).
- **Stage 1 (solo, host-only, Arcade, kl_online()==0):** smallest live proof, three steps, one human menu visit:
  (a) put ONE test window "Hire" in F01's online.xml with a single ToggleText on Option KLChar (exists already, so no new hook code),
  reached through the repurposed ZW_TAB element; check it opens from the Buy page and the value changes; (b) read
  `[[[0xdd265c]+0x824]+0x9f48]` there for headroom; (c) confirm the body changes at the next round (klchar log 'body:').
  Then add the charge: rank via 0x5103e0, deduct `[score+0x38]`, free default heister = current Char, hire lasts one heist (paid each
  round; with [Hire] Enable=1 the Heister-page value is only a wish until paid). Log "hire: <name> $P total A -> B rank R".
- **Stage 2:** all 9 stock maps + KLExpansion maps (bake order vs kl_shop_cards fixed), private match route, portraits (scene edits, or
  keep text only).
- **Stage 3 (needs owner OK, after stages 1-2):** "once per match" via a host-kept table (kl_cast); bots (see 6).
- **Stage 4 (online, later):** peers publish the wish in lobby member data, host arbitrates, apply via heroes[session] + 0x74ee10;
  money through game setters (0x6b1910 / 0x7f6950) or option D.

## 5. Money / price / rank table - PROPOSAL for the owner (not read from anywhere)
Rank is the FA rank 0..7 above; money is the banked total (stock gun prices 2,000-245,000, suits up to 160,000).
| Heister | Price | Rank |
|---|---|---|
| Default (your current Char) | 0 | 0 |
| Dog Days J.C., Tommy, Pierre, Liam | 10,000 | 0-1 |
| Dog Days Jean, Elwood, Bud, Mitchel | 20,000 | 2-3 |
| Dead Men Ashkanan, Meldal, Red, Parker, Standen, Hutchison | 40,000-60,000 | 4-5 |
| Kane, Lynch | 100,000 / 120,000 | 6 / 7 |
CRITIC: klsteam.c:31-53,63 forwards GetStat and fails only SetStat/StoreStats, so the rank READ (0x5103e0 on the profile word) works
on every map; only the RISE is blocked on non-stock levels in SHIP builds (and always in TEST builds).
Rank gates need the rank to actually rise on expansion maps: klsteam.c blocks SetStat/StoreStats off the stock slot level (GUESS: the
in-memory word still rises; owner's current rank unread). Fallback: price only, no rank, until verified.

## 6. Bots, once per match, online
- Arcade: one human and eight distinct heroes, so "once" holds by construction; nothing is tracked in code (re/characters.md 6).
- Bots never take the worn body when [Crew] Random=1 (klcrew.c excludes worn model and Char; 15 free characters for 7 bots; only on
  non-stock levels, klx_level_verdict==2). Without Random=1 stock bots keep Dog Days bodies; slot 137 gives the AI who wore the hired
  Dog Days model your old one. For a Dead Men body that slot's AI keeps its Dog Days body.
- Voice follows the body (rules+0x33e table, klc_voice_swap); HUD name stays the slot's C1..C8; Kane/Lynch own barks are opt-in, NOT RUN.
- Online: body, mask, outfit not replicated; Steam id -> session number unknown (blueprint 7.4 q2); needs host permutation. Later.

## 7. Risks
1. Element-table overflow = hard int3 (0x7fad8d); headroom in a level ~2200 entries by the static model (`re/menu_count.md`, ESTIMATE). 2. Input focus of a repurposed ZW_TAB unproven. 3. Slot 137 timing
at state 0x24 with the player transiently gone (GUESS: tick waits; re/antitamper.md 5.4 unresolved); klc_tries cap 3 silently drops the
4th hire. 4. Hook write to `[score+0x38]` may not refresh FATotal until a redraw; double-purchase guard is ours; the total can go
negative, and the stats commit (0x68b930) records the lower total locally. 5. Patch01 precedence unproven, so bake per zip and keep
backups (suffix `.before-...`); bake order vs the peer's kl_shop_cards. 6. Online money differs, so Stage 1 is Arcade only. 7. Dead Men
bodies need KLWardrobe.ini and the chunk table (CHUNK_SAFE 69,632) so they exist only on maps that carry them; on stock maps only
Dog Days bodies may be hireable until proven. 8. Greying out a taken/locked entry is impossible from XML alone (re/menus.md 7.3).

## 8. Open questions for the owner
1. Free default heister: your current Heister-page pick? 2. Hire per round (pay each round) or for the whole match?
3. Prices and rank gates: is section 5 close? 4. Text-only list first, or wait for portraits? 5. May bots take a hired heister's body
after the round? 6. Should Hire work on the 9 stock maps from the start, or Retomoto/expansion maps first? 7. Is it acceptable that
the stage 1 live test needs one human menu visit (the autotest cannot reach the shop)?

## Critic pass (2026-10-24)
Checked read-only against kl2.exe, the repo and the 9 stock F0x_Main.zip plus the installed KLExpansion zips.
**Confirmed (exe bytes / files):** money cmp/jg/sub at 0x8eaa3f..4a on `[[rules+0x5f8]+0x38]`, read 0x7f7434 `mov ecx,[eax+0x38]`; int3 at
0x7fad8d; 0x5103e0 is cdecl with thresholds 25/100/400/700/1500/2100/2800 and the 'HiddenDemo' string at 0xb891f0; 0x78a8b0 =
`arg*0xc8 + this + 0x15b8`; shop rows at 0xbd1f68 are 24-byte {item,ammo,price,rank,tier,DLC}; FABuyWeaponToggler is never defined
(6 references, 0 definitions); online.xml identical in stock F01-F09; Patch01.zip holds only menu/frontend.xml + menu/ingame.xml
(so online.xml override there stays an assumption); a level online.xml already binds ToggleText to Option names (MP_Weapon_Screen,
lines 3183-3450), so option-bound ToggleText in-level is a stock pattern; klchar apply gate (Arcade, rules vtable, type 2, not busy,
settle, tries<3) as described.
**Corrected in place:** ZW_TAB is a PAIR of dead lines and keyboard-only; OpenWindow+ActivateButton has no live precedent; the
KLHire plumbing cost and the ini-overwrite trap; the expansion zips carry two other XML variants; rank read works (GetStat forwarded).
**Added gaps (not in the draft):**
1. REVERT: klc_level_tick returns at once when Char, Mask and Outfit are all 0 (klchar.c:~323). "Hire lasts one heist" therefore cannot be
   undone by setting klc_char back to 0 - the swapped rules+0x208 entry, rules+0x33d and the worn body stay. A revert must write the
   free default (a non-zero Char) or re-run the attach explicitly; if the owner's default is 0 (stock), the stock body must be saved first.
2. TRIES BUDGET: `tries` (cap 3) is spent per attach call, not per failure, and is reset only on a new rules/player object, so three
   hires (or one hire plus retries) in one load exhaust it; reset it when KLHire changes.
3. TIMING: the tick applies as soon as Char differs from the worn model while player type==2 and not busy, i.e. possibly DURING the
   shop, not "at the next heist"; whether the body swap mid-shop is harmless is unproven.
4. Options object lifetime: klchar.c says it is deleted per scene and re-created lazily; in-level it evidently exists (MP_Weapon_Screen
   bytes live beside it, menus.md:296-300) but a KLHire window has never been read there.
5. Missing option E (untested): put the Hire window in Patch01 menu/ingame.xml (one file, all maps) and keep only the entry button in
   each online.xml; needs proof that a level loads Patch01's ingame.xml windows and that online.xml can open them.
**Still unverified (needs a live probe):** element-table headroom (`[[[0xdd265c]+0x824]+0x9f48]`); a visible OpenWindow button on
FABuyWeaponsNew opening a new window while MercsFASelectorWeaponsPC owns input; a KLHire/KLChar ToggleText in an in-level window
(options object present, vtable installed by klc_options_tick); `[score+0x38]` write visible in FATotal and not overwritten by the
server's own sync (fed_kit.md:9 says the write itself is not proven live); body swap at the score page (state 0x20) with the player
type/busy flags; Patch01 precedence for online.xml; gamepad route; private-match rules-object route; owner's real FA rank.
