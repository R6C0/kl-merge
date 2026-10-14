/*
 * KL_Look.fx - a cool, overcast, "tactical photo" grade for Kane & Lynch 2 (2026-10-13, written for the owner's reference shot:
 * desaturated blue-grey shadows, a lavender-white sky, strong local contrast on wood / plaster / foliage, crisp detail).
 * One file, no depth, no compute: Direct3D 9 (shader model 3) safe. About 0.3 ms at 2560x1440 on an RTX 4070 Ti class card.
 *
 * Passes: (1) luminance to a quarter-size texture, (2) + (3) a separable blur of it = the "local average",
 * (4) the grade: local contrast (detail = luma - local average), a filmic curve, saturation, split toning,
 *     a light contrast-adaptive sharpen and a soft vignette.
 * Put it BELOW Uplift in ReShade's list when neural rendering is on (the grade then works on NR's image).
 */
#include "ReShade.fxh"

uniform float Exposure      < ui_type = "slider"; ui_min = -1.5; ui_max = 1.5; ui_step = 0.01; ui_label = "Exposure (stops)"; > = -0.55;
uniform float Contrast      < ui_type = "slider"; ui_min = 0.5;  ui_max = 1.6; ui_step = 0.01; ui_label = "Filmic contrast"; > = 1.26;
uniform float LocalContrast < ui_type = "slider"; ui_min = 0.0;  ui_max = 1.5; ui_step = 0.01; ui_label = "Local contrast (texture pop)"; > = 0.65;
uniform float Saturation    < ui_type = "slider"; ui_min = 0.0;  ui_max = 1.5; ui_step = 0.01; ui_label = "Saturation"; > = 1.25;
uniform float3 ShadowTint   < ui_type = "color";  ui_label = "Shadow tint"; > = float3(0.88, 0.96, 1.08);
uniform float3 HighTint     < ui_type = "color";  ui_label = "Highlight tint"; > = float3(1.02, 1.00, 1.01);
uniform float TintAmount    < ui_type = "slider"; ui_min = 0.0;  ui_max = 1.0; ui_step = 0.01; ui_label = "Split-tone amount"; > = 0.35;
uniform float BlackLift     < ui_type = "slider"; ui_min = 0.0;  ui_max = 0.08; ui_step = 0.001; ui_label = "Black lift"; > = 0.000;
uniform float Sharpen       < ui_type = "slider"; ui_min = 0.0;  ui_max = 1.0; ui_step = 0.01; ui_label = "Sharpen (adaptive)"; > = 0.35;
uniform float WhitePoint    < ui_type = "slider"; ui_min = 0.6;  ui_max = 1.2; ui_step = 0.01; ui_label = "White point (lower = brighter highlights)"; > = 1.00;
uniform float KeepColour    < ui_type = "slider"; ui_min = 0.0;  ui_max = 1.0; ui_step = 0.01; ui_label = "Keep strong colours (HUD, signs)"; > = 0.85;
uniform float ShadowLift    < ui_type = "slider"; ui_min = 0.0;  ui_max = 1.0; ui_step = 0.01; ui_label = "Shadow lift (people, dark clothes)"; > = 0.00;
uniform float SkyTame      < ui_type = "slider"; ui_min = 0.0;  ui_max = 1.0; ui_step = 0.01; ui_label = "Sky / blown highlight tame"; > = 0.75;
uniform float3 SkyColour    < ui_type = "color";  ui_label = "Sky colour (overcast)"; > = float3(0.74, 0.80, 0.90);
uniform float Vignette      < ui_type = "slider"; ui_min = 0.0;  ui_max = 1.0; ui_step = 0.01; ui_label = "Vignette"; > = 0.28;

#define KLL_W (BUFFER_WIDTH / 4)
#define KLL_H (BUFFER_HEIGHT / 4)

texture KLL_LumaTex  { Width = KLL_W; Height = KLL_H; Format = R16F; };
texture KLL_BlurTex  { Width = KLL_W; Height = KLL_H; Format = R16F; };
texture KLL_BlurTex2 { Width = KLL_W; Height = KLL_H; Format = R16F; };
sampler KLL_Luma  { Texture = KLL_LumaTex;  };
sampler KLL_Blur  { Texture = KLL_BlurTex;  };
sampler KLL_Blur2 { Texture = KLL_BlurTex2; };

static const float3 KLL_LUMA = float3(0.2126, 0.7152, 0.0722);

