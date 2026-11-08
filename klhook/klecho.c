/*
 * klecho.c - [Echo]: room reverb that follows the place (2026-11-07, owner: "make gun shots more echoy or just adaptive to the
 * environment"). Part of KLHook (included by klhook.c after klambience.c, SHIP and TEST alike). OFF unless [Echo] Enable=1.
 *
 * WHAT: Dog Days has ONE global OpenAL EFX reverb slot. ZSynthOpenAL::SetReverb (0x5fff30) pushes the current room's roomeffect into it
 * with 12 alEffectf calls through the function pointer at 0x14f356c (a .data global, filled at init by alGetProcAddress("alEffectf")
 * at 0x521416). This file swaps that DATA pointer for a wrapper that lengthens the decay and lifts the reflections / late tail per
 * kind of room (indoor / street / roof / hall, klecho_logic.h) and calls the real function. Nothing else changes: no code byte is
 * written (a SHIP build may write data), nothing in the game's files. Every sound with an aux send follows (guns, footsteps, voices,
 * explosions); that is the "adaptive" part. Works the same on the 9 stock FA maps, the Dead Men maps (once they carry reverb boxes,
 * re/gun_echo_1107.md) and online (the same exe plays an online round).
 *
 * GUESS / NOT VERIFIED IN THE GAME (2026-11-07, offline, nothing was launched): whether a gun voice carries the aux send. Static reading
 * 2026-11-08 (re/gun_echo_1107.md section 6): a world (3D) voice gets the send at creation unless its sound flag bit 5 is set; a 2D / relative
 * voice only with flag bit 6. Which flag the gun sounds carry is what [Echo] Probe=1 answers in one bench run.
 * [Echo] Log=1 writes one line per distinct room effect ("echo: roof decay 1.49->2.38 refl 0.052->0.104 late ...").
 *
 * KLHook.ini
 *   [Echo]
 *   ; Room reverb follows the place: longer decay + stronger tail per room kind (recommended on once the owner has listened)
 *   Enable=0
 *   ; global strength in percent, 100 = the curve in klecho_logic.h, 0 = the engine's own values, up to 300
 *   Strength=100
 *   ; per kind percent of that curve (indoor = small tight rooms, street = between buildings, roof = open area, hall = big covered)
 *   IndoorPct=100  StreetPct=100  RoofPct=100  HallPct=100
 *   Log=1
 *   ; Bench probe, logs only, changes no sound (recommended off): per played source, is the EFX aux send attached, and which sound is it
 *   ; (gunshots vs the rest); every SetReverb room change; the reverb-box stack ('echo-stack', re/reverb_path_1108.md). Works with Enable=0 or 1.
 *   ; Recipe: re/gun_echo_1107.md section 7.
 *   Probe=0
 */
#ifndef KLECHO_C
#define KLECHO_C

#include "klecho_logic.h"
#include "klechoprobe_logic.h"

#define KLECHO_SLOT 0x14f356cu                               /* alEffectf pointer (kl2.exe .data) */
/* Reverb stack of the audio manager (re/reverb_path_1108.md, static reading 2026-11-08; read only, Probe=1 only). AUD = [[0xdd2640]+0xb00];
 * Audio_ReverbActivater's Enter (0x8cfe30 -> Push 0x765c70) is the ONLY writer; empty stack = the I3DL2 default every frame (decay 1.49). */
#define KLECHO_GAME     0xdd2640u
#define KLECHO_AUD      0xb00u
#define KLECHO_STK_N    0x68fcu                              /* count, max 20 */
#define KLECHO_STK_E    0x680cu                              /* entries {effect ptr, key, priority float}, stride 12 */
#define KLECHO_STK_TOP  0x6900u                              /* cached top = effect ptr of entry n-1 (getter 0x429b60; sorted by priority, n-1 drives the reverb) */
#define KLECHO_GATE     0xcdd93cu                            /* listener reverb update runs only when this is 1 (0x4a2d5e) */

static struct klecho_cfg klecho_c = { 100, { 100, 100, 100, 100, 100 } };
static struct klecho_st klecho_s;
static int klecho_on, klecho_log = 1, klecho_logn, klecho_installed, klecho_probe;
static LONG klecho_calls;
static float klecho_o[3], klecho_n[3];                       /* decay, reflections, late: engine value / ours (for the log line) */
static float klecho_seen[24][2]; static int klecho_nseen;    /* dedupe of the log: (kind, decay) */
typedef void (__cdecl *klecho_al_fn)(unsigned, int, float);
static klecho_al_fn klecho_real;
static int klecho_room_lines; static LONG klecho_room_n;

