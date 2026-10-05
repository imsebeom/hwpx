"""에디터(cli)로 칸 T38r7c1 에서 「국고보조금」 문단을 찾아, 다시 나누기 전후의 줄 시작을 본다."""

import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
CLI = ["node", "cli.mjs"]


def run(ops):
    p = subprocess.run(
        CLI + ["run", "-"],
        input=json.dumps(ops),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(p.stdout)


ppi, ci, cell = 172, 0, 21
n = run([{"doc": "getCellParagraphCount", "a": [0, ppi, ci, cell]}])[0]
texts = run(
    [{"doc": "getTextInCell", "a": [0, ppi, ci, cell, cp, 0, 200]} for cp in range(n)]
)
cp = next(i for i, t in enumerate(texts) if "국고보조금" in str(t))
text = str(texts[cp])
print("칸 문단", n, "개, 대상 문단", cp, "| 글:", text[:60])


def lines():
    seen = []
    for off in range(0, len(text), 1):
        r = run([{"doc": "getLineInfoInCell", "a": [0, ppi, ci, cell, cp, off]}])[0]
        if not seen or seen[-1] != r["charStart"]:
            seen.append(r["charStart"])
        if len(seen) >= 3:
            break
    return seen


print("저장된 줄 기록의 줄 시작:", lines())
run(
    [
        {"doc": "insertTextInCell", "a": [0, ppi, ci, cell, cp, 0, "x"]},
        {"doc": "deleteTextInCell", "a": [0, ppi, ci, cell, cp, 0, 1]},
    ]
)
print("다시 나눈 뒤 줄 시작:", lines(), "(한/글 [0, 49], 폭 표 없던 엔진 [0, 50])")
