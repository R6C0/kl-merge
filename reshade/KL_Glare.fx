/*
 * KL_Glare.fx - a stable anamorphic lens glare for Kane & Lynch 2 (KL Merge, 2026-10-15, worker fx).
 *
 * "Lens glare to be nice - sometimes it is, but sometimes it gets displayed like the camera feel."
 * A clean horizontal anamorphic streak (cool blue, Heat / Mann style) on real light sources only:
 *   - ISOLATION TEST: a pixel only glares when it is bright AND clearly brighter than a ring around it
 *     (radius ~2 % of the screen height). A lamp, a muzzle flash, a car light pass; a white sky, a lit wall,
 *     a bright floor do not -> the glare can never wash the frame.
 *   - Soft threshold knee (no hard on / off at the threshold) + TEMPORAL SMOOTHING of the streak (frame-rate
 *     independent, rises a little faster than it falls) -> no flicker, no popping when a light crosses a texel.
 *   - Soft clamp to "Max glare" and a screen blend (never above white, never adds on top of what is already white).
 *
 * The game's own lens flares / camera artefacts are drawn by the game, before ReShade: this effect cannot remove
 * them (see README). Use it with the game's flare as is, or have the hook turn the game's one off if it can.
 *
 * Passes (all but the last at 1/8 width x 1/4 height = 320 x 360 at 1440p, RGBA16F):
 *   Pre (8 taps) -> Streak1 (9 taps, step 1) -> Streak2 (9, step 4) -> Streak3 (9, step 14, + mix)
 *   -> Temporal (2) -> Store (1) -> Composite at full res (2 taps).
 * Expected cost: about 0.05-0.08 ms at 2560 x 1440 on an RTX 4070 Ti class card. Direct3D 9 / shader model 3 safe.
 */
#include "ReShade.fxh"

uniform float Threshold   < ui_type = "slider"; ui_min = 0.5; ui_max = 1.0; ui_step = 0.005; ui_label = "Threshold (brightness that glares)"; > = 0.80;
uniform float Knee        < ui_type = "slider"; ui_min = 0.01; ui_max = 0.3; ui_step = 0.005; ui_label = "Threshold softness"; > = 0.14;
uniform float Isolation   < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_label = "Light sources only (isolation)"; ui_tooltip = "1 = only small bright sources glare, big bright areas (sky, walls) never do."; > = 1.0;
uniform float RingRadius  < ui_type = "slider"; ui_min = 0.005; ui_max = 0.06; ui_step = 0.001; ui_label = "Largest light size (fraction of screen height)"; > = 0.02;
uniform float Intensity   < ui_type = "slider"; ui_min = 0.0; ui_max = 8.0; ui_step = 0.01; ui_label = "Intensity"; > = 2.2;
uniform float Length      < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_label = "Long tail amount"; > = 0.6;
uniform float MaxGlare    < ui_type = "slider"; ui_min = 0.05; ui_max = 0.8; ui_step = 0.01; ui_label = "Max glare (clamp)"; > = 0.35;
uniform float3 Tint       < ui_type = "color"; ui_label = "Streak tint"; > = float3(0.55, 0.75, 1.00);
uniform float TintAmount  < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_label = "Tint amount (0 = light's own colour)"; > = 0.7;
uniform float Smoothing   < ui_type = "slider"; ui_min = 0.0; ui_max = 0.3; ui_step = 0.005; ui_label = "Temporal smoothing (s)"; ui_tooltip = "Higher = calmer, but a slight lag when the camera moves fast. 0 = off."; > = 0.06;
uniform bool  GlareDebug  < ui_label = "Show the glare alone (debug)"; > = false;

uniform float KLG_FrameTime < source = "frametime"; >;

#define KLG_W (BUFFER_WIDTH / 8)
#define KLG_H (BUFFER_HEIGHT / 4)

texture KLG_ATex    { Width = KLG_W; Height = KLG_H; Format = RGBA16F; };
texture KLG_BTex    { Width = KLG_W; Height = KLG_H; Format = RGBA16F; };
texture KLG_CTex    { Width = KLG_W; Height = KLG_H; Format = RGBA16F; };
texture KLG_DTex    { Width = KLG_W; Height = KLG_H; Format = RGBA16F; };
texture KLG_HistTex { Width = KLG_W; Height = KLG_H; Format = RGBA16F; };
sampler KLG_A    { Texture = KLG_ATex;    AddressU = CLAMP; AddressV = CLAMP; };
sampler KLG_B    { Texture = KLG_BTex;    AddressU = CLAMP; AddressV = CLAMP; };
sampler KLG_C    { Texture = KLG_CTex;    AddressU = CLAMP; AddressV = CLAMP; };
sampler KLG_D    { Texture = KLG_DTex;    AddressU = CLAMP; AddressV = CLAMP; };
sampler KLG_Hist { Texture = KLG_HistTex; AddressU = CLAMP; AddressV = CLAMP; };

static const float3 KLG_LUMA = float3(0.2126, 0.7152, 0.0722);

float KLG_L(float2 uv) { return dot(tex2Dlod(ReShade::BackBuffer, float4(uv, 0, 0)).rgb, KLG_LUMA); }