static void __cdecl klecho_wrap(unsigned eff, int param, float v)
{
    float nv = v;
    if ((klecho_on || klecho_probe) && param >= 1 && param <= 12) {
        if (klecho_on) nv = klecho_value(&klecho_c, &klecho_s, param, v);
        else if (param == 5) klecho_s.kind = klecho_kind(v, 0, 0);          /* probe only: the kind is still named in the log, nothing changes */
        else if (param == 7) klecho_s.kind = klecho_kind(klecho_o[0], v, 1);
        if (param == 5) { klecho_o[0] = v; klecho_n[0] = nv; }
        if (param == 7) { klecho_o[1] = v; klecho_n[1] = nv; }
        if (param == 9) { klecho_o[2] = v; klecho_n[2] = nv; }
        if (param == 10 && klecho_probe && klecho_room_lines < 300) {   /* every room change, not deduped: when the room changes matters next to the plays */
            static const char *nm[5] = { "none", "indoor", "street", "roof", "hall" };
            klecho_room_lines++;
            klog("echo-room #%ld t %lu: %s engine decay %.2f refl %.3f late %.3f delay %.3f -> sent decay %.2f refl %.3f late %.3f delay %.3f%s",
                 InterlockedIncrement(&klecho_room_n), (unsigned long)GetTickCount(), nm[klecho_s.kind > 4 ? 0 : klecho_s.kind],
                 klecho_o[0], klecho_o[1], klecho_o[2], v, klecho_n[0], klecho_n[1], klecho_n[2], nv, klecho_on ? "" : " (Enable=0: unchanged)");
        }
        if (param == 10 && klecho_on && klecho_log && klecho_logn < 60) {
            int i, dup = 0; float key = klecho_o[0] * 1000.0f + klecho_o[1];
            for (i = 0; i < klecho_nseen; i++) if (klecho_seen[i][0] == (float)klecho_s.kind && klecho_seen[i][1] == key) dup = 1;
            if (!dup && klecho_nseen < 24) {
                static const char *nm[5] = { "none", "indoor", "street", "roof", "hall" };
                klecho_seen[klecho_nseen][0] = (float)klecho_s.kind; klecho_seen[klecho_nseen][1] = key; klecho_nseen++; klecho_logn++;
                klog("echo: %s decay %.2f->%.2f refl %.3f->%.3f late %.3f->%.3f (late delay %.3f->%.3f)", nm[klecho_s.kind], klecho_o[0], klecho_n[0],
                     klecho_o[1], klecho_n[1], klecho_o[2], klecho_n[2], v, nv);
            }
        }
        InterlockedIncrement(&klecho_calls);
    }
    if (klecho_real) klecho_real(eff, param, nv);
}

/* ---- [Echo] Probe (2026-11-08, TEST / bench only, "(recommended off)"): do gun voices carry the aux send? ----
 * Wraps two OpenAL IMPORT slots of kl2.exe (alSourcePlay, alSource3i; klh_iat: an import slot, no code byte) and logs per played source
 * whether the EFX aux send (AL_AUXILIARY_SEND_FILTER 0x20006) is attached, with the sound's name when the voice object can give one
 * (klechoprobe_logic.h has the voice layout read from kl2.exe). Nothing here changes a sound.
 *   - alSourcePlay wrapper: the caller is ZSoundBufferOpenAL::Play 0x5dbd50 (return address 0x5dbe18); that function keeps the voice in esi
 *     (mov esi,ecx) across the call, so the voice is read from ESI by a naked stub (it is not on the stack: fr[3] is the caller's saved esi).
 *     Validated: vtable 0xb9ad5c and voice+0x43bc == the source id, else the play is logged "(foreign ret ...)" (other alSourcePlay
 *     callers: 0x43d3bb, 0x4893ca). The send is read back with alGetSource3i(src, 0x20006) before the real Play. GUESS: OpenAL32.dll
 *     exports alGetSource3i (AL 1.1 core); if not, the state is predicted from the voice flags and the log line says so.
 *   - alSource3i wrapper: sees the late attach (Play attaches the send AFTER alSourcePlay for relative / 2D voices) and marks the pending play.
 *   - the sound's name: the descriptor at voice+0x60 is a .WHD record minus 4 (decoded 2026-11-08, re/gun_echo_1107.md section 8); the wave file name
 *     is the 16-aligned string before it (kpr_name_before; GUESS that the loaded image keeps the file layout). Fallbacks: the best-scoring printable
 *     string behind a pointer field of the descriptor (+0..+0x3c), else of the voice (+0x18..+0x7c). The first 12 plays log a hex dump of both so the layout can be
 *     decoded from the log if the guess fails.
 * Log lines: "echo-probe play ..." (budgeted by kpr_log), "echo-probe 10s: ..." / "total: ..." every 10 s while plays happen, "echo-room ..." per SetReverb. */
