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
OWNER 2026-10-24: x4.5 the proposal; the default is a random heister, never Kane or Lynch (see Owner decisions below).
| Heister | Price | Rank |
|---|---|---|
| Default (random, not Kane/Lynch) | 0 | 0 |
| Dog Days J.C., Tommy, Pierre, Liam | 45,000 | 0-1 |
| Dog Days Jean, Elwood, Bud, Mitchel | 90,000 | 2-3 |
| Dead Men Ashkanan, Meldal, Red, Parker, Standen, Hutchison | 180,000-270,000 | 4-5 |
| Kane, Lynch | 450,000 / 540,000 | 6 / 7 |
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

## Owner decisions (2026-10-24, answers to 8)
1. Default heister: random from the pool, NEVER Kane or Lynch (they are hire-only).
2. A hire lasts ONE round: next round you are back on a random default unless you pay again.
3. Prices = section 5 x 4.5 (45k / 90k / 180-270k / 450k / 540k). Open check: is 540k reachable in one match's banked total?
   If not, the top rows are unreachable; ask the owner before rescaling.
4. Portraits, black and white like the gun cards (the peer's white shop, tools/kl_shop_cards.py): needs heister renders baked into
   the level .TEX the same way; text-only only as a temporary stage-1 step.
5. Bots hire too, by the same rules: price, rank, one round. Each bot needs its own money and rank (open: where a bot's banked total
   lives) and a pick rule (GUESS: the best affordable heister not already worn).
6. Dead Men maps first (the KLExpansion online.xml variants: 289299 B md5 7c8828ec, 292873 B md5 9aa3e4b6); stock maps later.
7. (one human menu visit for stage 1): not answered yet.

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

## Stage 0 research (2026-10-24, read only)
Nothing built or run. Addresses are quoted from repo notes unless marked. Inferences are labelled GUESS.

### Element-table headroom
- Capacity 0x13e8 = 5096 entries (kl2.exe): add at 0x7fad4f..0x7fad8d (`cmp ecx,0x13e8; jge` to `int3` 0x7fad8d). Same guard for windows
  (0x667e46), colour sets (0x47d62f), button graphics (0x53c76f). Entries are 8 bytes from +8, so the count field sits at 0x9f48.
- Real budget is 5000, not 5096 (hud_menu.md 1.1): the cursor over `DefaultFocus` asks for entry 5000 via 0x861720.
- Live `[Menu] TableLog` (build\klhook\live logs of 2026-10-15): a level load reads `table 2921 of 5096 (2781 elements, 93 windows,
  24 colour sets, 23 button graphics); 2079 free below 5000`. The main menu reads 5065 of 5096 (31 free). The table is rebuilt per scene
  (GUESS: new manager or reset per load). So a Hire window in a level's `Menu/online.xml` costs nothing in the frontend.
- Mapping: each GuiElement/Window/ColorSet/ButtonGraphic is one entry, in file order (ingame.xml, then online.xml). Template definitions,
  toggle children and Platform/ExcludeIn/Locale wrappers make none. Raw tags overcount (3331 GuiElement tags vs 2781 live; Platform pairs).
- All 36 installed zips have identical tag counts. online.xml: 1826 GuiElement / 40 Window / 12 ColorSet / 11 ButtonGraphic. ingame.xml:
  1505 / 55 / 12 / 12. Three online.xml byte variants exist (e20b2764, 7c8828ec, 9aa3e4b6). Patch01 ingame.xml has 9 more GuiElement
  (GUESS: add 9 if it overrides; precedence unproven).
- Size of a Hire window (GUESS from existing patterns): about 6-7 entries per row, 17 rows about 120, frame about 25, so about 150
  entries, roughly 7% of the headroom. A 4x4 card grid is similar. Suggested hard budget: at most 300 added per level, keep 1500+ free.
  Bot hiring adds no elements (hook logic only).
- To do: set `[Menu] TableLog=1` (not set in the live KLHook.ini), load one DM map, read the `menu: table` line before and after baking.
  Do NOT add a Hire window or button to frontend.xml or the overlay (31 free); put the entry button in the level's online.xml only.

### Bots hiring
- The banked total is ONE session number `[[rules+0x5f8]+0x38]`; 0x8ea990 subtracts the price from it. A bot has no banked total and no
  rank. Per-member columns: `+0x150+4i` carried cash (klbot.c:283), `+0x184+4i` rewards, `+0x1d4+4i` flags. Bots earn only into +0x150.
  The rank path (0x5103e0) reads the LOCAL profile only.
- No bot shop routine found: 0x8ea990 and 0x55d3e0 have no direct caller (RMC dispatch). All bots carry `Rifle_zastavam85`
  (bots_dynamic.md:189). Conclusion: bots do not spend money in stock DD, so a bot hire needs a hook-side wallet.
- Body switch uses existing paths: `klcrew.c` calls 0x783fb0(actor, root) on `[record+4]` for AI records with status 0, only ZFFActor,
  and NOT on the stock slot level (`klx_level_verdict==2`), which fits "DM maps first". `[Crew] Tries=3` is separate from the player's
  `klc_tries`. `[Crew] Random=1` draws without replacement from the 16 and never takes the player's body.
- One round comes free: the draw is re-made each round, so last round's hire drops with no revert (unlike the human, see above).
- Proposed rule (GUESS): wallet = hook-kept `bank[i]` (carried cash plus an equal share of the pool); rank = the human's; pick the dearest
  affordable heister nobody wears (`taken[]`); else the free random default, never Kane/Lynch; charge the hook wallet, never `+0x38`.
  Human resolves first, then bots in record order. "Once per match" needs a new host table (kl_cast), which does not exist.
- Unknown: any reader of `rec[3..5]` for AI; whether `+0x150` resets at round start; whether a DM root works on 7 actors at once
  (klcrew.c:27-33 "NOT SEEN"); HUD/voice following a bot hire (`Names=1` unestablished); must be inert online (other rules classes).

### Are the prices reachable
- Money is `[score+0x38]`; at round end `[score+0x38] += [score+0x30]` (0x5e001b). A dead player banks $0; the loot carried is not banked
  without an escape. Round 1 starts at $0, so only the default heister is possible in round 1 (fa_round.md:355).
- Measured escapes: $723,625 (50k escape + 650k loot + 23,625 time), $707,778 (Retomoto), $585,791 (DM03). Bots loot $255k-$840k each,
  so seven bots compete for the same loot; how the split works with seven bots is not read. Evidence is solo-human runs.
- Table (GUESS beyond the measured escapes): escaping every round banks about 0.6-0.7M after round 1, 1.2-1.4M after 2. Hire bought on
  the score page is spendable for round N+1.
- 45k to 270k rows are affordable after any escaped round. 450k (Kane) is affordable after one good escape; 540k (Lynch) is borderline
  ($585k clears it, a thin escape does not) and leaves little for guns, since a hire lasts one round. Rank gates (6/7, XP 25/100/400/
  700/1500/2100/2800) are the stricter lock; the owner's rank is unread.
- Bots start at $0 as well, so they also hire only from round 2 (GUESS). Round cap and life cost of an escape are unread.
- Verify: run one DM round with seven bots and read KLHook.log for the real per-round payout.

### Black-and-white portraits
- No stock heister pictures exist in any DD or DM archive checked (frontend scene, DM KaneAndLynch.zip, DD02 F02_Main.zip). Online.xml
  uses MercsGraphicFA only for status tiles and weapon cards.
- Renders exist: `tools/kl_portraits.py render` made `<work>\build\portraits\char_01..16.png` (RGBA, 256x304, flat light, software).
  1-8 Dog Days, 9-16 Dead Men (Kane 9, Lynch 10). Grey via PIL `convert('L')`, card palette from `tools/kl_shop_cards.py`.
- A picture is a scene entity (ZWINGROUP + ZWINPIC -> picture chunk -> .TEX id), not a file; XML alone cannot add one (menus.md:467).
  The Heister page used `ToggleImages Option="KLChar"` over `KLPic_*` entities, which live in the FRONTEND overlay scene only; a level's
  online.xml resolves against its own scene, so they do not exist in-level. That is unsolved.
- Route 1: overwrite pixels of existing gun-card tiles via `kl_shop_swap.patch_pixels` (DXT1, big 512x256). Cheap, but a gun row then
  shows a face; unsafe unless Hire uses tiles no shop row shows. Route 2: add about 14 new entities per level scene
  (GUESS: possible with kl_scene/kl_prp/kl_prmgraph/kl_texmat; unproven in any level; costs about 14 table entries). Route 3: text only.
- Bake first on DM01; check the ToggleImages binding on KLChar. The Heister page pictures were switched off after the menu table overflowed.

### Next decisions for the owner
1. Portraits: accept a text-only Hire list first, with pictures added later by Route 2 after a DM01 bake?
2. Bot wallet: draw on the human's pool, or an invented per-bot budget (hook-kept)?
3. Rank: keep the rank gate as the real lock (needs your FA rank read) with price-only as fallback?
4. Allow `[Menu] TableLog=1` and one DM map load to confirm the 2921 / 2079-free numbers?

### Owner decisions on stage 0 (2026-10-24)
1. Portraits: text-only Hire list first is OK; B&W pictures follow once a DM01 scene can carry the picture entities.
2. Bot money = what each bot takes from the heist: a hook-kept per-bot bank that grows by that bot's own escaped take (its carried
   cash `+0x150+4i` at escape - GUESS that this is the right column; open: does it reset at round start, is it zeroed on death) and pays
   for its hires. Never the human's pool `+0x38`.
