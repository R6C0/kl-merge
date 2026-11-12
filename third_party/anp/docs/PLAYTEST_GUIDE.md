# ANP playtest guide (build out_rel5, 13 Oct 2026)

What to expect in each Dead Men chapter, and what to look at. The one-line level descriptions come from the chapter titles and cutscene names, so they may be loose. "Seen" means our unattended tests saw it. Everything else in a level is untested.

## Controls (Dead Men features in Dog Days)
| Key | What it does |
|---|---|
| **C** | Take cover (Dog Days' cover key). Dead Men snapped into cover by itself, and some hints still say so. |
| **W + E** at a ledge | Climb (crates, vans, walls), with 3 heights like Dead Men |
| **E** at a rappel point | Rappel down. Some rappels (M09) are multi-stage: press **S/W** to jump down the wall |
| **4** | Give the gun in your hands to the selected crew member within 3 m. If he already has that type of gun, you get his back |
| **G** | Throw a grenade |
| **1 / 2 / 3** | Crew orders: follow / fire at / defend. Tap = selected merc, hold = all |
| **Tab / Shift+Tab** | Select the next / previous merc |

## New since 11 Oct
- **M02 now plays end to end the Dead Men way.** You give Lynch the Remington and the Taurus yourself (stand close and press 4 with that gun in your hands). Kane gets the P90 and USP, and old guns are replaced as in Dead Men. Then cover practice (C, then aim and blind-fire from cover), grenades, rappel, fight, exit, and M03 loads.
- **Crew members have Dead Men's health** (about 8.5× tougher than before), so they no longer die in one or two hits. That had caused M03B's restart loop.
- **Cover:** every Dead Men cover box works with C. Dog Days already used most of them. We only rebuild the few that lie tilted in Dead Men's data.
- **Explosions do Dead Men's damage.** Before, every explosion did 1000.
- **Crashes fixed:**
  - quitting a level to the menu, which was the most common crash (Dead Men's handcuff chains/ropes);
  - rappel;
  - weapon swap;
  - M03 checkpoint reload;
  - M12/M13 sound.

## Everywhere
- **Damage is fixed.** One bullet should cost a small slice of health, not kill you.
- **Known gaps:**
  - If a crew member dies, the mission fails and restarts at the last checkpoint. Dead Men downed them first so you could revive them; the revive is built but not switched on yet (it's being tested).
  - Things that come by car can happen without the car. The vehicles are switched off, and their triggers now fire on their own in M01 (the escape), M03 (the getaway van), M07 (the monster truck), M09B (the getaway car) and M11 (the BTR).
  - Not active yet: crowds (they just stand), plants, ropes and rain, and mounted machine guns.
  - The pause menu: unverified. Please check whether Esc shows anything.
  - M03 (the bank) is about stealth at the start: firing raises the alarm, and the mission fails, as in Dead Men.
  - Climbing works anywhere you could climb in Dead Men: hold W and press E at a ledge.
- **Report for every level:**
  - crashes, with the time;
  - places where you're stuck with nothing happening;
  - silence where there should be sound;
  - cutscenes that don't play.

## 1. Impact (M01)
- **The level:** the prison-transport crash and the escape with the crew.
- **Seen:** loads; intro cutscene and movie; 21 cutscenes started in 5 min; continuous audio. Fixed since: the 0xcccccccc crash about 1 min in.
- **Check:**
  - Climbing (W+E) on the crates and the van.
  - Does Lynch follow you?
  - Can you take several hits and survive?
  - **The end:** does the escape trigger, and does M02 load? This was impossible before out_rel2.

## 2. Trial (M02)
- **The level:** the tutorial: guns, cover, grenades, rappel.
- **Seen (13 Oct, unattended, faithful build):** the whole level to M03. The order is:
  1. Lynch's car (Remington);
  2. give the Remington to Lynch (4);
  3. pick up the P90 (E);
  4. pick up the Taurus (E);
  5. give the Taurus to Lynch (4);
  6. pick up the USP (E);
  7. cover practice at the vending machine (C, then aim with RMB and blind-fire with LMB from cover);
  8. grenades (E to pick up, G to throw);
  9. rappel (E on the roof);
  10. a firefight;
  11. "Press 1" to make Lynch follow you;
  12. the exit, then M03 loads.
- **Check:**
  - The give step: Lynch should visibly hold the gun.
  - Cover with C.
  - After the Taurus pickup Kane may still hold the P90; switch with Q.
  - Lynch right after the rappel: in a test he bounced between roof and ground for a few seconds.

## 3. Withdrawal (M03)
- **The level:** the bank job (garage, vault, lobby).
- **Seen:** loads; cutscenes start; audio. Fixed since: a crash about 1 min in.
- **Check:**
  - The vault door and the "hands shaking" scene.
  - The alarm and the lobby fight.
  - The rappel, if there is one.

## 4. Cracking Up (M03B)
- **The level:** the van chase after the bank. The van doesn't drive in Dog Days, so the chase is replaced by Dead Men's own teleports between its on-foot stages:
  1. the tunnel roadblock (kill the snipers);
  2. the underpass crash;
  3. picking up the bag;
  4. the subway, then M05.
- **Seen:** the teleport into the tunnel works. Before the crew-health fix, a crew member died in seconds there and the level restarted in a loop. That's fixed in out_rel5 but not yet re-tested.
- **The ending (as in Dead Men):** when "GET TO THE TRAIN" shows, go right up to the train doors and stand on the yellow strip at the platform edge, with Lynch on the platform near you. The level ends about 5 s later. Miss the ~20 s window and you get "missed the train".
- **Check:**
  - Does the crew survive the roadblock?
  - Do the stage teleports follow each other?
  - Does it end in M05?

## 5. The Mizuki (M05)
- **The level:** the nightclub; Yoko.
- **Seen:** loads; 11 cutscenes; audio. Kidnap cutscene fix included (they were dead before).
- **Check:**
  - Do the kidnap cutscenes play?
  - Does the nightclub feel empty (crowd off)?
  - Do guards warn before shooting? That isn't ported yet.

## 6. Exchange (M06)
- **The level:** the exchange.
- **Seen:** loads; 4 cutscenes; audio; 5 min clean.
- **Check:** whether the exchange scene plays and you can go on from it.

## 7. Reunion (M07), then the funeral cutscene (M07F)
- **The level:** Kane's family.
- **Seen:** loads; 8 cutscenes; audio. At the end: M07 → funeral cutscene → M08, automatically.
- **Check:**
  - Does the funeral play with sound and lead into M08?
  - Do enemies go after the daughter? That isn't ported yet.

## 8. Breakout (M08)
- **The level:** the prison break.
- **Seen:** loads; 7 cutscenes; audio; 5 min clean.
- **Check:**
  - The blast scene.
  - The prisoner crowd (off, so it may look empty).

## 9. Retomoto Tower (M09)
- **The level:** the rooftop start and the office tower.
- **Seen:** loads. The intro replays every time a crew member dies in the first fight (mission fail → restart).
- **Check:**
  - Can you keep the crew alive and get past the roof?
  - The rappel down.

## 10. Tokyo Streets (M09B)
- **The level:** the streets of Tokyo.
- **Seen:** loads; 8 cutscenes. Fixed since: a crash at 45 s.
- **Check:**
  - The tear-gas scene.
  - The lobby "nearly there" talk.
  - Whether you can leave the start area.

## 11. Freedom Fighters (M11)
- **The level:** Havana, with the rebels.
- **Seen:** loads; 6 cutscenes; audio; 5 min clean.
- **Check:** the machine-gun nests (off: are you blocked by needing one?) and the attack from below.

## 12. El Capitol (M11B)
- **The level:** the rally and the capitol.
- **Seen:** loads; 3 cutscenes; one 8-second freeze (it recovered).
- **Check:**
  - Any freezes, and how long they last.
  - The rally crowd (off).

## 13. Bird's Eye View (M12)
- **The level:** the jungle, from above.
- **Seen:** loads; 8 cutscenes. Fixed since: the crash at about 4.5 min.
- **Check:**
  - Past the 5-minute mark.
  - The flare and grenade scenes.
  - The plants (off).

## 14. Within The Walls (M13)
- **The level:** the walled compound.
- **Seen:** loads. Fixed since: the crash at 26 s.
- **Check:**
  - Get past the first minute.
  - Can you reach the end?

## 15. Choice (M13B)
- **The level:** the final choice.
- **Seen:** loads. Its car fail-safe crash is fixed.
- **Check:** whether the choice comes up, and which ending each option leads to.

## 16. Consequence (M14)
- **The level:** the ending.
- **Seen:** loads (60 s test only).
- **Check:**
  - The church scene (its cutscene was fixed).
  - Whether the ending plays.
  - What happens after it (credits aren't ported yet).
