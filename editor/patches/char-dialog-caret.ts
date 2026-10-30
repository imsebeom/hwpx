// ==== find ====
      const savedSel = ih.getSelection();
      if (!savedSel) return;
      const dialog = new CharShapeDialog(services.wasm, services.eventBus);
// ==== replace ====
      const savedSel = ih.getSelection();
      // [claude-hwpx char-dialog-caret] 선택이 없어도 연다(한/글과 같다). 설정은 다음에 입력하는 글자에 적용된다(캐럿 대기 서식)
      const dialog = new CharShapeDialog(services.wasm, services.eventBus);
// ==== next ====
        ih.applyCharPropsToRange(savedSel.start, savedSel.end, mods);
      };
      dialog.onClose = () => ih.focus();
      dialog.show(charProps);
// ==== replace ====
        if (savedSel) ih.applyCharPropsToRange(savedSel.start, savedSel.end, mods);
        else (ih as unknown as { applyCharFormat(p: unknown): void }).applyCharFormat(mods);
      };
      dialog.onClose = () => ih.focus();
      dialog.show(charProps);
