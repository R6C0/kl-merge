/*
 * KL_CameraFX.fx - the raw handheld-camera layer for Kane & Lynch 2 (KL Merge, 2026-10-15, worker fx).
 *
 * "Gameplay should feel raw like a camera: it gets distorted the harder you shoot and the more you get hit."
 * Driven every frame by KLHook through ReShade's add-on API (effect_runtime::set_uniform_value_float):
 *
 *   KL_Fire   0..1  how hard you are shooting (smoothed by the hook: rises per shot, decays over ~0.5 s)
 *   KL_Hurt   0..1  recent damage (jumps on a hit, decays over ~1-2 s)
 *   KL_Down   0 / 1 while knocked down (the hook may ramp it over ~0.3 s for a softer start)
 *   KL_Speed  0..1  movement speed (sprint = 1)
 *
 * These four have NO initializer on purpose: in ReShade's performance mode (on in the owner's ReShade.ini) every
 * uniform WITH an initializer is baked into the shader as a constant and can no longer be set from code. Without an
 * initializer they stay real uniforms, start at 0 and are hidden from the overlay and never saved in the preset.
 * ALL effects are exactly zero when all four are 0 (the pass returns the untouched pixel): until the hook sets them
 * the picture is clean. Preview* sliders let you try the look in the ReShade overlay without the hook.
 *
 * Effects: shake (UV offset + roll, with a matching zoom so no edge shows), barrel distortion, chromatic aberration,
 * compression macro-blocking + banding, sharpening "crunch", exposure pumps, a pulsing vignette, red / drained colour
 * when hurt, sensor noise, and a soft blur while down.
 *
 * Cost: ONE full-resolution pass, 6 texture taps. About 0.1-0.15 ms at 2560 x 1440 on an RTX 4070 Ti class card while
 * active; about 0.02 ms when all inputs are 0 (one tap, early out). Zero if the hook switches the technique off while
 * idle. Direct3D 9 / shader model 3 safe: tex2Dlod only (no gradient ops inside the branch), no integer ops.
 */
#include "ReShade.fxh"

/* ---------------------------------------------------------------- set by KLHook every frame (do not give these initializers) */
uniform float KL_Fire < source = "KL_Fire"; hidden = 1; nosave = 1; >;
uniform float KL_Hurt < source = "KL_Hurt"; hidden = 1; nosave = 1; >;
uniform float KL_Down < source = "KL_Down"; hidden = 1; nosave = 1; >;
uniform float KL_Speed < source = "KL_Speed"; hidden = 1; nosave = 1; >;
uniform float KL_CamFX < source = "KL_CamFX"; hidden = 1; nosave = 1; >;   /* the in-game Camera FX row: 1 light x0.3, 2 medium x0.55, 3 strong x0.8, 4 raw x1; 0 = the technique is off anyway */

uniform float KLC_Timer < source = "timer"; >;

/* ---------------------------------------------------------------- knobs */
uniform float KL_FxAmount   < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_label = "Overall camera FX amount"; > = 1.0;
uniform float ShakeAmount   < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Shake"; > = 1.0;
uniform float DistortAmount < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Lens distortion (barrel)"; > = 1.0;
uniform float CAAmount      < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Chromatic aberration"; > = 1.0;
uniform float BlockAmount   < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Compression blocks"; > = 1.0;
uniform float CrunchAmount  < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Sharpening crunch"; > = 1.0;
uniform float PumpAmount    < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Exposure pumps"; > = 1.0;
uniform float VignetteAmount< ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Vignette pulse"; > = 1.0;
uniform float HurtColour    < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Hurt: red / drained colour"; > = 1.0;
uniform float NoiseAmount   < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_category = "Parts"; ui_label = "Sensor noise"; > = 1.0;

uniform float PreviewFire  < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Preview (no hook needed)"; ui_label = "Preview: firing"; > = 0.0;
uniform float PreviewHurt  < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Preview (no hook needed)"; ui_label = "Preview: hurt"; > = 0.0;
uniform float PreviewDown  < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Preview (no hook needed)"; ui_label = "Preview: down"; > = 0.0;
uniform float PreviewSpeed < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_category = "Preview (no hook needed)"; ui_label = "Preview: speed"; > = 0.0;

