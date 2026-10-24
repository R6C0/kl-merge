# Shop 36-row cap: can it go? (research 2026-10-24, static only)

Owner asked "try and get rid of the cap". Workflow wf_7f897760-b16: three routes + judge. Judge verdict first, then the route reports.

## Judge verdict

**Verdict: build a staged combo, mostly Route 3 (catalogue sets), with Route 2's text and hand-over parts folded in. Drop Route 1 for SHIP.**

I ran only static checks on kl2.exe. I changed no files in the repo and launched nothing.

## What I checked myself in kl2.exe

| Claim | Result |
|---|---|
| Route 1: the table is read by about 21 immediates in about 11 functions | CERTAIN. A raw scan of .text for dwords in 0xbd1f68..0xbd22d0 finds 24 hits. 21 are table fields, covering 0x4107a7/ae/d6/dd, 0x6a5278, 0x6a9d68, 0x7fc1c9/e2/203/217, 0x807 23e/250, 0x8a2e58 and 0x8cae0a/1a. The other three (0x410824, 0x655f9a, 0x872705) point at the armour and suit tables next door at 0xbd22c8/cc. Nothing in .rdata points at the table. Indirect reads through a register would not show in this scan, but they would only add sites. |
| Route 1: "hashed" is real, and a heap copy doesn't escape it | CERTAIN for the image layout. The table sits in .rdata at 0xb10000+, and every reader sits in .text. A heap copy leaves the table bytes alone, but you still have to patch the readers, which are code. The SHIP policy forbids that, and re/antitamper.md says so. |
| Route 1: the real session does trip the check | PARTLY established. The hash model is analysis only. The live evidence is RN1/RN3/RN4, which died 30-90 ms after load. The control runs X4-X6 were never run (re/fa_round.md says "not run"). re/antitamper.md says which check fired is not established. |
| Route 3: the selector's slot 20 is the message handler | CERTAIN. The vtable 0xbbd494 slot 20 is 0x810b20, and its code pushes the strings ZW_SELECT4, ZW_UP, ZW_DOWN, ZW_PAGEUP, ZW_PAGEDOWN, ZW_LEFT and ZW_RIGHT. |
| Route 2: the selector's slot 10 is the input handler | CERTAIN. Slot 10 is 0x879570. |
| Route 3: the same handler reacts to ZW_LEFT/RIGHT, so it can be hooked | GUESS. The strings are referenced, but what it does with them is unread. |
| Routes 2 and 3 disagree on whether LEFT/RIGHT is "ignored" | Not a contradiction. They talk about different slots (10 versus 20). Treat LEFT/RIGHT as unproven until a logging pass shows it. |
| Route 3's "owned" trick (write 0xFF briefly into the edited slot's byte at 0xced638/9 so the same row can be bought as another set) | GUESS. It is plausible: .data write, restored right after. It depends on the handler and the buy running on one thread, which I did not verify. |
| Routes 2 and 3: the new name text appears on screen | GUESS. The wrapper pattern is live in pass-through, but no override string has been seen on screen. This is the first gate for both. |
| Both routes: pictures can't be added | CERTAIN for XML, per the notes. The 36 pictures are fixed and the element table has about 4 spare slots. A runtime texture swap is a GUESS and not recommended. |

## Scores

| | Route 1: real table | Route 2: variants per row | Route 3: sets |
|---|---|---|---|
| Arcade, DM maps and 9 stock maps | Only in a direct boot. A real session likely exits (0x8000dead). | Yes, map-independent. | Yes, map-independent. |
| Private match | No. | No (hook state is local). | Not as stated. It needs the kl_cast side channel, a later stage. |
| Online | No. Peers need the identical patched table, and stock peers desync or exit. | Off (`kl_online()` gate). | Off. Peers only see the carrier gun. |
| SHIP-safe (no code byte) | No. It needs about 25 code patches. | Yes. | Yes. |
| Effort | High, with no way to ship. | About 400 lines of C plus a LOC merge. | About 600-800 lines of C plus a Python tool. |
| Crash risk | Very high. A missed reader indexes into the armour table. | Medium. The pool re-park mid-menu is the danger. | Medium. The 0xFF window and the pointer swap are the danger. |
| What the owner sees | Nothing, or an exit. | LEFT/RIGHT cycles a row's gun. The picture is a lineup card or a mismatch. | A key flips a category to its "II" set. The text changes, and the picture is the nearest of the 36. |
| Gun count | 36 plus a few, only in the rifle category | 36 rows, each with several guns | 36 rows × 2 sets = about 62 guns |

All three keep the carrier row's price, rank, lock and stars, because the readers are hashed.

## Recommendation, staged

**Stage 0 (no new code, ship now).** Use the live-proven `[Shop] Swap=row:item`. It already gives up to 26 more guns as replacements. Bake names and pictures per carrier row with `tools/kl_shop_extra.py` and kl-merge-27's card tools. This costs the stock gun on that row.

**Stage 1 (read-only probe, one live run).** Add a new `klhook/klshoppage.c` to the build. It logs only:
- the mode (0x154d810), the highlighted row (0x154d80c), the category (0xced640) and the slot (0xced63c);
- every message reaching a slot-20 wrapper;
- the key and LOC lookups from `MercsShowInfoFAWeapons` (0x50c630).

The same pass overrides ONE shop name key through `kllocname.c`. The question to answer is whether the name text changes on screen. If it does not, stop here.

**Stage 2 (sets, offline Arcade only).**
- **File:** `klhook/klshoppage.c`, included after `klshop.c`, reusing `kls_apply` and `kls_stg`.
- **Functions:**
  - `ksp_wrap_selector` handles slot 20: set toggle, `BuyWeapon` bookkeeping, and the 0xFF window.
  - `ksp_text` handles slot 0x60: key → ini string, static buffers.
  - `ksp_pic` handles slot 8: remap the picture row.
  - `ksp_reconcile` runs at shop open and round start. If the crew record's rows differ from `ownedRow`, it resets `ownedSet` to A.
