#!/usr/bin/env python3
"""Offline self-test of kl_menu_shots_1110 (no game, no dll of the game folder needed)."""
import json, os, sys, tempfile, shutil, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_menu_shots_1110 as K

fails = []


def check(c, msg):
    if not c:
        fails.append(msg); print('FAIL', msg)


def main():
    # script builders pass the klauto check
    for name, t in (('menus', K.menus_script()), ('host', K.match_host_script()), ('join', K.JOIN)):
        bad, ops = K.check_script(t, name)
        check(not bad, '%s script problems: %s' % (name, bad))
    # the checker catches mistakes
    bad, _ = K.check_script('[Script]\n1=bogus x\n2=jump nowhere\n3=tap NOKEY\n', 't')
    check(len(bad) >= 3, 'checker misses bad op / label / key: %s' % bad)
    bad, _ = K.check_script('[Script]\n1=wait 5\n3=wait 5\n4=pass 1\n', 't')
    check(any('numbering' in b for b in bad), 'checker misses numbering jump')
    # page labels match PAGES
    for run, text in (('menus', K.menus_script()), ('match', K.match_host_script())):
        import re
        got = re.findall(r'^\d+=log MENULOOK (\w+)\s*$', text, re.M)
        check(got == [p[1] for p in K.PAGES if p[0] == run], 'labels of %s: %s' % (run, got))
    check('onwin ShowAchievements' in K.menus_script(), 'Achievements guard missing')

    tmp = tempfile.mkdtemp()
    try:
        # gen + validate into a temp kit
        a = argparse.Namespace(kit=os.path.join(tmp, 'kit'), res='1280x720')
        K.cmd_gen(a)
        check(K.cmd_validate(argparse.Namespace(kit=a.kit)) == 0, 'validate fails on a fresh kit')
        ini = open(os.path.join(a.kit, 'MENULOOK_STOCK_MENUS_host.ini')).read()
        check('DeadMen=0' in ini and 'W=1280' in ini, 'stock ini override')
        # twin picking
        live = os.path.join(tmp, 'live.dll'); open(live, 'wb').write(b'ship')
        tw = os.path.join(tmp, 'twin.dll'); open(tw, 'wb').write(b'xx (TEST) xx')
        try:
            K.pick_twin(a.kit, live, None); check(False, 'unknown live dll must be refused')
        except SystemExit as e:
            check('REFUSED' in str(e), 'refusal text')
        try:
            K.pick_twin(a.kit, live, live); check(False, 'non-TEST override must be refused')
        except SystemExit:
            pass
        check(K.pick_twin(a.kit, live, tw)[2] == 'override', 'override accepted')
        live2 = os.path.join(tmp, 'live2.dll'); open(live2, 'wb').write(b'abc (TEST) abc')
        check('TEST build' in K.pick_twin(a.kit, live2, None)[2], 'live TEST dll runs as it is')
        # ship->test map through a kit twins.json with a real file
        d = os.path.join(a.kit, 'twins', 'tt'); os.makedirs(d)
        open(os.path.join(d, 'dinput8.dll'), 'wb').write(b'(TEST)')
        h = K.md5(live)[:8]
        tj = json.load(open(os.path.join(a.kit, 'twins.json')))
        tj['ship_to_test'][h] = {'test': 'tt', 'note': 'x', 'file': 'twins/tt/dinput8.dll'}
        json.dump(tj, open(os.path.join(a.kit, 'twins.json'), 'w'))
        p, t8, why = K.pick_twin(a.kit, live, None)
        check(p.endswith('dinput8.dll') and t8 == 'tt', 'ship->twin map')
        # shot picking
        shots = [('a', 100.0), ('b', 102.5), ('c', 104.9), ('d', 120.0)]
        p, how = K.pick_shot(shots, 101.0, 4)
        check(p == 'c' and how == 'settled', 'pick_shot %s %s' % (p, how))
        check(K.pick_shot(shots, 200.0, 3)[0] is None, 'pick_shot missing')
        # step parse
        lg = os.path.join(tmp, 'k.log')
        open(lg, 'w').write('10:00:01.250 script 5: MENULOOK lobby\n10:00:09.000 other\n')
        check(K.read_steps(lg) == [(36001.25, 'lobby')], 'read_steps')
        # ML5
        open(lg, 'w').write('x menulook: kaneandlynch.WHD -> _deadmen\nx menulook: kaneandlynch.WAV -> _deadmen\n')
        check(K.ml5_proof(lg, 'deadmen')[0] and not K.ml5_proof(lg, 'stock')[0], 'ml5 deadmen')
        open(lg, 'w').write('x menulook: off (DeadMen=0)\n')
        check(K.ml5_proof(lg, 'stock')[0] and not K.ml5_proof(lg, 'deadmen')[0], 'ml5 stock')
        # ML1 on synthetic images
        try:
            from PIL import Image, ImageDraw
            inv = os.path.join(tmp, 'inv'); os.makedirs(inv)
            hdr = '| # | a | b | name | type | c | x | y | w | h | d | e | f | font | g | text |\n'
            row = lambda i, n, x, y, w: '| %d | | | %s | Text | | %d | %d | %d | 20 | | | | 1 | | hello |\n' % (i, n, x, y, w)
            open(os.path.join(inv, 'w.md'), 'w').write('## Window `TestWin`\n' + hdr + row(1, 'A', 10, 10, 100) + row(2, 'B', 50, 10, 100))
            els = K.inv_elements('TestWin', inv)
            check(len(els) == 2 and els[0]['x'] == 10, 'inv parse %s' % els)
            def img(wid):
                im = Image.new('RGB', (1280, 720), (0, 0, 0)); dr = ImageDraw.Draw(im)
                x0 = 256 + 10; y0 = 72 + 10
                dr.rectangle([x0, y0, x0 + wid, y0 + 10], fill=(255, 255, 255)); return im
            img(40).save(os.path.join(tmp, 'st.png')); img(95).save(os.path.join(tmp, 'dm.png'))
            rows = K.compare_page(os.path.join(tmp, 'dm.png'), os.path.join(tmp, 'st.png'), ['TestWin'], inv)
            check(any('declared-overlap' in r for r in rows), 'overlap not found: %s' % rows)
            check(any('wider-than-stock' in r for r in rows), 'wider not found: %s' % rows)
        except ImportError:
            print('SKIP ML1 image test (PIL missing)')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
