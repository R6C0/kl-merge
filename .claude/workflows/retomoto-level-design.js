export const meta = {
  name: 'retomoto-level-design',
  description: 'Design the Retomoto Tower Fragile Alliance round from the research docs, judge three designs, write the design doc, implement it in kl_fa_author.py and adversarially review the code',
  phases: [
    { title: 'Understand', detail: 'six readers over re/*.md and tools/*.py' },
    { title: 'Design', detail: 'three designs from different angles' },
    { title: 'Judge', detail: 'three judges score every design' },
    { title: 'Synthesize', detail: 'one design doc re/retomoto_design.md + implementation spec' },
    { title: 'Implement', detail: 'code changes in tools/' },
    { title: 'Review', detail: 'three lenses, up to two fix rounds' },
    { title: 'Critique', detail: 'completeness against the owner\'s concept' },
  ],
}

const PRE = `CONTEXT (read before anything else)
Repo: /home/user/kl-merge, branch claude/charming-johnson-xblvr1. It is a hobby mod that grafts Kane & Lynch: Dead Men
maps under Kane & Lynch 2: Dog Days' game systems. CLAUDE.md is the brief (you have it). NO GAME FILES EXIST IN THIS
CONTAINER: nothing in tools/ can be run against a level, and any 'python tools/x.py ...' that loads a level or the
work folder will fail - do not try more than once. Work from re/*.md, CLAUDE.md and the source in tools/*.py.
Cite file:line for every fact. Mark anything inferred as ASSUMPTION and anything invented as GUESS, exactly as the
project's docs do. Do NOT edit any file unless your task says so. Return raw data per your schema, not prose for a human.`

const OWNER = `THE OWNER'S CONCEPT (CLAUDE.md, 'Owner's design for it (2026-10-09), to be followed as given'):
- Start: the heisters are ALREADY rappelled down at the main window, with the explosion sound playing as the round
  begins (the way stock Subway opens in the middle of the job). No rappel sequence. Straight into action as the main
  window blows.
- Part 1 (tower): fight through; loot comes from the STATUES, and from the MAIN ROOM once everyone in it is dead.
- Part 2 (lobby/street): out through the front entrance, down the road to a VAN, and escape. Mood reference: the
  street shoot-out in the film Heat.
- The assistant is to design how the two parts join. Its level music plays.
Also from CLAUDE.md: Dog Days keeps everything, Dead Men content is additive; Dead Men player models and voice lines,
Dog Days guns and sounds; Retomoto = M09_A (tower) + M09_B (lobby/street) in ONE Fragile Alliance map under F07's
systems. A first-pass FA layer already exists: tools/kl_fa_author.py with its spec re/retomoto_fa.md (built offline,
never run in the game). The survey of both parts is re/retomoto.md; the two-part build is re/maps.md section 5.`

const FACTS = {
  type: 'object',
  properties: {
    facts: { type: 'array', items: { type: 'object', properties: {
      fact: { type: 'string' }, source: { type: 'string' }, status: { type: 'string', description: 'read | ASSUMPTION | GUESS | LIVE (only a run can settle it)' } },
      required: ['fact', 'source', 'status'] } },
    tables: { type: 'string', description: 'markdown tables with coordinates / names / fields, ready to paste into a design' },
    unknowns: { type: 'array', items: { type: 'string' } },
    advice: { type: 'string', description: 'what a designer of the round must respect from this area' },
  },
  required: ['facts', 'tables', 'unknowns', 'advice'],
}

