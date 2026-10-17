// ==== find ====
function cacheLocalFontSnapshot(snapshot: LocalFontSnapshot | null): void {
  cachedSnapshot = snapshot;
  cachedFontRecords = snapshotRecords(snapshot);
  cachedFontLookup = buildLocalFontLookup(cachedFontRecords);
}
// ==== replace ====
// [claude-hwpx host-fonts] 에디터 서버가 읽어 준 이 PC 의 설치 글꼴(브라우저 글꼴 접근 권한 없이). 브라우저 감지 결과와 늘 합친다
let claudeHostRecords: LocalFontRecord[] = [];

function cacheLocalFontSnapshot(snapshot: LocalFontSnapshot | null): void {
  cachedSnapshot = snapshot;
  const own = snapshotRecords(snapshot);
  const known = new Set(own.map(record => record.family.toLocaleLowerCase('ko-KR')));
  cachedFontRecords = [...own, ...claudeHostRecords.filter(record => !known.has(record.family.toLocaleLowerCase('ko-KR')))];
  cachedFontLookup = buildLocalFontLookup(cachedFontRecords);
}

/** [claude-hwpx host-fonts] 서버가 준 설치 글꼴 가족을 로컬 글꼴로 더한다. 반환: 더한 뒤 로컬 글꼴 수 */
export function claudeAddHostFonts(fonts: ReadonlyArray<{ name: string; aliases?: string[] }>): number {
  claudeHostRecords = normalizeLocalFontRecords(
    fonts.map(font => ({
      family: font.name,
      fullName: font.name,
      postscriptName: '',
      style: '',
      displayName: font.name,
      aliases: font.aliases ?? [],
      detectionSource: 'font-presence-probe' as LocalFontDetectionSource,
    })),
    'font-presence-probe',
  );
  cacheLocalFontSnapshot(cachedSnapshot);
  return cachedFontRecords.length;
}
