/*
 * klhud_tags.c - THE TAGS OVER THE AI HEISTERS' HEADS in the new look: quiet INITIALS (and, on request, their money) drawn by the
 * game's own tag drawer 0x7b8150 with OUR text objects. Spec, the reading of kl2.exe with addresses, keys, guesses, live check G1:
 * re\hud_tags.md. NOT RUN IN THE GAME.
 * Part of KLHook, an add-on of klhud.c: included by klhook.c AFTER klhud_escape.c (it uses klhud.c's klu / klu_r / klu_cs /
 * klu_make_obj / klu_set / klu_dollars, klbot.c's klb_snap, klhud_values.c's kluv_kind and klhud_names.c's klnm_tag_ini).
 *
 * THE FACT (re\hud_tags.md 1): the tags are drawn by the FIRST LOOP of ZFAPlayerListDisplay's Render (slot 2 = 0x5e60f0): for every
 * entry of the element (el+0x2c + i * 0x10c, count el+0x28, at most 12) it calls 0x7b8150 on the entry's tag struct (entry + 0x38:
 * [+0] a ZCHAROBJ made by 0x51f3b0, style 0x44 = centred, colour 0xbbe494, layer 0xf). The same function then draws the top-left
 * block and the crew rows, so the element cannot be split by hiding parts of it. klhud hides the whole element (+0x25) - and the
 * tags went with it. THE ROUTE: the element stays HIDDEN (nothing of the top-left block is drawn, nothing is blanked, nothing has to
 * be restored); from the clock element's Render slot (the one place whose draws are proven) this part runs the first loop ITSELF:
 * the same conditions, the same node ([record + 4], the record = rules[+0x348] + 0x7c * id: 0x7fd930), the same call of 0x7b8150 -
 * but on a COPY of the tag struct whose text pointer is one of OUR objects (initials; the money line; a 1 px shadow under each).
 * So the game projects the head, we choose the words, the font and the colour. The record's name string is not touched
 * ([HUD] NameTags stays 0: the kill feed and the score page keep the full names).
 *
 * Keys ([HUD]; need Enable=1 and HideStock=1 - with the stock block shown the stock draws its own tags and this part is idle):
 *   HeadTags=0|1|2     0 none (the tags go with the hidden element, as before), 1 initials, 2 initials + money line.  (default: 1 under Draft, else 0)
 *   HeadShadow=1       a 1 px shadow object under each text (drawn first); a GUESS that SetOffset moves it
 *   HeadLine=N         the money line's distance below the initials in virtual pixels (default: the names font's cap + 5)
 *
 * SHIP rule kept: no code byte of kl2.exe changes; every game read is a checked read except the heap objects the tick validated in
 * the same lock; calls: 0x7b8150 (the game's own, same arguments as its Render), SetText / SetColour / SetOffset of our own objects.
 */
#ifndef KLHUD_TAGS_C
#define KLHUD_TAGS_C

#define KLHT_NSLOT       12                    /* the element holds at most 12 entries (0x470b65: cmp eax, 0xc) */
#define KLHT_ESTRIDE     0x10c
#define KLHT_E0          0x2c
#define KLHT_O_COUNT     0x28
#define KLHT_O_LOCAL     0xefc                 /* byte: the local player's entry (the top-left block shows him) */
#define KLHT_O_OLD       0xed8                 /* byte: the Render's first condition (0x5e61df) */
#define KLHT_TAGOFF      0x38                  /* the tag struct inside an entry; 0x44 bytes, [+0x40] a byte the drawer tests */
#define KLHT_TAGSIZE     0x44
#define KLHT_DRAWTAG     0x007b8150u
#define KLHT_SETOFS      0x0045d6e0u
#define KLHT_C_OUTLINE   0xd8080808u           /* v22: the outline's colour (alpha d8, near black); GUESS that the 'colour' of a text object carries its alpha as the shadows' 0x60000000 do */
#define KLHT_LAYER       0xf                   /* the stock tag text's layer (0x51f466) */

struct klht_slot {
    int ok, id, show, made;
    DWORD ini, inis, mon, mons, actor, out[4];
    char ini_cur[16], mon_cur[24]; DWORD ini_col;
};

static struct { int mode, shadow, outline, font, tab, tabdone; float line, tabpadx, tabpady, tabdy; } klht;
static struct { int active, fault, told, shown; DWORD tmpl, pl, recs; int n; struct klht_slot s[KLHT_NSLOT]; } klht_r;
static volatile LONG klht_n_draw, klht_n_nonode, klht_n_cond, klht_n_flag, klht_n_peak;

