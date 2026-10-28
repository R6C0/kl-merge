# Crew group name: the pointer chain behind the AI heister voice digit (static, 2026-10-28)

Evidence: kl2.exe disassembled with capstone/pefile (read only).

## 0x598460 (thiscall, ecx = a scene node), whole function
```
598460: mov eax,[ecx+0x50]     ; p = node->owner link
598463: test eax,eax
598465: jne 598468
598467: ret                    ; p == 0 -> returns 0
598468: mov eax,[eax+0x60]     ; returns [p+0x60] = the parent group object (grp)
59846b: ret
```
So 0x598460(node) = `[[node+0x50]+0x60]`, null when `[node+0x50]` is null.

## 0x588980 (ZGameRulesHeist slot 198, `ret 4`, one argument = the actor)
```
5889a2/8b: eax=[esp+0x94] (the argument, after sub esp 0x80 + 4 pushes + ret addr)
5889a8: mov ecx,[eax+4]        ; node = [actor+4]
5889bd: call 0x598460          ; grp = [[node+0x50]+0x60]
5889c2: mov eax,[eax+4]        ; gnode = [grp+4]
5889c5: mov eax,[eax+0x6c]     ; name = [gnode+0x6c]   (a POINTER, loaded as a dword)
5889c8: test eax,eax
5889ca: jne 5889d1
5889cc: mov eax,0xb31570       ; null -> default string
5889d1: mov al,[eax+0x12]      ; byte at index 0x12 of the string
5889d4: sub al,0x31            ; digit - '1'
5889e2: mov [ecx+ebp+0x33e],al ; rules[0x33e + slot] = that
```
Default string at 0xb31570 (read from the exe): `"<NONAME>\0..."`, i.e. a plain NUL-terminated C string.

## Answers
1. Chain: `actor -> node=[actor+4] -> p=[node+0x50] -> grp=[p+0x60] -> gnode=[grp+4] -> name=[gnode+0x6c]` (char*), byte `name[0x12]`.
2. The name is a `char*` (loaded with `mov eax,[..+0x6c]`, null-tested, then indexed; the fallback is a literal C string). Not an inline array, no length/ZString indirection at this site. Pass 0 of `klbf_lk_name` is the right layout; pass 1 (inline) is never used by the exe.
3. "Glazer_Bodyguard_0N": G0 l1 a2 z3 e4 r5 _6 B7 o8 d9 y10 g11 u12 a13 r14 d15 _16 '0'=17 N=18 = 0x12. Index 0x12 is right (digit '2'..'8' -> byte 1..7).

## Status of each hop
- `[actor+4]` (node): CONFIRMED (0x5889a8, the arg is the actor).
- `[node+0x50]`, `[p+0x60]`: CONFIRMED as the code of 0x598460 (that it is the *parent group* semantically stays an inference; the exe does not care).
- `[grp+4]` (gnode), `[gnode+0x6c]` char*: CONFIRMED (0x5889c2, 0x5889c5).
- Digit index 0x12: CONFIRMED (0x5889d1) and by counting.
- Not confirmed here: that the argument of slot 198 is the ZFFActor of vtable 0xbb3bac (taken from existing docs; not traced to the caller).

## C change for klbf_lk_name
None needed for correctness: the chain matches. Optional tidy: drop pass 1 (inline buffer), keep only `s = klh_rd32(gnode + 0x6c)`; if `s == 0` the exe uses "<NONAME>" (digit char '\0' - '1' = 0xCF, an out-of-range voice index), so log `group="<NONAME>"` for a null pointer instead of "?". Also reading `p`==0 is the exe's "return 0" case and then `[0+4]` would fault in the exe; the probe's early return is fine.
