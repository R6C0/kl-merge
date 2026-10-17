/*
 * klgun.c - switchable looks of guns: a Dead Men gun's model on a Dog Days gun. Part of KLHook (included by klhook.c
 * after klmem.c and before klchar.c, SHIP and TEST alike). Heap data writes only (one byte per gun part, in the
 * loaded level's .prm block); no code byte, no import slot, no game call.
 * Data side and the reasons: tools\kl_map_guns.py and re\map_guns.md. NOT RUN IN THE GAME (2026-10-10); run outside
 * the game against a real build's .prm and KLGuns.ini by a test program (the lead has its place and its output).
 *
 * 1. THE DATA
 *    A level built by kl_map_guns.py has, for some guns, a model whose object table is
 *        [the stock parts][the parts of look 1][the parts of look 2] ...
 *    every part a mesh object of the .prm (a 64-byte chunk: word +2 = 8; here always a rigid one-bone part: byte
 *    +0x0c = 2, dword +0x38 = 1), no part named by another model. KLGuns.ini beside the level archive (Version=2;
 *    HideWord=28, HideBit=8388608, Entries=<the chunk count of THIS build's .prm, its dword +4>) lists per gun:
 *    Item (eFF2Item number), Root (the model's chunk index in THIS build's .prm), Stock (number of stock parts),
 *    Looks, Look<n>Parts, Shown (the group the build was baked to show: only reported here).
 *    Entries ties the file to its build (re\hook_review_1010.md G1): a Root index is only a number, and a KLGuns.ini
 *    left beside the archive of a NEWER build could name another rigid model with the same number of objects (two
 *    guns of one build are the obvious case), whose parts would then be hidden. A Version 2 file WITHOUT Entries
 *    (every build made before 2026-10-10) is refused with one log line, and a file whose Entries is not the loaded
 *    .prm's count is left alone and said once, when the round runs. Until the folder is built again with
 *    tools\kl_map_guns.py (or the line is added: `kl_map_guns.py check <folder>` prints it) the level shows what
 *    was baked.
 *
 * 2. WHAT HIDES A PART (kl2.exe, read again for this file 2026-10-10 with debug\dasm.py)
 *        0x67cf68  mov  ebp, [eax*4 + 0xeac7b0]       the mesh object, out of the chunk table
 *        0x67cf77  test dword [ebp+0x1c], 0x800000    the HIDE bit
 *        0x67cf7e  jne  -> next object
 *        0x67cf84  mov  al, [ebx+0x158]               the entity's variant
 *        0x67cf8a  test al, al ; je -> take           variant 0 takes EVERY object
 *        0x67cf8e  cmp  byte [ebp+0xf], al ; jne -> next
 *    in 0x67cc60 = slot 3 of ZRenderEntryBones / ..Rigid / ..D3D / ..RigidD3D (debug\rtti.py), which starts by taking
 *    the model root from the table and testing `cmp word [root+2], 7` (0x67cca3). The same test of the bit at
 *    0x57ee43 (0x57ed50 = slot 1 of ZRenderEntryGeom and nine relatives), 0x7581e1 and 0x7af091 (there followed by
 *    `cmp word [object+2], 8`, 0x7af09e): a byte search of .text finds these four `test dword [reg+0x1c], 0x800000`
 *    and no instruction that sets or clears exactly that bit with an immediate (or / and on [reg+0x1c] or on
 *    byte [reg+0x1e]). A gun entity's variant is 0, so a variant byte hides nothing on a gun: that was Version 1 of
 *    the file and of this hook, and it could not work. A Version 1 file is refused with one log line.
 *
 * 3. WHERE THE LOADED CHUNKS ARE (0x8007f0 = ZRenderWintelD3DDll slot 28; 0x496d80 the same for the other renderer;
 *    a THIRD loader, 0x45f260, sets [0xeac7a0] at 0x45f2ab and clears it at 0x45f52a - re\hook_review_1010.md; the
 *    `loading != 0 -> return` of the tick covers all three. One more reader of the table: 0x69ad38)
 *        [0xeac7a0] = file + [file+0]                 the file's own table, 16 bytes a chunk: offset, size, refcount, 0
 *        memset(0xeac7b0, 0, 0x48000)                 the pointer table, 0x12000 slots
 *        [0xeac7a4] = [0xeac7a8] = [file+4]           the file's chunk count
 *        for i < count: if refcount[i]: table[i] = file + offset[i]
 *        [0xeac7a0] = 0 ; table[0] = 0
 *    So [0xeac7a0] != 0 means 'a loader is filling the table now', and a table that has the gun's root while
 *    [0xeac7a0] is 0 is FILLED. The file was read into one block of file size + 0x60000 (0x82049b), from the heap
 *    or from klmem.c's reserve.
 *
 * 4. WHAT THE HOOK DOES
 *    Every tick (once a frame on the main loop; every 100 ms from KLHook's own thread while the main loop stands
 *    still, which is the case during a level load) it reads three dwords: [0xeac7a0], [0xeac7a4] and the table
 *    entry of the first gun's root. Nothing more happens until a full pass is due: the level's archive was opened
 *    (klg_level_open; seen in KLHook.log: five opens per load, the first 1.4 s before the .prm block is asked for),
 *    one of the two options changed, the three dwords changed, or 64 ticks went by (a level loaded again into the
 *    same address with the same count looks the same in those three dwords: the .prm block was at 04300000 in two
 *    loads running, KLHook.log 12:49:14 and 12:49:32).
 *    A full pass, for every gun of the file, while the session's game mode is Arcade ([[0x168e598]+0x5c] == 4; it
 *    is 4 before the archive is opened: 'session: state 0x0 -> 0x12 (game mode 4)' precedes the open in the log):
 *      a. the BLOCK that holds the first gun's root chunk, once per pass: the block of klmem.c's reserve it lies in,
 *         else the run of committed pages around it inside its VirtualAlloc allocation (ASSUMPTION: a heap block
 *         of this size is an allocation of its own - the NT heap gives every request over about 508 KB one, on
 *         this Windows with some reserved pages in front; a block under 8 MB is refused as 'not a level's
 *         .prm'). Looked for in the block's first 256 bytes: the file's header (dword +4 = [0xeac7a4], and the
 *         file's table entry of the root gives the very pointer the chunk table holds). If it is there the bounds
 *         are the FILE's (header .. end of its table) and every part's entry must say 64 bytes and the pointer the
 *         chunk table holds; if not (NOT KNOWN whether the game keeps the file's table intact after the load) the
 *         block's bounds are used and the log says so.
 *      b. root: inside the bounds, word +2 = 7, object count +0x14 = Stock + all Look<n>Parts, object table chunk
 *         +0x18 inside the bounds; every part: index below the count, pointer not 0, the 64 bytes inside the bounds,
 *         word +2 = 8, byte +0x0c = 2, dword +0x38 = 1. A pointer that is still 0 = not loaded yet: tried again
 *         next tick. Anything else wrong: the gun is left alone, said once per load after it has stayed wrong for
 *         3 s, and tried again at every later full pass - no part of a gun is written unless ALL its parts pass.
 *      c. for every part: the bit must be CLEAR in the wanted group and SET in every other; a part that differs
 *         gets the ONE byte +0x1e of its object written (bit 0x80 flipped, the other seven bits as just read).
 *         The write is klg_poke: klh_may_write (the patch guard), the page must be committed and writable as it
 *         stands, then WriteProcessMemory on our own process, which cannot fault if the game frees the block at
 *         that moment (the pass can run on KLHook's thread).
 *    One line when a pass wrote something or answered a new load / option:
 *        guns: level f01\f01_main has 6 guns, 7 looks; shown Rifle_zastavam85=AK-74, Rifle_FN_SCAR=SG 552, ...
 *    It is a change of the MODEL: everyone who carries that gun in the level shows the look - the player, the AI
 *    heisters, the police, a gun on the floor. And it is local: another machine shows what its own setting says.
 *    Outside Arcade, with [Guns] Enable not 1, or with no usable KLGuns.ini the level shows what was baked.
 *
 * 5. WHICH LOOK (unchanged from Version 1; the window KLGuns of the overlay, mkoverlay.py GUN_ROWS)
 *      KLGunStart  0..2   the starting rifle (item 29, Zastava): 0 stock, 1 = its look 1 (MP5), 2 = its look 2 (AK-74)
 *      KLGunSet    0..1   every other gun of the file: 0 stock, 1 = its look 1 (the Dead Men look)
 *    Two menu options answered through klchar.c's private vtable on the option object: klchar.c asks klg_which()
 *    for the names it does not know itself. Kept in KLHook.ini [Guns] Start / Set.
 *
 * 6. NOT KNOWN (live checks: re\map_guns.md G6, and the list the lead has from this file's author)
 *    - Whether a gun that already exists re-reads the bit. 0x67cc60 is a method of the render ENTRY (one per drawn
 *      entity), with a 0x8154-byte stack frame of work lists: it may run every frame or only when the entry is
 *      (re)built - 0x88c810, the look change of a person, notifies the renderer after storing the variant, which
 *      points at 'kept per entry'. If kept, a switch during a round shows on guns created after it only. That is
 *      why the first pass comes as soon as the table is filled and not at the first frame of the round.
 *    - Whether anything of the game writes the other bits of byte +0x1e of a gun part while a pass runs on KLHook's
 *      thread (read, then write of one byte: not atomic). No such write was looked for beyond the bit itself.
 *    - Whether the scene's guns exist before the table is filled (they cannot: an entity's model is a chunk index).
 *    - Whether the three other places that test the bit (0x57ee43, 0x7581e1, 0x7af091) count objects in one pass
 *      and fill in another, which a flip between the two passes could overrun: NOT read (0x67cc60 takes one object
 *      at a time, no such pair there).
 *    DEPENDENCY (review G4): klg_level_open is reached only through klsteam.c's klh_level_open, which does nothing
 *    when the Steam write guard is not installed. Without the guard the looks never switch; the tick says so once.
 *
 * KLHook.ini
 *   [Guns]
 *   Enable=1      anything else, or no key: this file does nothing (the two options read 0 and are dropped, as in stock)
 *   Start=0
 *   Set=0
 *   Log=1
 */
