/* kladpcm_test.c - off-game checks of kladpcm.h (ported from luvsic's loader/adpcm.h @32aa649, in contribution with luvsic).
 * Build: cl /nologo /W3 kladpcm_test.c. The reference decoder below is written from the IMA ADPCM spec (a different shape
 * from the ported one: it walks sample by sample), so a table typo or an ordering slip in kladpcm.h shows as a difference. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "kladpcm.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static const int ref_step[89] = {7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,
    337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,
    8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767};
/* spec: diff = ((2*mag + 1) * step) >> 3 differs by rounding from the shift form; the IMA reference uses the shift form */
static int ref_one(int *pred, int *ix, int code)
{
    int step = ref_step[*ix], d = step >> 3;
    if (code & 4) d += step;
    if (code & 2) d += step >> 1;
    if (code & 1) d += step >> 2;
    *pred += (code & 8) ? -d : d;
    if (*pred > 32767) *pred = 32767;
    if (*pred < -32768) *pred = -32768;
    { static const int adj[8] = {-1,-1,-1,-1,2,4,6,8}; *ix += adj[code & 7]; }
    if (*ix < 0) *ix = 0;
    if (*ix > 88) *ix = 88;
    return *pred;
}
static void ref_block(const unsigned char *in, int balign, int ch, short *out, int spb)
{
    int c, s, pred[2], ix[2];
    int groups = (balign - 4 * ch) / (4 * ch);
    for (c = 0; c < ch; c++) { pred[c] = (short)(in[4*c] | (in[4*c+1] << 8)); ix[c] = in[4*c+2]; out[c] = (short)pred[c]; }
    for (s = 0; s < groups * 8 && 1 + s < spb; s++) {
        int g = s / 8, k = s % 8;
        for (c = 0; c < ch; c++) {
            unsigned char b = in[4 * ch + g * 4 * ch + c * 4 + k / 2];
            int code = (k & 1) ? (b >> 4) : (b & 15);
            out[(1 + s) * ch + c] = (short)ref_one(&pred[c], &ix[c], code);
        }
    }
}

int main(void)
{
    unsigned char blk[2048]; short a[4096], b[4096]; int i, t, ch, balign, spb, n;
    /* known vector: predictor 0, index 0, nibble 7 -> diff 0 + 1 + 3 + 7 = 11 */
    memset(blk, 0, sizeof blk); blk[4] = 0x77; blk[5] = 0x07;
    n = kladpcm_decode_block(blk, 8, 1, a, 5);
    CHECK(n == 5);
    CHECK(a[0] == 0);
    CHECK(a[1] == 11);                                   /* nibble 7, step 7 */
    CHECK(a[2] == 11 + (16 >> 3) + (16 >> 2) + (16 >> 1) + 16);   /* index moved 0 -> 8: step 16, nibble 7 again: +30 */
    /* a negative nibble: 8 | 0 = -(step >> 3) */
    memset(blk, 0, sizeof blk); blk[0] = 100; blk[2] = 20; blk[4] = 0x08;
    kladpcm_decode_block(blk, 8, 1, a, 3);
    CHECK(a[0] == 100);
    CHECK(a[1] == 100 - (ref_step[20] >> 3));
    /* clamp both ways */
    memset(blk, 0, sizeof blk); blk[0] = 0xff; blk[1] = 0x7f; blk[2] = 88; blk[4] = 0x77;   /* 32767, top step, big positive */
    kladpcm_decode_block(blk, 8, 1, a, 3);
    CHECK(a[1] == 32767);
    memset(blk, 0, sizeof blk); blk[0] = 0x00; blk[1] = 0x80; blk[2] = 88; blk[4] = 0xff;
    kladpcm_decode_block(blk, 8, 1, a, 3);
    CHECK(a[1] == -32768);
    /* index > 88 in the header is clamped, not an out-of-range read */
    memset(blk, 0, sizeof blk); blk[2] = 200; blk[4] = 0x11;
    CHECK(kladpcm_decode_block(blk, 8, 1, a, 3) == 3);
    /* random blocks against the reference, mono and stereo, the real Dead Men geometries (balign 1024, spb 2041 / 1017) */
    srand(12345);
    for (t = 0; t < 200; t++) {
        ch = 1 + (t & 1); balign = (t % 3 == 0) ? 1024 : (t % 3 == 1) ? 512 : 256;
        spb = (balign - 4 * ch) * 8 / (4 * ch) + 1;
        for (i = 0; i < balign; i++) blk[i] = (unsigned char)rand();
        blk[2] &= 0x7f; if (blk[2] > 88) blk[2] = 88; if (ch == 2) { blk[6] &= 0x7f; if (blk[6] > 88) blk[6] = 88; }
        memset(a, 0x55, sizeof a); memset(b, 0x55, sizeof b);
        n = kladpcm_decode_block(blk, balign, ch, a, spb);
        ref_block(blk, balign, ch, b, spb);
        CHECK(n == spb);
        CHECK(memcmp(a, b, (size_t)spb * ch * 2) == 0);
        CHECK(a[spb * ch] == 0x5555);                    /* nothing written past spb */
    }
    /* a short block never reads past its end and never writes past spb */
    for (i = 0; i < 64; i++) blk[i] = (unsigned char)(i * 7);
    memset(a, 0x55, sizeof a);
    n = kladpcm_decode_block(blk, 20, 1, a, 100);
    CHECK(n == 1 + 4 * 8);                               /* header sample + four 8-sample groups (20 bytes = 4 header + 4 x 4) */
    CHECK(a[100] == 0x5555);
    CHECK(kladpcm_decode_block(blk, 3, 1, a, 10) == 0);  /* too short for a header */
    CHECK(kladpcm_decode_block(blk, 64, 0, a, 10) == 0);
    CHECK(kladpcm_decode_block(blk, 64, 9, a, 10) == 0);
    CHECK(kladpcm_decode_block(blk, 64, 1, a, 0) == 0);
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
