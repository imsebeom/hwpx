    /// [claude-hwpx para-bf-base] 문단 테두리/배경을 바꿀 때 그 문단의 지금 BorderFill 에서 시작하게 한다.
    /// create_border_fill_from_json 은 borderFillId 가 없으면 기본값(네 변 실선)에서 시작해,
    /// 배경만 보낸 요청(fillType, 문단 모양 대화상자가 바꾼 것 없이도 보낸다)이 문단에 상자를 그렸다.
    fn para_bf_json_with_base(&self, para_shape_id: u16, props_json: &str) -> String {
        if props_json.contains("\"borderFillId\"") {
            return props_json.to_string();
        }
        let bf = self
            .document
            .doc_info
            .para_shapes
            .get(para_shape_id as usize)
            .map(|ps| ps.border_fill_id)
            .unwrap_or(0);
        match props_json.trim_start().strip_prefix('{') {
            Some(rest) if bf > 0 => format!("{{\"borderFillId\":{},{}", bf, rest),
            _ => props_json.to_string(),
        }
    }

