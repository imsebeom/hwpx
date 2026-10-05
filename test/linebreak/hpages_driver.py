"""대조 문서 317개의 한글 쪽수를 묶음으로 센다(숨은 데스크톱). 결과 hpages.json {원본 경로: 쪽수}."""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
import hidden_desktop
here = os.path.dirname(os.path.abspath(__file__))
files = [l.strip() for l in open(os.path.join(here, "reg_corpus.txt"), encoding="utf-8") if l.strip()]
out = os.path.join(here, "hpages.json")
res = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
todo = [f for f in files if f not in res]
N = 25
for s in range(0, len(todo), N):
    chunk = todo[s:s + N]
    lst = os.path.join(here, "hp_chunk.txt"); part = os.path.join(here, "hp_chunk.json")
    open(lst, "w", encoding="utf-8").write("\n".join(chunk))
    if os.path.exists(part): os.remove(part)
    code, text = hidden_desktop.run([sys.executable, os.path.join(here, "hwp_pages.py"), lst, part], timeout=420)
    if os.path.exists(part):
        res.update(json.load(open(part, encoding="utf-8")))
        json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"chunk {s // N}: code {code} total {len(res)}", flush=True)
print("done", len(res))