static const BYTE klht_code[10] = { 0x83, 0xec, 0x68, 0x53, 0x8b, 0xd9, 0x80, 0x7b, 0x40, 0x00 };      /* 0x7b8150 sub esp,0x68 ; push ebx ; mov ebx,ecx ; cmp byte [ebx+0x40],0 */
typedef void (__fastcall *klht_drawtag_t)(void *, void *, DWORD, DWORD, void *, void *, DWORD);

static DWORD klht_font(int role) { return klu.fontset && role >= 0 && role < KLU_NFONT ? klu_r.fonts[role] : klu_r.font; }

static void klht_offset(DWORD obj, float x, float y)
{   /* ZCHAROBJ slot +0x21c = 0x45d6e0 (vec*, byte), ret 8: stores +0x1c / +0x20 and re-lays out when it changed */
    float v[2]; v[0] = x; v[1] = y;
    if (klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + 0x21c)) != KLHT_SETOFS) return;
    ((void (__fastcall *)(void *, void *, float *, DWORD))(DWORD_PTR)KLH_VA(KLHT_SETOFS))((void *)(DWORD_PTR)obj, 0, v, 0);
}

static int klht_make(struct klht_slot *q)
{   /* the four objects of one entry (money ones only at HeadTags=2) */
    char why[160]; DWORD fi = klht_font(klht.font), fm = klht_font(KLU_FNT_SMALL); int k;
    if (!(q->ini = klu_make_obj(klu_r.tmpl, fi, KLU_STYLE_CENTRE, KLU_C_CHALK, KLHT_LAYER, why))) goto bad;
    if (klht.outline) {                                                /* v22: a dark 1 px outline (four copies at the diagonals) - the tags read on bright walls (audit T1) */
        static const float od[4][2] = { { -1, -1 }, { 1, -1 }, { -1, 1 }, { 1, 1 } };
        for (k = 0; k < 4; k++) {
            if (!(q->out[k] = klu_make_obj(klu_r.tmpl, fi, KLU_STYLE_CENTRE, KLHT_C_OUTLINE, KLHT_LAYER - 1, why))) goto bad;
            klht_offset(q->out[k], od[k][0], od[k][1]);
        }
    }
    else if (klht.shadow && !(q->inis = klu_make_obj(klu_r.tmpl, fi, KLU_STYLE_CENTRE, KLU_SHADOW_SMALL, KLHT_LAYER - 1, why))) goto bad;
    if (klht.mode == 2) {
        if (!(q->mon = klu_make_obj(klu_r.tmpl, fm, KLU_STYLE_CENTRE, KLU_C_GREEN, KLHT_LAYER, why))) goto bad;
        if (klht.shadow && !(q->mons = klu_make_obj(klu_r.tmpl, fm, KLU_STYLE_CENTRE, KLU_SHADOW_SMALL, KLHT_LAYER - 1, why))) goto bad;
    }
    if (q->inis) klht_offset(q->inis, 1.0f, 1.0f);
    if (q->mon) klht_offset(q->mon, 0.0f, klht.line);                  /* GUESS: the offset is in virtual pixels, y down */
    if (q->mons) klht_offset(q->mons, 1.0f, klht.line + 1.0f);
    q->made = 1; q->ini_col = KLU_C_CHALK;
    if (klu.log >= 2 && klht.outline) {         /* v23 (review SHOULD): read the outline colour back - find the dword in the object (offset unknown) */
        DWORD w, off; int found = 0;
        for (off = 4; off < 0x100; off += 4) if (klh_rd(q->out[0] + off, &w, 4) && w == KLHT_C_OUTLINE) { klog("tags: outline colour %08lx is stored at object+0x%lx (alpha byte kept: %s)", w, off, (w >> 24) == 0xd8 ? "yes" : "no"); found = 1; break; }
        if (!found) klog("tags: outline colour %08lx written to the object but not found in its first 0x100 bytes (stored in another form: A1 judges by eye)", KLHT_C_OUTLINE);
    }
    return 1;
bad:
    klog("tags: an object of a tag could not be made (%s): the tags stand down for this level", why);
    return 0;
}