3. Rank is the real lock (read the owner's FA rank via 0x5103e0), price-only as the fallback if the read fails.
4. The owner tests himself: no scripted live runs while he does. The TableLog check and the first Hire-window look happen in his own
   session (ask him to add `[Menu] TableLog=1`, or ship it in the stage-1 test ini).

## 7. Stage 1 BUILT 2026-10-26 (Arcade, Dead Men maps first) - NOT RUN IN THE GAME

Branch `hire-1026`. Code: `klhook/klhire.c` (included by klchar.c), wired in klchar.c (options Get/Set/Enabled, `klc_level_tick`, `klc_tick`, `klc_init`, `klc_level_open`). Menu: `tools/kl_hire_bake.py`. Ini: `[Hire] Enable=0` (default off), options row `hire`.

- Window `FAHire` (text only) in the level's Menu/online.xml, opened by a visible "Hire a heister" button in FABuyWeaponsNew after the Secondary button (same vertical group: keyboard Up/Down/Select and the pad). 16 ToggleText rows bound to the options `KLHire1..16` (= the KLChar number). Cost +43 element-table entries (2765 -> 2808 of 5000).
- A purchase is `Set(KLHire<n>, 1)`; it never goes through `klc_set`, so `[Character] Char=` is never written. Refusals (all logged, `hire:`): not Arcade / online / round running (state 0x12..0x1e) / one already hired / no body on this level / rank too low / not enough money. Charge: `[[rules+0x5f8]+0x38] -= price` via `klh_data`. A hire lasts one round; at the next round start (phase 2 -> 1) the body is the hired one or a random default (never Kane / Lynch). The swap is made by klchar.c's existing attach path (tries reset by a generation counter), never during the shop.
- Rank: the game's own `0x5103e0(xp)` with xp = profile + 0x15b8 + 0x90 (chain read from the callers of the shop's own lock, 0x7f74a0..0x7f74d1); the code bytes are checked first; if anything differs only the price counts (`[Hire] Rank=0` skips the gate).
- GUESS list: (1) the row's ToggleText re-reads Get after a Set (a refused row may still show HIRED if the widget caches); (2) the FATotal text redraws after our write and the game does not overwrite the banked total (same unproven write as klfedkit.c); (3) shop states 0x1f..0x28 and round states 0x12..0x1e; (4) the split of price and rank inside a band (the doc gave ranges only); (5) the row's right-hand data text ("-" / "HIRED for the next round") via TextReceiver, as the Mod settings page does; (6) the button's focus colours (own ColorSet KLHireCS, no focus bar).
- NOT BUILT: bots hiring (`[Hire] Bots=1` is read and said once, nothing else). Next: a per-bot bank kept by the hook from the bot's escaped take (`+0x150+4i`), same price table; needs a verified round-end hook and the reset behaviour of +0x150. Pictures in the window (stage 2).
- Install: stage with `python tools/kl_hire_bake.py stage` (staged zips + INSTALL / UNDO .bat under `<work>\build\hire_1026\`); the owner runs the .bat, which re-bakes from the live zips (backup `.before-1026hire`).

## 8. Stock maps + ONLINE hire, BUILT 2026-10-27 (branch worktree-wf_6b605c03-64c-1) - NOT RUN IN THE GAME

### 8.1 Dog Days stock maps F01..F09
`python tools/kl_hire_bake.py check|stage --stock` (live zips: `<DD>/Scenes/Locations/Fxx/Fxx_Main.zip`). The window has the 8 Dog Days rows only (a stock map has no wardrobe, `klhr_avail` refuses ids 9..16 there anyway). Element table headroom measured 2026-10-27: every stock map 2765 -> 2792 of budget 5000 (+27); the 16-row Dead Men version is +43 (DM01 2768 -> 2811). `stage --stock` writes only the baked `online.xml` per map plus `INSTALL hire window stock.bat` / `UNDO hire window stock.bat` and the tool copies into `<work>\build\hire_1027\`. The INSTALL bat refuses while kl2.exe runs (tasklist check in the bat and in the tool), re-bakes from the LIVE zip, and copies the zip to `<zip>.before-1027hire` only when that backup does not exist yet. UNDO moves the backups back. Hire (Arcade) then needs `[Hire] Enable=1` + `[Character] Enable=1`; AllMaps must be on for the character code to run on a stock map.

### 8.2 How the stock shop validates a purchase (read from kl2.exe, 2026-10-27)
Correction of the earlier premise: the shop money is NOT Sharable S+0x188 / Unsharable S+0x224 (those are carried in-round money). It is per seat, read by `0x622e10` (TotalLootMoney, array behind S+0x58) plus `0x639c10` (TotalRewardMoney); both are `thiscall(S, seat) ret 4`, S = `[rules+0x2c]` (vtable 0xbd5184, 12 seats). Rules slot 53 (0x5556f0) = their sum = the UI money.
The buy runs on the HOST: handler `0x55d3e0(rules, itemId)` sums the prices, returns SILENTLY when price > first + second, else `price < first` -> `0x6b1910(S, seat, price)`; otherwise `0x6b1910(S, seat, first)` then `0x7f6950(S, seat, price - first)` (both `thiscall(S, seat, amount) ret 8`; they mark the score object's dirty mask, so the new money REPLICATES to every client). A client therefore never writes its own money.

### 8.3 Online design (`klhook/klhire_online.c`, `[Hire] Online=0` default)
- Client presses KLHire<n>: local checks (hire on, not in a round, body available, not already hired) -> `HIREQ s<seat>r<row>k<rank>` through klnetchan (`knc_send`), nothing charged locally; a 6 s timeout clears the pending ask.
- Host (`m->role == 3` messages only): `klhro_decide` = round not running (session state != 0x19), seat in use and not the host's own, row valid, body available, nobody else wears it (`klco.p[].c`, the host's `klc_char`) or has hired it (`paid[]`), rank (as reported), money (the two game getters); then it spends with `0x6b1910` / `0x7f6950` EXACTLY like the stock handler and answers `HIREA s<seat>r<row>o<ok>m<reason>`. A repeated request for the same row is answered ok and charged once. The host's own press takes the same path without a message.
- Client on `o1`: `klhr_next = row` (row shows HIRED). At the next round's start (state 0x19 entered) every peer for itself: `klc_char = hired row` (the Heister page value is saved and restored when the round ends). klcharonline publishes `klc_char` (Steam `klx_look` + UDP 27414) and every peer applies it by entity; its Unique rule is the second guard on every screen. The host clears all `paid[]` at the round start.
- NO change of klcharonline.c / klnetchan.c / klsync / kldown / klucc is needed. `klcharonline.c` must be on (`[CharOnline] Enable=1`, `[Character] Enable=1`).
- Uniqueness ("one character per match"): covered at purchase (host refuses a character in use or hired) and at display (klcharonline Unique). Hired bodies are per round: the body is given back at the round's end, so a later round may hire the same one again. A peer without the klcharonline channel cannot be seen by the host.
- GUESSes (also marked in the code): G1 the shop is open whenever the session state is not 0x19 (other online state numbers unproven); G2 the seat in HIREQ is trusted (private match / friends); G3 the reported rank is trusted; G4 getters / spenders take S in ecx and the seat as the first stack argument (`__fastcall(S, 0, seat[, amount])` matches `ret 4` / `ret 8`); G5 the replicated score object redraws the client's money text; G6 `klc_char` set mid-match is picked up by klcharonline at the round start (its settle / tries rules apply). Pre-existing, not mine: `tools/kl_mod_options.py` fails its own assertion (duplicate feature id `onlineboard`).

### 8.4 Test recipe (two PCs or two instances, private match, host = player A)
1. SHIP/TEST dll on both; ini on both: `[Hire] Enable=1 Online=1`, `[Character] Enable=1`, `[CharOnline] Enable=1`, `[NetChan]` default. Both have the baked zips (INSTALL hire window stock.bat).
2. Play a round, collect money, reach the buy shop: `Hire a heister` row. As client press a row you can afford: log `hire-online: asked the host ...`; host log `hire-online: seat N hired X for $P`; client log `the host accepted`. The shop money must drop on BOTH screens (G5).
3. Press a row you cannot afford / below rank: host `refused, not enough money / rank too low`, client `the host refused`, money unchanged.
4. Both press the same row: the second is refused `another player wears or has hired him`.
5. Start the next round: both logs `round starts: I wear X`; the body shows on both screens (`charonline: heard peer ...`). After the round `the hired body is given back`.

### 8.5 Adding shop money (disassembled from kl2.exe, 2026-10-27; used only by [Bench] ShopMoney)
- The spenders CANNOT add. `0x6b1910` (first store) / `0x7f6950` (second) call the array ops `0x8bb7b0` / `0x6406f0`: `movsx eax,[esp+4]; lea edx,[ecx+eax*4+0x160 | 0x190]; mov eax,[edx]; mov esi,[esp+0xc]; cmp esi,eax; jbe -> sub eax,esi; mov [edx],eax` else `mov [edx],0`; then `or word [ecx+0x1fe], 0x80 | 1` (dirty mask). Unsigned compare: an amount above the store, a negative one included, CLAMPS the store to 0. So spend(-delta) would ZERO the money.
- The game has the add twin, identical wrapper shape (`sub esp,8 / push ebx / mov ebx,[esp+0x10] / ... / call 0x7dea30 (byte [ecx+0x1fc]=seat) / call array op / call 0x942b20 (notify) / call 0x57aca0`): `0x6cfdb0` AddLootMoney (first store) calls `0x688160` = `add [ecx+eax*4+0x160],edx ; or word [ecx+0x1fe],0x80`; `0x497ce0` AddRewardMoney (second store) calls `0x453cd0` = `add [ecx+eax*4+0x190],edx ; or word [ecx+0x1fe],1`. Both `thiscall(S, seat, amount) ret 8`. The only call sites of 0x688160 / 0x453cd0 are those wrappers (0x6cfdcf / 0x497cff).
- Getters: `0x622e10` = `add ecx,0x58; jmp 0x5f3b70` (`movsx eax,[esp+4]; mov eax,[ecx+eax*4+0x160]; ret 4`), `0x639c10` = `add ecx,0x58; jmp 0x411fe0` (same with +0x190). So first store = S+0x1b8+4*seat, second = S+0x1e8+4*seat, 12 seats.
- Code guard used by the hook: wrapper `0x6cfdb0` first 8 bytes `83 ec 08 53 8b 5c 24 10` and `e8 8c 83 fb ff` at 0x6cfdcf (the call to 0x688160). The page II judge (`klshoppage_online.c` kspo_judge) now compares the price with the getter sum (not klor on_money, which is in-round carried money). GUESS: that the 0x942b20 notify inside the add wrapper replicates to clients as for the spenders (same code shape, unproven online).

## 9. Hire PAGE in the stock shop (built 2026-10-27, NOT RUN IN THE GAME)

Owner: "make a damn shop page for the hiring, it's just a button". Code: `klshoppage.c` (block 'HIRE PAGE', `kspg_hire_tick`, `kspg_text_hire`, `kspg_hire_press`), `klhire.c` / `klhire_online.c` (refusal record `klhr_lastmsg`, accessors `klhro_waiting` / `klhro_enabled`). SHIP-safe: private vtable copies of the shop's elements (as page II), heap data writes, calls of klhr_set. No kl2.exe code byte changes.

Keys (KLHook.ini `[Hire]`): `Page=0` (recommended off until benched; needs `Enable=1`), `PageKey=123` (F12; F7 Unstick, F5 Ucc, F8 Inv/HostOpts, F9/F11 CharOnline are taken; refused if equal to `[ShopPage] Key`), `PageConfirm=1` (recommended on: first BUY arms the row 4 s, second BUY hires), `PageLog=1`. KL Mod Options row `hirepage`.

Facts used (read before): shop rows 0..35 in four tabs (Pistols 0..10, Shotguns 11..16, SMGs 17..27, Rifles 28..35); shown row `[0x154d80c]`, mode `[0x154d810]` == 2 = weapon list; selector row `[sel+0x90]`; text slot 24 of MercsShowInfoFAWeapons / MercsSendMessageWeapons; picture update slot 8 of MercsGraphicFA (PlayerIndex `[obj+0xc4]`); selector message slot 20 (BuyWeaponDialogVoodoo, then BuyWeapon after the confirm dialog). A press calls `klhr_set(ch,1)`: offline klhire.c (price, rank, one per round), online `klhro_set` (client asks the host, host judges and spends; wire format unchanged). Page works with `[ShopPage] Enable=0` (the tick, gate `kspg_gate_x(1)` and scan run on their own); with Page=0 nothing changes (`hireOn=0`, no wrapper acts, page II gate unchanged).

Layout: PageKey toggles `kspg.hire` (a third state; shownB forced 0 while up). Caption 'HIRE A HEISTER  [F12] stock page'; tab names DOG DAYS CREW (Pistols tab) / DEAD MEN CREW (SMGs tab), the Shotguns and Rifles tabs read '-'. Rows: Pistols rows 0..7 = KLChar 1..8 (J.C. Tommy Pierre Liam Jean Elwood Bud Mitchel), SMGs rows 17..24 = KLChar 9..16 (Kane Lynch Ashkanan Meldal Red Parker Standen Hutchison). Description: bio, hire price, rank needed, your rank, state (HIRED / already hired another / NOT ON THIS MAP / WAITING for the host / PRESS BUY AGAIN / REFUSED: last reason / rank too low). The stock BuyWeapon and BuyWeaponDialogVoodoo are swallowed (no gun, no money change by the shop). The big gun picture is hidden; stars show the rank need. Log lines `hirepage:` (shown/hidden, each press with row, heister, offline/online, result; each served text once).

GUESS list (all marked in the code):
1. Layout: 8 heisters per tab on rows 0..7 / 17..24, i.e. the tab's first page; a hidden second page of the list is not handled. Whether a tab with only '-' names behaves is unknown.
2. `BuyWeapons_Title` is the shop caption key (same guess as page II's hint); if never requested, the caption hint does not show.
3. `WeaponLocked` / `UnLocksWith` keys: the replacements ('see rank' / 'Gun lock, not used for hire:') assume these are the stock lock line pieces. The stock price, lock icon and star row belong to the CARRIER gun and cannot be replaced from a text key: the description says so and carries the real price and rank.
4. Star graphics: tag contains 'Star' (XML WeaponShopStar#01..06) to get role KR_STAR; the lit/dim rule (index below need) is a guess. No match = stars stay stock.
5. Picture index 99 hides the big picture (matches no row), as in page II's swap.
6. Name/description texts may be cached by the game until the cursor moves (page II has the same warning): after the key, move the cursor once.
7. Online: the shop gate `kspg_gate_x(1)` accepts the online FA rules (host Sv / client Cl vtables) when `[Hire] Online=1`; the selector message names are assumed identical online (page II G17).
8. Rank read `klhr_rank` runs from the text callback (cached 2 s): assumed callable on the draw thread like klhire_tick's game-thread call.

Test recipe (offline): Hire.Enable=1, Page=1 (Hire window baked, DM level for ids 9..16 or a stock map for 1..8), game: Arcade -> shop (weapon list). Press F12: caption reads HIRE A HEISTER, Pistols tab = DOG DAYS CREW with names. Move the cursor to Tommy, BUY (dialog may not show): log `hirepage: press ... ARMED`; BUY again: `-> HIRED for the next round`, description says HIRED; a second hire is refused ('already hired'). F12 again: stock pistols back and no gun was bought. Next round: the body is Tommy (`hire:` lines). Rank too low and money too low: description / log show the refusal.
Test recipe (online, Hire.Online=1, CharOnline on): host and client in a private match, shop between rounds. Client F12, hire a heister: log `hirepage: ... (online ...) -> asked the host, waiting`, then `hire-online:` answer lines; description WAITING then HIRED or REFUSED: <host reason>. Host presses its own: judged locally. Check round 2 body on both seats. Bench: the TEST dll (klauto) can hold the key (VK 123) in a script.
