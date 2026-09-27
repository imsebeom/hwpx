// ==== find ====
    const d = delta * overlap;
    updates.push(isHoriz ? { cellIdx: b.cellIdx, widthDelta: d } : { cellIdx: b.cellIdx, heightDelta: d });
  }
  return updates;
// ==== replace ====
    const d = delta * overlap;
    // [claude-hwpx column-resize-min] Shift, Alt 방식처럼 하나라도 최소 크기 아래로 가면 아무것도 바꾸지 않는다.
    // 검사가 없어 줄일 수 없는 크기에서도 계속 보내면 엔진이 칸마다 따로 최소값에서 멈춰, 어떤 칸은 줄고 어떤 칸은
    // 멈추며 표가 커졌다 작아졌다 어긋났다(2026-09-27 사용자 발견)
    if (cellSizeHwp(b, isHoriz) + d < RESIZE_MIN_CELL_HWP) return [];
    updates.push(isHoriz ? { cellIdx: b.cellIdx, widthDelta: d } : { cellIdx: b.cellIdx, heightDelta: d });
  }
  return updates;
