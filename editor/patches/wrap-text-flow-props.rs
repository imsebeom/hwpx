// ==== find ====
    text_wrap: u8,
    margin: (i16, i16, i16, i16),
}
// ==== replace ====
    text_wrap: u8,
    // [claude-hwpx wrap-text-flow-props] 본문 위치(양쪽, 왼쪽, 오른쪽, 큰 쪽)도 띠를 바꾼다
    text_flow: u8,
    margin: (i16, i16, i16, i16),
}
// ==== next ====
        text_wrap: common.text_wrap as u8,
        margin: (
// ==== replace ====
        text_wrap: common.text_wrap as u8,
        text_flow: common.text_flow as u8,
        margin: (
// ==== next ====
        let effect = match pic.image_attr.effect {
// ==== replace ====
        let text_flow = match c.text_flow {
            crate::model::shape::TextFlow::BothSides => "BothSides",
            crate::model::shape::TextFlow::LeftOnly => "LeftOnly",
            crate::model::shape::TextFlow::RightOnly => "RightOnly",
            crate::model::shape::TextFlow::LargestOnly => "LargestOnly",
        };
        let effect = match pic.image_attr.effect {
// ==== next ====
                "\"textWrap\":\"{}\",\"restrictInPage\":{},\"allowOverlap\":{},\"sizeProtect\":{},",
// ==== replace ====
                "\"textWrap\":\"{}\",\"textFlow\":\"{}\",\"restrictInPage\":{},\"allowOverlap\":{},\"sizeProtect\":{},",
// ==== next ====
            text_wrap, c.flow_with_text, c.allow_overlap, c.size_protect,
// ==== replace ====
            text_wrap, text_flow, c.flow_with_text, c.allow_overlap, c.size_protect,
// ==== next ====
        if let Some(v) = json_bool(props_json, "restrictInPage") {
            pic.common.flow_with_text = v;
// ==== replace ====
        if let Some(v) = json_str(props_json, "textFlow") {
            pic.common.text_flow = match v.as_str() {
                "BothSides" => crate::model::shape::TextFlow::BothSides,
                "LeftOnly" => crate::model::shape::TextFlow::LeftOnly,
                "RightOnly" => crate::model::shape::TextFlow::RightOnly,
                "LargestOnly" => crate::model::shape::TextFlow::LargestOnly,
                _ => pic.common.text_flow,
            };
        }
        if let Some(v) = json_bool(props_json, "restrictInPage") {
            pic.common.flow_with_text = v;
