# Menu element table: the static count (2026-10-24, scheduled check-in, read only)

Purpose: the Hire tab's first gate (re/shop_hire.md stage 0: "read the element-table usage statically") and
re/menus.md open questions 3 and 4 (the real count against the 5096 cap; the exact `<Platform>` rule). The
2026-10-09 model (`count.py`, not in the repo) gave 5992 for the frontend, which cannot be (the stock game
runs), so the reader was re-read from kl2.exe build 0490 and the model rewritten as `tools/kl_menu_count.py`
(self-test: every stock load set fits the table). Nothing here was run in the game; the K0 log line in
re/hud_menu.md section 8 is still what proves it. Numbers below are ESTIMATES from the model.

## 1. Results (keyboard, English, Europe, retail flags)

| load set | files | entries | free below 5000 | templates (of 512) |
|---|---|---|---|---|
| stock frontend | Patch01 frontend.xml + kaneandlynch.zip online.xml | 4730 (gamepad 4927) | 270 (73) | 500 |
| LIVE frontend (KLExpansion overlay) | Overlay\Patch01.zip frontend.xml + stock online.xml | 4793 (gamepad 4990) | 207 (10) | 502 |
| level, Arcade or FA | Patch01 ingame.xml + level online.xml (stock, DD01, DM02 variants) | 2775 | 2225 | 319 |
| level, DM01 variant | same with DM01's online.xml (3 more colour sets) | 2778 | 2222 | 319 |
| campaign level | Patch01 ingame.xml only | 1193 (Hard 1188) | 3807 | 147 |

Per file: frontend.xml 3143 stock / 3206 live, online.xml 1587, ingame.xml 1188 (Arcade/FA; the campaign-only
blocks `<ExcludeIn FA Arcade Extreme Hard>` are OUT in Arcade and FA, so ingame.xml is 5 entries smaller
there than in a Normal campaign level).

What this means for the Hire window (option B of re/shop_hire.md): in a LEVEL the table has about 2200
entries of room, so the element-table risk (shop_hire.md 7.1) is practically gone for an in-level window.
In the FRONTEND the live set is 207 entries under the 5000 line on a keyboard and only 10 under it on a
gamepad: a frontend page must stay small (and the gamepad case decides). The 14:24 crash class of
re/hud_menu.md 1.1 (a Window landing on entry 5000) needs ~210 more entries in the live frontend set.