#ifndef KLGUN_C
#define KLGUN_C

#define KLG_TABLE      0x00eac7b0             /* chunk index -> pointer, 0x12000 slots */
#define KLG_SLOTS      0x12000
#define KLG_COUNT      0x00eac7a4             /* the loaded file's chunk count */
#define KLG_LOADING    0x00eac7a0             /* the file's own table while a loader fills ours, else 0 */
#define KLG_SESSION    0x0168e598             /* +0x5c = game mode, 4 = Arcade (klchar.c, klsteam.c) */
#define KLG_HIDEWORD   0x1c                   /* the one pair this file knows: KLGuns.ini must say the same */
#define KLG_HIDEBIT    0x00800000
#define KLG_NGUN       16
#define KLG_NLOOK      4
#define KLG_NPART      96
#define KLG_START_ITEM 29                     /* eFF2ItemRifle_Zastavam85 */
#define KLG_MINBLOCK   (8u << 20)             /* ASSUMPTION: no level .prm with gun looks is smaller (they are 50 - 80 MB) */

static int klx_on;                                    /* klsteam.c (included later): the guard that tells us of archive opens is installed */
static int klg_on, klg_log = 1;
static volatile LONG klg_start, klg_set, klg_dirty;   /* dirty: a full pass is owed (archive opened, option changed) */
static CRITICAL_SECTION klg_cs;                       /* klg_f; taken before klmem.c's klm_cs, never after it */
static struct {
    int on, n, nlooks, stale_told; DWORD entries;       /* entries: the chunk count of the .prm the file was written for */
    struct { DWORD root, since; int item, stock, looks, parts[KLG_NLOOK], built, shown, told; char tpl[40], label[KLG_NLOOK][24]; } g[KLG_NGUN];
    char key[64], file[MAX_PATH];
} klg_f;
static struct { DWORD loading, count, root0; LONG start, set; } klg_done;      /* what the last complete pass saw */
static int klg_told_header;
/* THE LOOK'S NAME per item, for the HUD dial (klhud_weapon.c, [HUD] LookNames=1; worker 'shop' 2026-10-15). The shop sells the
   looks under their own names since tools\kl_hud_shop.py read KLGuns.ini (MP5, SG 552 ...); the dial said ZASTAVA M85 for the gun
   that looks and is sold as an MP5. Two buffers of 64 items x 24 bytes: klg_publish (under klg_cs) fills the one not in use, then
   switches klg_lk_cur; the render thread reads klg_lk[klg_lk_cur] without a lock. '' = no look: the dial keeps its own name.
   Which look: the one the last pass wrote (shown), else the one the build was baked to show (KLGuns.ini Shown) - what is on the
   screen in both cases. With [Guns] off the file is still read for the names when LookNames is on (klg_lknames), nothing is
   written to the level then: the build shows its baked look and the dial names it. */