const READERS = [
  { key: 'fa-layer', prompt: `${PRE}\n${OWNER}\nTASK: everything known about the HOST level F07's Fragile Alliance gameplay layer and how tools/kl_fa_author.py already uses it, so that a designer can re-use F07's police squads as waves in the Retomoto street.
Read tools/kl_fa_author.py (whole), tools/kl_fa.py (host_keep, repair, prune, controllers, node_values, edit, _refs, check), tools/kl_graft.py (Select, picks_of, build around lines 660-1050: how S's subtrees are kept or dropped, dm_rename, Heroes! handling), tools/kl_prpjoin.py (sides, graft_picks, references, resolve), tools/kl_maps.py (campaign_drop, chain, world), re/fa_gamemode.md section 2 (F01's wiring as the model of an FA level), re/fa_round.md sections 1 and 6, re/maps.md sections 3.2, 5, 8.
Answer precisely: (1) which F07 top-level names are known (every 'Gameplay!...', 'FASpecials!...', 'Specials!...', 'Animation/F07/...' string in the repo, with what each is); (2) how a police squad is built (ZSquadScript + routs + Pos boxes + actor groups) and how a trigger starts one; (3) whether F07's Gameplay!020_Loot!* / other police squads currently come into a Retomoto build or are dropped (trace Select(s_keep) + KEEP + picks_of), and what it takes to keep them; (4) exactly how a kept F07 subtree can be moved rigidly to a new place (kl_fa_author.place() on its top node: preconditions - parents identity at origin, .prp ZGEOM[1]/[2] and the .gms record both set; whether children with their own ZBoxPrimitive / defend boxes follow; Havok and nav-mesh caveats); (5) what kl_fa_author.wire() may and may not do (values and reference lists only; order relative to kl_fa.repair's prune); (6) what kl_fa.check would flag. Put every F07 name you find in 'tables'.` },
  { key: 'street-atlas', prompt: `${PRE}\n${OWNER}\nTASK: a coordinate ATLAS of M09_B (lobby, forecourt, road, north road, overpass, bus terminal) for placing a 'Heat'-style police shoot-out on the road between the front entrance and the escape van.
Read re/retomoto.md sections 1.2, 1.4, 3.4, 4, 5 (B tables), 7; re/retomoto_fa.md sections 1, 2, 4, 5; tools/kl_fa_author.py (constants ROAD_X, VAN_STOP_Z, PLACE, POLICE, STAGE_D, SQUADS, squad_plan, place_vans). Units: 1 unit = 1 cm, y up, 'north' = +z in the object names.
Produce in 'tables': (a) every named place with coordinates (door, forecourt, gardens, road centre line and width, static police cars and road blocks with node ids, SWAT truck, north bound, south bound, overpass entrance, bus terminal, lobby bounds, elevator landing); (b) the campaign B squads kl_fa_author keeps (Enemies!010_RetoBldFront!, Enemies!020_Street!) with their start boxes; (c) the three vans' fitted stops and drive z ranges; (d) the exit box; (e) the AFTER_DEATH / team-mode points on this part. Then: a proposed ZONE plan for the shoot-out (forecourt -> road south of the first road block -> the road block -> the van stops), each zone with a box (centre, half extents) on the road and the cover available, flagged GUESS where you choose numbers. State what is below the tower in this part (what a player falling out of the main window would hit).` },
  { key: 'tower-atlas', prompt: `${PRE}\n${OWNER}\nTASK: a coordinate ATLAS of M09_A (the tower interior) for pacing the fight from the boardroom down to the escape elevator.
Read re/retomoto.md sections 1.1, 1.3, 2, 3 (whole), 4.3, 5 (A tables); re/retomoto_fa.md sections 1, 2, 3, 5, 6; tools/kl_fa_author.py (FLOOR3, START, TRAITOR, POLICE, STAGE_B, STAGE_C, STATUES, MAIN_ROOM, CAMPAIGN_KEEP, SQUADS, NOT_SQUADS, squad_plan, wire). Units: 1 unit = 1 cm, y up.
Produce in 'tables': (a) rooms with bounds and floor heights; (b) the route boardroom -> reception -> atrium 3rd -> stairs -> 2nd -> stairs -> 1st -> elevator lobby -> escape car, with the door/stair/car coordinates and the room each step is in; (c) the 15 samurai cases and 4 sword cases with room and floor; (d) the 23 kept A squads by campaign area (020_Office, 030_Reception, 040_Atrium_3rd, 050_Atrium_2nd, 060_Atrium_1st, 070_Elevators) with actor counts and start boxes, and which are NOT kept and why; (e) the blast objects and what the campaign swaps (window pre/post, chairs, door whole/broken, elevator doors); (f) the spawn row and traitor points. Then: where TRIGGER BOXES for staged waves could stand (one per descent step: boardroom door, reception->atrium, each stair foot, elevator lobby), each with centre + half extents fitted to the room bounds (GUESS-flagged), and where a KillBox / level bound belongs for the roof side, the window drop and the atrium void. Note: the roof (Out_Roof_401) and TopOffices_401 are reachable only by rappel in the campaign - say whether a player can get there at all.` },
  { key: 'mechanics', prompt: `${PRE}\n${OWNER}\nTASK: the stock Dog Days mechanisms a designer may use for pacing, with their fields and proof state.
Read re/fa_gamemode.md (whole), re/fa_round.md sections 1-2 and 6, re/retomoto_fa.md section 3.1, tools/kl_fa.py (check(): every finding and what it reads off the exe), and look up the field lists of these controllers in re/kl2.json (first inspect the JSON structure with python -c to find how controllers and their field type letters are stored; cite the entries): TriggerBox, TriggerDelay, TriggerDelay2, TriggerCounter, AIDWrapper, ActivateGeom, DeactivateGeom, ZSquadScript, DefendBehaviourRout, RunToCoverBehaviourRout, SquadModifierBehaviour, RandomTrigger, TriggerActorsDead, OnlineSpawnpointTrigger, JumpPoint, OnlineGamePlayTrigger, PointOfInterest, KillBox, LevelBound, DocuCamControl, ShakeCamera, OnlineMoneyCtrl, OnlineMoneyContainer, TriggerBox2, OnlineExitLevelTrigger, OnlineEscAnimatedVehicle, OnlineEscVehicleMonitor, OnscreenMessage, PlayMusic, PlayMusicLayerFade, Explode, MatPosAnimProxy, RelayMessageList, Elevator.
For each: the field list (index: type / enum / what it is where known), how stock FA levels use it (with the examples the docs give), and its state: read in code / seen in stock / ASSUMPTION / LIVE. Also: the settings object ZOnlineFragileAllianceSettings fields that set the round clock, loot targets, music (157/158) and the start window; TriggerBox field 14 values (who may fire) and field 13 ('eTGS_AllInside' vs 'eTGS_AllDead'); what 'AITrigger' is. Put the field lists in 'tables'.` },
  { key: 'audio-music', prompt: `${PRE}\n${OWNER}\nTASK: how the level's music (Music/InHouse/Japan/M09_A/*, 7 clips) and the missing stream clips get into the game, and what code change does it.
Read re/retomoto.md section 6, re/retomoto_fa.md section 6, re/audio.md sections 0, 5, 6, 7, 8, 10, re/maps.md section 7 (patch 3 about kl_audio.merge) and 4.2, tools/kl_audio.py (whole: FA_FILTER, merge, verify_merge, main), tools/kl_snd.py (graft_audio and how streamed clips are resolved against PC_Def.str: grep 'str' / 'stream'), tools/kl_graft.py (where graft_audio and the stream file are used; 'stream_clips_missing' in tools/kl_maps.py), tools/kl_fa.py (S_MUSIC, settings_from_host).
Answer: (1) what FA_FILTER is now and why the 7 music clips and the Japanese guard lines are not merged; (2) the exact, minimal code change to kl_audio.py (and any caller) that adds them - give the patch as a unified diff in 'tables', with the owner-facing command to rebuild PC_Def.str and what must be reinstalled; (3) the two routes to play music in a round (PlayMusic object sent 'AITrigger' vs settings field 157 = clip offset) with the evidence for each and the LIVE test that decides; (4) what the window explosion, bomb warm-up and glass sounds need; (5) risks: bank size limits (waves 4,806 / sounds), PC_Def.str being the merged one on disk. Nothing can be run here; the patch is to be reviewed by reading.` },
  { key: 'join-net', prompt: `${PRE}\n${OWNER}\nTASK: the join between the tower (y 19,600) and the lobby (y 560), police respawn across the two heights, and the escape vans: constraints and the ordered live tests.
Read re/retomoto_fa.md sections 3, 4, 5 (police respawn), 8; re/maps.md section 5.6 and 6; re/retomoto.md section 2 (whole) and 3.4; re/netcode.md (whole: object addressing, owner-authoritative movement, what replicates); re/fa_round.md sections 5.4, 6.2, 6.4; tools/kl_fa_author.py (CAR_A, CAR_B, ROLE join/join box, wire() join lines, POLICE, SPAWN).
Answer: (1) the JumpPoint mechanism as read (addresses, what moves, crew flag, who is moved in multiplayer: the three cases) and what a designer should assume for Arcade (one human) vs online; (2) how the elevator ride should READ to a player (doors, timing, fade - does JumpPoint fade? what does a stock jump look like) and whether a TriggerDelay between the box and the jump is possible; (3) police: where AFTER_DEATH points are now, whether police can follow heisters down (they ride the same car), what OnlineSpawnpointTrigger can and cannot do for moving the police respawn from tower to street, and what the round rules do when the heisters have left the tower; (4) the vans: the baked drive, the three stops, the static Havok obstacle risk at (-450,0,0), the kill box, and the alternatives; (5) the exit box and 'BOARDS'. Give an ORDERED list of live tests (direct boot first, then round) with the pass criterion for each and what to change on a fail.` },
]

