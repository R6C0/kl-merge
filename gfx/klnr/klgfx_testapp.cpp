// klgfx_testapp.exe (32-bit): a small Direct3D 9 program that loads the KLGfx d3d9.dll beside it the way kl2.exe does
// (static import of Direct3DCreate9), draws, presents, resets, and creates shaders and textures on a second thread
// while it draws (the game's device is multithreaded too). With KLGfx.ini [NR] Enable=1 Test=1, the frames go through
// klnr.exe and come back with the right half grey; the D3DSWAPEFFECT_COPY back buffer is read after Present to check.
//   klgfx_testapp.exe [seconds]      exit code 0 = the last frames came back processed, Reset worked, no crash
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>

static volatile LONG g_stop;
static IDirect3DDevice9 *g_dev;

// vs_2_0: dcl_position v0; mov oPos, v0
static const DWORD kVs[] = {0xFFFE0200, 0x0200001F, 0x80000000, 0x900F0000, 0x02000001, 0xC00F0000, 0x90E40000, 0x0000FFFF};
// ps_2_0: def c0, 0.9999999, 0, 0, 1; mov oC0, c0. The red value's bits (0x3F7FFFFE) look like a comment token,
// which made KLGfx 0.1's shader scan run past the end of the code: bound during the capture, it must be parsed safely.
static const DWORD kPs[] = {0xFFFF0200, 0x05000051, 0xA00F0000, 0x3F7FFFFE, 0x00000000, 0x00000000, 0x3F800000,
                            0x02000001, 0x800F0800, 0xA0E40000, 0x0000FFFF};
static IDirect3DPixelShader9 *g_ps;

static DWORD WINAPI churn(void *)
{
    unsigned n = 0;
    while (!g_stop) {
        IDirect3DVertexShader9 *vs = nullptr;
        IDirect3DPixelShader9 *ps = nullptr;
        IDirect3DTexture9 *t = nullptr;
        g_dev->CreateVertexShader(kVs, &vs);
        g_dev->CreatePixelShader(kPs, &ps);
        g_dev->CreateTexture(64, 64, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &t, nullptr);
        if (vs) vs->Release();
        if (ps) ps->Release();
        if (t) t->Release();
        n++;
    }
    printf("churn thread: %u rounds of shader/texture create + release\n", n);
    return 0;
}

struct V { float x, y, z, rhw; DWORD c; };

static void quad(IDirect3DDevice9 *d, float x0, float y0, float x1, float y1, DWORD a, DWORD b)
{
    V v[4] = {{x0, y0, 0.5f, 1, a}, {x1, y0, 0.5f, 1, b}, {x0, y1, 0.5f, 1, b}, {x1, y1, 0.5f, 1, a}};
    d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP, 2, v, sizeof(V));
}

// Right half grey (every pixel R == G == B) and left half coloured: the frame went through klnr.exe in test mode.
static int check_processed(IDirect3DDevice9 *d, UINT w, UINT h)
{
    IDirect3DSurface9 *bb = nullptr, *sys = nullptr;
    if (FAILED(d->GetBackBuffer(0, 0, D3DBACKBUFFER_TYPE_MONO, &bb))) return -1;
    D3DSURFACE_DESC sd;
    bb->GetDesc(&sd);
    int result = -1;
    if (SUCCEEDED(d->CreateOffscreenPlainSurface(w, h, sd.Format, D3DPOOL_SYSTEMMEM, &sys, nullptr)) &&
        SUCCEEDED(d->GetRenderTargetData(bb, sys))) {
        D3DLOCKED_RECT lr;
        if (SUCCEEDED(sys->LockRect(&lr, nullptr, D3DLOCK_READONLY))) {
            unsigned grey_right = 0, colour_left = 0, total = 0;
            for (UINT y = 8; y < h - 8; y += 4)
                for (UINT x = 8; x < w - 8; x += 4) {
                    const BYTE *p = (const BYTE *)lr.pBits + y * lr.Pitch + x * 4;
                    bool grey = p[0] == p[1] && p[1] == p[2];
                    if (x > w / 2 + 2) { grey_right += grey; total++; }
                    else if (x < w / 2 - 2) colour_left += !grey;
                }
            sys->UnlockRect();
            result = (grey_right == total && colour_left > total / 4) ? 1 : 0;
        }
    }
    if (sys) sys->Release();
    bb->Release();
    return result;
}

