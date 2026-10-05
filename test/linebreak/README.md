# 줄 나눔 실측 도구 (2026-10-05 ~ 10-06)

한/글 2024 가 줄을 어디서 나누는지 재서 rhwp 엔진 패치의 근거로 삼은 도구와 결과다.
한/글은 `hidden_desktop.py` 로 보이지 않는 데스크톱에서 돌린다(사용자 창 포커스를 건드리지 않는다). 원본은 열지 않고 사본만 쓴다.

| 파일 | 하는 일 |
| --- | --- |
| `wl.py`, `wl_spec*.py` | 글자 폭 사다리. 한 문서에 1×1 표를 칸 폭 4 HWPUNIT 씩 바꿔 넣고, 한/글 재저장본에서 줄 수를 읽어 「한 줄에 들어가는 가장 좁은 자리」를 얻는다 |
| `wl_spec5.py`, `gen_font_patch.py` | 글꼴 파일(hmtx)의 폭으로 예상한 사다리(한컴산뜻돋움, 나눔스퀘어, 한컴 고딕 84건이 한/글과 모두 일치), 그 폭을 rhwp 폭 자료 패치 `patches/font-metrics-extra.rs` 로 만드는 생성기. `wl.py` 는 명세 옆 `.charpr.json` 에 `fonts` 가 있으면 글꼴 목록부터 늘린다 |
| `wlb.py` | 글머리표 자리 사다리(글머리 문자, 본문과의 거리, 너비 보정, 자동 내어쓰기) |
| `hwp_resave_many.py`, `hwp_resave.py`, `hwp2pdf.py`, `hwp_pages.py` | 한/글 COM: 다시 저장(쪽수를 먼저 물어야 조판된 줄 기록이 남는다), PDF, 쪽수 |
| `hres_driver.py`, `hpages_driver.py` | 대조 문서 전체를 묶음으로 재저장, 쪽수 세기 |
| `claude_lb_probe.rs` | 엔진 진단. `src/renderer/composer/line_breaking.rs` 끝에 `#[cfg(test)] #[path = "claude_lb_probe.rs"] mod claude_lb_probe;` 를 붙이고 `cargo test --lib claude_lb_probe -- --ignored --nocapture`. 환경 변수 `CLAUDE_LB_FILES`(목록), `CLAUDE_LB_VERBOSE`, `CLAUDE_LB_HEAD`, `CLAUDE_LB_ONE` + `CLAUDE_LB_KEY` |
| `resid.py`, `resid2.py`, `lbdiff.py` | 진단 로그에서 남은 차이를 원인 종류로 분류, 두 로그의 고침과 망침 비교 |
| `prep_new.mjs`, `pagemap.mjs`, `cmp3.py` | 에디터 서버와 같은 전처리 → 문단별 쪽 → 「전 엔진 / 새 엔진 / 한/글」 쪽수 비교 |
| `apply_blocks.py` | `patches/*.rs` 묶음 패치를 setup.mjs 와 같은 규칙으로 소스에 적용(시험용) |
| `font_cover.py` | 대조 문서의 글자를 글꼴별로 세어 「엔진에 폭 표 있음 / 없지만 이 PC 에 설치됨 / 설치도 안 됨」으로 나눈다. 엔진 유무는 `corpus_faces_metric.tsv`(임시 예제로 `find_metric` 을 직접 물은 결과)에서 읽는다 — 소스의 `name: "…"` 만 세면 별칭을 놓쳐 틀린다 |
| `fm_dump.mjs`, `fm_check.py` | 스킬 `editor/font-metrics.mjs` 가 글꼴 파일에서 읽은 폭 표를 JSON 으로 내고, fontTools 로 다시 읽어 글자 단위로 대조 |
| `fm_corpus.mjs`, `rt_fontdiff.py` | 대조 문서에서 엔진에 표가 없는 글꼴의 폭 표를 한 파일로(`rt_metrics.json`). `claude_lb_probe` 에 `CLAUDE_FONT_METRICS=<그 파일>` 을 주면 등록하고 잰다. 등록 전후 로그에서 그 글꼴 문단의 불일치 수 비교 |
| `rt_node.mjs`, `rt_e2e.py` | 한 문단을 다시 나누게 해(글자를 넣었다 지움) 줄 시작을 본다 — 엔진만(등록 없이, 등록 뒤), 에디터(cli) |
| `results/` | 사다리 명세와 한/글 실측 결과, 대조 문서 목록, 한/글 쪽수 |

확정한 규칙은 스킬 `editor/patches/hancom-quantum-*.rs`, `char-kinsoku.rs`, `bullet-advance.rs`, `line-spacing-quantum.rs`, `cell-trailing-ls-synth.rs`, `font-metrics-extra.rs`, `condense-pull.rs` 머리 주석에 있다.