phase('Understand')
log('Understand: 6 readers over the research docs and tool sources (no game files in this container)')
const reads = await parallel(READERS.map(r => () =>
  agent(r.prompt, { label: `read:${r.key}`, phase: 'Understand', schema: FACTS }).then(x => ({ key: r.key, ...x }))))
const known = reads.filter(Boolean)
log(`Understand: ${known.length}/6 readers returned (${known.map(k => k.key).join(', ')})`)
const KB = known.map(k => `=== ${k.key} ===\nFACTS:\n${k.facts.map(f => `- [${f.status}] ${f.fact} (${f.source})`).join('\n')}\nTABLES:\n${k.tables}\nUNKNOWNS:\n${k.unknowns.map(u => '- ' + u).join('\n')}\nADVICE: ${k.advice}`).join('\n\n')

const DESIGN = {
  type: 'object',
  properties: {
    title: { type: 'string' },
    angle: { type: 'string' },
    design: { type: 'string', description: 'the whole design as markdown with the fixed section list; coordinates in every table; GUESS / ASSUMPTION / LIVE marks' },
    changes: { type: 'array', items: { type: 'object', properties: {
      file: { type: 'string' }, what: { type: 'string' }, how: { type: 'string', description: 'concrete: which constants / tables / functions, which stock objects, which fields and values' }, risk: { type: 'string' } },
      required: ['file', 'what', 'how', 'risk'] } },
    live_tests: { type: 'array', items: { type: 'string' } },
    open: { type: 'array', items: { type: 'string' } },
  },
  required: ['title', 'angle', 'design', 'changes', 'live_tests', 'open'],
}

