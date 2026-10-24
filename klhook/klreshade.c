/*
 * klreshade.c - THE RESHADE BRIDGE (2026-10-15, the owner: the looks as part of the game's own settings, switched in the game,
 * no restart; and the shaders seeing what happens to the player). Part of KLHook (included by klhook.c after kladren.c, SHIP and
 * TEST alike). READS ONLY in the game's memory: no game byte is written by this file. What it writes: KLHook.ini (through
 * klset.c), ReShade.ini [GENERAL] PresetPath (klhook.c, as before) and ONE preset file of its own beside the game,
 * ReShadePreset_KLLive.ini ([ReShade] LivePreset), which it makes from the look's preset (ReShadePreset_KL.ini /
 * ReShadePreset_LiveLeak.ini are only READ - the owner's tuned files are never written by this file).
 * OFF unless [ReShade] Bridge=1. Without it [Graphics] Look works as before (read once at start).
 *
 * 1. WHAT IT IS. After klhook.c has loaded ReShade32.dll, KLHook registers ITSELF as a ReShade add-on through ReShade's exported
 *    add-on API (the DLL is no .addon32 file: ReShade calls this an 'externally registered add-on', addon_manager.cpp
 *    load_addons, 'Loading externally registered add-on'). Then ReShade calls five functions of this file:
 *      init_effect_runtime / destroy_effect_runtime   the runtime object we talk to (one: the game has one swap chain)
 *      reshade_reloaded_effects                        every handle is dead: the cache is emptied and looked up again
 *      reshade_present                                 after ReShade drew its overlay: menu changes are applied here
 *      reshade_begin_effects                           right before the effects draw: the KL_* uniforms are set, every frame
 *    All five run on the thread that presents (the game's main loop). The game thread (klh_tick -> klrs_tick) only computes
 *    numbers into volatile floats; the menu (klset.c kset_put, game thread) only raises a flag.
 *
 * 2. THE ABI THIS FILE RELIES ON (ReShade 6.8.0 = github crosire/reshade tag v6.8.0, include/reshade.hpp, reshade_api.hpp,
 *    reshade_events.hpp; BSD-3-Clause OR MIT, Copyright (C) 2014/2021 Patrick Mours. Numbers only are used here, no code).
 *    a. Exports of ReShade32.dll (extern "C", __cdecl):  bool ReShadeRegisterAddon(void *module, uint32_t api_version);
 *       void ReShadeUnregisterAddon(void *module);  void ReShadeRegisterEvent(addon_event ev, void *callback).
 *       RESHADE_API_VERSION is 20 in 6.8.0. ReShade refuses a version above its own or of another major (version / 10000): an
 *       older ReShade says no and this file does nothing; a newer 6.x only ever ADDS virtual functions at the end.
 *       ReShadeRegisterEvent finds the add-on from the CALLBACK's address (find_addon(callback): GetModuleHandleEx FROM_ADDRESS),
 *       so the callbacks must live in this DLL - they do.
 *       A ReShade built with 'limited add-on support' refuses only events between destroy_effect_runtime and present
 *       (addon_manager.cpp ReShadeRegisterEventForAddon); every event used here is outside that range.
 *    b. Event numbers (enum class addon_event : uint32_t; checked by compiling the 6.8.0 header with clang, i686 MSVC ABI):
 *       init_effect_runtime 9, destroy_effect_runtime 10, reshade_present 75, reshade_begin_effects 76, reshade_reloaded_effects 78.
 *       Callbacks are plain __cdecl functions (RESHADE_DEFINE_ADDON_EVENT_TRAITS: ret(*)(...)).
 *    c. reshade::api::effect_runtime is a C++ object: its first dword is the vtable; every method is __thiscall (this in ECX, the
 *       rest on the stack, the callee pops). From C a __fastcall pointer with a dummy second argument does the same (EDX unused,
 *       everything after it on the stack) - klchar.c calls the game's own __thiscall methods this way. The handles
 *       (effect_technique, effect_uniform_variable) are 'struct { uint64_t handle; }' passed by value = 8 bytes on the stack.
 *       No method that RETURNS a handle is called (MSVC returns a struct from a member function through a hidden pointer).
 *       vtable slots (clang -Xclang -fdump-vtable-layouts, -target i686-pc-windows-msvc, on the 6.8.0 headers; api_object 0..2,
 *       device_object 3, effect_runtime from 4; no virtual is overloaded, so MSVC keeps declaration order):
 *         19 enumerate_uniform_variables(effect_name, cb, user)     22 get_uniform_variable_name(var, char *, size_t *)
 *         33 set_uniform_value_float(var, const float *, count, index)
 *         47 enumerate_techniques(effect_name, cb, user)            49 get_technique_name(tech, char *, size_t *)
 *         55 get_technique_state(tech) -> bool                      56 set_technique_state(tech, bool)
 *         61 set_effects_state(bool)                               62 get_current_preset_path(char *, size_t *)
 *         63 set_current_preset_path(const char *)                 70 get_technique_effect_name(tech, char *, size_t *)
 *       Before the first call the vtable and every slot used are checked to point INTO ReShade32.dll's image; else nothing is called.
 *    d. Behaviour read in runtime.cpp / runtime_api.cpp 6.8.0: enumerate_* return nothing while effects load (is_loading);
 *       reload_effects destroys every effect and THEN fires reshade_reloaded_effects (handles die there), and fires it again when
 *       loading has finished; enable_technique refuses a technique whose effect did not compile, and with
 *       [GENERAL] SkipLoadingDisabledEffects=1 an effect that the preset does not list is not loaded at all (it has no techniques
 *       to enable); with PerformanceMode=1 every preset load reloads the effects; set_current_preset_path(same path) loads the
 *       preset again from disk (ini_file::load_cache reloads a file whose time changed); set_current_preset_path(another path)
 *       first SAVES the current preset; set_uniform_value_* does not mark the preset modified.
 *
 * 3. THE SETTINGS (klset.c rows, KLHook.ini; all live while the bridge is up):
 *      [Graphics] Look      0 Off / 1 KL / 2 LiveLeak    Off: set_effects_state(false) - instant, ReShade STAYS loaded (see 5)
 *      [Graphics] CameraFX  0 off / 1 subtle / 2 raw     uniform KL_CamFX; with [ReShade] TechCamFX set, that technique on for 1, 2
 *      [Graphics] Glare     0 / 1                        uniform KL_Glare; with [ReShade] TechGlare set, that technique
 *      [Graphics] AA        0 off / 1 SMAA / 2 FXAA      techniques SMAA@SMAA.fx / KL_FXAA@KL_FXAA.fx
 *      [Graphics] Neural    0 / 1                        the Uplift marker technique live; the Uplift ADD-ON itself is loaded or set
 *                                                         aside by klhook.c at start (next start, as before)
 *      [Graphics] Textures  next start (kltex.c), not this file's.
 *    A change is applied in two ways. FAST: every technique it needs is loaded -> set_technique_state on the managed ones (no
 *    reload, the next frame). SLOW: a technique it needs is not loaded (SkipLoadingDisabledEffects) or the look changed -> the live
 *    preset is written again (Techniques= / TechniqueSorting= of ours + every [effect] section of the look's preset) and loaded
 *    with set_current_preset_path(live) = one effect reload (a hitch of the effect compile; the cache in IntermediateCachePath
 *    makes it short). A configuration is loaded the slow way once; a technique still missing after that is logged, not chased.
 *    Managed techniques are only those of [ReShade] TechFXAA / TechSMAA / TechUplift / TechKL / TechLiveLeak / TechGlare /
 *    TechCamFX (+ Extra=, always on): a technique the owner enables himself in the overlay is left alone by the fast way (the
 *    slow way rewrites the list: put it in Extra= to keep it).
 *    ReShade's own keys keep working: # toggles every effect (ours is called only when the Look row changes), F7 / F8 (its preset
 *    shortcuts) load the KL / LiveLeak preset - the bridge sees the other preset within 30 frames, takes it as Look 1 / 2 (the
 *    menu row follows, KLHook.ini is written) and loads the live preset for it (two reloads for one key). Another preset
 *    entirely: logged once and left alone.
 *
 * 4. THE UNIFORMS (set by NAME in every effect that declares them, every frame). A shader MUST declare them with a 'source'
 *    annotation of a name ReShade does not know, e.g.  uniform float KL_Fire < source = "KL_Fire"; >;
 *    WHY: the owner's ReShade.ini has [GENERAL] PerformanceMode=1, and in performance mode ReShade compiles every uniform WITHOUT a
 *    'source' into a constant (reshade_api.hpp, find_uniform_variable: 'will not find uniform variables when performance mode is
 *    enabled, since in that case uniform variables are replaced with constants'; runtime.cpp fills spec constants from the preset)
 *    - a plain 'uniform float KL_Fire;' would be frozen at 0 and invisible to the API. With a 'source' it stays a live uniform
 *    (as source = "timer" must); an unknown source is special_uniform::unknown (runtime.cpp 1838), which ReShade never writes and
 *    never saves into the preset (save_current_preset skips special != none) - so nothing fights the bridge's value:
 *      KL_Fire    0..1  how hard the player shoots lately: every round that leaves the magazine of the gun in his hand adds
 *                       FirePerShot (0.25), it falls by 1 / FireSeconds (1.5) a second. The magazine: [player+0x920] the item in
 *                       hand, its gun object from the inventory [player+0xcec] (klhud_weapon.c's reading, re\hud_weapon.md 1),
 *                       [gun+0xdc] ^ 0xbeebbeeb when the gun's vtable +0x2fc is 0x511f50 (else no shots are seen for it).
 *      KL_Hurt    0..1  recent damage: a loss of health adds HurtGain (4) x lost / maximum (a quarter of the bar = 1.0), it falls
 *                       by 1 / HurtSeconds (2.0) a second. Health object [player+0xa48] (+4 now, +8 maximum, +0x24 = the player:
 *                       klbalance.c 2b). A tick in which the maximum changed is not counted (klbalance.c scales it).
 *      KL_Down    0 / 1 1 while the down-not-dead state [[player+0x2948]+4] is not 0 (kldown.c's reading; also without [Down])
 *      KL_Speed   0..1  the feet's horizontal speed [player+0x460] (x, z; 100 units a metre) / SpeedFull (6 m/s), smoothed 0.2 s;
 *                       a jump over 40 m/s (a teleport, a respawn) is not counted
 *      KL_Health  0..1  health now / maximum (1 with no player)
 *      KL_Look 0/1/2, KL_CamFX 0/1/2, KL_Glare 0/1   the menu's values (a shader can branch on them, no reload)
 *      KL_CrackN 0..3, KL_Crack0 / KL_Crack1 / KL_Crack2 (float4: x, y, size, intensity)   the cracked lens, see 6
 *    The local player is the one klbalance.c / kldown.c read ([0xdd265c] +0x828 + 4 x [+0x898], vtable 0xbb45f4). Any level, any
 *    mode: these are reads only, nothing of the game changes.
 *
 * 5. WHAT 'OFF' COSTS. Look=0 AT START: ReShade is not loaded at all (klhook.c, as before: the stock frame rate; run LOOK2 measured
 *    ~252 fps without, ~130 with the looks on) - then the menu cannot switch a look on before the next start (the row's change is
 *    logged 'from the next start'). [ReShade] LoadWhenOff=1: ReShade is loaded with Look=0 too and starts with every effect off,
 *    so the row can switch a look on live. Look=0 LIVE (or with LoadWhenOff): no effect is drawn, but ReShade still sits in
 *    Direct3D 9 - its Present hook, the state block it captures and restores every frame, its overlay / input hooks and the
 *    compiled effects in video memory stay. NOT MEASURED: expected a small part of the 130 vs 252 (that gap is mostly the
 *    effects themselves); a Perf=1 run with LoadWhenOff=1, Look=0 gives the number.
 *
 * 6. THE CRACKED LENS (2026-10-17, the owner: "if you get shot a lot ... the camera frame glass is cracked"). Cosmetic and local (nothing
 *    of the game is written, nothing is sent), so it also runs online. Hit = the same reading as KL_Hurt: a tick in which the health
 *    object's current value [[player+0xa48]+4] fell by at least 1 % of the maximum while the player is not in the down state (bleeding
 *    out is not a hit). The hit's time goes in a ring; when the hits inside LensCrackWindow seconds reach LensCrackHits - or health is
 *    under LensCrackHealth (a share, 0.35) with at least 2 hits in the window - ONE roll is made: the window is emptied, and when the
 *    cooldown (LensCrackCooldown s since the last crack) has passed, fewer than LensCrackMax cracks stand and a random number is under
 *    LensCrackChance (percent) a crack is added. Where the bullet came from is not known to the hook: the place is random, biased to
 *    the frame edges and corners (the biased axis is 0.06 .. 0.32 from the edge, so the crosshair stays clear). A crack lives until the
 *    health reaches 0, the player object changes (respawn as a fed, a new round, a level load), no player exists, or the health
 *    rises by more than 25 % of the maximum in one tick. The shader gets, every frame, KL_Crack0..2 (x, y = centre in 0..1 of the screen, size =
 *    reach in screen heights, which grows to its full value in KLRS_CRACK_SPREAD_MS, intensity 0..1) and KL_CrackN = how many stand.
 *    Ini [Graphics]: LensCrack (1; 0 = off, no uniform, the technique is not asked for), LensCrackHits (6), LensCrackWindow (4),
 *    LensCrackChance (35), LensCrackMax (3, 1..3), LensCrackCooldown (8), LensCrackHealth (0.35). The technique is [ReShade] TechCrack
 *    (default KL_LensCrack@KL_LensCrack.fx), wanted while LensCrack=1; ini only, there is no Mod settings row. Everything above is GUESS
 *    except the health reading (shared with KL_Hurt).
 *
 * NOT RUN IN THE GAME. Compiled only (agent build); the ABI is checked against the 6.8.0 headers, not against the running DLL.
 */