Second limit, new: TEMPLATE DEFINITION SLOTS. The reader keeps at most 512 `<Template>` definitions per
load set (0x686270: `[reader+0x1e8] >= 0x200 -> return NULL`, 0x5ac bytes each; the counter is zeroed only
in the reader's constructor, 0x51aa76, and 0x6cffa0 makes ONE reader for both files of a load set). The
frontend uses 500 (live 502). A 513th `<Template>` silently returns NULL: its children are still created
(as children of nothing) and every element naming it is built from its own attributes only. So a new
frontend page may define at most 10 templates (12 on stock), or reuse the existing ones. In a level: 319
used, 193 free.

## 2. The rules, as read in the exe (ZGUIXMLReader2)

Reader set-up 0x87e9e0 (in read-file 0x87e930): +0x1b0 = "PC" (0xb44750), +0x1b4 = "PC_GC" when
`[manager+0xaf68]` else "PC_KEYBOARD", +0x1b8 = language name (table 0xcd8dcc[ [0xdda79c] ]: English German
French Spanish Italian Dutch Russian Polish Japanese), +0x1bc = region name (0xcd8df0[ [0xcd8e00] ]:
NorthAmerica Europe Asia Rest), +0x1c0 = ini `BuildTag` or "Default", +0x1d0 = include flag (starts 1),
+0x1d1.. = its stack, +0x1e4 = depth. The file is loaded whole through `[0xdd263c]` slot 26 and parsed by
0x79edf0 -> tokenizer 0x7b9700 (see 3).

Start element 0x8ce850, in this order:
1. `ExcludeIn` (0x8ce8bd): push the flag; read each key as a bool (0x86f6e0: the value must be the word
   True or False, anything else = absent); the flag is CLEARED when a True key's condition holds:
   FA `0x863a60(session) && [session+0x5c]==4` | Arcade `0x7f6850` | Campaign `0x7aca80` | Demo
   `[[0xdd265c]+0x8ad]` | HiddenDemo that && `+0x8ae` | Normal NOT `+0x8ad` (so `Normal="True"` blocks are
   out of the retail game) | GameRelease ALWAYS | GermanSKU / NotGermanSKU ini `0x793550("GermanSKU")` and
   its negation | JapaneseSKU / NotJapaneseSKU likewise | Extreme `[0x156b5f0]==3` | Hard `==2` |
   PreviewBuild `+0x8af` | LifePreviewBuild `+0x8b0`. The key "FA" IS in the exe (0xb6ca28; re/menus.md 2.1
   said it was not). Unknown keys (`Preview`) do nothing.
2. `Platform`, and `BuildTag` when +0x1c0 is set (always): ONE shared rule at 0x8cef26. included =
   old && (b16 || b15) where b16 = attribute "PC" (exact case) as bool, or - only when there is no "PC"
   attribute at all - the attribute named after the BuildTag ("Default", case-insensitive); b15 = the
   attribute named PC_KEYBOARD / PC_GC. XENON and PS3 are never read. So on a keyboard
   `<Platform PC_GC="True" XENON="True" PS3="True">` is OUT and `<Platform PC_KEYBOARD="True" PC_GC="True">`
   is IN. (menus.md 2.1 "how the two lookups combine is not established" - this is it: OR.)
3. `Locale` (0x8cec41) / `GameRegion` (0x8cecbd): included = old && attribute named after the current
   language / region (case-insensitive) is True. No attribute = out.
4. `MainIniOption Name=K Value=V` (0x8ced39): included = old && atoi(ini K) == V (V default 1, missing key 0).
5. Anything else with the flag CLEAR: nothing is made, a null is pushed (0x8cee45).
6. Anything else with the flag SET (0x8cee51): `tmpl = 0x7a1ff0(attr "Template")`; `eff = 0x5532b0(attrs, tmpl)`
   (merged attributes, the element's own first). If tmpl exists AND has children (`[tmpl+0x5a0] !=
   [tmpl+0x5a4]`): `tmpl->0x403060(parent)` attaches tmpl's children to the enclosing object through its
   AddChild slot (`parent->vtbl[2](tag, child)`; the SAME objects, no clones) and a null is pushed: the
   element itself makes NOTHING. Else `obj = 0x4ecea0(tag, attr "Type" of eff)`:
   - tag "Template" -> 0x686270: a reader definition slot (512 cap above), NOT a table entry;
   - else 0x579650 (the manager): "GuiElement" with a Type -> 0x7fad10 asks the factories
     (ZMercsMenuFactory 0x859460: 146 names, ZStandardMenuFactory 0x5fa2d0: 18; re/menu_factory_names.json);
     unknown -> NULL, nothing; known -> table entry kind 0 (0x7fad5d; int3 at 0x7fad8d when the count is
     0x13e8). "ColorSet" -> 0x47d5e0, entry kind 2 (0x47d629). "ButtonGraphic" -> 0x53c720, kind 3
     (0x53c769). "Window" -> 0x667e00 with the Type or "Standard", kind 1 (0x667e5e; int3 0x667e6e).
     A GuiElement WITHOUT a Type (template missing, empty, or defined in an excluded block) falls through
     the name chain to 0x7b0fa0 like Text / Graphic / GraphicElement / Windows: no entry.
   Then `obj->vtbl[1](eff, manager)` reads the attributes.
End element 0x5dcf30: a conditional tag pops the flag; otherwise, with the flag set, `child = stack.back()`,
`parent = stack[-2]`, `parent->vtbl[2](tag, child)` when both exist (so a `<Template>`'s children are made
ONCE, at the definition, and attached to the definition; instancing re-attaches them).

## 3. The tokenizer is not XML (0x7b9700, 0x4b4be0, 0x674120) - rules a Hire window must respect
- Between tokens the bytes <= 0x20 and `. - _ :` are skipped; any other byte that is not `<` ends the
  file (token 4 = error: the elements made so far stay, the rest of the file is never read). Stray text
  between tags truncates a menu file SILENTLY. A `<?xml ...?>` first line would end the file at once ('?'
  is no name character). The stock files start with `<Windows>`.
- A comment `<!--` ends at the FIRST `-->`; a `<!--` inside is text. Patch01 frontend.xml:2656 nests one
  (so expat refuses the file; the tool has its own tokenizer).
- Names and bare values are runs of isalnum `. - _`; a quoted value runs to the next `"`, no escapes, no
  entities. A repeated attribute name: the FIRST wins (0x612380). More than 50 attribute pairs, or a
  malformed one, = token 4.
- `<a .../>` = start + end; `</a>` = end. Tag nesting is not checked.

## 4. Open / GUESS
- GUESS 1: 0x7a1ff0 (template lookup by name) is modelled as exact, then case-insensitive, over the slots
  defined so far (a template defined LATER in the file, or in another file, is not found).
- GUESS 2: the menu scene's own ZWIN* entities are not in this table; only XML-made objects are counted.
- The in-level `online.xml` is the level zip's own; whether Patch01's would override it (menus.md q9) is
  unchanged. The model counts the file you give it.
- Only the K0 line (`[[[0xdd265c]+0x824]+0x9f48]` logged after each XML load) turns these estimates into
  numbers; the model predicts frontend 4793 / level 2775 on the owner's live install, keyboard.

## 5. Tool
`python tools/kl_menu_count.py selftest <dir>` (the dir holds patch01_frontend.xml, patch01_ingame.xml,
frontend_online.xml pulled from the stock archives; the check-in left a copy in
`<work>\research\sched_1024_menu\` with the live overlay and map variants beside them);
`python tools/kl_menu_count.py frontend <frontend.xml> <online.xml> [--gamepad]`;
`python tools/kl_menu_count.py level --arcade <ingame.xml> <online.xml>`. Exit code 1 when over 5000.
kl_expansion.py / kl_hud_menu.py `check` could call `Counter` instead of their tag-sequence rule once K0
has confirmed the model (not done: those are the owner's install tools).
