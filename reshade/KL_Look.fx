/*
 * KL_Look.fx v2 - "Heat" grade for Kane & Lynch 2 (KL Merge, 2026-10-15, worker fx).
 *
 * The look: Michael Mann's Heat - steel-blue / teal shadows and mids, warm sodium / tungsten practical lights,
 * a restrained (slightly desaturated) palette with natural skin, dense blacks that never go to ink, heavy skies.
 * Replaces v1 (the "cool overcast photo" grade). Same technique name (KL_Look), so presets and the hook keep working.
 *
 * What is new against v1
 *   - ADAPTIVE SKY: the sky is found per pixel (depth == far plane when ReShade has depth, otherwise a
 *     bright + smooth + low-chroma + upper-screen heuristic), its average brightness is measured every frame and
 *     smoothed over time, and it is pushed toward a target that follows the scene's own brightness:
 *     a blown-out white sky is pulled down to a heavy steel grey-blue, a flat dull sky is lifted a little and
 *     its cloud detail stretched. Never blown, never flat.
 *   - Mild auto exposure (scene log-average, smoothed) so bright levels are held down and dark ones are not mud.
 *   - A real filmic tonemap (Hable curve on a linearised, highlight-expanded image), not a gamma-space S-curve.
 *   - Black crush + cool floor ("crushed but not black"), fine luma grain for grit.
 *   - Cheaper: 4 passes, only ONE at full resolution (v1 had 3 quarter-res + 1 full-res passes).
 *
 * Depth: ReShade's Generic Depth add-on is DISABLED in the owner's ReShade.ini. The effect tests every frame whether
 * the depth buffer holds anything (8 raw samples must not all be equal) and falls back to the heuristic sky when not.
 * Set KL_LOOK_DEPTH 0 in the preprocessor definitions to remove the depth taps entirely.
 *
 * Passes (2560 x 1440):
 *   1. Low     1/8 x 1/8 res (320 x 180)  RGBA16F: colour mean + sky weight            ~0.02 ms
 *   2. Adapt   1 x 1: scene log-average, sky average, sky cover, depth valid, smoothed ~0.01 ms
 *   3. Store   1 x 1: history copy                                                      ~0.00 ms
 *   4. Grade   full res: sharpen (4 taps), local contrast, sky, tonemap, tone, grain    ~0.15-0.25 ms
 * Expected cost: about 0.2-0.3 ms on an RTX 4070 Ti class card at 1440p (v1 measured ~8 % at ~150 fps = ~0.4 ms).
 * Direct3D 9 / shader model 3 safe: no compute, no integer ops, tex2Dlod inside branches only.
 */
#include "ReShade.fxh"

#ifndef KL_LOOK_DEPTH
	#define KL_LOOK_DEPTH 1   // 1 = use depth for the sky when the depth buffer is valid (auto-detected); 0 = never touch depth
#endif

/* ---------------------------------------------------------------- knobs */
uniform float Exposure      < ui_type = "slider"; ui_min = -1.5; ui_max = 1.5; ui_step = 0.01; ui_category = "Tone"; ui_label = "Exposure (stops)"; ui_tooltip = "Negative = moodier. Highlights stay put; mids and shadows move."; > = -0.15;
uniform float AutoExposure  < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Tone"; ui_label = "Auto exposure strength"; ui_tooltip = "Pull every scene toward the same moody key. 0 = off."; > = 0.45;
uniform float SceneKey      < ui_type = "slider"; ui_min = 0.15; ui_max = 0.6; ui_step = 0.01; ui_category = "Tone"; ui_label = "Scene key (target average)"; > = 0.30;
uniform float Contrast      < ui_type = "slider"; ui_min = 0.7; ui_max = 1.6; ui_step = 0.01; ui_category = "Tone"; ui_label = "Filmic contrast"; > = 1.12;
uniform float LocalContrast < ui_type = "slider"; ui_min = 0.0; ui_max = 1.5; ui_step = 0.01; ui_category = "Tone"; ui_label = "Local contrast (grit / texture pop)"; > = 0.55;
uniform float BlackCrush    < ui_type = "slider"; ui_min = 0.0; ui_max = 0.08; ui_step = 0.001; ui_category = "Tone"; ui_label = "Black crush"; > = 0.020;
uniform float BlackFloor    < ui_type = "slider"; ui_min = 0.0; ui_max = 0.06; ui_step = 0.001; ui_category = "Tone"; ui_label = "Black floor (cool, keeps detail)"; > = 0.016;

