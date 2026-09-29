// ==== find ====
        assert!(resolve_picture_exclusion(
            &supported_picture(TextFlow::LeftOnly),
            0..1_000,
            0..1_000,
            50,
        )
        .is_none());
        assert!(resolve_picture_exclusion(
            &supported_picture(TextFlow::RightOnly),
            0..1_000,
            0..1_000,
            50,
        )
        .is_none());
// ==== replace ====
        // [claude-hwpx wrap-exclusion-tests] 왼쪽/오른쪽도 한쪽만 남기는 정책으로 받는다(wrap-side-policy)
        let left_only = resolve_picture_exclusion(
            &supported_picture(TextFlow::LeftOnly),
            0..1_000,
            0..1_000,
            50,
        )
        .expect("LeftOnly keeps the left lane");
        assert_eq!(left_only.policy, FrameExclusionPolicy::LeftSide);
        let right_only = resolve_picture_exclusion(
            &supported_picture(TextFlow::RightOnly),
            0..1_000,
            0..1_000,
            50,
        )
        .expect("RightOnly keeps the right lane");
        assert_eq!(right_only.policy, FrameExclusionPolicy::RightSide);
// ==== next ====
        picture.common.treat_as_char = false;
        picture.common.text_wrap = TextWrap::TopAndBottom;
        assert!(resolve_picture_exclusion(&picture, 0..1_000, 0..1_000, 0).is_none());
// ==== replace ====
        // 자리 차지는 단 폭 전체를 막아 줄을 그림 아래로 보낸다(wrap-exclusion)
        picture.common.treat_as_char = false;
        picture.common.text_wrap = TextWrap::TopAndBottom;
        let top_bottom = resolve_picture_exclusion(&picture, 0..1_000, 0..1_000, 0)
            .expect("TopAndBottom blocks the whole column");
        assert_eq!(top_bottom.horizontal, -1..1_001);

        picture.common.text_wrap = TextWrap::BehindText;
        assert!(resolve_picture_exclusion(&picture, 0..1_000, 0..1_000, 0).is_none());
