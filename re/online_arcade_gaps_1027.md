# Online vs Arcade: current gap list (2026-10-27, evening)

Owner rule (10-27): online FA (Quick Play, Ranked, LAN, Private) must be 1:1 with the modded Arcade mode; only the humans in the seats differ.
Built from the live ini, the owner's session in KLHook.log (20:27-20:50), re/open_work_log.md and a static scan of the `kl_online()` gates in klhook/*.c.
Static work only: no live run, no code edit. CERTAIN = seen in a log line or in code read this pass. GUESS = inferred. Class: L local cosmetic, H host authoritative, C needs replicated data or a net message, X no seat/records.
This supersedes the stale 10-25 table in re/arcade_online_parity.md.

## Ranked by owner visibility

### G1. Hire on: the F9 / [Character] choice is still applied online (CERTAIN bug)
- Owner sees: with `[Hire] Enable=1` Arcade ignores the Heister page's Char; online the owner still spawns as the pre-chosen character (log: "hire: [Hire] Enable=1: the Heister page's Char=14 is ignored", then "charonline: network session (role 2): my choice is Parker mask 1 outfit 22", "charonline: applied to body ... Parker").
- Cause: klcharonline.c reads the saved choice and does not consult the hire state that klhire.c uses to ignore it in Arcade. The two parts do not share the flag.
- Fix: class L (local body look, the choice already travels over CharOnline UDP 27414). In klcharonline's choose step, when klhire's enabled flag is set, skip the saved choice and use the hire/seat character (host-assigned, as Arcade's hire does), logging "charonline: hire on, choice ignored". Code exact lines GUESS (file not re-read).
- Ini or code: code. Risk: low; SHIP-safe (reads only). Must not break the proven HRF2/HRP2 hire flow (hire writes the worn character in round 2).

### G2. Voice lines, banter, ambience, stingers, music play only partly online (CERTAIN keys unset, GUESS effect)
- Owner sees: Arcade has Dead Men voices, crew banter, ambience/stinger/music cues; online only the local player's own lines exist (klvoice_online.c). Banter between bots, stingers, ambience layers are silent because their readers need the Heist rules class.
- Cause: klvoice, kltalk (OOB guard, `[Voice] OnlineTalkNoScore`), klambience, klstinger, klmusic, klcensor gate on Heist rules or kl_online. Online keys exist but are unbenched.
- Fix: class L (local audio). Bench the Online keys one at a time with `[Online] Read=1`; kltalk's reader should use `[rules+0x2c]` online (already coded behind OnlineTalkNoScore).
- Ini only for the first step (see ini_only list). Risk: medium for talk (rules offsets are small heap blocks online, out-of-bounds read hazard: keep the guard).

### G3. Remote player look (D1/D2 in re/netcode_players_1027.md) (CERTAIN)
- Owner sees: other humans look stock or pop; low send rate stutter; NetSmooth blinds charonline/kldown_mirror.
- Fix: class C. `[NetSmooth]` and `[Net]` Tune keys are absent from the live ini; add them only after a bench. Code for the vtable blinding fix, GUESS size small.
- Risk: medium (touches peers' bodies).

### G4. Arcade-only gameplay parts that are inert online (CERTAIN gates, behavior GUESS)
Each is gated off by `kl_online()` and has no online replacement:
- klinv / klshop / klgrenade / klgun (inventory, shop page I, grenades, gun variants): online inventory replicates (DDL_SInventoryItems); page II shop online is already proven (OnlineSend/Apply/EarlyMake). Page I / grenade parity: class C, needs a replicated item+ref message. Risk high.
- klfreeclimb, kljoin jump request, klunstick, klfallrescue (opt-in `[FallRescue] Online=1`, untested): local position writes peers see as teleports. Class C (sendNet). Ini-only for FallRescue Online=1 once benched.
- klpm_gun / klpm_arc (pistol-mod pages, Arcade menu start): never in a network session. Class L but menu-side; defer.
- kladren, kltrait: adrenaline and traits answer neutral online (kltt_g.online factors 1.0); `[Voice] OnlineTraits=1` only logs/knows the trait. Class H if parity is wanted (health/regen are shared state). Risk high, recommend leaving neutral.
- klcam: ShoulderCover and Unstick writes stay out of network sessions. Class L; GUESS the cover camera is safe to allow (local camera only), bench it.

### G5. Host-authoritative AI heisters / cops (mostly done, CERTAIN proven; edges GUESS)
- Proven: BotFill OnlineHost/OnlineTactics, Ally bots from .bots.zip, klbotdown online downs, OnlinePointBlank (one cop step kills an ally bot), OnlineVanHold, OnlineCrew records.
- Gaps: klgrudge, klcrew, klhop, klcardown, klcdying, klshield show no online handling (0 online references): their Arcade behavior on bots may not reach a bot owned by the host. Not reproduced; GUESS only. Class H, host-only code path. Check in a 9-player dedicated bench before coding.

### G6. Round end, RankUp, letter, killed-by (CERTAIN not seen live)
- RankUp / Letter not yet seen live online (log note 10-27 15:30); intro "1 humans" on host is the first-tick log (logging only, fixed by c3608f1b0).
- Fix: verify with a bench; no code until seen failing.

### G7. Retomoto lift (not online-specific, staged)
- FedRide=2 + door box re-arm staged in C:\kl_build_1024\rtlift_1027, untested. Owner's call to install.

### G8. DM11B coordinate wrap crash kl2+0x1e4a22 (CERTAIN crash, cause GUESS)
- Local node ~65.5k below spawn x 34077: GUESS a 16-bit x wrap in online placement (only DM11B spawns at x > 32767). Class H/C. Fix: clamp or offset the DM11B online spawn x below 32767 (map-side data, no hook code), or guard in the placement path. Not live-tested.

## Not gaps
Hire online (HRF2/HRP2), page II online buy, HUD online ports (ALL2D..G, BOSE5), grades SteamXP, PumpNoBlock: proven 10-27.

## Recommended order
G1 (code, small), then bench G2 ini keys one at a time, then G3 tune keys, then G4 camera and FallRescue, then G5/G6 verification, G8 map fix.
Status 2026-10-27 23:10 (per gap):
- G1 CLOSED in code (OnlineIgnoreChar=1 live in SHIP 1827767d8); live proof pending: A1HIRE bench not run (owner at PC), staged.
- G2 OPEN (ini keys unbenched). G3 OPEN. G5 OPEN (edges, 9-player bench first). G6 OPEN (RankUp/Letter unseen live).
- G4 PARTLY: camera UnstickOnline coded, default off (not run); page I buy needs no port; grenades/free climb/guns shelf research only.
- G7 STAGED/live: FedRide=2 + door re-arm in SHIP; untested in play.
- G8 MITIGATED: [Int16Guard] Enable=1 OnlineSkip=DM11B keeps DM11B out online; Plan B codec bias not clean (6a739230c); unbenched.

## G4 next (2026-10-27 late, branch a1-g4-1027; static reading only, no live run)

### Done in this branch
- `[Camera] UnstickOnline=1` (recommended off until benched; row `camunstickonline`): Unstick steps 1-3 (latch cam+0x394, blend timer cam+0x5a0, side copy cam+0xb40), the low-fps chaser filter (cam+0x658.. +0x30), UnstickGate (cam+0x30/0xc54) and UnstickTarget (cam+0x540) now also run in a network session. They write ONLY the camera object ZFFCamera1; the player struct P is read, never written. GUESS: the camera object is not a replicated object (nothing in the read code sends it). Key off = old behaviour exactly (log only online).
- NanRepair and Recover (eye setter 0x7c9030) stay as they were (NanRepair offline-only, Recover not gated).

### Shop page I online buy: nothing to port (CERTAIN by code, behaviour unproven)
- Online, a page I (stock set A) row buy is the STOCK path: kspg_sel falls through to the stock handler, host Sv commit 0x55d3e0 charges and stores the row. The page II work (OnlineSend/Apply) only intercepts `shownB` rows. So "page I online buy" is not inert; the only page I part that IS Arcade-only is klshop.c `[Shop] Swap` (a carrier row hands over another gun), which is the more-guns shelf below.

### ShoulderCover / LeanFollow online: NOT view-only, left off
- The swap calls the stock key handler 0x640080 with [P+0x2954] lifted; the handler runs setter 0x74a120 which writes [P+0x818] bit 10 (side in use). In cover the cover state copies that bit into [state+0x105] and decider 0x89fd90 re-seats (action 1/2), which can change state+0x104 / [P+0x2954], and 0x4520d0 replicates the cover side (re/camera.md 4.1/4.4). b84 ([P+0xb84]) and LeanFollow's [P+0xb90] bit 0x20 are player fields too (b90 is replicated: certain; b84: unknown).
- Only a truly camera-side swap (write [cam+0xb40] / the sweep 0x9088c0 input without touching P) would be view-only, and nothing proves the camera does not re-sync from [P+0x280c] each frame (GUESS). What a port needs: a Log=1 bench in a 2-seat session (host + client) logging [P+0x2954], [state+0x104], and whether the peer's body leans after a swap; if the peer sees no change, `ShoulderCoverOnline=1` (existing test switch) is already enough for the swap, with LeanFollow still off.

### More-guns shelf (klshop.c Swap) online: research
- Pool relabel (park carrier's stock entries, add 8 objects made by 0x710ad0 labelled with the carrier item) is data only and already proven online for page II via OnlineApply + OnlineEarlyMake (ids line up on every peer). A standing Swap needs: (1) the early make for each Swap pair on every peer in the same row order (the existing kspg early-make loop, fed from [Shop] Swap pairs instead of page II pairs), (2) the net sub-object guard (gun+0x13c) from bed6e62d3, (3) host and clients carrying the same KLGuns.ini pair list (m4 "item differs" style check over SHOPG, or a hash in the hello), (4) kl_online() removed at klshop.c:180 behind a key. Risk: medium (a peer with another list hands out a different gun than the host's inventory record).

### Grenades: research
- Arcade path: G sets bit 0x40 in [P+0xb90] (replicated), 0x544780 copies it to [P+0x818] bit 0x800 which nothing in kl2.exe reads (VERIFIED 10-25), so step 1 is a dead bit and Probe=2 (own Create(0x11)+Start of ZFFActionThrow) is still undecided. Nothing to port online until the offline throw works. A port then needs: the throw action created on the local player only (the action is a replicated actor action?), the projectile spawn through the stock net-spawn bookkeeping (0x753150, not repeated in klshop.c), inventory count decrement via DDL_SInventoryItems, and the item delivered by a host-validated message (same shape as SHOPG). Class C, risk high.

### Free climb and jump: research
- klfreeclimb.c moves the body with a real ZFFActionVaultOver (kind 0x2B) on a private vtable copy and writes the end place; peers only see position updates. It refuses to START online (klfreeclimb.c:650). A port needs: proof that the vault action is replicated as an action (if the stock ladder/vault actions replicate through the action id, the peer plays the same clip), else a position-only teleport with a one-tick jump the peers' NetSmooth smooths (see G3). Climb clip /Movement/Climb/Up/<class> must exist on the peer (it is a Dead Men clip loaded by the expansion on every peer).
- kljoin.c jump boxes (Retomoto tower to lobby): the jump request writes the jump list index [gd+0x8d0]-driven teleport via 0x72e0f0; refused online (kljoin.c:376). A port needs the HOST to be the only one firing (box test on host seats, then a message to the owner client to move his body: the SHOPG/HIRE netchan shape) and the client's own position write, then NetSmooth must not rubber-band it. FedRide=2 (staged) already covers the host fed.
- klunstick (cover stuck-in-object, F7) and klfallrescue are the same class (local position write peers see as a teleport): `[FallRescue] Online=1` is the cheapest, bench it first.
