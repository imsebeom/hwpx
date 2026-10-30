// ==== find ====
  exportBytes: () => Uint8Array;
  /**
// ==== replace ====
  // [claude-hwpx export-worker-autosave] 워커 내보내기(비동기)도 받는다
  exportBytes: () => Uint8Array | Promise<Uint8Array>;
  /**
// ==== next ====
  private readonly exportBytes: () => Uint8Array;
// ==== replace ====
  private readonly exportBytes: () => Uint8Array | Promise<Uint8Array>;
// ==== next ====
      const bytes = this.exportBytes();
      const savedAt = this.now();
      const generationAtStart = this.discardGeneration;
// ==== replace ====
      const generationAtStart = this.discardGeneration;
      const bytes = await this.exportBytes();
      const savedAt = this.now();
