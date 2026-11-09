/* kl_oggdec.c - tiny Ogg Vorbis -> 16-bit WAV decoder for the KL Merge launcher (wraps stb_vorbis.c, public domain).
 *   kl_oggdec.exe -            Ogg stream on stdin, RIFF/WAVE 16-bit PCM on stdout (rate/channels of the stream)
 *   kl_oggdec.exe in.ogg       same, from a file
 * exit 0 = ok, 1 = usage / read error, 2 = not decodable. Nothing is written to stdout on failure. */
#define STB_VORBIS_NO_PUSHDATA_API
#include "stb_vorbis.c"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
static void le32(unsigned char *p, unsigned v) { p[0]=(unsigned char)v; p[1]=(unsigned char)(v>>8); p[2]=(unsigned char)(v>>16); p[3]=(unsigned char)(v>>24); }
int main(int argc, char **argv)
{
    FILE *in; unsigned char *buf = NULL; size_t cap = 0, len = 0, n;
    int ch = 0, rate = 0, frames; short *pcm = NULL; unsigned char h[44]; unsigned bytes;
    if (argc != 2) { fprintf(stderr, "usage: kl_oggdec (- | in.ogg) > out.wav\n"); return 1; }
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY); _setmode(_fileno(stdout), _O_BINARY);
#endif
    in = strcmp(argv[1], "-") ? fopen(argv[1], "rb") : stdin;
    if (!in) { fprintf(stderr, "cannot open %s\n", argv[1]); return 1; }
    for (;;) {
        if (len + 65536 > cap) { cap = cap ? cap * 2 : 1 << 20; buf = (unsigned char *)realloc(buf, cap); if (!buf) return 1; }
        n = fread(buf + len, 1, 65536, in); if (!n) break; len += n;
    }
    frames = stb_vorbis_decode_memory(buf, (int)len, &ch, &rate, &pcm);
    if (frames <= 0 || ch < 1 || ch > 2 || !pcm) { fprintf(stderr, "not decodable (%d)\n", frames); return 2; }
    bytes = (unsigned)frames * ch * 2;
    memcpy(h, "RIFF", 4); le32(h + 4, 36 + bytes); memcpy(h + 8, "WAVEfmt ", 8); le32(h + 16, 16);
    h[20] = 1; h[21] = 0; h[22] = (unsigned char)ch; h[23] = 0; le32(h + 24, rate); le32(h + 28, rate * ch * 2);
    h[32] = (unsigned char)(ch * 2); h[33] = 0; h[34] = 16; h[35] = 0; memcpy(h + 36, "data", 4); le32(h + 40, bytes);
    fwrite(h, 1, 44, stdout); fwrite(pcm, 1, bytes, stdout); fflush(stdout);
    return 0;
}
