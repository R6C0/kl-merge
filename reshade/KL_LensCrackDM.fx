/*
 * KL_LensCrackDM.fx - the cracked camera lens with the REAL Dead Men glass-crack decals (KL Merge, 2026-11-06).
 *
 * Same driver as KL_LensCrack.fx (klreshade.c 6): KL_CrackN, KL_Crack0..2 = (x, y, reach in screen heights, intensity).
 * Instead of procedural lines it stamps a fracture star from KL_LensCrackDM.png (reshade-shaders\Textures): a 2x2 atlas of 256 px cells
 * cut from the games' own bullet-hole-in-glass decals FX_Bullet_Hole_Glass_03 / _04 (Dead Men's two, plus the c variants of Dog Days'),
 * white cracks on black, recentred on the impact. Per crack: cell and mirror from a hash of x,y, random rotation, scale = the reach
 * (the texture's edge is at 1.0 reach, so the crack grows with the hook's 120 ms spread). The picture is bent along the cracks from the
 * texture's gradient (fine + wide), the crack itself is bright glass-white, with a faint dark halo beside the lines. Crosshair stays clear.
 *
 * Switch: [ReShade] TechCrack=KL_LensCrackDM@KL_LensCrackDM.fx in KLHook.ini (default stays KL_LensCrack@KL_LensCrack.fx = procedural).
 * Cost: idle one tap; per crack within its reach 9 mask taps + 3 picture taps, no loops (ps_3_0: tex2Dlod only, no gradient ops in branches).
 * Preview: PreviewCracks = 1 shows three cracks without the hook.
 * GUESS: every look constant (3.0 / 4.0 px bend, 0.85 shine, 0.55 dark) is tuned by eye on the offline preview, not seen in the game.
 *
 * 2026-11-07 immersion (owner: "a bit more immersive ... not too crazy"; klreshade.c 6b): KL_CrackFX = (1 + the newest crack's age in s,
 * 0 = none / an older dll; Flash, Glint, Haze flags from [Graphics] LensCrackFlash / Glint / Haze). Flash: the newest crack pops bright for
 * ~0.15 s with a 1.5 px picture jolt dying in ~0.3 s. Glint: the crack edges catch a slowly turning light, more in bright scenes. Haze: a
 * faint milky glass dust round each crack. No extra taps (all from the 9 mask taps + the 3 picture taps). With every flag 0 = the 11-06 look.
 * GUESS: the flash / jolt / glint / haze strengths are by eye, not seen in the game.
 */
#include "ReShade.fxh"

uniform float  KL_CrackN < source = "KL_CrackN"; hidden = 1; nosave = 1; >;
uniform float4 KL_Crack0 < source = "KL_Crack0"; hidden = 1; nosave = 1; >;
uniform float4 KL_Crack1 < source = "KL_Crack1"; hidden = 1; nosave = 1; >;
uniform float4 KL_Crack2 < source = "KL_Crack2"; hidden = 1; nosave = 1; >;
uniform float4 KL_CrackFX < source = "KL_CrackFX"; hidden = 1; nosave = 1; >;
uniform float  KLCD_Timer < source = "timer"; >;

uniform float CrackAmount  < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_label = "Crack strength"; > = 1.0;
uniform float CrackRefract < ui_type = "slider"; ui_min = 0.0; ui_max = 3.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Bend of the picture along the cracks"; > = 1.0;
uniform float CrackShine   < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Bright cracks"; > = 1.0;
uniform float CrackShadow  < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Dark halo beside the cracks"; > = 1.0;
uniform float PreviewCracks < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 1.0; ui_category = "Preview (no hook needed)"; ui_label = "Preview: three cracks"; > = 0.0;

texture KLCD_AtlasTex < source = "KL_LensCrackDM.png"; > { Width = 512; Height = 512; Format = RGBA8; };
sampler KLCD_Atlas { Texture = KLCD_AtlasTex; AddressU = CLAMP; AddressV = CLAMP; MagFilter = LINEAR; MinFilter = LINEAR; MipFilter = LINEAR; };