#ifndef KLRESHADE_C
#define KLRESHADE_C

#define KLRS_API_VERSION    20              /* RESHADE_API_VERSION of 6.8.0 */
#define KLRS_EV_INIT_RT     9
#define KLRS_EV_DESTROY_RT  10
#define KLRS_EV_PRESENT     75
#define KLRS_EV_BEGIN_FX    76
#define KLRS_EV_RELOADED    78
#define KLRS_V_ENUM_UNI     19
#define KLRS_V_UNI_NAME     22
#define KLRS_V_SET_FLOAT    33
#define KLRS_V_ENUM_TECH    47
#define KLRS_V_TECH_NAME    49
#define KLRS_V_GET_TECH     55
#define KLRS_V_SET_TECH     56
#define KLRS_V_SET_FX       61
#define KLRS_V_GET_PRESET   62
#define KLRS_V_SET_PRESET   63
#define KLRS_V_TECH_EFFECT  70

typedef struct { unsigned __int64 h; } klrs_h;      /* reshade::api::effect_technique / effect_uniform_variable */
typedef void (__cdecl *klrs_cb_t)(void *rt, klrs_h h, void *user);
typedef void (__fastcall *klrs_enum_t)(void *, void *, const char *, klrs_cb_t, void *);
typedef void (__fastcall *klrs_name_t)(void *, void *, klrs_h, char *, size_t *);
typedef void (__fastcall *klrs_setf_t)(void *, void *, klrs_h, const float *, size_t, size_t);
typedef unsigned char (__fastcall *klrs_gett_t)(void *, void *, klrs_h);
typedef void (__fastcall *klrs_sett_t)(void *, void *, klrs_h, int);
typedef void (__fastcall *klrs_setfx_t)(void *, void *, int);
typedef void (__fastcall *klrs_getp_t)(void *, void *, char *, size_t *);
typedef void (__fastcall *klrs_setp_t)(void *, void *, const char *);
#define KLRS_FN(rt, i) (((void **)*(void **)(rt))[i])

