# 줄 나눔 실측 도구 (2026-10-05 ~ 10-06)

한/글 2024 가 줄을 어디서 나누는지 재서 rhwp 엔진 패치의 근거로 삼은 도구와 결과다.
한/글은 `hidden_desktop.py` 로 보이지 않는 데스크톱에서 돌린다(사용자 창 포커스를 건드리지 않는다). 원본은 열지 않고 사본만 쓴다.

| 파일 | 하는 일 |
| --- | --- |
| `wl.py`, `wl_spec*.py` | 글자 폭 사다리. 한 문서에 1×1 표를 칸 폭 4 HWPUNIT 씩 바꿔 넣고, 한/글 재저장본에서 줄 수를 읽어 「한 줄에 들어가는 가장 좁은 자리」를 얻는다 |
| `wlb.py` | 글머리표 자리 사다리(글머리 문자, 본문과의 거리, 너비 보정, 자동 내어쓰기) |
| `hwp_resave_many.py`, `hwp_resave.py`, `hwp2pdf.py`, `hwp_pages.py` | 한/글 COM: 다시 저장(쪽수를 먼저 물어야 조판된 줄 기록이 남는다), PDF, 쪽수 |
| `hres_driver.py`, `hpages_driver.py` | 대조 문서 전체를 묶음으로 재저장, 쪽수 세기 |
| `claude_lb_probe.rs` | 엔진 진단. `src/renderer/composer/line_breaking.rs` 끝에 `#[cfg(test)] #[path = "claude_lb_probe.rs"] mod claude_lb_probe;` 를 붙이고 `cargo test --lib claude_lb_probe -- --ignored --nocapture`. 환경 변수 `CLAUDE_LB_FILES`(목록), `CLAUDE_LB_VERBOSE`, `CLAUDE_LB_HEAD`, `CLAUDE_LB_ONE` + `CLAUDE_LB_KEY` |
| `resid.py`, `resid2.py`, `lbdiff.py` | 진단 로그에서 남은 차이를 원인 종류로 분류, 두 로그의 고침과 망침 비교 |
| `prep_new.mjs`, `pagemap.mjs`, `cmp3.py` | 에디터 서버와 같은 전처리 → 문단별 쪽 → 「전 엔진 / 새 엔진 / 한/글」 쪽수 비교 |
| `apply_blocks.py` | `patches/*.rs` 묶음 패치를 setup.mjs 와 같은 규칙으로 소스에 적용(시험용) |
| `results/` | 사다리 명세와 한/글 실측 결과, 대조 문서 목록, 한/글 쪽수 |

확정한 규칙은 스킬 `editor/patches/hancom-quantum-*.rs`, `char-kinsoku.rs`, `bullet-advance.rs`, `line-spacing-quantum.rs`, `cell-trailing-ls-synth.rs` 머리 주석에 있다.