#define KLG_NITEM 64                          /* eFF2ItemCount (tools\kl_guns.py) */
static char klg_lk[2][KLG_NITEM][24];
static volatile LONG klg_lk_cur;
static int klg_lknames;                         /* set by klhud_weapon.c's klwd_init: [HUD] LookNames=1 */
static void klg_publish(void)                 /* klg_cs held */
{
    int nx = !klg_lk_cur, i, w, c; char *d; const char *src;
    memset(klg_lk[nx], 0, sizeof klg_lk[nx]);
    for (i = 0; klg_f.on && i < klg_f.n; i++) {
        w = klg_f.g[i].shown >= 0 ? klg_f.g[i].shown : klg_f.g[i].built;
        if (w < 1 || w > klg_f.g[i].looks || klg_f.g[i].item < 0 || klg_f.g[i].item >= KLG_NITEM) continue;
        for (src = klg_f.g[i].label[w - 1], d = klg_lk[nx][klg_f.g[i].item], c = 0; *src && c < 23; src++, c++)
            d[c] = (char)(*src >= 'a' && *src <= 'z' ? *src - 32 : *src);     /* the dial's capitals: 'Steyr TMP' -> 'STEYR TMP' */
        d[c] = 0;
        if (!strcmp(d, "?")) d[0] = 0;
    }
    InterlockedExchange(&klg_lk_cur, nx);
}
/* the look's name of an item for the dial, or 0 (any thread, no lock) */
static const char *klg_look_name(int item)
{
    const char *n;
    if (!klg_lknames || item < 0 || item >= KLG_NITEM) return 0;
    n = klg_lk[klg_lk_cur & 1][item];
    return n[0] ? n : 0;
}

