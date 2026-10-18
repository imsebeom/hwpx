"""빈칸 줄이기 당김 조건 실험용으로 엔진 소스를 잠시 바꾼다. 사용: exp_condense.py <A|B|off>"""

import sys
from pathlib import Path

f = Path(
    r"C:/Users/hccga/.claude/skills/hwpx/editor/.build/rhwp/src/renderer/composer/line_breaking.rs"
)
raw = f.read_bytes().decode("utf-8")
nl = "\r\n" if "\r\n" in raw else "\n"
s = raw.replace("\r\n", "\n")
ORIG = """    let condense_pull_allowed = !needs_condense_to_fit
        || CLAUDE_TOKEN_CONTINUES_WORD.with(|flag| flag.get())
        || current_width_hwp - CLAUDE_TOKEN_LEADING_SPACE_HWP.with(|width| width.get())
            <= effective_width_hwp;
"""
VARIANTS = {
    # A: 늘 당긴다
    "A": """    let condense_pull_allowed = true; // EXP-CONDENSE
""",
    # B: 새 낱말도 줄인 폭 기준(앞 띄어쓰기를 뺀 줄 내용이 줄인 폭 안)이면 당긴다
    "B": """    let condense_pull_allowed = !needs_condense_to_fit // EXP-CONDENSE
        || CLAUDE_TOKEN_CONTINUES_WORD.with(|flag| flag.get())
        || condensed_line_width_hwp(current_width_hwp, space_savings_hwp)
            - CLAUDE_TOKEN_LEADING_SPACE_HWP.with(|width| width.get())
            <= effective_width_hwp;
""",
}
mode = sys.argv[1]
cur = next((k for k, v in VARIANTS.items() if v in s), None)
if cur:
    s = s.replace(VARIANTS[cur], ORIG)
if mode != "off":
    assert s.count(ORIG) == 1
    s = s.replace(ORIG, VARIANTS[mode])
f.write_bytes(s.replace("\n", nl).encode("utf-8"))
print("모드", mode, "(이전", cur, ")")
