# A pass through luvsic's repository against our campaign maps

2026-10-11, kl-merge-48 (builder of The Vault and the club). Asked by the owner: "do a proper pass through and then copy
the files youd want / need into the repo". Source: `github.com/luvsicccc/a-newer-perspective` at `c053aa2` (2026-10-11),
local clone `G:\kl_scratch\luvsic\anp`. The files taken are in `third_party/anp/` (unchanged; its README says what and
why). OFFLINE reading; nothing of this ran in the game here.

Labels: MEASURED = I ran it on our files; READ = from his code or notes (file named); ASSUMED = says why.

## 0. Short answers

1. The campaign maps (The Vault, the club) were NOT built on his work. He converts a whole story level to run as the
   campaign; we take the map out of a level and put it under F07's systems. His converter is not a base for ours.
2. Four of his findings change something of ours TODAY (section 1). Two are hazards in what is built.
3. Six more are groundwork for things we have ruled out or worked around (section 2).
4. Not taken: his level converter, HUD / font / menu tools (kl-merge-12 holds the HUD), movie and setup tools.

## 1. What changes something now

### 1.1 Dog Days cannot play IMA ADPCM speech from the stream file - The Vault has 66 such lines

READ `loader/anp_loader.c` 351-406: "IMA-ADPCM (codec 3) entries, which Dog Days cannot read from a stream"; his loader
serves them as decoded PCM at virtual offsets (`adpcm.h` is the decoder), and 1,483 of Dead Men's 1,928 such entries
begin with a 4 KB 'LIP ' block that must not be decoded as audio.
MEASURED (kl_whd on the built banks): The Vault as the owner has it (`c_bank2_fx/bank_vault`) holds **66** streamed
single IMA ADPCM records (Advance_0x0_SWAT, Retreat_010_SWAT ... = the kept campaign guards' and police lines); the
tab's Withdrawal and Retomoto hold **0** - their voice lines were made in-memory records by the voice repairs
(`kl_snd.merge(inmem=...)`, `kl_voice.stream_clip`, re/voice.md 6.2), which is the form that plays.
So the Vault's 66 lines are silent or noise as built, and the nine guard lines added to the larger stream file for the
music build are of the same kind. Our own note had this as "never played in Dog Days: unknown"; his loader settles it.
TO DO (kl_fa_bank's build, after the waves fix): the Vault built with the voice repairs on, so that every streamed
ADPCM single becomes an in-memory record; mind the LIP block (does `kl_voice.stream_clip` skip it? - check).

### 1.2 Clip record +0x2C is a byte offset into the LEVEL'S OWN .SND - a crash class in any animation merge

READ `tools/clipsnd.py`: clip record dword 11 (+0x2C) names the clip's 'audio:animation/resources/<path>#seq' record by
its offset in that level's .SND (all 415 non-zero values in F03 and 417 in L01 are record starts there); kl2 reads it
when a player clip starts (ZPlayer vt+0x620 = 0x6b9d50 -> ... -> 0x5c8050). A clip carried into a level with another
bank points anywhere: his M12 crashed at kl2 0x5c8075 after long play (a type-2 record's mode word walked as a list).
OURS: `tools/kl_anm.py` 54 says of +0x2C "no reader found: NOT established"; `tools/kl_anmjoin.py` 68 gives an added
clip "the SOURCE file's value". So every Dead Men clip our tools merge into a Dog Days level (tools/kl_fa_climb.py's
climb clips; anything kl_anmjoin adds) carries a Dead Men .SND offset into a bank where that offset is something else.
Not seen as a crash here yet (the climb's own crash was the event id 5). Our grafted maps keep F07's .ANM and F07's
bank offsets (the merge appends), so the base clips are right; only ADDED clips are exposed.
TO DO (the holders of kl_anm / kl_anmjoin / kl_fa_climb): set +0x2C of an added clip by NAME in the target bank or to 0
(his rule 'name'); his `clipsnd.py <level zip>` is a ready check ("exit 1 if any clip names a non-record").

### 1.3 A collision ray that is checked against the game - and it disagrees with my sight flag

READ `scripts/hvk_ray.py`: a model of Dog Days' player ray 0x7daa80 on a level's .HVK; a sub-part is hit when
(flags & mask & 0xff) != 0, with **0x20 = solid for rays** and 0x08 = hero-only walls; five rays of a live press come
out within 0.2 cm of the game's. It reads OUR kl_hvk / kl_scene modules.
OURS: the waves build of The Vault tests "a wave man enters the world out of sight" with a ray test that ASSUMES
collision flag bit **0x10** blocks sight (taken from shape names). His measured rule says 0x20 for a ray.
TO DO (kl_fa_bank's wave_plan, kl_route): run the sight tests with his mask rule (0x20, and 0x28 to include hero-only
walls) and compare; where they differ, his is the measured one.

### 1.4 The shader permutations M03 and M05 ask for and do not get - with a way to give them

READ `fxc/miss_M03.txt` (60 lines) and `miss_M05.txt` (77): collected from his loader's log in the running game, e.g.
`Glow30.fx : MESH_RIGID`, `Cloth30.fx : MESH_WEIGHTED BLENDENABLED SPECULARENABLED`, `Glass.fx : MESH_STANDARD
BLENDENABLED BUMPENABLED REFRACTION2DENABLED SCROLLENABLED ALPHAFADEENABLED`. `tools/fxcalias.py` adds an ALIAS entry to
the level's cache for each missing key: the nearest Dog Days permutation of the same effect and mesh type (blend must
match), scored by missing / extra defines.
OURS: `kl_light.missing_shaders` reports them and `fit_shaders` changes the MATERIAL to a permutation the cache has;
what has none is not drawn (CLAUDE.md: the bomb on Retomoto's window, `glow30.fx MESH_RIGID`; the club's three lamp
materials; re/club_campaign.md). His way keeps the material and adds the cache entry.
TO DO: compare his two lists with what our Vault and club builds report missing; try the alias for the ones we leave
undrawn (the club's lamps first). NOT RUN here: whether an alias entry made this way draws in our grafted levels.

## 2. Groundwork for later

| What we ruled out or worked around | What he has (READ) | State on his side |
|---|---|---|
| .ANM: we keep the systems level's file and add a few clips with our own join | `docs/ANM_FORMAT.md` = the whole format with exe evidence (the two games differ only in the clip record, 0x50 / 0x68); `anm_lib.py`, `anm_merge.py` (a Dead Men database merged into a Dog Days one path by path), `anm_codec.py` (the key decoder), `verify_merge.py` | all 16 story levels convert; sound broke after his first merge (HANDOFF 137) and 1.2 above is the cause he found |
| The campaign's mini cut scenes are stripped from every squad (the vault breaker; the club) | `scriptconv.py`: Dead Men mini-cutscene script strings rewritten for Dog Days | used in his converted levels |
| The prison's whole campaign route: three mesh pieces joined by climbs | `climbs.py` + `loader/climb.inc`: a climb as a use prompt + a grafted Dog Days mini cut scene that plays Dead Men's climb clips; `scripts/climb_spots.py` | HANDOFF 125: the prompt at the first van did not show yet |
| Dead Men sound banks: we merge into the Dog Days bank | `sndconv.py`, `whdconv.py`: a Dead Men bank converted in place (10 language slots; the record's field order) | agrees with re/audio.md 3 field for field (READ both) |
| The pathfinder: 'most pairings ASSUMED' in kl_pf4 | `pfconv.py`: the same widening from PF4::ZData::Load of both exes (kl1 0x4ee810, kl2 0x63e750); A4, A5, A7 are '?' for him too | a second, independent derivation to compare record by record |
| Crew orders (follow / fire at / defend) | `loader/squad.inc`: through kl2's own ZSquadControl | his hook; for the session that holds klhook |

`tools/gunfit.py` (gun fitting) and `tools/graft.py` (his subtree graft) are in the folder for reading by whoever holds
kl_map_guns / kl_graft; I did not compare them.

## 3. What I did not find

Nothing in his repository on: the cloth blob that crashed The Vault (no 'cloth' in his code or notes beyond shader
names), cover lists, MatPosAnim doors (ours play from KEYS chunks in the .buf, not from the .ANM), waves or spawning,
Fragile Alliance layers. Those stay ours.

## 4. For luvsic (the owner can pass these on; tools and notes only, never game files)

- The cloth blob: a Dead Men cloth record is 8 bytes shorter than Dog Days' layout addresses; a plant pot's cloth then
  writes over the head of the next .prm chunk (re/crash_vault.md, tools/kl_fa_vaultfx.py). His converted M03 has the
  same pots.
- The point-blank rule (re/melee_damage.md): a firing soldier within 1.6 m lands a hit worth 100 bullets.
- ZFakeTarget outside the vision grid writes 16 bytes of heap every frame (re/crash_686a66.md).
- The campaign pre-pass facts of re/campaign_fa.md (door clips that shut again, G1.8).
