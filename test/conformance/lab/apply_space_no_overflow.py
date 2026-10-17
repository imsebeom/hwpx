"""개발용: 줄 끝 빈칸 묶음은 시작 위치가 줄 폭 이하인 빈칸까지만 앞줄에 두고 나머지는 다음 줄 앞에 둔다.

    python apply_space_no_overflow.py [--revert]

근거(정답본 줄 기록): 한/글이 빈칸 묶음 한가운데서 줄을 꺾은 곳이 101곳이다(「신청서를   」 / 「        작성하여」).
빈칸 여러 개로 둘째 줄 들여쓰기를 흉내 낸 문단이 대부분이다. 엔진은 줄 끝 빈칸을 모두 앞줄에 매달고 다음 줄을 글자부터
시작했다.
e19(함초롬바탕 10pt, 줄 폭 425.2pt): 「가」 43자(417.1pt) 뒤 빈칸(5pt)은 2개까지 남는다. 둘째 빈칸은 422.1pt 에서 시작해
줄 폭을 넘겨 끝나도 남고, 셋째는 427.1pt 에서 시작하므로 다음 줄로 간다. 42자 4개, 41자 6개, 40자 8개도 같다(정렬 무관).
시작 위치가 줄 폭과 같으면 남긴다(정답본에서 「같으면 넘김」보다 3곳 더 맞다).
글자만으로 줄 폭을 넘어 빈칸 압축(condense)으로 들어온 줄과 탭이 낀 줄은 종전대로 둔다(d048: 압축 줄도 나누면 431곳이 틀렸다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx space-no-overflow]"
REL = "renderer/composer/line_breaking.rs"

EDITS = [
    (
        REL,
        "fn recalc_width_hwp(tokens: &[BreakToken], current_token_idx: usize, new_line_start: usize) -> i32 {\n",
        f"/// {TAG} 줄을 `break_idx` 에서 꺾을 때, 그 자리의 빈칸 묶음 가운데 줄 폭 안에 드는 빈칸까지만 앞줄에 두고\n"
        "/// 나머지 빈칸부터 다음 줄을 시작할 자리. 한/글은 시작 위치가 줄 폭을 넘는 빈칸을 다음 줄로 보낸다(e19, 정답본 101곳).\n"
        "/// 묶음이 통째로 들어가거나 빈칸이 없거나 줄에 탭이 있으면 None(종전대로 빈칸을 앞줄에 매단다).\n"
        "fn claude_space_run_split(\n"
        "    tokens: &[BreakToken],\n"
        "    text_chars: &[char],\n"
        "    line_start: usize,\n"
        "    break_idx: usize,\n"
        "    effective_width: i32,\n"
        ") -> Option<usize> {\n"
        "    let mut run_start = break_idx.min(text_chars.len());\n"
        "    while run_start > line_start && text_chars[run_start - 1] == ' ' {\n"
        "        run_start -= 1;\n"
        "    }\n"
        "    let mut run_end = break_idx;\n"
        "    while run_end < text_chars.len() && text_chars[run_end] == ' ' {\n"
        "        run_end += 1;\n"
        "    }\n"
        "    if run_start >= run_end || run_start <= line_start {\n"
        "        return None;\n"
        "    }\n"
        "    let mut before = 0i32;\n"
        "    let mut spaces: Vec<(usize, i32)> = Vec::new();\n"
        "    for t in tokens {\n"
        "        match t {\n"
        "            BreakToken::Text { start_idx, end_idx, base_width, .. } => {\n"
        "                if *start_idx >= line_start && *end_idx <= run_start {\n"
        "                    before += to_hwp(*base_width);\n"
        "                } else if *start_idx < run_start && *end_idx > line_start {\n"
        "                    return None; // 묶음 경계에 걸친 토큰(줄 시작 앞에서 시작한 것 등)\n"
        "                }\n"
        "            }\n"
        "            BreakToken::Space { idx, width, .. } => {\n"
        "                if *idx >= line_start && *idx < run_start {\n"
        "                    before += to_hwp(*width);\n"
        "                } else if *idx >= run_start && *idx < run_end {\n"
        "                    spaces.push((*idx, to_hwp(*width)));\n"
        "                }\n"
        "            }\n"
        "            BreakToken::Tab { idx, .. } if *idx >= line_start && *idx < run_end => return None,\n"
        "            _ => {}\n"
        "        }\n"
        "    }\n"
        "    // 글자만으로 줄 폭을 넘어 빈칸 압축(condense)으로 들어온 줄은 끝 빈칸을 모두 앞줄에 둔다(d048)\n"
        "    if spaces.len() != run_end - run_start || before > effective_width {\n"
        "        return None;\n"
        "    }\n"
        "    // 빈칸은 시작 위치가 줄 폭 이하이면 앞줄에 남는다(자기 폭만큼은 넘친다). e19: 남은 폭 8.1pt 에 5pt 빈칸 2개\n"
        "    let mut w = before;\n"
        "    for (idx, sw) in spaces {\n"
        "        if w > effective_width {\n"
        "            return Some(idx);\n"
        "        }\n"
        "        w += sw;\n"
        "    }\n"
        "    None\n"
        "}\n"
        "\n"
        "fn recalc_width_hwp(tokens: &[BreakToken], current_token_idx: usize, new_line_start: usize) -> i32 {\n",
    ),
    (
        REL,
        "                        if let Some(break_token_idx) = cursor.last_break_token_idx {\n"
        "                            let result = LineBreakResult {\n"
        "                                start_idx: cursor.line_start_idx,\n"
        "                                end_idx: cursor.last_break_char_idx,\n"
        "                                max_font_size: cursor.fs_at_last_break,\n"
        "                                has_line_break: false,\n"
        "                            };\n"
        "                            let mut next_start = cursor.last_break_char_idx;\n"
        "                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {\n"
        "                                next_start += 1;\n"
        "                            }\n",
        "                        if let Some(break_token_idx) = cursor.last_break_token_idx {\n"
        "                            let mut result = LineBreakResult {\n"
        "                                start_idx: cursor.line_start_idx,\n"
        "                                end_idx: cursor.last_break_char_idx,\n"
        "                                max_font_size: cursor.fs_at_last_break,\n"
        "                                has_line_break: false,\n"
        "                            };\n"
        "                            let mut next_start = cursor.last_break_char_idx;\n"
        "                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {\n"
        "                                next_start += 1;\n"
        "                            }\n"
        "                            // [claude-hwpx space-no-overflow] 줄 폭을 넘는 빈칸부터 다음 줄로\n"
        "                            if let Some(split) = claude_space_run_split(\n"
        "                                tokens,\n"
        "                                text_chars,\n"
        "                                cursor.line_start_idx,\n"
        "                                cursor.last_break_char_idx,\n"
        "                                eff_w(cursor.is_first_line),\n"
        "                            ) {\n"
        "                                result.end_idx = split;\n"
        "                                next_start = split;\n"
        "                            }\n",
    ),
    (
        REL,
        "                        if let Some(break_token_idx) = last_break_token_idx {\n"
        "                            results.push(LineBreakResult {\n"
        "                                start_idx: line_start_idx,\n"
        "                                end_idx: last_break_char_idx,\n"
        "                                max_font_size: fs_at_last_break,\n"
        "                                has_line_break: false,\n"
        "                            });\n"
        "                            let mut next_start = last_break_char_idx;\n"
        "                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {\n"
        "                                next_start += 1;\n"
        "                            }\n",
        "                        if let Some(break_token_idx) = last_break_token_idx {\n"
        "                            // [claude-hwpx space-no-overflow] 운영 경로와 같게(동등성 시험용 사본)\n"
        "                            let split = claude_space_run_split(\n"
        "                                tokens,\n"
        "                                text_chars,\n"
        "                                line_start_idx,\n"
        "                                last_break_char_idx,\n"
        "                                eff_w(is_first_line),\n"
        "                            );\n"
        "                            results.push(LineBreakResult {\n"
        "                                start_idx: line_start_idx,\n"
        "                                end_idx: split.unwrap_or(last_break_char_idx),\n"
        "                                max_font_size: fs_at_last_break,\n"
        "                                has_line_break: false,\n"
        "                            });\n"
        "                            let mut next_start = last_break_char_idx;\n"
        "                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {\n"
        "                                next_start += 1;\n"
        "                            }\n"
        "                            if let Some(split) = split {\n"
        "                                next_start = split;\n"
        "                            }\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