static const char *const klg_names[2] = { "KLGunStart", "KLGunSet" };
static const int klg_upper[2] = { 2, 1 };     /* mkoverlay.py GUN_ROWS has as many entries + 1 */
static volatile LONG *const klg_value[2] = { &klg_start, &klg_set };
static const char *const klg_keys[2] = { "Start", "Set" };

/* ---------------------------------------------------------------- the two options (called by klchar.c) */

static int klg_which(const char *name)
{   /* -> 0 / 1 for our two option names, -1 for anything else (or unreadable) */
    char n[12]; int i;
    if (!klg_on || !name || !klh_rd((DWORD_PTR)name, n, 5) || memcmp(n, "KLGun", 5)) return -1;
    if (!klh_rdstr((DWORD_PTR)name, n, sizeof n)) return -1;
    for (i = 0; i < 2; i++) if (!strcmp(n, klg_names[i])) return i;
    return -1;
}

static int klg_get(int i) { return (int)*klg_value[i]; }

static void klg_put(int i, int value)
{
    char v[16];
    if (value < 0) value = 0;
    if (value > klg_upper[i]) value = klg_upper[i];
    if (InterlockedExchange(klg_value[i], value) != value) {
        snprintf(v, sizeof v, "%d", value); WritePrivateProfileStringA("Guns", klg_keys[i], v, klh_ini);
        if (klg_log) klog("guns: menu set %s = %d", klg_names[i], value);
        InterlockedExchange(&klg_dirty, 1);
    }
}

/* ---------------------------------------------------------------- KLGuns.ini of the level */

/* From klsteam.c's klh_level_open: the game opens the level archive <key> ("f01\f01_main.zip") from <opened>.
   Called several times per load and from whatever thread opens the file: reads the ini, nothing of the game. */