/* M1 (review): called from klu_reset inside klu_cs. A scene change frees the objects whatever address the next template lands at. */
static void klht_reset(void)
{
    int t = klht_r.told; DWORD tm = klht_r.tmpl; (void)tm;
    memset(&klht_r, 0, sizeof klht_r);
    klht_r.told = t;
}

/* THE TICK (game thread; the HUD's own 100 ms): the table of what to draw for each entry. Called after klu_hide_tick. */
static void klht_tick(DWORD osd, const struct klb_snap *s, int show)
{
    DWORD pl, cnt = 0, recs; int i; BYTE local = 0xff; char buf[16], mb[24];
    if (!klht.mode) return;
    EnterCriticalSection(&klu_cs);
    if (klht_r.tmpl != klu_r.tmpl) { memset(&klht_r, 0, sizeof klht_r); klht_r.tmpl = klu_r.tmpl; }      /* a new level: its objects went with the old scene */
    klht_r.active = 0;
    /* only while the stock element is hidden BY US (klu_r.hid) in the state the stock draws tags in (0x5e6120: state 0x19) */
    if (!klu_r.made || klu_r.fault || klht_r.fault || !show || !klu_r.hid || !s || s->state != 0x19 || !s->rules) goto out;
    pl = klh_rd32(osd + KLU_O_PLIST);
    if (!pl || klh_rd32(pl) != KLU_PLIST_VT || !klh_rd(pl + KLHT_O_COUNT, &cnt, 4) || cnt > KLHT_NSLOT) goto out;
    if (!klh_rd(pl + KLHT_O_LOCAL, &local, 1)) goto out;
    if (!(recs = klh_rd32(s->rules + 0x348))) goto out;
    if (!klu_same_code(KLHT_DRAWTAG, klht_code, sizeof klht_code)) {
        klht_r.fault = 1; klog("tags: 0x7b8150 is not the tag drawer this build knows: no tags are drawn"); goto out;
    }
    for (i = 0; i < KLHT_NSLOT; i++) klht_r.s[i].ok = 0;
    for (i = 0; i < (int)cnt; i++) {
        DWORD E = pl + KLHT_E0 + (DWORD)i * KLHT_ESTRIDE; BYTE id = 0xff; struct klht_slot *q = &klht_r.s[i]; const struct klb_rec *r; int kind; DWORD col;
        if (!klh_rd(E, &id, 1) || id == 0xff || id >= KLB_NREC || (BYTE)i == local) continue;
        r = &s->r[id];
        if (!r->used || !(r->flags & 1)) continue;                       /* a bot: the stock reads [record + 4] for those (0x5e61a5 / 0x5e6189; 0x79 bit 1 = the record's AI byte) */
        kind = kluv_kind(s, id);
        q->show = kind == KLUV_K_CREW || kind == KLUV_K_TRAITOR || kind == KLUV_K_YOU;
        if (!q->made && !klht_make(q)) { klht_r.fault = 1; goto out; }
        if (!klnm_tag_ini(r->at, buf, sizeof buf)) { char nm[48]; DWORD blk, str = 0; nm[0] = 0; if ((blk = klh_rd32(r->at)) != 0 && klh_rd(blk + 8, &str, 4) && str) klh_rdstr(str, nm, sizeof nm); klnm_initials_one(nm, 0, buf, sizeof buf); }
        if (klht.mode == 2) klu_cash(mb, sizeof mb, (long)r->money); else mb[0] = 0;
        /* S2 (review): only the SCORE flag turns a world tag orange; the bot's own mark (flags&2) is set before he turns on anyone and the tag has no wall test */
        col = (kind == KLUV_K_TRAITOR && (kluv_flags(s, id) & KLUV_F_TRAITOR)) ? KLU_C_ORANGE : KLU_C_CHALK;
        if (strcmp(buf, q->ini_cur)) {
            int k;
            klu_set(q->ini, KLU_VT_TEXT, (DWORD)(DWORD_PTR)buf); if (q->inis) klu_set(q->inis, KLU_VT_TEXT, (DWORD)(DWORD_PTR)buf);
            for (k = 0; k < 4; k++) if (q->out[k]) klu_set(q->out[k], KLU_VT_TEXT, (DWORD)(DWORD_PTR)buf);      /* v23 (review MUST): the outline copies carry the same words */
            if (klu.log >= 2) klog("tags: entry %d (record %d at %08lx): initials '%s' -> '%s'%s", i, id, r->at, q->ini_cur, buf, kind == KLUV_K_TRAITOR ? " (traitor: orange)" : "");
            snprintf(q->ini_cur, sizeof q->ini_cur, "%s", buf);
        }
        if (col != q->ini_col) { klu_set(q->ini, KLU_VT_COLOUR, col); q->ini_col = col; }
        if (q->mon && strcmp(mb, q->mon_cur)) {
            klu_set(q->mon, KLU_VT_TEXT, (DWORD)(DWORD_PTR)mb); if (q->mons) klu_set(q->mons, KLU_VT_TEXT, (DWORD)(DWORD_PTR)mb);
            snprintf(q->mon_cur, sizeof q->mon_cur, "%s", mb);
        }
        q->id = id; q->actor = r->actor; q->ok = 1;
    }
    klht_r.pl = pl; klht_r.recs = recs; klht_r.n = (int)cnt; klht_r.active = 1;
    if (!klht_r.told) { klht_r.told = 1; klog("tags: on (HeadTags=%d): the stock element %08lx stays hidden; its tag loop is run by the hook with our texts (%d entries now)", klht.mode, pl, (int)cnt); }
    if (klu.log >= 2) {
        static DWORD said; DWORD now = GetTickCount();
        if (now - said >= 5000) { said = now; klog("tags: %ld tag draws, %ld without a node, %ld by the stock conditions, %ld with the drawer's flag clear, %d entries; peak draw instances after the tags %ld (budget: keep under ~320)", InterlockedExchange(&klht_n_draw, 0), InterlockedExchange(&klht_n_nonode, 0), InterlockedExchange(&klht_n_cond, 0), InterlockedExchange(&klht_n_flag, 0), (int)cnt, InterlockedExchange(&klht_n_peak, 0)); }
    }
out:
    LeaveCriticalSection(&klu_cs);
}

