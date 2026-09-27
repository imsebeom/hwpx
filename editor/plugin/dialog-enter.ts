// @ts-nocheck
/**
 * 문단 모양, 글자 모양 대화상자에서 Enter 로 「설정」을 누르게 한다(2026-09-27 사용자 요청). 한/글처럼 숫자 칸에
 * 값을 적고 바로 Enter 로 끝낼 수 있다. 목록 상자와 단추 위, 한글 조합 중인 Enter 는 그대로 둔다.
 */
import { ParaShapeDialog } from '@/ui/para-shape-dialog';
import { CharShapeDialog } from '@/ui/char-shape-dialog';

export function installDialogEnter() {
  for (const Dialog of [ParaShapeDialog, CharShapeDialog]) {
    const proto = Dialog.prototype;
    if (proto.__enterOk) continue;
    proto.__enterOk = true;
    const origShow = proto.show;
    proto.show = function (...args) {
      origShow.apply(this, args);
      if (this.__enterListen) return;
      this.__enterListen = true;
      this.overlay.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter' || e.isComposing || e.altKey || e.ctrlKey || e.shiftKey || e.metaKey) return;
        const tag = e.target?.tagName;
        if (tag === 'SELECT' || tag === 'BUTTON' || tag === 'TEXTAREA') return;
        e.preventDefault();
        e.stopPropagation();
        this.handleOk();
      });
    };
  }
}
