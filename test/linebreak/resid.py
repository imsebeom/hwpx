import sys, collections
sys.stdout.reconfigure(encoding="utf-8")
log = sys.argv[1]
tot = collections.Counter(); rows = []
for l in open(log, encoding="utf-8", errors="replace"):
    if l.startswith("  전체\t"):
        p = l.rstrip("\n").split("\t"); tot[p[1]] += 1
    elif l.startswith("  분석\t"):
        rows.append(l.rstrip("\n").split("\t")[1:])
FORB = set(")]},.!?;:'\"、。…·―ー》」』】）｝〕〉＞≫］﹞〞’”，．！？；：%")
def cat(r):
    if len(r) != 12: return "탭이나 줄바꿈이 낀 줄"
    kind, amount, line, indent, head, kbu, hend, rend, nextw, shapes, ctl, font = r
    amount = int(amount); nextw = int(nextw.replace("다음폭", ""))
    h_prev, h_next = hend[len("한글끝["):-1].split("|") if "|" in hend else ("?", "?")
    r_prev, r_next = rend[len("rhwp끝["):-1].split("|") if "|" in rend else ("?", "?")
    if ctl != "ctl0": return "개체 있는 문단"
    if head not in ("None",): return f"머리({head})"
    if indent != "indent0": return "들여쓰기/내어쓰기 " + ("첫 줄" if line == "줄1" else "둘째 줄 뒤")
    if kind == "덜담음":
        if r_next in FORB: return "덜담음: rhwp 줄 머리가 금칙 문자"
        if amount < nextw: return "덜담음: 다음 글자가 안 들어감(폭 차이)"
        return "덜담음: 자리가 남는데 꺾음"
    else:
        if amount >= 0: return "더담음: rhwp 가 들어가는데 꺾음"
        if amount >= -8: return "더담음: 1~8 넘침"
        if amount >= -60: return "더담음: 9~60 넘침"
        return "더담음: 60 넘게 넘침"
c = collections.Counter(cat(r) for r in rows)
print("남은 차이", len(rows))
for k, v in c.most_common(): print(f"  {v:5d}  {k}")
f = collections.Counter(r[-1] for r in rows)
print("글꼴별 (다름/전체)")
for k, v in sorted(f.items(), key=lambda kv: -kv[1])[:14]: print(f"  {v:5d}/{tot[k]:<6d} {100*v/max(tot[k],1):5.1f}%  {k}")
if len(sys.argv) > 2:
    want = sys.argv[2]
    n = 0
    for r in rows:
        if cat(r) == want:
            print("   ", "\t".join(r)); n += 1
            if n >= int(sys.argv[3]) if len(sys.argv) > 3 else n >= 12: break
