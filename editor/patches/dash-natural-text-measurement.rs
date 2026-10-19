// ==== find ====
    let dash_leader = is_dash_leader_run(chars, i);
// ==== replace ====
    // [claude-hwpx dash-natural] 한/글은 하이픈 묶음도 글꼴 폭으로 둔다(사본 실험 6종). 0.3em 상한은 폭 표가 0.7em 넘게 잡힌 글꼴(Task #352 HY신명조 0.83em)만
    let dash_leader = is_dash_leader_run(chars, i) && base_width_raw > font_size * 0.7;
