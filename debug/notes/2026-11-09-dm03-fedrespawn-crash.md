# 2026-11-09 16:46 - DM03 Withdrawal crash at the police respawn (round 2)

Owner, live: "oh game crash". Files: `<DD>\KLHook_1.dmp` (58 MB, used here), `KLHook_2.dmp`, `kl2_490_crash_2026_11_9T16_46_44C0.mdmp`.

- Slot F03 = DM03 (06's dm03cops -> doors -> DM03_van chain, live zip c586d445). Round 2 started at 16:45:49. The owner died
  at 16:46:37 and came back as police ([FedKeep] path) at 16:46:42.209. The crash came 4 ms later, on the main thread.
- `c0000005 at kl2 0x4f8a8e reading 0x4f09`; callers 0x6307ed (CListUser func 0x630700) < 0x5bfc05 < ... < 0x607703 (ZHavokRayCollector).
- 0x4f8a60(this, key, value, flag) = remove `value` from the hash chain `[this+0x20][key]` (nodes of 3 values + next at +0xc).
  0x630700 walks an array of 0x80-byte records (edi = 0x33ce7604) and passes each record's `[rec+0x54] & 0xffffff` as the key.
- The dump shows the cause: record 0x593c2db0 has id **0**. Its neighbours have 0x7b2, 0x7b5, 0x7b9 (ascending). Key 0 makes the
  walk read bucket 0 = `[this+0x20][0]`, and table 0x3dc82020's first word is 0x4f09, the same as `[this+0x1c]` (a count, not a
  node pointer). The walk follows 0x4f09 and faults.
  this = 0x4a0fa120 (vt 0xb5a1d4); value = 0x593c3bb0 (id 0x741).
- So a record still in the per-frame list had its id cleared (released). The timing points at the police body that was just taken over.
  This is the same family as the 11-08 Hasta 0x538f02 police-respawn pool crash fixed by [ShopPage] FedKeep, but at a new site.
- First sighting of this exact site. GUESS: dm03cops added 11 police and raised the census 33/27 -> 44/29, so the police
  body pool runs fuller on DM03 than on any map benched with a fed respawn.
- Next: (1) a fed respawn bench on DM03 (needs the owner's OK for live runs); (2) find who writes `[rec+0x54] = 0` (watch
  candidates: 0x6986b0, the release path of 0x630700's records); (3) a hook guard is possible: skip key 0 in 0x630700's loop,
  since 0x4f8a60 with key 0 can never be valid. That needs a .text patch, so TEST/bench builds only, unless it is done through a
  detour the ship build allows.
