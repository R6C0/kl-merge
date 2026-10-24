"""Offline check of klcamsmooth.c's stance stage (StanceMs). Mirrors the C maths (kcs_cd, pivot follower, stance takeover).
Feeds a synthetic crouch -> stand/run step (pivot offset from the feet jumps in ONE frame, eye follows the pivot 1:1, as the owner's
KLHook.log suggests: 160 -> 145 / 130 / 110 cm) with uneven frame times, and prints the largest per-frame step of the displayed
eye height relative to the feet. Usage: python tools/sim_camsmooth.py [stepcm] [stancems] [pivotms]"""
import math, random, sys

def cd(x, v, w, dt):
    a = v + w * x; ex = math.exp(-w * dt)
    return (x + a * dt) * ex, (v - a * w * dt) * ex

def run(fps, step, stancems=280.0, pivotms=60.0, stancecm=6.0, jitter=True, seed=1):
    random.seed(seed)
    t = 0.0; T = 2.0; qs = qsv = 0.0; q_prev = None; qpv = 0.0
    S = Sv = 0.0; sact = False; O = None; Ov = 0.0; Iprev = None; Iv = 0.0
    out = []; raw = []; follow = []
    while t < T:
        dt = 1.0 / fps * (random.uniform(0.6, 1.5) if jitter else 1.0)
        t += dt
        q = 160.0 if t < 0.5 else 160.0 - step            # crouch -> pivot offset drops 'step' cm in ONE frame at t = 0.5 s
        eye_rel = q + 10.0                                 # eye follows the pivot 1:1 (feet-relative), + fixed offset
        if q_prev is None: qs = q; q_prev = q
        pop = abs(q - (q_prev + qpv * dt)) > stancecm and stancems >= 20
        if pop: qs, qsv, qpv = q, 0.0, 0.0
        else: qpv += ((q - q_prev) / dt - qpv) * 0.5
        q_prev = q
        if pivotms > 0:                                    # pivot follower: shifts the displayed eye by (qs - q)
            x = qs - q; x, qsv = cd(x, qsv if not pop else 0.0, 6.0 / (pivotms * 1e-3), dt); qs = q + x
        else: qs = q
        I = eye_rel + (qs - q)
        if stancems >= 20:
            if pop and O is not None:
                S = O + Ov * dt - I; Sv = Ov - Iv; sact = True
            elif Iprev is not None and not pop: Iv = (I - Iprev) / dt
            if sact:
                S, Sv = cd(S, Sv, 6.0 / (stancems * 1e-3), dt)
                if abs(S) < 0.05 and abs(Sv) < 1.0: S = Sv = 0.0; sact = False
            Oc = I + (S if sact else 0.0)
            if O is not None: Ov = (Oc - O) / dt
            O = Oc; Iprev = I
        else: Oc = I
        out.append((t, dt, Oc)); raw.append(eye_rel); follow.append(I)
    def mx(vals): return max(abs(b - a) for a, b in zip(vals, vals[1:]))
    return mx([o[2] for o in out]), mx(raw), mx(follow)

if __name__ == "__main__":
    step = float(sys.argv[1]) if len(sys.argv) > 1 else 50.0
    sm = float(sys.argv[2]) if len(sys.argv) > 2 else 280.0
    pm = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    print("crouch -> stand pivot pop of %.0f cm in one frame; max per-frame step of the shown eye height (cm)" % step)
    print("%5s | %9s | %16s | %22s" % ("fps", "raw(stock)", "PivotMs=%d only" % pm, "with StanceMs=%d" % sm))
    for fps in (240, 144, 60):
        a, r, _ = run(fps, step, sm, pm)
        _, _, f = run(fps, step, 0.0, pm)
        print("%5d | %9.1f | %16.1f | %22.2f" % (fps, r, f, a))
    for st in (15, 30, 55):
        print("step %2d cm @240: shown max %.2f cm/frame (raw %.0f)" % (st, run(240, st, sm, pm)[0], st))
    print("no-pop control (smooth running, no step): max frame step %.3f cm (must be ~0, no lag)" % run(240, 0.0, sm, pm)[0])
