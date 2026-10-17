/*
 * KL_LensCrack.fx - the cracked camera lens for Kane & Lynch 2 (KL Merge, 2026-10-17).
 *
 * "If you get shot a lot, the glass of the camera frame cracks." Up to three impact cracks, driven by KLHook through ReShade's
 * add-on API (klreshade.c 6), which decides WHEN (a burst of hits, a roll, a cooldown) and WHERE (random, near the frame edges):
 *
 *   KL_CrackN   0..3  how many cracks stand
 *   KL_Crack0/1/2     float4: x, y = the impact's centre in 0..1 of the screen, z = reach in screen heights (the hook grows it over
 *                     ~120 ms when the crack appears), w = intensity 0..1
 *
 * No initializers on these on purpose (performance mode, see KL_CameraFX.fx). Everything is procedural, no textures: per crack a
 * pitted bright impact centre, 8..14 jagged radial cracks with a fork each, two partial concentric rings; thin bright and dark edge
 * lines, the picture displaced a little along the lines (the glass bends it) and split into red / blue near the centre.
 * Nothing is drawn within ~0.1 screen heights of the middle of the screen (the crosshair) and the cracks keep to the frame edges.
 * Cost: while KL_CrackN is 0 one tap; with cracks 3 taps, and ~30 line tests per crack only for the pixels within its reach.
 * Shader model 3 safe (tex2Dlod only, no gradient ops in branches, no integer ops). Put it AFTER KL_CameraFX.
 * Preview: PreviewCracks = 1 shows three cracks without the hook.
 */
#include "ReShade.fxh"

uniform float  KL_CrackN < source = "KL_CrackN"; hidden = 1; nosave = 1; >;
uniform float4 KL_Crack0 < source = "KL_Crack0"; hidden = 1; nosave = 1; >;
uniform float4 KL_Crack1 < source = "KL_Crack1"; hidden = 1; nosave = 1; >;
uniform float4 KL_Crack2 < source = "KL_Crack2"; hidden = 1; nosave = 1; >;

uniform float CrackAmount  < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_label = "Crack strength"; > = 1.0;
uniform float CrackRefract < ui_type = "slider"; ui_min = 0.0; ui_max = 3.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Refraction along the cracks"; > = 1.0;
uniform float CrackSplit   < ui_type = "slider"; ui_min = 0.0; ui_max = 3.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Colour split near the impact"; > = 1.0;
uniform float CrackShine   < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Bright edges"; > = 1.0;
uniform float PreviewCracks < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 1.0; ui_category = "Preview (no hook needed)"; ui_label = "Preview: three cracks"; > = 0.0;

static const float KLC_TAU = 6.2831853;