const SECTIONS = `Use EXACTLY these sections, in this order, each with tables where numbers are involved:
0. The round in one page (timeline from round start to escape with seconds, by whom, and what the player sees)
1. The opening (spawn row, the blast, camera, HUD/briefing, what is swapped)
2. Part 1 - the tower: the fight (which squads, started by what, where; waves per floor), the statues (loot values, reach), the main room (gating, the counter), traitor dynamics, time budget
3. The join: how the elevator ride reads, trigger, doors, police following, what online needs
4. Part 2 - the street as Heat: zones from the front entrance to the van, police waves (which stock squads, from where - F07's kept squads moved as rigid groups and/or the campaign's B squads - start triggers, defend positions, cover from the static cars), the SWAT truck, sirens, what makes it read as Heat (open street, long sight lines, cars as cover, police arriving in numbers)
5. The escape: vans (stops, which fit, order), the exit box, BOARDS, the camera, 'last van', failure modes
6. Spawns, respawn and team modes (START, TRAITOR, AFTER_DEATH, UCC, TEAM stages B/C/D, cameras)
7. Bounds and kill boxes (roof, the window drop, the atrium void, the street west/north/south)
8. Music and sound (what plays when, the clip merge, the two music routes, the LIVE test)
9. Implementation: every change to tools/kl_fa_author.py (constants, PLACE entries, ROLE, KEEP, wire() lists) and tools/kl_audio.py, in the order to apply, each with its source for the numbers
10. Live test order (each with a pass criterion and the change on a fail)
11. Risks, most serious first, and what is GUESS`

