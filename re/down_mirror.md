# Online flop mirror (track mirror, 2026-10-26) - BUILT, NOT RUN

Goal: the other players see this player's Arcade flop (belly-fall clip, and the sped get-up) online. Before: the flop is a local write into
the victim's animation pool [pl+0x78] and his prone movement's fall words; the other machines run the stock fall (down_online_read_a.md Q3).

Code: `klhook/kldown_mirror.c` (included by klhook.c after klnetchan.c), pure part `klhook/kldown_mirror_logic.h`, test `klhook/kldown_mirror_test.c`.
Hooks in kldown.c (3 small ones): `kldm_det_r` in `kld_mix_next` (hash draw), `kldm_probe_line` in `kld_o_probe`, two forward declarations.
klnetchan.c and klucc_down.c are NOT touched.

## Design
- Flop=3 picks the NEXT knock-down clip right after the previous get-up (kld_mix_next), so it is known long before the fall. The victim announces it
  (`KDFL`, "1;mode;sheet;n;group;mask") every 4 s and at every change while he is UP. No mid-fall clip switch is needed.
- A receiver arms the replica of that body while its D state is 0: carrier pair (Flop=3) or belly pairs (Flop=1) in the REPLICA's pool, and the three
  fall words of the REPLICA's prone movement (same rules as kld_flop_words: stock id, 0xffff or ours).
- Guards: not the local master (kld_o.pl and 0x9425a0), heister type 2, police byte clear, D object its own, writes only at D 0, pool exclusive
  (no other body of the session table or the game data's 32 places wears the same [+0x78]; shared = REFUSED, logged once per body with the verdict),
  not an AI heister's set. Dry=1 writes nothing. Disarm (restore) on: stale announce (20 s), round not online, another body at the index, mode change.
- Sped get-up (`KDSY` "1;n;frame*10;rate*100;to", every 0.7 s or at a speed change of 0.2, only after the landing): the replica's channel fps =
  master rate*25 + 2*(target frame - frame), clamped to 0.5x..2x of the master's pace; the two end ticks are held 2 s behind the clip end as the master
  does. Writes only a channel inside the replica's [+0x70] chans that plays the armed clip; stops after 15 s.
- Fall counter: the replica counts its D 0 -> nonzero transitions; the announce's n-1 raises it (corrects drift).

## Message-less fallback (judged)
`OnlineFlopMirror=1` makes the victim draw with r from `kdm_hash(table index, fall number, 'KL')` instead of the xorshift, with kld_mix_next's own walk
(`kdm_pick_r`; test 3053 checks). A replica can then compute the same clip with `OnlineFlopMirrorAssume=1` and NO message. Valid only with identical
FlopMix / FlopReach / FlopCarrier / sets on every machine, the same table index for a body on every machine (GUESS, klucc.c's convention) and equal fall
counts (a light stumble that does or does not set D 2 on a replica breaks the count until the next announce). Default off (recommended off).
VERDICT: usable as a LAN/SL cross-check and the only thing that can reach Steam internet play; not reliable enough to be on by default.

## Carriers (re/hook_netchannel.md)
- UDP broadcast 255.255.255.255:27416: LAN and System Link ONLY. Never the internet.
- Steam lobby member data `klx_msg`: internet, but only while the lobby exists. GUESS: the game leaves the lobby when the match starts; not proven.
- So over Steam INTERNET play no carrier is proven; Assume=1 (hash, no message) is the only route that can work there.

## Remaining GUESSES (live bench)
1. A replica's prone movement plays a fall at all and reads its [M+0x8b0] words and the pool pairs like the master's (MIRROR OK / MISSED lines answer it).
2. The pool of a replica is not shared with the master's. ReplicaProbe=1 now prints EXCLUSIVE / SHARED per body. If SHARED (likely for two bodies of the same
   hero model), the mirror refuses and nothing changes; the next step would be a private copy of the replica's pool (not built).
3. The table index of a body is the same on every machine (messages carry the sender's own index; the receiver reads it in its own table).
4. A replica's channel is writable (speed) and its M end ticks are read like the master's.
5. The replica's D state follows the network (D 2 at the fall); the order of the D 0 -> 2 change and the arm (arm needs a message at least ~0.3 s before the fall).

## Live bench checklist (2 machines, LAN or System Link, [Down] Enable=1 Log=1 ReplicaProbe=1 Flop=3 on BOTH)
- Both logs: `down: mirror:` OnlineFlopMirror line, `RECEIVED an announce ... by UDP|Steam`, per body `ReplicaProbe ... EXCLUSIVE|SHARED`.
- Victim goes down: his `SENT the announce` names the clip; the other machine `ARMED replica` with the same clip, then `MIRROR OK` at the fall (or MISSED).
- While he mashes: `SENT the sync`, the other machine `FOLLOWS`; look at the picture: the copy rises at his speed.
- `REFUSED` lines name a shared pool; then the cure is a private pool copy, not these keys.
- Counters line every 60 s: received by Steam vs UDP shows which carrier carried it. Repeat once with System Link off and a Steam lobby only.