uniform float Saturation    < ui_type = "slider"; ui_min = 0.0; ui_max = 1.5; ui_step = 0.01; ui_category = "Colour"; ui_label = "Saturation"; > = 0.80;
uniform float SkinKeep      < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Colour"; ui_label = "Keep skin tones natural"; > = 0.6;
uniform float KeepColour    < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Colour"; ui_label = "Keep strong colours (HUD, signs)"; > = 0.85;
uniform float3 ShadowTint   < ui_type = "color"; ui_category = "Colour"; ui_label = "Shadow / mid tint (steel blue)"; > = float3(0.76, 0.88, 1.00);
uniform float ShadowAmount  < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Colour"; ui_label = "Shadow tint amount"; > = 0.70;
uniform float3 PracticalTint< ui_type = "color"; ui_category = "Colour"; ui_label = "Practical light tint (sodium / tungsten)"; > = float3(1.00, 0.91, 0.745);
uniform float PracticalAmount<ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Colour"; ui_label = "Practical highlight warmth"; > = 0.55;

uniform float SkyControl    < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Sky"; ui_label = "Adaptive sky strength"; > = 0.85;
uniform float SkyRatio      < ui_type = "slider"; ui_min = 0.8; ui_max = 3.0; ui_step = 0.01; ui_category = "Sky"; ui_label = "Sky brightness vs scene"; ui_tooltip = "Target sky = scene average x this, clamped to Sky min / max."; > = 1.7;
uniform float SkyMin        < ui_type = "slider"; ui_min = 0.1; ui_max = 0.7; ui_step = 0.01; ui_category = "Sky"; ui_label = "Sky min brightness"; > = 0.32;
uniform float SkyMax        < ui_type = "slider"; ui_min = 0.3; ui_max = 0.95; ui_step = 0.01; ui_category = "Sky"; ui_label = "Sky max brightness"; > = 0.62;
uniform float SkyDetail     < ui_type = "slider"; ui_min = 0.5; ui_max = 3.0; ui_step = 0.01; ui_category = "Sky"; ui_label = "Sky cloud detail stretch"; > = 1.6;
uniform float3 SkyColour    < ui_type = "color"; ui_category = "Sky"; ui_label = "Sky colour (heavy steel)"; > = float3(0.70, 0.78, 0.86);
uniform float SkyTint       < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Sky"; ui_label = "Sky colour amount"; > = 0.55;
uniform float SkyGradient   < ui_type = "slider"; ui_min = 0.0; ui_max = 0.5; ui_step = 0.01; ui_category = "Sky"; ui_label = "Sky darker toward the top"; > = 0.18;
uniform bool  SkyDebug      < ui_category = "Sky"; ui_label = "Show the sky mask (debug)"; > = false;

uniform float Sharpen       < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Finish"; ui_label = "Sharpen (adaptive)"; > = 0.30;
uniform float Grain         < ui_type = "slider"; ui_min = 0.0; ui_max = 0.08; ui_step = 0.001; ui_category = "Finish"; ui_label = "Grain"; > = 0.022;
uniform float Vignette      < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Finish"; ui_label = "Vignette"; > = 0.30;
uniform float AdaptSpeed    < ui_type = "slider"; ui_min = 0.1; ui_max = 5.0; ui_step = 0.01; ui_category = "Finish"; ui_label = "Adaptation time (s)"; ui_tooltip = "How long exposure / sky take to follow a change of view."; > = 0.8;

uniform float KLL2_FrameTime < source = "frametime"; >;
uniform float KLL2_Timer     < source = "timer"; >;

/* ---------------------------------------------------------------- resources */
#define KLL2_W (BUFFER_WIDTH / 8)
#define KLL2_H (BUFFER_HEIGHT / 8)

texture KLL2_LowTex       { Width = KLL2_W; Height = KLL2_H; Format = RGBA16F; };
texture KLL2_AdaptTex     { Width = 1; Height = 1; Format = RGBA16F; };
texture KLL2_AdaptPrevTex { Width = 1; Height = 1; Format = RGBA16F; };
sampler KLL2_Low       { Texture = KLL2_LowTex;       AddressU = CLAMP; AddressV = CLAMP; };
sampler KLL2_Adapt     { Texture = KLL2_AdaptTex;     MagFilter = POINT; MinFilter = POINT; };
sampler KLL2_AdaptPrev { Texture = KLL2_AdaptPrevTex; MagFilter = POINT; MinFilter = POINT; };

static const float3 KLL2_LUMA = float3(0.2126, 0.7152, 0.0722);