const ANGLES = [
  { key: 'stock-faithful', text: 'STOCK-FAITHFUL: mirror how stock F01/F07 pace a round (opening, loot area, police waves started by MERCONLY trigger boxes as the criminals advance, respawn-only triggers for the police side, escape) using only idioms that stock levels use, with F07\'s own police squads re-placed as rigid groups. Prefer what has been seen in a stock level over what merely exists in the exe.' },
  { key: 'cinematic', text: 'CINEMATIC / HEAT: maximise the feel the owner asked for - the blast opening, a descending fight past the statues, the elevator as a beat, then an open street with long sight lines where police arrive in numbers along the road, cars as cover, the SWAT truck, the van at the end of the road. Use every stock object that serves the mood (DocuCamControl jolt, ShakeCamera, sirens, OnscreenMessage, PointOfInterest markers, spawn cameras) but keep it buildable with kl_fa_author.' },
  { key: 'risk-first', text: 'RISK-FIRST: minimise the number of LIVE unknowns between the owner and a playable first round. Everything on mechanisms already seen working in the live bank round (re/fa_round.md 6.2) or in stock levels; stage the design so that the first live build has the fewest new things, with the Heat street and the main-room gating as switchable later stages (module flags), and name for each feature the single live test that unlocks the next.' },
]

phase('Design')
const designs = (await parallel(ANGLES.map(a => () =>
  agent(`${PRE}\n${OWNER}\nYou are one of three level designers. ANGLE: ${a.text}
Everything the readers established (cite their sources when you use them; do not re-read the whole repo, but DO open
tools/kl_fa_author.py and re/retomoto_fa.md yourself, and any doc you need to settle a number):
${KB}
Write the complete design of the Retomoto Tower Fragile Alliance round. ${SECTIONS}
Rules: every position is a number with its source (a stock object, a campaign actor, a room bound) or GUESS; every
mechanism carries its proof state; only stock objects that F07 or the two campaign parts already contain (no new
entity, no new controller - that is kl_fa_author's rule, re/retomoto_fa.md section 0); the design must be buildable
by editing tools/kl_fa_author.py's tables and wire(). Be concrete enough that an implementer who has only your text
and the code can make the change. The 'changes' array is the implementation spec.`,
    { label: `design:${a.key}`, phase: 'Design', schema: DESIGN }).then(d => d && ({ key: a.key, ...d }))))).filter(Boolean)
log(`Design: ${designs.length}/3 designs (${designs.map(d => d.title).join(' | ')})`)

const VERDICT = {
  type: 'object',
  properties: {
    scores: { type: 'array', items: { type: 'object', properties: {
      key: { type: 'string' }, fidelity: { type: 'number' }, feasibility: { type: 'number' }, live_risk: { type: 'number', description: '10 = few unknowns' }, play: { type: 'number' }, total: { type: 'number' }, why: { type: 'string' } },
      required: ['key', 'fidelity', 'feasibility', 'live_risk', 'play', 'total', 'why'] } },
    winner: { type: 'string' },
    graft: { type: 'array', items: { type: 'string' }, description: 'the best ideas of the losers worth taking into the winner, each with the design key' },
    errors: { type: 'array', items: { type: 'string' }, description: 'factual errors found in any design, with the source that refutes them' },
  },
  required: ['scores', 'winner', 'graft', 'errors'],
}

