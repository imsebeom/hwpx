// ==== find ====
export function recoveryFileName(fileName: string): string {
  const base = baseNameWithoutKnownExtension(fileName);
  // autosave draft는 exportHwp() 결과이므로 모든 출처의 복구본은 HWP로 생성한다.
  return `${base} 복구본.hwp`;
}
// ==== replace ====
// [claude-hwpx recovery-hwpx-format] 복구본 형식은 내용으로 가린다(hwpx 는 zip). 전에 저장한 hwp 복구본도 그대로 열린다
const isZip = (data?: Uint8Array): boolean => !!data && data.length > 2 && data[0] === 0x50 && data[1] === 0x4b;

export function recoveryFileName(fileName: string, data?: Uint8Array): string {
  const base = baseNameWithoutKnownExtension(fileName);
  return `${base} 복구본.${isZip(data) ? 'hwpx' : 'hwp'}`;
}
// ==== next ====
  const suffix = ['hwpx', 'hml'].includes(draft.sourceFormat.toLowerCase()) ? ' → HWP 복구본' : '';
// ==== replace ====
  const suffix = ['hwpx', 'hml'].includes(draft.sourceFormat.toLowerCase()) && !isZip(new Uint8Array(draft.data)) ? ' → HWP 복구본' : '';