/* what ReShade's add-on list shows (addon_manager.cpp reads the exports NAME / DESCRIPTION as 'const char *const *') */
const char *klrs_addon_name = "KLHook (KL Merge)";
const char *klrs_addon_desc = "Kane & Lynch 2 mod settings: the looks from the game's Options menu, and the player's fire / hurt / down / speed for the shaders.";
#pragma comment(linker, "/EXPORT:NAME=_klrs_addon_name,DATA")
#pragma comment(linker, "/EXPORT:DESCRIPTION=_klrs_addon_desc,DATA")

enum { KLRS_U_FIRE, KLRS_U_HURT, KLRS_U_DOWN, KLRS_U_SPEED, KLRS_U_HEALTH, KLRS_U_LOOK, KLRS_U_CAMFX, KLRS_U_GLARE, KLRS_U_CRACKN, KLRS_NU };
static const char *const klrs_uname[KLRS_NU] = { "KL_Fire", "KL_Hurt", "KL_Down", "KL_Speed", "KL_Health", "KL_Look", "KL_CamFX", "KL_Glare", "KL_CrackN" };
static volatile float klrs_val[KLRS_NU] = { 0, 0, 0, 0, 1, 0, 0, 0, 0 };
/* the cracked lens' float4 uniforms: handle kind KLRS_NU + j */
#define KLRS_NCRACK 3
#define KLRS_CRACK_SPREAD_MS 120            /* GUESS: how long a new crack takes to reach its full size */
static const char *const klrs_cname[KLRS_NCRACK] = { "KL_Crack0", "KL_Crack1", "KL_Crack2" };

enum { KLRS_T_FXAA, KLRS_T_SMAA, KLRS_T_UPLIFT, KLRS_T_KL, KLRS_T_LL, KLRS_T_GLARE, KLRS_T_CAMFX, KLRS_T_CRACK, KLRS_NT };
static const char *const klrs_tkey[KLRS_NT] = { "TechFXAA", "TechSMAA", "TechUplift", "TechKL", "TechLiveLeak", "TechGlare", "TechCamFX", "TechCrack" };
static const char *const klrs_tdef[KLRS_NT] = { "KL_FXAA@KL_FXAA.fx", "SMAA@SMAA.fx", "Uplift@Uplift.fx", "KL_Look@KL_Look.fx", "KL_Camcorder@KL_Camcorder.fx", "", "", "KL_LensCrack@KL_LensCrack.fx" };

#define KLRS_MAXU 64
#define KLRS_MAXT 32
static struct {
    int want, on, log;                       /* Bridge=1; registered with ReShade; Log */
    HMODULE rs, self; DWORD_PTR lo, hi;       /* ReShade32.dll and its image */
    void (__cdecl *unreg)(void *);
    void *rt;                                 /* the effect runtime (present thread) */
    volatile LONG dirty;                      /* a menu change waits for the present thread */
    int fxoff;                                /* this file switched the effects off (Look 0) */
    int genlook;                              /* the look the live preset on disk was written for (0 = none / unknown) */
    int slowdone;                             /* the configuration last loaded the slow way (-1 = none) */
    int foreign, missingtold, nouni;
    int scan, scantries; DWORD frames, scanat;
    int nu; struct { klrs_h h; int k; } u[KLRS_MAXU];
    int nt; struct { klrs_h h; int k; } t[KLRS_MAXT];
    char tech[KLRS_NT][96], extra[512], sorting[1024];
    char live[MAX_PATH], liveabs[MAX_PATH], tpl[3][MAX_PATH];
    float fire_per, fire_s, hurt_gain, hurt_s, speed_full;
    int reload_on; float reload_lvl, reload_hold, reload_tail;   /* k39 [ReShade] ReloadFx / ReloadFxLevel / ReloadFxHold / ReloadFxTail */
    /* the cracked lens (6): settings, then the state (the game thread writes, the present thread reads) */
    int crack_on, crack_hits, crack_max; float crack_win, crack_chance, crack_cool, crack_hp;
    struct { float x, y, size, inten; DWORD birth; } crack[KLRS_NCRACK];
    volatile LONG crack_n;
    DWORD hit_t[32]; int nhit; DWORD crack_last; unsigned rng;
} klrs = { 0 };

static float klrs_inif(const char *key, float def)
{
    char b[32]; float v;
    GetPrivateProfileStringA("ReShade", key, "", b, sizeof b, klh_ini);
    if (!b[0]) return def;
    v = (float)atof(b);
    return v == v && v > -1e6f && v < 1e6f ? v : def;
}

/* a [Graphics] key (the cracked lens' settings live beside the other looks) */
static float klrs_inig(const char *key, float def)
{
    char b[32]; float v;
    GetPrivateProfileStringA("Graphics", key, "", b, sizeof b, klh_ini);
    if (!b[0]) return def;
    v = (float)atof(b);
    return v == v && v > -1e6f && v < 1e6f ? v : def;
}

static const char *klrs_base(const char *p)
{
    const char *a = strrchr(p, '\\'), *b = strrchr(p, '/');
    if (b > a) a = b;
    return a ? a + 1 : p;
}

/* klset.c's rows: 0 Look, 4 CameraFX, 5 Glare, 6 AA, 7 Neural */
static unsigned klrs_wantmask(int look)
{
    unsigned m = 0; int k;
    if (kset_v[6] == 2) m |= 1u << KLRS_T_FXAA;
    if (kset_v[6] == 1) m |= 1u << KLRS_T_SMAA;
    if (kset_v[7]) m |= 1u << KLRS_T_UPLIFT;
    m |= 1u << (look == 2 ? KLRS_T_LL : KLRS_T_KL);
    if (kset_v[5]) m |= 1u << KLRS_T_GLARE;
    if (kset_v[4]) m |= 1u << KLRS_T_CAMFX;
    if (klrs.crack_on) m |= 1u << KLRS_T_CRACK;
    for (k = 0; k < KLRS_NT; k++) if (!klrs.tech[k][0]) m &= ~(1u << k);
    return m;
}