#define KLECHO_PLAY_RET 0x5dbe18u                            /* return address inside ZSoundBufferOpenAL::Play after alSourcePlay */
#define KLECHO_VT_VOICE 0xb9ad5cu                            /* ZSoundBufferOpenAL vtable */
typedef void (__cdecl *klecho_play_fn)(unsigned);
/* The descriptor at voice+0x60 is a .WHD record minus 4 (see kpr_name_before): its wave file name ("SFX/.../x.wav") is the 16-aligned string just
   before it in the loaded .WHD image. Reads 0x100 bytes before the descriptor, guarded (shorter windows near a page start); 0 = not found. */
static int klecho_wave_name(DWORD_PTR d, char *out, int cap)
{
    unsigned char buf[0x100]; int n;
    out[0] = 0;
    if (d < 0x10000u || (d & 3) || d >= 0x7fff0000u) return 0;
    for (n = 0x100; n >= 0x40; n -= 0x40) {
        memset(buf, 0, sizeof buf);
        if (klh_rd(d - (DWORD_PTR)n, buf, (SIZE_T)n)) return kpr_name_before(buf, n, out, cap);
    }
    return 0;
}

static void __cdecl klecho_play_wrap2(unsigned src, DWORD esi_in, DWORD ret);
typedef void (__cdecl *klecho_s3i_fn)(unsigned, int, int, int, int);
typedef void (__cdecl *klecho_gs3i_fn)(unsigned, int, int *, int *, int *);
typedef int (__cdecl *klecho_err_fn)(void);
static klecho_play_fn klecho_real_play;
static klecho_s3i_fn klecho_real_s3i;
static klecho_gs3i_fn klecho_gs3i;
static klecho_err_fn klecho_gerr;
static int klecho_probe_ok, klecho_got_play, klecho_got_s3i;
static struct kpr_stats klecho_ps10, klecho_psall;
static struct kpr_log klecho_pl = { {0}, 0, 0, 40, 500 };
static volatile LONG klecho_plock;
static DWORD klecho_p10;                                      /* GetTickCount of the last 10 s summary */
static int klecho_dumps;
static LONG klecho_attach_all, klecho_attach_null;
static struct { unsigned src; int late, with, unknown; char name[KPR_NAMELEN]; } klecho_pend;   /* the play whose late attach may still come */

static void klecho_lock(void) { while (InterlockedCompareExchange(&klecho_plock, 1, 0)) Sleep(0); }
static void klecho_unlock(void) { InterlockedExchange(&klecho_plock, 0); }

/* a play is final when the next play or the summary tick sees it (its late send, if any, came right after its Play). Caller holds the lock. */
static void klecho_flush_pend(void)
{
    if (!klecho_pend.src) return;
    kpr_add(&klecho_ps10, klecho_pend.name, klecho_pend.with, klecho_pend.late, klecho_pend.unknown);
    kpr_add(&klecho_psall, klecho_pend.name, klecho_pend.with, klecho_pend.late, klecho_pend.unknown);
    klecho_pend.src = 0;
}

/* the best-scoring printable string behind a dword in [p, p+len); 0 = none, out = "" then */
static int klecho_find_name(DWORD_PTR p, int len, char *out, int cap)
{
    int i, best = 0; char cand[KPR_NAMELEN]; unsigned char win[64];
    out[0] = 0;
    if (!p) return 0;
    for (i = 0; i + 4 <= len; i += 4) {
        DWORD v = klh_rd32(p + (DWORD_PTR)i);
        if (v < 0x10000u || v >= 0x7fff0000u) continue;
        memset(win, 0, sizeof win);
        if (!klh_rd(v, win, 63)) { int k; for (k = 32; k >= 8; k -= 8) if (klh_rd(v, win, (SIZE_T)k)) break; if (k < 8) continue; }   /* a string near the end of a page */
        if (kpr_name_from(win, 64, cand, cap)) {
            int sc = kpr_name_score(cand);
            if (sc > best) { best = sc; strcpy(out, cand); }
        }
    }
    return best;
}

