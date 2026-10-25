"""Per-map loot decisions of tools/kl_loot_1025.py (2026-10-25). Numbers come from Floors.stand / nav-reach surveys of each map (see the report of the run).
Node numbers are kl_fa_bots node ids (1-based entity order). GUESS markers say where a number is a judgement, not a measurement."""
import collections

MAPS = collections.OrderedDict()

# DM09 (Retomoto): the 6 main-room briefcases (300k, model 70) sat in two rows (z -220 / -8) on the conference table; node 25490 (5000, -223) had NO home nav
# part under its trigger (census reach_home None: bots could not take it). New places (re-surveyed 2026-10-25 evening on a copy of the live zip, blast switched):
# every one passes kl_fa_loot.check's "on the table top" corner test (case footprint ~+-28, rim z -248..20 at the table ends), Floors.stand spare 54-90 (reach 165)
# and home-part nav spare >= 20 (20..25 - the nav mesh only reaches the table ends, so 20 is the best the table allows; the whole table centre has no home nav).
# GUESS: the minimum accepted nav spare is the owner's rule (>= 20), the exact cells are the surveyed ones (dm09_sel.py), not a hand layout.
# 15 statue stacks stay: each has a SamuraiSuit Whole/Remain node at distance 0 (checked by kl_fa_loot.check: 15 at cases). Total 4,050,000 -> 4,000,000 by one statue stack 150k -> 100k.
MAPS['DM09'] = dict(
    slot='F06', zip='F06_Main.zip', pin='24e9c878ebd574754529a4787374385b',
    moves={25488: (4680.0, 21070.0, -216.0),
           25489: (4680.0, 21070.0, -11.0),
           25490: (5110.0, 21070.0, -222.0),
           25491: (4930.0, 21070.0, -5.0),
           25492: (5320.0, 21070.0, -210.0),
           25493: (5180.0, 21070.0, -11.0)},
    amounts={25504: 100000})


# DM01B (Hot Coffee II): 6 cases lay loose on the street (y -15) and 6 on the back-lot floor; total 2,100,000.
# Moved onto table tops (y 75) and the counter (y 120) of the Diner (101a), and onto crate tops (y 160) / the pallet of the Warehouse (floor y 60).
# Surfaces read from the HVK (tops.py: floor-like samples at the xz) : tables 75, counter 120, crates 160, pallet 190 (samples 185/190, the higher taken).
# Every spot: Floors.stand spare 25-107 (reach 165) and home-part nav spare 35-85.
# 20742 first went on the pallet stack (y 190): Floors.stand found NO standing place within reach (spare None) - re-placed on a CrateX top (y 160, HVK sample 160, Floors spare 150, nav home 115, >= 200 from the other five).
# GUESS: the Floors flood starts in the diner / the warehouse (the spawn is 21000+ units away and the HVK flood from there does not connect), so 'stand'
#        is the proof that the spot is standable and the nav (home part) is the proof of reach from the spawn.
MAPS['DM01B'] = dict(
    slot='F03', zip='F03_Main.zip', pin='186cf3f81e16bd900c90230213336b7e',
    moves={20640: (5200.0, 75.0, 23070.0), 20641: (5465.0, 75.0, 23080.0), 20642: (5780.0, 75.0, 23030.0),
           20643: (5660.0, 75.0, 22560.0), 20654: (6340.0, 120.0, 22520.0), 20743: (6340.0, 120.0, 22760.0),
           20737: (2389.0, 160.0, 18878.0), 20738: (2712.0, 160.0, 18619.0), 20739: (2833.0, 160.0, 18631.0),
           20740: (2460.0, 160.0, 18376.0), 20741: (1984.0, 160.0, 18810.0), 20742: (1800.0, 160.0, 18725.0)},
    amounts={20640: 333333, 20641: 333333, 20642: 333333, 20643: 333333, 20654: 333335, 20743: 333335,
             20737: 333333, 20738: 333333, 20739: 333333, 20740: 333333, 20741: 333333, 20742: 333333})   # 10 x 333,333 + 2 x 333,335 = 4,000,000 (GUESS: even split)

# DM03A (Bank): the six desk sportsbags (20397..20401, 20412, y 899) already rest on the counter top: the HVK has a floor-like surface at y 900 under each
# (tops.py), so the "321 below" of the nav survey was the nav mesh, not a floating bag: NO MOVE. Total 2,900,000 -> 4,000,000 by value in the vault
# (hidden until the vault opens): 6 x 300k -> 400k and the 500k stack -> 1,000,000 (GUESS: the vault takes the whole +1.1M, the desk bags keep 100k).
MAPS['DM03A'] = dict(
    slot='F07', zip='F07_Main.zip', pin='a869705b8f65232a40ec97dac0ca4ab6',
    moves={},
    amounts={20495: 400000, 20496: 400000, 20497: 400000, 20498: 400000, 20499: 400000, 20500: 400000, 20501: 1000000})

# DM06B (Pagoda park): 19115 stood in the Scatter_Grass_Collapse cluster (70 from its origin, shards above): moved 244 from it onto clean floor y 180 with nav
# under it. The six pagoda cases in a straight row 70 apart (x 1240) alternate x 1180 / 1300 (same z, same y 624; Floors spare 132-154, nav 40/0).
# Total 3,150,000 -> 4,000,000 (GUESS split): pagoda 6 x 300k -> 375k (+450k), 19115 and 19204 150k -> 250k (+200k), 19098 and 19099 150k -> 250k (+200k).
MAPS['DM06B'] = dict(
    slot='F02', zip='F02_Main.zip', pin='02458756ed893496743b653fb34c3a96',
    moves={19115: (100.0, 184.0, -1900.0),
           19198: (1180.0, 624.0, 2200.0), 19199: (1300.0, 624.0, 2270.0), 19200: (1180.0, 624.0, 2340.0),
           19201: (1300.0, 624.0, 2410.0), 19202: (1180.0, 624.0, 2480.0), 19203: (1300.0, 624.0, 2550.0)},
    amounts={19198: 375000, 19199: 375000, 19200: 375000, 19201: 375000, 19202: 375000, 19203: 375000,
             19115: 250000, 19204: 250000, 19098: 250000, 19099: 250000})

# DM05A (Club / office block) - STAGE ONLY, needs a K50 memory run before install (no model or size change, .prm identical, but the map is memory-tight).
# 18903 / 18904 stood on the lounge glass table (Sofa_Lounge_TableA, y 377) inside its pre-placed Shard_60xx set (8 and 11 from the nearest shard): moved to the
# lounge floor (y 340, HVK floor-like sample there) beside 18905, > 150 from every shard, nav under them (home reach 0).
# 18806 stood 133 from the 'Flames_*' nodes: those are ZParticleTemplate definitions (no emitter named flame/fire within 500), so there may be no live fire
# (GUESS); it is moved anyway to the far end of its counter top (y 130 surface, x 228..300, z -1350..-1150) 227 from them, home nav reach 45.
# Values untouched (total 2,200,000: the task gave moves only).
MAPS['DM05A'] = dict(
    slot='F01', zip='F01_Main.zip', pin='9cdd6dee29f9a0a349589bf842b6e995',
    moves={18903: (3050.0, 340.0, 2490.0), 18904: (2950.0, 340.0, 2520.0), 18806: (290.0, 127.0, -1150.0)},
    amounts={})
