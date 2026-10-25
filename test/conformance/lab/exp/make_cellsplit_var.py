import sys, zipfile, re, os
src, outdir = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(src)
items = [(i.filename, z.read(i.filename)) for i in z.infolist()]
sec = dict(items)['Contents/section0.xml'].decode('utf-8')
def setpb(s, tid, val):
    pat = re.compile(r'(<hp:tbl id="%s"[^>]*?pageBreak=")[A-Z]+(")' % tid)
    s2, n = pat.subn(r'\g<1>%s\g<2>' % val, s); assert n == 1; return s2
for o in ['CELL', 'TABLE']:
    for i in ['CELL', 'TABLE', 'NONE']:
        s = setpb(setpb(sec, '1188435459', o), '1188435460', i)
        out = os.path.join(outdir, f'o{o}_i{i}.hwpx')
        with zipfile.ZipFile(out, 'w') as w:
            for name, raw in items:
                data = s.encode('utf-8') if name == 'Contents/section0.xml' else raw
                w.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
        print(out)
