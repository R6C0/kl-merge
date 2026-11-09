"""Off-game test for the one-sided door guard of kl_doors_1108 (2026-11-09: DM03 hosts 546 / 1255 opened onto nothing)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_doors_1108 as D

assert D.one_sided([(176, 648, 7480, 2), (64, 506, 7745, 2)]) == []
assert D.one_sided([(176, 648, 7480, 2), (546, 4005, 6527, 1), (1255, 3684, 7981, 1), (9, 1, 1, 0)]) == [546, 1255, 9]
assert 546 not in D.MAPS['DM03']['hosts'] and 1255 not in D.MAPS['DM03']['hosts']
print('kl_doors_1108_test PASS')
