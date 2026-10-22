"""개발용: 문단 끝에 남은 빈칸도 시작 위치가 줄 폭을 넘으면 다음 줄로 보낸다(빈칸만으로 여러 줄이 될 수 있다).

    python apply_trailing_space_wrap.py [--revert]

근거(새 정답본): d317 본문 645 「전국대회 출품 현황 및 목록」 + 빈칸 100여 개를 한/글은 세 줄(글 + 빈칸, 빈칸 51, 빈칸 27)로,
661 은 두 줄(마지막 줄 빈칸 하나)로 나눈다. 칸 426, 479 「(서명)」 뒤 빈칸도 같다. 엔진은 문단 끝 빈칸을 모두 앞줄에 매달았다.
space-no-overflow(e19, 정답본 101곳)의 「빈칸은 시작 위치가 줄 폭 이하일 때만 앞줄」 규칙이 글자 토큰이 넘칠 때만 돌아, 뒤에 글이
없는 빈칸 묶음에는 걸리지 않았다. 빈칸 앞 글자만으로 줄 폭을 넘는 줄(빈칸 줄이기로 들어온 줄)은 종전대로 둔다.
묶음의 처음 두 빈칸은 늘 앞줄에 남는다(사본 실험 ts, t2, 함초롬바탕 10pt, 왼쪽, 가운데, 양쪽 정렬 모두: 「가」43 + 「ii」 + 빈칸 k 는
k=2 까지 한 줄, k=3 이면 셋째부터 다음 줄 — 둘째 빈칸은 줄 폭 밖에서 시작해도 남는다. 「가」42 + 빈칸 5 는 시작이 줄 폭 안인 넷까지
앞줄). 정답본 칸 「 구조화  」(d141 등 끝 빈칸 둘) 열세 곳도 한 줄이다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx trailing-space-wrap]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "            BreakToken::Space {\n"
        "                idx,\n"
        "                width,\n"
        "                max_font_size,\n"
        "            } => {\n"
        "                if *max_font_size > cursor.line_max_fs {\n"
        "                    cursor.line_max_fs = *max_font_size;\n"
        "                }\n"
        "                cursor.last_break_token_idx = Some(ti);\n",
        "            BreakToken::Space {\n"
        "                idx,\n"
        "                width,\n"
        "                max_font_size,\n"
        "            } => {\n"
        f"                // {TAG} 문단 끝 빈칸 묶음에서 시작 위치가 줄 폭을 넘는 빈칸부터 다음 줄로(d317 645, 661)\n"
        "                if *idx > cursor.line_start_idx\n"
        "                    && cursor.lw > eff_w(cursor.is_first_line)\n"
        "                    // 글자처럼 놓인 개체의 폭이 얹힌 빈칸(글자 크기보다 넓음)은 빈칸으로 보지 않는다(d142 그림 묶음 문단)\n"
        "                    && tokens[ti..].iter().all(|t| matches!(t, BreakToken::Space { width: w, max_font_size: f, .. } if *w <= *f))\n"
        "                {\n"
        "                    let mut run_w = 0i32;\n"
        "                    let mut k = ti;\n"
        "                    while k > 0 {\n"
        "                        match &tokens[k - 1] {\n"
        "                            BreakToken::Space { idx: si, width: sw, max_font_size: sf } if *si >= cursor.line_start_idx && *sw <= *sf => {\n"
        "                                run_w += to_hwp(*sw);\n"
        "                                k -= 1;\n"
        "                            }\n"
        "                            _ => break,\n"
        "                        }\n"
        "                    }\n"
        "                    // 묶음의 처음 두 빈칸은 시작 위치와 상관없이 앞줄에 매단다(사본 실험 t2: 「가」43 + ii + 빈칸 2 는 한 줄)\n"
        "                    if ti - k >= 2 && cursor.lw - run_w <= eff_w(cursor.is_first_line) {\n"
        "                        let result = LineBreakResult {\n"
        "                            start_idx: cursor.line_start_idx,\n"
        "                            end_idx: *idx,\n"
        "                            max_font_size: cursor.line_max_fs,\n"
        "                            has_line_break: false,\n"
        "                        };\n"
        "                        cursor.line_start_idx = *idx;\n"
        "                        cursor.lw = 0;\n"
        "                        cursor.line_space_savings = 0;\n"
        "                        cursor.line_max_fs = *max_font_size;\n"
        "                        cursor.is_first_line = false;\n"
        "                        cursor.last_break_token_idx = None;\n"
        "                        cursor.emitted_any = true;\n"
        "                        return Some(FilledInterval {\n"
        "                            line: result,\n"
        "                            termination: FillTermination::IntervalFull,\n"
        "                        });\n"
        "                    }\n"
        "                }\n"
        "                if *max_font_size > cursor.line_max_fs {\n"
        "                    cursor.line_max_fs = *max_font_size;\n"
        "                }\n"
        "                cursor.last_break_token_idx = Some(ti);\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