static void klrs_cat(char *out, size_t cap, const char *s)
{
    size_t n = strlen(out);
    if (!s[0] || n + strlen(s) + 2 >= cap) return;
    if (n) { out[n++] = ','; out[n] = 0; }
    strcat(out, s);
}

/* The live preset for a look: our two technique lines, then the look's preset without its own two (the lines before the first
   [section]: ReShade's preset keeps them there, section-less). -> 1 = written */
static int klrs_write_live(int look)
{
    char *buf = 0, want[1200], sort[1600]; FILE *f; long n = 0; unsigned m; int k, head = 1; char *p, *e;
    if (look < 1 || look > 2) look = 1;
    m = klrs_wantmask(look);
    want[0] = 0; sort[0] = 0;
    for (k = 0; k < KLRS_NT; k++) if (m & (1u << k)) klrs_cat(want, sizeof want, klrs.tech[k]);
    if (klrs.extra[0]) klrs_cat(want, sizeof want, klrs.extra);
    if (klrs.sorting[0]) strncpy(sort, klrs.sorting, sizeof sort - 1);
    else { for (k = 0; k < KLRS_NT; k++) klrs_cat(sort, sizeof sort, klrs.tech[k]); if (klrs.extra[0]) klrs_cat(sort, sizeof sort, klrs.extra); }
    sort[sizeof sort - 1] = 0;
    if ((f = fopen(klrs.tpl[look], "rb")) != 0) {
        if (!fseek(f, 0, SEEK_END) && (n = ftell(f)) > 0 && n < (1 << 20) && !fseek(f, 0, SEEK_SET) && (buf = (char *)malloc((size_t)n + 1)) != 0) {
            n = (long)fread(buf, 1, (size_t)n, f); buf[n] = 0;
        } else n = 0;
        fclose(f);
    } else klog("reshade: the look's preset %s is not there: the live preset gets the technique lists only (every effect's own defaults)", klrs.tpl[look]);
    if (!(f = fopen(klrs.liveabs, "wb"))) { klog("reshade: cannot write %s (error %lu): the live preset stays as it was", klrs.liveabs, GetLastError()); free(buf); return 0; }
    fprintf(f, "Techniques=%s\r\nTechniqueSorting=%s\r\n", want, sort);
    for (p = buf; p && *p; p = e) {
        size_t len; e = strchr(p, '\n'); e = e ? e + 1 : p + strlen(p); len = (size_t)(e - p);
        if (*p == '[') head = 0;
        if (head && (!strncmp(p, "Techniques=", 11) || !strncmp(p, "TechniqueSorting=", 17))) continue;
        fwrite(p, 1, len, f);
    }
    fclose(f);
    free(buf);
    klrs.genlook = look;
    if (klrs.log) klog("reshade: live preset %s written for the %s look: Techniques=%s", klrs.live, look == 2 ? "LiveLeak" : "KL", want);
    return 1;
}

/* klhook.c, before LoadLibrary: reads the keys, writes the live preset. -> the PresetPath to give ReShade (0 = bridge off) */
static const char *klrs_prepare(int look)
{
    char v[MAX_PATH]; int k;
    klrs.want = GetPrivateProfileIntA("ReShade", "Bridge", 0, klh_ini) != 0;
    if (!klrs.want) return 0;
    klrs.log = GetPrivateProfileIntA("ReShade", "Log", 1, klh_ini);
    for (k = 0; k < KLRS_NT; k++) GetPrivateProfileStringA("ReShade", klrs_tkey[k], klrs_tdef[k], klrs.tech[k], sizeof klrs.tech[k], klh_ini);
    GetPrivateProfileStringA("ReShade", "Extra", "", klrs.extra, sizeof klrs.extra, klh_ini);
    GetPrivateProfileStringA("ReShade", "Sorting", "", klrs.sorting, sizeof klrs.sorting, klh_ini);
    GetPrivateProfileStringA("ReShade", "LivePreset", "ReShadePreset_KLLive.ini", v, sizeof v, klh_ini);
    snprintf(klrs.live, sizeof klrs.live, ".\\%s", klrs_base(v));
    snprintf(klrs.liveabs, sizeof klrs.liveabs, "%s\\%s", dir, klrs_base(v));
    GetPrivateProfileStringA("ReShade", "PresetKL", "ReShadePreset_KL.ini", v, sizeof v, klh_ini);
    snprintf(klrs.tpl[1], sizeof klrs.tpl[1], "%s\\%s", dir, klrs_base(v));
    GetPrivateProfileStringA("ReShade", "PresetLiveLeak", "ReShadePreset_LiveLeak.ini", v, sizeof v, klh_ini);
    snprintf(klrs.tpl[2], sizeof klrs.tpl[2], "%s\\%s", dir, klrs_base(v));
    klrs.fire_per = klrs_inif("FirePerShot", 0.25f);
    klrs.fire_s = klrs_inif("FireSeconds", 1.5f); if (klrs.fire_s < 0.05f) klrs.fire_s = 0.05f;
    /* k39 (owner 2026-10-25: 'when you reload it acts like theres no effects'): KL_Fire only rises with rounds leaving the magazine, so a reload
       (magazine goes UP, nothing leaves it) let every camera effect fade out in 1.5 s and the picture went perfectly clean. ReloadFx keeps KL_Fire at a
       floor (ReloadFxLevel) from the last shot for ReloadFxHold seconds, and for ReloadFxTail seconds after the magazine count rises (the reload's end). */
    klrs.reload_on = klrs_inif("ReloadFx", 1.0f) != 0;
    klrs.reload_lvl = klrs_inif("ReloadFxLevel", 0.35f); if (klrs.reload_lvl < 0) klrs.reload_lvl = 0; if (klrs.reload_lvl > 1) klrs.reload_lvl = 1;
    klrs.reload_hold = klrs_inif("ReloadFxHold", 3.5f); if (klrs.reload_hold < 0) klrs.reload_hold = 0; if (klrs.reload_hold > 20) klrs.reload_hold = 20;
    klrs.reload_tail = klrs_inif("ReloadFxTail", 0.6f); if (klrs.reload_tail < 0) klrs.reload_tail = 0; if (klrs.reload_tail > 10) klrs.reload_tail = 10;
    klrs.hurt_gain = klrs_inif("HurtGain", 4.0f);
    klrs.hurt_s = klrs_inif("HurtSeconds", 2.0f); if (klrs.hurt_s < 0.05f) klrs.hurt_s = 0.05f;
    klrs.speed_full = klrs_inif("SpeedFull", 6.0f); if (klrs.speed_full < 0.5f) klrs.speed_full = 0.5f;
    if (!_stricmp(klrs_base(klrs.liveabs), klrs_base(klrs.tpl[1])) || !_stricmp(klrs_base(klrs.liveabs), klrs_base(klrs.tpl[2]))) {
        klog("reshade: [ReShade] LivePreset is one of the looks' own presets (%s): refused, the bridge stays off (it must never write those)", klrs.live);
        klrs.want = 0; return 0;
    }
    klrs.crack_on = klrs_inig("LensCrack", 1) != 0;
    klrs.crack_hits = (int)klrs_inig("LensCrackHits", 6); if (klrs.crack_hits < 1) klrs.crack_hits = 1; if (klrs.crack_hits > 30) klrs.crack_hits = 30;
    klrs.crack_win = klrs_inig("LensCrackWindow", 4.0f); if (klrs.crack_win < 0.2f) klrs.crack_win = 0.2f;
    klrs.crack_chance = klrs_inig("LensCrackChance", 35.0f);
    klrs.crack_max = (int)klrs_inig("LensCrackMax", 3); if (klrs.crack_max < 1) klrs.crack_max = 1; if (klrs.crack_max > KLRS_NCRACK) klrs.crack_max = KLRS_NCRACK;
    klrs.crack_cool = klrs_inig("LensCrackCooldown", 8.0f); if (klrs.crack_cool < 0) klrs.crack_cool = 0;
    klrs.crack_hp = klrs_inig("LensCrackHealth", 0.35f);
    klrs.rng = GetTickCount() * 2654435761u | 1u;
    klrs.slowdone = -1;
    if (!klrs_write_live(look ? look : 1)) { klrs.want = 0; return 0; }
    return klrs.live;
}