float KLL2_Chroma(float3 c) { return max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b)); }

/* sky from depth: 1 at the far plane. Only meaningful when the depth buffer is valid (Adapt.w). */
float KLL2_DepthSky(float2 uv)
{
#if KL_LOOK_DEPTH
	return smoothstep(0.97, 0.999, ReShade::GetLinearizedDepth(uv));
#else
	return 0.0;
#endif
}

/* ---------------------------------------------------------------- pass 1: 1/8 res colour mean + sky weight */
float4 PS_KLL2_Low(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	/* four bilinear taps spread over the 8 x 8 cell (each one averages 2 x 2 pixels) */
	float2 o = BUFFER_PIXEL_SIZE * 2.0;
	float3 a = tex2Dlod(ReShade::BackBuffer, float4(uv + float2(-o.x, -o.y), 0, 0)).rgb;
	float3 b = tex2Dlod(ReShade::BackBuffer, float4(uv + float2( o.x, -o.y), 0, 0)).rgb;
	float3 c = tex2Dlod(ReShade::BackBuffer, float4(uv + float2(-o.x,  o.y), 0, 0)).rgb;
	float3 d = tex2Dlod(ReShade::BackBuffer, float4(uv + float2( o.x,  o.y), 0, 0)).rgb;
	float3 m = (a + b + c + d) * 0.25;
	float la = dot(a, KLL2_LUMA), lb = dot(b, KLL2_LUMA), lc = dot(c, KLL2_LUMA), ld = dot(d, KLL2_LUMA);
	float l = dot(m, KLL2_LUMA);
	float spread = max(max(la, lb), max(lc, ld)) - min(min(la, lb), min(lc, ld));

	/* heuristic sky: bright, smooth, not strongly coloured, and more likely high on the screen */
	float sky = smoothstep(0.42, 0.72, l)
	          * (1.0 - smoothstep(0.03, 0.10, spread))
	          * (1.0 - smoothstep(0.18, 0.40, KLL2_Chroma(m)))
	          * lerp(0.35, 1.0, smoothstep(0.85, 0.45, uv.y));

	/* depth sky when last frame found a valid depth buffer */
	float depthValid = tex2Dlod(KLL2_AdaptPrev, float4(0.5, 0.5, 0, 0)).w;
	sky = lerp(sky, KLL2_DepthSky(uv), step(0.5, depthValid));
	return float4(m, sky);
}

/* ---------------------------------------------------------------- pass 2: 1 x 1 adaptation (smoothed) */
float4 PS_KLL2_Adapt(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float logSum = 0.0, wSum = 0.0, skySum = 0.0, skyW = 0.0;
	/* 6 x 4 grid; each tap sits on a texel corner, so the bilinear fetch averages 4 low-res texels (32 x 32 pixels) */
	[unroll] for (int y = 0; y < 4; y++)
	{
		[unroll] for (int x = 0; x < 6; x++)
		{
			float2 p = floor((float2(x, y) + 0.5) / float2(6.0, 4.0) * float2(KLL2_W, KLL2_H)) / float2(KLL2_W, KLL2_H);
			float4 s = tex2Dlod(KLL2_Low, float4(p, 0, 0));
			float l = dot(s.rgb, KLL2_LUMA);
			/* the scene average leaves the sky out (it is what we are correcting) and weights the centre more */
			float w = (1.0 - s.a) * (1.0 - 0.5 * length(p - 0.5));
			logSum += log(max(l, 0.004)) * w;
			wSum   += w;
			skySum += l * s.a;
			skyW   += s.a;
		}
	}
	float scene = exp(logSum / max(wSum, 1e-3));
	float skyAvg = (skyW > 0.05) ? skySum / skyW : 0.7;
	float cover = skyW / 24.0;

	/* depth valid? 8 raw depth samples: an absent depth buffer reads one constant everywhere */
	float valid = 0.0;
#if KL_LOOK_DEPTH
	{
		float mn = 1.0, mx = 0.0;
		[unroll] for (int j = 0; j < 8; j++)
		{
			float2 p = float2(0.1 + 0.8 * frac(j * 0.375), 0.15 + 0.1 * j);
			float r = tex2Dlod(ReShade::DepthBuffer, float4(p, 0, 0)).x;
			mn = min(mn, r); mx = max(mx, r);
		}
		valid = step(1e-4, mx - mn);
	}
#endif

	float4 cur = float4(scene, skyAvg, cover, valid);
	float4 prev = tex2Dlod(KLL2_AdaptPrev, float4(0.5, 0.5, 0, 0));
	/* first frame / reset: history is zero */
	if (prev.x <= 0.0) return cur;
	float k = 1.0 - exp(-max(KLL2_FrameTime, 0.0) * 0.001 / max(AdaptSpeed * 0.5, 0.05));
	float4 r = lerp(prev, cur, saturate(k));
	r.w = valid; /* the depth flag switches at once */
	return r;
}

