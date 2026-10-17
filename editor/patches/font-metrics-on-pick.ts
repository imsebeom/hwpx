// ==== find ====
      // 대표 글꼴 세트 선택인지 확인
      const fontSet = this.findFontSetByName(name);
      if (fontSet) {
        this.applyFontSet(fontSet);
        return;
      }
// ==== replace ====
      // 대표 글꼴 세트 선택인지 확인
      const fontSet = this.findFontSetByName(name);
      if (fontSet) {
        this.applyFontSet(fontSet);
        return;
      }

      // [claude-hwpx font-metrics-on-pick] 처음 고르는 글꼴은 에디터 서버에서 그 글꼴 파일의 폭 표를 받아 엔진에 등록한 뒤 적용한다.
      // 먼저 적용하면 줄 나눔이 어림 폭(한글 1em, 그 밖 0.5em)으로 계산된다
      const claudeEnsure = (globalThis as { __claudeEnsureFontMetrics?: (name: string) => Promise<unknown> | boolean })
        .__claudeEnsureFontMetrics;
      if (typeof claudeEnsure === 'function') {
        const pending = claudeEnsure(name);
        if (pending instanceof Promise) {
          void pending.catch(() => undefined).then(() => {
            if (this.fontName.value === name) this.fontName.dispatchEvent(new Event('change', { bubbles: true }));
          });
          return;
        }
      }