static int klrs_in(DWORD_PTR p) { return p >= klrs.lo && p < klrs.hi; }

/* is this the runtime we talk to, and does its vtable look like ReShade's? (the first time: every slot used is checked) */
static int klrs_rt_ok(void *rt)
{
    static void *checked; static int told;
    static const int slots[] = { KLRS_V_ENUM_UNI, KLRS_V_UNI_NAME, KLRS_V_SET_FLOAT, KLRS_V_ENUM_TECH, KLRS_V_TECH_NAME, KLRS_V_GET_TECH,
                                 KLRS_V_SET_TECH, KLRS_V_SET_FX, KLRS_V_GET_PRESET, KLRS_V_SET_PRESET, KLRS_V_TECH_EFFECT };
    DWORD vt = 0, f = 0; int i;
    if (!klrs.on || !rt || rt != klrs.rt) return 0;
    if (checked == rt) return 1;
    if (!klh_rd((DWORD_PTR)rt, &vt, 4) || !klrs_in(vt)) { if (!told++) klog("reshade: the effect runtime %p has a vtable %08lx outside ReShade32.dll (%08lx-%08lx): the bridge calls nothing", rt, vt, (DWORD)klrs.lo, (DWORD)klrs.hi); klrs.on = 0; return 0; }
    for (i = 0; i < (int)(sizeof slots / sizeof slots[0]); i++)
        if (!klh_rd(vt + 4 * slots[i], &f, 4) || !klrs_in(f)) { if (!told++) klog("reshade: slot %d of the effect runtime's vtable is %08lx, not in ReShade32.dll: not the 6.x layout this build knows - the bridge calls nothing", slots[i], f); klrs.on = 0; return 0; }
    checked = rt;
    return 1;
}

static void __cdecl klrs_cb_uni(void *rt, klrs_h h, void *user)
{
    char n[40]; size_t sz = sizeof n; int k; (void)user;
    if (klrs.nu >= KLRS_MAXU) return;
    n[0] = 0;
    ((klrs_name_t)KLRS_FN(rt, KLRS_V_UNI_NAME))(rt, 0, h, n, &sz);
    n[sizeof n - 1] = 0;
    if (n[0] != 'K' || n[1] != 'L' || n[2] != '_') return;
    for (k = 0; k < KLRS_NU; k++) if (!strcmp(n, klrs_uname[k])) { klrs.u[klrs.nu].h = h; klrs.u[klrs.nu].k = k; klrs.nu++; return; }
    for (k = 0; k < KLRS_NCRACK; k++) if (!strcmp(n, klrs_cname[k])) { klrs.u[klrs.nu].h = h; klrs.u[klrs.nu].k = KLRS_NU + k; klrs.nu++; return; }
}

static void __cdecl klrs_cb_tech(void *rt, klrs_h h, void *user)
{
    char n[64], e[64], both[132]; size_t a = sizeof n, b = sizeof e; int k; (void)user;
    if (klrs.nt >= KLRS_MAXT) return;
    n[0] = e[0] = 0;
    ((klrs_name_t)KLRS_FN(rt, KLRS_V_TECH_NAME))(rt, 0, h, n, &a);
    ((klrs_name_t)KLRS_FN(rt, KLRS_V_TECH_EFFECT))(rt, 0, h, e, &b);
    n[sizeof n - 1] = e[sizeof e - 1] = 0;
    snprintf(both, sizeof both, "%s@%s", n, e);
    for (k = 0; k < KLRS_NT; k++) if (klrs.tech[k][0] && !_stricmp(both, klrs.tech[k])) { klrs.t[klrs.nt].h = h; klrs.t[klrs.nt].k = k; klrs.nt++; return; }
}

static void klrs_scan(void *rt)
{
    klrs.nu = klrs.nt = 0;
    ((klrs_enum_t)KLRS_FN(rt, KLRS_V_ENUM_UNI))(rt, 0, 0, klrs_cb_uni, 0);
    ((klrs_enum_t)KLRS_FN(rt, KLRS_V_ENUM_TECH))(rt, 0, 0, klrs_cb_tech, 0);
    if (!klrs.nu && !klrs.nt && ++klrs.scantries < 60) { klrs.scanat = klrs.frames; return; }      /* still loading: again in 10 frames (60 x = ~10 s) */
    klrs.scan = 0;
    if (!klrs.nu && klrs.log && !klrs.nouni++)
        klog("reshade: no effect declares a KL_ uniform the API can see (KL_Fire, KL_Hurt, KL_Down, KL_Speed, KL_Health, KL_Look, KL_CamFX, KL_Glare, KL_CrackN, KL_Crack0..2): with PerformanceMode=1 they need < source = \"KL_Fire\"; > etc. (klreshade.c 4)");
    if (klrs.log) {
        char s[400]; int i; s[0] = 0;
        for (i = 0; i < klrs.nt; i++) klrs_cat(s, sizeof s, klrs.tech[klrs.t[i].k]);
        klog("reshade: effects loaded: %d KL_ uniform(s) to set every frame, managed technique(s) present: %s", klrs.nu, s[0] ? s : "none");
    }
    InterlockedExchange(&klrs.dirty, 1);                   /* the states as the menu has them (a no-op after our own slow load) */
}

