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


# ===================================================================================================================
# Replay of the owner's logged k36 failures (tools/sim_camsmooth_log.txt = excerpts of KLHook.log 2026-10-24)
# ===================================================================================================================
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "sim_camsmooth_log.txt")

def budget(dt): return max(0.8, 300.0 * dt)             # kcs_clamp in klcamsmooth.c

# ---- 1. stance detector: old = world vector q, new = (horizontal length, height)
def replay_stance():
    rows = []
    for ln in open(LOG):
        m = re.search(r"STANCE pop: pivot offset from the feet stepped ([\d.]+) cm .*q (\S+) (\S+) (\S+) <- (\S+) (\S+) (\S+)", ln)
        if m:
            v = [float(x) for x in m.groups()]
            q, p = v[1:4], v[4:7]
            new = math.hypot(math.hypot(q[0], q[2]) - math.hypot(p[0], p[2]), q[1] - p[1])
            rows.append((v[0], new, q, p))
    return rows

def rotation_test(fps=240, deg_per_s=900.0, off=30.0, limit=6.0):
    """player turns with a 30 cm horizontal pivot offset: false pops (old world vector, new length+height)"""
    dt = 1.0 / fps; ang = 0.0; prev = None; fo = fn = 0
    for _ in range(int(fps * 2)):
        ang += math.radians(deg_per_s) * dt
        q = (off * math.cos(ang), 146.0, off * math.sin(ang))
        if prev is not None:
            if math.dist(q, prev) > limit: fo += 1
            if math.hypot(math.hypot(q[0], q[2]) - math.hypot(prev[0], prev[2]), q[1] - prev[1]) > limit: fn += 1
        prev = q
    return fo, fn

# ---- 2. pose takeover, eye height channel, world-space model: pivot height P, raw eye E, shown eye S = P + D
def parse_seq(first_pat):
    """(dt, raw eye step) of the 'eye step raw' lines from the line after first_pat until 'takeover ended'"""
    fr = []; on = False
    for ln in open(LOG):
        if re.search(first_pat, ln): on = True
        if not on: continue
        m = re.search(r"dt ([\d.]+) \| eye step raw ([\d.]+) disp ([\d.]+)", ln)
        if m: fr.append((float(m.group(1)), float(m.group(2)), float(m.group(3))))
        if "takeover ended" in ln or (fr and ("STANCE" in ln or ("TRIGGER" in ln and not re.search(first_pat, ln)) and len(fr) > 30)): break
    return fr