float4 PS_KLL2_Store(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	return tex2Dlod(KLL2_Adapt, float4(0.5, 0.5, 0, 0));
}

/* ---------------------------------------------------------------- filmic */
float3 KLL2_Hable(float3 x)
{   /* Hable's filmic curve (the "ideal" parameters): soft toe, long shoulder */
	const float A = 0.22, B = 0.30, C = 0.10, D = 0.20, E = 0.01, F = 0.30;
	return ((x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F)) - E / F;
}

float KLL2_Hash(float2 p)
{
	float3 p3 = frac(float3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return frac((p3.x + p3.y) * p3.z);
}

/* ---------------------------------------------------------------- pass 4: the grade */
float3 PS_KLL2_Grade(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float2 o = BUFFER_PIXEL_SIZE;
	float3 c = tex2D(ReShade::BackBuffer, uv).rgb;
	float4 ad = tex2D(KLL2_Adapt, float2(0.5, 0.5));   /* x scene log-avg, y sky avg, z sky cover, w depth valid */

	/* contrast-adaptive sharpen (CAS-like cross) */
	float3 n = tex2D(ReShade::BackBuffer, uv + float2(0, -o.y)).rgb, s = tex2D(ReShade::BackBuffer, uv + float2(0, o.y)).rgb;
	float3 w = tex2D(ReShade::BackBuffer, uv + float2(-o.x, 0)).rgb, e = tex2D(ReShade::BackBuffer, uv + float2(o.x, 0)).rgb;
	{
		float3 mn = min(c, min(min(n, s), min(w, e))), mx = max(c, max(max(n, s), max(w, e)));
		float3 amp = sqrt(saturate(min(mn, 1.0 - mx) / max(mx, 1e-4)));
		float3 wgt = -amp * lerp(1.0 / 8.0, 1.0 / 5.0, Sharpen) * step(0.001, Sharpen);
		c = saturate((c + (n + s + w + e) * wgt) / (1.0 + 4.0 * wgt));
	}

	/* the 1/8-res neighbourhood: a small tent of 4 bilinear taps (~16 px reach) */
	float2 lo = float2(0.75 / KLL2_W, 0.75 / KLL2_H);
	float4 nb = (tex2D(KLL2_Low, uv + float2(-lo.x, -lo.y)) + tex2D(KLL2_Low, uv + float2(lo.x, -lo.y))
	           + tex2D(KLL2_Low, uv + float2(-lo.x,  lo.y)) + tex2D(KLL2_Low, uv + float2(lo.x,  lo.y))) * 0.25;
	float l  = dot(c, KLL2_LUMA);
	float la = dot(nb.rgb, KLL2_LUMA);

	/* per-pixel sky weight: the low-res mask refined by this pixel (keeps dark rooftops / wires out of it) */
	float sky;
	if (ad.w > 0.5)
		sky = KLL2_DepthSky(uv);
	else
		sky = nb.a * lerp(smoothstep(0.30, 0.55, la), smoothstep(0.22, 0.60, l), 0.35) * smoothstep(0.80, 0.30, uv.y);   /* v2.1: soft edge (mostly the 1/8 mask), upper screen only - bright objects lower down are not re-toned */
	sky *= SkyControl;

	/* local contrast (not on the sky: its detail is handled below) */
	{
		float guard = smoothstep(0.02, 0.15, l) * (1.0 - smoothstep(0.80, 0.98, l)) * (1.0 - sky);
		float dl = l - la; dl *= 1.0 - smoothstep(0.03, 0.10, abs(dl));   /* v2.2: texture only - near an edge (a lit object on a dark wall, a head against a pillar) the difference is large and the step fades out: no halo, no cut-out look */
		float l2 = max(l + dl * LocalContrast * guard, 0.0);
		c *= (l > 1e-4) ? (l2 / l) : 1.0;
	}

	/* ADAPTIVE SKY: pull the measured sky average to a target that follows the scene, stretch its detail, tint it */
	{
		float target = clamp(ad.x * SkyRatio, SkyMin, SkyMax);
		float skyAvg = max(ad.y, 0.02);
		float ls = dot(c, KLL2_LUMA);
		float newL = target + (ls - skyAvg) * SkyDetail * (target / skyAvg);
		newL *= 1.0 - SkyGradient * saturate(1.0 - uv.y * 1.6);   /* heavier toward the top */
		newL = clamp(newL, 0.04, 0.92);                           /* never paper white, never black */
		float3 keepHue = c * (newL / max(ls, 1e-4));
		float3 steel = SkyColour * (newL / max(dot(SkyColour, KLL2_LUMA), 1e-3));
		float3 cs = lerp(keepHue, steel, SkyTint);
		c = lerp(c, cs, sky);
	}

	/* linearise, expand the clipped highlights a little, exposure (+ auto), filmic tonemap, back to display */
	{
		float autoGain = clamp(pow(SceneKey / max(ad.x, 0.01), AutoExposure), 0.65, 1.45);
		float k = 1.5 * exp2(Exposure) * autoGain;
		float3 x = pow(max(c, 0.0), 2.2);
		x = x / (1.0 - 0.75 * min(x, 1.0));                       /* 1.0 -> 4.0 */
		x = 0.18 * pow(max(x, 1e-6) / 0.18, Contrast);
		float white = 0.18 * pow(4.0 / 0.18, Contrast);
		x = KLL2_Hable(x * k) / KLL2_Hable(float3(white, white, white) * k).x;
		c = pow(saturate(x), 1.0 / 2.2);
	}

	/* colour: restrained saturation, skin and strong colours (HUD, neon) kept, steel shadows, warm practicals */
	{
		l = dot(c, KLL2_LUMA);
		float chroma = KLL2_Chroma(c);
		float keep = smoothstep(0.30, 0.55, chroma) * KeepColour;
		/* skin: red > green > blue, moderate chroma */
		float skin = saturate((c.r - c.g) * 6.0) * saturate((c.g - c.b) * 8.0) * (1.0 - smoothstep(0.25, 0.45, chroma)) * SkinKeep;
		float sat = lerp(Saturation, 1.0, max(keep, skin * 0.8));
		c = lerp(l.xxx, c, sat);

		float ws = (1.0 - smoothstep(0.02, 0.55, l)) * smoothstep(0.0, 0.03, l);
		float wh = smoothstep(0.45, 1.05, la * 0.5 + l * 0.5) * (1.0 - sky);   /* v2.1: follows the neighbourhood too, so one bright object is not tinted apart from its light pool */
		float3 tint = 1.0 + (ShadowTint - 1.0) * ws * ShadowAmount + (PracticalTint - 1.0) * wh * PracticalAmount;
		tint /= max(dot(tint, KLL2_LUMA), 1e-3);                 /* hue only, keep brightness */
		c *= lerp(float3(1.0, 1.0, 1.0), tint, 1.0 - keep);
	}

	/* blacks: crush, then a faint cool floor so shadows read as air, not ink */
	c = max(c - BlackCrush, 0.0) / (1.0 - BlackCrush);
	c = c * (1.0 - BlackFloor) + BlackFloor * float3(0.80, 0.92, 1.0);

	/* vignette */
	float2 v = uv - 0.5; v.x *= BUFFER_ASPECT_RATIO;
	c *= 1.0 - Vignette * smoothstep(0.35, 1.05, dot(v, v) * 2.0);

	/* fine luma grain, strongest in the mids */
	{
		float g = KLL2_Hash(pos.xy + frac(KLL2_Timer * 0.00071) * float2(1031.0, 719.0)) - 0.5;
		l = dot(c, KLL2_LUMA);
		c += g * Grain * (1.0 - abs(l * 2.0 - 1.0) * 0.7);
	}

	if (SkyDebug) c = lerp(c, float3(1.0, 0.0, 1.0), sky * 0.7);
	return saturate(c);
}

technique KL_Look < ui_tooltip = "Kane & Lynch 2: a moody 'Heat' grade with an adaptive sky (v2). Put it below Uplift and SMAA."; >
{
	pass Low   { VertexShader = PostProcessVS; PixelShader = PS_KLL2_Low;   RenderTarget = KLL2_LowTex; }
	pass Adapt { VertexShader = PostProcessVS; PixelShader = PS_KLL2_Adapt; RenderTarget = KLL2_AdaptTex; }
	pass Store { VertexShader = PostProcessVS; PixelShader = PS_KLL2_Store; RenderTarget = KLL2_AdaptPrevTex; }
	pass Grade { VertexShader = PostProcessVS; PixelShader = PS_KLL2_Grade; }
}
