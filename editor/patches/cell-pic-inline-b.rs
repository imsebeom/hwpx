// ==== find ====
                    attr: common_attr,
                    treat_as_char: false,
                    vert_rel_to: VertRelTo::Para,
                    horz_rel_to: HorzRelTo::Para,
// ==== replace ====
                    // [claude-hwpx cell-pic-inline-b] 칸 글자처럼 취급 그림은 CommonObjAttr bit0 과 treat_as_char 를 켠다
                    attr: if claude_inline { common_attr | 1 } else { common_attr },
                    treat_as_char: claude_inline,
                    vert_rel_to: VertRelTo::Para,
                    horz_rel_to: HorzRelTo::Para,
