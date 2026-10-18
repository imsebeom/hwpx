// ==== find ====
    let mut w = before;
    for (idx, sw) in spaces {
        if w > effective_width {
            return Some(idx);
        }
// ==== replace ====
    let mut w = before;
    for (idx, sw) in spaces {
        if w > effective_width {
            // [claude-hwpx space-run-keep2] 빈칸 묶음 가운데서 꺾으면 남는 폭이 빈칸 하나보다 좁아도 앞줄에 빈칸을 적어도 둘 남긴다(e35, 정답본 약 150곳)
            let keep2 = run_start + 2;
            return if keep2 >= run_end { None } else { Some(idx.max(keep2)) };
        }
