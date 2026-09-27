// @ts-nocheck
/**
 * 문단 모양 대화상자의 미리보기가 줄 간격, 문단 위/아래 간격을 따르게 한다(2026-09-27 사용자 발견).
 * rhwp 의 updatePreview 는 줄 높이를 1.5 로 고정하고 정렬, 여백, 첫 줄만 반영했으며, 정렬 단추와 첫 줄 선택에서만
 * 다시 그려 여백이나 간격 숫자를 바꿔도 그림이 그대로였다. 한/글처럼 앞뒤 문단(회색) 사이에 대상 문단(검정)을 그리고,
 * 대화상자 안의 모든 입력 변경에 다시 그린다. 스튜디오 원본은 고치지 않고 prototype 만 바꾼다.
 */
import { ParaShapeDialog } from '@/ui/para-shape-dialog';

const PT = 1.1;          // 미리보기에서 1pt 의 픽셀 수(본문 10pt = 11px)
const FONT = 10 * PT;
const OTHER = '앞 문단과 뒤 문단은 회색으로 그립니다. 바꾼 설정은 가운데 검은 문단에만 들어갑니다.';
const SAMPLE = '이것은 문단 미리보기입니다. 줄 간격, 문단 위와 아래 간격, 정렬, 여백, 들여쓰기를 바꾸면 이 문단이 그에 맞게 바뀝니다. 여러 줄이 되어야 줄 간격 차이가 보이므로 문장을 조금 길게 두었습니다.';

const num = (el) => parseFloat(el?.value) || 0;

/** 입력값으로 대상 문단의 줄 높이(px). 줄 간격 종류마다 뜻이 다르다. */
function lineHeight(type, v) {
  if (type === 'Fixed') return Math.max(1, v * PT);
  if (type === 'Minimum') return Math.max(FONT, v * PT);
  if (type === 'SpaceOnly') return FONT + v * PT;
  return FONT * (v || 160) / 100;   // Percent: 글자 크기에 대한 비율
}

function updatePreview() {
  const align = this.getSelectedAlignment();
  const ml = num(this.marginLeftInput) * PT;
  const mr = num(this.marginRightInput) * PT;
  const first = this.firstLineRadios?.find((r) => r.checked)?.value;
  const ind = num(this.indentInput) * PT;
  const lh = lineHeight(this.lineSpacingTypeSelect.value, num(this.lineSpacingInput));

  const para = (text, color) => {
    const p = document.createElement('div');
    p.style.fontSize = `${FONT}px`;
    p.style.lineHeight = `${FONT * 1.6}px`;
    p.style.color = color;
    p.style.textAlign = 'justify';
    p.textContent = text;
    return p;
  };
  const before = para(OTHER, '#b0b0b0');
  const after = para(OTHER, '#b0b0b0');
  const target = para(SAMPLE, '#111111');
  target.style.lineHeight = `${lh}px`;
  target.style.textAlign = { left: 'left', right: 'right', center: 'center' }[align] ?? 'justify';
  if (align === 'distribute' || align === 'split') target.style.textAlignLast = 'justify';
  target.style.marginLeft = `${ml}px`;
  target.style.marginRight = `${mr}px`;
  target.style.marginTop = `${num(this.spacingBeforeInput) * PT}px`;
  target.style.marginBottom = `${num(this.spacingAfterInput) * PT}px`;
  if (first === 'indent') target.style.textIndent = `${ind}px`;
  else if (first === 'hanging') {
    target.style.paddingLeft = `${ind}px`;
    target.style.textIndent = `${-ind}px`;
  }

  this.previewEl.style.height = '150px';
  this.previewEl.style.overflow = 'hidden';
  this.previewEl.replaceChildren(before, target, after);
}

export function installParaPreview() {
  const proto = ParaShapeDialog.prototype;
  if (proto.__livePreview) return;
  proto.__livePreview = true;
  proto.updatePreview = updatePreview;
  const origShow = proto.show;
  proto.show = function (props) {
    origShow.call(this, props);
    if (this.__previewListen) return;
    this.__previewListen = true;
    const redraw = () => this.updatePreview();
    this.overlay.addEventListener('input', redraw);
    this.overlay.addEventListener('change', redraw);
  };
}
