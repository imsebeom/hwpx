"""등록한 글꼴(rt_metrics.json)의 문단 불일치 수를 등록 전후 로그에서 센다."""

import collections
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
names = {m["name"] for m in json.load(open("rt_metrics.json", encoding="utf-8"))}


def count(path):
    c = collections.Counter()
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("  다름\t"):
            p = line.rstrip("\n").split("\t")
            if len(p) > 2:
                c[p[2]] += 1
    return c


a, b = count(sys.argv[1]), count(sys.argv[2])
rows = [(n, a[n], b[n]) for n in sorted(names) if a[n] or b[n]]
print(
    "등록한 글꼴",
    len(names),
    "| 그 글꼴 문단의 불일치: 전",
    sum(r[1] for r in rows),
    "후",
    sum(r[2] for r in rows),
)
for n, x, y in rows:
    print(f"   {n:<24} 전 {x:>3} 후 {y:>3}")
