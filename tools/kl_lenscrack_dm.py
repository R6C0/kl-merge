"""
Dead Men glass-crack atlas + offline preview for reshade/KL_LensCrackDM.fx (2026-11-06).

  python tools/kl_lenscrack_dm.py atlas   <out_dir>          # reads the DM/DD bullet-hole glass decals, writes KL_LensCrackDM.png
  python tools/kl_lenscrack_dm.py preview <out_dir> <shot>   # numpy port of the shader over a screenshot -> preview_*.png

The decals are FX_Bullet_Hole_Glass_03 / _04 (Dead Men Effects/BulletHoles, DXT5, 256x256: white fracture star on black, alpha 255).
They are read straight from the game's own archives; the output stays in the work folder (never committed).
The atlas is 2x2 cells of 256 px, each decal recentred on its bright core (GUESS: centroid of luminance > 0.85), luminance in R,G,B, alpha 255.
"""
import glob
import io
import os
import struct
import sys
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_texmat as T      # noqa: E402
import kl_texmip as M      # noqa: E402

DM = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men'
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
# (source game, archive, texture name, label)  -- cell order of the atlas
CELLS = [
    ('dm', DM + r'\Scenes\Locations\M01_A\M01A_Main.zip', 'Effects/BulletHoles/FX_Bullet_Hole_Glass_03', 'DM_Glass_03'),
    ('dm', DM + r'\Scenes\Locations\M01_A\M01A_Main.zip', 'Effects/BulletHoles/FX_Bullet_Hole_Glass_04', 'DM_Glass_04'),
    ('dd', DD + r'\Scenes\Locations\F01\F01_Main.zip', 'tex:Effects/BulletHoles/FX_Bullet_Hole_Glass_03#Diffuse_c', 'DD_Glass_03_c'),
    ('dd', DD + r'\Scenes\Locations\F01\F01_Main.zip', 'tex:Effects/BulletHoles/FX_Bullet_Hole_Glass_04#Diffuse_c', 'DD_Glass_04_c'),
]


def _dds(fc, w, h, blob):
    hdr = bytearray(b'DDS ' + struct.pack('<7I', 124, 0x81007, h, w, len(blob), 0, 1) + bytes(44) + struct.pack('<8I', 32, 4, 0, 0, 0, 0, 0, 0))
    hdr[84:88] = fc
    return bytes(hdr) + bytes(20) + blob


def load(zpath, name):
    zf = zipfile.ZipFile(zpath)
    for n in zf.namelist():
        if n.upper().endswith('.TEX'):
            t = T.read_tex(zf.read(n))
            for x in t.tex.values():
                if x.name == name:
                    d = M.parse(x.entry)
                    p, sz = d['blobs'][0]
                    return Image.open(io.BytesIO(_dds(d['fc'], d['w'], d['h'], x.entry[p + 4:p + 4 + sz]))).convert('RGBA')
    raise KeyError(name)


