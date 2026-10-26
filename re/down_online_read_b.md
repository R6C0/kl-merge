# kldown online: static read B (2026-10-26)

Static read of `klhook/kldown.c` (no code changed, no game launched). Verdicts: VERIFIED = read in code/disassembly, GUESS, UNKNOWN.

## Q1 The online gate

| Item | Finding | Verdict |
|---|---|---|
| `kld_tick_main` (kldown.c:2129) | `act = klr_arcade(&rules,&state,&level); if (act) act = klb_level(why);` | VERIFIED |
| `klr_arcade` (klbalance.c:414) | returns 0 for role `[sm+0x54]` 2 or 3 | VERIFIED |
| `klb_read` (klbot.c:363) | same role test; `kld_dead` uses it | VERIFIED |
| `klb_level` (klbot.c:510) | Arcade level policy; AllMaps (klsteam.c) applies only in an Arcade session, an online session gets the raw verdict | VERIFIED |
| Result | kldown cannot act online today; `klb_level` must be dropped online (keep it for Arcade) | VERIFIED |
| New gate | sm vtable ok, `[sm+0x5c]==4`, role 0/1 (Arcade, as before) or 2/3, `[sm+0x70]==0x19`, rules vtable `KLH_RULES_SV_OK` / `KLH_RULES_CL_OK` (klhook.c:267), sub-mode `[0x168e59c]` 0/1/2 all allowed | GUESS (design) |

## Q2 Local player and master

| Item | Finding | Verdict |
|---|---|---|
| kldown lookup | `gd=[KLD_GAMEDATA]`, `idx=[gd+0x898]`, `pl=[gd+0x828+4*idx]`, vtable == `KLD_PLAYER_VT`, police byte `+0x2723` | VERIFIED |
| Online correctness | slot method fails on a client (klcharonline.c L3/L4); host ok | VERIFIED (per notes) |
| Fix | reuse `klco_find_own`: slot method, then scan for the player with `klco_is_master` (`0x9425a0` on `R=[ent+0x274c]`, `[R+0x540]==ent`) | VERIFIED exists |
| Master | local human is master (owner == station 0x94bc10) of his own ZFFPlayer R | VERIFIED in klcharonline; not re-run live |
| Remote players | have klnetsmooth's private vtable, so the vtable test misses them; harmless for the local test, but the local player himself must not be in that set | GUESS |

## Q3 Tuning object T `[0x168d7c0]`

| Item | Finding | Verdict |
|---|---|---|
| Trigger 0x8da3b0 reads | switch `[0xceb40c]`, `[0x1535a2c]`!=1, 0x828710 (`[gd+0x4d38]`!=0, `[gd+0x4d48]` bit2), 0x49aac0 (`T+0x274`, `T+0x26c/0x270`), `T+0x268`, 0x86d630, 0x449520 (`T+0x27c/0x280`), then go-down 0x76a450 (`T+0x25c/0x260/0x264`) | VERIFIED |
| Who runs it online | the machine that owns the hit victim runs ReceiveHit / trigger: the victim's machine applies (shooter prices). So each peer's T governs only his own human's downs | GUESS (from stock RMC notes) |
| Host-side writes | T is per process; writing it on the host changes only the host's own and the host's AI behaviour. Risk: AI path 0x70e0e0 / 0x847968 may read `T+0x25c..0x280`; host T edits could change bot downs (not read) | UNKNOWN |
| Cooldown field online (`T+0x260` vs `0x264`) | branch 0x76a7c0..0x76a7ce not read | UNKNOWN |
| `[gd+0x4d38]` / `0x4d48` online | previous notes say "looked at, not used"; online values unknown | UNKNOWN |

Rule: every peer needs the same T numbers (the hook on every peer), as for all other hook parts.

## Q4 Writes on objects this machine is not master of

| Write | Object | Rating |
|---|---|---|
| T numbers (`kld_tuning`) | process global | SAFE (local data, not replicated) |
| switch `[0xceb40c]`=0 (Flop=3 Vulnerable) | process-wide: freezes EVERY player's down state on this machine; the three setters (0x62db70/0x8c8150/0x5491d0) do nothing while 0, so a remote player's down would be lost here | UNSAFE online (keep Vulnerable off or write it only while the local player is the only one downed) |
| D = `[player+0x2948]` fields (`+0x2b`, `+0x21`, `+0x38`, `+0xf0`), M `[D+0xc]` end ticks, `[M+0x8b0]/[M+0x898]` slot words | LOCAL player only (master) | SAFE if master-checked; UNSAFE on a replica (stock sends nothing; the owner would overwrite) |
| input mask `[player+0xed0]` (NoFire, camera LOOK bit) | local player's input | SAFE |
| prompt fields `[osd+0x10fc]` | local HUD | SAFE |
| damage table floats (DownFromCop/Crew), klbalance wrapper | per machine, Arcade-only parts inert online (Sv/Cl rules never read the table) | SAFE but no effect |
| `kld_bots` (AI downs) | AI are host-owned online; writing them on a client touches replicas | UNSAFE on client, host-only |
| Flop=3 clip number into the carrier pair | replica sees only the stock fall/GettingUp messages; the clip speed (FlopBase etc.) is invisible to peers | SAFE, but not mirrored |

## Q5 Conflicts with klucc_down.c

| Item | Finding | Verdict |
|---|---|---|
| klucc_down gate | `klud_gate(mode,sub)`: mode==4 && sub==1 (UCC only); wraps rules vtable slot 15 (0x425320) on private Sv/Cl vtable copies; own `klud_local`, `klud_is_player` | VERIFIED |
| Overlap | with the new gate sub-mode 1 both run: both can write the trigger/cooldown (T) and the down state of the same player | VERIFIED overlap |
| Resolution | kldown must yield in sub-mode 1 until the two are reconciled (or klucc_down calls into kldown's mash). Do not install a second rules vtable copy (klucc_down owns the private copy) | GUESS (design) |

## Design consequences

1. New online gate in kldown (state, role 0..3, type 4, rules vtable ok), drop `klb_level` online.
2. Local player = slot method then master scan (klcharonline); write D only for the master.
3. Vulnerable (switch `[0xceb40c]`) is off online; Flop clip speed is local-only; Arcade damage-table parts are inert.
4. Bots part stays host-only/off on clients; UCC (sub-mode 1) stays klucc_down's.
5. Live checks needed for the UNKNOWNs (`[gd+0x4d38]` online, cooldown field, AI reads of T) before claiming Arcade parity.
