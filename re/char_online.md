# Heister / mask / outfit online (klcharonline.c, 2026-10-25; built, NOT run live)

Owner: "make sure the player models transfer over too or add an option to select either in game or at the menu like in arcade".
Builds: klhook/out_charonline_1025a (SHIP f5132547) and _test (9aae9ae9). Default off: `[CharOnline] Enable=1`.

## 1. How the stock game picks an online player's model (kl2.exe 0x74ee10, disassembled)
No model or variant is sent. Slot 137 of the Sv / Cl rules takes the ENTITY TABLE INDEX `bl`: `ent = [[0x6161c0(session)] + 12*bl + 4]`
(skips when `[ent+0x2748]==0` or `[ent+0x2723]!=0`), `n = 0x817160(session, 0x8e8010(8))` (the client's session number; -1 or >=8 -> 7),
`model = rules->vtbl[0x220](2, n)` (GetHero), `ent->0x783fb0(model)`. Every machine runs it, so the body is a function of the seat number the host
handed out. The variant byte `[ent+0x50]` is set locally (option UseMask). So "feed our choice into the stock path" is not possible
(nothing on the wire); the cheap route is klchar.c's own two calls (0x783fb0, 0x88c810) on each entity.

## 2. Who is whom: the entity table index
Same number on every peer (order of the level's ZFFPlayer entities; the argument slot 137 gets). The own entity is
`[gd+0x828+4*[gd+0x898]]` (klfed.c) found in the table by pointer. The Steam id -> client -> player chain (pm_options 8.2) is NOT needed and NOT established.
GUESS (probe `charonline: my body`): the local player pointer is that slot online too.

## 3. Transport (per player, every peer sends and listens)
- Steam lobby MEMBER data key `klx_look` = `i<idx>c<c>m<m>o<o>`: SetLobbyMemberData = ISteamMatchmaking008 slot 24, GetLobbyMemberData 23, GetNumLobbyMembers 16,
  GetLobbyMemberByIndex 17 (GUESS: SDK 008 numbering; the proxy already uses 12/18/19 of it). Written on change + every 5 s, read every 1 s. klmm.c installs the proxy when `[CharOnline] Enable=1 Steam=1`.
- UDP broadcast `KLCH1;i<idx>c..m..o..` port 27414 every 2 s (System Link has no lobby). Own packets are recognised by the entity index.
- A peer without the mod sends nothing (stock body). A character the receiver's wardrobe lacks is ignored, said once.
- Only heisters (type 2, not busy) are published or touched; police bodies never.

## 4. Choosing
Choice = klchar.c's KLChar/KLMask/KLOutfit (`[Character]` in KLHook.ini; Options > Match options / Heister page where the overlay has them: before the match).
Hotkeys in lobby and match (window in front, online only): F9 next heister (Shift: previous), F11 next mask, Ctrl+F11 next outfit; beep + log; written to the ini.
The body can only be announced once the level is loaded (the table exists then): the lobby choice is sent at load, a change in the match is sent at once.

## 5. Not solved / limits
- No "each character once per match" arbiter (two peers can pick Kane; both see two Kanes).
- Stale announcements for up to 1 s (Steam) / 7 s (UDP) after a round change; own-body change clears the peer table.
- A new round re-runs slot 137 and puts the seat model back: re-applied within 250 ms + Settle (max Tries per 10 s per entity).
- Without a KLWardrobe.ini for the level only mask 1/2 apply (no Dog Days hero choice: the seat->hero map online is unknown).
- Mask/outfit on a REMOTE body: if the variant byte is replicated by the game, the owner's own value arrives anyway and agrees.

## 6. Live test
Single PC (System Link solo, SL10.ini + `[CharOnline] Enable=1`, `[Character] Char=14 Mask=1 Outfit=22`, TEST build; `TestPeer=<idx> TestChar=9` fakes a second peer):
expect `charonline: on`, `network session (role 2)`, `my body: entity K of N (type 2)`, `I chose ... announcing`, `sent on UDP 27414`, `heard OWN announcement back via UDP ... ignored - the transport works`,
`applied to body: my body on entity K: model A -> B ... now B`, then `variant ...`. With TestPeer: `heard peer on entity T chose ...` and `applied to body: peer on entity T`.
Press F9 in the lobby/match: `I chose heister X`, then the re-announce + apply lines.
Two PCs (needed for the real proof): each logs `heard peer on entity J chose X via UDP` (System Link) or `via Steam lobby` (Quick/Private), then `applied to body: peer on entity J`; look at the other player's model on screen.
