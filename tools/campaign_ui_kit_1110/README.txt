campaign_ui_1110 - luvsic's Dead Men UI, inside his campaign only (in contribution with luvsic)
===========================================================================================

What the owner sees after INSTALL.bat (everything else is untouched: Arcade, Fragile Alliance, online, the 9 stock maps, the Dead Men
FA maps, Dog Days' main menu):

1. In the 17 Dead Men campaign levels (M01 .. M14, M07F): Dead Men's own HUD artwork and typefaces (baked into each level archive by
   luvsic's dmhud.py / dmfont.py). GUESS: Dog Days' HUD code draws them without a fault (the converter's checks pass; never run).
2. Main menu -> Play: a fourth row "Dead Men Campaign" (under Resume / Single player / Online). It opens luvsic's page with
   New game (chapter 1) / Chapters (16 buttons, Dead Men's own titles, all nine languages) / Difficulty (Aspirin, Codeine, Morphine,
   Morphine+). Needs [Campaign] Routing=1 (already on). Takes effect at the next game start. [CampaignUI] Menu=0 hides it again.
   NOT in the menu: Continue (needs luvsic's loader), the Dead Dogs saga page, the intro movie (see the slice report).

Files changed (all backed up, all removed by UNDO.bat):
  Scenes\Locations\M01..M14 + Scenes\CutScenes\M07 : the level archives (hard-linked backups in <kit>\backup, old manifests too)
  KLExpansion\Overlay\Patch01*_campui.zip (4) + Patch01_campui.zip : NEW files beside the menu archives (the stock ones are not modified)
  dinput8.dll (pinned 258daf8e; backup dinput8.dll.before-campui1110), KLHook.ini (pinned c62045c9; + [CampaignUI] Menu=1)

Refuses (nothing written) while kl2.exe has a thread, when a pin differs, when a level was changed since campaign_1109, when a target
exists, or when the drive has no room (about 3.4 GB). 0-thread zombie kl2.exe processes do not block it.

MERGE NOTE: the dll in this kit is built from campaign-integrate 1abca43f (= the campaign_1110 camera/voice dll 258daf8e) plus
klcampui_logic.h and the klslot.c hook. A later dll from another branch must carry the same klslot.c change (kls_campui) and the
install.py pin must be updated.
