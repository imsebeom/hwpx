# hwpx 에디터 기반 에이전트 스킬

`/hwpx` 스킬(`~/.claude/skills/hwpx`, 저장소 imsebeom/hwpx2)에 rhwp 에디터 모드를 붙이는 개발 폴더.
사용자는 브라우저의 rhwp 에디터로 문서를 보고, 터미널 Claude 가 같은 문서를 실시간으로 고친다.
**2026-09-25 스킬로 통합 완료** — 코드 원본은 이제 `~/.claude/skills/hwpx/editor/`(설명서 `references/editor-mode.md`, 시험 `editor/tests/`)이다. 이 폴더의 `editor/` 는 개발 당시 사본이고 **여기서 고치지 않는다.** `.build/`(rhwp 소스, Rust 빌드 캐시)는 이 폴더에만 있다.
- 노션: https://app.notion.com/p/3f1b9a4fc96d81799519c353c423deee (「hwpx 스킬 개발」 — 2026-10-06 사용자 결정으로 스킬 전체 범위, 2026-03-21 시작, **상태는 「관리」**(운영 중이 아니라는 사용자 지시 — 세션정리가 「진행 중」으로 바꾸지 않는다). 세션정리 2단계의 프로젝트 relation 은 여기)
- 구분: 앱 개발

## 구조
- `editor/plugin/claude-plugin.ts` — rhwp-studio 플러그인. JSON op(`doc`/`m`/`run`)를 한 트랜잭션으로 적용
- `editor/setup.mjs` — rhwp v0.8.6 받기, npm `@rhwp/core` prebuilt WASM 넣기, 플러그인 등록, 빌드 → `studio-dist/`, `sdk/`
- `editor/server.mjs` — 의존성 없는 브리지(localhost:7780). 명령 큐, long-poll, 스냅샷, 줄 diff
- `editor/host/` — 에디터를 띄우는 호스트 페이지. 1.5초 주기로 사용자 편집 감지
- `editor/cli.mjs` — Claude 용 CLI(start, run, text, outline, state, goto, inspect, slots, tools, changes, save, undo, stop)
- `editor/hwpx-zip.mjs` — 의존성 없는 zip 읽기/쓰기, 저장 단계 머리말/꼬리말 쪽 번호 보정
- `editor/plugin/lib/` — 형제 프로젝트 hwpx에디터기반AI(커밋 866416b)의 doc-tools/doc-rules/collab-ops 를 고치지 않고 복사(SOURCE.md)
- `editor/patches/hwpx-hf-autonum.rs` — rhwp hwpx 저장기 패치(쪽 번호 표식 → hp:autoNum). Rust 가 있으면 setup 이 적용해 WASM 을 직접 빌드
- `editor/EDITOR.md` — Claude 용 사용 설명서(스킬 통합 시 references 로)
- `test/roundtrip.mjs` — rhwp 로 열고 다시 저장하는 보존력 시험

## 결정
- 에디터 화면은 직접 빌드해 로컬 제공(사용자 선택). github.io 호스팅에 의존하지 않는다.
- Claude 수정은 실시간 반영(사용자 선택: hwpctrl 실시간만). hwpctrl 호환층은 `Execute` 가 파라미터셋을 안 읽고 `InsertCtrl` 이 5×5 고정이라 문서 작성에 부족 → 플러그인에 WASM `HwpDocument` 직접 호출(`doc`) 경로를 함께 둠. 둘 다 다시 열지 않고 화면에 반영, 배치=undo 1스텝.
- 사용자 편집 전달은 "말을 걸 때 읽기"(사용자 선택). `changes` 가 줄 diff + 커서 문단을 준다.
- 저장할 때마다 새 판 `<이름>_<YYMMDD>_<NN>.hwpx`(사용자 지시). 덮어쓰기 없음, 원본 보존.
- rhwp API 가 없는 작업(A 생성, F/H 양식, I 병합, J 시험지, N 메모)은 에디터 모드에서 하지 않는다 — 저장, 종료 후 기존 워크플로(사용자 선택: 실시간만 유지, Python 처리 후 재적재 안 함).
- 스킬 통합은 사용자가 실제 문서로 써 본 뒤에 한다(사용자 선택).

## 실측 (2026-09-25)
- 왕복 보존력: 실사용 hwpx 4개 + 스킬 템플릿 산출물 2개(22쪽)를 rhwp 로 열고 저장 → 한컴 쪽수 동일, 픽셀 차이 0%, 필드(메모) 표 그림 개수 동일.
- hwp→hwpx(rhwp): 공문 2건 중 1건 0%, 1건 표 셀 한 곳 줄 간격 차이(0.4%).
- 라이브 편집 실측 통과: insertText, replaceAll(표 셀 포함), applyCharFormat(bold, fontSize 1600=16pt, textColor), splitParagraph, pasteHtml(첫 블록은 대상 문단에 이어 붙음, 목록은 글머리표 문단), undo(배치 통째로).
- 사용자 타이핑 → 입력이 멈춘 뒤 1건으로 기록, 커서 문단 포함. 저장본은 verify_hwpx 통과, 한컴에서 정상 열림.
- rhwp 에 없는 것: 메모 생성, 문서 병합(InsertFile), 꼬리말 쪽 번호(insertFieldInHf 는 hwpx 저장 시 필드가 빠짐 — rhwp 에 보고할 만한 결함).
- KS X 6101 반영(2026-09-25): start 가 전자서명(§16), 암호화(§15) 문서를 거절(--force), run 이 문자열을 NFC 정규화(§5.3), EDITOR.md 에 요청→명령 사전(한컴 렌더 실측: repeatHeader, 캡션, pageBreakBefore, 수식, 머리말 글).

## 함정
- **Node 24.11 `fs.rmSync`/`fs.cpSync`(recursive)는 한글 경로에서 node 를 소리 없이 죽인다**(종료 코드 127). vite 가 outDir 를 비울 때도 같다. setup.mjs 는 자체 rmrf/copyDir 를 쓰고 빌드 전에 dist 를 지운다.
- Claude Code 의 작업 디렉터리가 폴더 안에 잡혀 있으면 그 폴더를 옮기거나 이름을 바꿀 수 없다.
- StreamDocs(standard.go.kr) 링크는 밖에서 열면 "문서를 열 수 없습니다" — 세션에 묶여 있다.
- 🔴 **스킬 파이프라인 산출물은 rhwp 에서 문단이 한 줄로 눌려 그려진다**(2026-09-25 생각쓰기캠프 문항 3에서 사용자 발견).
  `hwpx_helpers.LINESEG_DUMMY`(와 `exam_builder._lineseg`)가 polaris-dvc 호환용으로 **모든 문단에 한 줄짜리 lineseg 캐시**를 박는데,
  한글은 열 때 다시 계산하고 rhwp 는 캐시를 믿는다. `reflowLinesegs()` 는 캐시가 비었거나 높이 0인 문단만 고쳐 이 더미에는 0건이다.
  **처방: `server.mjs` `/api/doc` 이 보내기 전에 `hwpx-zip.mjs stripDummyLinesegs()` 로 더미 문자열과 정확히 같은 것만 걷어낸다**(원본 파일은 그대로).
  캐시가 없으면 rhwp 가 스스로 계산한다 — 문항 3에서 성취기준, 평가 요소가 두 줄로 바뀌고 쪽수 6쪽(한글 PDF와 같음) 확인.
  ⚠ 9/25 왕복 시험의 「스킬 템플릿 산출물 픽셀 차이 0%」는 **한글로 렌더해 잰 것**이라 rhwp 화면의 이 결함을 잡지 못했다
