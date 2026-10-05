import json, sys
sys.stdout.reconfigure(encoding="utf-8")
old = json.load(open("map_old.json", encoding="utf-8")); new = json.load(open(sys.argv[1], encoding="utf-8")); han = json.load(open("hpages.json", encoding="utf-8"))
rows = []
for k in old:
    if k in new and k in han and "pages" in old[k] and "pages" in new[k] and isinstance(han[k], int):
        rows.append((k, old[k]["pages"], new[k]["pages"], han[k]))
print("문서", len(rows))
print("한글과 쪽수 같음: 전", sum(o == h for _, o, n, h in rows), "후", sum(n == h for _, o, n, h in rows))
better = [r for r in rows if abs(r[2] - r[3]) < abs(r[1] - r[3])]
worse = [r for r in rows if abs(r[2] - r[3]) > abs(r[1] - r[3])]
print("한글에 가까워짐", len(better), "멀어짐", len(worse))
for k, o, n, h in worse: print("  멀어짐: 전", o, "후", n, "한글", h, k[-60:])
for k, o, n, h in better[:40]: print("  가까워짐: 전", o, "후", n, "한글", h, k[-60:])
still = [r for r in rows if r[2] != r[3]]
print("아직 다른 문서", len(still))
for k, o, n, h in still[:40]: print("  전", o, "후", n, "한글", h, k[-64:])
