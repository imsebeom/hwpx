// ==== find ====
    assert_eq!(cap_para.text, "표  ");
    assert_eq!(cap_para.char_count, 13);
    assert_eq!(cap_para.char_offsets, vec![0, 1, 2, 11]);
// ==== replace ====
    // [claude-hwpx table-caption-default-tests] 한/글 2024 가 만드는 캡션과 같은 「표 {번호} 」(patches/table-caption-default.rs)
    assert_eq!(cap_para.text, "표   ");
    assert_eq!(cap_para.char_count, 12);
    assert_eq!(cap_para.char_offsets, vec![0, 1, 2, 10]);
// ==== next ====
    assert_eq!(cap_para.text, "표  ");
    assert_eq!(cap_para.char_offsets, vec![0, 1, 2, 11]);
// ==== replace ====
    assert_eq!(cap_para.text, "표   ");
    assert_eq!(cap_para.char_offsets, vec![0, 1, 2, 10]);