int main(int argc, char **argv)
{
    double seconds = argc > 1 ? atof(argv[1]) : 6;
    WNDCLASSA wc = {};
    wc.lpfnWndProc = DefWindowProcA;
    wc.hInstance = GetModuleHandleA(nullptr);
    wc.lpszClassName = "klgfxtest";
    RegisterClassA(&wc);
    HWND hwnd = CreateWindowA("klgfxtest", "klgfx test", WS_OVERLAPPEDWINDOW, 0, 0, 840, 640, nullptr, nullptr, wc.hInstance, nullptr);
    ShowWindow(hwnd, SW_SHOW);
    IDirect3D9 *d3d = Direct3DCreate9(D3D_SDK_VERSION);
    if (!d3d) { printf("FAIL: Direct3DCreate9\n"); return 2; }
    D3DPRESENT_PARAMETERS pp = {};
    pp.Windowed = TRUE;
    pp.SwapEffect = D3DSWAPEFFECT_COPY;   // the back buffer keeps the presented frame, so it can be checked after Present
    pp.BackBufferFormat = D3DFMT_X8R8G8B8;
    pp.BackBufferWidth = 640;
    pp.BackBufferHeight = 480;
    pp.hDeviceWindow = hwnd;
    pp.EnableAutoDepthStencil = TRUE;
    pp.AutoDepthStencilFormat = D3DFMT_D24S8;
    pp.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;
    HRESULT hr = d3d->CreateDevice(0, D3DDEVTYPE_HAL, hwnd, D3DCREATE_HARDWARE_VERTEXPROCESSING | D3DCREATE_MULTITHREADED, &pp, &g_dev);
    if (FAILED(hr))
        hr = d3d->CreateDevice(0, D3DDEVTYPE_HAL, hwnd, D3DCREATE_SOFTWARE_VERTEXPROCESSING | D3DCREATE_MULTITHREADED, &pp, &g_dev);
    if (FAILED(hr)) { printf("FAIL: CreateDevice %#lx\n", hr); return 2; }
    HANDLE thread = CreateThread(nullptr, 0, churn, nullptr, 0, nullptr);
    DWORD t0 = GetTickCount();
    unsigned frames = 0, processed = 0, checked = 0, resets = 0;
    bool reset_done = false;
    while (GetTickCount() - t0 < seconds * 1000) {
        MSG m;
        while (PeekMessageA(&m, nullptr, 0, 0, PM_REMOVE)) DispatchMessageA(&m);
        if (!reset_done && GetTickCount() - t0 > seconds * 500) {
            pp.BackBufferWidth = 800;
            pp.BackBufferHeight = 600;
            hr = g_dev->Reset(&pp);
            printf("Reset to 800x600: %#lx\n", hr);
            resets += SUCCEEDED(hr);
            reset_done = true;
        }
        g_dev->Clear(0, nullptr, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, D3DCOLOR_XRGB(20, 40, 90), 1.0f, 0);
        g_dev->BeginScene();
        g_dev->SetFVF(D3DFVF_XYZRHW | D3DFVF_DIFFUSE);
        g_dev->SetRenderState(D3DRS_LIGHTING, FALSE);
        float w = (float)pp.BackBufferWidth, h = (float)pp.BackBufferHeight, s = (float)(frames % 100) / 100.0f;
        quad(g_dev, 0, 0, w, h, D3DCOLOR_XRGB(200, 60, 30), D3DCOLOR_XRGB(30, 160, 220));
        quad(g_dev, w * 0.1f + s * w * 0.3f, h * 0.3f, w * 0.4f + s * w * 0.3f, h * 0.7f, D3DCOLOR_XRGB(250, 250, 40), D3DCOLOR_XRGB(40, 220, 60));
        if (!g_ps) g_dev->CreatePixelShader(kPs, &g_ps);
        g_dev->SetPixelShader(g_ps);   // a red bar drawn with the pixel shader above
        quad(g_dev, w * 0.05f, h * 0.8f, w * 0.45f, h * 0.9f, 0, 0);
        g_dev->SetPixelShader(nullptr);
        g_dev->EndScene();
        if (frames & 1) {   // odd frames through swap chain 0's Present (kl2.exe may use either path)
            IDirect3DSwapChain9 *sc = nullptr;
            if (SUCCEEDED(g_dev->GetSwapChain(0, &sc)) && sc) {
                sc->Present(nullptr, nullptr, nullptr, nullptr, 0);
                sc->Release();
            }
        } else {
            g_dev->Present(nullptr, nullptr, nullptr, nullptr);
        }
        frames++;
        if (frames % 20 == 0) {
            int r = check_processed(g_dev, pp.BackBufferWidth, pp.BackBufferHeight);
            if (r >= 0) { checked++; processed += r; }
        }
    }
    g_stop = 1;
    WaitForSingleObject(thread, 5000);
    int last = check_processed(g_dev, pp.BackBufferWidth, pp.BackBufferHeight);
    printf("%u frames in %.1f s; %u of %u checked frames came back processed; last frame %s; resets %u\n", frames, seconds, processed,
           checked, last == 1 ? "processed" : "NOT processed", resets);
    if (g_ps) g_ps->Release();
    g_dev->Release();
    d3d->Release();
    bool pass = last == 1 && resets == 1;
    printf("%s\n", pass ? "PASS" : "FAIL");
    return pass ? 0 : 1;
}
