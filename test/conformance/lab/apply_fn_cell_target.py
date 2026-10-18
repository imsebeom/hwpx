"""개발용: 표 칸 안 각주, 미주도 각주 편집 함수로 다룰 수 있게 한다(칸 안 각주 위치 등록 + 가짜 컨트롤 번호).

    python apply_fn_cell_target.py [--revert]

근거(2026-10-19 사용자 보고): 각주가 많으면 위쪽 각주가 눌리지 않는다. 각주 영역을 누르면 에디터는 출처가 본문 문단인 각주만
편집에 들어가고(getPageFootnoteInfo 의 sourceType === 'body'), 표 칸 안 각주(가이드북은 섞여 있다)는 무시했다. 엔진의 각주 함수들
(글 넣기, 지우기, 문단 나누기와 합치기, 정보, 줄 다시 만들기)이 (구역, 본문 문단, 컨트롤 번호)만 받아서다. 칸 안 각주의
(표가 든 문단, 표 컨트롤, 칸, 칸 문단, 각주 컨트롤)을 목록에 등록하고 CLAUDE_FN_CELL_BASE + 목록 번호를 컨트롤 번호로 쓴다.
등록마다 번호가 따로라 되돌리기 기록도 제자리를 찾는다. getPageFootnoteInfo 는 칸 정보를 함께 준다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx fn-cell-target]"

HELPERS = r"""
/// TAG 칸 안 각주 위치를 가리키는 가짜 컨트롤 번호의 시작. 이 값 이상이면 claude_fn_cells 목록 번호로 읽는다.
pub(crate) const CLAUDE_FN_CELL_BASE: usize = 0x4000_0000;

/// TAG 각주 컨트롤(가변). 컨트롤 번호가 CLAUDE_FN_CELL_BASE 이상이면 등록된 칸 안 각주를 찾는다.
pub(crate) fn claude_note_ctrl_mut<'a>(
    doc: &'a mut crate::model::document::Document,
    cells: &[[usize; 5]],
    section_idx: usize,
    para_idx: usize,
    control_idx: usize,
) -> Option<&'a mut Control> {
    let host = doc.sections.get_mut(section_idx)?.paragraphs.get_mut(para_idx)?;
    if control_idx >= CLAUDE_FN_CELL_BASE {
        let [pp, tc, ci, cp, cc] = *cells.get(control_idx - CLAUDE_FN_CELL_BASE)?;
        if pp != para_idx {
            return None;
        }
        match host.controls.get_mut(tc)? {
            Control::Table(t) => t.cells.get_mut(ci)?.paragraphs.get_mut(cp)?.controls.get_mut(cc),
            _ => None,
        }
    } else {
        host.controls.get_mut(control_idx)
    }
}

/// TAG 각주 컨트롤(읽기).
pub(crate) fn claude_note_ctrl<'a>(
    doc: &'a crate::model::document::Document,
    cells: &[[usize; 5]],
    section_idx: usize,
    para_idx: usize,
    control_idx: usize,
) -> Option<&'a Control> {
    let host = doc.sections.get(section_idx)?.paragraphs.get(para_idx)?;
    if control_idx >= CLAUDE_FN_CELL_BASE {
        let [pp, tc, ci, cp, cc] = *cells.get(control_idx - CLAUDE_FN_CELL_BASE)?;
        if pp != para_idx {
            return None;
        }
        match host.controls.get(tc)? {
            Control::Table(t) => t.cells.get(ci)?.paragraphs.get(cp)?.controls.get(cc),
            _ => None,
        }
    } else {
        host.controls.get(control_idx)
    }
}

