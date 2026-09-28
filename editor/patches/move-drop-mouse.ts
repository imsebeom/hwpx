// ==== find ====
                const props = this.getObjectProperties(ref);
                if (!props.treatAsChar) {
// ==== replace ====
                const props = this.getObjectProperties(ref);
                // [claude-hwpx move-drop-line] 본문의 글자처럼 취급 그림도 끌 수 있게 한다 — 놓을 때 문단 자리로 옮긴다(move-drop-picture)
                if (!props.treatAsChar || (ref.type === 'image' && !ref.cellPath?.length && !ref.headerFooter)) {
