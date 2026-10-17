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
        // 넣고 빼게 한다. 글상자 안은 종전대로
        if (!anchorInCell && hit.parentParaIndex !== undefined && !hit.isTextBox) {
          const sec = hit.sectionIndex;
          const ppi = hit.parentParaIndex;
          const ci = hit.cellPath?.[0]?.controlIndex ?? hit.controlIndex;
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
