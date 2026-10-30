// ==== find ====
            self.provenance.format == SourceFormat::Hwpx && !native_hwp3_hwpx,
            hwp5_origin_hwpx,
// ==== replace ====
            // [claude-hwpx hwpx-lineage-layout] 에디터가 hwpx 에서 내보낸 hwp 는 같은 문서다. 같은 규칙으로 조판해야 쪽수가 안 바뀐다
            (self.provenance.format == SourceFormat::Hwpx && !native_hwp3_hwpx) || self.provenance.hwpx_lineage,
            hwp5_origin_hwpx,
