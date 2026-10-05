import sys, collections, re
sys.stdout.reconfigure(encoding="utf-8")
src = open("resid.py", encoding="utf-8").read()
exec(src[src.index("FORB ="):src.index("c = collections.Counter(cat(r)")])
pairs = []; cur = None
for l in open(sys.argv[1], encoding="utf-8", errors="replace"):
    if l.startswith("  분석\t"): cur = l.rstrip("\n").split("\t")[1:]
    elif l.startswith("  다름\t") and cur is not None:
        d = l.rstrip("\n").split("\t"); pairs.append((cur, d)); cur = None
def cat2(r, d):
    c = cat(r)
    if c.startswith("더담음") and len(r) == 12:
        try: want = eval(d[8])
        except Exception: want = []
        if len(want) == 1 and int(r[1]) < 0: return "한글은 한 줄에 다 담음(넘쳐도)"
    return c
if __name__ == "__main__":
    c = collections.Counter(cat2(r, d) for r, d in pairs)
    for k, v in c.most_common(): print(f"  {v:5d}  {k}")
    if len(sys.argv) > 2:
        n = 0
        for r, d in pairs:
            if cat2(r, d) == sys.argv[2]:
                print("  ", "|".join(r[:11]), "|", d[1][-28:], "|", d[2], d[3], d[4], d[5], "|폭", d[7], d[8], d[9], d[10][:36]); n += 1
                if n >= int(sys.argv[3] if len(sys.argv) > 3 else 12): break
