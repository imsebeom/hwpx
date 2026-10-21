// @ts-nocheck
/**
 * 오른쪽 클릭 메뉴를 한/글처럼 늘린다(2026-10-21 사용자 요청). rhwp 기본 메뉴는 오려 두기, 복사, 붙이기와 글자, 문단 모양뿐이라
 * 지우기, 스타일, 글머리표, 하이퍼링크, 모두 선택, 찾아 바꾸기를 더한다. 표 안 메뉴에도 지우기와 글자, 문단 모양을 넣는다.
 * 「새 메모」는 k-commands.ts 의 insert:comment(엔진 insertMemoEx). 교정 부호, 번역처럼 studio 에 동작이 없는 명령은 넣지 않는다.
 */
const sep = { type: 'separator' };
const cmd = (commandId, label) => ({ type: 'command', commandId, ...(label ? { label } : {}) });

const TEXT_MENU = [
  cmd('edit:cut'), cmd('edit:copy'), cmd('edit:paste'), cmd('edit:delete'),
  cmd('edit:format-copy'), cmd('edit:format-paste'), cmd('table:transpose-paste'),
  sep,
  cmd('format:char-shape', '글자 모양'), cmd('format:para-shape', '문단 모양'), cmd('format:style-dialog', '스타일'),
  sep,
  cmd('format:bullet-shape', '글머리표 모양'), cmd('format:para-num-shape', '문단 번호 모양(N)...'),
  sep,
  cmd('insert:hyperlink', '하이퍼링크'), cmd('insert:comment', '새 메모'),
  sep,
  cmd('edit:select-all'), cmd('edit:find-replace'),
];
const CELL_EXTRA = [sep, cmd('format:char-shape', '글자 모양'), cmd('format:para-shape', '문단 모양')];

export function installContextMenu(getInputHandler) {
  const patch = () => {
    const ih = getInputHandler();
    if (!ih?.getDefaultContextMenuItems) return false;
    if (ih.__kMenu) return true;
    ih.__kMenu = true;
    ih.getDefaultContextMenuItems = () => TEXT_MENU;
    const cellMenu = ih.getTableContextMenuItems.bind(ih);
    ih.getTableContextMenuItems = () => {
      const items = cellMenu();
      const at = items.findIndex((it) => it.commandId === 'edit:paste') + 1;   // 붙이기 뒤에 지우기, 모양 복사 묶음 뒤에 글자, 문단 모양
      items.splice(at, 0, cmd('edit:delete'));
      const fmtEnd = items.findIndex((it) => it.commandId === 'edit:format-paste') + 1;
      items.splice(fmtEnd, 0, ...CELL_EXTRA);
      return items;
    };
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }
}