/* v22 HeadTab=1 (GUESS, default off until live check A1): a dark painted tab (picture 111, tint 0xb0101010) behind the initials. Where the
   drawer put the text is read back from OUR text object after the drawer ran: +0x3c / +0x40 = the stored position in virtual pixels
   (the same fields klhud.c's notes read on the stock timer's text, H1f / H1g) - only used when both lie on the 1280 x 720 screen;
   the text's top is assumed to be that y (baked header[9] = -cap: the capitals span y .. y + cap). */
static void klht_tab(void *el, void *ctx, const struct klht_slot *q)
{
    float p[2] = { 0, 0 }; float cap = klu_cap_of(klht.font), w, h; size_t n = strlen(q->ini_cur);
    if (!n || !klh_rd(q->ini + 0x3c, p, 8) || !(p[0] > 0 && p[0] < 1280.0f && p[1] > 0 && p[1] < 720.0f)) return;
    w = klht.tabpadx + (float)n * cap * 0.72f; h = cap + klht.tabpady;
    klu_pic(el, ctx, KLU_NPIC, 111, p[0] - w * 0.5f, p[1] - klht.tabpady * 0.5f + klht.tabdy, w, h, 0xb0101010u, KLHT_LAYER - 3);
    if (klu.log >= 2 && !klht.tabdone) { klht.tabdone = 1; klog("tags: tab: first tab at (%.0f, %.0f), %.0f x %.0f (the text object's +0x3c / +0x40 read as the place: A1 checks it)", p[0], p[1], w, h); }
}

/* THE RENDER SLOT (the clock element's Render, after the stock draw and ours; whichever thread renders): the first loop of 0x5e60f0.
   Reads the table the tick made; the element's entries are re-read here (an entry whose id changed since the tick is skipped). */
