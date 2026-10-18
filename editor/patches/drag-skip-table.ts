// ==== find ====
        if (anchorInCell && !hitInSameCell) {
          return;
        }
      }
      this.cursor.moveToHit(hit);
      this.updateCaretDuringDrag();
// ==== replace ====
        if (anchorInCell && !hitInSameCell) {
          return;
        }
        // [claude-hwpx drag-skip-table] 본문에서 시작한 끌기가 표 칸 위로 가면 칸 안으로 들어가지 않는다(한/글은 표 밖 글과 칸 안을
        // 함께 고르지 않는다). 표를 담은 문단의 표 부호 바로 뒤(앞으로 끌 때)나 바로 앞(뒤로 끌 때)에 두어 표를 글자 하나처럼 통째로
        // 넣고 빼게 한다. 글상자 안은 종전대로.
        // 칸 안 그림 위를 맞히면 hitTest 가 parentParaIndex 없이 표를 담은 문단 번호와 배열 꼴 cellPath([[표, 칸, 칸 문단]]),
        // 그림 상자 좌표를 준다 — 이것도 표 안으로 본다(2026-10-18 사용자 보고: 그림 칸까지 끌면 캐럿이 그림 옆에 그림 높이로 섰다)
        const claudeFirst: any = hit.cellPath?.[0];
        const claudeInTable = hit.parentParaIndex !== undefined || claudeFirst !== undefined;
        if (!anchorInCell && claudeInTable && !hit.isTextBox) {
          const sec = hit.sectionIndex;
          const ppi = hit.parentParaIndex ?? hit.paragraphIndex;
          const ci = Array.isArray(claudeFirst) ? claudeFirst[0] : (claudeFirst?.controlIndex ?? hit.controlIndex);
          const pos = ci !== undefined ? this.wasm.getControlTextPositions(sec, ppi)[ci] : undefined;
          if (pos === undefined) return;
          const forward = ppi > sel.anchor.paragraphIndex
            || (ppi === sel.anchor.paragraphIndex && pos >= sel.anchor.charOffset);
          this.cursor.moveToHit({ sectionIndex: sec, paragraphIndex: ppi, charOffset: forward ? pos + 1 : pos });
          this.updateCaretDuringDrag();
          return;
        }
      }
      this.cursor.moveToHit(hit);
      this.updateCaretDuringDrag();
