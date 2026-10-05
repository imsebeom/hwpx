"""대조 문서를 사본으로 떠서 한글로 다시 저장한다(묶음마다 숨은 데스크톱, 실패한 묶음은 건너뜀)."""
import os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8")
import hidden_desktop
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "hres")
os.makedirs(out, exist_ok=True)
files = [l.strip() for l in open(os.path.join(here, "reg_corpus.txt"), encoding="utf-8") if l.strip()]
pairs = []
for i, f in enumerate(files):
    dst = os.path.join(out, f"d{i}.hwpx")
    if not os.path.exists(dst):
        shutil.copyfile(f, dst)
    pairs.append((dst, f))
todo = [d for d, _ in pairs if not os.path.exists(d[:-5] + "_hwp.hwpx")]
print("todo", len(todo), flush=True)
N = 20
for s in range(0, len(todo), N):
    chunk = todo[s:s + N]
    code, text = hidden_desktop.run([sys.executable, os.path.join(here, "hwp_resave_many.py"), *chunk], timeout=420)
    done = sum(os.path.exists(d[:-5] + "_hwp.hwpx") for d in chunk)
    print(f"chunk {s // N}: code {code} saved {done}/{len(chunk)}", flush=True)
with open(os.path.join(here, "hres_list.txt"), "w", encoding="utf-8") as fh:
    for d, f in pairs:
        h = d[:-5] + "_hwp.hwpx"
        if os.path.exists(h):
            fh.write(h + "\n")
print("list written")