static const float KLCD_TAU = 6.2831853;
static const float KLCD_T  = 1.5 * 2.0 / 256.0;   /* fine tap distance: 1.5 texels, in units of the reach (a cell spans 2 reaches) */
static const float KLCD_WD = 5.0 * 2.0 / 256.0;   /* wide tap distance: 5 texels */

float KLCD_Hash(float2 p)
{
	float3 p3 = frac(float3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return frac((p3.x + p3.y) * p3.z);
}

float3 KLCD_Fetch(float2 uv) { return tex2Dlod(ReShade::BackBuffer, float4(uv, 0, 0)).rgb; }

/* the decal at q (screen axes, units of the reach, 0 = the impact): rotate by cs = (cos, sin), mirror by fl, pick the atlas cell at org (0 or 0.5 per axis) */
float KLCD_Mask(float2 q, float2 cs, float fl, float2 org)
{
	float2 r = float2((cs.x * q.x + cs.y * q.y) * fl, -cs.y * q.x + cs.x * q.y);
	float2 u = r * 0.5 + 0.5;
	float e = max(abs(u.x - 0.5), abs(u.y - 0.5));
	float em = 1.0 - smoothstep(0.42, 0.50, e);                      /* fade at the cell edge so no cell border shows */
	float2 a = org + clamp(u, 0.004, 0.996) * 0.5;
	return tex2Dlod(KLCD_Atlas, float4(a, 0, 0)).r * em;
}

/* one crack: cr = (x, y, reach, intensity). off in pixels, shine / dark / glint / haze 0..; pop = the birth flash 0..1 (newest only),
   ld = the glint's light direction (0 = no glint) */
void KLCD_Crack(float4 cr, float2 uv, float pop, float2 ld, inout float2 off, inout float shine, inout float dark, inout float glint, inout float haze)
{
	[branch] if (cr.z > 0.004 && cr.w > 0.0)
	{
		float2 p = (uv - cr.xy) * float2(BUFFER_ASPECT_RATIO, 1.0) / cr.z;
		float r = length(p);
		[branch] if (r < 1.25)
		{
			float seed = KLCD_Hash(cr.xy * 91.7);
			float cell = floor(KLCD_Hash(float2(seed * 13.1, 5.0)) * 4.0);
			float row = floor(cell * 0.5);                                /* no fmod in ReShade FX */
			float2 org = float2(cell - 2.0 * row, row) * 0.5;
			float ang = KLCD_Hash(float2(seed * 7.7, 2.0)) * KLCD_TAU;
			float2 cs = float2(cos(ang), sin(ang));
			float fl = KLCD_Hash(float2(seed * 3.3, 9.0)) > 0.5 ? 1.0 : -1.0;

			float m  = KLCD_Mask(p, cs, fl, org);
			float gx = KLCD_Mask(p + float2(KLCD_T, 0.0), cs, fl, org) - KLCD_Mask(p - float2(KLCD_T, 0.0), cs, fl, org);
			float gy = KLCD_Mask(p + float2(0.0, KLCD_T), cs, fl, org) - KLCD_Mask(p - float2(0.0, KLCD_T), cs, fl, org);
			float hx1 = KLCD_Mask(p + float2(KLCD_WD, 0.0), cs, fl, org);
			float hx2 = KLCD_Mask(p - float2(KLCD_WD, 0.0), cs, fl, org);
			float hy1 = KLCD_Mask(p + float2(0.0, KLCD_WD), cs, fl, org);
			float hy2 = KLCD_Mask(p - float2(0.0, KLCD_WD), cs, fl, org);
			float halo = 0.25 * (hx1 + hx2 + hy1 + hy2);
			float2 wg = float2(hx1 - hx2, hy1 - hy2);                 /* the wide gradient: bends the picture over a few pixels round the line */

			float w = cr.w * CrackAmount;
			float env = 1.0 - smoothstep(0.85, 1.2, r);
			off += (float2(gx, gy) * 3.0 + wg * 4.0) * w * env;       /* 3 / 4 px: GUESS */
			shine += (m * 0.85 + halo * 0.10) * w * env;
			dark += saturate(halo - m * 0.5) * 0.55 * w * env;
			shine += m * pop * 0.8 * env + (1.0 - smoothstep(0.0, 0.9, r)) * pop * 0.12;   /* the birth flash: the lines + a soft glow */
			float2 g = float2(gx, gy);
			float gl = length(g);
			glint += saturate(gl * 3.0) * pow(saturate(dot(g / (gl + 1e-4), ld)), 6.0) * w * env;
			haze += pow(saturate(1.0 - r), 1.5) * w;
		}
	}
}

float3 PS_KLCD_Crack(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float n = PreviewCracks > 0.5 ? 3.0 : KL_CrackN;
	[branch] if (n < 0.5)
		return KLCD_Fetch(uv);

	float4 c0 = PreviewCracks > 0.5 ? float4(0.10, 0.16, 0.24, 1.0) : KL_Crack0;
	float4 c1 = PreviewCracks > 0.5 ? float4(0.90, 0.70, 0.20, 1.0) : KL_Crack1;
	float4 c2 = PreviewCracks > 0.5 ? float4(0.84, 0.10, 0.17, 1.0) : KL_Crack2;
	c1.w *= step(1.5, n);
	c2.w *= step(2.5, n);

	/* immersion (KL_CrackFX); the preview loops a birth every 3 s */
	float4 fx = PreviewCracks > 0.5 ? float4(1.0 + frac(KLCD_Timer / 3000.0) * 3.0, 1.0, 1.0, 1.0) : KL_CrackFX;
	float age = fx.x - 1.0;
	float pop = fx.x > 0.5 && fx.y > 0.5 ? exp(-age * 18.0) : 0.0;
	float jolt = fx.x > 0.5 && fx.y > 0.5 ? exp(-age * 12.0) * 1.5 : 0.0;      /* px */
	float la = KLCD_Timer * 0.00025 + 2.4;                                     /* ~25 s a turn, starts from the upper left */
	float2 ld = fx.z > 0.5 ? float2(cos(la), sin(la)) : float2(0.0, 0.0);
	float p0 = n < 1.5 ? pop : 0.0, p1 = n >= 1.5 && n < 2.5 ? pop : 0.0, p2 = n >= 2.5 ? pop : 0.0;   /* the newest crack is the last one */

	float2 off = 0.0; float shine = 0.0, dark = 0.0, glint = 0.0, haze = 0.0;
	KLCD_Crack(c0, uv, p0, ld, off, shine, dark, glint, haze);
	KLCD_Crack(c1, uv, p1, ld, off, shine, dark, glint, haze);
	KLCD_Crack(c2, uv, p2, ld, off, shine, dark, glint, haze);

	/* the crosshair stays clear: nothing within ~0.1 of the screen's height of the middle, a soft rim up to 0.2 */
	float2 m = (uv - 0.5) * float2(BUFFER_ASPECT_RATIO, 1.0);
	float keep = smoothstep(0.10, 0.20, length(m));
	off *= keep * CrackRefract; shine *= keep * CrackShine; dark *= keep * CrackShadow; glint *= keep; haze *= keep * (fx.w > 0.5 ? 1.0 : 0.0);
	off += float2(sin(age * 55.0), cos(age * 47.0)) * jolt * CrackRefract;     /* the whole picture shakes (also the middle); CrackRefract 0 = none */

	float3 c = KLCD_Fetch(uv + off * BUFFER_PIXEL_SIZE);
	float lum = dot(c, float3(0.299, 0.587, 0.114));
	c = lerp(c, lum * 0.85 + 0.10, saturate(haze) * 0.16);                   /* milky glass dust */
	c *= 1.0 - min(saturate(dark), 0.6);
	c += saturate(shine) * float3(0.92, 0.95, 1.0) * 0.7;
	c += saturate(glint) * (0.15 + 0.6 * lum) * float3(1.0, 0.98, 0.94) * 0.9 * CrackShine;
	return saturate(c);
}

technique KL_LensCrackDM < ui_tooltip = "Kane & Lynch 2: cracked camera lens with the real Dead Men glass-crack decals (up to 3 impacts) driven by KLHook: KL_CrackN / KL_Crack0..2. Clean while KL_CrackN is 0. Put it after KL_CameraFX."; >
{
	pass { VertexShader = PostProcessVS; PixelShader = PS_KLCD_Crack; }
}
