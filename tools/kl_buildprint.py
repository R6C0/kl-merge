#!/usr/bin/env python3
"""
kl_buildprint - offline "do we have the same build?" fingerprint for private matches.

    python tools/kl_buildprint.py [<Dog Days folder>] [--out FILE] [--all] [--quick] [-v]
    python tools/kl_buildprint.py [<Dog Days folder>] --compare FILE

Why: re/private_match.md / private_match_buildcheck.md - the Fragile Alliance start gate never
looks at map content, so every player needs the identical expansion build; the in-hook lobby
check (klx_build / klx_slots) is designed but not built. Players run this tool, read the 8-hex
BUILD CODE to each other, and use --out / --compare to see WHICH map differs. Read-only: nothing
in the game folder is written (the optional --out file goes wherever you say).

What is fingerprinted
  Per map folder under <DD>\\KLExpansion\\Maps (all of them; those that a redirect rule actually
  points at are marked "active" with the slot/page that uses them) a map hash over:
   * every *_Main.zip: NOT the bytes. Hash of the zip central directory entries (member name,
     CRC-32, uncompressed size), sorted by name. Sound: the CRC-32 is of the uncompressed member, so
     it covers content; member times and compression level (which differ with every rebuild,
     buildcheck section 10 notes klx_fingerprint's raw central directory hashes the DOS timestamp)
     are deliberately left out. Weakness: CRC-32 is not collision proof against a deliberate
     forgery (this is an accident detector, not security) and a bit-identical rebuild with a
     different compression gives the SAME print (correct: the engine sees the same members).
     It is fast (one seek to the tail of a 200 MB file) and still falls back to full-bytes if the
     zip cannot be parsed.
   * Fxx_Main.WHD, Fxx_Main.WAV, Fxx_Main_LS.SND, Fxx_Main.hti: full-content hash (blake2b, streamed).
     The .WHD is the sound index the scene's sound ids point into (CLAUDE.md: .SND ids are offsets
     into the level's sounds), so a mismatch changes which sound plays; GUESS that a WAV-only
     mismatch cannot desync objects (audio only) but it is included because it is cheap to see and
     the owner builds regenerate WHD+WAV together. .hti: GUESS, texture index, included.
   * KLJoin.ini, KLTalk.ini, KLWardrobe.ini, KLGuns.ini beside the map: content hash with comments and
     blank lines stripped. KLWardrobe/KLGuns decide which bodies/guns exist (an index the peer does
     not have is a visible/net problem, GUESS: object ids over the wire); KLJoin/KLTalk drive crew AI and
     lines, host-side AI per buildcheck section 4 (GUESS: clients do not simulate it), so a
     mismatch there is likely harmless but is still listed as a separate "soft" hash (j=) next to the
     hard one (h=). The overall code uses ONLY the hard hashes plus the soft ones when --strict.
  Skipped on purpose: *.before-*, *.absent, *.log, *.bak, other backups (the game never reads them);
     Fxx_Main_LS_<Language>.WAV/.WHD (loading-screen voice, local presentation; GUESS no sync effect;
     --all includes them); timestamps.
  Global: hook dll (dinput8.dll, full hash), KLHook.ini (comments/blank lines stripped, section names
     and keys case-folded, sorted; presentation-only sections dropped: Graphics, HUD, ReShade,
     Camera, Censor, Shoulder, Memory, Steam, Load, KLHook, Page.*, Wardrobe, Character (GUESS:
     local look / UI; everything else - Balance, Bots, Redirect*, Down, Fed ... - can change
     gameplay and stays), Patch01.zip (CD hash; buildcheck section 4: mounted first, overrides every
     archive), and the redirect table itself.
  Redirects: [Redirect] and [Redirect.N] sections of KLHook.ini (klslot.c) give slot -> folder per
     menu page; their normalised text is hashed as "redirect table" (buildcheck section 10), and the
     per-map line says which slots use that map.

Build code = first 8 hex of blake2b over: dll hash, ini hash, Patch01 hash, redirect table, then
  every ACTIVE map's name + hard hash (sorted by folder name). Inactive folders are listed but do not
  change the code (a player with extra, unused maps still matches); --strict counts all folders.
  Maps are hashed whether or not active, so --compare can show them.
Runtime: zips are instant (central directory only). Measured 2026-10-18 on the owner's PC: 1.1 s for 27 map
folders, 665 MB of WAV/WHD/SND/hti read (warm disk cache; a cold HDD read is bound by ~665 MB of I/O).
--quick skips WAV content (size only).
"""
import hashlib
import os
import re
import sys
import time
import zipfile

SOFT = {"kljoin.ini", "kltalk.ini"}
INI_SIDE = {"kljoin.ini", "kltalk.ini", "klwardrobe.ini", "klguns.ini"}
DROP_SECTIONS = {"graphics", "hud", "reshade", "camera", "censor", "shoulder", "memory", "steam",
                 "load", "klhook", "wardrobe", "character"}