impl DocumentCore {
    /// TAG 칸 안 각주 위치를 등록하고 가짜 컨트롤 번호를 돌려준다(같은 위치는 같은 번호).
    pub fn claude_register_fn_cell(
        &mut self,
        parent_para: usize,
        table_ctrl: usize,
        cell_idx: usize,
        cell_para: usize,
        cell_ctrl: usize,
    ) -> usize {
        let key = [parent_para, table_ctrl, cell_idx, cell_para, cell_ctrl];
        let idx = match self.claude_fn_cells.iter().position(|k| *k == key) {
            Some(i) => i,
            None => {
                self.claude_fn_cells.push(key);
                self.claude_fn_cells.len() - 1
            }
        };
        CLAUDE_FN_CELL_BASE + idx
    }
"""

NOT_FOUND = (
    'HwpError::RenderError(format!("각주 컨트롤 {} 을 찾을 수 없음", control_idx))'
)

SPLIT_MERGE_FIND = (
    "            let section = self.document.sections.get_mut(section_idx).ok_or_else(|| {\n"
    '                HwpError::RenderError(format!("구역 인덱스 {} 범위 초과", section_idx))\n'
    "            })?;\n"
    "            let para = section.paragraphs.get_mut(para_idx).ok_or_else(|| {\n"
    '                HwpError::RenderError(format!("문단 인덱스 {} 범위 초과", para_idx))\n'
    "            })?;\n"
    "            let ctrl = para.controls.get_mut(control_idx).ok_or_else(|| {\n"
    '                HwpError::RenderError(format!("컨트롤 인덱스 {} 범위 초과", control_idx))\n'
    "            })?;\n"
)
SPLIT_MERGE_REPL = (
    f"            // {TAG}\n"
    "            let ctrl = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)\n"
    f"                .ok_or_else(|| {NOT_FOUND})?;\n"
)

EDITS = [
    # 구조체 필드
    (
        "document_core/mod.rs",
        "    pub(crate) validation_report: validation::ValidationReport,\n}\n",
        "    pub(crate) validation_report: validation::ValidationReport,\n"
        f"    /// {TAG} 등록한 표 칸 안 각주 위치 [표가 든 문단, 표 컨트롤, 칸, 칸 문단, 각주 컨트롤]\n"
        "    pub(crate) claude_fn_cells: Vec<[usize; 5]>,\n}\n",
        1,
    ),
    (
        "document_core/mod.rs",
        "            validation_report: validation::ValidationReport::new(),\n        }\n",
        "            validation_report: validation::ValidationReport::new(),\n            claude_fn_cells: Vec::new(),\n        }\n",
        1,
    ),
    (
        "document_core/commands/document.rs",
        "            validation_report,\n",
        "            validation_report,\n            claude_fn_cells: Vec::new(), // [claude-hwpx fn-cell-target]\n",
        1,
    ),
    # 도우미와 등록 함수: 첫 impl 앞에 두고 impl 을 이어 연다
    (
        "document_core/commands/footnote_ops.rs",
        "impl DocumentCore {\n    fn renumber_footnotes_in_section(",
        HELPERS.replace("TAG", TAG) + "\n    fn renumber_footnotes_in_section(",
        1,
    ),
    # get_footnote_paragraph_mut
    (
        "document_core/commands/footnote_ops.rs",
        "        let section = self.document.sections.get_mut(section_idx).ok_or_else(|| {\n"
        '            HwpError::RenderError(format!("구역 인덱스 {} 범위 초과", section_idx))\n'
        "        })?;\n"
        "        let para = section\n"
        "            .paragraphs\n"
        "            .get_mut(para_idx)\n"
        '            .ok_or_else(|| HwpError::RenderError(format!("문단 인덱스 {} 범위 초과", para_idx)))?;\n'
        "        let ctrl = para.controls.get_mut(control_idx).ok_or_else(|| {\n"
        '            HwpError::RenderError(format!("컨트롤 인덱스 {} 범위 초과", control_idx))\n'
        "        })?;\n",
        f"        // {TAG} 칸 안 각주(가짜 컨트롤 번호)도 찾는다\n"
        "        let ctrl = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)\n"
        f"            .ok_or_else(|| {NOT_FOUND})?;\n",
        1,
    ),
    # get_footnote_paragraph_ref
    (
        "document_core/commands/footnote_ops.rs",
        "        let section = self.document.sections.get(section_idx)?;\n"
        "        let para = section.paragraphs.get(para_idx)?;\n"
        "        let ctrl = para.controls.get(control_idx)?;\n",
        f"        // {TAG}\n"
        "        let ctrl = claude_note_ctrl(&self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)?;\n",
        1,
    ),
    # reflow_footnote_paragraph
    (
        "document_core/commands/footnote_ops.rs",
        "        let section = &mut self.document.sections[section_idx];\n"
        "        let ctrl = &mut section.paragraphs[para_idx].controls[control_idx];\n",
        f"        // {TAG}\n"
        "        let Some(ctrl) = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx) else {\n"
        "            return;\n"
        "        };\n",
        1,
    ),
    # get_footnote_info_native
    (
        "document_core/commands/footnote_ops.rs",
        "        let section = self.document.sections.get(section_idx).ok_or_else(|| {\n"
        '            HwpError::RenderError(format!("구역 인덱스 {} 범위 초과", section_idx))\n'
        "        })?;\n"
        "        let para = section\n"
        "            .paragraphs\n"
        "            .get(para_idx)\n"
        '            .ok_or_else(|| HwpError::RenderError(format!("문단 인덱스 {} 범위 초과", para_idx)))?;\n'
        "        let ctrl = para.controls.get(control_idx).ok_or_else(|| {\n"
        '            HwpError::RenderError(format!("컨트롤 인덱스 {} 범위 초과", control_idx))\n'
        "        })?;\n",
        f"        // {TAG}\n"
        "        let ctrl = claude_note_ctrl(&self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)\n"
        f"            .ok_or_else(|| {NOT_FOUND})?;\n",
        1,
    ),
    # split
    (
        "document_core/commands/footnote_ops.rs",
        "        let mut new_para = {\n" + SPLIT_MERGE_FIND,
        "        let mut new_para = {\n" + SPLIT_MERGE_REPL,
        1,
    ),
    # merge
    (
        "document_core/commands/footnote_ops.rs",
        "        let removed_meta;\n        {\n" + SPLIT_MERGE_FIND,
        "        let removed_meta;\n        {\n" + SPLIT_MERGE_REPL,
        1,
    ),
    # split 의 새 문단 넣기
    (
        "document_core/commands/footnote_ops.rs",
        "            let ctrl =\n"
        "                &mut self.document.sections[section_idx].paragraphs[para_idx].controls[control_idx];\n",
        f"            // {TAG}\n"
        "            let ctrl = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)\n"
        f"                .ok_or_else(|| {NOT_FOUND})?;\n",
        1,
    ),
    # 쪽 각주 정보에 칸 정보
    (
        "document_core/queries/cursor_rect.rs",
        "        Ok(format!(\n"
        '            "{{\\"ok\\":true,\\"sectionIdx\\":{},\\"paraIdx\\":{},\\"controlIdx\\":{},\\"sourceType\\":\\"{}\\"}}",\n'
        "            section_idx, para_idx, control_idx, source_type\n"
        "        ))\n",
        f"        // {TAG} 표 칸 출처면 칸 위치를 함께 준다(에디터가 칸 안 각주를 등록해 편집에 들어간다)\n"
        "        let claude_cell = match &fn_ref.source {\n"
        "            FootnoteSource::TableCell {\n"
        "                cell_index,\n"
        "                cell_para_index,\n"
        "                cell_control_index,\n"
        "                ..\n"
        "            } => format!(\n"
        '                ",\\"cellIdx\\":{},\\"cellParaIdx\\":{},\\"cellControlIdx\\":{}",\n'
        "                cell_index, cell_para_index, cell_control_index\n"
        "            ),\n"
        "            _ => String::new(),\n"
        "        };\n"
        "        Ok(format!(\n"
        '            "{{\\"ok\\":true,\\"sectionIdx\\":{},\\"paraIdx\\":{},\\"controlIdx\\":{},\\"sourceType\\":\\"{}\\"{}}}",\n'
        "            section_idx, para_idx, control_idx, source_type, claude_cell\n"
        "        ))\n",
        1,
    ),
    # wasm 등록 함수
    (
        "wasm_api.rs",
        "    /// 글로벌 쪽 번호에 해당하는 첫 문단 위치 반환\n    #[wasm_bindgen(js_name = getPositionOfPage)]\n",
        f"    /// {TAG} 표 칸 안 각주 위치를 등록하고 각주 함수에 넘길 가짜 컨트롤 번호를 돌려준다\n"
        "    #[wasm_bindgen(js_name = registerFootnoteCellTarget)]\n"
        "    pub fn register_footnote_cell_target(\n"
        "        &mut self,\n"
        "        parent_para: u32,\n"
        "        table_ctrl: u32,\n"
        "        cell_idx: u32,\n"
        "        cell_para: u32,\n"
        "        cell_ctrl: u32,\n"
        "    ) -> u32 {\n"
        "        self.core.claude_register_fn_cell(\n"
        "            parent_para as usize,\n"
        "            table_ctrl as usize,\n"
        "            cell_idx as usize,\n"
        "            cell_para as usize,\n"
        "            cell_ctrl as usize,\n"
        "        ) as u32\n"
        "    }\n\n"
        "    /// 글로벌 쪽 번호에 해당하는 첫 문단 위치 반환\n    #[wasm_bindgen(js_name = getPositionOfPage)]\n",
        1,
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl, want in edits:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        if (repl not in s) if revert else (repl in s):
            print("이미", rel)
            continue
        n = s.count(find)
        if n != want:
            sys.exit(f"{rel}: 자리 {n}곳(기대 {want}) — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
