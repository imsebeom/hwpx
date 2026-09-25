## 변경 요약

저장 LINE_SEG 가 없는 글자처럼 취급(TAC) 표에서 셀 글이 선언 높이보다 길어지면, 행이 늘지 않아 둘째 줄이 칸 밖으로 나가고 다음 표와 겹치던 결함(#7419)을 고칩니다. `src/renderer/height_measurer.rs` 한 파일, 두 곳입니다.

1. **TAC 비례 축소에서 생성기 표를 뺀다.** 셀 문단이 전부 NO_LS 이고 표 선언 높이(`hp:sz height`)가 행별 셀 선언(`cellSz`) 합과 같은 표는, 선언 높이가 독립된 측정이 아니라 셀 선언을 다시 적은 값입니다. 여기서 행을 줄여 합을 선언에 맞추면 layout 의 `trust_declared_row_heights` viewtext 갈래(칸 전부 NO_LS 면 선언 신뢰)가 합이 같다는 이유로 행을 셀 선언 [32, 32] 로 되돌렸습니다. 이 표는 축소하지 않아 행이 내용만큼 자랍니다(재현 [32.0, 38.5] = 한/글 재저장본). `is_native_hwp5` 문서는 종전 그대로입니다.
2. **합성 줄이 품은 중첩 표의 성장분을 더한다.** `unabsorbed_nested_tables_height` 는 문단 줄높이가 중첩 표 선언 높이 이상이면 "줄높이가 이미 담고 있다"고 보았는데, NO_LS 문단의 합성 줄은 선언 높이만 담습니다. 중첩 표가 내용으로 선언보다 자랐으면 그 차이만 더합니다(이중 계상 없음). 저장 줄은 종전대로 신뢰합니다. 표 속 표의 바깥 칸이 67.8 → 74.2px 로 안쪽 표(70.5px)를 담습니다.

## 관련 이슈

closes #7419

## 테스트

- 변경 범위: Rust (renderer 측정) + 새 integration test 원본 1개(`tests/cases/issue_7419_no_ls_tac_row_growth.rs`) + 샘플 2개(`samples/issue7419/*.hwpx`, 8KB, 생성기 산출·개인정보 없음)
- 검증한 commit SHA / 정책 비교 PR base SHA:
  - 전체 검증: `9c190efb` (base `devel@b3e3d4e2`)
  - 최신 devel 로 rebase 후 제출 HEAD `4905a31d0` (base `devel@c80a8370`). rebase 사이 devel 5커밋은 수정 파일(`height_measurer.rs`, `table_layout.rs`)을 건드리지 않았고 충돌 없음. 제출 HEAD 에서 fmt, native Clippy, 새 회귀 시험(`regression_suite_008` 에 배정), `regression_suite_021` 전체를 다시 실행
- 실행 명령·결과(모두 별도 review worktree, `--prepare` 후, Windows 11 / Rust 1.93.1):

| 검사 | 명령 | 결과 |
| --- | --- | --- |
| fmt | `cargo fmt --all -- --check` | 통과(9c190efb, 4905a31d0) |
| unit | `cargo test --lib` | 3,873 passed, 13 ignored |
| 전체 integration | `cargo nextest run --locked --cargo-profile release-test --tests --no-fail-fast` | 10,207 passed, 50 skipped (9c190efb) |
| Native Skia | `cargo test --profile release-test --features native-skia --lib` / `run-rust-test.mjs issue_2225_missing_picture_placeholder` / `render_p37_direct_pdf_export` | 3,930 passed / 2 passed / 4 passed |
| Clippy | native, `-p rhwp --lib --target wasm32-unknown-unknown`, `--workspace --all-targets` (`-D warnings`) | 셋 다 통과(9c190efb). native 는 4905a31d0 에서도 재실행 — 통과 |
| 배정 계약 | `node --test scripts/tests/rust-test-suite-manifest.test.mjs` | 통과 |
| 새 회귀 시험 | `node scripts/run-rust-test.mjs issue_7419_no_ls_tac_row_growth` | 2 passed. **수정 전 코드에서 2 failed**(h=32.0, h=67.8) 확인 |
| 제출 HEAD 재실행 | `run-rust-test.mjs issue_7419_no_ls_tac_row_growth -- --cargo-profile release-test` (rebase 후 `regression_suite_008` 에 배정) / `cargo nextest run --cargo-profile release-test --test regression_suite_021` | 2 passed / 211 passed |

- `#[cfg(test)]` 변경 없음(단위 시험 tier 검사 비해당). Studio·npm·편집 command 변경 없음.
- Visual Sweep 은 실행하지 않았습니다 — 한/글 기준 PDF 대조 대신 아래 OVR 과 수치(한/글 재저장본의 저장 geometry)로 대조했습니다.

- [x] 변경 범위별 필수 검증 수행(위 표). 제출 HEAD 는 rebase 로 SHA 가 바뀌어 전체 integration·Skia·WASM/workspace Clippy·OVR 은 부모 커밋(9c190efb)에서 수행했음을 밝힙니다
- [x] 별도 worktree 준비 후 fmt, native·WASM32·workspace all-target Clippy 통과(9c190efb)
- [x] focused·전체 integration·Native Skia 회귀 수행(9c190efb). 시각 검증은 OVR 로 갈음
- [x] 새 integration test 원본은 `tests/cases/*.rs` 에만 추가, generated 파일·manifest 미포함

## 조판 변경 근거

| 구현 주장 | 적용·비적용 경로 | 독립 기대값·실제 검사 항목 | 수정 전후 결과·증적 | 판정·남은 범위 |
| --- | --- | --- | --- | --- |
| 생성기 NO_LS TAC 표는 선언 높이로 축소하지 않는다 | 적용: hwpx·HWP 비네이티브, 셀 문단 전부 NO_LS, 표 선언 = 행별 셀 선언 합(±0.5px). 비적용: `is_native_hwp5`, 저장 LINE_SEG 가 하나라도 있는 표, 선언이 셀 합과 다른 표 | 한/글 재저장본(표 4800 → 5284HU)의 행 32.0 + 38.5px. 시험: 둘째 행 셀 사각형 ≥ 38px, 다음 표가 그 아래에서 시작 | 수정 전 32.0px(시험 실패), 수정 후 38.45px(통과) | 충족 |
| NO_LS 합성 줄의 중첩 표 성장분을 바깥 칸에 더한다 | 적용: 문단 줄높이 ≥ 중첩 표 선언 이고 그 줄이 합성(NO_LS)일 때만 성장분(측정 − 줄높이)을 더함. 비적용: 저장 줄 | 안쪽 표 측정 70.5px + 여백 → 바깥 칸 ≥ 72px | 수정 전 67.8px(실패), 수정 후 74.2px(통과) | 충족 |

- 위반된 계약과 입력: 생성기 hwpx(`hp:linesegarray` 없음, `cellSz` 한 줄 기준, `hp:sz height` = `cellSz` 합). 한/글은 열 때 재조판해 행을 키운다. 샘플은 합성 입력이다.
- 분할 변경 아님. 쪽 나눔은 여전히 TAC 표의 선언 높이를 쓴다(이 PR 범위 밖) — 선언보다 크게 자란 긴 표가 쪽 끝을 넘을 수 있다. 사용자 쪽에서는 측정한 높이를 `hp:sz` 에 적어 넘기는 방식으로 우회 중이다.

## 개체 시각 회귀(OVR)

`python tools/object_visual_regression.py --preset ovr5 <샘플 둘> -o output/ovr --diff-against devel` (9c190efb vs devel@b3e3d4e2, tol ±2px). ⚠ 이 PC 에서는 `--diff-against` 의 `git worktree add` 가 120초 제한에 걸려, review worktree 에서만 제한을 1,200초로 늘려 실행했다(PR 미포함).

### OVR 개체 무회귀 — 현재(9c190efb) vs devel@b3e3d4e2 · tol ±2px

| 샘플 | 페이지 | 개체 | 회귀 | 상세 |
|---|---|---|---|---|
| tac_two_line_cell_no_lineseg.hwpx | 1→1 | 0→0 | 0 | - |
| tac_nested_two_line_cell_no_lineseg.hwpx | 1→1 | 1→1 | 1 | obj0 page+0 w+0.0 h+6.5 |
| KTX.hwp | 27→27 | 9→9 | 0 | - |
| exam_math.hwp | 20→20 | 9→9 | 0 | - |
| 21_언어_기출_편집가능본.hwp | 15→15 | 3→3 | 0 | - |
| aift.hwp | 74→74 | 27→27 | 0 | - |
| biz_plan.hwp | 6→6 | 0→0 | 0 | - |

**합계: 회귀 1건 — 개체 이동/크기변경 검출**

프리셋 5종은 쪽수·개체 모두 불변. `tac_nested_two_line_cell_no_lineseg.hwpx` 의 h+6.5 는 이 PR 이 의도한 변화(안쪽 표 64.0 → 70.5px)다.

## 성능 영향 및 측정 결과

- 예상 영향: 영향 없음에 가깝다. ① 은 TAC 축소 분기 앞의 셀 순회 한 번, ② 는 NO_LS 합성 줄이 중첩 표를 품은 경우에만 중첩 표 측정을 한 번 더 한다.
- 재현·측정: 미측정.

---
이 PR 은 Claude Code(Anthropic)의 도움으로 원인 추적, 수정, 검증을 했습니다. 모든 수치는 위 명령으로 이 PC 에서 직접 얻은 값입니다.
