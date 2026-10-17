#!/usr/bin/env python3
"""
kl_dmgunsnd.py - find and decode Kane & Lynch: Dead Men gun sounds (M4 by default) from the level banks.

Dead Men level bank = Scenes/Locations/<L>/<L>_Main.WHD (+ .WAV beside the zip). Gun shots are NOT streamed
(fmt flag 0x00800000 clear): their ADPCM data sits in the level's .WAV at the record's offset.
Record (Dead Men, dwords; re/audio.md / tools/kl_whd.py): w0=0, w1=name offset, w2=fmt tag (low word),
w3=rate, w4=bits, w5=decoded pcm bytes, w6=data bytes, w7=channels, w8=data offset in the .WAV,
w9=samples (per channel), w10=block align, w11=samples per block.
M4 clips are fmt 0x11 = Microsoft IMA ADPCM, 4 bit, mono, 32000 Hz, block align 1024, 2041 samples/block.

    python kl_dmgunsnd.py scan  [regex]            list matching records and the banks holding them
    python kl_dmgunsnd.py decode <outdir> [regex]  decode one copy per clip to 16-bit PCM .wav + INDEX.json
                                                   (default regex: the six M4 shot records)
Read-only on the game folder. IMA decoder: credit luvsic, a-newer-perspective (loader/adpcm.h, whdconv.py
record finder), via tools/kl_gunsnd.py.
"""
import glob, hashlib, json, math, os, re, struct, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_gunsnd import ima_decode  # luvsic's adpcm.h logic

DM = r'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/Scenes/Locations'
M4_RX = r'^SFX/Weapons/(Assault_Rifle_M4/Shot/Shot_M4_|_Common/DistantShot/M4/Distant_Shot_M4_)\d+\.wav$'
PREFERRED = 'M01_FA_A'
FMTS = (0x1, 0x2, 0x11, 0x55, 0x1000)


def find_records(d):
    """record offsets of a Dead Men/Dog Days .WHD (luvsic whdconv.find_records, same rule)"""
    h0, hsz = struct.unpack_from('<II', d, 0)
    if h0 == 0: h0 = hsz
    out = []
    for o in range(16, h0 - 63 + 16, 16):
        w = struct.unpack_from('<9I', d, o)
        if w[0] != 0 or not (16 <= w[1] < o): continue
        if (w[2] & 0xffff) not in FMTS or not (4000 <= w[3] <= 96000) or w[7] not in (1, 2, 4, 6): continue
        e = d.find(b'\0', w[1], o)
        if e < 0 or not d[w[1]:e].lower().endswith(b'.wav'): continue
        out.append(o)
    return out


def banks():
    for f in sorted(glob.glob(DM + '/*/*.WHD')):
        b = os.path.basename(f)
        if '_LS' in b or b.startswith('Loader'): continue
        yield os.path.basename(os.path.dirname(f)), f


def records(f):
    d = open(f, 'rb').read()
    for o in find_records(d):
        w = struct.unpack_from('<14I', d, o)
        yield d[w[1]:d.index(b'\0', w[1])].decode('latin1'), o, w


def read_clip(whd, w):
    wav = open(whd[:-3] + 'WAV', 'rb')
    wav.seek(w[8]); return wav.read(w[6])


def decode(w, data):
    assert (w[2] & 0xffff) == 0x11 and not (w[2] & 0x00800000), 'not an in-memory IMA clip'
    return ima_decode(data, w[7], w[10], w[11], w[9])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'scan'
    if cmd == 'scan':
        rx = re.compile(sys.argv[2] if len(sys.argv) > 2 else M4_RX, re.I); held = {}
        for bank, f in banks():
            for nm, o, w in records(f):
                if rx.search(nm): held.setdefault(nm, []).append(bank)
        for nm in sorted(held): print(nm, len(held[nm]), 'banks')
    elif cmd == 'decode':
        out = sys.argv[2]; rx = re.compile(sys.argv[3] if len(sys.argv) > 3 else M4_RX, re.I)
        os.makedirs(out, exist_ok=True); idx = []; hashes = {}
        for bank, f in banks():
            for nm, o, w in records(f):
                if not rx.search(nm): continue
                data = read_clip(f, w)
                hashes.setdefault(nm, {}).setdefault(hashlib.sha1(data + struct.pack('<6I', *(w[2:8]))+struct.pack('<3I', *w[9:12])).hexdigest(), []).append(bank)
                if bank != PREFERRED: continue
                pcm = decode(w, data)
                fn = re.sub(r'[^A-Za-z0-9_.-]', '_', nm.split('/')[-1])
                with wave.open(os.path.join(out, fn), 'wb') as wf:
                    wf.setnchannels(w[7]); wf.setsampwidth(2); wf.setframerate(w[3]); wf.writeframes(pcm.astype('<i2').tobytes())
                x = pcm.astype(np.float64) / 32768
                pk = float(np.abs(x).max()); rms = float(np.sqrt((x ** 2).mean()))
                idx.append(dict(clip=fn, bank=bank, record=nm, rate=w[3], channels=w[7], samples=int(len(pcm)),
                                seconds=round(len(pcm) / w[3], 4), codec='MS IMA ADPCM 0x11, 4 bit, block %d, %d spb' % (w[10], w[11]),
                                peak_dbfs=round(20 * math.log10(max(pk, 1e-9)), 2), rms_dbfs=round(20 * math.log10(max(rms, 1e-9)), 2)))
        for e in idx: e['identical_in_banks'] = sum(len(v) for v in hashes[e['record']].values()) if len(hashes[e['record']]) == 1 else \
            {k[:8]: v for k, v in hashes[e['record']].items()}
        json.dump(idx, open(os.path.join(out, 'INDEX.json'), 'w'), indent=1)
        for e in idx: print(e)


if __name__ == '__main__':
    main()
