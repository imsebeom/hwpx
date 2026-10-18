// ==== find ====
        // 각주 영역 클릭 → 내부 텍스트 히트테스트로 커서 이동
        try {
          const inFnHit = this.wasm.hitTestInFootnote(pageIdx, pageX, pageY);
          if (inFnHit.hit && inFnHit.fnParaIndex !== undefined && inFnHit.charOffset !== undefined) {
// ==== replace ====
        // 각주 영역 클릭 → 내부 텍스트 히트테스트로 커서 이동
        try {
          const inFnHit = this.wasm.hitTestInFootnote(pageIdx, pageX, pageY);
          // [claude-hwpx fn-cell-target-mouse] 같은 쪽의 다른 각주를 누르면 그 각주로 옮겨 탄다(전에는 원래 각주에 남아 캐럿만 움직였다).
          // 편집 모드를 나와 아래 진입 경로로 흘려보낸다
          if (inFnHit.hit && inFnHit.footnoteIndex !== undefined
            && (inFnHit.footnoteIndex !== this.cursor.fnFootnoteIndex || pageIdx !== this.cursor.fnPageNum)) {
            this.cursor.exitFootnoteMode();
            this.eventBus.emit('footnoteModeChanged', false);
            throw new Error('claude-switch-footnote');
          }
          if (inFnHit.hit && inFnHit.fnParaIndex !== undefined && inFnHit.charOffset !== undefined) {
// ==== next ====
        } catch { /* 무시 */ }
        this.textarea.focus();
        return;
      }
    } catch { /* 무시 */ }
  }

  // 본문 각주 마커 클릭 → 각주 편집 모드 진입
// ==== replace ====
        } catch (err) {
          // [claude-hwpx fn-cell-target-mouse] 다른 각주로 옮겨 타면 아래 진입 경로로 간다
          if (!(err instanceof Error && err.message === 'claude-switch-footnote')) { this.textarea.focus(); return; }
        }
        if (this.cursor.isInFootnote()) {
          this.textarea.focus();
          return;
        }
      }
    } catch { /* 무시 */ }
  }

  // 본문 각주 마커 클릭 → 각주 편집 모드 진입
// ==== next ====
          const pageInfo = this.wasm.getPageFootnoteInfo(pageIdx, inFnHit.footnoteIndex);
          if (pageInfo && pageInfo.sourceType === 'body') {
            this.cursor.enterFootnoteMode(
              pageInfo.sectionIdx, pageInfo.paraIdx, pageInfo.controlIdx,
              inFnHit.footnoteIndex, pageIdx,
            );
// ==== replace ====
          const pageInfo = this.wasm.getPageFootnoteInfo(pageIdx, inFnHit.footnoteIndex);
          // [claude-hwpx fn-cell-target-mouse] 표 칸 안 각주도 편집에 들어간다. 칸 위치를 엔진에 등록해 받은 가짜 컨트롤 번호로 각주 함수를 부른다
          // (전에는 출처가 본문 문단인 각주만 들어가 칸 안 각주가 섞인 쪽에서 위쪽 각주가 눌리지 않았다)
          if (pageInfo && pageInfo.sourceType === 'table' && pageInfo.cellIdx !== undefined
            && pageInfo.cellParaIdx !== undefined && pageInfo.cellControlIdx !== undefined) {
            const fake = this.wasm.registerFootnoteCellTarget(
              pageInfo.paraIdx, pageInfo.controlIdx, pageInfo.cellIdx, pageInfo.cellParaIdx, pageInfo.cellControlIdx,
            );
            if (fake !== null && fake !== undefined) {
              pageInfo.controlIdx = fake;
              pageInfo.sourceType = 'body';
            }
          }
          if (pageInfo && pageInfo.sourceType === 'body') {
            this.cursor.enterFootnoteMode(
              pageInfo.sectionIdx, pageInfo.paraIdx, pageInfo.controlIdx,
              inFnHit.footnoteIndex, pageIdx,
            );
