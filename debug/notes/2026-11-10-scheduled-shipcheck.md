# 2026-11-10 scheduled check-in: shipped-ini review (offline, tools/kl_ini_shipcheck.py)

Input: C:\kl_build_1024\bench_1110\DM03BS_1110\KLHook_base.ini (02:19 UTC, 82903 bytes = the live ini per the kl_bench_1110 commit "base ini = live ini"),
checked against klhook/KLHook.ini. No ERROR (no absolute owner path in any VALUE). Comments: 7 lines name C:\kl_build_1024\... UNDO kits (fcs_1106 x6, echo_1108): cosmetic for a tester. The T0 "Owner: shipped-ini review" questions:

```
WARN  line 437   [CarDown] Dry=1                                    sample says: (recommended off)
WARN  line 1313  [Brain] OnlineBrainTraitorRayAim=1                 sample says: (recommended off; UNTESTED; TEST build only; CHANGES the game: rewrites the muzz
WARN  line 1320  [Brain] OnlineBrainTraitorHolderSet=1              sample says: (recommended off; UNTESTED; TEST build only; CHANGES the game, host only, online
WARN  line 1323  [Brain] OnlineBrainTraitorFireLine=2               sample says: (recommended off; UNTESTED; needs OnlineBrainTraitorArcade=1)
WARN  line 1325  [Brain] OnlineBrainTraitorDefendPull=2             sample says: (recommended off)
WARN  line 1328  [Brain] OnlineBrainTraitorCombatFlag=3             sample says: (recommended off; UNTESTED; TEST build only; CHANGES the game, host only, online
WARN  line 1334  [Brain] OnlineBrainBoard=1                         sample says: (recommended off; needs Build=1)
logging on (47): [Steam] Log=1, [Character] Log=1, [Balance] Log=1, [Fed] Log=1, OnlineTagProbe=1, OnlineShopNames=1, [HUD] Log=1, ReplicaProbe=1, [Down] Log=1, [BotDown] Log=1, [Adrenaline] Log=1, [CrewHop] Log=1, [Expansion] Log=1, [Bots] Log=1, [ReShade] Log=1, [Climb] Log=1, OnlineSwap=1, [Rigid] Log=1, [Voice] Log=2, [CarDown] Log=1, [Ambience] Log=1, [Music] Log=1, [Traits] Log=1, [FrameLimit] Log=1, [Unstick] Log=1, [Shield] Log=1, Enable=1, [Dying] Log=1, [VanBlow] Log=1, [StanceFix] Log=1, OnlineApply=1, [ShopPage] Log=1, [Grenade] Log=8, OnlineLooks=1, OnlineBank=1, OnlineBankCredit=1, OnlineGuardMode=1, OnlineLootParts=1, OnlineVanGatherSmart=1, OnlineBoardAll=1, [CharOnline] Log=1, [Hire] Log=1, [Campaign] Log=1, [CampSquad] Log=1, [CampGive] Log=1, [CampRappel] Log=1, [CampRevive] Log=1
RESULT: FAIL - 0 ERROR, 7 WARN (diagnostics / TEST-only on), 73 FEAT (sample says off until benched), 47 logging, 0 NOTE (KLHook_base.ini (live 02:19) vs sample klhook/KLHook.ini)
```

FEAT (73 keys the sample still marks "recommended off until benched / not run live" but the live ini has on: Bots, BotFill, Brain, Lobby, Echo ...):
the owner benched and chose them since; the SAMPLE comments are stale, not the ini. Not listed here; `python tools/kl_ini_shipcheck.py <ini>` prints them.

Sections in the live ini the sample does not document at all (a tester gets keys nobody wrote up): [Campaign] + Camp*, [Redirect.N]/[Page.N], [Wardrobe], per-map [Ambience.X]/[Music.X]/[Bots.X]: --notes lists them.

Reading: the 7 WARN are the only diagnostic / TEST-only keys on. CarDown Dry=1 = a dry run (log only) on every tester; the three [Brain] "TEST build only" keys are inert on the SHIP dll but say so in the log; FireLine=2 / DefendPull=2 / OnlineBrainBoard=1 are log-only modes by the sample text. The 47 Log=1 levels + OnlineTagProbe/ReplicaProbe are what a tester KLHook.log will carry: fine for a tester build (logs come back with the launcher Collect-Logs), noisy for a release.
