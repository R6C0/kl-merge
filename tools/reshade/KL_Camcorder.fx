/*
 * KL_Camcorder.fx - the "LiveLeak" camcorder look for Kane & Lynch 2, in ONE file (2026-10-14).
 * Written from the parameters of Stethr1's "Liveleak" preset on Nexus (virtual 1280 x 720, a strong luma sharpen, a wide soft
 * bloom, light chromatic aberration, heavy film grain, the teal ambient pulled to grey, a vignette); that preset needs fifteen shaders
 * from eight packs, this is the same idea in four cheap passes with no depth and no compute: Direct3D 9 (shader model 3) safe.
 * Not a copy of any of those shaders.
 */
#include "ReShade.fxh"

uniform float VirtualHeight < ui_type = "slider"; ui_min = 360.0; ui_max = 1440.0; ui_step = 1.0; ui_label = "Camera resolution (lines)"; > = 720.0;
uniform float Sharpen     < ui_type = "slider"; ui_min = 0.0; ui_max = 3.0; ui_step = 0.01; ui_label = "Camera sharpening (crunch)"; > = 1.6;
uniform float Bloom       < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_label = "Bloom"; > = 0.55;
uniform float BloomCurve  < ui_type = "slider"; ui_min = 1.0; ui_max = 5.0; ui_step = 0.01; ui_label = "Bloom threshold curve"; > = 2.5;
uniform float Aberration  < ui_type = "slider"; ui_min = 0.0; ui_max = 4.0; ui_step = 0.01; ui_label = "Chromatic aberration (px at the edge)"; > = 1.6;
uniform float Grain       < ui_type = "slider"; ui_min = 0.0; ui_max = 0.3; ui_step = 0.001; ui_label = "Film grain"; > = 0.075;
uniform float AmbientCrush< ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_label = "Remove the teal ambient"; > = 0.6;
uniform float Saturation  < ui_type = "slider"; ui_min = 0.0; ui_max = 2.0; ui_step = 0.01; ui_label = "Saturation"; > = 1.08;
uniform float Contrast    < ui_type = "slider"; ui_min = 0.5; ui_max = 2.0; ui_step = 0.01; ui_label = "Contrast"; > = 1.12;
uniform float Vignette    < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_label = "Vignette"; > = 0.40;
uniform int   FrameCount  < source = "framecount"; >;

#define KLC_VW 1280
#define KLC_VH 720
#define KLC_BW (BUFFER_WIDTH / 8)
#define KLC_BH (BUFFER_HEIGHT / 8)

texture KLC_VirtTex  { Width = KLC_VW; Height = KLC_VH; Format = RGBA8; };
texture KLC_BrightTex{ Width = KLC_BW; Height = KLC_BH; Format = RGBA16F; };
texture KLC_BlurTex  { Width = KLC_BW; Height = KLC_BH; Format = RGBA16F; };
texture KLC_BlurTex2 { Width = KLC_BW; Height = KLC_BH; Format = RGBA16F; };
sampler KLC_Virt   { Texture = KLC_VirtTex; MagFilter = LINEAR; MinFilter = LINEAR; AddressU = CLAMP; AddressV = CLAMP; };
sampler KLC_Bright { Texture = KLC_BrightTex; };
sampler KLC_Blur   { Texture = KLC_BlurTex; };
sampler KLC_Blur2  { Texture = KLC_BlurTex2; };

static const float3 KLC_LUMA = float3(0.2126, 0.7152, 0.0722);

