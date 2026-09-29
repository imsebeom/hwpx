// ==== find ====
    let (cur, prev) = (&segs[idx], &segs[idx - 1]);
    cur.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0
        && prev.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0
        && cur.vertical_pos == prev.vertical_pos
        && cur.column_start != prev.column_start
// ==== replace ====
    let (cur, prev) = (&segs[idx], &segs[idx - 1]);
    let impl_bit = LineSeg::TAG_IMPLEMENTATION_PROPERTY;
    // [claude-hwpx wrap-band-fragment] 편집 뒤 그림 띠(layout_picture_band)가 새로 짠 좌우 조각도 한 줄이다.
    // 엔진이 만든 줄(구현 비트)은 저장 증거가 아니라 종전에는 빠졌는데, 그러면 어울림 양쪽 그림 옆 줄이
    // 조각마다 한 줄씩 쌓여 문단이 두 배로 길어졌다. 띠 조각은 한 줄의 첫 조각만 FIRST, 끝 조각만 LAST 를
    // 달므로(한 조각 줄은 둘 다) 앞 조각에 LAST 가 없고 뒤 조각에 FIRST 가 없을 때만 이어진 조각으로 본다
    let authentic = cur.tag & impl_bit == 0 && prev.tag & impl_bit == 0;
    let band_fragment = cur.tag & impl_bit != 0
        && prev.tag & impl_bit != 0
        && prev.tag & LineSeg::TAG_LAST_SEGMENT == 0
        && cur.tag & LineSeg::TAG_FIRST_SEGMENT == 0;
    (authentic || band_fragment)
        && cur.vertical_pos == prev.vertical_pos
        && cur.column_start != prev.column_start