phase('Judge')
const LENSES = ['the owner (fidelity to the concept as given, fun, the Heat mood, the elevator as a beat)', 'the engineer (buildable with kl_fa_author.py and stock objects only, every number sourced, nothing that kl_fa.check or kl_graft.verify would reject; open the code to check)', 'the tester (fewest LIVE unknowns between now and a playable round; which design fails most gracefully; are the live tests ordered right)']
const judged = (await parallel(LENSES.map((l, i) => () =>
  agent(`${PRE}\n${OWNER}\nYou are judge ${i + 1} of 3, reading as ${l}. Score each design 1-10 on fidelity, feasibility,
live_risk (10 = few unknowns), play; total = sum. Check facts against the repo (open re/retomoto.md, re/retomoto_fa.md,
tools/kl_fa_author.py where a claim matters); list every factual error with the refuting source. Name the winner and
the ideas of the other designs worth grafting into it.
${designs.map(d => `##### DESIGN ${d.key}: ${d.title} (${d.angle})\n${d.design}\nCHANGES:\n${d.changes.map(c => `- ${c.file}: ${c.what} :: ${c.how} [risk: ${c.risk}]`).join('\n')}\nLIVE TESTS:\n${d.live_tests.join('\n')}\nOPEN:\n${d.open.join('\n')}`).join('\n\n')}`,
    { label: `judge:${i + 1}`, phase: 'Judge', schema: VERDICT })))).filter(Boolean)
const tally = {}
for (const j of judged) for (const s of j.scores) tally[s.key] = (tally[s.key] || 0) + s.total
const ranked = Object.entries(tally).sort((a, b) => b[1] - a[1])
log(`Judge: ${judged.length}/3 judges; totals ${ranked.map(([k, v]) => `${k}=${v}`).join(', ')}`)
const winner = designs.find(d => d.key === (ranked[0] || [designs[0].key])[0]) || designs[0]

const SYNTH = {
  type: 'object',
  properties: {
    doc_path: { type: 'string' },
    summary: { type: 'string' },
    impl_spec: { type: 'string', description: 'the ordered, concrete implementation spec for tools/kl_fa_author.py and tools/kl_audio.py: every constant, table entry, ROLE/KEEP/PLACE change, wire() list, with values and sources' },
    live_tests: { type: 'array', items: { type: 'string' } },
  },
  required: ['doc_path', 'summary', 'impl_spec', 'live_tests'],
}

phase('Synthesize')
const synth = await agent(`${PRE}\n${OWNER}\nYou write the final design document. WINNER: design '${winner.key}' (${winner.title}).
Take it whole, graft the judges' recommended ideas, and correct every factual error the judges found. Write it to
/home/user/kl-merge/re/retomoto_design.md (you MAY write that one file) in the house style of re/retomoto_fa.md:
a dated header naming the sources, the words read / ASSUMPTION / GUESS / LIVE defined, tables with coordinates,
file:line or doc-section citations, no prose padding. ${SECTIONS}
Its section 9 must be a complete implementation spec: an implementer with only that section and the code must be
able to make every change. Reference the existing constants and functions of tools/kl_fa_author.py by name (open the
file; verify each name exists). Also return the same spec in 'impl_spec'.
WINNER:\n${winner.design}\nCHANGES:\n${winner.changes.map(c => `- ${c.file}: ${c.what} :: ${c.how} [risk: ${c.risk}]`).join('\n')}\nLIVE TESTS:\n${winner.live_tests.join('\n')}\nOPEN:\n${winner.open.join('\n')}
JUDGES:\n${judged.map((j, i) => `judge ${i + 1}: winner ${j.winner}; graft: ${j.graft.join(' | ')}; errors: ${j.errors.join(' | ')}; scores: ${j.scores.map(s => `${s.key} ${s.total} (${s.why})`).join(' ; ')}`).join('\n')}
OTHER DESIGNS (for the grafts):\n${designs.filter(d => d.key !== winner.key).map(d => `##### ${d.key}: ${d.title}\n${d.design}`).join('\n\n')}
READERS' KNOWLEDGE (for the numbers):\n${KB}`,
  { label: 'synthesize:design-doc', phase: 'Synthesize', schema: SYNTH })
if (!synth) throw new Error('synthesis returned nothing')
log(`Synthesize: ${synth.doc_path} - ${synth.summary.slice(0, 200)}`)