static void klg_level_open(const char *key, const char *opened)
{
    static char lastkey[64], lastfile[MAX_PATH]; static int lastver = -2; static DWORD lastent;
    char file[MAX_PATH], sec[16], k[24], kk[64], *s; int i = 0, j, n, ver, word, bit, fresh; DWORD len, ent;
    if (!klg_on && !klg_lknames) return;               /* LookNames alone: the file is read for its names, nothing is written */
    len = GetFullPathNameA(opened, MAX_PATH, file, 0);
    if (!len || len >= MAX_PATH || !(s = strrchr(file, 0x5c)) || (size_t)(s - file) + 12 >= sizeof file) return;
    strcpy(s + 1, "KLGuns.ini");
    snprintf(kk, sizeof kk, "%s", key); if ((s = strrchr(kk, '.')) != 0) *s = 0;
    ver = (int)GetPrivateProfileIntA("Guns", "Version", 0, file);
    n = (int)GetPrivateProfileIntA("Guns", "Count", 0, file);
    word = (int)GetPrivateProfileIntA("Guns", "HideWord", -1, file);
    bit = (int)GetPrivateProfileIntA("Guns", "HideBit", 0, file);
    ent = GetPrivateProfileIntA("Guns", "Entries", 0, file);      /* 0 = no key: a Version 2 file of before 2026-10-10 */
    if (ent > KLG_SLOTS) ent = 0;
    EnterCriticalSection(&klg_cs);
    fresh = strcmp(lastkey, kk) || lastver != ver || lastent != ent || _stricmp(lastfile, file);      /* the lines below: once per level and file, not per open (a REFUSED file too) */
    strcpy(lastkey, kk); strcpy(lastfile, file); lastver = ver; lastent = ent;
    memset(&klg_f, 0, sizeof klg_f);
    strcpy(klg_f.key, kk);
    if (ver == 2 && ent && n > 0 && n <= KLG_NGUN && word == KLG_HIDEWORD && (DWORD)bit == KLG_HIDEBIT) {
        klg_f.entries = ent;
        for (i = 0; i < n; i++) {
            snprintf(sec, sizeof sec, "Gun.%d", i + 1);
            klg_f.g[i].root = GetPrivateProfileIntA(sec, "Root", 0, file);
            klg_f.g[i].item = (int)GetPrivateProfileIntA(sec, "Item", 0, file);
            klg_f.g[i].stock = (int)GetPrivateProfileIntA(sec, "Stock", 0, file);
            klg_f.g[i].looks = (int)GetPrivateProfileIntA(sec, "Looks", 0, file);
            klg_f.g[i].built = (int)GetPrivateProfileIntA(sec, "Shown", -1, file);
            klg_f.g[i].shown = -1;
            GetPrivateProfileStringA(sec, "Template", "?", klg_f.g[i].tpl, sizeof klg_f.g[i].tpl, file);
            if (!klg_f.g[i].root || klg_f.g[i].root >= KLG_SLOTS || klg_f.g[i].stock < 1 || klg_f.g[i].stock > KLG_NPART || klg_f.g[i].looks < 1 || klg_f.g[i].looks > KLG_NLOOK) break;
            for (j = 0; j < klg_f.g[i].looks; j++) {
                snprintf(k, sizeof k, "Look%dParts", j + 1); klg_f.g[i].parts[j] = (int)GetPrivateProfileIntA(sec, k, 0, file);
                snprintf(k, sizeof k, "Look%d", j + 1); GetPrivateProfileStringA(sec, k, "?", klg_f.g[i].label[j], sizeof klg_f.g[i].label[j], file);
                if (klg_f.g[i].parts[j] < 1 || klg_f.g[i].parts[j] > KLG_NPART) break;
            }
            if (j < klg_f.g[i].looks) break;
            klg_f.nlooks += klg_f.g[i].looks;
        }
        if (i == n) { klg_f.on = 1; klg_f.n = n; strcpy(klg_f.file, file); }
    }
    memset(&klg_done, 0, sizeof klg_done);
    klg_publish();                                   /* the baked looks' names now; a pass replaces them with what it wrote */
    LeaveCriticalSection(&klg_cs);
    InterlockedExchange(&klg_dirty, 1);
    if (fresh && klg_lknames && klg_f.on) {
        char line[200], *p = line; int g;
        for (g = 0, line[0] = 0; g < klg_f.n && p < line + sizeof line - 40; g++) {
            const char *nm = klg_look_name(klg_f.g[g].item);
            if (nm) p += snprintf(p, 40, "%s%d=%s", p == line ? "" : ", ", klg_f.g[g].item, nm);
        }
        klog("guns: names for the HUD dial (LookNames=1), item=name: %s", line[0] ? line : "none (no gun of the file shows a look)");
    }
    if (!klg_on) return;                             /* guns off: the names only, the lines below belong to the switch */
    if (!fresh) return;
    if (klg_f.on) { if (klg_log) klog("guns: level %s has %d gun(s) with %d look(s) (%s, Version 2: hide bit, for a .prm of %lu chunks)", klg_f.key, klg_f.n, klg_f.nlooks, file, klg_f.entries); }
    else if (ver == 1) klog("guns: %s is Version 1 (looks hidden by a variant byte, which hides nothing on a gun: kl2 0x67cf84): refused, this level shows what its file holds - build it with tools\\kl_map_guns.py", file);
    else if (ver == 2 && !ent) klog("guns: %s has no usable Entries= (the chunk count of the .prm it was written for; 1..%d): it cannot be told from a file left over from another build, so it is REFUSED and the level shows what was built in - build the folder again with tools\\kl_map_guns.py, or add the line that `kl_map_guns.py check <folder>` prints", file, KLG_SLOTS);
    else if (ver == 2) klog("guns: %s is not usable (Count=%d, entry %d, HideWord=%d, HideBit=%d; this hook knows 28 / 8388608): the level shows what was built in", file, n, i + 1, word, bit);
    else if (ver) klog("guns: %s has Version=%d, this hook reads 2: the level shows what was built in", file, ver);
}

/* ---------------------------------------------------------------- the loaded .prm */

/* The block of memory address p lies in: a block of klmem.c's reserve, else the run of committed pages around it
   inside its VirtualAlloc allocation (a large heap block is an allocation of its own; Windows may leave some
   reserved pages in front of it, so the run and not the allocation's base is the start). */
