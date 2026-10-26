# FA lobby with 12 player rows (2026-10-26; static, NOT run live)

Owner: the FA online lobby shows 8 rows; with PlayersMax=12 the extra players are not listed.

## Findings (frontend.xml of the live overlay Patch01.zip, kl2.exe)
- Window `FALobby` (frontend.xml, ~line 8148). ONE window serves all three modes; sub-mode word `[0x168e59c]` (0 FA, 1 UCC, 2 Cops and Robbers).
- Plain list (FA/UCC): seven column groups, each 8 elements `PlayerIndex 0..7`: `LobbyPlayerReady_T` (graphic FAStatus_Ready#01-08, TagName LobbyReady),
  `LobbyPlayerReadyNot_T` (ReadyNot#01-08), `LobbyPlayerChat_T` (Speak#01-08), `LobbyPlayerName_T` (X -60), `...Trust_T` (230), `...Style_T` (480), `...Rank_T` (700).
  Rows flow inside the group (`GeomSpace` = gap added to the element height; re/hud_board.md): text 16 + 16 = pitch 32, ticks 18 + 14, speaker icons 32 + 0.
  Name elements carry `FocusGraphic="LobbyFB#01..08"` (static fake bars at Y 290 + 32k); the moving bar is `LobbyFB`.
- CnR layout (what the owner means by "the cops and robbers one"): same window, tags `LobbyTeamPlayerName/Ready/ReadyNot/Chat` with `TeamIndex` 0 (team A, X -65),
  -1 (unassigned, X 266), 1 (team B, X 618), 6 rows each (PlayerIndex 0..5), headlines TeamA / TeamUnassigned / TeamB. Pictures FAStatus_Ready#09-20, Speak#09-26.
  Which set is visible: element update 0x62c36d..0x62c43e: sub-mode 2 hides the plain tags, otherwise the team tags (`bl=1` -> hidden).
- Selector: `<GuiElement Type="MercsFASelectorLobby" ... PageSize="12" FocusBarBaseY="290" FocusBarDeltaY="32">`, class ZMercsFASelectorLobby, attribute parse 0x66c660
  (FocusBar +0xa0, OptionsFocusBar +0xa4, TeamFocusBar +0xa8, base/delta floats +0xb0..+0xbc). PageSize is already 12.
- Where the 8 comes from: THE XML ELEMENT LIST. Not a code constant: the text provider (0x631b56 `cmp [ebp+0x12c], connected` -> empty text, name via 0x67f300(sm, index);
  0x631c35 same for trust/style/rank) and the graphic provider (0x58c238 / 0x58c2a9 / 0x58c353: `cmp [esi+0xc4], connected`, then 0x8fdf90(sm, index))
  are index driven with `connected` = 0x698250. So elements with `PlayerIndex` 8..11 are filled by the stock code.
- Room: list rows 290..546, box `BlackBackground#02` ends at Y 545, bottom frame at ~538. Twelve rows at pitch 32 do not fit (674); pitch 20 ends at 533.
- Pictures are scene entities (`Graphic=` names, re/menus.md 2); the lobby only has FAStatus_Ready/ReadyNot up to #20 and Speak up to #26, FocusBar_Long_02 #01-#12
  (all used). New entities would mean editing Scenes/kaneandlynch.zip.

## Chosen method (least risk, data only)
`tools/kl_lobby12.py` writes `<DD>\KLExpansion\Overlay\Patch01_rows12.zip` = live overlay Patch01.zip with the FALobby window changed:
1. PlayerIndex 8..11 appended to the seven plain column groups (28 elements; no FocusGraphic; tick/speaker pictures reuse FAStatus_*#09-#12, the team instances).
2. Pitch 32 -> 20: GeomSpace 16 -> 4, 14 -> 2, 0 -> -12 (all list groups, team lists too so they stay consistent).
3. Separators Line_Long_01#02..#09 (Y 320 + 32k) -> #02..#13 (Y 308 + 20k); fake focus bars LobbyFB#/LobbyTeamFB# to Y 289 + 20k;
   selector FocusBarBaseY 289, FocusBarDeltaY 20.
`klslot.c` (SHIP and TEST): `[Lobby] Rows12=1` (default 1) answers the open of Patch01.zip with that file (the MountFirst alias path, 0x7f5610 mount; no code patch).
Skipped with a log line when the file is missing, older than Overlay\Patch01.zip (rebuild after kl_lobbynames / kl_expansion), or MountFirst is set.
Why not a hook-drawn list: the stock code already fills the rows; a hooked list would duplicate it and fight the focus bar.
Mod option row: `lobbyrows12` in tools/kl_mod_options.py ("(recommended on)").

## GUESSes (check live; all cosmetic, none can crash the code path since the XML parser only sees extra elements)
- pitch = element height + GeomSpace (so 4 / 2 give 20); a negative GeomSpace (-12 for the 32 px speaker icons) is accepted, else speaker icons of rows 2+ sit lower.
- The selector's moving bar is at base + index * delta (so 289 / 20); 32 px tall bars overlap by 12 px at alpha 64.
- Two elements naming one picture instance (rows 9-12 and the team elements) are fine because only one set is shown.
- Unknown parser reaction to elements beyond the original count: none expected; if the lobby fails to open, set `Rows12=0`.
- Rows 9-12 cannot be hovered with the mouse (no free FocusBar_Long_02 instance). Keyboard focus uses the moving bar.
- Rank/Style/Trust columns: widths unchanged; long names may touch (re/hud_menu.md note).
Live check: host a System Link lobby, 9+ players (or Solo + AI: rows show only connected humans), look at rows 1-12, the focus bar (Up/Down), ready ticks, speaker icons, a CnR lobby (Cops and Robbers toggle) still shows 6/6, and `KLHook.log` has "[Lobby] Rows12=1: an open of Patch01.zip is answered with".
Install (not done): `python tools/kl_lobby12.py` (writes the zip), ini `[Lobby] Rows12=1`, SHIP dll from out_rows12_1026a.
