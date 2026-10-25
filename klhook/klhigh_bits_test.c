/*
 * klhigh_bits_test.c - klhigh.c's carving bit maps on their own, any C compiler (no Windows needed): the section between
 * "bit maps" and "who called" of klhigh.c is cut out with sed and driven over two fake chunks (addresses only, nothing
 * is dereferenced). 18 checks: bounds, first fit inside one chunk, exact release by block, no double release, hole
 * reuse, fill and drain. Written and PASSED 2026-10-25 (gcc 13, Linux).
 *   sed -n '/^\/\* -\+ bit maps \*\//,/^\/\* -\+ who called \*\//p' klhigh.c | sed '$d' > bits.inc && gcc -O2 -o bits_test klhigh_bits_test.c && ./bits_test
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef uint32_t DWORD; typedef unsigned char BYTE; typedef size_t SIZE_T; typedef uintptr_t DWORD_PTR;
#define KLVH_BASE 0x80000000u
#define KLVH_PAGES 32768
#define KLVH_CHUNKS 48
static struct { BYTE *base; SIZE_T size; } klvh_chunk[KLVH_CHUNKS]; static int klvh_nchunk;
static DWORD klvh_in[KLVH_PAGES / 32], klvh_used[KLVH_PAGES / 32], klvh_start[KLVH_PAGES / 32];
#include "bits.inc"
static int fails;
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("FAIL "); printf(__VA_ARGS__); printf("\n"); } } while (0)
static int used_count(void){int n=0;for(int i=0;i<KLVH_PAGES;i++)n+=klvh_bit(klvh_used,i);return n;}
int main(void){
  /* two chunks: 64 MB at 0xfc000000 (top) and 4 MB at 0x80000000, like the takeover leaves them (addresses only; never dereferenced) */
  klvh_chunk[0].base=(BYTE*)(uintptr_t)0xfc000000u; klvh_chunk[0].size=64u<<20;
  klvh_chunk[1].base=(BYTE*)(uintptr_t)0x80000000u; klvh_chunk[1].size=4u<<20;
  klvh_nchunk=2;
  for(int c=0;c<2;c++) for(DWORD i=(DWORD)(((uintptr_t)klvh_chunk[c].base-KLVH_BASE)>>16),n=(DWORD)(klvh_chunk[c].size>>16);n;i++,n--) klvh_set(klvh_in,i,1);
  CHECK(klvh_in_high((void*)(uintptr_t)0xfc000000u) && klvh_in_high((void*)(uintptr_t)0xffffffffu) && klvh_in_high((void*)(uintptr_t)0x803fffffu) && !klvh_in_high((void*)(uintptr_t)0x80400000u) && !klvh_in_high((void*)(uintptr_t)0x7fffffffu) && !klvh_in_high((void*)(uintptr_t)0x90000000u), "in_high bounds");
  long a=klvh_carve_pages(48);  /* 3 MB: first fit = chunk 0 (listed first) */
  CHECK(a==(long)((0xfc000000u-KLVH_BASE)>>16), "first carve at the first chunk's start (%ld)", a);
  long b=klvh_carve_pages(16);
  CHECK(b==a+48, "second carve right after (%ld)", b);
  long big=klvh_carve_pages(1024); /* 64 MB: no chunk has room (chunk 0 partly used) */
  CHECK(big==-1, "64 MB refused when no chunk has room (%ld)", big);
  long c4=klvh_carve_pages(64); /* 4 MB: fits chunk 1 exactly */
  CHECK(c4==b+16, "4 MB goes after b in chunk 0, first fit (%ld)", c4);
  CHECK(klvh_carve_pages(1)!=-1, "1 page still fits chunk 0");
  CHECK(used_count()==48+16+64+1, "used pages %d", used_count());
  /* release a: exactly 48 pages, not b's */
  DWORD n=klvh_release_pages((DWORD)a); CHECK(n==48, "release a -> %u pages", n);
  CHECK(klvh_bit(klvh_used,(DWORD)b) && klvh_bit(klvh_start,(DWORD)b), "b untouched");
  CHECK(klvh_release_pages((DWORD)a)==0, "double release -> 0");
  CHECK(klvh_release_pages((DWORD)b+3)==0, "release of a non-start -> 0");
  long a2=klvh_carve_pages(48); CHECK(a2==a, "the hole is reused (%ld = %ld)", a2, a);
  long a3=klvh_carve_pages(49); CHECK(a3!=a && a3!=-1 && a3>b, "49 pages do not fit the 48-page hole: after b (%ld)", a3);
  n=klvh_release_pages((DWORD)c4); CHECK(n==64, "release the 4 MB block -> %u", n);
  /* a block that ends at the chunk's last page: release must stop at the chunk end */
  CHECK(klvh_release_pages((DWORD)b)==16 && klvh_release_pages((DWORD)a2)==48 && klvh_release_pages((DWORD)a3)==49, "the rest released by size");
  CHECK(used_count()==1, "only the 1-page block stays (%d)", used_count());
  /* fill chunk 0 completely with 1-page blocks, then release them all */
  int k=0; while(klvh_carve_pages(1)!=-1) k++;
  CHECK(k==1024+64-1, "chunk 0 + chunk 1 fill page by page (%d more)", k);
  int rel=0; for(DWORD i=0;i<KLVH_PAGES;i++) if(klvh_bit(klvh_start,i)) rel+=klvh_release_pages(i)==1;
  CHECK(rel==1024+64 && used_count()==0, "all 1-page blocks released (%d)", rel);
  printf("bits_test: %d check(s) failed\n", fails); return fails?1:0; }