- **Hand-over:** push only the carried `{row → item of ownedSet}` pairs through the klshop pool code.
- **Tool:** `tools/kl_shop_sets.py` picks carriers by price and tier and writes the ini block and strings.
- **ini keys** (each with an options toggle labelled "(recommended on/off)"):
  - `[ShopPage] Enable=1`
  - `ToggleKey=`
  - `Set1.Row28=item,Name,Desc,PicRow`, one line per row
  - `Carrier price fit` chosen by the tool
- **Fallback input:** key polling (`GetAsyncKeyState` with edge detection and a foreground check). Retargeting the dead `FABuyWeaponToggler` XML pair is a second option, but it is a GUESS and would need baking per level variant.

Route 2's LEFT/RIGHT multi-variant idea is not worth building separately. Sets give the same reach with less per-row state.

## Test steps for the owner (live runs are paused)

1. Stage 1 build with logging only. Open the shop and walk all four categories and both slots. Send me `KLHook.log`.
2. Check that the one overridden shop name shows on screen. This is the go/no-go for everything after.
3. Stage 2 with one set on one category (rifles). Buy a set-B gun, start the round, and confirm the gun is in hand and the carried-gun name is right.
4. Repeat on a stock FA map (e.g. F02) and on an expansion map.
5. Buy the same row in set A and set B. This checks the owned-check trick.
6. Buy, then die and respawn. Then start a new round, which exercises `ksp_reconcile`.

## Plain-language summary for the owner

- **How many guns:** the shop stays at 36 rows. With the set toggle each row can show one of two guns, so about 62 guns are reachable (36 stock plus the 26 non-shop ones).
- **How it would look:** a key flips a category to an "II" page. The headline, name and description change. The picture is the nearest stock gun's picture, or a generic class card if kl-merge-27 bakes those.
- **What stays impossible:**
  - A real 37th row, or a fifth category tab. The table and the category code are integrity-checked, and changing them probably exits the game in a real session.
  - A correct picture for every extra gun.
  - An independent price, rank or lock for set-B guns. They inherit the carrier row's.
  - Online or private-match use, until a later stage that shares each player's choice.
- **CERTAIN:** the immediate count, the hashed layout, and the vtable slots.
- **GUESS:** the on-screen name override, how the handler reacts to LEFT/RIGHT, the 0xFF window being safe, and the XML retarget.


## Route 1: bigger table (code patch)

**ROUTE 1 verdict (real bigger shop table, relocated to the heap): not feasible in a SHIP build. It is feasible only as a TEST, direct-boot experiment, and the result could not be played in a real Arcade or Fragile Alliance session.**

I did this by static analysis only. I launched nothing, installed nothing and committed nothing. Claims I could not prove are marked GUESS.

**1. Mechanism**
- Allocate a 64-row heap copy of the table (24 bytes per row), copy the 36 stock rows, and append the new rows.
- Repoint every code reader of 0xbd1f68..0xbd22c8 to the copy.
- Change the four category limits, because rows are grouped by constants compiled into the code. Pistols are 0..10, shotguns 11..16, SMGs 17..27, rifles 28..35, and the limit is 8+28=36. New rows can only join the rifle category.
- The armour float table at 0xbd22c8 and the suit table at 0xbd22cc follow the shop table directly. They do not need to move.
- 0xbd1f50..0xbd1f67 is a vtable, not shop data. The 85 raw hits at 0xbd1f50 are vtable stores, not table readers.

**2. Every reference to the table**
All hits are immediates in .text; nothing in the data references it. That is 21 immediates in 11 functions. The "Hashed" column shows which of them sit in ranges the integrity checks cover.

| Address | What it does | Hashed |
|---|---|---|
| 0x410710 | Loadout. Reads item and ammo at 0x4107a7/ae and 0x4107d6/dd, calls 0x538ec0, and reads the armour table at 0x410821. Row 0xff gives 0 and -1 gives 0x1c. | yes |
| 0x684cb0 | Loop from 0x684cc2 to 0x684ce6 (stride 0x18); calls 0x698110 for matching items. Called from 0x8e1ea0. | yes |
| 0x6a5260 | Price getter (0x6a5278) | yes |
| 0x8a3e40 | Rank getter (0x8a3e58) | yes |
| 0x77a4f0 | Tier/stars getter (0x77a508) | no (page-lucky) |
| 0x6a9d50 | DLC getter (0x6a9d68) | yes |
| 0x8c0d40 | Ammo getter (0x8c0d65) | yes |
| 0x808220 | IsLocked. Reads row*24 at 0x80823e and 0x808250, then checks DLC through the [0x168f750] vtable +0x38. | yes |
| 0x8cbdf0 | Item-to-row search (0x8cbe0a/1a). Items 0x3e and 0x3f return -2; not found returns -1. | yes |
| 0x7fd180 | Bot weapon pick. A random row in 11..35 via 0x8b66c0(0x0b, 0x23), plus hard-coded 0x23 and 0x18. | yes |
| 0x78a8d0 | Weapon pool builder (0x78a923/936). Marks each item and builds the objects. | no |

- The getters share one accessor object, [0x168e96c], which is also the weapon pool. Each getter returns 0 if byte [this+0xbc] (Arcade enabled) is clear.
- Callers of each getter are listed in my notes. For example, price is called from 0x50ca03, 0x55d456, 0x7f7551, 0x8eaa06 and 0x96b73e.
- A vtable swap does not help, because the readers are plain direct calls and immediates.

