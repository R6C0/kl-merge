# Crew modules online: design (wk-merge, 2026-10-28)

Static research only. Nothing launched, kl2.exe read-only, no repo file edited. CERTAIN = read in code/docs/exe. GUESS = inferred, evidence given.
Rule for everything below: data / heap / private vtable / game-thread tick only (SHIP refuses every .text patch).

## 1. What holds (newest facts first)
- Sv ctor 0x79acc0 uses rules+0x348 and +0x350 as its OWN fields (mov [esi+0x348] at 0x79ad27, [esi+0x350] at 0x79ad2d). CERTAIN (VERIFY read the exe). Writing the Arcade crew-table pointer there corrupts Sv state. Do NOT fake the table.
- Sv (0xbd2eb4) and Cl (0xbd31e4) are siblings of ZGameRulesHeist (0xbd3514), not subclasses. Sv fields start at 0x334 (re/hud_online.md). Cl size 0x334 and Sv size 0x3a8: GUESS (doc match, allocation size not read from the exe).
- Online seat table is 0x74-byte records at [rules+8], count [rules+0xc/0x14]; it feeds score, round end and replication. Do NOT add fake seats.
- DDL_ZFFActor (netcode.md:593) has no model / outfit / name / voice field. KLSY2 is our own UDP packet (port 27415, 20-byte records: slot, hp, pos, cls, team). So a host-only look change stays on the host. CERTAIN by docs; not re-disassembled.
- The host census (klbotfill.c / klbotdown.c: ZFFActor 0xbb3bac, team Ally, ZSoldier at actor+0x77c) and klbd_online_view (3 private slots, pseudo-records) are the right substrate. It is hook heap, so shippable.
- klcharonline.c is the proven look carrier for HUMANS: KLCH1 UDP 27414 + lobby key klx_look, applied per peer with 0x783fb0 / 0x88c810. StockHero path CONFIRMED online for hire (41e2c1c85, commit comment, not an independent trace).

## 2. Refuted / downgraded
- "Slots / census ORDER are equal on host and client": REFUTED as stated. Logs show only equal COUNTS (71 ZFFActor, 7 Ally; bots_online_sync.md:11). Order never compared; cause B (peers load different entity orders) is still open. Option "key by slot" and "shared seed by census index" both rest on it, so both are GUESS until diffed.
- "Client copies are replicas bound by m_iRef": GUESS. bots_online_sync.md cause A (clients may run cop AI locally; cops differ per screen per owner 10-26) is unrefuted, and the DO creation site was never traced (netcode.md:213).
- "Writing the crew table / faking seats is an option": REFUTED (section 1).
- Client's CERTAIN tags on the visual effect of 0x783fb0 on a client-side AI actor: downgraded to GUESS (proven for players and offline crew only).

## 3. Cross-peer key (decides every look/voice/name module)
Candidates, best first. All GUESS until the proof bench in section 6 passes:
1. Group-name digit of Glazer_Bodyguard_0N (scene data, identical per level; klcrew.c:48). Evidence: static scene data. Weakness: maps without those groups.
2. Entity slot with cls 0xbb3bac + team check as klsync.c does (class test must use klsy_vtof, puppets carry private vtables). Weakness: order unproven.
3. Position-nearest match at round start (all bots spawn at known spawns): fallback, GUESS.
Host sends (key, char, mask, outfit, voice, name-id) records; peer resolves key to its local actor.

## 4. Per-module plan, ordered by value to owner (online must equal Arcade)

| # | Module | Online substitute | Ini key (default 0) | Effort | Risk |
|---|---|---|---|---|---|
| 1 | klcrew looks | Hook-owned per-bot struct (key, seed, model, variant) + new AI-look record next to KLCH1 (or klhostopt seed key); each peer calls 0x783fb0 then 0x88c810 on its own copy, code-head checks, Tries/Settle from klcharonline | `[BotFill] OnlineLooks=0  ; (recommended off)` | M | Medium: model mismatch crash, round rebuild resets bodies (re-run apply each round), client apply on puppet unproven |
| 2 | klcrew voices | Voice online is recording [0] (0x421f07 -> 0x422063, only hook_review_talk.md:157 supports; GUESS). Need hook-driven swap of line entries through speech manager, per pseudo-slot, reuse klvoice_online | `[BotFill] OnlineVoices=0  ; (recommended off)` | M-H | Medium; no proven path |
| 3 | klcrew names | HUD name source for a bot online not located; GUESS it is the crew record name. Do nothing until traced (find the HUD reader, then supply from hook table) | `[BotFill] OnlineNames=0  ; (recommended off)` | unknown | Low if skipped |
| 4 | klescort | Drop Heist-only reads (+0x1b3, +0x1d8..+0x1ec, +0xeec, +0xf1c); drive from census + klbf_ob_stage / klbf_ob[] (puppeteer gather/hold exist). Host-only motion, replicates as actor position | `[BotFill] OnlineEscort=0  ; (recommended off)` | M | Medium; reads invalid on Sv must be removed, not defaulted |
| 5 | traits (kltrait/klbot) | klb_read_any: Arcade reads the real table, online returns klbd_online_view pseudo-records; lift forced 1.0 (klgrudge kly_health 249 / kly_aim 278) per pseudo-slot. Host-side hp/aim only | `[BotFill] OnlineTraits=0  ; (recommended off)` | M | Low-Med; Arcade path must stay byte-identical |
| 6 | klshield | Writes local player's health object; health is server-side online. Skip | none | n/a | n/a |
| 7 | klgrudge | ZBecomeTraitorTactic 0x79b7c0 needs the Arcade brain, plus record writes. CERTAIN blocker. Leave off | none | n/a | n/a |

## 5. First implementation step (shared by 1, 4, 5)
Build `klb_read_any` plus the per-bot struct in klbotdown.c (key = actor pointer for local use, cross-peer key per section 3). Log-only first (no model writes): each peer logs (slot, cls, team, group-name digit, current model root [[actor+4]+0x68]) once per round. No ini key needed for the log (add under `OnlineLooks=2` dry mode).

## 6. Proof bench before any apply code (2 seats, game free after c9)
Run host and client, diff the logged tuples. Pass = same digit-to-model-root mapping on both and identical ordering of keys, or a proven key. Then enable OnlineLooks=1 and expect same model root per key on both seats, 0 faults, and a second round re-applies. Also confirm on the client that [[actor+4]+0x68] changes after 0x783fb0 and the body draws (never shown for client AI actors).

## 7. GUESS list
1. Digit of Glazer_Bodyguard_0N is equal on all peers (static scene data only).
2. Census / slot order equal across peers (counts only).
3. Client accepts a model write on a puppeted AI actor without desync.
4. HUD name path accepts hook-supplied names online (not located).
5. Teleport / hp changes by host replicate via the actor sync (Arcade-side evidence only).
6. A new round resets AI bodies as it does human ones (slot 137); apply loop must re-run.