static void __cdecl klecho_play_wrap2(unsigned src, DWORD esi_in, DWORD ret)
{
    DWORD voice = 0, wave = 0; int sent = -1, pred = 0, rel = -1, s3d = -1, s2d = -1, kind = -1, state, late = 0, unknown = 0;
    float gain = -1.0f; char name[KPR_NAMELEN] = "(unreadable)";
    if (klecho_probe_ok && klh_exe_ok) {
        if (ret == (DWORD)(DWORD_PTR)KLH_VA(KLECHO_PLAY_RET)) {
            DWORD cand = esi_in, vt = 0, id = 0;
            klh_rd(cand, &vt, 4); klh_rd(cand + 0x43bc, &id, 4);
            if (vt == (DWORD)(DWORD_PTR)KLH_VA(KLECHO_VT_VOICE) && id == src) voice = cand;
        }
        if (voice) {
            BYTE b10 = 0, b11 = 0; DWORD r54 = 0, k78 = 0, g = 0;
            klh_rd(voice + 0x10, &b10, 1); klh_rd(voice + 0x11, &b11, 1); klh_rd(voice + 0x54, &r54, 4); klh_rd(voice + 0x78, &k78, 4);
            klh_rd(voice + 0x5c, &g, 4); klh_rd(voice + 0x60, &wave, 4);
            rel = r54 != 0; s3d = b10 != 0; s2d = b11 != 0; kind = (int)k78; memcpy(&gain, &g, 4);
            if (!klecho_wave_name(wave, name, sizeof name) && !klecho_find_name(wave, 0x3c, name, sizeof name)) klecho_find_name(voice + 0x18, 0x64, name, sizeof name);
            if (!name[0]) snprintf(name, sizeof name, "(unnamed k%d)", kind);
        } else snprintf(name, sizeof name, "(foreign ret %06lx)", (unsigned long)(ret - (DWORD)klh_delta));
    }
    if (klecho_gs3i && klecho_probe_ok) {                        /* what is attached right now: 3D voices got it at creation, relative ones get it right after this call */
        int a = 0, b = 0, c = 0; klecho_gs3i(src, 0x20006, &a, &b, &c);
        sent = a != 0;
        if (klecho_gerr && klecho_gerr()) sent = -1;             /* our query must not leave an AL error for the engine's next alGetError; an error = the readback is not trustworthy (a=0 would read as NO SEND) */
    }
    pred = voice ? kpr_predict(rel, s3d, s2d, 1) : 0;            /* efx listener assumed present: the aux slot exists once SetReverb ran */
    if (sent < 0) { unknown = 1; sent = pred == 1; }
    late = !sent && pred == 2;
    state = sent ? 1 : late ? 2 : 0;
    klecho_lock();
    klecho_flush_pend();
    klecho_pend.src = src; klecho_pend.with = sent || late; klecho_pend.late = late; klecho_pend.unknown = unknown;
    strncpy(klecho_pend.name, name, KPR_NAMELEN - 1); klecho_pend.name[KPR_NAMELEN - 1] = 0;
    if (kpr_log_ok(&klecho_pl, name, state)) {
        klog("echo-probe play src %u %s: %s%s | rel %d send3d %d send2d %d kind %d gain %.2f pred %d%s%s", src, voice ? "voice" : "other",
             name, kpr_gunish(name) ? " [gun-like]" : "", rel, s3d, s2d, kind, gain, pred,
             sent ? " | SEND ATTACHED" : late ? " | send expected right after play (2D voice)" : " | NO SEND", unknown ? " (readback unavailable: predicted)" : "");
        if (voice && klecho_dumps < 12) {
            char line[400]; int i, n = 0;
            klecho_dumps++;
            for (i = 0; i < 16; i++) n += snprintf(line + n, sizeof line - (size_t)n, " %08lx", (unsigned long)klh_rd32((DWORD_PTR)wave + (DWORD_PTR)i * 4));
            klog("echo-probe dump voice %08lx wave %08lx:%s", (unsigned long)voice, (unsigned long)wave, line);
            for (n = 0, i = 0; i < 16; i++) n += snprintf(line + n, sizeof line - (size_t)n, " %08lx", (unsigned long)klh_rd32((DWORD_PTR)voice + 0x18 + (DWORD_PTR)i * 4));
            klog("echo-probe dump voice+0x18:%s", line);
        }
    }
    klecho_unlock();
    if (klecho_real_play) klecho_real_play(src);
}

