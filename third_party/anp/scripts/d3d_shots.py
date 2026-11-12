"""While kl2.exe runs, ask ANP_Loader for a D3D back-buffer screenshot every <interval> s (ANP_shot.txt -> <name>.bmp in
the DD folder; works with the screen off, unlike desktop capture), then move them to <outdir> as JPGs.
usage: d3d_shots.py <outdir> [interval=0.6] [max_seconds=600]"""
import os, sys, time, subprocess, glob
DD = r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
iv = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
mx = float(sys.argv[3]) if len(sys.argv) > 3 else 600
FF = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe'))[0]
def running():
    return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout.lower()
t0 = time.time()
while not running() and time.time() - t0 < 120: time.sleep(1)
n = 0
while running() and time.time() - t0 < mx:
    sq = os.path.join(DD, 'ANP_shot.txt')
    if not os.path.exists(sq):
        open(sq, 'w').write('anpd3d_%05d_%06.1f.bmp' % (n, time.time() - t0)); n += 1
    time.sleep(iv)
    for b in glob.glob(os.path.join(DD, 'anpd3d_*.bmp')):
        try:
            if time.time() - os.path.getmtime(b) < 0.5: continue
            j = os.path.join(OUT, os.path.basename(b)[:-4] + '.jpg')
            subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', b, '-vf', 'scale=640:-2', '-q:v', '5', j], capture_output=True, timeout=20)
            os.remove(b)
        except OSError: pass
time.sleep(2)
for b in glob.glob(os.path.join(DD, 'anpd3d_*.bmp')):
    j = os.path.join(OUT, os.path.basename(b)[:-4] + '.jpg')
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', b, '-vf', 'scale=640:-2', '-q:v', '5', j], capture_output=True, timeout=20)
    try: os.remove(b)
    except OSError: pass
if os.path.exists(os.path.join(DD, 'ANP_shot.txt')): os.remove(os.path.join(DD, 'ANP_shot.txt'))
print('shots requested %d, saved %d -> %s' % (n, len(glob.glob(os.path.join(OUT, '*.jpg'))), OUT))
