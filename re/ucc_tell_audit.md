# Undercover Cop tell audit (2026-10-26, static only)

Item 2 of `re/ucc_cnr_owner_request.md`. Workflow ucc-tell-audit (wf_ff961ff5-f9c): one finder, one skeptic who tried to
refute each claim from the repo. Nothing run live. "Holds" = the skeptic could not refute it from the cited evidence.

## Tells that hold (fix candidates, each a toggle)
| id | tell | evidence | fix idea |
|---|---|---|---|
| S10 | OUR crew list / Tab card maps flag 0x80 to KLUV_ST_UNDERCOP(2), grouped as fed (proven) | klhook/klhud_values.c:497, :525, :538; drawn online by OnlineCrew (klhud.c) | for viewers who are neither police nor that UCC, return the crew state until the reveal. Pure DLL code. [HUD] UccHide (recommended on) |
| S1 | stock crew list: score flag 0x80 -> row state 3 (4 with 0x40000), held per crew index by every peer | re/hud_values.md:44-45, re/fed_kit.md:345 (slot 114 0x771a10) | strip 0x80 in the slot-114 answer for non-police viewers. Whether the stock row looks different was NOT read |
| S4 | kill / mode pop-ups name the role: FA_Killed_UCC (shared), FA_UCC_* (not shared) | re/hud_popup.md:61, 64, 65 | route the UCC kill through FA_Killed_Merc while hidden (.LOC data, kllocname.c style) |
| S5 | killing him pays 100,000 (+0x674) vs 10,000 for a cop (+0x66c): visible as a money jump per crew row | re/fed_kit.md:357 | tuning data write while hidden. Weak tell |
| S6 | own speaker -5 and own lines (UCC_PoliceShootingUCC, UCCRogueCop ...) | re/bain.md:52, re/fa_gamemode.md:420-424, klhook/klvoice.c:158-167 | make -5 lines local to the UCC. Whether others hear them is NOT read |
| S2 | SetUndercoverCop RMC / m_iFlags 0x80 reach every client (inspection leak, not on screen) | re/netcode.md:373, re/fed_kit.md:83 | send only to the UCC until reveal; send path not located, so SHIP falls back to S1/S10 display hiding |

## Missed by the finder (skeptic's list, to check)
- FA_NoFriendlyFireUCC pop-up (0x6fff68 / 0x868bb1, shared): a heister who shoots the UCC gets a different message. Likely the
  strongest stock tell (one shot outs him).
- Friendly-fire / traitor gate on the police flag (0x41d480, re/fed_kit.md:50-54): shooting the UCC never makes you a traitor.
- Stock row state 3 vs 4 (0x40000) is a second visible variant.

## Refuted or unsupported (keep as open questions, not tells)
S3 tag colour (only shown for police viewers), S7 AI police ignore him (no evidence either way: needs a read of the AI
target filter), S8 separate spawn set, S9 police body at start, S11-S16 (mod round counts, names, KilledBy offline only,
sync gate, start window, leaderboard name).

## Next
A live UCC1 bench (queued) should log the sub-mode, then a 3-instance run with screenshots of each viewer's crew list,
plus one heister shooting the UCC, to confirm S1/S10 and the friendly-fire pop-up before any fix is built.
