#!/usr/bin/env python3
"""
kl_grenadefx_1110.py - extract the two grenade cues klhook/klgrenadefx.c plays ([Grenade] PinSound) from Dead Men's M01_FA_A bank.

    python kl_grenadefx_1110.py <outdir> [--pin REGEX] [--throw REGEX]

Writes <outdir>/grenade_pin.wav and <outdir>/grenade_throw.wav (16-bit mono PCM, peak -3 dBFS, the bank's own rate), plus INDEX.json.
Copy <outdir> to <Dog Days>\\KLGrenade\\ (next to KLHook.ini; the owner does that, this tool never writes into a game folder).
Read-only on the Dead Men folder. Decoder: kl_dmgunsnd.py (MS IMA ADPCM, luvsic's adpcm.h logic).

WHICH CLIPS (measured: tools/kl_whd.py name table of M01FAA_Main.WHD, grenade-ish names):
  throw  SFX/Weapons/Grenades/Fragmentation/Shot_Fragmentation/Shot_Fragmentation_01.wav   (the frag grenade's own 'shot' = the throw). REAL.
  pin    SFX/Weapons/_Common/Reloads/HK69/HK69_ClipIn_01.wav   GUESS: Dead Men has no clip named for a pin; a short metallic click of the
         grenade launcher's breech is the nearest. Alternatives to try with --pin: 'Grenade_Can_Ignite_01' (a hiss), 'Usp_ClipIn_01'.
"""
import json, math, os, re, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_dmgunsnd as D

PIN_RX = r'HK69_ClipIn_01\.wav$'
THROW_RX = r'Shot_Fragmentation_01\.wav$'
PEAK = 10 ** (-3 / 20)


def pick(rx):
    rx = re.compile(rx, re.I)
    for bank, f in D.banks():
        if bank != D.PREFERRED: continue
        for nm, o, w in D.records(f):
            if rx.search(nm) and (w[2] & 0xffff) == 0x11 and not (w[2] & 0x00800000):
                return bank, f, nm, w
    raise SystemExit('no in-memory IMA clip matches %r in %s' % (rx.pattern, D.PREFERRED))


def write(path, bank, f, nm, w):
    pcm = D.decode(w, D.read_clip(f, w)).astype(np.float64)
    if w[7] != 1: pcm = pcm.reshape(-1, w[7]).mean(axis=1)
    pk = float(np.abs(pcm).max()) or 1.0
    pcm = np.clip(pcm * (PEAK * 32767 / pk), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(w[3]); wf.writeframes(pcm.tobytes())
    return dict(file=os.path.basename(path), record=nm, bank=bank, rate=w[3], samples=int(len(pcm)), seconds=round(len(pcm) / w[3], 3))


def main(argv):
    if not argv or argv[0].startswith('-'): raise SystemExit(__doc__)
    out = argv[0]; pin, thr = PIN_RX, THROW_RX
    for i, a in enumerate(argv):
        if a == '--pin': pin = argv[i + 1]
        if a == '--throw': thr = argv[i + 1]
    os.makedirs(out, exist_ok=True); idx = []
    for name, rx in (('grenade_pin.wav', pin), ('grenade_throw.wav', thr)):
        idx.append(write(os.path.join(out, name), *pick(rx)))
        print(idx[-1])
    json.dump(idx, open(os.path.join(out, 'INDEX.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