BACKUP = re.compile(r"\.(before|bak|absent|old|orig)|\.log$|~$", re.I)
LANG_LS = re.compile(r"_Main_LS_[A-Za-z]+\.(WAV|WHD)$", re.I)
SIDE_EXT = (".whd", ".wav", ".snd", ".hti")


def h():
    return hashlib.blake2b(digest_size=16)


def file_hash(path, chunk=1 << 22):
    d = h()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            d.update(b)
    return d.hexdigest()


def zip_print(path):
    """hash of (name, crc32, size) of every member, sorted by name; full bytes if unparsable"""
    try:
        with zipfile.ZipFile(path) as z:
            rows = sorted((i.filename, i.CRC, i.file_size) for i in z.infolist())
        d = h()
        for n, c, s in rows:
            d.update(("%s|%08x|%d\n" % (n, c, s)).encode("utf-8", "replace"))
        return d.hexdigest() + ("" if rows else "-empty"), "cd:%d" % len(rows)
    except Exception as e:  # noqa
        return file_hash(path), "bytes(%s)" % type(e).__name__


def norm_ini_text(path, drop=()):
    """comments/blank stripped; sections and keys lower-cased; sections sorted (order inside kept)"""
    secs, cur = {}, ""
    with open(path, "rb") as f:
        txt = f.read().decode("latin-1")
    for ln in txt.splitlines():
        ln = ln.strip()
        if not ln or ln[0] in ";#":
            continue
        if ln.startswith("["):
            cur = ln.strip("[]").strip().lower()
            secs.setdefault(cur, [])
            continue
        if "=" in ln:
            k, v = ln.split("=", 1)
            ln = k.strip().lower() + "=" + v.split(";")[0].strip()
        secs.setdefault(cur, []).append(ln)
    out = []
    for s in sorted(secs):
        if s in drop or s.startswith("page."):
            continue
        out.append("[%s]" % s)
        out += secs[s]
    return "\n".join(out) + "\n", secs


def ini_hash(path, drop=()):
    t, secs = norm_ini_text(path, drop)
    return hashlib.blake2b(t.encode(), digest_size=16).hexdigest()


def redirects(inipath):
    """{(page, slot): folder} from [Redirect] (page 0) and [Redirect.N]"""
    _, secs = norm_ini_text(inipath)
    out = {}
    for s, lines in secs.items():
        m = re.fullmatch(r"redirect(?:\.(\d+))?", s)
        if not m:
            continue
        page = int(m.group(1) or 0)
        for ln in lines:
            if "=" in ln:
                k, v = ln.split("=", 1)
                out[(page, k.strip().upper())] = v.strip()
    return out


def map_print(folder, allfiles, quick):
    """returns (hard_hash, soft_hash, [detail lines], bytes_read)"""
    hard, soft = h(), h()
    det, nread = [], 0
    for name in sorted(os.listdir(folder), key=str.lower):
        p = os.path.join(folder, name)
        if not os.path.isfile(p) or BACKUP.search(name):
            continue
        low = name.lower()
        if LANG_LS.search(name) and not allfiles:
            continue
        if low.endswith(".zip"):
            hv, how = zip_print(p)
            tgt = hard
        elif low in INI_SIDE:
            hv, how = ini_hash(p), "ini"
            tgt = soft if low in SOFT else hard
        elif low.endswith(SIDE_EXT):
            sz = os.path.getsize(p)
            if quick and low.endswith(".wav"):
                hv, how = "size%d" % sz, "size-only"
            else:
                hv, how = file_hash(p), "bytes"
                nread += sz
            tgt = hard
        else:
            continue
        tgt.update(("%s|%s\n" % (low, hv)).encode())
        det.append("    %-28s %s  %s%s" % (name, hv[:12], how, "  (soft)" if tgt is soft else ""))
    return hard.hexdigest()[:16], soft.hexdigest()[:16], det, nread


