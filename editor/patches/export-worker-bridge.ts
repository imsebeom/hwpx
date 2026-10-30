// ==== find ====
  exportHwp(): Uint8Array {
    if (!this.doc) throw new Error('문서가 로드되지 않았습니다');
// ==== replace ====
  /**
   * [claude-hwpx export-worker-bridge] 주 스레드를 막지 않는 내보내기(복구본, latest.hwpx 용). wasm 메모리를 복사해(약 30ms) 워커에서
   * 내보낸다. 복사 시점의 문서가 그대로 나온다. 메모리가 너무 크거나 워커가 실패하면 주 스레드에서 내보낸다.
   * postTo 를 주면 워커가 그 주소로 바로 보내고 빈 배열을 돌려준다(36MB 를 주 스레드 fetch 로 보내면 370ms 막힌다).
   */
  async exportInWorker(kind: 'hwp' | 'hwpx', postTo?: string): Promise<Uint8Array> {
    if (!this.doc) throw new Error('문서가 로드되지 않았습니다');
    this.onBeforeExport?.();
    const onMain = (): Uint8Array => {
      if (!this.doc) throw new Error('문서가 로드되지 않았습니다');
      return kind === 'hwp' ? this.doc.exportHwp() : this.doc.exportHwpx();
    };
    const mem = this.wasmLinearMemory;
    const ptr = (this.doc as unknown as { __wbg_ptr?: number }).__wbg_ptr;
    if (!mem || !ptr || mem.buffer.byteLength > 1_200_000_000 || typeof Worker === 'undefined') return onMain();
    let worker: Worker | null = null;
    try {
      const snap = mem.buffer.slice(0);
      worker = new Worker(new URL('../plugin/export-worker.ts', import.meta.url), { type: 'module' });
      const w = worker;
      const bytes = await new Promise<Uint8Array>((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('시간 초과')), 120_000);
        w.onmessage = (e) => {
          clearTimeout(timer);
          if (e.data.ok) resolve(e.data.bytes);
          else reject(new Error(e.data.error));
        };
        w.onerror = (e) => {
          clearTimeout(timer);
          reject(new Error(e.message));
        };
        w.postMessage({ snap, ptr, kind, postTo }, [snap]);
      });
      if (postTo) return bytes;   // 워커가 검사하고 보냈다
      // 파일 머리 검사: hwpx 는 zip(PK), hwp 는 OLE(D0 CF)
      const ok = bytes.length > 4 && (kind === 'hwp' ? bytes[0] === 0xd0 && bytes[1] === 0xcf : bytes[0] === 0x50 && bytes[1] === 0x4b);
      if (!ok) throw new Error('내보낸 파일 머리가 맞지 않음');
      return bytes;
    } catch (err) {
      console.warn('[exportInWorker] 주 스레드로 되돌림:', err);
      const made = onMain();
      if (postTo) await fetch(postTo, { method: 'POST', body: made as BodyInit });
      return made;
    } finally {
      worker?.terminate();
    }
  }

  exportHwp(): Uint8Array {
    if (!this.doc) throw new Error('문서가 로드되지 않았습니다');
