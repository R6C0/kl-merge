/* klclubcalm.c - [ClubCalm] READ-ONLY probe for "guns holstered, the club calm until you draw" (Last Call, 2026-10-24).
 *
 * The owner's wish: start Last Call with no gun out and the club calm; the guards and bouncers turn on you when you draw
 * or fire. WHAT IS KNOWN (re/club_crowd.md): nothing in the data of Dog Days' scenes reacts to a drawn weapon (no
 * ZSneakTrigger / ZShootAtTrigger / psycho trigger class in Dog Days' or Dead Men's .prp files), and the only runtime
 * lever found, the police byte [player+0x2723], also turns the bots on the human, so it is NOT used. [player+0x920] is the
 * item in the hand, 0 = empty (klhud_weapon.c: it only decides bright or dim on the HUD - it is not known to be a real
 * holster state). This file therefore changes NOTHING in the game. It writes one log line whenever the local human's
 * hand item ([player+0x920] / [player+0x924] selected) changes and, with Shots=1, whenever his FIRED byte
 * ([input+0x3c], klshoulder.c) goes up, so the next live run on DM05A tells us: does the game ever hold the hand empty
 * at the round start, what does a draw look like in these two fields, and how soon after it the guards open fire. Only
 * then can an Act= switch (wake / alert the guards) be written on facts. No offsets are guessed here: every address
 * is one klshoulder.c / klhud_weapon.c already read.
 *
 * KEYS ([ClubCalm]): Enable=0  Shots=1 (also log the first fired byte of each burst)  Every=250 (ms between looks, at least 100)
 */
static struct { int on, shots; DWORD every, at; DWORD hand, sel; BYTE fired; int seen; } klcc;

static void klcc_tick(int game_thread)
{
    DWORD gd, pl, hand, sel, now = GetTickCount(); BYTE idx = 0xff, f = 0; DWORD h;
    if (!klcc.on || !game_thread || !klx_on) return;
    if (klcc.at && now - klcc.at < klcc.every) return;
    klcc.at = now;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLO_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || idx > 31) return;
    if (!(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_pvt(pl) != KLO_PLAYER_VT) return;
    hand = klh_rd32(pl + 0x920); sel = klh_rd32(pl + 0x924);
    if (!klcc.seen || hand != klcc.hand || sel != klcc.sel) {
        klog("clubcalm: hand item %lu (was %lu), selected %lu (was %lu)%s", (unsigned long)hand, (unsigned long)klcc.hand, (unsigned long)sel,
             (unsigned long)klcc.sel, klcc.seen ? "" : " [first look]");
        klcc.hand = hand; klcc.sel = sel; klcc.seen = 1;
    }
    if (klcc.shots && (h = klo_input(gd, pl)) != 0) {
        f = 0; klh_rd(h + 0x3c, &f, 1);
        if (f && !klcc.fired) klog("clubcalm: fired byte went up (hand item %lu)", (unsigned long)hand);
        klcc.fired = f;
    }
}

static void klcc_init(void)
{
    klcc.on = GetPrivateProfileIntA("ClubCalm", "Enable", 0, klh_ini) != 0;
    klcc.shots = GetPrivateProfileIntA("ClubCalm", "Shots", 1, klh_ini) != 0;
    klcc.every = GetPrivateProfileIntA("ClubCalm", "Every", 250, klh_ini); if (klcc.every < 100) klcc.every = 100;
    if (klcc.on) klog("clubcalm: on (READ-ONLY probe: logs the human's hand item%s every %lu ms; changes nothing)", klcc.shots ? " and shots" : "", (unsigned long)klcc.every);
}