static void klrs_apply(void *rt)
{
    int look = (int)kset_v[0], k, i, have, key, missing = 0; unsigned m;
    klrs_val[KLRS_U_LOOK] = (float)look; klrs_val[KLRS_U_CAMFX] = (float)kset_v[4]; klrs_val[KLRS_U_GLARE] = (float)kset_v[5];
    if (look == 0) {
        if (!klrs.fxoff) { ((klrs_setfx_t)KLRS_FN(rt, KLRS_V_SET_FX))(rt, 0, 0); klrs.fxoff = 1; klog("reshade: Look Off: every effect off (ReShade stays loaded; # turns them on again by hand)"); }
        return;
    }
    if (klrs.fxoff) { ((klrs_setfx_t)KLRS_FN(rt, KLRS_V_SET_FX))(rt, 0, 1); klrs.fxoff = 0; }
    m = klrs_wantmask(look);
    key = (int)((m << 2) | (unsigned)look);
    for (k = 0; k < KLRS_NT; k++) {
        if (!(m & (1u << k))) continue;
        for (have = 0, i = 0; i < klrs.nt; i++) if (klrs.t[i].k == k) have = 1;
        if (!have) missing |= 1 << k;
    }
    if ((look != klrs.genlook || missing) && klrs.slowdone != key) {
        klrs.slowdone = key;
        if (klrs_write_live(look)) {
            /* the path exactly as ReShade holds it when it is ours: another spelling of the same file would make
               set_current_preset_path SAVE the running preset over the file just written before it loads it */
            char cur[MAX_PATH]; size_t sz = sizeof cur; cur[0] = 0;
            ((klrs_getp_t)KLRS_FN(rt, KLRS_V_GET_PRESET))(rt, 0, cur, &sz);
            cur[sizeof cur - 1] = 0;
            klrs.nu = klrs.nt = 0;                        /* the reload kills every handle (the event will say so too) */
            ((klrs_setp_t)KLRS_FN(rt, KLRS_V_SET_PRESET))(rt, 0, cur[0] && !_stricmp(klrs_base(cur), klrs_base(klrs.liveabs)) ? cur : klrs.liveabs);
            klog("reshade: %s look%s: the live preset loaded again (one effect reload)", look == 2 ? "LiveLeak" : "KL", missing ? " with a technique that was not loaded" : "");
            klrs.missingtold = 0;
            return;
        }
    }
    if (missing && !klrs.missingtold++) {
        char s[400]; s[0] = 0;
        for (k = 0; k < KLRS_NT; k++) if (missing & (1 << k)) klrs_cat(s, sizeof s, klrs.tech[k]);
        klog("reshade: wanted but not among the loaded effects even after a reload: %s (no such technique / file, or it failed to compile - ReShade.log says)", s);
    }
    for (i = 0; i < klrs.nt; i++) {
        int want = (m >> klrs.t[i].k) & 1, now = ((klrs_gett_t)KLRS_FN(rt, KLRS_V_GET_TECH))(rt, 0, klrs.t[i].h) != 0;
        if (want != now) {
            ((klrs_sett_t)KLRS_FN(rt, KLRS_V_SET_TECH))(rt, 0, klrs.t[i].h, want);
            if (klrs.log) klog("reshade: %s %s", klrs.tech[klrs.t[i].k], want ? "on" : "off");
        }
    }
}

/* F7 / F8 (ReShade's preset shortcuts) or the overlay loaded another preset: follow it as the Look row */
static void klrs_watch(void *rt)
{
    char p[MAX_PATH]; size_t sz = sizeof p; const char *b; int look = 0;
    p[0] = 0;
    ((klrs_getp_t)KLRS_FN(rt, KLRS_V_GET_PRESET))(rt, 0, p, &sz);
    p[sizeof p - 1] = 0;
    if (!p[0]) return;
    b = klrs_base(p);
    if (!_stricmp(b, klrs_base(klrs.liveabs))) { klrs.foreign = 0; return; }
    if (!_stricmp(b, klrs_base(klrs.tpl[1]))) look = 1;
    else if (!_stricmp(b, klrs_base(klrs.tpl[2]))) look = 2;
    if (!look) { if (!klrs.foreign++) klog("reshade: ReShade now runs the preset %s, not one of ours: the bridge leaves the techniques alone while it stands (the uniforms are still set)", p); return; }
    klog("reshade: ReShade loaded %s (a preset key or the overlay): taken as Look %d, the live preset goes back in", b, look);
    klrs.genlook = 0; klrs.slowdone = -1;
    kset_put(0, look);
    InterlockedExchange(&klrs.dirty, 1);
}

static void __cdecl klrs_ev_init(void *rt)
{
    if (!klrs.on) return;
    if (klrs.rt && klrs.rt != rt) { klog("reshade: a second effect runtime %p (ours is %p): left alone", rt, klrs.rt); return; }
    klrs.rt = rt;
    if (!klrs_rt_ok(rt)) { klrs.rt = 0; return; }
    klrs.nu = klrs.nt = 0; klrs.scan = 1; klrs.scantries = 0; klrs.scanat = klrs.frames; klrs.fxoff = 0;
    InterlockedExchange(&klrs.dirty, 1);
    klog("reshade: effect runtime %p up (Look %ld, CameraFX %ld, Glare %ld, AA %ld, Neural %ld)", rt, kset_v[0], kset_v[4], kset_v[5], kset_v[6], kset_v[7]);
}

static void __cdecl klrs_ev_destroy(void *rt)
{
    if (!klrs.on || rt != klrs.rt) return;
    klrs.rt = 0; klrs.nu = klrs.nt = 0; klrs.scan = 0;
    if (klrs.log) klog("reshade: effect runtime %p gone (a device reset or the end)", rt);
}

static void __cdecl klrs_ev_reloaded(void *rt)
{
    if (!klrs.on || rt != klrs.rt) return;
    klrs.nu = klrs.nt = 0;                              /* every handle is dead from here */
    klrs.scan = 1; klrs.scantries = 0; klrs.scanat = klrs.frames;
}

static void __cdecl klrs_ev_present(void *rt)
{
    if (!klrs_rt_ok(rt)) return;
    klrs.frames++;
    if (klrs.scan && klrs.frames - klrs.scanat >= 10) klrs_scan(rt);
    if (klrs.frames % 30 == 0 && kset_v[0] != 0) klrs_watch(rt);
    if (klrs.foreign) return;
    if (!klrs.scan && InterlockedExchange(&klrs.dirty, 0)) klrs_apply(rt);
}

static void __cdecl klrs_ev_begin(void *rt, void *cmd, klrs_h rtv, klrs_h rtv_srgb)
{
    float v[KLRS_NU]; int i; (void)cmd; (void)rtv; (void)rtv_srgb;
    if (!klrs_rt_ok(rt) || !klrs.nu) return;
    for (i = 0; i < KLRS_NU; i++) v[i] = klrs_val[i];
    for (i = 0; i < klrs.nu; i++) {
        int k = klrs.u[i].k;
        if (k < KLRS_NU) ((klrs_setf_t)KLRS_FN(rt, KLRS_V_SET_FLOAT))(rt, 0, klrs.u[i].h, &v[k], 1, 0);
        else {                                           /* KL_Crack<j>: x, y, size (grown over the spread time), intensity */
            float c[4], t, e; int j = k - KLRS_NU; DWORD age = GetTickCount() - klrs.crack[j].birth;
            t = age >= KLRS_CRACK_SPREAD_MS ? 1.0f : (float)age / KLRS_CRACK_SPREAD_MS; e = 1.0f - (1.0f - t) * (1.0f - t) * (1.0f - t);
            c[0] = klrs.crack[j].x; c[1] = klrs.crack[j].y;
            c[2] = j < klrs.crack_n ? klrs.crack[j].size * e : 0.0f;
            c[3] = j < klrs.crack_n ? klrs.crack[j].inten : 0.0f;
            ((klrs_setf_t)KLRS_FN(rt, KLRS_V_SET_FLOAT))(rt, 0, klrs.u[i].h, c, 4, 0);
        }
    }
}