const IMPL = {
  type: 'object',
  properties: {
    files: { type: 'array', items: { type: 'string' } },
    done: { type: 'array', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' }, description: 'spec items you did not implement, each with why' },
    traced: { type: 'array', items: { type: 'string' }, description: 'every function / field index you used and where its definition is (file:line)' },
    guesses: { type: 'array', items: { type: 'string' } },
  },
  required: ['files', 'done', 'not_done', 'traced', 'guesses'],
}

phase('Implement')
let impl = await agent(`${PRE}\n${OWNER}\nYou are the implementer. You MAY edit /home/user/kl-merge/tools/kl_fa_author.py and /home/user/kl-merge/tools/kl_audio.py
(and tools/kl_graft.py / tools/kl_maps.py ONLY if the spec requires a hook there - prefer not). Nothing can be run
here: 'python -m py_compile' and 'python -c "import ast; ..."' for syntax only is the whole of what you can execute.
Implement the spec below exactly, in the style of the existing code (its comment density, its GUESS / ASSUMPTION
marks, its docstring tables). Rules of the file (read its docstring): no new entity, no new controller; stock objects
re-placed and re-wired; place() preconditions; wire() edits values and reference lists only and runs after both
parts are in the scene; everything the spec marks GUESS stays marked GUESS in a comment. Keep the existing behaviour
reachable: new features default ON only where the spec says so, with a module-level switch where the spec says so.
Before using any function, field index, enum value or object name, open its definition or the doc that proves it
and list it in 'traced'. Do not touch unrelated code. Finish with py_compile on every file you changed and
'git diff --stat'. Update the module docstring and the spec doc re/retomoto_design.md section 9 if a name differs
from what you implemented.
SPEC:\n${synth.impl_spec}`,
  { label: 'implement:kl_fa_author', phase: 'Implement', schema: IMPL })
if (!impl) throw new Error('implementer returned nothing')
log(`Implement: ${impl.files.join(', ')}; done ${impl.done.length}, not done ${impl.not_done.length}, guesses ${impl.guesses.length}`)

const REVIEW = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'object', properties: {
      severity: { type: 'string', description: 'blocker (build or verify would fail, or the game would crash) | major (feature would not work) | minor' },
      file: { type: 'string' }, line: { type: 'number' }, claim: { type: 'string' }, evidence: { type: 'string' }, fix: { type: 'string' } },
      required: ['severity', 'file', 'line', 'claim', 'evidence', 'fix'] } },
    ok: { type: 'array', items: { type: 'string' }, description: 'what you checked and found right' },
  },
  required: ['findings', 'ok'],
}
const RLENS = [
  { key: 'api', text: 'API CORRECTNESS: every function called, every field index (setv(sc, us, i, v), kl_fa.node_values(...)[n], ZGEOM[n], ZBoxPrimitive[n], controller field numbers), every enum string and every object name must match its definition in tools/*.py, re/kl2.json or a stock-level fact in re/*.md. Trace each one to its definition; a wrong index is a blocker. Check place() preconditions (top-level node or parents identity at origin; rigid moves of subtrees), node_of() uniqueness, ctrl_of() names, and that wire() only touches values / reference lists.' },
  { key: 'geometry', text: 'GEOMETRY: every new position must be on a floor a player or AI can stand on (compare with room bounds, floor heights, campaign actor positions and the static objects in re/retomoto.md), every box must lie inside the room it is meant for, facings must point the right way (facing = local +Z, the assumption of the file), vans and police must be on the road (x -5700..-300) and not inside the static cars, nothing may be placed below y of its floor or inside the tower shell. Flag any number that lacks a source or a GUESS mark.' },
  { key: 'build', text: 'BUILD AND ROUND: would kl_maps.chain + kl_graft.verify + kl_fa.check still pass (read kl_graft.verify and kl_fa.check: name resolution of every reference list, prune order vs wire(), KEEP patterns matched by Select.match, subtrees that must exist in F07 for node_of to succeed, reference lists that name nodes of the second map before it is joined, controllers that must stay on their class, the two KNOWN problems), and would the round still run (nothing removed that the live bank round used; settings untouched; exactly one escape monitor; spawn point counts; AIMonitor list 2 still reaching the blast timer). Also run python -m py_compile on the changed files and python -c to import-check nothing (imports need game paths? check kl_port_check.workdir() at import time).' },
]
phase('Review')
let rounds = 0, survivors = []
while (rounds < 2) {
  const rev = (await parallel(RLENS.map(l => () =>
    agent(`${PRE}\nYou are an adversarial code reviewer. LENS: ${l.text}
Review the working-tree diff of this repo (run: git -C /home/user/kl-merge diff; read the full changed files too) made
by the implementer per re/retomoto_design.md section 9. Nothing can be run except syntax checks. Default to reporting
only what you can PROVE with a file:line; do not pad. Implementer's own trace list:\n${impl.traced.join('\n')}\nImplementer's guesses:\n${impl.guesses.join('\n')}`,
      { label: `review:${l.key}:r${rounds + 1}`, phase: 'Review', schema: REVIEW })))).filter(Boolean)
  survivors = rev.flatMap(r => r.findings).filter(f => f.severity === 'blocker' || f.severity === 'major')
  const minors = rev.flatMap(r => r.findings).filter(f => f.severity === 'minor')
  log(`Review round ${rounds + 1}: ${survivors.length} blocker/major, ${minors.length} minor`)
  rounds++
  if (!survivors.length) { survivors = minors; break }
  const fixed = await agent(`${PRE}\nYou are the fixer. Apply these review findings to the working tree of /home/user/kl-merge (tools/kl_fa_author.py,
tools/kl_audio.py, re/retomoto_design.md section 9 if a number or name changes). Verify each finding against the
code and the docs before changing anything; if a finding is wrong, say so in not_done with the refuting file:line and
leave the code. Keep the style. py_compile every changed file.
FINDINGS:\n${survivors.map(f => `- [${f.severity}] ${f.file}:${f.line} ${f.claim}\n  evidence: ${f.evidence}\n  fix: ${f.fix}`).join('\n')}
MINOR (apply when cheap and clearly right):\n${minors.map(f => `- ${f.file}:${f.line} ${f.claim} -> ${f.fix}`).join('\n')}`,
    { label: `fix:r${rounds}`, phase: 'Review', schema: IMPL })
  if (fixed) impl = { ...impl, traced: [...impl.traced, ...fixed.traced], guesses: [...impl.guesses, ...fixed.guesses], done: [...impl.done, ...fixed.done], not_done: [...impl.not_done, ...fixed.not_done] }
}