static int klg_block(DWORD p, DWORD *lo, DWORD *hi)
{
    MEMORY_BASIC_INFORMATION mbi; BYTE *base, *at, *run = 0; int i, found = 0;
    if (klm_inside((LPCVOID)(DWORD_PTR)p)) {
        SIZE_T off = (SIZE_T)((BYTE *)(DWORD_PTR)p - (BYTE *)klm_reserve);
        EnterCriticalSection(&klm_cs);
        for (i = 0; i < klm_n; i++) if (off >= klm_blk[i].off && off < klm_blk[i].off + klm_blk[i].asked) {
            *lo = (DWORD)(DWORD_PTR)((BYTE *)klm_reserve + klm_blk[i].off); *hi = *lo + (DWORD)klm_blk[i].asked; found = 1;
        }
        LeaveCriticalSection(&klm_cs);
        return found;
    }
    if (!VirtualQuery((LPCVOID)(DWORD_PTR)p, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT || mbi.Type != MEM_PRIVATE || !mbi.AllocationBase) return 0;
    base = at = (BYTE *)mbi.AllocationBase;
    while (VirtualQuery(at, &mbi, sizeof mbi) && mbi.AllocationBase == (PVOID)base && mbi.RegionSize && at + mbi.RegionSize > at) {
        if (mbi.State == MEM_COMMIT) { if (!run) run = at; }
        else if (run && (DWORD_PTR)at > p) break;      /* the run that holds p has ended */
        else run = 0;
        at += mbi.RegionSize;
    }
    if (!run || (DWORD_PTR)run > p || (DWORD_PTR)at <= p) return 0;
    *lo = (DWORD)(DWORD_PTR)run; *hi = (DWORD)(DWORD_PTR)at;
    return 1;
}

/* The loaded file around the chunk `ptr` of index `root`: -> 2 = its header and table were found (lo = the file,
   hi = the end of its table, *table = the table), 1 = only the block (lo .. hi), 0 = no block a level's .prm
   could be. */
static int klg_file(DWORD count, DWORD root, DWORD ptr, DWORD *lo, DWORD *hi, DWORD *table)
{
    DWORD blo, bhi, b, h[4], e[4];
    *table = 0;
    if (!klg_block(ptr, &blo, &bhi) || bhi - blo < KLG_MINBLOCK) return 0;
    *lo = blo; *hi = bhi;
    for (b = blo; b < blo + 0x100; b += 8) {          /* a heap block starts a few bytes into its first page */
        if (!klh_rd(b, h, sizeof h) || h[1] != count || h[0] != h[2] || h[3] || h[0] < 16 || h[0] >= bhi - b || (bhi - b - h[0]) / 16 < count) continue;
        if (!klh_rd(b + h[0] + 16 * root, e, sizeof e) || !e[2] || e[0] >= h[0] || b + e[0] != ptr) continue;
        *lo = b; *hi = b + h[0] + 16 * count; *table = b + h[0];
        return 2;
    }
    return 1;
}

/* One byte of the game's heap data: the patch guard, a page that is committed and writable as it stands, and a
   write that cannot fault (klh_data's memcpy could, if the game freed the block between the test and the copy). */
static int klg_poke(DWORD at, BYTE v)
{
    MEMORY_BASIC_INFORMATION mbi; SIZE_T done = 0;
    if (!klh_may_write((void *)(DWORD_PTR)at, 1, "gun part hide bit")) return 0;
    if (!VirtualQuery((void *)(DWORD_PTR)at, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT || mbi.Type != MEM_PRIVATE ||
        !(mbi.Protect & PAGE_READWRITE) || (mbi.Protect & PAGE_GUARD)) return 0;
    return WriteProcessMemory(GetCurrentProcess(), (void *)(DWORD_PTR)at, &v, 1, &done) && done == 1;
}

/* Group `want` of gun gi shown, the others hidden. Reads and checks everything before the first write.
   k, lo, hi, ftab: klg_file's answer for this pass (the bounds every address is held against).
   -> 1 done (*wrote = bytes written), 0 the level's file is not in (yet), -1 this is not the model the file describes. */
static int klg_apply(int gi, int want, DWORD count, int k, DWORD lo, DWORD hi, DWORD ftab, int *wrote)
{
    DWORD root, tabc, tab, n, objs[KLG_NPART], idx[KLG_NPART], e[4], word, now = GetTickCount();
    BYTE head[0x20], oh[0x40]; int total, i, j, g, changed = 0, failed = 0; const char *why = 0;
    *wrote = 0;
    total = klg_f.g[gi].stock; for (j = 0; j < klg_f.g[gi].looks; j++) total += klg_f.g[gi].parts[j];
    if (total > KLG_NPART) why = "more than 96 parts";
    else if (klg_f.g[gi].root >= count) return 0;                                   /* another file is loaded (the menu's) */
    else if (!(root = klh_rd32((DWORD_PTR)KLH_VA(KLG_TABLE + 4 * klg_f.g[gi].root)))) return 0;
    else if (!k) why = "the chunk table points into no block a level's .prm could be";
    else if (root < lo || root > hi - sizeof head || !klh_rd(root, head, sizeof head)) why = "the model root is outside the .prm block";
    else if (head[2] != 7 || head[3] != 0) why = "the chunk is not a model root";
    else if ((n = *(DWORD *)(head + 0x14)) != (DWORD)total) why = "the model does not have the parts the file lists";
    else if ((tabc = *(DWORD *)(head + 0x18)) >= count || !(tab = klh_rd32((DWORD_PTR)KLH_VA(KLG_TABLE + 4 * tabc)))) return 0;
    else if (tab < lo || tab > hi - 4 * n || !klh_rd(tab, idx, 4 * n)) why = "the object table is outside the .prm block";
    if (!why) for (i = 0; i < total; i++) {
        if (idx[i] >= count) { why = "a part's chunk index is past the file's count"; break; }
        if (!(objs[i] = klh_rd32((DWORD_PTR)KLH_VA(KLG_TABLE + 4 * idx[i])))) return 0;                 /* not filled in yet */
        if (objs[i] < lo || objs[i] > hi - sizeof oh || !klh_rd(objs[i], oh, sizeof oh)) { why = "a part is outside the .prm block"; break; }
        if (oh[2] != 8 || oh[3] != 0 || oh[0x0c] != 2 || *(DWORD *)(oh + 0x38) != 1) { why = "a part is not a rigid mesh object"; break; }
        if (k == 2 && (!klh_rd(ftab + 16 * idx[i], e, sizeof e) || e[1] != sizeof oh || lo + e[0] != objs[i])) { why = "a part is not the 64-byte chunk the file's table names"; break; }
        for (j = 0; j < i; j++) if (objs[j] == objs[i]) break;
        if (j < i) { why = "a part is listed twice"; break; }
    }
    if (why) {
        if (!klg_f.g[gi].since) klg_f.g[gi].since = now | 1;
        else if (!klg_f.g[gi].told && now - klg_f.g[gi].since >= 3000) {
            klg_f.g[gi].told = 1;
            klog("guns: %s (model %lu) left alone on this level: %s", klg_f.g[gi].tpl, klg_f.g[gi].root, why);
        }
        return -1;
    }
    klg_f.g[gi].since = 0;
    for (i = 0, g = 0, j = klg_f.g[gi].stock; i < total; i++) {
        BYTE b;
        while (i >= j) j += klg_f.g[gi].parts[g++];           /* g = the group object i belongs to: 0 stock, n look n */
        if (!klh_rd(objs[i] + KLG_HIDEWORD, &word, 4)) { failed++; continue; }
        if (((word & KLG_HIDEBIT) == 0) == (g == want)) continue;       /* as it must be */
        b = (BYTE)(((word ^ KLG_HIDEBIT) >> 16) & 0xff);
        if (klg_poke(objs[i] + KLG_HIDEWORD + 2, b)) changed++; else failed++;
    }
    if (failed) klog("guns: %s: %d part(s) of model %lu COULD NOT BE WRITTEN (%d written): the gun may show parts of two looks", klg_f.g[gi].tpl, failed, klg_f.g[gi].root, changed);
    klg_f.g[gi].shown = want; *wrote = changed;
    return 1;
}

static void klg_tick(void)
{
    static DWORD calls; DWORD loading = 1, count = 0, root0 = 0, sm, lo = 0, hi = 0, ftab = 0; LONG start, set, dirty;
    int i, r, w, want, wrote = 0, waiting = 0, done = 0, k; char line[400], *p;
    if (!klg_on || !klh_exe_ok) return;
    if (!klx_on) {                                    /* review G4: nobody tells us which archive is opened */
        static int told;
        if (!told++) klog("guns: the Steam write guard is not installed, and only it reports the level archive being opened: no KLGuns.ini is read, every level shows what was built in");
        return;
    }
    if (!klg_f.on) return;
    calls++;
    if (!klh_rd((DWORD_PTR)KLH_VA(KLG_LOADING), &loading, 4) || loading) return;        /* a loader is filling the table */
    if (!klh_rd((DWORD_PTR)KLH_VA(KLG_COUNT), &count, 4) || count > KLG_SLOTS) return;
    start = klg_start; set = klg_set;
    EnterCriticalSection(&klg_cs);
    if (!klg_f.on) { LeaveCriticalSection(&klg_cs); return; }
    if (klg_f.entries != count) {                     /* G1: not the .prm this file was written for - the menu's, or ANOTHER BUILD's */
        DWORD st = 0;
        if (!klg_f.stale_told && count && (sm = klh_rd32((DWORD_PTR)KLH_VA(KLG_SESSION))) != 0 && klh_rd32(sm + 0x5c) == 4 && klh_rd(sm + 0x70, &st, 4) && st == 0x19) {
            klg_f.stale_told = 1;                     /* said when the round runs: the .prm in the table is the level's then */
            klog("guns: %s was written for a .prm of %lu chunks, the level's has %lu: the file belongs to another build (left over beside a newer archive?) - nothing is written, level %s shows what was built in", klg_f.file, klg_f.entries, count, klg_f.key);
        }
        LeaveCriticalSection(&klg_cs); return;
    }
    if (klg_f.g[0].root >= count || !(root0 = klh_rd32((DWORD_PTR)KLH_VA(KLG_TABLE + 4 * klg_f.g[0].root)))) { LeaveCriticalSection(&klg_cs); return; }      /* not filled in */
    dirty = klg_dirty;
    if (!dirty && (calls & 63) && klg_done.count == count && klg_done.root0 == root0 && klg_done.start == start && klg_done.set == set) { LeaveCriticalSection(&klg_cs); return; }
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLG_SESSION))) || klh_rd32(sm + 0x5c) != 4) { LeaveCriticalSection(&klg_cs); return; }       /* Arcade only */
    if (kl_online()) { LeaveCriticalSection(&klg_cs); return; }                                               /* [Net] OnlineSafe: no variant-byte write in a network session */
    InterlockedExchange(&klg_dirty, 0);
    k = klg_file(count, klg_f.g[0].root, root0, &lo, &hi, &ftab);
    for (i = 0; i < klg_f.n; i++) {
        want = klg_f.g[i].item == KLG_START_ITEM ? (int)start : (set ? 1 : 0);
        if (want > klg_f.g[i].looks) want = 0;
        r = klg_apply(i, want, count, k, lo, hi, ftab, &w);
        if (r > 0) { done++; wrote += w; } else if (!r) waiting++;
    }
    if (waiting) InterlockedExchange(&klg_dirty, 1);          /* a pointer was still 0: again next tick */
    else { klg_done.count = count; klg_done.root0 = root0; klg_done.start = start; klg_done.set = set; }
    if (done) klg_publish();                                  /* the dial names what this pass shows */
    if (done && (wrote || dirty) && !waiting && klg_log) {
        for (i = 0, p = line; i < klg_f.n && p < line + sizeof line - 72; i++)
            if (klg_f.g[i].shown >= 0 && klg_f.g[i].since == 0)
                p += snprintf(p, 72, "%s%s=%s", p == line ? "" : ", ", klg_f.g[i].tpl, klg_f.g[i].shown ? klg_f.g[i].label[klg_f.g[i].shown - 1] : "its own");
        *p = 0;
        klog("guns: level %s has %d guns, %d looks; shown %s (KLGunStart=%ld KLGunSet=%ld; %d of %d guns done, %d part byte(s) written; .prm %s %08lx..%08lx, %lu chunks)",
             klg_f.key, klg_f.n, klg_f.nlooks, line, start, set, done, klg_f.n, wrote, k == 2 ? "file" : "block", lo, hi, count);
        if (k == 1 && !klg_told_header++) klog("guns: the .prm's own header was not found at the start of its block: the block's bounds are used for the checks, not the file's table");
    }
    LeaveCriticalSection(&klg_cs);
}

