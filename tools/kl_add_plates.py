#!/usr/bin/env python3
"""Add Payday 2 face plates to an already-built KL wardrobe level.

    python kl_add_plates.py <wardrobe build> <output folder>
        [--plates=wolf,dallas,chains,hoxton] [--slot=F01]

This deliberately does not run the full wardrobe conversion again.  The input
must contain chars.json produced by kl_chars.py wardrobe.
"""
import json
import os
import sys

import kl_chars as C
import kl_prmgraph as G
import kl_texmat as T
import kl_pd2mask


def _variants(lv, chars):
    p = G.read(lv[".prm"], "dd")
    return {c["name"]: {p.chunks[o][0x0f] for o in C.objects(p, c["root"])}
            for c in chars}


def build(src, out, slot="F01", names=("wolf", "dallas", "chains", "hoxton")):
    if not os.path.isdir(src):
        raise ValueError("%s is not a build folder" % src)
    manifest = os.path.join(src, "chars.json")
    if not os.path.isfile(manifest):
        raise ValueError("%s has no chars.json; it is not a wardrobe build" % src)
    with open(manifest, encoding="utf-8") as f:
        old = json.load(f)
    chars = old.get("characters")
    if not isinstance(chars, list) or len(chars) != 16:
        raise ValueError("chars.json must describe the sixteen wardrobe characters")
    if int(old.get("masks", 8)) != C.STOCK_MASKS:
        raise ValueError("input already has extended masks; refusing a second plate pass")

    names = list(names)
    if not names or len(set(names)) != len(names):
        raise ValueError("--plates must name each plate once")
    if len(names) > C.PD2_MASKS:                       # variant numbers: OUTFIT_STEP = STOCK_MASKS + PD2_MASKS + 2
        raise ValueError("%d plates, the variant numbering has room for %d" % (len(names), C.PD2_MASKS))
    if os.path.abspath(out) == os.path.abspath(src):
        raise ValueError("the output folder is the build folder: give another one (the build is not written over)")
    lv = C.Lv(src)
    before = _variants(lv, chars)
    os.makedirs(out, exist_ok=True)
    p = G.read(lv[".prm"], "dd")
    mat = T.read_mat(lv[".MAT"])
    tex = T.read_tex(lv[".TEX"])
    specs = kl_pd2mask.plate_specs(",".join(names), lv)
    plates = kl_pd2mask.add_plates(p, mat, tex, chars, specs)
    lv[".prm"] = G.write(p)
    mat.refs = T.material_refs(lv[".prm"], mat.ninst)
    lv[".MAT"] = T.write_mat(mat)
    lv[".TEX"] = T.write_tex(tex)
    new_manifest = dict(old)
    new_manifest["base"], new_manifest["slot"] = src, slot     # the manifest described the wardrobe build, not this one
    new_manifest["masks"] = C.STOCK_MASKS + len(specs)
    new_manifest["plate_names"] = list(names)
    new_manifest["plate_report"] = plates
    path = lv.write(out, slot)
    C.wardrobe_ini(new_manifest, os.path.join(out, "KLWardrobe.ini"))
    import kl_impact
    limit = kl_impact.chunk_limit(lv[".prm"])
    if limit:
        raise ValueError("chunk table limit: %s" % limit[:3])
    after = _variants(C.Lv(out), chars)
    for character in chars:
        expected_plates = {C.variant_of(k, C.STOCK_MASKS + i + 1)
                           for k in range(character["bodies"]) for i in range(len(specs))}
        missing = expected_plates - after[character["name"]]
        removed = before[character["name"]] - after[character["name"]]
        if missing or removed:
            raise ValueError("%s: missing plate variants %s; removed variants %s" %
                             (character["name"], sorted(missing), sorted(removed)))
    report = dict(base=src, slot=slot, masks=C.STOCK_MASKS + len(specs), plates=plates)
    with open(os.path.join(out, "chars.json"), "w", encoding="utf-8") as f:
        json.dump(new_manifest, f, indent=1, default=str)
    print("built %s; masks: %d; plates: %d" % (path, report["masks"], len(plates)))
    return report


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        raise SystemExit(__doc__)
    names = next((x.split("=", 1)[1].split(",") for x in args if x.startswith("--plates=")),
                 ["wolf", "dallas", "chains", "hoxton"])
    slot = next((x.split("=", 1)[1] for x in args if x.startswith("--slot=")), "F01")
    build(args[0], args[1], slot, names)