const CRIT = {
  type: 'object',
  properties: {
    covered: { type: 'array', items: { type: 'string' } },
    missing: { type: 'array', items: { type: 'string' } },
    doc_code_mismatch: { type: 'array', items: { type: 'string' } },
    verdict: { type: 'string' },
  },
  required: ['covered', 'missing', 'doc_code_mismatch', 'verdict'],
}
phase('Critique')
const crit = await agent(`${PRE}\n${OWNER}\nCompleteness critic. Read re/retomoto_design.md and the working-tree diff (git -C /home/user/kl-merge diff).
Against the owner's four bullets and 'its level music plays': what is covered, what is missing, where the doc and the
code disagree (a number, a name, a switch default), and what the PC session must do first. Do not edit anything.`,
  { label: 'critique:completeness', phase: 'Critique', schema: CRIT })

return {
  readers: known.map(k => ({ key: k.key, facts: k.facts.length, unknowns: k.unknowns })),
  designs: designs.map(d => ({ key: d.key, title: d.title })),
  tally: ranked, winner: winner.key,
  judge_errors: judged.flatMap(j => j.errors),
  synth: { doc: synth.doc_path, summary: synth.summary, live_tests: synth.live_tests },
  impl: { files: impl.files, done: impl.done, not_done: impl.not_done, guesses: impl.guesses },
  review_rounds: rounds, open_findings: survivors,
  critique: crit,
}