static const float3 KLX_LUMA = float3(0.2126, 0.7152, 0.0722);

float KLX_Hash(float2 p)
{
	float3 p3 = frac(float3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return frac((p3.x + p3.y) * p3.z);
}

float3 KLX_Fetch(float2 uv) { return tex2Dlod(ReShade::BackBuffer, float4(uv, 0, 0)).rgb; }

float3 PS_KLX_Camera(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float amt = KL_FxAmount * (KL_CamFX > 3.5 ? 1.0 : (KL_CamFX > 2.5 ? 0.8 : (KL_CamFX > 1.5 ? 0.55 : (KL_CamFX > 0.5 ? 0.3 : 1.0))));   /* the menu row: 1 light, 2 medium, 3 strong, 4 raw */
	float f = saturate(max(KL_Fire,  PreviewFire))  * amt;
	float h = saturate(max(KL_Hurt,  PreviewHurt))  * amt;
	float d = saturate(max(KL_Down,  PreviewDown))  * amt;
	float s = saturate(max(KL_Speed, PreviewSpeed)) * amt;

	[branch] if (f + h + d + s <= 0.0001)
		return KLX_Fetch(uv);   /* clean: nothing is applied until the hook (or a preview slider) says so */

	/* time in seconds, wrapped every 10 minutes so the float keeps its precision in long sessions */
	float t = (KLC_Timer % 600000.0) * 0.001;

	/* ---- shake: fast recoil jitter (fire), a jolt (hurt), a slow sway + roll (down), a walk bob (speed) */
	float2 shake = 0.0;
	shake += f * 0.0035 * float2(sin(t * 61.0) + 0.6 * sin(t * 97.0 + 1.3), cos(t * 53.0) + 0.6 * sin(t * 89.0 + 0.4)) / 1.6;
	shake += h * 0.0060 * float2(sin(t * 17.0 + 0.7) + 0.5 * sin(t * 31.0), cos(t * 23.0) + 0.5 * sin(t * 37.0 + 2.1)) / 1.5;
	shake += d * 0.0090 * float2(sin(t * 0.9) + 0.4 * sin(t * 2.3 + 1.0), cos(t * 0.7) + 0.4 * sin(t * 1.9)) / 1.4;
	shake += s * 0.0020 * float2(sin(t * 5.2), abs(sin(t * 5.2)) * 2.0 - 1.0);
	shake *= ShakeAmount;
	float maxShake = (f * 0.0035 + h * 0.006 + d * 0.009 + s * 0.002) * ShakeAmount;
	float roll = (d * 0.035 * sin(t * 0.6) + h * 0.008 * sin(t * 13.0)) * ShakeAmount;

	/* zoom in just enough that the shake and roll never show the frame edge */
	float zoom = 1.0 + 2.0 * maxShake + abs(roll) * BUFFER_ASPECT_RATIO;
	float2 q = (uv - 0.5) / zoom;
	float cr = cos(roll), sr = sin(roll);
	q = float2(q.x * cr - q.y * sr * (1.0 / BUFFER_ASPECT_RATIO), q.x * sr * BUFFER_ASPECT_RATIO + q.y * cr);
	q += shake;

	/* ---- barrel distortion (normalised so the corners stay inside the image) */
	float k = (0.10 * f + 0.14 * h + 0.22 * d + 0.03 * s) * DistortAmount;
	float r2 = dot(q, q) * 2.0;               /* 1.0 at the corners */
	float2 qd = q * (1.0 + k * r2) / (1.0 + k);
	float2 uvd = qd + 0.5;

	/* ---- chromatic aberration, growing toward the edges */
	float ca = (0.0035 * f + 0.0070 * h + 0.0050 * d) * CAAmount;
	float2 cad = qd * r2 * ca;
	float3 c;
	c.r = KLX_Fetch(uvd + cad).r;
	c.g = KLX_Fetch(uvd).g;
	c.b = KLX_Fetch(uvd - cad).b;

	/* ---- sharpening crunch (a cheap camcorder edge enhancer); while down the same taps spread into a soft blur */
	{
		float spread = 1.0 + d * 5.0;
		float2 px = BUFFER_PIXEL_SIZE * spread;
		float3 t1 = KLX_Fetch(uvd + float2(px.x, px.y));
		float3 t2 = KLX_Fetch(uvd - float2(px.x, px.y));
		float3 blur = (t1 + t2) * 0.5;
		float crunch = (0.9 * f + 0.5 * h) * CrunchAmount * (1.0 - d);
		c += clamp((c - blur) * crunch * 2.0, -0.15, 0.15);
		c = lerp(c, (c + t1 + t2) / 3.0, d * 0.6);
	}

	/* ---- compression artefacts: damaged 16 px macro-blocks smear to their block's centre (and slip a little), plus banding */
	{
		float qa = saturate(0.7 * f + 0.6 * h + 0.3 * d) * BlockAmount;
		float2 bsize = 16.0 * BUFFER_PIXEL_SIZE;
		float2 block = floor(uvd / bsize);
		float frameSlot = floor(t * 12.0);        /* the damage pattern changes 12 times a second, like a stream */
		float hb = KLX_Hash(block + frameSlot * float2(7.13, 3.71));
		float hit = step(hb, qa * 0.22);
		float2 slip = (float2(KLX_Hash(block + 11.0 + frameSlot), KLX_Hash(block + 23.0 + frameSlot)) - 0.5) * bsize * 1.5;
		float3 bc = KLX_Fetch((block + 0.5) * bsize + slip * hit);
		c = lerp(c, bc, hit * 0.85);
		float levels = lerp(64.0, 14.0, qa);
		c = lerp(c, floor(c * levels + 0.5) / levels, saturate(qa * 1.5) * 0.6);
	}

	/* ---- exposure pumps: muzzle flashes overshoot the camera's auto exposure; a hit dips it; down is dark */
	{
		float flick = saturate(sin(t * 47.0) * sin(t * 13.1 + 0.5) * 2.0);
		float e = 1.0 + f * 0.22 * flick - h * 0.22 * (0.6 + 0.4 * sin(t * 9.0)) - d * 0.30;
		c *= lerp(1.0, e, PumpAmount);
	}

	/* ---- hurt / down: drained, reddish colour */
	{
		float l = dot(c, KLX_LUMA);
		c = lerp(c, l.xxx, saturate(h * 0.6 + d * 0.5) * HurtColour);
		c = lerp(c, l * float3(1.25, 0.62, 0.55), saturate(h * 0.35) * HurtColour);
	}

	/* ---- vignette pulse (red-edged when hurt) */
	{
		float2 v = uv - 0.5; v.x *= BUFFER_ASPECT_RATIO;
		float edge = smoothstep(0.25, 1.05, dot(v, v) * 2.0);
		float va = (0.12 * f + h * (0.35 + 0.15 * sin(t * 7.5)) + 0.45 * d + 0.08 * s) * VignetteAmount;
		c *= 1.0 - saturate(va) * edge;
		c *= lerp(float3(1.0, 1.0, 1.0), float3(1.0, 0.35, 0.3), saturate(h * 0.6 * HurtColour) * edge);
	}

	/* ---- sensor noise (gain goes up when the camera is stressed) */
	{
		float n = KLX_Hash(pos.xy + frac(t * 7.31) * float2(1013.0, 797.0)) - 0.5;
		c += n * (0.04 * f + 0.06 * h + 0.05 * d) * NoiseAmount;
	}

	return saturate(c);
}

technique KL_CameraFX < ui_tooltip = "Kane & Lynch 2: raw handheld-camera layer (shake, distortion, aberration, compression) driven by KLHook: KL_Fire / KL_Hurt / KL_Down / KL_Speed. Clean while those are 0. Put it LAST."; >
{
	pass { VertexShader = PostProcessVS; PixelShader = PS_KLX_Camera; }
}
