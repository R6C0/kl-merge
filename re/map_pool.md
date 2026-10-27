# Random map pools (mappool_1027a) - NOT run live

Code: klhook/klmappool.c (included after klslot.c, before klhostopt.c), hooks in klslot.c kls_map (one line) and klhostopt.c (wire + key).
Icons: tools/kl_mappool.py (build), staged in `<DM>\KL_PortTools\build\mappool_1027\` with INSTALL_dm/dd/mix.bat and UNDO.bat.

## Keys
`[MapPool] Enable=0 / Pool=0 (0 off, 1 Full Dead Men, 2 Full Dog Days, 3 Mix) / Apply=0 / Seed=0 / Log=1`; `[HostOpts] KeyPool=0x2E` (Delete cycles the pool, host only).
Needs `[HostOpts] Enable=1` (it carries the pool). Mod-settings row: tools/kl_mod_options.py `mappool` ("recommended off until benched").

## How it works
- Pool = entries (slot, page, folder) from the loaded [Redirect]/[Redirect.N] rules; DM* folders = Dead Men, DD* folders + stock levels = Dog Days.
- Draw = seeded permutation (splitmix64 Fisher-Yates); each load takes the first UNUSED entry of the slot being loaded; all used -> new cycle. No repeat until the pool is spent.
- Sync: klx_opts / UDP 27413 string gained `p<pool>q<seed hex>` (old clients stop before it). Host makes one seed per session (or `Seed=`). Clients apply the host's pool in memory only; no per-round message.
- Slot: map folders are slot-bound (Fxx_Main.*), and the game replicates only the slot index. Apply=0: the draw chooses among the loaded slot's maps only. Apply=1 (GUESS): the host in the lobby (sm state 0xd) sets the slot of the next entry with the stock selector's own calls: sm vtbl+0x28(slot), 0x7163e0, 0x4b5fc0 (commit/replicate), store MP_SelectedLevel (0xb6d6e4) = menu index (inverse of 0x746570: 0,1,2,3,6,4,5,7,8), 0x549e80.
- Icons: static. The lobby picture is a toggler over the 9 slot pictures indexed by the replicated slot; no safe live swap found. kl_mappool.py makes one grid-of-every-map picture per pool, used for all 9 slots, and sets the 9 titles to the pool label. Install the set that matches the host's pool; UNDO restores the first backup (`*.before-1027mappool`, never overwritten).

## Bench
1. Host, System Link or private match, `[MapPool] Enable=1 Pool=3`, log `mappool:` lines: pool order, LOAD n (cycle c): <map> on slot Fxx.
2. Client with the same ini maps: log `CLIENT uses the host's pool 3 ... seed`, same LOAD lines.
3. Play more rounds than maps: `new cycle` appears only after the pool is spent. Then try Apply=1.
Open GUESSes: sm vtbl+0x28 is the selector's SetLevel(slot) in menu-order-independent slot units; whether the commit in the lobby state 0xd refreshes the clients' picture.
Changes wanted in peer-owned files: none required (klhostopt.c is edited here only for the wire + key).
