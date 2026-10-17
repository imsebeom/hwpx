"""한글 정답본 만들기(지휘자). 문서 목록을 사본으로 뜨고 25개씩 숨은 데스크톱에서 oracle_worker.py 를 돌린다.

이미 결과가 있는 문서는 건너뛴다(중간에 죽어도 이어서 돌린다). 원본은 열지 않는다.
산출물(사본, 정답본)은 out/ 아래이며 git 에서 뺀다(실사용 문서 사본).

    python oracle_driver.py [목록.txt]   (기본: ../linebreak/results/reg_corpus_1014.txt)
"""

import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "references"))  # 전역 참조본(최신)
import hidden_desktop  # noqa: E402

CHUNK = 25
OUT = os.path.join(HERE, "out")
SRC, ORA = os.path.join(OUT, "src"), os.path.join(OUT, "oracle")
RES = os.path.join(OUT, "oracle.jsonl")


def main(corpus):
    os.makedirs(SRC, exist_ok=True)
    os.makedirs(ORA, exist_ok=True)
    files = [
        line.strip().split("\t")[0]
        for line in open(corpus, encoding="utf-8")
        if line.strip()
    ]
    index = {}
    for i, f in enumerate(files):
        did = f"d{i:03d}"
        ext = os.path.splitext(f)[1].lower()
        index[did] = f
        dst = os.path.join(SRC, did + ext)
        if os.path.exists(f) and not os.path.exists(dst):
            shutil.copyfile(f, dst)
    json.dump(
        index,
        open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=1,
    )

    done = set()
    if os.path.exists(RES):
        done = {
            json.loads(line)["id"]
            for line in open(RES, encoding="utf-8")
            if line.strip()
        }
    todo = []
    for did, f in index.items():
        src = os.path.join(SRC, did + os.path.splitext(f)[1].lower())
        if did in done:
            continue
        if not os.path.exists(src):
            with open(RES, "a", encoding="utf-8") as r:
                r.write(json.dumps({"id": did, "missing": True}) + "\n")
            continue
        todo.append((did, src))
    print("할 일", len(todo), "끝남", len(done), flush=True)

    for s in range(0, len(todo), CHUNK):
        chunk = todo[s : s + CHUNK]
        lst = os.path.join(OUT, "chunk.tsv")
        with open(lst, "w", encoding="utf-8") as fp:
            fp.write("\n".join(f"{d}\t{p}" for d, p in chunk))
        code, text = hidden_desktop.run(
            [sys.executable, os.path.join(HERE, "oracle_worker.py"), lst, ORA, RES],
            timeout=900,
        )
        got = (
            {
                json.loads(line)["id"]
                for line in open(RES, encoding="utf-8")
                if line.strip()
            }
            if os.path.exists(RES)
            else set()
        )
        lost = [d for d, _ in chunk if d not in got]
        for d in lost:  # 묶음이 죽어 기록이 없는 문서는 실패로 남기고 넘어간다
            with open(RES, "a", encoding="utf-8") as r:
                r.write(json.dumps({"id": d, "worker_died": True, "code": code}) + "\n")
        print(
            f"묶음 {s // CHUNK + 1}: {len(chunk)}개, 종료코드 {code}, 기록 없음 {len(lost)}",
            flush=True,
        )


if __name__ == "__main__":
    main(
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(HERE, "..", "linebreak", "results", "reg_corpus_1014.txt")
    )