def pose_run(frames, new, clamp, dE0=0.0, dP0=0.0, drift=1.0, jumpcm=12.0, T=0.25):
    """Frame 0: raw eye moves by dE0 and the pivot by dP0 (the logged jump); every later frame the raw eye drifts by the logged raw step
    (sign +, as the logged residuals show). old = k36 (Rv always updated, seed from the displayed h/y, ev unbounded), new = k37.
    Returns (max shown step - raw step, max shown step, max |e|, number of triggers)."""
    w = 6.0 / T
    E = P = 0.0; R = 0.0; Rv = 0.0; D = 0.0; Dv = 0.0; e = ev = 0.0; act = False
    S = 0.0; Sv = 0.0; worst = mxs = mxe = 0.0; ntrig = 0
    for k, (dt, step, _) in enumerate(frames):
        En = E + (dE0 if k == 0 else drift * step); Pn = P + (dP0 if k == 0 else 0.0)
        Rn = En - Pn; raw_step = abs(En - E)
        res = Rn - (R + Rv * dt); jumped = abs(res) > jumpcm; trig = False
        if jumped:
            if new:
                Ip = S + Sv * dt                                    # shown eye carried on in the WORLD, over the new pivot
                Dp = Ip - Pn
            else:
                Dp = D + Dv * dt                                    # old: displayed height over the pivot, carried on
            e = Dp - Rn; ev = Dv - Rv
            if new and ev * e > 0: ev = 0.0
            act = True; trig = True; ntrig += 1
        if act and not trig:
            a = ev + w * e; ex = math.exp(-w * dt); e, ev = (e + a * dt) * ex, (ev - a * w * dt) * ex
            if abs(e) < 0.05 and abs(ev) < 1.0: e = ev = 0.0; act = False
        Dn = Rn + (e if act else 0.0)
        Dv = (Dn - D) / dt
        if not (new and jumped): Rv = (Rn - R) / dt                 # new: keep the pre-jump glide on a jump frame
        D, R = Dn, Rn
        Sn = Pn + D
        if clamp:
            lim = raw_step + budget(dt); d = Sn - S
            if abs(d) > lim: Sn = S + math.copysign(lim, d)
            D = Sn - Pn                                             # the shown pose is what was shown
        shown_step = abs(Sn - S) if k > 0 or True else 0.0
        Sv = (Sn - S) / dt; S = Sn
        E, P = En, Pn
        worst = max(worst, shown_step - raw_step); mxs = max(mxs, shown_step); mxe = max(mxe, abs(e) if act else 0)
    return worst, mxs, mxe, ntrig
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

    ok = True
    print("\n== 1. stance detector on the owner's logged 'STANCE pop' lines (limit 6 cm)")
    rows = replay_stance(); bad_old = [r for r in rows if r[0] > 6.0]; false_new = [r for r in rows if r[1] > 6.0]
    for old, new, q, p in rows:
        print("  old vector step %5.1f cm | new (length,height) step %5.1f cm | q %s <- %s" % (old, new, ["%.1f" % x for x in q], ["%.1f" % x for x in p]))
    rot = [r for r in rows if r[0] > 20 and r[1] < 3]
    print("  %d logged pops: %d are pure turns (old step > 20 cm, new < 3 cm); new detector keeps %d of %d" % (len(rows), len(rot), len(false_new), len(rows)))
    fo, fn = rotation_test()
    print("  synthetic 900 deg/s turn with a 30 cm pivot offset, 2 s @240: false pops old %d, new %d" % (fo, fn))
    if fn != 0 or not rot: ok = False; print("  FAIL")
    # a real crouch pop must still be seen by the new detector
    real = math.hypot(0.0, 165.3 - 159.0)
    print("  real stance pop (logged 165.3 -> 159.0 cm height): new step %.1f cm -> detected %s" % (real, real > 6.0))
    if not real > 6.0: ok = False

    print("\n== 2. pose takeover replays (shown eye step minus raw eye step, cm; budget = max(0.8, 300*dt))")
    seqs = [
        ("19:31:21 mode takeover, raw eye jumps 69.7 cm in one frame, 2nd trigger 4 ms later (log: raw 1.13 -> shown 60.86, e y 130.6)",
         parse_seq(r"raw jump h 2\.7 y -69\.9"), dict(dE0=-69.7)),
        ("19:22:44 mode takeover, the PIVOT steps 12.3 cm while the eye stays (log: raw 0.72 -> shown 12.24)",
         parse_seq(r"raw jump h -0\.1 y 12\.3"), dict(dE0=0.72, dP0=-12.3)),
    ]
    print("  %-8s %-10s | %10s %10s %8s %5s" % ("variant", "", "shown-raw", "max shown", "max |e|", "trig"))
    for name, fr, kw in seqs:
        print(" ", name, "(%d logged frames)" % len(fr))
        for label, new, clamp in (("k36 old", False, False), ("k37 noclamp", True, False), ("k37 +clamp", True, True)):
            w, ms, me, nt = pose_run(fr, new, clamp, **kw)
            lim_ok = (w <= 0.8 + 1e-6 + max(300 * dt for dt, _, _ in fr) * 0 + 0.9) if clamp else True
            print("    %-9s %-10s | %10.2f %10.2f %8.1f %5d" % (label, "", w, ms, me, nt))
            if clamp:
                bmax = max(budget(dt) for dt, _, _ in fr)
                if w > bmax + 1e-6: ok = False; print("    FAIL: shown step exceeds raw + budget (%.2f)" % bmax)
    # a plain smooth glide must not be touched
    gl = [(0.006, 0.6, 0.6)] * 200
    w, ms, me, nt = pose_run(gl, True, True)
    print("  control: smooth glide, 200 frames: shown-raw %.3f, triggers %d (must be 0)" % (w, nt))
    if nt or abs(w) > 1e-6: ok = False
    print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)
