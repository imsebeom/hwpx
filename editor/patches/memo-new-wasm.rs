    /// [claude-hwpx memo-new-wasm] 문단 안 글에 메모를 건다(오른쪽 클릭 「새 메모」).
    /// options JSON: { sectionIdx, paraIdx(본문 문단 또는 표를 품은 문단), path?, start, end, author, body, created(현지 시각 ISO, 한/글처럼 끝에 Z), fileTime: [하위, 상위] }
    #[wasm_bindgen(js_name = insertMemoEx)]
    pub fn insert_memo_ex_api(&mut self, options_json: &str) -> Result<String, JsValue> {
        let v: serde_json::Value =
            serde_json::from_str(options_json).map_err(|e| JsValue::from_str(&e.to_string()))?;
        let path: Vec<(usize, usize, usize)> = v
            .get("path")
            .and_then(|p| p.as_array())
            .map(|a| {
                a.iter()
                    .filter_map(|e| {
                        let t = e.as_array()?;
                        Some((
                            t.first()?.as_u64()? as usize,
                            t.get(1)?.as_u64()? as usize,
                            t.get(2)?.as_u64()? as usize,
                        ))
                    })
                    .collect()
            })
            .unwrap_or_default();
        let n = |k: &str| v.get(k).and_then(|x| x.as_u64()).unwrap_or(0) as usize;
        let ft = v
            .get("fileTime")
            .and_then(|x| x.as_array())
            .map(|a| (a.first().and_then(|x| x.as_u64()).unwrap_or(0) as u32, a.get(1).and_then(|x| x.as_u64()).unwrap_or(0) as u32))
            .unwrap_or((0, 0));
        let s = |k: &str| v.get(k).and_then(|x| x.as_str()).unwrap_or("").to_string();
        self.insert_memo_at(n("sectionIdx"), n("paraIdx"), &path, n("start"), n("end"), &s("author"), &s("body"), &s("created"), ft)
            .map_err(|e| e.into())
    }