def compute(dd, allfiles=False, quick=False, strict=False):
    t0 = time.time()
    res = {"maps": {}, "global": {}}
    ini = os.path.join(dd, "KLHook.ini")
    dll = os.path.join(dd, "dinput8.dll")
    g = res["global"]
    g["dll"] = file_hash(dll)[:16] if os.path.isfile(dll) else "absent"
    g["ini"] = ini_hash(ini, DROP_SECTIONS)[:16] if os.path.isfile(ini) else "absent"
    p1 = os.path.join(dd, "Patch01.zip")
    g["patch01"] = zip_print(p1)[0][:16] if os.path.isfile(p1) else "absent"
    red = redirects(ini) if os.path.isfile(ini) else {}
    g["redirect"] = hashlib.blake2b(
        "\n".join("%d:%s=%s" % (pg, sl, f) for (pg, sl), f in sorted(red.items())).encode(),
        digest_size=16).hexdigest()[:16]
    used = {}
    for (pg, sl), f in sorted(red.items()):
        used.setdefault(f, []).append("%s%s" % (sl, "" if pg == 0 else "@p%d" % pg))
    root = os.path.join(dd, "KLExpansion", "Maps")
    nread = 0
    names = sorted(os.listdir(root)) if os.path.isdir(root) else []
    for n in names:
        p = os.path.join(root, n)
        if not os.path.isdir(p):
            continue
        hd, sf, det, nr = map_print(p, allfiles, quick)
        nread += nr
        res["maps"][n] = {"hard": hd, "soft": sf, "active": used.get(n, []), "detail": det}
    for f in used:   # a redirect to a folder that does not exist is itself a difference
        if f not in res["maps"]:
            res["maps"][f] = {"hard": "MISSING", "soft": "MISSING", "active": used[f], "detail": []}
    c = h()
    for k in ("dll", "ini", "patch01", "redirect"):
        c.update(("%s=%s\n" % (k, g[k])).encode())
    for n in sorted(res["maps"]):
        m = res["maps"][n]
        if m["active"] or strict:
            c.update(("%s=%s%s\n" % (n, m["hard"], m["soft"] if strict else "")).encode())
    res["code"] = c.hexdigest()[:8]
    res["seconds"] = time.time() - t0
    res["bytes"] = nread
    return res


def render(res, verbose=False):
    L = ["BUILD CODE: %s" % res["code"].upper(), ""]
    for k in ("dll", "ini", "patch01", "redirect"):
        L.append("global %-9s %s" % (k, res["global"][k]))
    L.append("")
    for n in sorted(res["maps"]):
        m = res["maps"][n]
        L.append("map %-8s h=%s j=%s %s" % (n, m["hard"], m["soft"],
                 ("active:" + ",".join(m["active"])) if m["active"] else "inactive"))
        if verbose:
            L += m["detail"]
    return "\n".join(L) + "\n"


def parse(path):
    r = {"code": None, "global": {}, "maps": {}}
    for ln in open(path, encoding="utf-8"):
        t = ln.split()
        if ln.startswith("BUILD CODE:"):
            r["code"] = t[2].lower()
        elif ln.startswith("global "):
            r["global"][t[1]] = t[2]
        elif ln.startswith("map "):
            r["maps"][t[1]] = {"hard": t[2][2:], "soft": t[3][2:],
                               "active": t[4].startswith("active")}
    return r


def compare(mine, other):
    out = ["your code %s, theirs %s: %s" % (mine["code"].upper(), (other["code"] or "?").upper(),
           "SAME" if mine["code"] == other["code"] else "DIFFERENT")]
    for k in sorted(set(mine["global"]) | set(other["global"])):
        a, b = mine["global"].get(k), other["global"].get(k)
        if a != b:
            out.append("  global %s differs: %s vs %s" % (k, a, b))
    for n in sorted(set(mine["maps"]) | set(other["maps"])):
        a, b = mine["maps"].get(n), other["maps"].get(n)
        if a is None or b is None:
            out.append("  map %s: only %s has it" % (n, "you" if b is None else "they"))
        elif a["hard"] != b["hard"]:
            out.append("  map %s DIFFERS (files that matter): %s vs %s" % (n, a["hard"], b["hard"]))
        elif a["soft"] != b["soft"]:
            out.append("  map %s differs only in KLJoin/KLTalk (soft, probably harmless)" % n)
    if len(out) == 1 and mine["code"] != other["code"]:
        out.append("  only inactive maps or strict-only parts differ")
    return "\n".join(out) + "\n"


def main(argv):
    args = list(argv)
    opt = {"out": None, "compare": None}
    flags = set()
    pos = []
    while args:
        a = args.pop(0)
        if a in ("--out", "--compare"):
            opt[a[2:]] = args.pop(0)
        elif a.startswith("--") or a == "-v":
            flags.add(a)
        else:
            pos.append(a)
    dd = pos[0] if pos else r"C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
    res = compute(dd, "--all" in flags, "--quick" in flags, "--strict" in flags)
    txt = render(res, "-v" in flags)
    if opt["out"]:
        with open(opt["out"], "w", encoding="utf-8") as f:
            f.write(render(res, False))
    print(txt, end="")
    if opt["compare"]:
        print()
        print(compare(parse_text(render(res)), parse(opt["compare"])), end="")
    print("\n(%.1f s, %.0f MB of side files read)" % (res["seconds"], res["bytes"] / 1e6))
    return 0


def parse_text(t):
    import tempfile
    fd, p = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(t)
        return parse(p)
    finally:
        os.remove(p)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
