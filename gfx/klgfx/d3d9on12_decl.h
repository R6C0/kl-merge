// D3D9On12 declarations (Windows SDK d3d9on12.h is not in MinGW's headers).
// Layout and GUID as in the Windows SDK; cross-checked against DXVK's src/d3d9/d3d9_include.h.
// Direct3DCreate9On12 / Direct3DCreate9On12Ex are exported by Windows' own d3d9.dll (ordinals 20/21).
#pragma once
#include <d3d9.h>
#include <unknwn.h>

#define KLG_MAX_D3D9ON12_QUEUES 2

struct KLG_D3D9ON12_ARGS {
    BOOL Enable9On12;
    IUnknown *pD3D12Device;
    IUnknown *ppD3D12Queues[KLG_MAX_D3D9ON12_QUEUES];
    UINT NumQueues;
    UINT NodeMask;
};

typedef IDirect3D9 *(WINAPI *PFN_KLG_Direct3DCreate9On12)(UINT sdk_version, KLG_D3D9ON12_ARGS *override_list,
                                                          UINT override_entry_count);

// {E7FDA234-B589-4049-940D-8878977531C8}
static const GUID KLG_IID_IDirect3DDevice9On12 =
    {0xe7fda234, 0xb589, 0x4049, {0x94, 0x0d, 0x88, 0x78, 0x97, 0x75, 0x31, 0xc8}};

struct ID3D12CommandQueue;
struct ID3D12Fence;

struct KLG_IDirect3DDevice9On12 : public IUnknown {
    virtual HRESULT STDMETHODCALLTYPE GetD3D12Device(REFIID riid, void **object) = 0;
    virtual HRESULT STDMETHODCALLTYPE UnwrapUnderlyingResource(IDirect3DResource9 *resource,
                                                               ID3D12CommandQueue *command_queue, REFIID riid,
                                                               void **object) = 0;
    virtual HRESULT STDMETHODCALLTYPE ReturnUnderlyingResource(IDirect3DResource9 *resource, UINT num_sync,
                                                               UINT64 *signal_values, ID3D12Fence **fences) = 0;
};