**3. The hash (Valve's CEG checks, re/antitamper.md)**
- The checks are several hundred inlined CRC32/MD5 checks over fixed ranges of the image in memory.
- Coverage is 84.9% of .text and 65.9% of .rdata. That includes 0xb8b000..0xbeb000, which holds this table.
- Not covered: the IAT, .data/.bss, the heap, and 221 unhashed 4KB .text pages.
- A mismatch overwrites a return address with a stub that calls ExitProcess(0x8000dead).
- The checks run only when game code passes a check site. A direct boot (`-o DefaultScene=...`) never trips them.
- A real menu-started session exits about 30 to 90 ms after the level load (runs RN1 to RN4).
- Nothing periodic was found.
- The table bytes themselves are in a hashed range, so editing them in place is detectable in a real session.
- A heap copy leaves the .rdata bytes intact, but all 17 or more reader patches would still be in hashed code.

**4. TEST hooks versus SHIP**
- SHIP allows IAT slots and data only. It writes no code or .rdata byte, and it does not contain klauto.c.
- TEST with `SessionSafe=1` (the default) also allows image bytes outside the hashed ranges.
- TEST with `SessionSafe=0` allows anything. That is for direct-boot runs only.
- `klh_data()` writes heap and .data. `klh_poke` is the code patcher, and the guard in klhook.c gates it.
- The live evidence is re/fa_round.md section 5.3 and 7.1. Five detours in unhashed pages survived real sessions (X1 to X3). Hashed patches died (RN1 to RN4). The separate hashed-code control runs X4 to X6 were never run.
- re/voiceplain_1023.md says the same: hashed code patches work only in a direct boot.

**5. Patch sites and risk**
- About 25 code sites in total: the 21 table immediates plus 4 category limits (`mov eax/ecx,8` at 0x50c746, 0x556434, 0x58c7ae and 0x7d2e23).
- Further constants to widen:
  - the scroller caps 0x28 at 0x7d2dd5 and 0x7e4cfa;
  - the absolute bases 0, 0xb, 0x11 and 0x1c at 0x58c691..0x58c6b5;
  - the bot pick's 0x23.
- Almost all of these are in hashed .text. Only 0x78a923/936 and 0x77a508 are not.
- GUESS: which specific checks cover each page in a menu-started offline Arcade session. The ranges say hashed, but I did not run it.
- Risk is high:
  - A real session would exit.
  - A missed reader would index past the old table into the armour table.
  - Category and paging code would need extra patches.

**6. Menu side for rows 36 and above**
- Text comes from LOC keys `Weapon%d` and `Weapon%dDesc`, built with sprintf (formats at 0xb48d64 and 0xb80444). These can be added in the level .LOC, which is not hashed.
- Pictures, stars and locks are XML elements keyed by PlayerIndex, 0..35 (`FAStatus_WeaponNN`, `FAStatus_WeaponBigNN`).
  - Rows 36 and above need new XML elements.
  - The menu element table has 5,096 slots with about 4 spare, so this is probably blocked. The exact headroom is a GUESS.
  - The XML is byte-identical across F01 to F09 (re/shop_hire.md).
- Paging is generic (row = page*8 + PlayerIndex), so extra pages work in principle. Rows 36 and above could only join the rifle category.

**7. What each route means online**
- ROUTE 1: the buy is an RMC (RMCBuyWeaponPack) carrying int8 row bytes, so rows 36 and above need every peer to hold the same patched table. The server pricing arrays at 0x55d3e0, 0x622e10 and 0x639c10 were not read, so this is a GUESS. Stock peers would exit or desync.
- Existing Swap route: `[Shop] Swap=row:item` in klshop.c writes weapon pool heap data only, with no code byte. It was proven live in S7 to S16 and is SHIP-safe. It is gated by kl_online()==0, so online it is off and peers are unaffected.
- Both routes would need to work on the 9 stock FA maps and in private matches.
- Because the Swap route changes only the item behind an existing row, it already works on every map. The XML and LOC are the same in all slots.

**8. What the owner would see**
- ROUTE 1 in a SHIP build: nothing, because the guard refuses the patches.
- ROUTE 1 in a TEST build with `SessionSafe=0`: it can only be tried by direct boot into F01. A real Arcade start would end with the 0x8000dead exit.
- Swap: the cap stays at 36 rows, but any row can hand over a different gun. Name and picture have to be baked per carrier row.

**9. Effort if someone still wanted ROUTE 1 as a direct-boot experiment**
- New klshop-style module with about 25 `klh_poke` patches and a table-builder function.
- Table builder: allocate and fill a 64-row heap copy, patch the immediates, and widen the limits.
- An extra LOC file, and an XML change in the per-level archive for the pictures.
- Roughly one new C file, a few helper functions, and tools updates. Likely several live iterations, with no way to ship the result.

**Recommendation**
- Drop ROUTE 1 for SHIP.
- Keep the live-proven Swap route. It reuses the usable non-shop items from re/shop_more_guns.md (33, 35, 38, 40-59, 62, 63).
- Bake the names and pictures per carrier row through tools/kl_shop_swap.py and kl-merge-27's card tools (tools/kl_shop_cards.py).

All files I read are under C:\kl-merge\kl-merge: re/shop_more_guns.md, re/shop_plan.md, re/antitamper.md, re/shop_hire.md, re/fa_round.md, re/voiceplain_1023.md, re/pm_options.md, klhook/klshop.c and klhook/klhook.c.


## Route 2: variants per row

VERDICT: PARTLY FEASIBLE. Static analysis only: nothing was launched, installed, committed or written. Everything below is read from the exe, the existing hook sources or the `re/` notes. Anything I did not see run is labelled GUESS.

**0. What is hashed and what is not**
- Valve CEG covers about 84.9% of .text and parts of .rdata. That includes the shop table at 0xbd1f68 (36 rows x 24 bytes: item, ammo, price, rank, tier, DLC).
- A mismatch ends in ExitProcess(0x8000dead). It is not online-only.
- Unhashed and safe to write: .data/.bss, the heap, and IAT or import slots. The SHIP hook policy (`klh_data`, `klh_poke`) allows only those writes.
- Consequence: price, rank and item per row can never be edited in place. Only runtime data and string lookups can change.

**1. Answers to the five research questions**
1. **Name and description text: YES (mechanism proven, on-screen result not yet seen).**
   - 0x50c630 (ShowInfoFAWeapons update) builds a text key via 0x694bc0 and fetches the text through vtable +0x64. It sets the result on every update via 0x7bb920 at 0x50d13f.
   - That fetch goes through the LOC lookup (0x490730 and 0x47d8c0), the same path `klhook/kllocname.c` already wraps through a private vtable copy (slot 0, thiscall, 3 stack args, ret 0xc).
   - The wrapper is installed and called live in pass-through. An override string for the shop keys has not been seen on screen. That part is GUESS.
   - Conflict: a second wrapper on the same object would clash with `kllocname.c`. The variant logic must be merged into that module or chained.
2. **Price text: NO by LOC.** The price is not a LOC string, and the table is hashed. A displayed price other than the stock one would need a texture or text-element write, which is GUESS and not found.
   - Charging a difference is possible in principle through money at `[[rules+0x5f8]+0x38]`, with rules = `[[0x168e9e4]+0x54]`. The compare, jg and sub are at 0x8eaa3f..4a (`re/shop_hire.md`).
   - A write to the money dword is a data write. Whether the game accepts a hook-side extra charge or refund cleanly is GUESS.
   - The on-screen price would still show the stock row's price. The variant price difference would have to appear in the description text.
3. **Picture: PARTLY.**
   - Element-table headroom is about 4, so there are no new XML elements. There are 36 distinct big pictures.
   - 0x58bc50 (WeaponBig, at 0x58c617) shows the picture iff PlayerIndex equals the highlighted row at 0x154d80c. Per-row pictures are therefore fixed by the XML.
   - Option A, safe: a "family lineup" card for the row, baked offline by kl-merge-27's `tools/kl_shop_cards.py`. It shows all variants of that row on one picture. That tool belongs to kl-merge-27, so I coordinate rather than touch it.
   - Option B, GUESS: swap texture content or repoint the element's texture pointer at runtime. Not found or tested.
4. **LEFT/RIGHT input: seen, but ignored.**
   - The selector input at 0x879570 (slot 10) receives LEFT/RIGHT and ignores them. CERTAIN.
   - The hook can read state as data. The highlighted row is 0x154d80c (CERTAIN). Mode is 0x154d810 (2 = weapon list). Category is 0xced640 (-4..-1). Slot is 0xced63c. The carried rows are in 0xced638 and 0xced639, written by 0x6ddd10.
   - For key edges, use `GetAsyncKeyState` with edge detection and a foreground check, as the existing input options do. A second press on the same row would be a game-side event I did not find, so I do not recommend it.
   - Caveat, GUESS: LEFT/RIGHT might also move the selection in menu mode. I did not check whether other categories or modes react to them, so a swallow-free design is needed (see 7).
5. **Per-player swap: PARTLY.**
   - The weapon pool is `[[0x168e96c]]`, a vector with +4 count, +8 cap, +0xc grow and a +0x10 array of 12-byte records {object, item label, byte+8 free, byte+9 dropped}. The label search is 0x55bee0 via 0x538ec0.
   - `klshop.c` Swap parks the stock objects and adds 8 objects of the extra gun with the carrier row's label (maker 0x710ad0, template 0x5d2f50). It is global per carrier row, not per player.
   - The call order of the loadout hand-over at 0x410710 (thiscall, ret 0x10; callers 0x42bd3c, 0x4b669c, 0x4d104d, 0x74ac22, 0x892dc3) is not established. Per-player relabeling at hand-over is therefore GUESS.
   - For one human offline (a solo run with AI), a global per-label swap is enough and already works for single-variant rows. Multi-variant needs a re-park when the choice changes.

**2. Mechanism (Route 2)**
- Keep the 36 real rows. For chosen carrier rows, declare variants in an ini, for example `[Shop] Variants=<row>:<itemA>/<itemB>/<itemC>`.
- Each tick, read 0x154d810 and 0x154d80c. When mode is 2 and the row is a variant row, listen for LEFT/RIGHT edges and keep `cur[row]`.
- Name and description: the merged LOC wrapper returns the variant's text for the carrier row's keys.
- Buy: detect the purchase from the money drop or from 0xced638/9 changing (0x6ddd10). Then re-park the pool: stock objects out, the chosen variant's 8 objects in with the carrier label. Redo it at round reset. The ReserveClips key (0xbeebbeeb) and ammo handling in `kls_ammo` still apply.
- Price: let the carrier price stand and explain the difference in the description text. The optional refund or surcharge through the money dword is GUESS.

**3. Effort**
- `klhook/klshop.c`: multi-variant `made[KLS_MAX][KLS_PER]` becomes per row per variant. Add the ini parser, input edge detector, re-park logic and a state-machine tick. About 300 to 450 lines. The new struct field is `cur[row]`.
- `klhook/kllocname.c`: merge or chain the variant text override into it. About 80 lines.
- Texts for each variant (name and description) and the lineup cards. The cards go through kl-merge-27.
- The KL Mod Options tool needs a toggle labelled "(recommended on/off)", per the owner's rule.
- Live testing is mandatory, since the name override, the input and the re-park have never been seen live.

**4. Risks**
- **Crash or desync:** re-parking the pool while the menu or a hand-over is in flight (the 0x410710 order is unknown). Mitigation: re-park only when mode is not 2, or only on buy detection and round reset.
- **CEG:** none if only .data and heap writes are used. Never patch code.
- **Input:** the foreground check is needed, or the keys fire while alt-tabbed. LEFT/RIGHT may also drive other menu behaviour, GUESS.
- **Two-wrapper conflict** on the LOC object, as noted.
- **Money write** may be reverted by the game's own accounting or fail a sanity check, GUESS.
- **Picture** stays one per row, so it may not match the active variant.
- **Online:** peers would see different loadouts. The online money is a different store (`re/shop_hire.md`).

**5. What the owner would see**
- On a variant row, LEFT/RIGHT cycles the gun. The name and description change (if the LOC override works on screen). The big picture is the shared lineup card, or a mismatched picture if only the stock one is used. The price shown is the carrier's. After buying, the player gets the chosen gun, with the stock reserve ammo handling.
- The 36-row cap is not removed. It becomes a 36-row menu where each row can hold several guns.

**6. Online, per route**
- Route 2 (virtual rows): gated off online by the existing `kl_online()` gate. Each peer's pool and money would differ. Treat it as offline only (GUESS that the gate also covers this new code, since it would be in `klshop.c`).
- More real rows (the Route 1 baseline): impossible because of the hashed table and the element headroom.
- Online is a later stage anyway, so nothing here blocks it.

**7. Recommended order**
1. First, prove the LOC override on a single shop key (name text on screen). The whole route depends on it.
2. Then implement the key edge reader as read-only logging first (log row, mode and key edges).
3. Then the re-park at buy and round reset, with one two-variant row.
4. Pictures last. Start with the lineup card from kl-merge-27.

**8. Unproven items (all GUESS)**
- LOC override visible on screen for the shop keys; LEFT/RIGHT having side effects elsewhere in the menu; the money surcharge or refund being accepted; a texture or element-pointer swap for pictures; call order of 0x410710 and per-player relabeling; the `kl_online()` gate covering the new code; behaviour of every stock FA map and private match with variants (each is expected to work, since the code is map-independent, but none were tested).

Files: `C:\kl-merge\kl-merge\klhook\klshop.c`, `C:\kl-merge\kl-merge\klhook\kllocname.c`, `C:\kl-merge\kl-merge\re\shop_more_guns.md`, `C:\kl-merge\kl-merge\re\shop_plan.md`, `C:\kl-merge\kl-merge\re\shop_hire.md`, `C:\kl-merge\kl-merge\re\antitamper.md`.


## Route 3: catalogue sets / pages

**ROUTE 3 report: extra "catalogue sets" in the weapon shop, driven from the menu side. Static analysis only; nothing was run, installed, committed or written.**

I read `re/shop_more_guns.md`, `re/shop_plan.md`, `re/shop_hire.md`, `re/antitamper.md`, `re/pm_options.md`, `klhook/klshop.c` and `klhook/klhook.c` (the SHIP/TEST policy code). I also disassembled kl2.exe (capstone via `debug/dasm.py`) and read the online.xml from the stock F02 zip. Anything not read or proven is marked GUESS.

## Verdict: PARTLY feasible

- **Feasible (Arcade only):** a page-2 / Dead Men set of rows. Each set remaps what a row hands over, plus its name and description. It is hook-only, SHIP-safe, and works on all 9 stock FA maps and the expansion maps.
- **Not feasible as asked:** a real 5th or 6th category, or more than 36 selectable rows at once. The category code is hashed and clamped, so a 5th bar can exist in XML but can never be selected.
- **Weak spot:** pictures. Each set can only show one of the 36 existing row pictures, so extra guns get a look-alike picture.
- **Also tied to the row:** price, rank, lock and stars stay those of the carrier row.
- **Online / private match:** no. See the last section.

## 1. The "hashed" claim: source, checker, mismatch

- **Source:** `re/antitamper.md` (static analysis, 2026-10-09), plus the compiled-in range map `klhook/klranges.h` (225 ranges).
- **Checker:** Valve CEG integrity checks inlined into game code, not a thread or timer.
  - There are 594 call sites and 735 copies of the hash routine.
  - Each site computes CRC32 over fixed image ranges, then MD5, and compares against constants in `.rdata`.
- **When:** only when game code passes a check site. Nothing is periodic.
- **On mismatch:** `0x6a8390` and its nine siblings overwrite a return address with an exit stub. The stub wipes the stack and calls `ExitProcess(0x8000dead)`.
- **Coverage:**
  - 84.9 % of `.text` and 65.9 % of `.rdata` are hashed. That includes the shop table 0xbd1f68 and the vtable 0xbbd494, since 0xb8b000-0xbeb000 is a hashed range.
  - Not hashed: the IAT, `.data`/`.bss`, the heap, and anything outside the image.
- **Evidence level:**
  - The CRC and MD5 model was recomputed for 6 resolvers.
  - Live: klauto code patches in hashed bytes ended runs RN1, RN3 and RN4 about 30-90 ms after load.
  - A direct boot with only unhashed detours did not trip.
  - Whether the owner's menu-to-Arcade path passes a check site is NOT established. Treat any hashed-byte write as a gamble even offline.
- **Online:** the session-create thunk 0x790060 is a check site, so online is certain to pass one.
- **Hook policy:** `klh_may_write` in `klhook.c` refuses code and hashed bytes in a SHIP build. Everything below stays inside that rule: private vtable copies in our DLL, heap pointer writes, `.data` globals (0xced638 etc.), and pool data.

## 2. How the shop works (read from kl2.exe)

**Shop state is plain `.data`, so the hook can read and write it:**

| Address | Meaning |
|---|---|
| 0x154d810 | screen: 0 = Primary/Secondary, 1 = category list, 2 = weapon list |
| 0xced640 | category: -4 pistols, -3 shotguns, -2 SMG, -1 rifles |
| 0xced63c | slot being edited: -6 = primary, -5 = secondary |
| 0x154d7d4 | cursor |
| 0x154d80c | selected row |
| 0xced638 / 0xced639 / 0xced63a | carried primary / secondary / suit row |

**Category numbering and row bases:**
- Category → row base 0/11/17/28 is computed at 0x7e4c30. The bases are added to the row at 0x7e4c8b..0x7e4ca0.
- The clamps `[0,11) [11,17) [17,28) [28,36)` are at 0x7d2db0, via the jump table at 0x7d2f00.
- The page size is 8, from the XML. The row is page×8 + cursor + base.

**The buy path is message driven.**
- The selector's message handler is 0x810b20, vtable 0xbbd494 slot 20. It takes one pointer argument whose first dword is the message name, and returns with `ret 4`.
- It handles the messages `ZW_SELECT`, `BuyWeaponDialogVoodoo`, `BuyWeapon`, `ZW_SELECT4`, `ZW_UP`, `ZW_DOWN`, `ZW_PAGEUP`, `ZW_PAGEDOWN`, `ZW_LEFT` and `ZW_RIGHT`.
- `BuyWeaponDialogVoodoo` runs 0x7f73d0. In order it checks:
  1. already owned: the selected row (`[sel+0x90]`) equals the byte at 0xced638 or 0xced639; the message is `WeaponAlreadyOwned`.
  2. rank and DLC, using the carrier row through the hashed readers 0x8a3e40 and 0x6a9d50.
  3. price, through 0x6a5260.
  4. availability, through 0x808220.
  5. only then it opens `BuyWeaponDialog`.
- `BuyWeapon` runs 0x6ddd10:
  - It writes the selected row into 0xced638, or into 0xced639 when 0xced63c == -6 (disassembled, corrected 2026-10-24).
  - It then sends the client call with the player index and all three bytes (0xced638, 0xced639, 0xced63a).
  - The server-side RMC is `RMCBuyWeaponPack`. I did not confirm that 0x6ddd10 is the final commit rather than one step before it (GUESS).

**Texts, pictures and stars:**
- Text comes from `MercsShowInfoFAWeapons` update 0x50c630.
  - It builds the key `/Menu/Online/WeaponShop/Weapon%d` (and `Desc`) from the row.
  - It looks the key up through the element's vtable slot 0x64, which forwards to slot 0x60 (0x490730, key → `char*`).
- Pictures are not looked up.
  - They are 36 separate `MercsGraphicFA` elements, each with a fixed `PlayerIndex` (the row). Their update is vtable slot 8 (0x58bc50).
  - Per frame, each compares its index with the selected row (`WeaponBig` and `Primary/SecondaryWeapon`) and shows or hides itself through `[this+0x88]` vtable +0xa0.
- Stars and locks use the same function. The star count comes from 0x77a4f0(row), a hashed-table reader.

**Categories are code.** The 5-category idea is dead in code:
- The clamps and jump table are hashed.
- The category cursor is clamped to -4..-1.
- A 5th XML bar would never get focus. Any ced640 outside the range falls to base 0.
- The XML still has the cut console leftovers `FABWHeaderMedium/Heavy/Special`, which fits a removed design.

## 3. Design: catalogue sets

**Idea.** Row numbers stay 0-35, so every hashed reader still works. A "set" (A = stock, B, C…) is a hook-side table `set[s][row] -> item, name, description, picture-row`. Sets can be per category.

**Per-category page B** is just a per-category "current set" variable. The owner's "rifles II" is then rows 28-35 shown from set B.

**Mechanism, all SHIP-safe.** Each wrapper is a private heap-copy vtable with one slot wrapped, the pattern already used for the clock and board HUD elements (`klhud.c:531`, `klchar.c`):

1. **Selector, slot 20 (message).** `__thiscall(this, MSG*)`, `ret 4`.
   - It sees every message, so it can toggle the set and handle the category press. A category press is `ZW_SELECT` while 0x154d810 == 1, and the category is then in 0xced640.
   - On `BuyWeapon` it records `ownedSet[slot] = curSet[cat]` after the original returns. The slot comes from 0xced63c and the row from the changed byte of 0xced638/9.
   - Around `BuyWeaponDialogVoodoo`, if the byte of the slot being edited equals the selected row but `ownedSet[slot] != curSet`, it temporarily writes 0xFF to that one byte. The same row in another set can then be bought, instead of `WeaponAlreadyOwned`. The byte is restored right after the original returns.
   - Only the edited slot's own byte is touched. `BuyWeapon` overwrites that byte anyway. The other slot's byte is never changed, because `BuyWeapon` sends all three bytes and a 0xFF in the other slot would unequip it.
   - The same row cannot be held in both slots, which also avoids a pool-label collision.

2. **`MercsShowInfoFAWeapons` instances, slot 0x60 (key → text).** `ret 4`, returns a `char*`.
   - If the key is `.../Weapon<N>` or `.../Weapon<N>Desc` and the set for N's category is not A, return the hook's own static string.
   - The `HeadlineText` key can get an "II" suffix the same way.
   - The carried-gun name elements `OldPrimaryWeapon` and `OldSecondaryWeapon` use `ownedSet[slot]` instead of the current set. A per-instance role is read from the TagName at install time.
   - The text comes from the hook's ini, so no LOC bake is needed. This is also why it is uniform on stock maps.
   - The category-list entries use the static `FAWeaponText` template, a different class, and cannot be changed this way. Keep them generic.

3. **`MercsGraphicFA` instances, slot 8.** Remap the compared row to the set's "picture row", for `WeaponBig`, the row pictures, and the carried-gun cards. The wrapper replicates the show/hide logic read at 0x58c617..0x58c6c1. The picture is a look-alike from the 36 existing ones; see "Pictures" below.

4. **Hand-over at round start.** Reuse klshop's pool code (`kls_apply`) with only the rows actually carried.
   - Build the pair list `{ownedRow[slot] -> item of set ownedSet[slot]}` for the two slots and push it through `kls_stg` / `kls_sgen`.
   - The existing code re-applies it when the pool is rebuilt each round. Live-proven in S6-S11 and S14-S15, including stock F02.
   - This needs far fewer pool objects than swapping every row of the displayed set.
   - Bots sharing a carrier row would also receive the human's variant (GUESS; bots do not use the shop).

5. **Reconcile.** At each shop open and at round start, compare the crew record's row bytes rec[3] and rec[4] against the hook's `ownedRow`. If they differ, set `ownedSet` back to A. This covers a server-refused buy.

**How the owner switches sets.**
- Preferred (GUESS that it works): retarget the existing dead XML pair. In `online.xml` lines 3153/3395/3684 the ZW_TAB elements already send `Increase` to a nonexistent `FABuyWeaponToggler`.
  - Change only `Receiver` to the selector and `Message` to `KLShopSet`. The wrapped slot 20 then sees it.
  - This adds no element-table slots, but the critic noted these elements sit inside keyboard-only wrappers, so gamepad has no route.
  - It must be baked per level variant: md5 e20b2764 (stock), 7c8828ec and 9aa3e4b6 (expansion zips).
- Fallback with no XML: the hook polls a key while 0x154d810 != 0 (no-bake route, uniform on stock zips).

## 4. What is data, code or hashed

| Item | Kind | How it is handled |
|---|---|---|
| Table 0xbd1f68, readers 0x6a5260 / 0x8a3e40 / 0x6a9d50 / 0x808220 / 0x77a4f0 | hashed | untouched. Price, rank, lock, stars and ammo stay the carrier's. |
| Category code 0x7e4c30 / 0x7d2db0 / 0x50c630 / 0x534530, vtable 0xbbd494 | hashed | untouched. Only per-instance private vtable copies are used. |
| 0xced638/9/63a/63c/640, 0x154d7d4/80c/810 | `.data` | read, and one byte is written briefly. |
| Pool at `[0x168e96c]` | heap | klshop data writes. |
| Element instances and their vtable pointers | heap | private vtable copies. |

Element discovery uses the manager walker (`[[[0xdd265c]+0x824]+0x9f48]` count, `{object,kind}` from +8; `klset.c` / `hud_menu.md` §1.1). The table is rebuilt per scene, so re-install when the vtable pointer is no longer ours (the `klchar` pattern).

## 5. Pictures: the weak spot

- XML cannot add a picture entity (`menus.md:467`), and the 36 are fixed per level.
- Options:
  - **(a) Look-alike art:** best fit by class. A Dead Men or non-shop gun shows the nearest stock picture, with the real name in the text. Cheap, honest if the description says so.
  - **(b) Generic class silhouettes:** the white-shop tool (`tools/kl_shop_cards.py`, kl-merge-27's area) bakes chalk silhouettes. Those look less wrong for a different gun of the same class.
  - **(c) Hook-drawn card:** blocked on `hud_board_b.md` B-P1, "does the HUD draw in state 0x20", never run.
  - **(d) Swapping an entity's texture at runtime:** a GUESS, not read, and the launch option is `-dx10`. I do not recommend it.

## 6. Quantities, effort and risks

**Reach.** There are 26 usable non-shop items (33 35 38 40-59 62 63). One set B maps all of them onto any of the 36 rows, so the catalogue grows from 36 to 62 guns.

**Cost.**
- About 600-800 lines of C in a new `klhook/klshoppage.c`, wired like klshop (included after `klshop.c`).
- A `tools/kl_shop_sets.py`: chooses carriers (price and tier fit), writes the ini block and the strings, and the optional online.xml retarget.
- A small edit in `kl_hud_menu.py` for the XML retarget.
- Live tests. The autotest cannot reach the shop; it needs a menu visit plus a scripted route, as in the S10 route.

**Risks.**
1. The `__thiscall` / `ret 4` signatures of slots 20, 0x60 and 8, read but not run.
2. Whether the XML ZW_TAB route reaches slot 20 (GUESS). Keep the key-poll fallback.
3. The commit order of `BuyWeapon` against the RMC (above).
4. The 0xFF byte virtualisation window is tight. Do not restore it late.
5. Text encoding of returned strings (GUESS UTF-8) and buffer lifetime. Use static buffers.
6. Handling clips for the extra guns (klshop GUESS 1) apply as before.
7. The carrier's rank lock decides who may buy a set-B gun. The scripted run showed the lock is a UI check only.
8. Pictures, as above.

**What the owner would see.**
- The Tab key (or a retargeted button) flips a category between stock and "II". The headline, names, descriptions and picture change.
- The price, stars and lock remain the carrier's, so pick carriers whose price and tier fit the gun.
- Buying works through the stock dialogs. The carried gun shows the right name.

## 7. Online and private match

- All of this is gated to Arcade (`kl_online()==0`), like klshop. The hook is inert online.
- A client's chosen set is not replicated: `RMCBuyWeaponPack` carries row bytes only.
- A private-match host could apply it only if each client's `(row, set)` reached the host, for example through the `kl_cast` lobby side channel (`pm_options.md` §7). The host would then apply per client, and two clients holding the same row in different sets would collide in the pool, which needs a labelling scheme. That is a later stage. Peers without the hook see only the carrier gun.

## Files

Read:
- `C:\kl-merge\kl-merge\re\shop_more_guns.md`
- `C:\kl-merge\kl-merge\re\shop_plan.md`
- `C:\kl-merge\kl-merge\re\shop_hire.md`
- `C:\kl-merge\kl-merge\re\antitamper.md`
- `C:\kl-merge\kl-merge\re\pm_options.md`
- `C:\kl-merge\kl-merge\klhook\klshop.c`
- `C:\kl-merge\kl-merge\klhook\klhook.c`

Scratch copy of the F02 online.xml (the only file written, outside the repo): `C:\Users\Henri\AppData\Local\Temp\claude\c--kl-merge-kl-merge\d4c7e4f4-84d7-4249-a418-cad3917427d6\scratchpad\online.xml`

## Page II build (2026-10-24, STAGED, NOT INSTALLED, not run in the game)
Owner: 'okay yes do a page 2'. `klhook/klshoppage.c` (+3 lines in klhook.c) and `tools/kl_shop_sets.py`; staged in `C:/kl_build_1024/shoppage_1024a/stage`
(SHIP dll md5 26393984, TEST 41b8ccf5 after the review fixes below, built on the k37 sources fb2dce1bf + page; INSTALL/UNDO shoppage.bat rehearsed on a scratch folder, undo byte-identical). Key F6 flips set A / B.
- Text: per-ELEMENT private vtable of MercsShowInfoFAWeapons (0xbbd0ec) and MercsSendMessageWeapons (0xbbd18c), slot 24 (0x490730, key -> char*, ret 4)
  wrapped; keys '/Menu/Online/WeaponShop/Weapon<row>' and '...Desc' answered from KLShopPage.ini; BuyWeapons_Title / Headline* get ' II'. Roles from the TagName
  at [obj+0xc4]: OldPrimaryWeapon / OldSecondaryWeapon follow the set the carried gun was bought in. No clash with kllocname.c (it wraps the LOC object).
- Picture: MercsGraphicFA (0xbbcc84) slot 8 (0x58bc50: NO stack args, see the review fixes) swaps the element's own PlayerIndex [obj+0xc4]
  between the selected row and the picture row for the call (WeaponBig in mode 2, Primary/SecondaryWeapon when carried from B). Global selection untouched.
- Buy: selector (0xbbd494) slot 20 = 0x810b20 wrapped; 'BuyWeaponDialogVoodoo' (0x7f73d0 refuses an owned row) gets the carried byte blanked to 0xff for the call
  when the row was bought in the other set (OwnedTrick, GUESS); 'BuyWeapon' (0x6ddd10) records the set. Hand-over: own copy of klshop.c's relabel recipe, per pair,
  8 objects, ONLY for guns a slot carries from B; parked/unparked each tick before the round (st < 0x19); rows klshop.c swaps are skipped.
- Pairs (20; `kl_shop_sets.py show`; `--grenades` adds 5 thrown items, untried in a gun slot): carriers by category, price, tier, dlc-free first.
- Open: live test (text on both classes, picture swap, buy of a B row, buy of the other set's gun of the carried row, round hand-over); 
  rows without a pair show the stock gun in B; pad/mouse cannot toggle; the built dll comes from the working tree (live dll is a9414890, k37).

### Review fixes (2026-10-24, same day, two reviews; still not run in the game)
Fixed (SHIP 263939849cf195702d684dc10cdfb2f3, TEST 41b8ccf5d80eb608f94a3d3f1616b9cc; stage dll = SHIP):
- Picture wrapper had the wrong signature (CONFIRMED by disassembly): 0x58bc50 takes no stack args (every path ends `add esp,0xc; jmp 0x832470`, which jumps to 0x48f8e0 = plain `ret`).
  `ret 0x14` would have eaten 20 bytes of the caller's stack at the first update of any wrapped element. Now `(self, edx)`, `orig(self, 0)`.
- Owned trick used the wrong byte (CONFIRMED): 0x6ddd10 writes 0xced639 when [0xced63c] == -6, else 0xced638 (the note above was backwards). Now slot = (edit == -6) ? 1 : 0.
  The row is read from [selector+0x90] (what 0x7f73d0 and 0x6ddd10 use), not the global. The trick runs only when the EDITED slot's own byte holds the row (replacing that gun with the
  other set's gun) and the other slot does not hold it; if both slots carry the row the stock refusal stands and the log says so ("carried in both slots"). So the same row is never
  held twice (resolves the both-sets case; `kspg_wantB` can stay a per-row OR).
- Role table is rebuilt on every full scan (elements already wrapped are matched by our vtable pointer), KR_NONE is not stored: no overflow, no stale roles.
- Toggle: edge detection (up -> down, 150 ms guard), only before the round (gate 1) AND in shop mode 2 (weapon list); a press in another mode is logged and ignored. The page falls back to A when the
  round runs or the gate closes. Log line on every toggle carries mode, highlighted row, category 0xced640, slot 0xced63c.
- Key hint: BuyWeapons_Title gets "  [F6] page II" (set A) / "  II  [F6] stock page" (set B), `[ShopPage] Hint=1` (GUESS: that key is the shop caption; if it is never requested nothing shows).
  The four category headlines get " II" in set B only.
- Stale-text check: the first text request after each toggle is logged (key, row, role, set served); if none comes within 1.5 s a WARNING line says the game may cache the names.
- A failed template / object-maker lookup disables the row only for 20 s (log 3 times at most), so the next map can have it. `kspg_ammo` returns at once while nothing of ours is made.
- INSTALL refuses unless the LIVE dinput8.dll is a9414890 (k37; value read from the game folder at stage time). UNDO refuses (without -Force) when the live dll is neither the page build nor the
  backup (a later hook is live), and always deletes the KLHook.ini backup after stripping the block (a stale one blocked the next INSTALL). Backup tag stays `.before-1024page`.
  Rehearsed on a scratch copy: install, double install refused, wrong live dll refused, later-hook undo refused, plain undo byte-identical (dll and ini), ini edited between install and undo, reinstall.
- The dlls are built on the k37 sources (fb2dce1bf) plus the page, NOT on the k39 head: installing changes only the page. The head tree has the page too, so the next hook build includes it
  (then the INSTALL guard md5 must be re-staged: `kl_shop_sets.py stage` re-reads the live dll).
Not fixed: carriers with a DLC lock (rows 12 15 19 27: dlc 0 3 2 0) still get set-B guns, unreachable without that DLC (shotguns have 5 guns for 4 free rows, SMGs 9 for 7);
the picture swap of +0xc4 assumes 0x58bc50 uses it only for the selected test (GUESS, other branches read it too); pad/mouse cannot toggle.
