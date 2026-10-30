// ==== find ====
    if (!this.selectedPictureRef) return;
    const outside = this.positionOutsideSelectedPicture();
    if (outside) this.position = outside;
    this.exitPictureObjectSelection();
// ==== replace ====
    if (!this.selectedPictureRef) return;
    // [claude-hwpx pic-esc-stay] 칸 안 그림은 Esc 로 칸 밖에 나가지 않고 그 칸 문단 끝에 커서를 둔다
    const r = this.selectedPictureRef as any;
    const path = r.cellPath?.length
      ? r.cellPath
      : (r.cellIdx != null && r.outerTableControlIdx != null
        ? [{ controlIndex: r.outerTableControlIdx, cellIndex: r.cellIdx, cellParaIndex: r.cellParaIdx ?? 0 }]
        : null);
    let stay: DocumentPosition | null = null;
    if (path && r.type === 'image' && !r.headerFooter && !r.noteRef) {
      try {
        const last = path[path.length - 1];
        const len = this.wasm.getCellParagraphLengthByPath(r.sec, r.ppi, JSON.stringify(path));
        stay = {
          sectionIndex: r.sec, paragraphIndex: last.cellParaIndex, charOffset: len, parentParaIndex: r.ppi,
          controlIndex: path[0].controlIndex, cellIndex: path[0].cellIndex, cellParaIndex: path[0].cellParaIndex, cellPath: path,
        } as DocumentPosition;
      } catch { /* 글상자 안 등 칸 경로가 아니면 종전대로 */ }
    }
    const outside = stay ?? this.positionOutsideSelectedPicture();
    if (outside) this.position = outside;
    this.exitPictureObjectSelection();
