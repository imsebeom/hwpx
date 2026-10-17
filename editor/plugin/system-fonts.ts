/**
 * 이 PC 에 설치된 글꼴을 글꼴 목록에 넣고, 처음 고르는 글꼴의 폭 표를 엔진에 등록한다.
 *
 * 브라우저의 글꼴 접근 권한(queryLocalFonts)은 앱 창(pywebview)에서 동작하지 않아 「모든 글꼴」이 기본 글꼴과 문서 글꼴뿐이었다.
 * 에디터 서버는 줄 나눔 폭 때문에 이미 Windows 글꼴 폴더를 색인하므로(font-metrics.mjs) 그 목록을 받아 로컬 글꼴로 더한다
 * (그리기는 CSS 글꼴 이름으로 설치 글꼴을 쓴다). 폭 표는 고를 때 받는다 — toolbar 패치(font-metrics-on-pick)가
 * `__claudeEnsureFontMetrics` 를 부른다. 이미 등록했거나 서버가 없으면 false 를 돌려 바로 적용하게 한다.
 */
import * as rhwpWasm from '@wasm/rhwp.js';
import { claudeAddHostFonts } from '@/core/local-fonts';

const asked = new Set<string>();

async function ensureFontMetrics(name: string): Promise<number> {
  asked.add(name);
  const r = await fetch(`/api/font-metrics?name=${encodeURIComponent(name)}`).then((x) => x.json());
  if (!r?.ok || !Array.isArray(r.metrics) || r.metrics.length === 0) return 0;
  const register = (rhwpWasm as unknown as { registerFontMetrics?: (json: string) => number }).registerFontMetrics;
  return typeof register === 'function' ? register(JSON.stringify(r.metrics)) : 0;
}

export function installSystemFonts(): void {
  (globalThis as { __claudeEnsureFontMetrics?: (name: string) => Promise<number> | boolean }).__claudeEnsureFontMetrics = (name) => {
    if (!name || asked.has(name)) return false;
    return ensureFontMetrics(name);
  };
  void fetch('/api/system-fonts')
    .then((x) => x.json())
    .then((r) => {
      if (r?.ok && Array.isArray(r.fonts) && r.fonts.length) {
        const n = claudeAddHostFonts(r.fonts);
        console.log(`[claude] 설치 글꼴 ${r.fonts.length}개를 글꼴 목록에 더함(로컬 글꼴 ${n})`);
      }
    })
    .catch(() => undefined);
}
