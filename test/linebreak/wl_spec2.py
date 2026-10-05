import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
EXE = r"C:\Users\hccga\.claude\skills\hwpx\editor\.build\rhwp\target\debug\rhwp.exe"
FONTS = {4: "함초롬바탕", 0: "굴림", 1: "돋움", 2: "바탕"}
P = "가 "
SET = ["가" * 10, "가 가 가 가 가 가", P + "0" * 10, P + "a" * 10, P + "(" * 10, P + "「" * 10, P + "e" * 10, "가0가0가0가0가0"]
variants = [
    dict(id=50, height=1000, font=4), dict(id=51, height=1000, font=4, bold=False), dict(id=52, height=900, font=4, bold=False),
    dict(id=53, height=1100, font=4, bold=False), dict(id=54, height=1200, font=4, bold=False),
    dict(id=55, height=1000, font=4, bold=False, spacing=-5), dict(id=56, height=1000, font=4, bold=False, spacing=-10),
    dict(id=57, height=1000, font=4, bold=False, ratio=95), dict(id=58, height=1000, font=4, bold=False, ratio=90),
    dict(id=59, height=1000, font=4, bold=False, spacing=5), dict(id=60, height=1300, font=4, bold=False),
    dict(id=61, height=1000, font=0, bold=False), dict(id=62, height=1000, font=1, bold=False), dict(id=63, height=1000, font=2, bold=False),
    dict(id=64, height=800, font=0, bold=False),
]
def est(text, v):
    args = [EXE, "measure-width", "--size", str(v["height"] / 100), "--font", FONTS[v["font"]], "--ratio", str(v.get("ratio", 100)), "--", text]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    line = [l for l in r.stdout.splitlines() if "\t" in l and not l.startswith("text")][-1]
    return float(line.split("\t")[2])
spec = [dict(text=P + "-" * 10, char=45, est=1323 + 4950, span=40), dict(text=P + "!" * 10, char=45, est=4203 + 1000, span=1100)]
for v in variants:
    for t in SET:
        px = est(t, v)
        e = round(px * 75) + round(len(t) * v["height"] * v.get("spacing", 0) / 100)
        spec.append(dict(text=t, char=v["id"], est=e, span=80 if v.get("spacing") else 32, v={k: v[k] for k in v if k != "id"}))
json.dump(spec, open("wl2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(variants, open("wl2.charpr.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(spec))
