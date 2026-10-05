"""사다리 시험 글 목록을 만든다: python wl_spec.py <out.json> <font> <size_pt> <charPrId>"""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
out, font, size, char = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
EXE = r"C:\Users\hccga\.claude\skills\hwpx\editor\.build\rhwp\target\debug\rhwp.exe"
P = "가 "
texts = ["가" * 10, "가 가 가 가 가 가", "가 가"]
for ch in "01258Aaeimw()[]-,.:·~/%「」『』<>'\"!?+=":
    texts.append(P + ch * 10)
texts += [P + "0 0 0 0 0 0", P + "a a a a a a", "[4국02-04]", "가0가0가0가0가0", "가a가a가a가a가a", "(가)(가)(가)(가)",
          "가,가,가,가,가,가", "가.가.가.가.가.", "「가」「가」「가」", P + "Dual", P + "COP(C", P + "2026.", P + "10.15.(목)"]
spec = []
for t in texts:
    r = subprocess.run([EXE, "measure-width", "--size", size, "--font", font, "--", t], capture_output=True, text=True, encoding="utf-8")
    line = [l for l in r.stdout.splitlines() if "\t" in l and not l.startswith("text")][-1]
    px = float(line.split("\t")[2])
    spec.append({"text": t, "char": char, "est": round(px * 75), "px": px})
json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(spec), spec[0], spec[3])