static void klht_render(void *el, void *ctx, void *cam)
{
    DWORD pl, recs; int i; BYTE tag[KLHT_TAGSIZE + 4];
    if (!klht.mode || !klht_r.active || !klu_draw_on || !klu_r.hid || !ctx || (DWORD)(DWORD_PTR)el != klu_r.elem) return;
    if (!TryEnterCriticalSection(&klu_cs)) return;
    pl = klht_r.pl; recs = klht_r.recs;
    if (klht_r.active && klh_rd32(pl) == KLU_PLIST_VT) {
        DWORD a1 = klh_rd32(pl + 0x10), a5 = klh_rd32(pl + 0xc); BYTE old = 0; DWORD cnt = 0;
        if (klh_rd(pl + KLHT_O_OLD, &old, 1) && klh_rd(pl + KLHT_O_COUNT, &cnt, 4) && cnt <= KLHT_NSLOT) {
            for (i = 0; i < (int)cnt && i < klht_r.n; i++) {
                const struct klht_slot *q = &klht_r.s[i]; DWORD E = pl + KLHT_E0 + (DWORD)i * KLHT_ESTRIDE, st10 = 0, st14 = 0, node = 0, rec; BYTE id = 0xff;
                if (!q->ok || !q->show || !klh_rd(E, &id, 1) || id != q->id) continue;
                if (!old && (!klh_rd(E + 0x10, &st10, 4) || !klh_rd(E + 0x14, &st14, 4))) continue;
                if (!(old || st10 == 1 || st10 == 4 || st14 == 5 || st14 == 6)) { InterlockedIncrement(&klht_n_cond); continue; }      /* 0x5e61df .. 0x5e6200 */
                rec = recs + 0x7c * (DWORD)id;
                if (!klh_rd(rec + 4, &node, 4) || !node || node != q->actor || !klh_rd32(node)) { InterlockedIncrement(&klht_n_nonode); continue; }
                if (!klh_rd(E + KLHT_TAGOFF, tag, KLHT_TAGSIZE)) continue;
                if (!tag[0x40]) { InterlockedIncrement(&klht_n_flag); continue; }                                              /* the drawer's own first test (0x7b8156) */
                {
                    DWORD o[8]; int k, n = 0;
                    for (k = 0; k < 4; k++) if (q->out[k]) o[n++] = q->out[k];
                    if (q->inis) o[n++] = q->inis;
                    o[n++] = q->ini;
                    if (q->mons) o[n++] = q->mons;
                    if (q->mon) o[n++] = q->mon;
                    if (klht.tab) { float z[2] = { 0, 0 }; memcpy((void *)(DWORD_PTR)(q->ini + 0x3c), z, 8); }       /* v23 (review SHOULD): a skipped draw leaves 0, not the last tag's place */
                    for (k = 0; k < n; k++) {
                        *(DWORD *)tag = o[k];                                                                                /* the copy's text object = ours; the copy absorbs anything the drawer writes */
                        ((klht_drawtag_t)(DWORD_PTR)KLH_VA(KLHT_DRAWTAG))(tag, 0, a1, node, ctx, cam, a5);
                        if (o[k] == q->ini || o[k] == q->mon) InterlockedIncrement(&klht_n_draw);
                    }
                    if (klht.tab && klu_r.handle[111]) klht_tab(el, ctx, q);
                }
            }
        }
    }
    {   /* S1 (review): the peak of draw instances AFTER the tags (DrawChunk has no capacity test); ctx[1] is the count the render slot reads */
        DWORD c = 0; if (klh_rd(((DWORD)(DWORD_PTR)ctx) + 4, &c, 4) && (LONG)c > klu_n_maxinst) InterlockedExchange(&klu_n_maxinst, (LONG)c);
        if (c > (DWORD)klht_n_peak) InterlockedExchange(&klht_n_peak, (LONG)c);
    }
    LeaveCriticalSection(&klu_cs);
}

static void klht_init(void)
{
    klht.mode = klu_inii("HeadTags", klu.draft, 0, 2);
    klht.shadow = klu_inii("HeadShadow", 1, 0, 1);
    klht.outline = klu_inii("HeadOutline", 1, 0, 1);               /* v22 (audit T1): four dark copies round the initials; replaces the single shadow of the initials */
    klht.font = klu_inii("HeadFont", 1, 0, 3);                     /* v22: 0 the names' face (cap 11), 1 the big face (cap 15, the draft's total) - 'a step larger' */
    klht.tab = klu_inii("HeadTab", 0, 0, 1);                       /* v22 GUESS: a dark painted tab behind the letters; off until A1 has shown the place it reads */
    klht.tabpadx = klu_inif("HeadTabPadX", "8"); klht.tabpady = klu_inif("HeadTabPadY", "6"); klht.tabdy = klu_inif("HeadTabDY", "0");
    klht.line = klu_inif("HeadLine", "-1"); if (!(klht.line >= 4 && klht.line <= 60)) klht.line = klu_cap_of(klht.font) + 5.0f;
    if (klht.mode) klog("tags: HeadTags=%d (1 initials, 2 initials + money) HeadShadow=%d HeadLine=%.0f; needs [HUD] HideStock=1 (the stock tags go with the hidden element); NOT RUN IN THE GAME", klht.mode, klht.shadow, klht.line);
}


#endif /* KLHUD_TAGS_C */
