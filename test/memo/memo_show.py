import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(sys.argv[1], encoding="utf-8"))
print(len(d), "개, closed", sum(x["closed"] for x in d), "여러 문단", sum(x["startPara"] != x["endPara"] for x in d))
for x in d[: int(sys.argv[2]) if len(sys.argv) > 2 else 14]:
    path = [(h["controlIndex"], h["cellIndex"], h["cellParaIndex"]) for h in x["path"]]
    print(" #%s %s %s | p%s path%s %s:%s~%s:%s %s | 걸린 글=%r | 본문=%r" % (
        x["number"], x["author"], x["createdAt"], x["paraIndex"], path, x["startPara"], x["startOffset"],
        x["endPara"], x["endOffset"], "" if x["closed"] else "(안 닫힘)", x["anchor"][:30], x["text"][:40]))