float KLC_Hash(float2 p)
{
	float3 p3 = frac(float3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return frac((p3.x + p3.y) * p3.z);
}

float3 KLC_Fetch(float2 uv) { return tex2Dlod(ReShade::BackBuffer, float4(uv, 0, 0)).rgb; }

/* one straight-ish segment from o along dir (length len) seen from p (all in units of the crack's reach, x already aspect-corrected):
   dp = distance in pixels, side = which side of the line p is on (+1 / -1), nrm = the unit vector away from the line on that side,
   taper = 0 at the start .. 1 at the end. The line wobbles sideways so it reads as a fracture, not a ruler line. */
void KLC_Seg(float2 p, float2 o, float2 dir, float len, float fi, float pxs, out float dp, out float side, out float2 nrm, out float taper)
{
	float2 q = p - o;
	float al = dot(q, dir);
	float pe = dot(q, float2(-dir.y, dir.x));
	pe += 0.018 * sin(al * 21.0 + fi * 2.3) + 0.010 * sin(al * 53.0 + fi * 4.1);
	float ex = al - clamp(al, 0.0, len);
	dp = length(float2(pe, ex)) * pxs;
	side = pe >= 0.0 ? 1.0 : -1.0;
	nrm = float2(-dir.y, dir.x) * side;
	taper = saturate(al / len);
}

/* adds one line's look: off = displacement in pixels, shine = bright edge, dark = the shadow on one side of the line */
void KLC_Line(float dp, float side, float2 nrm, float taper, float w, inout float2 off, inout float shine, inout float dark)
{
	float hw = lerp(0.85, 0.30, taper);                              /* half width in pixels: thin, thinner toward the tip */
	float core = 1.0 - smoothstep(hw * 0.5, hw + 0.7, dp);
	float band = 1.0 - smoothstep(0.4, 4.0, dp);
	shine += core * 0.40 * w;                                        /* 0.40: overlaps near the impact must not saturate to a white blob */
	dark += (side < 0.0 ? band : 0.0) * 0.35 * w * (1.0 - core);
	off += nrm * band * smoothstep(0.0, 1.0, dp) * 1.8 * w;          /* 0 on the line itself: no 1 px tear where the side flips */
}

/* one crack: cr = (x, y, reach, intensity). off: pixels, ca: pixels (red out / blue in), shine, dark: 0.. */
void KLC_Crack(float4 cr, float2 uv, float2 pos, inout float2 off, inout float2 ca, inout float shine, inout float dark)
{
	[branch] if (cr.z > 0.004 && cr.w > 0.0)
	{
		float pxs = cr.z * BUFFER_HEIGHT;                                /* pixels per unit */
		float2 p = (uv - cr.xy) * float2(BUFFER_ASPECT_RATIO, 1.0) / cr.z;
		float r = length(p);
		[branch] if (r < 1.25)
		{
			float seed = KLC_Hash(cr.xy * 91.7);
			float nrays = 8.0 + floor(KLC_Hash(float2(seed * 13.1, 5.0)) * 7.0);            /* 8 .. 14 */
			float w = cr.w * CrackAmount;
			float2 o2 = 0.0; float sh = 0.0, dk = 0.0;
			float dp, side, taper; float2 nrm;

			/* radial cracks and their forks */
			[unroll] for (int i = 0; i < 14; i++)
			{
				float fi = (float)i;
				float ex = step(fi + 0.5, nrays);
				float h1 = KLC_Hash(float2(fi * 1.7 + seed * 40.0, 3.1));
				float th = ((fi + (h1 - 0.5) * 0.6) / nrays + seed) * KLC_TAU;
				float2 dir = float2(cos(th), sin(th));
				/* cull: a ray and its fork stay within ~0.52 rad (+ wobble and width) of the ray's direction; near the origin test everything */
				[branch] if (ex > 0.0 && (r < 0.12 || dot(p, dir) > 0.7 * r))
				{
					float h2 = KLC_Hash(float2(fi * 2.3 + 7.0, seed * 57.0));
					float h3 = KLC_Hash(float2(fi + 31.0, seed * 13.0));
					float len = 0.45 + 0.55 * h2;
					KLC_Seg(p, 0.0, dir, len, fi, pxs, dp, side, nrm, taper);
					KLC_Line(dp, side, nrm, taper, w, o2, sh, dk);
					/* the fork: leaves the ray at 25 .. 55 % of its length, 13 .. 30 degrees to one side, half as long */
					float rf = len * (0.25 + 0.30 * h3);
					float fa = th + (h3 > 0.5 ? 1.0 : -1.0) * (0.22 + 0.30 * h1);
					KLC_Seg(p, dir * rf, float2(cos(fa), sin(fa)), len * 0.5, fi + 40.0, pxs, dp, side, nrm, taper);
					KLC_Line(dp, side, nrm, taper, w * 0.8, o2, sh, dk);
				}
			}

			/* two partial concentric rings (the glass breaks in rings round the hit) */
			float a = atan2(p.y, p.x);
			[unroll] for (int k = 0; k < 2; k++)
			{
				float fk = (float)k;
				float R = k == 0 ? 0.20 + 0.12 * seed : 0.50 + 0.20 * KLC_Hash(float2(seed, 9.0));
				float rw = 0.012 * sin(a * 9.0 + seed * 20.0 + fk) + 0.008 * sin(a * 23.0 + fk * 3.0);
				float dr = r + rw - R;
				float arc = saturate((sin(a * 2.0 + seed * 40.0 + fk * 3.0) + 0.6 * sin(a * 5.0 + seed * 17.0) - 0.15) * 6.0);
				float rdp = abs(dr) * pxs;
				float core = 1.0 - smoothstep(0.25, 1.0, rdp);
				float band = 1.0 - smoothstep(0.4, 3.0, rdp);
				float2 rn = (p / max(r, 0.001)) * (dr >= 0.0 ? 1.0 : -1.0);
				sh += core * 0.30 * w * arc;
				o2 += rn * band * 1.2 * w * arc;
			}

			/* the impact: a small pitted bright crater with a dark rim, jagged edge */
			float rpx = r * pxs;
			float R0 = 3.0 + 1.4 * sin(a * 5.0 + seed * 9.0) + 0.9 * sin(a * 11.0 + seed * 4.0);
			float pit = 1.0 - smoothstep(R0 - 1.0, R0 + 1.0, rpx);
			float rim = smoothstep(R0, R0 + 1.2, rpx) * (1.0 - smoothstep(R0 + 1.2, R0 + 5.0, rpx));
			float pits = 0.55 + 0.45 * KLC_Hash(floor(pos / 1.5));
			sh += pit * 0.9 * pits * w;
			dk += rim * 0.45 * w;

			/* the faint colour split: strongest at the impact, gone at ~0.5 of the reach */
			ca += (p / max(r, 0.001)) * (1.0 - smoothstep(0.0, 0.5, r)) * 1.6 * w;

			/* everything fades out toward the reach so no line ends hard in the middle of nowhere */
			float env = 1.0 - smoothstep(0.85, 1.2, r);
			off += o2 * env; shine += sh * env; dark += dk * env;
		}
	}
}

float3 PS_KLC_Crack(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float n = PreviewCracks > 0.5 ? 3.0 : KL_CrackN;
	[branch] if (n < 0.5)
		return KLC_Fetch(uv);

	float4 c0 = PreviewCracks > 0.5 ? float4(0.10, 0.16, 0.24, 1.0) : KL_Crack0;
	float4 c1 = PreviewCracks > 0.5 ? float4(0.90, 0.70, 0.20, 1.0) : KL_Crack1;
	float4 c2 = PreviewCracks > 0.5 ? float4(0.84, 0.10, 0.17, 1.0) : KL_Crack2;
	c1.w *= step(1.5, n);
	c2.w *= step(2.5, n);

	float2 off = 0.0, ca = 0.0; float shine = 0.0, dark = 0.0;
	KLC_Crack(c0, uv, pos.xy, off, ca, shine, dark);
	KLC_Crack(c1, uv, pos.xy, off, ca, shine, dark);
	KLC_Crack(c2, uv, pos.xy, off, ca, shine, dark);

	/* the crosshair stays clear: nothing within ~0.1 of the screen's height of the middle, a soft rim up to 0.2 */
	float2 m = (uv - 0.5) * float2(BUFFER_ASPECT_RATIO, 1.0);
	float keep = smoothstep(0.10, 0.20, length(m));
	off *= keep * CrackRefract; ca *= keep * CrackSplit; shine *= keep * CrackShine; dark *= keep;

	float2 px = BUFFER_PIXEL_SIZE;
	float2 u0 = uv + off * px;
	float3 c;
	c.r = KLC_Fetch(u0 + ca * px).r;
	c.g = KLC_Fetch(u0).g;
	c.b = KLC_Fetch(u0 - ca * px).b;
	c *= 1.0 - min(saturate(dark), 0.6);
	c += saturate(shine) * float3(0.92, 0.95, 1.0) * 0.7;
	return saturate(c);
}

technique KL_LensCrack < ui_tooltip = "Kane & Lynch 2: cracked camera lens (up to 3 impact cracks) driven by KLHook: KL_CrackN / KL_Crack0..2. Clean while KL_CrackN is 0. Put it after KL_CameraFX."; >
{
	pass { VertexShader = PostProcessVS; PixelShader = PS_KLC_Crack; }
}