/* klhook.c, right after LoadLibrary(ReShade32.dll) succeeded */
static void klrs_attach(HMODULE rs, HMODULE self)
{
    typedef unsigned char (__cdecl *reg_t)(void *, unsigned);
    typedef void (__cdecl *ev_t)(unsigned, void *);
    reg_t reg; ev_t ev; IMAGE_NT_HEADERS *nt;
    if (!klrs.want || !rs) return;
    reg = (reg_t)GetProcAddress(rs, "ReShadeRegisterAddon");
    ev = (ev_t)GetProcAddress(rs, "ReShadeRegisterEvent");
    klrs.unreg = (void (__cdecl *)(void *))GetProcAddress(rs, "ReShadeUnregisterAddon");
    if (!reg || !ev || !klrs.unreg) {
        klog("reshade: ReShade32.dll has no add-on API (ReShadeRegisterAddon %s, ReShadeRegisterEvent %s, ReShadeUnregisterAddon %s): the bridge stays off; the look is the one of the start",
             reg ? "yes" : "no", ev ? "yes" : "no", klrs.unreg ? "yes" : "no");
        return;
    }
    nt = (IMAGE_NT_HEADERS *)((BYTE *)rs + ((IMAGE_DOS_HEADER *)rs)->e_lfanew);
    klrs.lo = (DWORD_PTR)rs; klrs.hi = klrs.lo + nt->OptionalHeader.SizeOfImage;
    klrs.rs = rs; klrs.self = self;
    if (!(reg(self, KLRS_API_VERSION) & 0xff)) {
        klog("reshade: ReShade refused KLHook as an add-on (API version %d asked - an older ReShade than 6.8, or another add-on of that name; ReShade.log has the reason): the bridge stays off", KLRS_API_VERSION);
        return;
    }
    klrs.on = 1;
    ev(KLRS_EV_INIT_RT, (void *)klrs_ev_init);
    ev(KLRS_EV_DESTROY_RT, (void *)klrs_ev_destroy);
    ev(KLRS_EV_RELOADED, (void *)klrs_ev_reloaded);
    ev(KLRS_EV_PRESENT, (void *)klrs_ev_present);
    ev(KLRS_EV_BEGIN_FX, (void *)klrs_ev_begin);
    klog("reshade: KLHook is a ReShade add-on (API %d, ReShade32.dll %08lx-%08lx): the Mod settings rows Look / Camera FX / Lens glare / Anti-aliasing switch live; live preset %s",
         KLRS_API_VERSION, (DWORD)klrs.lo, (DWORD)klrs.hi, klrs.live);
}

/* klset.c, after a row changed (the game thread): what the change does now */
static const char *klrs_setting(int i)
{
    if (i == 1) return "; from the next start of the game";
    if (klrs.on && klrs.foreign && (i == 0 || i >= 4)) { klrs.foreign = 0; klrs.genlook = 0; klrs.slowdone = -1; }     /* the menu wins over a foreign preset */
    if (i == 7) { if (klrs.on) InterlockedExchange(&klrs.dirty, 1); return klrs.on ? "; the Uplift marker now, the Uplift add-on itself from the next start" : "; from the next start of the game"; }
    if (i == 0 || i == 4 || i == 5 || i == 6) {
        if (klrs.on) { InterlockedExchange(&klrs.dirty, 1); return klrs.rt ? "; now (ReShade bridge)" : "; when ReShade's runtime is up"; }
        return i == 0 ? "; from the next start of the game" : "; needs [ReShade] Bridge=1 and ReShade loaded (nothing now)";
    }
    return "; now";
}

static float klrs_rnd(void)
{
    klrs.rng ^= klrs.rng << 13; klrs.rng ^= klrs.rng >> 17; klrs.rng ^= klrs.rng << 5;
    return (klrs.rng & 0xffffff) / 16777216.0f;
}

/* the cracked lens (6). now = GetTickCount; hit = the health fell this tick; health = share 0..1; clear = the situation ended */
static void klrs_crack_tick(DWORD now, int hit, float health, int clear)
{
    int i, n, recent = 0;
    if (!klrs.crack_on) return;
    if (clear) {
        if (klrs.crack_n && klrs.log) klog("reshade: lens crack: %ld crack(s) cleared (death, respawn, new round, level load or a big health refill)", (long)klrs.crack_n);
        klrs.crack_n = 0; klrs.nhit = 0; klrs.crack_last = 0; klrs_val[KLRS_U_CRACKN] = 0;
        return;
    }
    if (!hit) return;
    if (klrs.nhit >= 32) { memmove(klrs.hit_t, klrs.hit_t + 1, 31 * sizeof(DWORD)); klrs.nhit = 31; }
    klrs.hit_t[klrs.nhit++] = now;
    for (i = 0; i < klrs.nhit; i++) if (now - klrs.hit_t[i] <= (DWORD)(klrs.crack_win * 1000.0f)) recent++;
    if (recent < klrs.crack_hits && !(health < klrs.crack_hp && recent >= 2)) return;
    klrs.nhit = 0;                                       /* one roll per burst */
    n = (int)klrs.crack_n;
    if (n >= klrs.crack_max) return;
    if (klrs.crack_last && now - klrs.crack_last < (DWORD)(klrs.crack_cool * 1000.0f)) return;
    {
        float roll = klrs_rnd() * 100.0f;
        if (roll >= klrs.crack_chance) { if (klrs.log >= 2) klog("reshade: lens crack: roll %.0f >= %.0f, no crack (%d hits, health %.0f %%)", roll, klrs.crack_chance, recent, health * 100.0f); return; }
    }
    /* the place: a corner (both axes near an edge) or an edge (one axis near, the other free); 0.06 .. 0.32 from the edge */
    {
        float ex = 0.06f + 0.26f * klrs_rnd() * klrs_rnd(), ey = 0.06f + 0.26f * klrs_rnd() * klrs_rnd(), x, y;
        int corner = klrs_rnd() < 0.5f, sx = klrs_rnd() < 0.5f, sy = klrs_rnd() < 0.5f, ax = klrs_rnd() < 0.5f;
        x = sx ? ex : 1.0f - ex; y = sy ? ey : 1.0f - ey;
        if (!corner) { if (ax) y = 0.15f + 0.7f * klrs_rnd(); else x = 0.15f + 0.7f * klrs_rnd(); }
        klrs.crack[n].x = x; klrs.crack[n].y = y;
        klrs.crack[n].size = 0.17f + 0.14f * klrs_rnd();
        klrs.crack[n].inten = 0.75f + 0.25f * klrs_rnd();
        klrs.crack[n].birth = now;
        klrs.crack_last = now;
        klrs.crack_n = n + 1;                            /* published last */
        klrs_val[KLRS_U_CRACKN] = (float)(n + 1);
        if (klrs.log) klog("reshade: lens crack %d at (%.2f, %.2f) size %.2f intensity %.2f (%d hits in %.1f s, health %.0f %%)", n + 1, x, y, klrs.crack[n].size, klrs.crack[n].inten, recent, klrs.crack_win, health * 100.0f);
    }
}

