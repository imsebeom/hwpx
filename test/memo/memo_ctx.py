import re, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8")
nth = int(sys.argv[1])
for f in sys.argv[2:]:
    s = zipfile.ZipFile(f).read("Contents/section0.xml").decode()
    ms = [m.start() for m in re.finditer('type="MEMO"', s)]
    i = ms[nth]
    a = s.rfind("<hp:fieldBegin", 0, i)
    b = s.find("</hp:fieldBegin>", a) + 16
    pa = s.rfind("<hp:p ", 0, a)
    print("==", f.replace("\\", "/").rsplit("/", 1)[-1], len(s))
    strip = lambda x: re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "<LS/>", x, flags=re.S)
    print("  PRE :", strip(s[pa:a])[-300:])
    print("  BEG :", re.sub(r"<hp:subList.*?</hp:subList>", "<SUB/>", s[a:b], flags=re.S)[:700])
    print("  POST:", strip(s[b : b + 600])[:520])
