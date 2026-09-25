    /// [claude-hwpx field-ex-wasm] 표시 글을 감싼 필드를 넣는다.
    /// options JSON: { sectionIdx, paraIdx(본문 문단 또는 표를 품은 문단), charOffset,
    ///                path?: [[controlIndex, cellIndex, cellParaIndex], ...], kind, text, params }
    #[wasm_bindgen(js_name = insertFieldEx)]
    pub fn insert_field_ex_api(&mut self, options_json: &str) -> Result<String, JsValue> {
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
        self.insert_field_ex_at(
            v.get("sectionIdx").and_then(|x| x.as_u64()).unwrap_or(0) as usize,
            v.get("paraIdx").and_then(|x| x.as_u64()).unwrap_or(0) as usize,
            &path,
            v.get("charOffset").and_then(|x| x.as_u64()).unwrap_or(0) as usize,
            v.get("kind").and_then(|x| x.as_str()).unwrap_or(""),
            v.get("text").and_then(|x| x.as_str()).unwrap_or(""),
            v.get("params").and_then(|x| x.as_str()).unwrap_or(""),
        )
        .map_err(|e| e.into())
    }

