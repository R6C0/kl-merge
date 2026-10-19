# Netcode references the owner passed on (2026-10-19)

Source: an AI-search answer the owner pasted. The repos it names were NOT opened or checked here.
- miwarnec/Game-Networking-Resources (index)
- petitgamedev/GameNetworkingResources (index)
- minism/fps-netcode (Quake-style prediction and reconciliation)
- Vercidium/lag-compensation (C#)
- Colyseus prototypes
- Mirror, Netcode for Entities
- mas-bandwidth/netcode

## The three rules it gives, against what kl2.exe allows

| Rule | Can we do it? | Why |
|---|---|---|
| Fixed simulation tick, rendering interpolates between ticks | NO | Engine code; hashed .text. |
| Client sends intents, the server is the truth (prediction + reconciliation) | NO | Net-Z replicated datasets are fixed in the exe (re/netcode.md); changing what is sent is a protocol change for every peer. |
| **Snapshot interpolation: show remote players ~100 ms in the past, blend between received samples, never snap** | **YES, display side** | This is the receiver-side smoother: klnetsmooth.c / klrigid.c, through a heap-object vtable-pointer swap. Our own character and the server's hit tests stay as they are. |
| Lag compensation (rewinding hit boxes) | NO | Server hit code; hashed. Showing remotes 100 ms late widens the gap between where you see someone and where the server hits them. Keep the delay small (the 50-100 ms of Source's cl_interp) and make it a key. |

## Starting numbers (Source-engine style; RECALL)
- Interpolation delay = 2 x the send interval (cl_interp_ratio 2), about 100 ms.
- Extrapolate at most ~250 ms when samples stop, then hold.
- Snap only past a large error (Unreal smoothing snaps at a few metres).