/* the game thread, every tick: the numbers the shaders get (reads only) */
static void klrs_tick(int game_thread)
{
    static DWORD last, lastpl, lastw, lasth; static float hp0 = -1, mx0 = -1, pos0[3]; static int rounds0 = -1, havepos;
    static DWORD logat, lastshot, reload_until; static int reloaded;
    DWORD now, gd, pl = 0, h, d, inv, vt, ds = 0, hand = 0, arr = 0, cnt = 0, e[4], w = 0, raw; BYTE idx = 0xff, mode = 0;
    float dt, fire, hurt, speed, health = 1.0f, pos[3], cur, mx; int hit = 0, clear = 0;
    if (!klrs.on || !game_thread || !klh_exe_ok) return;
    now = GetTickCount();
    dt = last ? (now - last) / 1000.0f : 0.0f; last = now;
    if (dt < 0 || dt > 0.5f) dt = 0.5f;
    fire = klrs_val[KLRS_U_FIRE] - dt / klrs.fire_s; if (fire < 0) fire = 0;
    hurt = klrs_val[KLRS_U_HURT] - dt / klrs.hurt_s; if (hurt < 0) hurt = 0;
    speed = klrs_val[KLRS_U_SPEED];
    if ((gd = klh_rd32((DWORD_PTR)KLH_VA(KLR_GAMEDATA))) != 0 && klh_rd(gd + 0x898, &idx, 1) && (signed char)idx >= 0 && idx <= 31 &&
        (pl = klh_rd32(gd + 0x828 + 4 * idx)) != 0 && klh_rd32(pl) != KLR_PLAYER_VT) pl = 0;
    if (pl != lastpl) { lastpl = pl; hp0 = mx0 = -1; rounds0 = -1; havepos = 0; lastw = lasth = 0; clear = 1; }
    if (!pl) {
        clear = 1;
        klrs_val[KLRS_U_DOWN] = 0; klrs_val[KLRS_U_HEALTH] = 1.0f; speed -= speed * (dt / 0.2f > 1 ? 1 : dt / 0.2f);
    } else {
        /* health: [player+0xa48] (klbalance.c 2b) */
        if ((h = klh_rd32(pl + 0xa48)) != 0 && klh_rd32(h + 0x24) == pl && klh_rd(h + 4, &cur, 4) && klh_rd(h + 8, &mx, 4) && cur == cur && mx == mx && mx >= 1 && mx < 100000) {
            if (h == lasth && hp0 >= 0 && mx == mx0 && cur < hp0 - 0.01f) { hurt += (hp0 - cur) / mx * klrs.hurt_gain; hit = (hp0 - cur) >= 0.01f * mx; }
            if (h != lasth || cur <= 0 || (hp0 >= 0 && mx == mx0 && cur > hp0 + 0.25f * mx)) clear = 1;   /* a jump, not regen: a respawn or new round on a reused object */
            hp0 = cur; mx0 = mx; lasth = h;
            health = cur <= 0 ? 0 : cur >= mx ? 1 : cur / mx;
        }
        klrs_val[KLRS_U_HEALTH] = health;
        /* down: [[player+0x2948]+4] (kldown.c) */
        if ((d = klh_rd32(pl + 0x2948)) != 0 && klh_rd32(d) == pl) klh_rd(d + 4, &ds, 4);
        klrs_val[KLRS_U_DOWN] = ds ? 1.0f : 0.0f;
        if (ds) hit = 0;                                 /* bleeding out is no hit */
        /* speed: the feet (kljoin.c), x and z (y is up), 100 units a metre */
        if (klh_rd(pl + 0x460, pos, 12) && pos[0] == pos[0] && pos[2] == pos[2]) {
            if (havepos && dt > 0.001f) {
                float dx = pos[0] - pos0[0], dz = pos[2] - pos0[2], v = (float)sqrt(dx * dx + dz * dz) / 100.0f / dt, tgt, a;
                if (v < 40.0f) { tgt = v / klrs.speed_full; if (tgt > 1) tgt = 1; a = dt / 0.2f; if (a > 1) a = 1; speed += (tgt - speed) * a; }
            }
            pos0[0] = pos[0]; pos0[1] = pos[1]; pos0[2] = pos[2]; havepos = 1;
        }
        /* fire: the magazine of the gun in his hand (klhud_weapon.c's reading) */
        if (klh_rd(pl + 0x920, &hand, 4) && hand > 0 && hand < 64 && (inv = klh_rd32(pl + 0xcec)) != 0 &&
            klh_rd(inv + 4, &mode, 1) && klh_rd(inv + 8, &arr, 4) && klh_rd(inv + 0xc, &cnt, 4) && arr) {
            if (!mode) { if (klh_rd(arr + 16 * hand, e, sizeof e)) w = e[2]; }
            else if (cnt <= 256) { DWORD i; for (i = 0; i < cnt; i++) if (klh_rd(arr + 16 * i, e, sizeof e) && e[0] == hand) { w = e[2]; break; } }
        }
        if (w && klh_rd(w, &vt, 4) && klu_rdata_ptr(vt) && klh_rd32((DWORD_PTR)KLH_VA(vt + 0x2fc)) == 0x00511f50u && klh_rd(w + 0xdc, &raw, 4) && (raw ^= 0xbeebbeebu) <= 9999) {
            if (w == lastw && rounds0 >= 0 && (int)raw < rounds0 && rounds0 - (int)raw <= 12) { fire += (rounds0 - (int)raw) * klrs.fire_per; lastshot = now; }
            else if (w == lastw && rounds0 >= 0 && (int)raw > rounds0) {
                /* the magazine went UP on the same gun = a reload finished (GUESS: the count is set at the end of the reload, not rising during it; the
                   start of a reload is not detected - no state field found - so the floor covers the time after the last shot, see below) */
                reload_until = now + (DWORD)(klrs.reload_tail * 1000.0f); lastshot = 0; reloaded++;
                if (klrs.log >= 2) klog("reshade: reload seen (magazine %d -> %d), KL_Fire floor %.2f for %.1f s more", rounds0, (int)raw, klrs.reload_lvl, klrs.reload_tail);
            }
            rounds0 = (int)raw; lastw = w;
        } else { rounds0 = -1; lastw = 0; }
    }
    if (klrs.reload_on && pl && w && ((lastshot && now - lastshot <= (DWORD)(klrs.reload_hold * 1000.0f)) || (int)(reload_until - now) > 0) && fire < klrs.reload_lvl) fire = klrs.reload_lvl;
    klrs_crack_tick(now, hit, health, clear);
    klrs_val[KLRS_U_FIRE] = fire > 1 ? 1 : fire;
    klrs_val[KLRS_U_HURT] = hurt > 1 ? 1 : hurt;
    klrs_val[KLRS_U_SPEED] = speed < 0.001f ? 0 : speed > 1 ? 1 : speed;
    if (klrs.log >= 2 && now - logat >= 2000) {
        logat = now;
        klog("reshade: KL_Fire %.2f KL_Hurt %.2f KL_Down %.0f KL_Speed %.2f KL_Health %.2f (%d uniform handle(s))", klrs_val[0], klrs_val[1], klrs_val[2], klrs_val[3], klrs_val[4], klrs.nu);
    }
}

#endif