static void klg_init(void)
{
    InitializeCriticalSection(&klg_cs);
    {   /* Enable=1 switches the part on. An ini that carries a Start or Set choice but no Enable key at all counts as on
           too: on 2026-10-11 the owner's ini was rewritten with [Guns] Start=1 Set=1 and without Enable, and the Guns
           page did nothing for a day. Enable=0 written out still switches it off. */
        int en = (int)GetPrivateProfileIntA("Guns", "Enable", -1, klh_ini);
        if (en < 0) en = GetPrivateProfileIntA("Guns", "Start", -1, klh_ini) >= 0 || GetPrivateProfileIntA("Guns", "Set", -1, klh_ini) >= 0;
        klg_on = en == 1;
    }
    klg_log = GetPrivateProfileIntA("Guns", "Log", 1, klh_ini);
    klg_start = (LONG)GetPrivateProfileIntA("Guns", "Start", 0, klh_ini); if (klg_start < 0 || klg_start > klg_upper[0]) klg_start = 0;
    klg_set = (LONG)GetPrivateProfileIntA("Guns", "Set", 0, klh_ini); if (klg_set < 0 || klg_set > klg_upper[1]) klg_set = 0;
    if (klg_on) klog("guns: on (hide bit, KLGuns.ini Version 2); starting rifle look %ld, shop guns %s; Arcade only", klg_start, klg_set ? "Dead Men looks" : "Dog Days");
    else klog("guns: off ([Guns] Enable=1 is not set): a level with gun looks shows what was built in, the Guns page does nothing");
}

#endif /* KLGUN_C */
