# -*- coding: utf-8 -*-
"""scan_super.py — 找 superclass 实际是 interface / interfaces 实际是 class 的 class（26.3 类型翻转后必炸/必坏）。"""
import json, struct, sys, zipfile
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT/"work/run26/mods-stable"
MC = Path(r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar")
ACC_INTERFACE = 0x0200

def parse(data):
    i=8; cnt=struct.unpack(">H",data[i:i+2])[0]; i+=2
    cp=[None]*cnt; idx=1
    while idx<cnt:
        tag=data[i]; i+=1
        if tag==1:
            ln=struct.unpack(">H",data[i:i+2])[0]; i+=2; cp[idx]=(1,data[i:i+ln].decode("utf-8","replace")); i+=ln
        elif tag in (7,8,16,19,20): cp[idx]=(tag,struct.unpack(">H",data[i:i+2])[0]); i+=2
        elif tag==15: cp[idx]=(tag,struct.unpack(">BH",data[i:i+3])); i+=3
        elif tag in (3,4,9,10,11,12,17,18): cp[idx]=(tag,struct.unpack(">HH",data[i:i+4])); i+=4
        elif tag in (5,6): cp[idx]=(tag,data[i:i+8]); i+=8; idx+=1
        else: raise ValueError(tag)
        idx+=1
    off=i
    access=struct.unpack(">H",data[off:off+2])[0]; off+=2
    this_i=struct.unpack(">H",data[off:off+2])[0]; off+=2
    super_i=struct.unpack(">H",data[off:off+2])[0]; off+=2
    ic=struct.unpack(">H",data[off:off+2])[0]; off+=2
    ifaces=[struct.unpack(">H",data[off+2*k:off+2*k+2])[0] for k in range(ic)]
    return cp,access,this_i,super_i,ifaces

def name(cp,i):
    e=cp[i]
    if not e or e[0]!=7: return None
    n=cp[e[1]]
    return n[1] if n and n[0]==1 else None

def main():
    jars=[MC]+sorted(LIVE.glob("*.jar"))
    index={}
    for p in jars:
        try: z=zipfile.ZipFile(p)
        except Exception: continue
        for n in z.namelist():
            if not n.endswith(".class"): continue
            try: b=z.read(n); cp,acc,ti,si,ifs=parse(b)
            except Exception: continue
            index[n[:-6]]=(bool(acc&ACC_INTERFACE), p.name)
    print("classes:",len(index))
    bad=[];
    for p in sorted(LIVE.glob("*.jar")):
        z=zipfile.ZipFile(p); cnt=0
        for n in z.namelist():
            if not n.endswith(".class"): continue
            try: b=z.read(n); cp,acc,ti,si,ifs=parse(b)
            except Exception: continue
            sn=name(cp,si); tn=name(cp,ti)
            si_iface = index.get(sn,(False,None))[0] if sn else False
            if sn and sn in index and si_iface:
                bad.append({"jar":p.name,"class":n,"super":sn,"kind":"super-is-interface"}); cnt+=1
            for ii in ifs:
                inm=name(cp,ii)
                if inm and inm in index and not index[inm][0]:
                    bad.append({"jar":p.name,"class":n,"iface":inm,"kind":"implements-class"}); cnt+=1
        if cnt: print("==",p.name,cnt)
    out=ROOT/"work/run26/port/g31/out/super-scan.json"; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(bad,ensure_ascii=False,indent=1),encoding="utf-8")
    print("TOTAL:",len(bad),"->",out)
    for k,v in Counter((b["jar"],b["kind"]) for b in bad).most_common(20): print("  ",k,v)
if __name__=="__main__": main()
