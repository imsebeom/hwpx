// @ts-nocheck
/**
 * 문서 내보내기 워커. 주 스레드 wasm 메모리 사본을 받아 같은 엔진에 얹고 그 안의 문서를 내보낸다.
 * 내보내기는 49쪽 36MB 문서에서 약 1초 주 스레드를 막지만, 메모리 복사는 약 30ms 다(2026-10-30 실측, 결과 바이트 같음).
 * 호출 쪽(WasmBridge.exportInWorker)이 결과를 검사하고, 실패하면 주 스레드에서 다시 내보낸다.
 */
import init, { HwpDocument } from '@wasm/rhwp.js';

self.onmessage = async (e) => {
  const { snap, ptr, kind, postTo } = e.data;
  try {
    const w = await init();
    const mem = w.memory;
    const need = snap.byteLength - mem.buffer.byteLength;
    if (need > 0) mem.grow(Math.ceil(need / 65536));
    new Uint8Array(mem.buffer).set(new Uint8Array(snap));
    const doc = HwpDocument.__wrap(ptr);
    const bytes = kind === 'hwp' ? doc.exportHwp() : doc.exportHwpx();
    if (postTo) {
      const ok = bytes.length > 4 && (kind === 'hwp' ? bytes[0] === 0xd0 && bytes[1] === 0xcf : bytes[0] === 0x50 && bytes[1] === 0x4b);
      if (!ok) throw new Error('내보낸 파일 머리가 맞지 않음');
      const r = await fetch(postTo, { method: 'POST', body: bytes });
      if (!r.ok) throw new Error(`전송 실패 ${r.status}`);
      self.postMessage({ ok: true, bytes: new Uint8Array(0) });
      return;
    }
    self.postMessage({ ok: true, bytes }, [bytes.buffer]);
  } catch (err) {
    self.postMessage({ ok: false, error: String(err) });
  }
};
