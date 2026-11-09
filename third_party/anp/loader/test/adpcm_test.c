#include <stdio.h>
#include <stdlib.h>
#include "../adpcm.h"
int main(int argc, char **argv) {   /* adpcm_test in.raw balign ch spb samples out.pcm */
    FILE *f = fopen(argv[1], "rb"); fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char *d = malloc(n); fread(d, 1, n, f); fclose(f);
    int ba = atoi(argv[2]), ch = atoi(argv[3]), spb = atoi(argv[4]); long total = atol(argv[5]);
    short *blk = malloc(sizeof(short) * spb * ch); FILE *o = fopen(argv[6], "wb"); long done = 0;
    for (long off = 0; off + ba <= n && done < total; off += ba) {
        int got = ima_decode_block(d + off, ba, ch, blk, spb);
        long take = got; if (done + take > total) take = total - done;
        fwrite(blk, 2 * ch, take, o); done += take;
    }
    fclose(o); printf("decoded %ld samples\n", done); return 0;
}
