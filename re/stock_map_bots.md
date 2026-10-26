# Bots online on a STOCK Dog Days FA map (2026-10-26)

Question: can the 2-instance bots-online bench run on one of Dog Days' 9 stock FA maps with the hook alone, or does it need a map change?

## Answer: NO, a map change is needed (hook-only is dead)

What the botsonline_1025 kit changes in DM01 (and nothing else):
- `C:/kl_build_1024/botsonline_1025/install.py:1-2` swaps `KLExpansion/Maps/DM01/F01_Main.zip` (md5 3f3f684a -> 61ad6de1, pinned at install.py:12).
- That zip is the live DM01 with ONE field changed on 7 entities: `ZSquadScript` field 1 (EGameType) `eHeistOnly` -> `eAllTypes` for the 7 `Squad#02..08` (Glazer_Bodyguard_0N). Only the .prp differs, every other member is byte for byte (`tools/kl_botsonline.py:1-9`, `:23-35`).
- Why it matters: online FA, `ZSquadScript` slot 14 (kl2 0x7b3790) drops a member whose squad mask lacks bit 1, when networked and FA (test at 0x7b37d1..0x7b37f0; `re/bots_online_fill.md:30-36`, `klhook/klbotfill.c:6-10`). eHeistOnly = mask 8 has no bit 1, so the Ally heisters are disabled online. eAllTypes keeps Arcade (mask has 8) and adds online.
- Stock maps are the same: the heister squads are mask 8 on all 9 stock levels (63 of 63, `re/bots_online_fill.md:38`; section 5 at `:83-86`: "same 7 eHeistOnly chains, same obstacles").

Why the hook cannot do it alone:
- The squad filter runs at level load, when no hook tick runs. `klbotfill.c:49-71` (`klbf_squads`, [Bots] OnlineFillSquads) tried to set bit 1 in the lobby; SL8 live result: it found 0 ZSquadScript. "Hook route is dead; do not retry it" (`re/bots_online_fill.md:119-122`). Also `klslot.c:335` ("a byte pass found 0 ZSquadScript") and the BotGate reasoning.
- `klbotfill.c:116` log text confirms the split: OnlineHost "activates NOTHING (the level must keep the squads online: tools/kl_botsonline.py zip)".
- What the hook DOES supply on top of a level that keeps the squads: Puppet mirroring on the client (OnlineHost, `klbotfill.c:31,116`), loot/van/box tactics (OnlineTactics, Van*, Box*, `:36-40`, `:209-360`), cop->bot damage factor and point-blank rules (`klbalance.c:1034`). The ZSoldier ctor builds no tactics online (`klbotfill.c:12-15`), so the hook puppeteers them. None of that runs without Ally actors in the world.

## The delivery route that already exists (data only, no code byte)

BotGate (`klhook/klslot.c:334-343`): online, the host's `[BotFill] OnlineHost=1` makes both peers open `Fxx_Main.bots.zip` next to the normal `Fxx_Main.zip` (the host's value reaches the client through [HostOpts]). The plain zip stays stock (mask 8), so Arcade and offline are untouched and no stock file is replaced. `C:/kl_build_1024/lan_1025/bg1.py` stages exactly such a sibling for DM01 and deletes it afterwards. Checked 2026-10-26: no `*.bots.zip` exists under `KLExpansion/` for any DD01..DD09 slot, so a stock-map bench needs one built first.

## What is needed for a stock-map bench (NOT built, per instructions)

1. A `.bots.zip` per chosen stock slot: the stock level's squads' field 1 set to eAllTypes. `kl_botsonline.convert()` cannot be used as is: it builds via `kl_fa_bots.Built`, requires exactly 7 controllers whose names contain `KB.SQUAD + 'Squad#'` (`kl_botsonline.py:20-24`), which are DM01's clones, not the stock names. It needs a variant that edits every mask-8 `ZSquadScript` of the stock .prp (same `kl_fa.edit` / `AU.setv(sc, us, 1, 'eAllTypes')` call). Unknown: the stock squad count per map (63/9 = 7 each is only the total).
2. Placement: copy to `<DD>\KLExpansion\Maps\DDxx\F0x_Main.bots.zip` (game folder, owner/peer install; I may not write there).
3. Unproven on stock maps: the tactics assume a `ZAllyEscapeBox`, an exit trigger and loot stacks with guards (`klbotfill.c:209-360`, tuned on DM01 BO runs). Stock maps' Arcade bots have those via Heist code, but the hook's scan/gather has never been run on them; expect first runs to be diagnostic.

## Bench files for later (hook, inis) - candidate map

Candidate: DD01 (Subway, slot F01, expansion Page 0). Reason: the map row needs 0 RIGHT presses (`M2_DD01_host.ini:115` "stepped 0 x RIGHT"), so the lobby script is the shortest and the same slot F01 the whole DM01 series ran in. The exit (subway/van) is the one the Arcade reference already uses; I did not verify the exit geometry in the map. Alternative DD02 needs 1 RIGHT.
Not written: `bos1.py`, `BOS1_host.ini`, `BOS1_join.ini`, because without the `.bots.zip` the run would only prove "0 Ally, bots dropped" (that is already the stock behaviour, BG1 "off" state). They are a 10-minute job once the zip exists: copy `bo11.py` without install/undo/md5, hook `out_all_1026zd_test`, host ini = `maps9_1026/M2_DD01_host.ini` + the `[BotFill]`/`[Bots]` sections of `BO11_host.ini`, join = `maps9_1026/M_DD01_join.ini` + `[BotFill] OnlineHost=1`, `[Sync] Probe/Compare/PuppetDiag`.

## 2026-10-26 ~09:15 - DD01 .bots.zip staged, BOS1 queued
- `tools/kl_botsonline.py --stock <in> <out> [game] [--only <name part>]` (convert_stock): every eHeistOnly ZSquadScript, or only those whose name contains the part; full verify (other members byte-equal, other fields equal).
- DD01 has 11 eHeistOnly squads: merc_bot_squad Squad#02..08 (the bots) and SwatExit#03..06_HEIST (SWAT, not heisters). Built with `--only merc_bot_squad`: 7 changed.
- Source `KLExpansion/Maps/DD01/F01_Main.zip` 27680110 (the page-0 F01=DD01 redirect target); output `C:/kl_build_1024/botsstock_1026/DD01/F01_Main.bots.zip` c7a110ef. BotGate (klslot.c 391, 449-453) opens `KLExpansion/Maps/DD01/F01_Main.bots.zip` online with the host's OnlineHost=1.
- Bench: `C:/kl_build_1024/lan_1025/bos1.py` (install.py places one file, always undoes), BOS1_host/join.ini (M2_DD01 lobby + BO11 bot keys), hook 1026zd. Review READY (wqi2u6ver). Not run live yet.
