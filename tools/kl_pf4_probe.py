"""kl_pf4_probe.py - the 16 'mesh probes' of the game's down test b (kl2 0x70f330), reproduced offline (re/bots_down.md 9).

0x70f330 calls PF4::ZData slot 41 (0x4dd5f0) 16 times with the bot's place and a vector of 100 units at i * 22.5 degrees.
The slot (1) locates his place on the mesh (slot 0x80 = 0x68bef0 -> 0x55e6e0; failing = off the mesh), (2) traces the segment
along polygon edges (slot 0xa8 = 0x82b950, returns the fraction reached; the caller wants >= 1.0), (3) locates the end point.
A probe fails when the segment meets an edge with no neighbour (a wall, a cover box) before 100 units, or ends off the mesh.
Mesh coordinates: vertex (x, z, height, normal x, normal z); a bot at (X, Y, Z) is (X, Z) with height Y.
MODEL: a 2-D polygon walk; the polygon is the one nearest in height within 250 (the game's tolerance was NOT read); the end point's
locate is not modelled. Usage:
  python kl_pf4_probe.py stat <level zip> ...        pass rate over polygon centres
  python kl_pf4_probe.py at <level zip> x y z        (polygon, the 16 fractions) at a place
"""
import sys, os, struct, zipfile, glob, random
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_gms, kl_scene, kl_pf4
def nav_from_zip(path):
    with zipfile.ZipFile(path) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        return kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf'])).nav
class Mesh:
    def __init__(s, block):
        n, A = kl_pf4.split(block, True)
        s.n=n
        s.areas=[struct.unpack('<12I6f', r) for r in A[4]]
        s.polys=[struct.unpack('<BBHIIIIIII', r) for r in A[3]]
        s.edges=[struct.unpack('<iII', r) for r in A[9]]
        s.vert=[struct.unpack('<5f', r) for r in A[6]]
        s.wp=[struct.unpack('<3f', r[:12]) for r in A[5]]

import math
def build(M):
    M.P=[]
    for p in M.polys:
        n=p[0]; first=p[5]
        vs=[M.edges[first+i][1] for i in range(n)]
        nb=[M.edges[first+i][0] for i in range(n)]
        M.P.append((vs,nb,p[4]))
    return M
def check_adj(M):
    ok=bad=0; alt=0
    for pi,(vs,nb,a) in enumerate(M.P):
        n=len(vs)
        for i in range(n):
            q=nb[i]
            if q<0: continue
            if q>=len(M.P): continue
            qv=set(M.P[q][0])
            if vs[i] in qv and vs[(i+1)%n] in qv: ok+=1
            elif vs[i] in qv and vs[(i-1)%n] in qv: alt+=1
            else: bad+=1
    return ok,alt,bad

def locate(M, x, z, y, dh=250):
    best=None
    for pi,(vs,nb,a) in enumerate(M.P):
        V=[M.vert[v] for v in vs]
        xs=[v[0] for v in V]; zs=[v[1] for v in V]
        if x<min(xs) or x>max(xs) or z<min(zs) or z>max(zs): continue
        inside=False; n=len(V)
        for i in range(n):
            x1,z1=V[i][0],V[i][1]; x2,z2=V[(i+1)%n][0],V[(i+1)%n][1]
            if (z1>z)!=(z2>z) and x < (x2-x1)*(z-z1)/(z2-z1)+x1: inside=not inside
        if not inside: continue
        h=sum(v[2] for v in V)/n
        d=abs(h-y)
        if d<=dh and (best is None or d<best[0]): best=(d,pi)
    return None if best is None else best[1]
def trace(M, pi, x, z, dx, dz, L=100.0):
    """-> fraction reached (1.0 = full), polygon at end"""
    t_done=0.0; seen=0
    while seen<64:
        seen+=1
        vs,nb,a=M.P[pi]; n=len(vs)
        best=None
        for i in range(n):
            A=M.vert[vs[i]]; B=M.vert[vs[(i+1)%n]]
            ex,ez=B[0]-A[0],B[1]-A[1]
            den=dx*ez-dz*ex
            if abs(den)<1e-9: continue
            # solve x+dx*t = A + ex*s
            t=((A[0]-x)*ez-(A[1]-z)*ex)/den
            s=((A[0]-x)*dz-(A[1]-z)*dx)/den
            if -1e-6<=s<=1+1e-6 and t>1e-4:
                if best is None or t<best[0]: best=(t,i)
        if best is None or best[0]>=L: return 1.0, pi
        t,i=best
        q=nb[i]
        if q==-1: return (t_done+t)/L if False else t/L, pi
        if q<-1: return 1.0, pi
        x+=dx*t; z+=dz*t; L-=t; dx,dz=dx,dz; pi=q
        t_done+=t
    return 1.0, pi
def probes(M, x, y, z, r=100.0):
    pi=locate(M,x,z,y)
    if pi is None: return None, []
    out=[]
    for i in range(16):
        a=2*math.pi*i/16
        f,_=trace(M,pi,x,z,math.cos(a),math.sin(a),r)
        out.append(round(f,2))
    return pi,out

def area(V):
    a=0
    for i in range(len(V)):
        x1,z1=V[i][0],V[i][1]; x2,z2=V[(i+1)%len(V)][0],V[(i+1)%len(V)][1]
        a+=x1*z2-x2*z1
    return abs(a)/2
def stat(zp,label,N=400):
    try: M=build(Mesh(nav_from_zip(zp)))
    except Exception as e: print(label,'ERR',e); return
    random.seed(1)
    idx=list(range(len(M.P))); random.shuffle(idx)
    tot=ok=loc=0; w=0; wok=0
    for pi in idx[:N]:
        vs=M.P[pi][0]; V=[M.vert[v] for v in vs]
        if len(V)<3: continue
        cx=sum(v[0] for v in V)/len(V); cz=sum(v[1] for v in V)/len(V); cy=sum(v[2] for v in V)/len(V)
        A=area(V)
        p2,o=probes(M,cx,cy,cz)
        tot+=1; w+=A
        if p2 is not None:
            loc+=1
            if all(f>=1.0 for f in o): ok+=1; wok+=A
    print('%-10s polys %5d sampled %3d located %3d pass-all-16 %3d  (%.0f %% of sampled; %.0f %% by area)'%(label,len(M.P),tot,loc,ok,100.0*ok/max(tot,1),100.0*wok/max(w,1)))

if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'stat':
        for z in sys.argv[2:]: stat(z, os.path.basename(os.path.dirname(z)))
    elif len(sys.argv) == 6 and sys.argv[1] == 'at':
        M = build(Mesh(nav_from_zip(sys.argv[2])))
        print(probes(M, float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])))
    else:
        print(__doc__)
