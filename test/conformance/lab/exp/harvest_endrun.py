import sys, glob, os, re, zipfile, collections
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
stats=collections.Counter(); ex=[]
for f in sorted(glob.glob(os.path.join(sys.argv[1],'*.hwpx'))):
    z=zipfile.ZipFile(f)
    h=z.read('Contents/header.xml').decode('utf-8')
    hts={m.group(1):int(m.group(2)) for m in re.finditer(r'<hh:charPr id="(\d+)" height="(\d+)"',h)}
    for n in z.namelist():
        if not re.match(r'Contents/section\d+\.xml',n): continue
        root=etree.fromstring(z.read(n))
        for p in root.iter(HP+'p'):
            segs=[l for l in p.iter(HP+'lineseg') if l.getparent().getparent() is p]
            if len(segs)!=1: continue
            runs=p.findall(HP+'run')
            if len(runs)<2: continue
            def rtext(r): return ''.join(t.text or '' for t in r.findall(HP+'t'))
            def robj(r): return any(c.tag in (HP+'tbl',HP+'pic',HP+'rect',HP+'container',HP+'equation',HP+'ellipse',HP+'line') for c in r)
            if any(robj(r) for r in runs): continue
            text_h=[hts.get(r.get('charPrIDRef'),0) for r in runs if rtext(r).strip()]
            if not text_h: continue
            last=runs[-1]
            if rtext(last): continue
            he=hts.get(last.get('charPrIDRef'),0); ht=max(text_h)
            if he<=ht: continue
            vs=int(segs[0].get('vertsize')); th=int(segs[0].get('textheight'))
            k='end' if vs==he else ('text' if vs==ht else 'other')
            stats[k]+=1
            if len(ex)<25: ex.append((os.path.basename(f),ht,he,vs))
print(stats); print(ex)