/* The voice is NOT on the stack: Play (0x5dbd50) does push esi / mov esi,ecx, so [esp+0xc] in the wrapper is the CALLER's saved esi.
 * (Review 2026-11-08 fixed the first version, which read fr[3].) The voice is still live in ESI when Play calls alSourcePlay, and ESI is
 * untouched on entry here, so a naked stub passes (src, esi, return address) on to klecho_play_wrap2. */
static void __declspec(naked) klecho_play_wrap(void)
{
    __asm {
        push dword ptr [esp]            ; return address
        push esi                        ; the voice (ZSoundBufferOpenAL this) when the caller is Play
        push dword ptr [esp+12]         ; src
        call klecho_play_wrap2
        add esp, 12
        ret
    }
}

static void __cdecl klecho_s3i_wrap(unsigned src, int param, int a, int b, int c)
{
    if (klecho_probe_ok && param == 0x20006) {
        InterlockedIncrement(&klecho_attach_all); if (!a) InterlockedIncrement(&klecho_attach_null);
        klecho_lock();
        if (klecho_pend.src == src && a && !klecho_pend.with) { klecho_pend.with = 1; klecho_pend.late = 1; }   /* the send Play attaches after alSourcePlay */
        klecho_unlock();
    }
    if (klecho_real_s3i) klecho_real_s3i(src, param, a, b, c);
}

/* Probe: does any Audio_ReverbActivater ever push onto the stack? Logs each change of (count, top), capped, plus a 10 s state line. */
/* A count that stays 0 means no Push survived to a tick (a Push + Remove inside one frame is missed); AUD rebuilt on a map load is logged. */
static DWORD klecho_stk_n = 0xffffffffu, klecho_stk_top, klecho_stk_aud, klecho_stk_t10; static int klecho_stk_lines; static LONG klecho_stk_changes;
static void klecho_stack_probe(DWORD now)
{
    DWORD game = klh_rd32((DWORD_PTR)KLH_VA(KLECHO_GAME)), aud = game ? klh_rd32(game + KLECHO_AUD) : 0, n, top;
    if (!aud) return;                                        /* audio manager not up yet */
    if (aud != klecho_stk_aud) {
        klog("echo-stack: audio manager %08lx -> %08lx", (unsigned long)klecho_stk_aud, (unsigned long)aud);
        klecho_stk_aud = aud;
    }
    n = klh_rd32(aud + KLECHO_STK_N); top = klh_rd32(aud + KLECHO_STK_TOP);
    if (n != klecho_stk_n || top != klecho_stk_top) {
        klecho_stk_changes++;
        if (klecho_stk_lines < 200) {
            DWORD_PTR e = aud + KLECHO_STK_E + 12 * (n ? (n > 20 ? 19 : n - 1) : 0);      /* the active (highest) entry; max 20 */
            DWORD ef = n ? klh_rd32(e) : 0, ky = n ? klh_rd32(e + 4) : 0, pr = n ? klh_rd32(e + 8) : 0;
            float pf; memcpy(&pf, &pr, 4);
            klecho_stk_lines++;
            klog("echo-stack #%ld t %lu: count %lu -> %lu, top %08lx -> %08lx; active entry effect %08lx key %08lx prio %.1f",
                 (long)klecho_stk_changes, (unsigned long)now, (unsigned long)(klecho_stk_n == 0xffffffffu ? 0 : klecho_stk_n), (unsigned long)n,
                 (unsigned long)klecho_stk_top, (unsigned long)top, (unsigned long)ef, (unsigned long)ky, pf);
        }
        klecho_stk_n = n; klecho_stk_top = top;
    }
    if (now - klecho_stk_t10 >= 10000u) {
        klecho_stk_t10 = now;
        klog("echo-stack: count %lu top %08lx, changes %ld, gate [%08lx]=%lu (1 = listener reverb update on)", (unsigned long)n, (unsigned long)top,
             (long)klecho_stk_changes, (unsigned long)KLECHO_GATE, (unsigned long)klh_rd32((DWORD_PTR)KLH_VA(KLECHO_GATE)));
    }
}