- 🔴 **스킬 산출물의 표가 rhwp 에서 아래 표와 겹쳤다 — 한글 줄 배치를 옮겨 심어 해결**(2026-09-25, 같은 문항 3, 스킬 커밋 042a754).
  - 원인: 산출물은 칸 높이를 한 줄 기준으로 적는다. 더미 줄 배치를 걷으면 rhwp 가 스스로 줄을 나누는데, **잰 줄 수가 그리는 줄 수보다 하나 적어** 행이 덜 늘고 다음 표가 위로 올라온다. rhwp v0.8.6 과 devel(1,541커밋 뒤, `~/.cache/rhwp-devel` 빌드) 모두 같다
  - **한글 재저장본은 rhwp 에서 정확히 그려진다.** 한글이 바꾸는 것은 줄 배치와 **표 `sz height`(4862 → 5573)** 둘이고 `cellSz` 는 그대로다. 둘 다 옮겨 심어야 한다 — 줄 배치만 옮기면 여전히 겹친다
  - 처방: `editor/hancom_layout.py` 가 사본을 한글로 열어 저장하고 **문단끼리 짝지어** 줄 배치를, 표끼리 짝지어 `sz height` 를 원본에 옮긴다(원본은 문단 203개 중 3개에 줄 배치가 없어 순서대로 옮기면 한 칸씩 밀린다). 결과가 한글 재저장본과 **6쪽 3,478자 좌표까지 같다**. 재저장본을 통째로 쓰지 않는 것은 그림이 BMP 로 부풀기 때문이다(104KB 유지)
  - 🔴 **한글 COM 은 `PageCount` 를 묻지 않고 `SaveAs` 하면 조판 전 줄 배치(더미)를 그대로 저장한다.** 스크립트가 쪽수를 먼저 읽고, 저장본에 더미가 남으면 실패로 처리한다
  - 🔴 **앱 창이 둘 떠서 측정이 뒤섞였다.** `stop` 이 서버만 내려 옛 창이 새 서버에 다시 붙고 `start` 가 창을 또 열었다. 두 창이 명령을 나눠 받아 같은 칸이 41.9px/36.5px 로 나오고 SVG 와 셀 상자가 어긋났다 — **그 사이의 「한글 재저장본도 겹친다」, 「측정이 글꼴 로딩 때문에 흔들린다」는 이 때문에 나온 잘못된 결론이었다.** 이제 cli 가 앱 창 pid 를 기록해 창을 하나만 쓴다
  - 원인이 아닌 것(변형 시험): 문단 id 2147483648, 셀 세로 정렬, hasMargin, 자간 -7%.
    ⚠ 「treatAsChar 도 아니다」는 창 둘일 때 잰 틀린 결론이었다 — 최소 재현으로 **`treatAsChar="1"` 이 원인 조건**임이 드러났다(#7419)
  - 도구: `~/.cache/rhwp-devel/cmp.mjs`(2쪽 글자 줄과 셀 상자), `allpages.mjs <pkg> <a> <b>`(전 쪽 글자 좌표 대조), `variants.py`, `winshot.py`(에디터 창을 앞으로 올리지 않고 PrintWindow 로 캡처 — 사용자 화면을 뺏지 않는다)

## 컨텍스트 앵커
- **10-17 셋째**: 사용자 「ktx 문항 내용 표 크기 자동 조절 안 된 이유」(자료 1 칸의 3행 표가 0행만 보임) → 스킬 efada63(엔진 패치 4개, **릴리스, 푸시 안 함**, 로컬 `setup.mjs --build`)
  - 원인: 안쪽 표 sz 1560(내용 9000), 바깥 T3 28680. 한/글 재저장 36121/9000. rhwp 는 ① `tac-row-ladder` 가 합성 줄(0x80000000)을 저장 줄로 보고 칸 높이를 글 높이로 되돌림 ② `tac-no-ls-shrink` 가 「적힌 높이 = 칸 합」만 면제해 T3 를 비례 축소 ③ `tac-no-ls-nested` 자란 몫에 바깥 여백 누락 ④ 세로 가운데 정렬 내용 높이에 자란 몫 누락(새 `cell-tac-nested-valign`)
  - 1560 은 10-13 판부터 `rhwp_layout.mjs` 가 같은 엔진 결함으로 잰 값(높이 0 으로 재도 바깥 칸이 안 늘어 0행만 잡힘). 새 엔진으로는 36120/9000
  - 회귀: 354개 중 34개 변경, 쪽수 동일, 결정적. 한/글 대조(scratchpad `ktx3/moved.py`, 남지 않음)의 「악화」는 직전도 깨진 문서(전지직렬, 조상들의불 — 칸 그림 표가 안 커져 출처와 겹침, 별개 결함)와 쪽 나누기 차이 착시. 계절원인 계열은 겹침이 사라짐. `cargo test --lib` 3889
  - 사용자 질문 「문항3 채점요소 사이 선만 굵다」 → 문서 설정(ⓐ 칸 bf26 만 아래 0.4mm, 옆 칸 bf5/bf13 은 0.12mm). 한/글 PDF 도 같음
  - 사용자 질문 「편집기록, 작업기록이 디버깅에 충분한가」 → 부족한 점 보고(아래 next_steps ③)
  - 사용자 「그래」(로그 보강) + 다른 세션이 「표 속 표를 지울 방법이 없다」며 멈춘 기록 → 스킬 37f6ca3(엔진 패치 `cell-table-delete` + `delete_table` 이 `T3r1c0/T1` 받기), 392530a(작업 기록: 불러옴에 엔진 지문과 바뀐 표 높이 `T3/칸1/T1 3×2 1560 → 9000`, run 에 op 와 결과, 빌드 단계는 `~/.claude/cache/hwpx-editor/build-log.jsonl`). **릴리스, 푸시 안 함**, 로컬 `setup.mjs --build` 끝남
  - 시험: 화면 없는 브라우저로 KTX 사본 — 지우기 전 바깥 칸 379.4 → 278.3px, 그림 지우기 212.1px, 틀린 번호 거절, 기록 줄 확인. `cargo test --lib` 3889
  - 🔑 시험 함정: `hold.py`(화면 없는 페이지)가 남아 있으면 같은 포트의 새 서버에 다시 붙어 명령을 받는다(지운 문서로 재 「222px, 칸 문단 1개」로 오진할 뻔). 매번 `hold.py` 프로세스를 끄고 시작
  - 사용자 「릴리스 하고 푸시하라」 → 릴리스 **editor-899decdab577**(hwpx, hwpx2 각 17.4MB, 옛 editor-2136cd34482a 정리) → 9726de5 까지 hwpx, hwpx2 푸시(830a0f4 다시 열기 문턱 포함)
  - next_steps: ① 떠 있는 창(KTX, 문항 3, 문항 4)은 옛 엔진, 옛 서버 — 저장 후 `stop`, `start` 로 다시 열어 확인 ② 별개 결함: 칸 안 그림 표(전지직렬, 조상들의불 구버전)가 안 커져 출처와 겹침
- **10-17 둘째**: 사용자 「에디터가 켜져 있어도 에디터에서 고치지 않고 리빌드해 새로 띄우는 경향」 → 스킬 830a0f4(**푸시 안 함**, cli.mjs 는 저장소 파일이라 릴리스 대상 아님)
  - 원인: 10-05 규칙(「열린 문서는 run 으로」)이 SKILL.md 에디터 절 한 줄과 editor-mode.md 에만 있고, 먼저 읽히는 결정 트리는 맨 위가 「마지막 단계는 언제나 에디터로 열기」, 갈래는 「HWPX 수정 → 워크플로 C」였다. `start` 는 저장 안 한 편집만 없으면 아무 말 없이 새 판으로 바꿔 열었다
  - 처방: `start` 가 이 인스턴스 창에 같은 파일이나 `_YYMMDD_NN` 만 다른 판이 떠 있으면 멈추고 run 을 안내(`--force` 로도 못 넘음, `--reopen` 만). 결정 트리 맨 위에 「에디터에 떠 있으면 run」, 「마지막 단계」에서 열린 문서 제외
  - 시험: `--no-browser` 서버 + 헤드리스 playwright 페이지로 같은 파일, 다른 판, --force 멈춤 / --reopen, 다른 문서 열림 5경우 통과
  - next_steps: 실사용에서 또 다시 빌드로 가는지 지켜본다. 다른 이름으로 다시 빌드해(`_v2` 등) 문턱을 피하는 일이 나오면 열린 문서와 내용 유사도로 넓힌다
- **10-17**: 사용자 「에디터 ktx 에 글자 겹침은 문서 설정인가 에디터 오류인가」(KTX 문항 `_261017_01`, 6쪽 「◎ 문항 4 _수행특성과 예시 답안」이 위 채점표 아래 괘선을 덮음) → 에디터 오류. 스킬 625e258(엔진 패치 `empty-float-offset-flow`, `-typeset`, **릴리스, 푸시 안 함**)
  - 원인: 빈 문단의 위아래 배치 블록 표(vertRelTo=PARA, 오프셋 893, 바깥 여백 141)는 rhwp 가 오프셋만큼 내려 그리는데, 빈 앵커 흐름 규칙(layout.rs `lane_flow_bottom`, typeset `empty_host_physical_extras_hu`)은 표 높이만 전진한다. 여분(오프셋 + 위 여백 + 아래 여백)은 #5870 이 저장 줄 배치가 물리 공식과 맞을 때만 더해, 줄 배치 없는 스킬 산출물에서 다음 문단이 15.7px 위로 올라왔다. 한/글 재저장본은 rhwp 에서도 맞았다
  - 근거: 한/글 재저장본 표 8개(KTX, 교과 평가계획, 문예복지부)에서 다음 문단 vpos 차이 = 오프셋 + 위 여백 + 표 높이 + 아래 여백, HWPUNIT 까지 일치
  - 처방: 저장 줄 배치가 없고 표가 하나인 빈 문단만 여분을 더한다(layout, typeset 대칭). KTX 제목 기준선 807.9 → 823.6px, 다음 표 위 852.5px(한/글 재저장본 rhwp 렌더와 같음)
  - 회귀: `reg_corpus_1014.txt` 354개 1,990쪽 SVG 해시 — 바뀐 것 11개, 쪽수 모두 같음(두 번 결정적). 한/글 PDF 줄 대조 도구는 세션 scratchpad `ktx/cmp.py`, `detail.py`(남지 않음). `cargo test --lib` 3889 통과
  - ❌ 남은 기존 오차 둘(이번 변경과 무관): ① rhwp 가 블록 표를 바깥 위 여백 없이 그려 표가 그만큼(1.9~3.8px) 높다 ② 교과 평가계획(5학년) 2쪽 두 표 사이 제목 구간이 한/글보다 8px 크다 — 옛 엔진에서는 빠진 여분 12.5px 와 우연히 상쇄돼 맞아 보였고 지금은 다음 표가 4.6px 낮다
  - 새 창(인스턴스 ktx2)으로 열어 사용자가 「해결되었군」 확인 → 릴리스 **editor-455cce1eab08**(옛 editor-276d53ac6e56 정리) → 1a87197 까지 hwpx, hwpx2 푸시(다른 세션의 785b7ee, a77260c 포함)
  - 사용자 「해결해」(남은 오차 ①②) → 스킬 2dabd9c(엔진 패치 `empty-float-outer-top`, `empty-float-offset-gap`, **릴리스, 푸시 안 함**)
    - ① 빈 문단 표 위치(`empty_host_float_raw_top` 의 `fragment_outer_top_px`)에 줄 배치 없는 문단만 바깥 위 여백을 싣는다(#6378 은 저장 사다리 문서 근거라 그대로)
    - ② 「8px 큰 제목 칸」은 오진이었다: 실제는 첫 표 문단(p15) 뒤 표-표 줄 간격(#1133, 다음도 빈 문단 표일 때 보존) 600HU 가 우리 여분 위에 또 붙은 것. 한/글 재저장본 p15 → p16 차이 23724 = 375+283+22783+283(줄 간격 없음). 줄 배치 없는 표 하나 문단은 이 간격을 뺀다
    - 결과: 교과 평가계획 1~3쪽 괘선 한/글 PDF 와 1px 안(옛 3.9~8px). KTX 표 위 286.9px(한/글 286.5)
    - 회귀: 직전 릴리스 대비 354개 중 16개 변경, 쪽수 동일, 두 번 결정적. 16개 한/글 괘선 대조(scratchpad `ktx/cmp2.py`) — 1px 넘는 괘선 수가 늘어난 문서 없음, 10개 줄어듦. `cargo test --lib` 3889 통과
  - ❌ 새로 본 기존 오차(이번 변경과 무관): 교과 평가계획 5쪽 표 첫 행이 한/글보다 8.6px 크다(4, 6~8쪽도 비슷한 칸 높이 오차), linetest2 1쪽 끝 나뉜 표 조각 끝이 24px 짧다
  - 사용자 「추가 수정」 → 스킬 bb57e29(엔진 패치 4개, **릴리스, 푸시 안 함**). 교과 평가계획 칸 높이 오차의 원인은 넷이었다
    - `cell-squeeze-one-line`: 「한 줄로 입력」(subList lineWrap=SQUEEZE) 칸을 문서를 열 때 칸 폭으로 나눠 「평가/영역」 두 줄(5쪽 머리 행 26.6 → 18.2px). 그리기 쪽 가로 축소(transform scale)는 rhwp 가 이미 한다. 넓은 상자로 다시 나눈 한 줄을 **저장 줄로 표시**해야 그릴 때 다시 안 나뉜다(합성 표시면 `recompose_cell_lines_in_frame` 이 다시 나눔)
    - `hangul-word-char-widths`: 칸보다 긴 한글 어절의 글자 단위 나눔이 글자별 폭이 비어 「max(글자 크기, 12px)」로 어림 → 8pt 장평 90% 자간 -15% 「노력요함」이 「노/력/요/함」(6쪽). 늘 `measure_char_width` 로 잰다
    - `tac-synthetic-full-spacing`: 계산된 줄 하나뿐인 문단의 글자처럼 취급 표 뒤에 줄 간격 절반만 더하던 규칙(`current_owned_row_covers_object`, 근거 시험 없음, 대형 병합 커밋 유래)을 끔. 한/글 재저장본 줄 24158 + 600 = 다음 vpos
    - `partial-float-outer-top`: 쪽에 걸친 표 첫 조각과 이어진 조각 맨 위에 바깥 위 여백(7쪽 2.9px, 8쪽 3.3px)
    - 결과: 교과 평가계획 1~7쪽 괘선 한/글과 1.2px 안. 회귀: 직전 대비 354개 중 47개 변경, 쪽수 동일, 두 번 결정적, 한/글 대조 46개 중 개선 27, 같음 17, +1 둘(e2e2, 2-3 원고 — 원래 대부분 어긋난 문서라 지표 잡음). `cargo test --lib` 3889 통과
    - 🔑 함정: SVG 글자는 `<text x= y=>` 말고 `<text transform="translate(x,y) scale(..)">`(SQUEEZE, 장평) 형태도 있다 — 정규식이 놓쳐 「글자가 안 그려진다」로 오진할 뻔했다. `document.rs` 는 LF, `layout.rs` 등은 CRLF
  - ❌ 남은 것(일반 rhwp 동작, 줄 배치가 있는 문서에도 걸림): ① 쪽 끝에서 잘린 행을 한/글은 본문 끝까지 늘려 그리고 글을 그 안에서 정렬한다(linetest2 1쪽 22px, 한/글 재저장본도 rhwp 26px 어긋남). 쪽 나누기 규칙(#3820 Stage 76 `end_row_height_override` 등)과 얽혀 있다 ② 이어진 조각 첫 행(잘린 행의 나머지)에 칸 위 여백이 빠진다(교과 평가계획 8쪽 3.7px) ③ 단보다 넓은 표의 가로 위치: 한/글은 p21, p28 을 단 가운데(양쪽으로 넘침, 56px), p15~17 은 단 왼쪽(79px)에 두는데 rhwp 는 76/79px. 구분 조건 미확인
  - 사용자 「이어하자」(남은 셋) → 스킬 e5e9037(엔진 패치 4개, **릴리스, 푸시 안 함**)
    - ② `cut-row-pad`: 잘린 행 나머지 높이(`row_cut_content_height`)가 #501 축소 여백(566 칸에 283×2 → 1.9)을 썼다. 내용이 선언을 넘으면 원래 여백. ⚠ 처음엔 범위 없이 넣었다가 `cargo test` 3개(#3820 p106 표 29, issue2214, issue1949 큰 칸) 실패 — 이 값이 쪽 나누기에도 쓰여 저장 문서 나눔이 바뀐다. **칸 문단이 모두 저장 줄 배치 없음일 때만**으로 좁혀 통과
    - ③ `wide-table-column-center(-float)`: 한/글은 단 기준 가운데 표가 단보다 넓으면 단 가운데(음수 여유)로 둔다. 비 TAC 6개 모두 56.1px. 앞서 「p15~17 은 79px」은 쪽을 잘못 짝지은 오판이었다(79px 은 TAC 표)
    - ① `rspan-fragment-fill`: 한/글은 병합 칸이 다음 쪽까지 이어지고 조각이 행 경계에서 끝나면 마지막 행을 「본문 끝 − 바깥 아래 여백」까지 빈칸으로 늘린다(그리기만). ❌ 첫 시도(Stage 76 의 25px 빈 꼬리 조건을 HWPX 에서 끄기)는 3행 내용을 1쪽에 남겨 2쪽이 15px 올라가 되돌렸다 — 한/글은 2쪽에 3행을 통째로 다시 그린다
    - 결과: 교과 평가계획 8쪽 3.7 → 0.5px, 가로 위치 전 쪽 일치, linetest2 1쪽 22.3 → 2.6px(한/글 재저장본 26.5 → 3.5). 회귀 354개 중 33개 변경, 쪽수 동일, 한/글 대조 어긋난 괘선 수 늘어난 문서 0(최대 오차가 커진 몇 문서는 한/글과 쪽 배치가 원래 다른 문서). `cargo test --lib` 3889
    - 🔑 함정: Bash `sed` 로 백슬래시 경로를 바꾸다 apply.py 를 깨뜨림(글로벌 규칙 그대로) — Write 로 다시 씀. `cd` 뒤 상대 경로 `rm` 은 안전 검사가 명령 전체를 막는다 → 새 출력 폴더를 만든다
  - ❌ 남은 것: 교과 평가계획 7쪽 첫 조각 끝(글줄 사이에서 잘린 병합 묶음) 한/글 1030.1, rhwp 1032.4(2.3px) — 한/글의 잘린 앞부분 높이 규칙 미확인
  - 사용자 「왜 문단을 못 지운다고 할까」(다른 세션이 [자료 2] 그림 아래 빈 줄을 「칸 안 문단을 지우는 도구가 없다」며 Backspace 를 부탁) → 이름 붙은 도구 `delete_paragraphs` 가 본문 문단만 받고 설명서가 칸 메서드(`deleteRangeInCellByPath`, `mergeParagraphInCell`)를 안 적어 `doc` 경로를 못 찾은 것. 사용자 「재발 막기 해라」 → 스킬 02556da: 플러그인 도구 `delete_cell_paragraphs`(cell, from_para~to_para 또는 only_empty, 번호 없으면 칸 문단 목록, 그림/표 문단 거절, 문단 하나 남김 — 칸 그림 문단은 글 길이 0 이라 개체를 따로 본다) + editor-mode.md(도구 설명, 칸 메서드 표 행, 「손 편집 넘기기 전에 doc 경로 확인」). 화면 없는 브라우저 시험 6경우 통과. **릴리스 전이라 미리 빌드한 에디터를 받는 사람에게는 아직 없다**
  - 사용자 「릴리스하고 푸시하라」 → 릴리스 **editor-ee6778d45cbe**(hwpx, hwpx2, 옛 editor-f4128e4ff7a5 정리) → 56acbcc 까지 hwpx, hwpx2 푸시
  - next_steps: ① 교과 평가계획 7쪽 2.3px
- **10-15**: 사용자 「cd8fe559 에디터는 큰 덩어리의 글자취급 표 등으로 에디터와 한/컴에서 순서가 달라진다」(CORE 실적 새틀 `_261015_02`, 한/글 4쪽, 에디터 6쪽) → 스킬 151352f(엔진 패치 `oversized-tac-table`)
  - 원인: p0 한 문단에 TAC 표 셋(T1~T3, `flowWithText="0"`, 모두 쪽 본문 876.8px보다 큼), p1 에 T4. rhwp 는 HWPX 에서 `treatAsChar && flowWithText`(#3930)만 TAC 로 보고, 예외로 첫 줄(`tac_table_line_index == Some(0)`) 표만 TAC 로 인정 → T2, T3, T4 는 블록 표로 쪽이 나뉘고, `typeset_table_paragraph` 정렬 키 `table_flow_tiebreak` 가 블록 표를 앞세워 T2 → T3 → T1 순서
  - 처방: `is_effective_tac_table` 에 「쪽 본문보다 큰 글자처럼 취급 표」 추가(엔진에 구역 본문 높이 `body_height_px` 칸). #3930 근거 편람의 fwt0 TAC 표 5개는 모두 쪽 안에 든다. 6쪽 → 4쪽, 순서와 글자 세로 범위 한/글 PDF 와 맞음
  - 회귀: `reg_corpus_1014.txt` 354개 SVG 해시 동일(두 번 결정적), 편람 hwpx 383쪽, hwp 384쪽 동일, `cargo test --lib` 3889 통과. ⚠ `tests/issue_3930_hwpx_hwp_save_layout.rs` 는 Cargo.toml(autotests=false)에 연결되어 있지 않아 돌지 않는다
  - next_steps: ① (끝남: 사용자가 창을 닫은 뒤 cd8fe559 로 다시 열어 4쪽 확인) ② (끝남: 세션정리에서 릴리스 **editor-2136cd34482a**(옛 editor-d37819d8e1f9 정리) → 84038bb 까지 hwpx, hwpx2 푸시. 첫 시도는 gh 토큰 무효로 401 — `gh auth login -h github.com -p https -w` 를 백그라운드로 돌려 로그 파일에서 기기 코드를 읽어 사용자에게 건넸다)
- **10-14 둘째**: 사용자 「훅이 빈 문서만 열게 되니 의미가 없다. 훅을 빼든지 대화 맥락의 문서를 열든지」 → 훅 `hwpx-editor-open.py` 수정: 파일 이름이 없으면 열지 않고 모델에 넘김(모델이 맥락의 문서를 연다), 빈 문서는 「새/빈 문서」라고 할 때만. 분류 시험 9건 통과. 이어서 사용자 「그냥 훅 빼라」 → settings.json 등록을 빼고 스크립트와 표식 폴더(`~/.claude/cache/hwpx-editor/hook-opened-*`)를 지웠다. 이제 「에디터 열어」는 모델이 맥락의 문서를 연다(글로벌 CLAUDE.md 한 줄 갱신). 10-10 블록의 훅 관련 next_steps ②는 폐기
- **10-14**: 사용자 「전보유예 희망서가 왜 이렇게 보이나, 내가 넣은 건가」(표 둘이 본문과 겹침) → 스킬 b61c7fb(엔진 패치 `tac-overlay-flow`)
  - 원인: 교육청 서식 표 둘이 처음부터 treatAsChar="1" + BEHIND_TEXT(사용자가 넣은 것 아님). `/hwpx` 채우기가 줄 배치를 걷어(원본 46 → 0) rhwp 가 직접 조판하는데, `table_layout.rs` 가 글 뒤로/글 앞으로 표는 글자처럼 취급이어도 흐름을 전진시키지 않는다. 저장 줄 배치가 있으면 `layout.rs` overlay_tac 보정이 그 줄 높이로 전진시켜 가려져 있었다. 한/글 PDF 는 정상
  - 처방: `layout.rs` 에서 TAC + 글 뒤로/글 앞으로 + 저장 줄 배치 없음 + 표 끝 == 시작일 때만 표 높이만큼 전진. 줄 기준선 12곳이 한/글 PDF 와 0.2px 안
  - 회귀: 새 코퍼스(바탕화면 code 의 hwpx 1,953개 중복 제외에서 TAC 글 뒤로 표 문서 4 + 무작위 250, hwp 100) 354개 2,110쪽 SVG 해시 — 바뀐 것은 대상 문서 하나. ⚠ 옛 `reg_corpus.txt` 317개는 세션 임시 폴더를 가리켜 14개만 남았다 → 새 목록 `test/linebreak/results/reg_corpus_1014.txt`(바탕화면 경로라 지워지지 않는다. 쓰는 법: `node test/linebreak/svghash.mjs <pkg폴더> <목록> <출력.json>` 을 직전, 새 엔진으로 두 번 돌려 비교). 앞으로 코퍼스에 임시 폴더 경로를 넣지 않는다
  - 사용자 「푸시, 스킬 받은 사람들에게 업데이트 알림 방법 없나 — 앞으로부터라도」 → 스킬 f25b072 `scripts/check_update.py`(하루 한 번 ls-remote, 다르면 fetch 해 받지 않은 커밋 제목과 에디터 변경 여부 출력, 캐시 `~/.cache/hwpx-skill/update-check.json`) + SKILL.md 「새 버전 확인」 절(대화에서 처음 한 번 실행, 출력 있으면 알리고 받을지 묻기) + README. 릴리스 **editor-f4128e4ff7a5**(옛 editor-a41aab5691fe 정리) → 0ea4f16 까지 hwpx, hwpx2 푸시. 뒤처진 사본에서 알림 4건 → pull → setup 3.2초 → 알림 없음 확인
  - decisions: 알림은 스킬 안에서 확인하는 방식(사용자 연락처가 없어 밀어 보낼 수단이 없다). ⚠ 이 장치가 없는 옛 사본을 가진 사람은 한 번은 직접 pull 해야 그 뒤부터 알림을 받는다
  - next_steps: 실제 에디터 창(9422a794)에서 겹침 해소 확인함. 옛 창(85068ab8)은 이전 번들이라 닫고 다시 열어야 반영
- **10-11**: 사용자 「guid3 에디터에 왜 셀에 글자가 잘렸나. 5쪽」(가이드북 2-3, 「참고: 디지털 포용」 1×1 큰 표 T13) → 스킬 beabfee(**푸시 안 함**)
  - 원인은 엔진이 아니라 `rhwp_layout.mjs`: 모든 표를 높이 0 으로 두고 한 번에 재서, 칸 안의 머리표(글자처럼 취급)가 바깥 칸 줄 높이에 0 으로 들어갔다 → 바깥 표가 614.4px(46080)로 적히고 TAC 축소 규칙이 627px 내용을 눌러 마지막 줄이 칸 밖으로
  - 처방: 표마다 안쪽 표 깊이를 매기고 깊이 순서로 다시 잰다(단계 j 는 깊이 j 이상만 0). 627.0px(47025), 7쪽 그대로. 보정을 거친 실제 문서 62개 대조에서 바뀐 표는 이것 하나
  - 사용자 「그래」 → guide3 를 `_261011_02.hwpx` 로 저장하고 다시 열었다(포트 7780, load layout rhwp, T13 627.0px)
  - 사용자 「6쪽 중간에서 7쪽으로 왜 넘어갔나」 → 절 제목 앞 빈 문단의 쪽 나누기(pageBreak="1"). `261002_06` 에는 없고 `_07`(10-05 18:31 다시 쓰임)부터 있다 — 넣은 주체는 찾다가 사용자가 멈춤, 오류 아님
  - 사용자 「표 마지막 칸 → 는 표 오른쪽, 첫 칸 ← 는 표 왼쪽, 반대도 들어가기, 한/글처럼」 → 스킬 feed1d1(스튜디오 패치 `patches/table-arrow-edge.ts`, cursor.ts, WASM 그대로, **릴리스 안 함**)
    - 종전: 엔진은 본문 표를 글자 한 칸으로 건너뛰고, 마지막 칸 → 는 다음 문단 처음, 첫 칸 ← 는 표 문단 0번. 표 앞뒤 캐럿(엔진 좌표)은 테두리와 겹친 12px 막대라 안 보였다
    - 처방: 표 앞 캐럿 칸은 `convertCaretOffset` 모드 7(컨트롤 번호 → 그 개체 앞 캐럿 칸), 표 판정은 `getTableDimensionsByPath`, 첫/끝 칸은 `cellCount`. 표 앞뒤 캐럿은 칸 상자 합집합 바깥 2px 에 표 높이. Shift 선택 중은 종전(표를 글자로 고름), Tab 은 종전(마지막 칸에서 줄 추가)
    - 시험: 화면 없는 playwright 로 사본 인스턴스(arrowtest)에 키 — 본문 1×1(T13), 2×2(T14), 표 속 표(T13 머리표) 들어가기/나오기 모두 통과. 도구는 세션 scratchpad `g3/at/arrow.py <포트> <cases.json>`(남지 않음)
    - (릴리스, 푸시는 아래 세션정리에서 끝남)
  - 사용자 「표 앞에 텍스트 하나를 입력했는데 표가 아래로 지나치게 이동」(udlB, 2-9 읽을거리 — 문서 전체가 큰 표 T1 한 칸, 칸 문단 9 의 그림 표 앞) → 스킬 a2b42a7(엔진 패치 `cell-tac-table-line`, **릴리스 안 함**)
    - 원인: 쪽에 걸친 칸은 `table_partial.rs` 로 그리는데, 글 있는 문단의 칸 안 표를 글 줄을 다 그린 뒤의 `para_y` 에 놓았다. 그 줄 높이가 이미 표 높이라 표가 제 줄 아래로 한 번 더 내려갔다. `table_layout.rs`(쪽 안 나뉜 칸)는 표 줄 vpos 로 놓아 맞다
    - 처방: 표 띠와 높이가 맞는 줄(없으면 마지막 줄) vpos + 바깥 위 여백, 표의 첫 조각일 때만(`mixed_nested_split` 이 start_row 0, 오프셋 0). 표 뒤 `para_y` 는 글 줄 끝과 max
    - 한/글 대조(`hwp2pdf.py` 를 `hidden_desktop`): 앞 글 5자, 60자 → 글 줄 보통 높이, 표 다음 줄, 캡션 y 1px 안. ❌ 1자(넘침 6px)는 한/글이 같은 줄(글자는 표 왼쪽 아래 기준선)에 두는데 rhwp 는 조판 줄이 `[빈 줄(표), "x"]` 로 나뉘어 글자가 표 아래 줄 — 한 줄(22px) 길다. 저장 줄 배치는 한 줄이라 칸 줄 다시 짜기(`composer.rs` `recompose_horizontal_cell_lines_for_width`) 쪽
    - 회귀: 문서 367개 2,145쪽 SVG 해시 직전 엔진과 동일(`reg_corpus.txt` + 보정 문서 62개)
    - 🔑 rhwp `exportHwpx` 의 zip 은 header.xml CRC 가 틀려 파이썬 zipfile 이 거부한다(한/글은 연다) — 변형은 `hwpx-zip.mjs` 로 만든다. 네이티브 진단은 `cargo build --bin rhwp`(1분, `target/debug/rhwp.exe export-svg`)
  - 사용자 「표 안에서 셀선택 상태가 아닌데도 p 를 누르면 표/셀 속성 메뉴가 열린다」 → 스킬 0bb34ae. da9eadc 가 도구 모음 「개체 속성」을 칸 안에서 쓰려고 `format:object-properties` 실행 조건을 `inTable` 로 넓혔는데 맨 글쇠 P 도 그 명령이라 칸에서 p 가 글자로 안 들어갔다. 처리 중인 키(`window.event`)가 수식키 없는 P 면 넓히지 않음. 칸 커서 p 입력, F5 중 P 대화상자, 도구 모음 단추 셋 다 시험 통과
  - 세션정리 「푸시」 → pre-push 훅(원본 지문 ≠ prebuilt.json)에 막혀 `release.mjs` 로 릴리스 **editor-276d53ac6e56**(hwpx, hwpx2, 옛 editor-f9dd411d4321 정리) → 72b7362 까지 두 원격 푸시
  - next_steps(10-11 이후): ① 1자 앞 글 + 넓은 표를 한/글처럼 같은 줄에(칸 줄 다시 짜기 `composer.rs` 가 `[빈 줄(표), "x"]` 로 나누는 까닭부터. 재현은 udlB 사본 칸 문단 9 앞에 1자, 한/글 대조는 `test/linebreak/hwp2pdf.py` 를 `hidden_desktop.py` 로) ② 에디터 창 다시 열어 화살표 드나들기, p 입력이 실제 창에서도 되는지 사용자 확인
  - 사용자 「푸시」 → hwpx, hwpx2 에 beabfee 까지 푸시(10-08 의 75b115c, 9e2cba6 과 다른 세션의 b4b3013, 436eda1, bd04758 포함). `rhwp_layout.mjs` 는 저장소 파일이라 릴리스 대상 아님
- **10-10**: 사용자 「에디터 열 때마다 너무 오래 걸린다」 → 시작 시간 실측 후 UserPromptSubmit 훅 `~/.claude/scripts/hwpx-editor-open.py`(settings.json 등록, scripts와 settings.json은 `~/.claude` 저장소에서 gitignore라 커밋되지 않음. 글로벌 CLAUDE.md 한 줄은 6fd3b14)
  - 실측: 서버 기동→응답 0.2초(빈 node 0.08초), 앱 창(pywebview, WebView2, 화면 38MB) 약 2.1초, 그리기 0.8초 → 처음 열기 3.5초, 떠 있는 창 재사용 0.7초. editor-log 336건 중앙값: 일반 문서(`stored`) 3.4초, 스킬 산출물(`rhwp`) 7.4초(서버 표 높이 재기 첫 회 0.5초 + 그리기 2초). `pruneStale` 0.2초. **느림의 대부분은 모델 턴이었다**
  - 훅: 여는 말뿐인 프롬프트(「에디터 열어」, `"x.hwpx" 에디터로 열어`)는 열고 block(모델 턴 없음), 다른 요청이 붙으면 파일을 찾았을 때만 열고 넘김. 인스턴스 = 세션 ID 앞 8자(cli 의 `CLAUDE_CODE_SESSION_ID` 와 같음), 막힌 프롬프트는 다음 프롬프트에 「훅이 이미 열었다」 알림. 분류 13건, 실제 4.5초, 실사용 1회(같은 세션에서 `.test/새 문서.hwpx`) 확인
  - decisions: 빈 문서는 작업 폴더에 둔다(사용자 승인) — 플레이그라운드 하위 폴더 규칙은 훅이 모른다. 탐색기 오른쪽 클릭 열기, 창 상주(숨겼다 보이기)는 제안만 하고 보류
  - next_steps: ① 스킬 산출물 7.4초가 거슬리면 창 상주(앱 창 2초 제거) 검토 ② 훅이 놓치거나 잘못 잡는 문장이 나오면 `TRIGGER`, `FILLER` 정규식 조정(시험 `scratchpad hooktest.py` 는 세션 임시 폴더라 남지 않음)
- **10-08**: 사용자 「너가 차지하는 용량이 너무 큰데 왜인가」 → 정리 약 22GB, 스킬 75b115c, 9e2cba6(**푸시와 릴리스는 안 함**)
  - 원인: 에디터 인스턴스 폴더가 세션마다 생기고 지워지지 않았고(130개 9.3GB), 폴더마다 WebView2 프로필(60~400MB, Code Cache와 Cache)이 따로 있었다. 그 밖에 `editor/.build/rhwp/target` 22GB, 폐기한 `~/.cache/whisper` 5.1GB
  - 정리: 7일 넘은 인스턴스 48개 삭제와 나머지의 `webview` 삭제(→ 1.1GB), `target/debug/incremental`, `examples` 삭제(→ 13GB, `deps` 는 남김), whisper 삭제
  - 수정: `app.py` 프로필을 `hwpx-editor/webview` 하나로 공용, `cli.mjs` `start` 가 7일 지난 다른 인스턴스 폴더를 지움(서버가 살아 있으면 남김, 한글 이름 때문에 파일 단위 삭제). 동시 `start` 가 같은 포트를 잡거나 남의 서버에 붙던 것(`allocatePort`, `ensureServer` 가 상태 폴더를 확인하지 않음) → 진 쪽이 포트를 다시 고른다. 셋 동시 시작 2회 통과
  - 🔑 `.build` 는 이 폴더 바로 아래가 아니라 `editor/.build` 다. `~/.cache/rhwp-devel`(14GB)의 `rhwp` 와 `latest` 는 rhwp 작업 트리와 worktree(#7419 브랜치)라 빌드 폴더(1GB)만 캐시다
  - 사용자 「진행해」 → `editor/.build/rhwp` 를 `~/.cache/rhwp-devel/rhwp` 의 worktree 로 바꿈(옛 `.git` 1.9GB 삭제, 작업 파일과 `target` 은 제자리). 이 worktree 만 `core.autocrlf=true`(`extensions.worktreeConfig`, 작업 파일이 CRLF). 전환 전후 `status --ignored` 25,446줄과 diff(57파일 +5991/−322) 동일
  - ⚠ 처음 「5GB 안팎」이라 했으나 `mydocs`, `pdf` 는 작업 트리마다 있어야 하는 파일이라 줄어든 것은 `.git` 뿐이었다. `setup.mjs --clean` 은 다시 얕은 clone(1.9GB)을 만든다 — 쓸 일이 있으면 그때 worktree 로 바꾼다
  - next_steps: ① 스킬 75b115c, 9e2cba6 푸시(사용자 요청 시). 릴리스 대상 아님(cli.mjs, app.py 는 저장소 파일) ② 다음 에디터 첫 실행 때 `hwpx-editor/webview` 공용 프로필로 두 쪽 보기, 확대 비율 설정이 유지되는지 확인 ③ 10-07 블록 next_steps ②③
- **10-07**: 사용자 보고 「표 속에 표를 드래그 이동시켰는데 상위 표까지 같이 이동되네」 → 스킬 b0dbdaf. 사용자 「좋아 릴리스 푸시」 → 릴리스 **editor-d37819d8e1f9**(85ee01c 까지 hwpx, hwpx2 푸시 — b51bb30, 58f6a5b, 839b31a 포함, GitHub 새 사본 3.5초 설치와 지문 확인, 옛 editor-08b2ac806e2d 정리)
  - 원인: 스튜디오 끌기 상태(`moveDragState`)가 바깥 표 `{sec, ppi, ci}` 만 들고 cellPath 를 버려 선택 상자 판정, 놓일 자리 선, 옮기기가 모두 바깥 표에 걸렸다
  - 처방: 엔진 `move-control-cell(-wasm)`(`moveControlInCellByPath` — 같은 칸 안 문단 사이로, 홀로 든 개체 문단만, 칸 다시 싸기 + 쪽 나누기, 되돌리기 1번), 스튜디오 패치 `patches/move-drop-nested.ts`(표 속 표면 `updateCellDropLine`/`applyCellDrop`, 마우스 쪽 `getTableBBoxAtPage` 두 곳 → `claudeSelectedTableBBox`), `plugin/move-drop.ts`
  - 옮긴 뒤 표가 칸 맨 위 그림과 겹쳤다 → 엔진 `cell-tac-object-preceding`: 칸 문단 배치의 `has_preceding_text` 가 글만 세서, 글자처럼 취급 그림만 든 문단 뒤의 위아래 배치 표가 `inner_area.y`(칸 맨 위)로 갔다. 한/글 PDF(`hwp2pdf.py` 를 `hidden_desktop`)는 그림 아래. 고친 뒤 에디터도 그림 → 표 → 설명 글
  - 검증: `scratchpad clip/drag_test.py <포트>`(12단원 사본, 바깥 표 그대로, 표 속 표 칸 문단 2 → 1, 글 문단 아래로, Ctrl+Z 4항목 통과), 문서 321개 1,955쪽 SVG 해시 직전 엔진과 동일(새 도구 `test/linebreak/svghash.mjs <wasm폴더> <목록> <출력>` — 쪽 배치 대조가 못 잡는 칸 안 위치 변화까지 본다, 두 번 돌려 결정적 확인), `cargo test --lib` 3,889, issue_2069 10
  - 🔑 시험 함정: 표 속 표는 왼쪽 테두리 정확히(x)가 아니라 x+2 를 눌러야 골라진다. 예열 클릭이 화면을 스크롤하니 좌표는 예열 뒤에 잰다. Git Bash 에서 `cargo` 가 PATH 에 없어 `timeout … cargo check | grep` 이 조용히 「통과」처럼 보였다 — `export PATH="$HOME/.cargo/bin:$PATH"`
  - next_steps: ① (끝남: 릴리스, 푸시) ② 표 속 표를 칸 밖(본문, 다른 칸)으로 끌기는 아직 안 된다(같은 칸 안만) — 요청 오면 ③ 10-06 넷째 next_steps ②③ ④ 10-06 셋째 이전 블록(rhwp 에 보고할 결함 목록, 이슈 #7535~7537, #7484, #7492 답 확인, 표 속 표 미확인 둘 등)은 10-07 세션정리에서 `CLAUDE-ARCHIVE.md` 로 내렸다 — 남은 일은 거기 각 블록의 next_steps
- **10-06 넷째**: 사용자 「여러 셀이든 한 셀이든 ctrl-c v x 이런게 되야지」, 「에디터 core_silj 가 또 페이지가 밀린다」 → 스킬 b51bb30, 58f6a5b(**푸시, 릴리스 안 함**)
  - CORE 실적표(`2026 수업/교육연구/2026 교육력제고/실적_임세범/…_261006_02.hwpx`, 한/글 9쪽, 에디터 13쪽 → 9쪽). 엔진 패치 8개:
    `table-zero-pad(-measure,-layout,-float)` — HWPX 표 inMargin 네 방향 0 을 rhwp 가 「미지정 → 칸 여백(141)」(#2195 stage50, 근거 86712 HWP)으로 세로에 써 행마다 282 커졌다. 한/글 사다리(`scratchpad core/rowmin.py`): hasMargin 0 + 표 여백 0 이면 칸 여백 141/500 모두 무시(900/1000), HWP 로 저장했다 다시 열어도 같음. HWPX 에서 읽은 표(`raw_ctrl_data` 빈 표)에만 적용, HWP5 원본은 종전대로.
    `empty-host-object-max(-layout,-partial)` — 칸 안 빈 문단의 위아래 배치 그림: 다음 문단 = max(빈 줄, 그림)(한/글 재저장 1559→1600, 1617, 1824). 측정 additive 두 곳, 배치(`para_y_before_compose + flow`), 세로 정렬 내용 높이.
    `html-paste-whitespace` — HTML 붙이기가 태그 사이 소스 줄바꿈을 글자(`\n`)로 넣던 것
  - 🔑 진단법: 한/글 행 높이는 칸 cellSz 가 아니라(한/글은 cellSz 를 안 고친다) **표 sz height**(다시 적는다)와 **PDF 점선 괘선 y**(`fitz` 가로 조각 모으기)로 잰다. 한 칸만 바꾼 사본 여럿을 재저장해 표 높이 차로 행 높이를 역산(`scratchpad core/rowvar.py`). 글자 위치 대조 `cmptext.py`(PDF ↔ rhwp SVG)
  - ❌ 남은 것: 표 1이 11px 큼(874.9 / 863.9, 쪽은 안 바뀜). 병합 칸 행 배분 — 한/글은 행 경계를 「그 경계에서 끝나는 칸들의 (시작 경계 + 칸 높이) 최댓값」(최장 경로)으로 정하는데 rhwp 2-b 단계는 걸친 행 수가 적은 제약부터 풀어 10, 11행 배분이 다르다. 많은 문서에 걸리는 변경이라 따로
  - 칸 클립보드: 플러그인 `plugin/cell-clipboard.ts`(F5 칸 선택 중 Ctrl+C/X/V — 키에서 rhwp 의 칸 선택 해제만 막고 window 캡처 copy/cut/paste 에서 처리, 칸마다 HTML+글, 시스템 클립보드에 탭 글 + `<table data-claude-cells>`, 붙이기는 블록/커서 칸 왼쪽 위부터 덮어쓰기, 한 칸 → 여러 칸 채우기, 바깥 탭 글과 표 HTML). 시험 `scratchpad clip/clip_test.py <포트>`(CDP `commands: ['copy'|'cut'|'paste']` 로 실제 클립보드 명령, 21항목 세 번 연속 통과). ⚠ 첫 실행 직후 첫 붙이기가 한 번 실패한 적 있음(재현 안 됨)
  - 🔑 패치 생성기 2판 `scratchpad u14/mkpatch2.py`(기준 = 그날 첫 백업 + 첫 묶음 패치). ⚠ 조각이 빈 줄로 끝나면 setup.mjs 의 끝 줄바꿈 떼기에 깎인다 — 문맥을 더 잡는다
  - 사용자 시험 보고 셋 → 스킬 839b31a: ① 칸 붙이기 후 자간 눌림 — HTML 경로가 글자 모양을 「글꼴, 크기 같은 다른 번호」로 바꾸고 칸 경로판(`pasteHtmlInCellByPath`)은 줄을 다시 나누지 않았다 → 엔진 `clipboard-stash`(칸마다 내부 클립보드 보관, `claudeClipboardStash/Restore`)로 같은 문서 붙이기는 `pasteInternalInCellByPath`, `html-paste-path-reflow` ② 그림이 「[이미지]」 글 — 같은 원인(내부 클립보드는 그림째) ③ 칸 블록 Del → Ctrl+E 지우기 창. 시험 `scratchpad clip/clip_test2.py`(CORE 사본 7항목) + clip_test 21항목 통과. 패치 생성기 3판 `mkpatch3.py`(`BASE_SPECS=spec.json,spec2.json`)
  - 🔑 시험 함정: `cli start --no-browser` 를 `timeout` 으로 감싸면 서버까지 꺼진다 — run_in_background 로 띄운다. 시험이 붙은 서버는 health 의 browser 가 true 로 남아 다음 실행이 거절된다 — stop 후 다시 띄운다
  - next_steps: ① 사용자 확인(칸 복사, CORE 실적표) 뒤 요청 시 `release.mjs` → prebuilt.json 커밋 → 푸시 ② 병합 칸 행 배분(최장 경로) — 회귀 넓게 볼 것 ③ #2195 stage50 의 HWP5 근거(86712) 재확인 — 한/글 HWP 왕복도 0 이었다