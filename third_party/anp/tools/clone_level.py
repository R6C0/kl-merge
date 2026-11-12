# clone a DD level folder under a new scene id (raw zip entry rename, no recompression)
import sys, os, shutil
sys.path.insert(0, os.path.dirname(__file__))
from zipraw import read_zip, write_zip
from anp_paths import game_dir, DD_FOLDER
src_id, dst_id = sys.argv[1], sys.argv[2]
root = os.path.join(game_dir('ANP_DD_GAME', DD_FOLDER), 'Scenes', 'Locations')
sd, dd = os.path.join(root, src_id), os.path.join(root, dst_id)
os.makedirs(dd, exist_ok=True)
for fn in sorted(os.listdir(sd)):
    s = os.path.join(sd, fn); t = os.path.join(dd, fn.replace(src_id + '_', dst_id + '_'))
    if fn == src_id + '_Main.zip':
        ents = read_zip(s)
        for e in ents:
            e.name = e.name.replace('Locations/%s/%s_' % (src_id, src_id), 'Locations/%s/%s_' % (dst_id, dst_id))
        write_zip(t, ents)
    else:
        shutil.copyfile(s, t)
    print('wrote', t, os.path.getsize(t))
