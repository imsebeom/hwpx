import sys, collections
sys.stdout.reconfigure(encoding="utf-8")
def load(f):
    d = {}
    for line in open(f, encoding="utf-8", errors="replace"):
        if not line.startswith("  다름\t"): continue
        p = line.rstrip("\n").split("\t")
        if len(p) < 11: continue
        key = (p[1], p[7], p[8], p[10])
        d[key] = p
    return d
a, b = load(sys.argv[1]), load(sys.argv[2])
fixed = [a[k] for k in a if k not in b]
broken = [b[k] for k in b if k not in a]
print("기준 다름", len(a), "새 다름", len(b), "고침", len(fixed), "망침", len(broken))
def summ(rows, title):
    c = collections.Counter((r[2], r[3], r[4], r[5]) for r in rows)
    print(title)
    for k, v in c.most_common(12): print("   ", v, k)
summ(fixed, "고친 문단(글꼴, 크기px, 자간, 장평)")
summ(broken, "망친 문단")
print("망친 예:")
for r in broken[:14]: print("   ", r[2], r[3], r[4], r[5], "폭", r[7], "한글", r[8], "rhwp", r[9], r[10][:30])
print("고친 예:")
for r in fixed[:8]: print("   ", r[2], r[3], r[4], r[5], "폭", r[7], "한글", r[8], "rhwp", r[9], r[10][:30])
