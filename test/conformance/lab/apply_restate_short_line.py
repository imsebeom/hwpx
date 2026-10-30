"""개발용: 열 때 다시 재기(tac-restate-on-open)가 「품은 줄이 표 높이 + 바깥 여백보다 짧은」 글자처럼 취급 표도 다시 잰다.

    python apply_restate_short_line.py [--revert]

근거(회귀 모음 「문항카드_발화점」 c70, 10번 문단): 표 높이 60135 를 품은 줄이 50775 다. 줄이 그 안의 글자처럼 취급 표보다 짧을 수는
없으니 낡은 줄이고, 한/글은 열 때 다시 잰다(끝 상자가 6쪽으로 넘어감, 한/글 6쪽). 엔진은 쪽 나누기에 이 줄을 써 표를 125px 작게
보고 상자까지 5쪽에 담았다. 다시 재기는 줄 = 선언 + 여백일 때만 들어가서 이 표를 건너뛰었다. 짧은 줄이면 표 높이가 그대로여도
줄을 고친다(뒤 문단 밀기는 restate-keep-reset). 줄이 표의 절반도 안 되는 더미 줄 배치(생성기 900, 서식2 c52 와 c69 에서 나빠짐)는
대상이 아니다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx restate-short-line]"

EDITS = [
    (
        "document_core/commands/document.rs",
        (
            "                    if t.caption.is_some()\n"
            "                        || (p.line_segs[0].line_height - (t.common.height as i32 + outer)).abs() > 75\n"
            "                    {\n"
        ),
        (
            f"                    // {TAG} 줄이 표 + 여백보다 짧으면 낡은 줄이다(한/글은 줄을 표보다 짧게 쓰지 않는다) — 다시 잰다(c70 10번: 줄 50775, 표 60135)\n"
            "                    // 표의 절반도 안 되는 줄(생성기 더미 줄 배치 900)은 대상이 아니다(서식2 c52, c69 에서 나빠짐)\n"
            "                    let claude_short_line = p.line_segs[0].line_height < t.common.height as i32 + outer - 75\n"
            "                        && p.line_segs[0].line_height * 2 >= t.common.height as i32 + outer;\n"
            "                    if t.caption.is_some()\n"
            "                        || (!claude_short_line\n"
            "                            && (p.line_segs[0].line_height - (t.common.height as i32 + outer)).abs() > 75)\n"
            "                    {\n"
        ),
    ),
    (
        "document_core/commands/document.rs",
        (
            "                let p = &mut doc.document.sections[si].paragraphs[pi];\n"
            "                let Some(Control::Table(t)) = p.controls.get_mut(ci) else {\n"
            "                    continue;\n"
            "                };\n"
            "                let old_h = t.common.height as i32;\n"
            "                if new_h <= 0 || (new_h - old_h).abs() < 75 {\n"
        ),
        (
            "                let p = &mut doc.document.sections[si].paragraphs[pi];\n"
            f"                // {TAG} 짧은 줄은 표 높이가 그대로여도 고친다\n"
            "                let claude_short_line = match p.controls.get(ci) {\n"
            "                    Some(Control::Table(t)) => {\n"
            "                        let full = t.common.height as i32 + t.outer_margin_top as i32 + t.outer_margin_bottom as i32;\n"
            "                        p.line_segs[0].line_height < full - 75 && p.line_segs[0].line_height * 2 >= full\n"
            "                    }\n"
            "                    _ => false,\n"
            "                };\n"
            "                let Some(Control::Table(t)) = p.controls.get_mut(ci) else {\n"
            "                    continue;\n"
            "                };\n"
            "                let old_h = t.common.height as i32;\n"
            "                if new_h <= 0 || ((new_h - old_h).abs() < 75 && !claude_short_line) {\n"
        ),
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        if (find not in s) if revert else (repl in s):
            print("이미", rel)
            continue
        n = s.count(find)
        if n != 1:
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
