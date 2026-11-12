import struct, sys
def cstr(d,p,align=4):
    e=d.index(b'\0',p); q=e+1
    if align: q=(q+align-1)//align*align
    return d[p:e].decode('latin1'), q
class ANM:
    def __init__(s, d):
        s.d=d
        s.magic, s.fsize_f, s.fsize, s.count = struct.unpack_from('<4sIII',d,0)
        p=0x10; s.ents=[]
        while p < len(d):
            t=struct.unpack_from('<I',d,p)[0]
            if t==5:
                _,sf,size,one,n,size2=struct.unpack_from('<6I',d,p)
                items=struct.unpack_from('<%dI'%n,d,p+24)
                s.ents.append(dict(kind='list',off=p,size=size,items=items)); p+=size
            elif d[p:p+7]==b'anmcol:':
                name,q=cstr(d,p); typ,size=struct.unpack_from('<II',d,q)
                s.ents.append(dict(kind='db',off=p,name=name,typ=typ,size=size,body=q+8)); p=q+size
            else:
                s.tail=p; break
if __name__=='__main__':
    a=ANM(open(sys.argv[1],'rb').read())
    print('count',a.count,'ents',len(a.ents),'tail',hex(a.tail),'file',hex(len(a.d)))
    for x in a.ents:
        if x['kind']=='list': print(hex(x['off']),'list',len(x['items']),x['items'][0] if x['items'] else None,x['items'][-1] if x['items'] else None)
        else: print(hex(x['off']),'db',x['typ'],hex(x['size']),x['name'], struct.unpack_from('<I',a.d,x['body']+len(x['name'])+1+ (-(len(x['name'])+1))%4)[0])
    print(a.d[a.tail:a.tail+96].hex())