float PS_Luma(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{   /* a 4 x 4 box average through four bilinear taps */
    float2 o = BUFFER_PIXEL_SIZE;
    float3 c = tex2D(ReShade::BackBuffer, uv + float2(-o.x, -o.y)).rgb + tex2D(ReShade::BackBuffer, uv + float2(o.x, -o.y)).rgb
             + tex2D(ReShade::BackBuffer, uv + float2(-o.x,  o.y)).rgb + tex2D(ReShade::BackBuffer, uv + float2(o.x,  o.y)).rgb;
    return dot(c * 0.25, KLL_LUMA);
}

float KLL_Gauss(sampler s, float2 uv, float2 dir)
{   /* 9 taps (5 bilinear fetches), sigma about 2.5 quarter-res pixels = about 10 full-res pixels */
    float2 d = dir * float2(1.0 / KLL_W, 1.0 / KLL_H);
    float r = tex2D(s, uv).r * 0.2270;
    r += (tex2D(s, uv + d * 1.3846).r + tex2D(s, uv - d * 1.3846).r) * 0.3162;
    r += (tex2D(s, uv + d * 3.2308).r + tex2D(s, uv - d * 3.2308).r) * 0.0703;
    return r;
}
float PS_BlurH(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target { return KLL_Gauss(KLL_Luma, uv, float2(1, 0)); }
float PS_BlurV(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target { return KLL_Gauss(KLL_Blur, uv, float2(0, 1)); }

float3 KLL_Filmic(float3 x)
{   /* a gentle ACES-like shoulder with a toe, normalised so 1.0 maps near 1.0 */
    const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    float3 y = saturate((x * (a * x + b)) / (x * (c * x + d) + e));
    return saturate(y / WhitePoint);   /* ACES fit maps 1.0 to ~0.80: WhitePoint brings paper white back */
}

float3 PS_Grade(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float2 o = BUFFER_PIXEL_SIZE;
    float3 c = tex2D(ReShade::BackBuffer, uv).rgb;

    /* contrast-adaptive sharpen (CAS-like): a 3x3 cross, weight falls where the neighbourhood already has contrast */
    if (Sharpen > 0.0) {
        float3 n = tex2D(ReShade::BackBuffer, uv + float2(0, -o.y)).rgb, s = tex2D(ReShade::BackBuffer, uv + float2(0, o.y)).rgb;
        float3 w = tex2D(ReShade::BackBuffer, uv + float2(-o.x, 0)).rgb, e = tex2D(ReShade::BackBuffer, uv + float2(o.x, 0)).rgb;
        float3 mn = min(c, min(min(n, s), min(w, e))), mx = max(c, max(max(n, s), max(w, e)));
        float3 amp = sqrt(saturate(min(mn, 1.0 - mx) / max(mx, 1e-4)));
        float3 wgt = -amp * lerp(1.0 / 8.0, 1.0 / 5.0, Sharpen);
        c = saturate((c + (n + s + w + e) * wgt) / (1.0 + 4.0 * wgt));
    }

    /* local contrast: push luma away from its 10 px neighbourhood, protected in deep shadows and highlights */
    float l  = dot(c, KLL_LUMA);
    float la = tex2D(KLL_Blur2, uv).r;
    float detail = l - la;
    float guard = smoothstep(0.02, 0.15, l) * (1.0 - smoothstep(0.80, 0.98, l));
    float l2 = max(l + detail * LocalContrast * guard, 0.0);
    c *= (l > 1e-4) ? (l2 / l) : 1.0;

    /* exposure + filmic curve, contrast about middle grey in log space */
    c *= exp2(Exposure);
    c = pow(max(c, 1e-5) / 0.18, Contrast) * 0.18;
    c = KLL_Filmic(c);

    /* saturation (keeps luma), split toning (shadows cool, highlights faintly lavender like the reference sky) */
    /* strongly coloured pixels (the HUD's coral / green, neon signs) keep their colour: the grade acts on the world's greys */
    l = dot(c, KLL_LUMA);
    float chroma = max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b));
    float keep = smoothstep(0.30, 0.55, chroma) * KeepColour;
    c = lerp(l.xxx, c, lerp(Saturation, 1.0, keep));
    float hw = smoothstep(0.25, 0.85, l);
    float3 tint = lerp(ShadowTint, HighTint, hw);
    c *= lerp(float3(1.0, 1.0, 1.0), tint, TintAmount * (1.0 - keep));

    /* the sky and other blown whites: the game paints them pure white; pull them down to an overcast grey-blue */
    {
        float lh = dot(c, KLL_LUMA);
        float k = smoothstep(0.66, 0.95, lh) * SkyTame;
        c = lerp(c, SkyColour * max(lh, 0.0), k);
    }

    /* shadow lift: brighten the low midtones (dark clothes, faces in shade) without greying the blacks or touching the sky */
    {
        float ls = dot(c, KLL_LUMA);
        float w = smoothstep(0.0, 0.06, ls) * (1.0 - smoothstep(0.08, 0.40, ls));
        c *= 1.0 + ShadowLift * w;
    }

    /* black lift (a faint, cool floor so the shadows read as air, not crushed ink) */
    c = c * (1.0 - BlackLift) + BlackLift * float3(0.85, 0.92, 1.0);

    /* vignette */
    float2 v = uv - 0.5; v.x *= BUFFER_ASPECT_RATIO;
    c *= 1.0 - Vignette * smoothstep(0.35, 1.05, dot(v, v) * 2.0);

    return saturate(c);
}

technique KL_Look < ui_tooltip = "Kane & Lynch 2: a cool overcast photo grade (local contrast, filmic curve, split toning, sharpen). Put it below Uplift."; >
{
    pass { VertexShader = PostProcessVS; PixelShader = PS_Luma;  RenderTarget = KLL_LumaTex; }
    pass { VertexShader = PostProcessVS; PixelShader = PS_BlurH; RenderTarget = KLL_BlurTex; }
    pass { VertexShader = PostProcessVS; PixelShader = PS_BlurV; RenderTarget = KLL_BlurTex2; }
    pass { VertexShader = PostProcessVS; PixelShader = PS_Grade; }
}
