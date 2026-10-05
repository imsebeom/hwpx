import json, subprocess, sys, math
sys.stdout.reconfigure(encoding="utf-8")
EXE = r"C:\Users\hccga\.claude\skills\hwpx\editor\.build\rhwp\target\debug\rhwp.exe"
P = "가 "
# 자간 사다리
G = {1000: {"가": 243, " ": 125, "0": 138, "(": 80}, 900: {"가": 218, " ": 112, "0": 124, "(": 72}}
sv = [(1000, -5), (1000, -10), (1000, 5), (1000, -3), (1000, -7), (900, -5), (900, -10)]
S_SET = ["가" * 10, "가" * 5, "가 가 가 가 가 가", P + "0" * 10, P + "(" * 10, "가0가0가0가0가0"]
spec, variants = [], []
for i, (h, p) in enumerate(sv):
    cid = 50 + i
    variants.append(dict(id=cid, height=h, font=4, bold=False, spacing=p))
    s = math.trunc(h / 4 * p / 100)
    for t in S_SET:
        units = sum(G[h][c] for c in t) + (len(t) - 1) * s
        spec.append(dict(text=t, char=cid, est=units * 4, span=120, v=dict(height=h, spacing=p)))
json.dump(spec, open("wl3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(variants, open("wl3.charpr.json", "w", encoding="utf-8"), ensure_ascii=False)
# 장평 사다리
rv = [(1000, 97), (1000, 80), (1000, 50), (1000, 110), (1000, 120), (900, 95), (900, 90), (1200, 95), (1000, 99), (1000, 93)]
R_SET = ["가" * 10, "가 가 가 가 가 가", P + "0" * 10, P + "a" * 10, P + "(" * 10, P + "「" * 10, P + "e" * 10]
spec, variants = [], []
def est(text, h, r):
    out = subprocess.run([EXE, "measure-width", "--size", str(h / 100), "--font", "함초롬바탕", "--ratio", str(r), "--", text], capture_output=True, text=True, encoding="utf-8").stdout
    return float([l for l in out.splitlines() if "\t" in l and not l.startswith("text")][-1].split("\t")[2])
for i, (h, r) in enumerate(rv):
    cid = 50 + i
    variants.append(dict(id=cid, height=h, font=4, bold=False, ratio=r))
    for t in R_SET:
        spec.append(dict(text=t, char=cid, est=round(est(t, h, r) * 75), span=48, v=dict(height=h, ratio=r)))
json.dump(spec, open("wl4.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(variants, open("wl4.charpr.json", "w", encoding="utf-8"), ensure_ascii=False)
print("ok")