def recentre(lum):
    """Shift so the bright core sits on the cell centre; returns the array and the (dy, dx) shift."""
    ys, xs = np.nonzero(lum > 0.85)
    h, w = lum.shape
    dy, dx = int(round(h / 2 - ys.mean())), int(round(w / 2 - xs.mean()))
    out = np.zeros_like(lum)
    y0, y1 = max(0, dy), min(h, h + dy)
    x0, x1 = max(0, dx), min(w, w + dx)
    out[y0:y1, x0:x1] = lum[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    return out, (dy, dx)


def atlas(outdir):
    os.makedirs(outdir, exist_ok=True)
    A = np.zeros((512, 512), np.float32)
    for k, (_g, z, n, lab) in enumerate(CELLS):
        im = load(z, n)
        lum = np.asarray(im.convert('L'), np.float32) / 255.0
        lum, sh = recentre(lum)
        print(lab, 'shift', sh)
        A[(k // 2) * 256:(k // 2 + 1) * 256, (k % 2) * 256:(k % 2 + 1) * 256] = lum
    g = (np.clip(A, 0, 1) * 255 + 0.5).astype(np.uint8)
    rgba = np.dstack([g, g, g, np.full_like(g, 255)])
    Image.fromarray(rgba, 'RGBA').save(os.path.join(outdir, 'KL_LensCrackDM.png'))
    print('wrote', os.path.join(outdir, 'KL_LensCrackDM.png'))


# ---- numpy port of KL_LensCrackDM.fx (same constants; keep them in step) ----
def _hash(x, y):
    p = np.array([x, y, x]) * 0.1031
    p = p - np.floor(p)
    p = p + np.dot(p, np.array([p[1], p[2], p[0]]) + 33.33)
    v = (p[0] + p[1]) * p[2]
    return v - np.floor(v)


def _bilin(A, u, v):
    """A: HxW; u,v in pixels (texel centres at +0.5 already removed)."""
    h, w = A.shape
    u = np.clip(u, 0, w - 1.001)
    v = np.clip(v, 0, h - 1.001)
    u0, v0 = np.floor(u).astype(int), np.floor(v).astype(int)
    fu, fv = u - u0, v - v0
    return (A[v0, u0] * (1 - fu) * (1 - fv) + A[v0, u0 + 1] * fu * (1 - fv) + A[v0 + 1, u0] * (1 - fu) * fv + A[v0 + 1, u0 + 1] * fu * fv)


def preview(outdir, shot, cracks=None, name='preview', fx=(0.0, 0, 0, 0), la=2.4):
    """fx = KL_CrackFX (1 + newest age s or 0, Flash, Glint, Haze); la = the glint light angle (shader: timer * 0.00025 + 2.4)."""
    img = np.asarray(Image.open(shot).convert('RGB'), np.float32) / 255.0
    H, W, _ = img.shape
    asp = W / H
    A = np.asarray(Image.open(os.path.join(outdir, 'KL_LensCrackDM.png')).convert('L'), np.float32) / 255.0
    cracks = cracks or [(0.10, 0.16, 0.24, 1.0), (0.90, 0.70, 0.20, 1.0), (0.84, 0.10, 0.17, 1.0)]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    uvx, uvy = (xx + 0.5) / W, (yy + 0.5) / H
    offx = np.zeros((H, W), np.float32); offy = np.zeros_like(offx); shine = np.zeros_like(offx); dark = np.zeros_like(offx)
    glint = np.zeros_like(offx); haze = np.zeros_like(offx)
    age = fx[0] - 1.0
    pop = float(np.exp(-age * 18.0)) if fx[0] > 0.5 and fx[1] > 0.5 else 0.0
    jolt = float(np.exp(-age * 12.0)) * 1.5 if fx[0] > 0.5 and fx[1] > 0.5 else 0.0
    ld = (np.cos(la), np.sin(la)) if fx[2] > 0.5 else (0.0, 0.0)
    for ci, (cx, cy, reach, inten) in enumerate(cracks):
        cpop = pop if ci == len(cracks) - 1 else 0.0           # the newest crack is the last one
        px = (uvx - cx) * asp / reach
        py = (uvy - cy) / reach
        r = np.hypot(px, py)
        seed = _hash(cx * 91.7, cy * 91.7)
        cell = int(np.floor(_hash(seed * 13.1, 5.0) * 4.0)) % 4
        ang = _hash(seed * 7.7, 2.0) * 6.2831853
        flip = 1.0 if _hash(seed * 3.3, 9.0) > 0.5 else -1.0
        ca, sa = np.cos(ang), np.sin(ang)

        def mask(dx, dy):                       # dx, dy in units of the reach, screen axes
            qx, qy = px + dx, py + dy
            rx = (ca * qx + sa * qy) * flip
            ry = -sa * qx + ca * qy
            u, v = rx * 0.5 + 0.5, ry * 0.5 + 0.5
            e = np.maximum(np.abs(u - 0.5), np.abs(v - 0.5))
            em = 1.0 - np.clip((e - 0.42) / 0.08, 0, 1)
            cu, cv = (cell % 2) * 256 + np.clip(u, 0, 1) * 255, (cell // 2) * 256 + np.clip(v, 0, 1) * 255
            return _bilin(A, cu, cv) * em
        t = 1.5 * 2.0 / 256.0
        wd = 5.0 * 2.0 / 256.0
        m = mask(0, 0)
        gx = mask(t, 0) - mask(-t, 0)
        gy = mask(0, t) - mask(0, -t)
        hx1, hx2, hy1, hy2 = mask(wd, 0), mask(-wd, 0), mask(0, wd), mask(0, -wd)
        halo = 0.25 * (hx1 + hx2 + hy1 + hy2)
        wgx, wgy = hx1 - hx2, hy1 - hy2                         # as the shader (11-07: was +-2 wd here)
        w = inten * 1.0
        env = (1.0 - np.clip((r - 0.85) / 0.35, 0, 1)) * (r < 1.2)
        offx += (gx * 3.0 + wgx * 4.0) * w * env
        offy += (gy * 3.0 + wgy * 4.0) * w * env
        shine += (m * 0.85 + halo * 0.10) * w * env
        dark += np.clip(halo - m * 0.5, 0, 1) * 0.55 * w * env
        shine += m * cpop * 0.8 * env + (1.0 - np.clip(r / 0.9, 0, 1) ** 2 * (3 - 2 * np.clip(r / 0.9, 0, 1))) * cpop * 0.12
        gl = np.hypot(gx, gy)
        glint += np.clip(gl * 3.0, 0, 1) * np.clip((gx * ld[0] + gy * ld[1]) / (gl + 1e-4), 0, 1) ** 6 * w * env
        haze += np.clip(1.0 - r, 0, 1) ** 1.5 * w
    mx, my = (uvx - 0.5) * asp, uvy - 0.5
    keep = np.clip((np.hypot(mx, my) - 0.10) / 0.10, 0, 1)
    keep = keep * keep * (3 - 2 * keep)
    offx *= keep; offy *= keep; shine *= keep; dark *= keep; glint *= keep; haze *= keep * (1.0 if fx[3] > 0.5 else 0.0)
    offx += np.sin(age * 55.0) * jolt; offy += np.cos(age * 47.0) * jolt     # x CrackRefract in the shader (1 = default, as here)
    sx = np.clip(xx + offx, 0, W - 1.001); sy = np.clip(yy + offy, 0, H - 1.001)
    out = np.dstack([_bilin(img[:, :, c], sx, sy) for c in range(3)])
    lum = (out * np.array([0.299, 0.587, 0.114])).sum(2)
    hz = np.clip(haze, 0, 1)[:, :, None] * 0.16
    out = out * (1 - hz) + (lum * 0.85 + 0.10)[:, :, None] * hz
    out *= (1 - np.minimum(np.clip(dark, 0, 1), 0.6))[:, :, None]
    out += np.clip(shine, 0, 1)[:, :, None] * np.array([0.92, 0.95, 1.0]) * 0.7
    out += (np.clip(glint, 0, 1) * (0.15 + 0.6 * lum))[:, :, None] * np.array([1.0, 0.98, 0.94]) * 0.9
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(outdir, name + '.png'))
    print('wrote', os.path.join(outdir, name + '.png'))


if __name__ == '__main__':
    if sys.argv[1] == 'atlas':
        atlas(sys.argv[2])
    elif sys.argv[1] == 'preview':
        # preview <outdir> <shot> [age_s Flash Glint Haze [light_angle]]: e.g. 0.05 1 1 1 = 50 ms after a birth, everything on
        a = [float(v) for v in sys.argv[4:]]
        fx = (1.0 + a[0], a[1], a[2], a[3]) if len(a) >= 4 else (0.0, 0, 0, 0)
        preview(sys.argv[2], sys.argv[3], fx=fx, la=a[4] if len(a) >= 5 else 2.4, name='preview' if len(a) < 4 else 'preview_fx_%g' % a[0])
