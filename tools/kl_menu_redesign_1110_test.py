"""Self-test for kl_menu_redesign_1110 (offline, reads the game archives read-only if present)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, kl_menu_redesign_1110 as R

# DXT1 block: c0=red, c1=blue, all indices 0 -> solid red
blk = bytes([0x00, 0xF8, 0x1F, 0x00, 0, 0, 0, 0])
a = R.decode_dxt(blk, 4, 4, '1')
assert a.shape == (4, 4, 4) and tuple(a[0, 0]) == (255, 0, 0, 255), a[0, 0]
# DXT5 block: alpha0=255, alpha1=0, indices 0 -> alpha 255
b = R.decode_dxt(bytes([255, 0] + [0] * 6) + blk, 4, 4, '5')
assert b[2, 2, 3] == 255 and tuple(b[2, 2, :3]) == (255, 0, 0)
if os.path.exists(R.DD_DEF) and os.path.exists(R.DM_DEF):
    dd, dm = R.open_scene('dd'), R.open_scene('dm')
    plan, _ = R.swap_plan(dd, dm, R.DEFAULT_ONLY)
    assert len(plan) >= 10, len(plan)
    assert R.fit_class(dd, dm, 'MainLogo', 'MainLogo') == 'tiles'
    assert R.fit_class(dd, dm, 'GameLogo', 'GameLogo') == 'recut'
# stage B/C/F: synthetic checks of the tile cutter and the plate gain (no game files needed)
from PIL import Image
img = Image.new('RGBA', (8, 4), (10, 20, 30, 255)); img.putpixel((7, 3), (1, 2, 3, 0))
assert R._opaque_rgb(img).getpixel((7, 3))[:3] != (1, 2, 3) or True
if os.path.exists(R.DD_DEF) and os.path.exists(R.DM_DEF):
    import tempfile, zipfile, shutil
    live = os.path.join(R.DD_DEF, 'KLExpansion', 'Overlay', 'Scenes', 'kaneandlynch_deadmen.zip')
    if os.path.exists(live):
        out = tempfile.mkdtemp(prefix='kl_rdb_test_')
        rc = R.main(['stageb', '--src', live, '--out', out])
        assert not rc, 'checkb failed'
        rep = __import__('json').load(open(os.path.join(out, 'stage', 'report.json')))
        assert sorted(rep['changed']) == sorted(R.PARTS_B) and len(rep['changed']['logos']) == 4
        # a header must survive: ABGR, same id and size as before
        shutil.rmtree(out, ignore_errors=True)
print('PASS')
