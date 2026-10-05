import re, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8")
for f in sys.argv[1:]:
    z = zipfile.ZipFile(f)
    for n in z.namelist():
        if not re.match(r"Contents/section\d+\.xml", n):
            continue
        s = z.read(n).decode()
        bodies = []
        for m in re.finditer(r'<hp:fieldBegin[^>]*type="MEMO".*?</hp:fieldBegin>', s, re.S):
            sub = re.search(r"<hp:subList.*?</hp:subList>", m.group(0), re.S)
            bodies.append("".join(re.findall(r"<hp:t>([^<]*)</hp:t>", sub.group(0))) if sub else None)
        print(f.replace("\\", "/").rsplit("/", 1)[-1], n, "memogroup", s.count("<hp:memogroup"), "MEMO", len(bodies), "fieldEnd", s.count("<hp:fieldEnd"))
        for b in bodies[:3]:
            print("   본문:", (b or "")[:50])
