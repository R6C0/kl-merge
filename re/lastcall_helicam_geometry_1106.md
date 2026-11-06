# Last Call (DM05A) escape camera: geometry findings, 2026-11-06

Offline research on live zip `KLExpansion\Maps\DM05A\F01_Main.zip` (md5 e6d2f73e). Nothing written to the game folder, no game launch.
Units cm, y up. Problem: EscCamera01 shows black (run 1) or a flat uniform grey (run 2, variant A: LookAtPos, aim EscCameraLAST (7800,2271,3500), f5=-900, f6=+200) after the heli leaves.

## Readers used
- `tools/kl_map_escape.py` (Level, Ground collision proxy, heli spline)
- `tools/kl_octree.py` (read, Tree, RoomIndex: rmi inside boxes, rmc camera boxes)
- `tools/kl_prmgraph.py` (read, root chunk, bounds at +0x20) and `tools/kl_scene.py` (Entity.model)
- Own scratch scripts (ray cast against the HVK Ground triangles; advisory only).

## Method notes
- Octree record boxes are record-local, not world geometry. Not used. World bounds come from the .prm root bounds (+0x20) transformed by Level.frame; these agree with the HVK collision.
- Parity "inside solid" ray tests are unreliable: the collision shells are open. Treat them as advisory.

## Findings
1. Points in geometry. BuildingF is a large tower mass directly west of the pad, and the heli Escaping route flies into it. Both variant A eyes (hover eye and park eye) lie inside F's bounds and outside the rmi pad room boxes (rmi ceiling y 2610). So the eye is inside a solid: back faces are culled and the view shows nothing but whatever is behind, which explains black or flat grey.
2. Facade and windows. The original fixed eye sat 258 cm from F's wall, with the lit Building_H_03 facade behind the hovering heli. The lit windows face the pad from the east side of F; a camera east of F's face sees them.
3. Fog, sky, environment. No fog or post-filter cause was found near the pad. Skydome/Distance/Glow billboard shells exist but none encloses the pad. No lights sit within 1 km of the park position above y 2000, so a view into the sky above y 2000 is unlit sky colour (flat grey/black) with nothing to see.
4. Heli distance to EscCameraLAST. The route runs into BuildingF, so the park point itself is the root problem; no f5/f6 offset from a point inside F can fix the view.

## Conclusion
Key conclusion: the park point should change (end the spline east of F), or the eye must be kept east of F's face (x >= about 6850) inside rmi box 7 with y <= 2610.

## Candidates (all offsets are GUESSes; f5 ~ world x offset, f6 ~ scaled y offset, per the helicam plan)
- Candidate A, keep route, move eye: LookAtPos, aim stays the heli or Building_H_03 (not the empty EscCameraLAST). f5 = +700, f6 = -500 (range -400..-800). GUESS. Expected view: eye east of F's face looking west at the heli against the lit Building_H_03 windows, F's facade filling the background, heli lifting away; no solid around the eye.
- Candidate B, small offset plus route fix: f5 = -450, f6 = +100, used only for hover and rise (GUESS), and cut or reroute the spline so the park lies east of F (the lcoutro 6-point spline ends before reaching F). Expected view: heli rising into open air with the lit facade behind, and no dive into the tower. If the park cannot move, use Candidate A.

Both need one live bench to confirm; run order: A first (no spline change, smallest edit).
