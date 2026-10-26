# Online FA loudness vs Arcade (2026-10-26, read-only investigation, nothing installed)

Finding: an online round loads the SAME sound banks as Arcade. KLHook.log 10-26 18:59:52 (DM09 slot F06) and 19:01:59 (DM02 slot F02):
`CreateFileA redirect ...F06_Main.WHD / F06_Main.WAV -> KLExpansion\Maps\DM09\F06_Main.{WHD,WAV}`; the archive is `F06_Main.bots.zip`, which differs
from the plain zip only in `Scenes/Locations/F06/F06_Main.prp` (checked DM09, DM02, DD05: same member list, same CRCs, same .snd).
All 42 banks (21 maps, 9 stock, 12 story) carry the 1025gunraw AND the 1025fxraw output (live md5 == manifest output_md5, backups *.before-1025gunraw / *.before-1025fxraw).
No runtime volume code exists (no groupvol / gain in klhook). `.SND` group volumes (shot_npc 0.35 / shot_player 0.70) were never changed.

Gaps (same in Arcade and online): 1025fxraw covered only SFX/Explosions, Impacts/GlassBreak, Impacts/Shatter/Glass, Fire/Cannisters. Not covered: Impacts/Bullet/Glass (glass hit by
bullets, -8..-18 dB), Glass_Crack (-14.6), Shatter non-glass (wood, plastic, concrete, cardboard, metal plate, ceramic), Metal_Break / Metal_Crack / Concrete_Break,
Impacts/Canisters (extinguisher / fuel can hit, -10.5), all Impacts/Bullet/* (214 records, median -12.5), grenade impacts; streamed stereo records (Retomoto
window blast `M09_Explosion_Window_Office`, vault explosion PCM stereo) cannot be patched in the .WAV. Cap-limited leftovers: Glass_Shatter_Small_01 (-7.8), _02 (-4.1).
GUESS: if a friend joins the private match, their PC plays their OWN banks: a stock install is quiet.

Staged (NOT installed): C:\kl_build_1024\sndonline_1026\ (kl_sndonline.py = kl_fxsnd.py derived, only records the fx pass did not touch).
 tierA_destruction     glass-hit, Glass_Crack, non-glass Shatter, breaks, canisters: 1516 records, 30 banks (maps + stock), 14.1 MB spans
 tierB_plus_bullets    tier A + every bullet impact (SNDON_BULLETS=1): 6219 records, 48.2 MB; loud on full auto: OPTIONAL
Each: INSTALL / UNDO "impact sounds*.bat", md5-chained, backups *.WAV.before-1026sndon, verify PASS (apply + undo byte-exact, guns untouched).
Choose ONE tier (both are built from the same live input).
