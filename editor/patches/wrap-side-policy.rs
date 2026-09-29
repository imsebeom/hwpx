// ==== find ====
pub(crate) enum FrameExclusionPolicy {
    BothSides,
    LargestSide,
}
// ==== replace ====
pub(crate) enum FrameExclusionPolicy {
    BothSides,
    LargestSide,
    // [claude-hwpx wrap-side-policy] 어울림 「왼쪽」, 「오른쪽」(TextFlow LeftOnly/RightOnly): 개체의 그쪽에만 글이 흐른다
    LeftSide,
    RightSide,
}
// ==== next ====
                        if exclusion.policy == FrameExclusionPolicy::LargestSide {
// ==== replace ====
                        if exclusion.policy == FrameExclusionPolicy::LeftSide {
                            carved.push(left_interval);
                        } else if exclusion.policy == FrameExclusionPolicy::RightSide {
                            carved.push(right_interval);
                        } else if exclusion.policy == FrameExclusionPolicy::LargestSide {
// ==== next ====
                    } else if interval.start < left {
                        carved.push(interval.start..left);
                    } else if right < interval.end {
                        carved.push(right..interval.end);
                    } else {
// ==== replace ====
                    } else if interval.start < left {
                        // 개체가 이 구간의 오른쪽을 덮었다 — 남은 왼쪽은 「오른쪽」 정책이면 글을 받지 않는다
                        if exclusion.policy == FrameExclusionPolicy::RightSide {
                            carved.push(interval.start..interval.start);
                        } else {
                            carved.push(interval.start..left);
                        }
                    } else if right < interval.end {
                        if exclusion.policy == FrameExclusionPolicy::LeftSide {
                            carved.push(interval.end..interval.end);
                        } else {
                            carved.push(right..interval.end);
                        }
                    } else {
