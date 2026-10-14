/*
 * KL_FXAA.fx - edge anti-aliasing for Kane & Lynch 2 (2026-10-14, the owner: 'gotta apply some anti aliasing its got too many zig zag lines').
 * One pass, no depth: a fast approximate AA in the manner of FXAA 3.11 (luma edges, a search along the edge, a sub-pixel blend).
 * Written here for this game; Direct3D 9 (shader model 3) safe. Put it FIRST in the list (before the grade / camcorder look).
 */
#include "ReShade.fxh"

uniform float Subpix      < ui_type = "slider"; ui_min = 0.0; ui_max = 1.0; ui_step = 0.01; ui_label = "Sub-pixel smoothing (more = softer)"; > = 0.60;
uniform float EdgeMin     < ui_type = "slider"; ui_min = 0.02; ui_max = 0.33; ui_step = 0.005; ui_label = "Edge threshold (lower = more edges)"; > = 0.10;
uniform float EdgeMinDark < ui_type = "slider"; ui_min = 0.0; ui_max = 0.1; ui_step = 0.001; ui_label = "Ignore edges darker than"; > = 0.0312;

static const float3 KLA_LUMA = float3(0.299, 0.587, 0.114);
#define KLA_STEPS 10
static const float KLA_STEP[KLA_STEPS] = { 1.0, 1.0, 1.0, 1.0, 1.5, 2.0, 2.0, 2.0, 4.0, 8.0 };

float KLA_L(float2 uv) { return dot(tex2Dlod(ReShade::BackBuffer, float4(uv, 0, 0)).rgb, KLA_LUMA); }

float3 PS_FXAA(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float2 px = BUFFER_PIXEL_SIZE;
    float3 rgbM = tex2Dlod(ReShade::BackBuffer, float4(uv, 0, 0)).rgb;
    float lM = dot(rgbM, KLA_LUMA);
    float lN = KLA_L(uv + float2(0, -px.y)), lS = KLA_L(uv + float2(0, px.y));
    float lW = KLA_L(uv + float2(-px.x, 0)), lE = KLA_L(uv + float2(px.x, 0));
    float lMax = max(lM, max(max(lN, lS), max(lW, lE))), lMin = min(lM, min(min(lN, lS), min(lW, lE)));
    float range = lMax - lMin;
    if (range < max(EdgeMinDark, lMax * EdgeMin)) return rgbM;

    float lNW = KLA_L(uv + float2(-px.x, -px.y)), lNE = KLA_L(uv + float2(px.x, -px.y));
    float lSW = KLA_L(uv + float2(-px.x, px.y)),  lSE = KLA_L(uv + float2(px.x, px.y));

    /* sub-pixel amount from the 3x3 average */
    float lAvg = (2.0 * (lN + lS + lW + lE) + (lNW + lNE + lSW + lSE)) / 12.0;
    float sub = saturate(abs(lAvg - lM) / range);
    sub = smoothstep(0.0, 1.0, sub); sub = sub * sub * Subpix;

    /* edge direction */
    float edgeH = abs(lNW - 2.0 * lW + lSW) + 2.0 * abs(lN - 2.0 * lM + lS) + abs(lNE - 2.0 * lE + lSE);
    float edgeV = abs(lNW - 2.0 * lN + lNE) + 2.0 * abs(lW - 2.0 * lM + lE) + abs(lSW - 2.0 * lS + lSE);
    bool horz = edgeH >= edgeV;
    float l1 = horz ? lN : lW, l2 = horz ? lS : lE;
    float g1 = abs(l1 - lM), g2 = abs(l2 - lM);
    float stepLen = horz ? px.y : px.x;
    float lLocal, grad;
    if (g1 >= g2) { stepLen = -stepLen; lLocal = 0.5 * (l1 + lM); grad = g1; }
    else          { lLocal = 0.5 * (l2 + lM); grad = g2; }
    float2 uvE = uv;
    if (horz) uvE.y += stepLen * 0.5; else uvE.x += stepLen * 0.5;

    /* walk both ways along the edge */
    float2 dir = horz ? float2(px.x, 0) : float2(0, px.y);
    float2 uvP = uvE + dir, uvN = uvE - dir;
    float gScaled = grad * 0.25;
    float eP = KLA_L(uvP) - lLocal, eN = KLA_L(uvN) - lLocal;
    bool doneP = abs(eP) >= gScaled, doneN = abs(eN) >= gScaled;
    [unroll] for (int i = 1; i < KLA_STEPS; i++) {
        if (!doneP) { uvP += dir * KLA_STEP[i]; eP = KLA_L(uvP) - lLocal; doneP = abs(eP) >= gScaled; }
        if (!doneN) { uvN -= dir * KLA_STEP[i]; eN = KLA_L(uvN) - lLocal; doneN = abs(eN) >= gScaled; }
    }
    float dP = horz ? (uvP.x - uv.x) : (uvP.y - uv.y);
    float dN = horz ? (uv.x - uvN.x) : (uv.y - uvN.y);
    bool nearN = dN < dP;
    float dist = min(dN, dP), len = dN + dP;
    bool mLess = (lM - lLocal) < 0.0;
    bool good = ((nearN ? eN : eP) < 0.0) != mLess;
    float off = good ? (0.5 - dist / len) : 0.0;
    off = max(off, sub);

    float2 uvF = uv;
    if (horz) uvF.y += off * stepLen; else uvF.x += off * stepLen;
    return tex2Dlod(ReShade::BackBuffer, float4(uvF, 0, 0)).rgb;
}

technique KL_FXAA < ui_tooltip = "Kane & Lynch 2: fast edge anti-aliasing (FXAA-style). Keep it FIRST in the list."; >
{
    pass { VertexShader = PostProcessVS; PixelShader = PS_FXAA; }
}
