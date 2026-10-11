/* Microsoft IMA ADPCM (WAVE_FORMAT_IMA_ADPCM, 0x11) block decoder -> 16-bit PCM, interleaved */
#ifndef ANP_ADPCM_H
#define ANP_ADPCM_H
static const int ima_step[89] = {7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,
 130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,
 1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,
 15289,16818,18500,20350,22385,24623,27086,29794,32767};
static const int ima_idx[16] = {-1,-1,-1,-1,2,4,6,8,-1,-1,-1,-1,2,4,6,8};
static inline short ima_nib(int *pred, int *idx, int n) {
    int step = ima_step[*idx], diff = step >> 3;
    if (n & 1) diff += step >> 2;
    if (n & 2) diff += step >> 1;
    if (n & 4) diff += step;
    if (n & 8) *pred -= diff; else *pred += diff;
    if (*pred > 32767) *pred = 32767; else if (*pred < -32768) *pred = -32768;
    *idx += ima_idx[n & 15]; if (*idx < 0) *idx = 0; else if (*idx > 88) *idx = 88;
    return (short)*pred;
}
/* decode one block (blockAlign bytes, ch channels) into out[spb*ch]; returns samples per channel written */
static int ima_decode_block(const unsigned char *in, int balign, int ch, short *out, int spb) {
    int pred[8], idx[8];
    if (ch < 1 || ch > 8 || balign < 4 * ch) return 0;
    for (int c = 0; c < ch; c++) {
        pred[c] = (short)(in[4*c] | (in[4*c+1] << 8)); idx[c] = in[4*c+2]; if (idx[c] > 88) idx[c] = 88;
        out[c] = (short)pred[c];
    }
    int s = 1; const unsigned char *p = in + 4 * ch, *end = in + balign;
    while (p + 4 * ch <= end && s < spb) {
        for (int c = 0; c < ch; c++) {
            for (int k = 0; k < 4; k++) {
                int b = p[4*c + k];
                int s0 = s + 2*k, s1 = s0 + 1;
                short v0 = ima_nib(&pred[c], &idx[c], b & 15);
                short v1 = ima_nib(&pred[c], &idx[c], b >> 4);
                if (s0 < spb) out[s0*ch + c] = v0;
                if (s1 < spb) out[s1*ch + c] = v1;
            }
        }
        p += 4 * ch; s += 8;
    }
    return s < spb ? s : spb;
}
#endif
