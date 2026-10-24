"""Offline simulation of klhook/klfps.c adaptive pacing (same integer maths as klfps_pace_feed / klfps_step).
Work times model the owner's log: 153..251 fps free-running (4.0 .. 6.5 ms), slow drift, a 40 ms hitch every ~600 frames.
Prints frametime spread for: no cap, fixed 240 cap, fixed cap + Adaptive. GUESS: the work model, not a measurement."""
import random

FREQ = 10_000_000


def run(adaptive, cap, n=20000, seed=7):
    rnd = random.Random(seed)
    period = FREQ // cap if cap else 0
    pace = 0
    t = 0
    deadline = 0
    last = None
    ft = []
    ret = 0
    for i in range(n):
        base = 4.0e-3 + 1.2e-3 * (1 + __import__('math').sin(i / 400.0))
        w = base * rnd.uniform(0.85, 1.25)
        if rnd.random() < 1 / 600:
            w += 40e-3
        t += int(w * FREQ)
        if adaptive and cap and ret:
            work = t - ret
            lo, hi = period, FREQ // 30
            ref = max(pace, lo)
            work = min(work, ref * 3 // 2)
            if not pace:
                pace = max(work, lo)
            elif work > pace:
                pace += (work - pace) * 5 // 100
            else:
                pace -= (pace - work) * 1 // 100
            pace = min(max(pace, lo), hi)
        if cap:
            if not deadline:
                deadline = t
            if t < deadline:
                t = deadline
            deadline += max(period, pace) if adaptive else period
            if t > deadline:
                deadline = t + max(period, pace if adaptive else 0)
        if last is not None:
            ft.append((t - last) / FREQ * 1000)
        last = t
        ret = t
    ft.sort()
    m = sum(ft) / len(ft)
    sd = (sum((x - m) ** 2 for x in ft) / len(ft)) ** 0.5
    p1 = ft[int(len(ft) * 0.99)]
    # steady frames only: drop the injected hitches
    steady = [x for x in ft if x < 20]
    ms = sum(steady) / len(steady)
    ssd = (sum((x - ms) ** 2 for x in steady) / len(steady)) ** 0.5
    return m, sd, p1, ssd, 1000 / m


if __name__ == '__main__':
    for name, ad, cap in (('uncapped', 0, 0), ('fixed 240', 0, 240), ('adaptive 240', 1, 240)):
        m, sd, p1, ssd, fps = run(ad, cap)
        print('%-13s avg %.2f ms (%.0f fps)  sd %.2f  steady-sd %.2f  p99 %.2f ms' % (name, m, fps, sd, ssd, p1))