/* ---- 1. what glares: bright, soft-kneed, and isolated from its surroundings */
float4 PS_KLG_Pre(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float2 o = BUFFER_PIXEL_SIZE * float2(2.0, 1.0);   /* four bilinear taps cover the 8 x 4 pixel cell */
	float3 c = (tex2Dlod(ReShade::BackBuffer, float4(uv + float2(-o.x, -o.y), 0, 0)).rgb
	          + tex2Dlod(ReShade::BackBuffer, float4(uv + float2( o.x, -o.y), 0, 0)).rgb
	          + tex2Dlod(ReShade::BackBuffer, float4(uv + float2(-o.x,  o.y), 0, 0)).rgb
	          + tex2Dlod(ReShade::BackBuffer, float4(uv + float2( o.x,  o.y), 0, 0)).rgb) * 0.25;
	float l = dot(c, KLG_LUMA);

	float bright = smoothstep(Threshold, min(Threshold + Knee, 1.0) + 0.0001, l);

	float2 r = float2(RingRadius / BUFFER_ASPECT_RATIO, RingRadius);
	float ring = max(max(KLG_L(uv + float2(r.x, 0)), KLG_L(uv - float2(r.x, 0))),
	                 max(KLG_L(uv + float2(0, r.y)), KLG_L(uv - float2(0, r.y))));
	float isol = saturate((l - ring) / 0.25);
	float w = bright * lerp(1.0, isol, Isolation);
	return float4(c * w, w);
}

/* ---- 2. the streak: three horizontal 9-tap passes with growing steps */
float4 KLG_Streak(sampler s, float2 uv, float stepTexels)
{
	float dx = stepTexels / KLG_W;
	float4 acc = tex2Dlod(s, float4(uv, 0, 0));
	float wsum = 1.0;
	[unroll] for (int i = 1; i <= 4; i++)
	{
		float wi = exp(-0.55 * i);
		acc += (tex2Dlod(s, float4(uv + float2(dx * i, 0), 0, 0)) + tex2Dlod(s, float4(uv - float2(dx * i, 0), 0, 0))) * wi;
		wsum += 2.0 * wi;
	}
	return acc / wsum;
}
float4 PS_KLG_S1(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target { return KLG_Streak(KLG_A, uv, 1.0); }
float4 PS_KLG_S2(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target { return KLG_Streak(KLG_B, uv, 4.0); }
float4 PS_KLG_S3(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	/* bright short core (S2) + long faint tail (S3) */
	float4 tail = KLG_Streak(KLG_C, uv, 14.0);
	float4 core = tex2Dlod(KLG_C, float4(uv, 0, 0));
	return core * 1.0 + tail * (Length * 2.5);
}

/* ---- 3. temporal smoothing (frame-rate independent; rises twice as fast as it falls) */
float4 PS_KLG_Temporal(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float4 cur  = tex2Dlod(KLG_B, float4(uv, 0, 0));
	float4 prev = tex2Dlod(KLG_Hist, float4(uv, 0, 0));
	float dt = max(KLG_FrameTime, 0.0) * 0.001;
	float tau = max(Smoothing, 1e-4);
	float4 aUp = 1.0 - exp(-dt / (tau * 0.5));
	float4 aDn = 1.0 - exp(-dt / tau);
	float4 a = lerp(aDn, aUp, step(prev, cur));
	a = (Smoothing <= 0.0) ? float4(1.0, 1.0, 1.0, 1.0) : saturate(a);
	return lerp(prev, cur, a);
}
float4 PS_KLG_Store(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target { return tex2Dlod(KLG_D, float4(uv, 0, 0)); }

/* ---- 4. composite: tint, soft clamp, screen blend */
float3 PS_KLG_Composite(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float3 c = tex2D(ReShade::BackBuffer, uv).rgb;
	float3 g = tex2D(KLG_D, uv).rgb * Intensity;
	float gl = dot(g, KLG_LUMA);
	g = lerp(g, gl * Tint / max(dot(Tint, KLG_LUMA), 1e-3), TintAmount);
	g = MaxGlare * (1.0 - exp(-max(g, 0.0) / MaxGlare));                 /* soft clamp: never above MaxGlare */
	g *= 1.0 - 0.7 * smoothstep(0.80, 1.0, dot(c, KLG_LUMA));           /* do not pile onto what is already white */
	if (GlareDebug) return g / MaxGlare;
	return 1.0 - (1.0 - c) * (1.0 - g);                                  /* screen */
}

technique KL_Glare < ui_tooltip = "Kane & Lynch 2: stable anamorphic lens glare on light sources only (isolation test, temporal smoothing, clamped). Put it after KL_Look, before KL_CameraFX."; >
{
	pass Pre       { VertexShader = PostProcessVS; PixelShader = PS_KLG_Pre;       RenderTarget = KLG_ATex; }
	pass Streak1   { VertexShader = PostProcessVS; PixelShader = PS_KLG_S1;        RenderTarget = KLG_BTex; }
	pass Streak2   { VertexShader = PostProcessVS; PixelShader = PS_KLG_S2;        RenderTarget = KLG_CTex; }
	pass Streak3   { VertexShader = PostProcessVS; PixelShader = PS_KLG_S3;        RenderTarget = KLG_BTex; }
	pass Temporal  { VertexShader = PostProcessVS; PixelShader = PS_KLG_Temporal;  RenderTarget = KLG_DTex; }
	pass Store     { VertexShader = PostProcessVS; PixelShader = PS_KLG_Store;     RenderTarget = KLG_HistTex; }
	pass Composite { VertexShader = PostProcessVS; PixelShader = PS_KLG_Composite; }
}
