"""개발용: 각주, 미주 글에 글자 모양(굵게, 기울임, 크기 등)을 적용하고 읽는다.

    python apply_fn_char_format.py [--revert]

근거(2026-10-19 각주 편집 점검): 스튜디오는 각주 편집 중 글자 서식을 「전용 범위 API 가 없다」며 막아 두었다(Ctrl+B 무반응).
머리말/꼬리말 판(apply_char_format_in_header_footer_native)과 같은 방식으로 각주 문단 범위에 글자 모양을 입힌다.
머리말 판과 달리 고른 범위 안 run 마다 따로 바꿔(굵은 글과 기울인 글이 섞여 있어도 각자 바꾼 속성만 더한다) 섞인 서식을 지운다.
칸 안 각주는 fn-cell-target 가짜 컨트롤 번호로 받는다. wasm: applyCharFormatInFootnote, getCharPropertiesInFootnote.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx fn-char-format]"

CORE_FIND = """    /// 각주 문단 리플로우
    pub(crate) fn reflow_footnote_paragraph(
"""
CORE_REPL = f"""    /// {TAG} 각주, 미주 문단의 글자 위치 글자 모양을 JSON 으로 돌려준다(머리말 판과 같은 형식).
    pub fn claude_get_char_properties_in_footnote_native(
        &self,
        section_idx: usize,
        para_idx: usize,
        control_idx: usize,
        fn_para_idx: usize,
        char_offset: usize,
    ) -> Result<String, HwpError> {{
        let paragraph = self
            .get_footnote_paragraph_ref(section_idx, para_idx, control_idx, fn_para_idx)
            .ok_or_else(|| HwpError::RenderError("각주 문단을 찾을 수 없음".to_string()))?;
        let offset = char_offset.min(paragraph.text.chars().count());
        Ok(self.build_char_properties_json(paragraph, offset))
    }}

    /// {TAG} 각주, 미주 문단 범위에 글자 모양을 적용한다. 범위 안 run 마다 그 모양에 바꾼 속성만 더한다.
    #[allow(clippy::too_many_arguments)]
    pub fn claude_apply_char_format_in_footnote_native(
        &mut self,
        section_idx: usize,
        para_idx: usize,
        control_idx: usize,
        start_fn_para: usize,
        start_offset: usize,
        end_fn_para: usize,
        end_offset: usize,
        props_json: &str,
    ) -> Result<String, HwpError> {{
        if (start_fn_para, start_offset) > (end_fn_para, end_offset) {{
            return Err(HwpError::RenderError("시작 위치가 끝 위치보다 뒤에 있음".to_string()));
        }}
        let mut mods = crate::document_core::helpers::parse_char_shape_mods(props_json);
        if json_has_border_keys(props_json) {{
            mods.border_fill_id = Some(self.create_border_fill_from_json(props_json));
        }}
        let mut changed = Vec::new();
        for fp in start_fn_para..=end_fn_para {{
            // 범위 안 글자마다 지금 모양을 읽어 같은 모양끼리 묶는다
            let runs: Vec<(usize, usize, u32)> = {{
                let p = self
                    .get_footnote_paragraph_ref(section_idx, para_idx, control_idx, fp)
                    .ok_or_else(|| HwpError::RenderError("각주 문단을 찾을 수 없음".to_string()))?;
                let len = p.text.chars().count();
                let a = if fp == start_fn_para {{ start_offset.min(len) }} else {{ 0 }};
                let b = if fp == end_fn_para {{ end_offset.min(len) }} else {{ len }};
                let mut runs: Vec<(usize, usize, u32)> = Vec::new();
                for i in a..b {{
                    let id = p.char_shape_id_at(i).unwrap_or(0);
                    match runs.last_mut() {{
                        Some(last) if last.2 == id && last.1 == i => last.1 = i + 1,
                        _ => runs.push((i, i + 1, id)),
                    }}
                }}
                runs
            }};
            if runs.is_empty() {{
                continue;
            }}
            for (x, y, base) in runs {{
                let new_id = self.document.find_or_create_char_shape(base, &mods);
                self.get_footnote_paragraph_mut(section_idx, para_idx, control_idx, fp)?
                    .apply_char_shape_range(x, y, new_id);
            }}
            changed.push(fp);
        }}
        if changed.is_empty() {{
            return Ok("{{\\"ok\\":true,\\"changed\\":0}}".to_string());
        }}
        self.rebuild_resolved_styles();
        for fp in &changed {{
            self.reflow_footnote_paragraph(section_idx, para_idx, control_idx, *fp);
        }}
        self.document.sections[section_idx].raw_stream = None;
        self.mark_section_dirty(section_idx);
        self.paginate_if_needed();
        self.invalidate_page_tree_cache();
        Ok(format!("{{{{\\"ok\\":true,\\"changed\\":{{}}}}}}", changed.len()))
    }}

    /// 각주 문단 리플로우
    pub(crate) fn reflow_footnote_paragraph(
"""

WASM_FIND = """    /// 머리말/꼬리말 캐럿 위치의 글자 속성을 조회한다.
"""
WASM_REPL = f"""    /// {TAG} 각주, 미주 글 범위에 글자 모양을 적용한다(칸 안 각주는 가짜 컨트롤 번호).
    #[wasm_bindgen(js_name = applyCharFormatInFootnote)]
    #[allow(clippy::too_many_arguments)]
    pub fn apply_char_format_in_footnote(
        &mut self,
        section_idx: u32,
        para_idx: u32,
        control_idx: u32,
        start_fn_para: u32,
        start_offset: u32,
        end_fn_para: u32,
        end_offset: u32,
        props_json: &str,
    ) -> Result<String, JsValue> {{
        self.core
            .claude_apply_char_format_in_footnote_native(
                section_idx as usize,
                para_idx as usize,
                control_idx as usize,
                start_fn_para as usize,
                start_offset as usize,
                end_fn_para as usize,
                end_offset as usize,
                props_json,
            )
            .map_err(|e| e.into())
    }}

    /// {TAG} 각주, 미주 글자 위치의 글자 모양을 조회한다.
    #[wasm_bindgen(js_name = getCharPropertiesInFootnote)]
    pub fn get_char_properties_in_footnote(
        &self,
        section_idx: u32,
        para_idx: u32,
        control_idx: u32,
        fn_para_idx: u32,
        char_offset: u32,
    ) -> Result<String, JsValue> {{
        self.core
            .claude_get_char_properties_in_footnote_native(
                section_idx as usize,
                para_idx as usize,
                control_idx as usize,
                fn_para_idx as usize,
                char_offset as usize,
            )
            .map_err(|e| e.into())
    }}

    /// 머리말/꼬리말 캐럿 위치의 글자 속성을 조회한다.
"""

EDITS = [
    ("document_core/commands/footnote_ops.rs", CORE_FIND, CORE_REPL),
    ("wasm_api.rs", WASM_FIND, WASM_REPL),
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