static void klecho_probe_tick(void)
{
    DWORD now = GetTickCount();
    klecho_stack_probe(now);
    if (!klecho_probe_ok) {
        HMODULE al = GetModuleHandleA("OpenAL32.dll");
        if (!al) return;
        if (!klecho_gs3i) klecho_gs3i = (klecho_gs3i_fn)(void *)GetProcAddress(al, "alGetSource3i");
        if (!klecho_gerr) klecho_gerr = (klecho_err_fn)(void *)GetProcAddress(al, "alGetError");
        if (!klecho_got_play && klh_iat("OpenAL32.dll", "alSourcePlay", (void *)klecho_play_wrap, (void **)&klecho_real_play)) klecho_got_play = 1;   /* each once: a retry would find the slot already ours */
        if (!klecho_got_s3i && klh_iat("OpenAL32.dll", "alSource3i", (void *)klecho_s3i_wrap, (void **)&klecho_real_s3i)) klecho_got_s3i = 1;
        if (klecho_got_play && klecho_got_s3i) {
            klecho_probe_ok = 1; klecho_p10 = now;
            klog("echo-probe: wrapped alSourcePlay + alSource3i (import slots); alGetSource3i %s, alGetError %s",
                 klecho_gs3i ? "found" : "MISSING (state predicted from the voice flags only)", klecho_gerr ? "found" : "MISSING");
        }                                                        /* imports not resolved yet, or refused: retried next tick (klh_iat logs a refusal) */
        return;
    }
    if (now - klecho_p10 >= 10000u) {
        char line[700];
        klecho_p10 = now;
        klecho_lock();
        klecho_flush_pend();
        if (klecho_ps10.played) {
            kpr_summary(&klecho_ps10, "10s", line, sizeof line, 4);
            klog("%s | send attaches seen %ld (null slot %ld)", line, (long)klecho_attach_all, (long)klecho_attach_null);
            kpr_summary(&klecho_psall, "total", line, sizeof line, 4); klog("%s", line);
            kpr_init(&klecho_ps10);
        }
        klecho_unlock();
    }
}

static void klecho_tick(int game_thread)
{
    BYTE *slot; DWORD cur, mine = (DWORD)(DWORD_PTR)klecho_wrap;
    if (!(klecho_on || klecho_probe) || !game_thread || !klh_exe_ok) return;
    if (klecho_probe) klecho_probe_tick();
    slot = KLH_VA(KLECHO_SLOT);
    cur = klh_rd32((DWORD_PTR)slot);
    if (!cur || cur == mine) return;                         /* alEffectf not resolved yet, or already ours */
    klecho_real = (klecho_al_fn)(DWORD_PTR)cur;              /* (re)wrap: the engine may re-resolve it after an audio device reset */
    if (klh_data(slot, &mine, 4, "echo alEffectf")) {
        if (!klecho_installed++) klog("echo: wrapping alEffectf slot %08lx (was %08lx): %s strength %d, indoor/street/roof/hall %d/%d/%d/%d%%%s",
                                      (unsigned long)KLECHO_SLOT, (unsigned long)cur, klecho_on ? "ON" : "probe only (sound unchanged),", klecho_c.strength,
                                      klecho_c.pct[KLE_INDOOR], klecho_c.pct[KLE_STREET], klecho_c.pct[KLE_ROOF], klecho_c.pct[KLE_HALL], klecho_probe ? ", Probe=1" : "");
    } else klecho_real = 0;
}

static void klecho_init(void)
{
    klecho_on = GetPrivateProfileIntA("Echo", "Enable", 0, klh_ini) != 0;
    klecho_probe = GetPrivateProfileIntA("Echo", "Probe", 0, klh_ini) != 0;
    if (!klecho_on && !klecho_probe) return;
    klecho_log = GetPrivateProfileIntA("Echo", "Log", 1, klh_ini) != 0;
    klecho_c.strength = GetPrivateProfileIntA("Echo", "Strength", 100, klh_ini);
    klecho_c.pct[KLE_INDOOR] = GetPrivateProfileIntA("Echo", "IndoorPct", 100, klh_ini);
    klecho_c.pct[KLE_STREET] = GetPrivateProfileIntA("Echo", "StreetPct", 100, klh_ini);
    klecho_c.pct[KLE_ROOF] = GetPrivateProfileIntA("Echo", "RoofPct", 100, klh_ini);
    klecho_c.pct[KLE_HALL] = GetPrivateProfileIntA("Echo", "HallPct", 100, klh_ini);
    if (klecho_c.strength < 0) klecho_c.strength = 0;
    if (klecho_c.strength > 300) klecho_c.strength = 300;
    kpr_init(&klecho_ps10); kpr_init(&klecho_psall);
    klog("echo: %s%s: the engine's reverb slot is wrapped once the audio system is up", klecho_on ? "on ([Echo] Enable=1)" : "off", klecho_probe ? ", probe on ([Echo] Probe=1: logs the aux send per played source)" : "");
}

#endif /* KLECHO_C */