float3 PS_Virt(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{   /* the camera's sensor: a box average of the back buffer at 1280 x 720 (the "virtual resolution") */
    float2 o = BUFFER_PIXEL_SIZE * 0.5;
    return (tex2D(ReShade::BackBuffer, uv + float2(-o.x, -o.y)).rgb + tex2D(ReShade::BackBuffer, uv + float2(o.x, -o.y)).rgb
          + tex2D(ReShade::BackBuffer, uv + float2(-o.x,  o.y)).rgb + tex2D(ReShade::BackBuffer, uv + float2(o.x,  o.y)).rgb) * 0.25;
}

float4 PS_Bright(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{   /* what blooms: the bright part, raised to a curve */
    float3 c = tex2D(KLC_Virt, uv).rgb;
    float l = dot(c, KLC_LUMA);
    return float4(c * pow(saturate(l), BloomCurve), 1.0);
}

float4 KLC_Gauss(sampler s, float2 uv, float2 dir)
{
    float2 d = dir * float2(1.0 / KLC_BW, 1.0 / KLC_BH) * 2.0;
    float4 r = tex2D(s, uv) * 0.2270;
    r += (tex2D(s, uv + d * 1.3846) + tex2D(s, uv - d * 1.3846)) * 0.3162;
    r += (tex2D(s, uv + d * 3.2308) + tex2D(s, uv - d * 3.2308)) * 0.0703;
    return r;
}
float4 PS_BlurH(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target { return KLC_Gauss(KLC_Bright, uv, float2(1, 0)); }
float4 PS_BlurV(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target { return KLC_Gauss(KLC_Blur, uv, float2(0, 1)); }

float KLC_Hash(float2 p)
{
    p = frac(p * float2(0.1031, 0.1030));
    p += dot(p, p.yx + 33.33);
    return frac((p.x + p.y) * p.x);
}

float3 PS_Final(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    /* the sensor's resolution: sample the 720p image through a coarser grid when VirtualHeight is below 720 */
    float2 grid = float2(VirtualHeight * BUFFER_ASPECT_RATIO, VirtualHeight);
    float2 uvv = (floor(uv * grid) + 0.5) / grid;
    uvv = lerp(uv, uvv, step(VirtualHeight, 719.0));

    /* chromatic aberration: red and blue pulled apart toward the edges */
    float2 fromc = uv - 0.5;
    float2 ca = fromc * dot(fromc, fromc) * 4.0 * Aberration / float2(KLC_VW, KLC_VH);
    float3 c;
    c.r = tex2D(KLC_Virt, uvv + ca).r;
    c.g = tex2D(KLC_Virt, uvv).g;
    c.b = tex2D(KLC_Virt, uvv - ca).b;

    /* camera sharpening: luma unsharp mask on the 720p image (the crunchy edges of a cheap camcorder) */
    float2 p = float2(1.0 / KLC_VW, 1.0 / KLC_VH);
    float3 blur = (tex2D(KLC_Virt, uvv + float2(p.x, p.y)).rgb + tex2D(KLC_Virt, uvv - float2(p.x, p.y)).rgb
                 + tex2D(KLC_Virt, uvv + float2(p.x, -p.y)).rgb + tex2D(KLC_Virt, uvv - float2(p.x, -p.y)).rgb) * 0.25;
    float detail = dot(c - blur, KLC_LUMA);
    c += clamp(detail * Sharpen, -0.12, 0.12);

    /* bloom */
    c += tex2D(KLC_Blur2, uv).rgb * Bloom;

    /* the teal ambient: pull the shadows' blue-green cast toward neutral */
    float l = dot(c, KLC_LUMA);
    float shadow = 1.0 - smoothstep(0.05, 0.45, l);
    c = lerp(c, l.xxx + (c - l.xxx) * 0.6, shadow * AmbientCrush * smoothstep(0.0, 0.08, max(c.g, c.b) - c.r));

    /* contrast and saturation */
    c = saturate((c - 0.5) * Contrast + 0.5);
    l = dot(c, KLC_LUMA);
    c = saturate(lerp(l.xxx, c, Saturation));

    /* film grain, stronger in the mids */
    float n = KLC_Hash(pos.xy + fmod((float)FrameCount, 1024.0) * float2(17.0, 31.0)) - 0.5;
    c += n * Grain * (1.0 - abs(l * 2.0 - 1.0) * 0.6);

    /* vignette */
    float2 v = fromc; v.x *= BUFFER_ASPECT_RATIO;
    c *= 1.0 - Vignette * smoothstep(0.30, 1.10, dot(v, v) * 2.0);
    return saturate(c);
}

technique KL_Camcorder < ui_tooltip = "Kane & Lynch 2: the 'LiveLeak' camcorder look (720p sensor, crunchy sharpening, bloom, aberration, grain)."; >
{
    pass { VertexShader = PostProcessVS; PixelShader = PS_Virt;   RenderTarget = KLC_VirtTex; }
    pass { VertexShader = PostProcessVS; PixelShader = PS_Bright; RenderTarget = KLC_BrightTex; }
    pass { VertexShader = PostProcessVS; PixelShader = PS_BlurH;  RenderTarget = KLC_BlurTex; }
    pass { VertexShader = PostProcessVS; PixelShader = PS_BlurV;  RenderTarget = KLC_BlurTex2; }
    pass { VertexShader = PostProcessVS; PixelShader = PS_Final; }
}
