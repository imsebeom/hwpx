// ==== find ====
use crate::renderer::canvas::CanvasRenderer;
use crate::renderer::composer::{
// ==== replace ====
use crate::renderer::canvas::CanvasRenderer;

thread_local! {
    /// [claude-hwpx clipboard-stash] 칸 블록 복사가 칸마다 보관하는 내부 클립보드(문단, 글)
    static CLAUDE_CLIPBOARD_STASH: std::cell::RefCell<Vec<(Vec<Paragraph>, String)>> =
        const { std::cell::RefCell::new(Vec::new()) };
}
use crate::renderer::composer::{
// ==== next ====

    /// 선택 영역을 내부 클립보드에 복사한다.
// ==== replace ====

    /// [claude-hwpx clipboard-stash] 지금 내부 클립보드를 보관함에 넣고 번호를 돌려준다(비었으면 -1).
    ///
    /// 칸 블록 복사(여러 칸)는 칸마다 내부 클립보드가 필요한데 엔진의 내부 클립보드는 한 벌이다. 칸마다 복사한 뒤 보관하고,
    /// 붙일 때 `claudeClipboardRestore` 로 그 칸 것을 되살려 `pasteInternalInCellByPath` 로 붙인다 — HTML 을 거치면 글자 모양이
    /// 다른 번호로 바뀌고 그림이 「[이미지]」 글로 바뀌었다(2026-10-06).
    #[wasm_bindgen(js_name = claudeClipboardStash)]
    pub fn claude_clipboard_stash(&self) -> i32 {
        let Some(clip) = self.core.clipboard.as_ref() else {
            return -1;
        };
        CLAUDE_CLIPBOARD_STASH.with(|stash| {
            let mut stash = stash.borrow_mut();
            stash.push((clip.paragraphs.clone(), clip.plain_text.clone()));
            (stash.len() - 1) as i32
        })
    }

    /// [claude-hwpx clipboard-stash] 보관함의 그 번호를 내부 클립보드로 되살린다.
    #[wasm_bindgen(js_name = claudeClipboardRestore)]
    pub fn claude_clipboard_restore(&mut self, id: u32) -> bool {
        let item = CLAUDE_CLIPBOARD_STASH.with(|stash| stash.borrow().get(id as usize).cloned());
        let Some((paragraphs, plain_text)) = item else {
            return false;
        };
        self.core.clipboard = Some(crate::document_core::ClipboardData { paragraphs, plain_text });
        true
    }

    /// [claude-hwpx clipboard-stash] 보관함을 비운다.
    #[wasm_bindgen(js_name = claudeClipboardStashClear)]
    pub fn claude_clipboard_stash_clear(&self) {
        CLAUDE_CLIPBOARD_STASH.with(|stash| stash.borrow_mut().clear());
    }

    /// 선택 영역을 내부 클립보드에 복사한다.
