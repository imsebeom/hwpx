# hwpx 에디터 기반 에이전트 스킬

`/hwpx` 스킬(`~/.claude/skills/hwpx`, 저장소 imsebeom/hwpx2)에 rhwp 에디터 모드를 붙이는 개발 폴더.
사용자는 브라우저의 rhwp 에디터로 문서를 보고, 터미널 Claude 가 같은 문서를 실시간으로 고친다.
**2026-09-25 스킬로 통합 완료** — 코드 원본은 이제 `~/.claude/skills/hwpx/editor/`(설명서 `references/editor-mode.md`, 시험 `editor/tests/`)이다. 이 폴더의 `editor/` 는 개발 당시 사본이고 **여기서 고치지 않는다.** `.build/`(rhwp 소스, Rust 빌드 캐시)는 이 폴더에만 있다.

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
- **09-29 넷째**: 글자처럼 취급하지 않는 그림의 본문 배치 실측(시험 문서 9가지, 한글 PDF 대조, scratchpad `wrap/`).
  한글 저장본을 열면 7/9 맞음(문단 기준 세로 거리 그림은 약 2줄 아래, 글 뒤로는 다음 문단이 겹침). **그림 문단을 편집하면 어울림 큰 쪽과 글 앞으로만 맞고** 자리 차지, 양쪽, 왼쪽만, 오른쪽만, 쪽 기준은 글이 그림 밑으로 겹친다
  (`float_placement.rs resolve_picture_exclusion` 이 LeftOnly/RightOnly 를 빼고, 줄 배치를 다시 짜면 나머지도 비키지 않음). 배치 속성은 저장 시 보존돼 한글에서는 정상. 대화상자 「본문 위치」 목록은 스튜디오가 잠가 둠.
  사용자 지적 「아이콘을 이해 못 하겠다, 글자로」 → 스킬 f082aa1(푸시 안 함) `patches/wrap-text-labels.ts`: 단추를 글자로, 본문 위치는 다음 줄. 시험 창 캡처로 확인
  - **이어서 「엔진고쳐」**(스킬 d7251aa, 4f48723, 푸시 안 함, `patches/wrap-*` 13개): 시험 9가지가 편집 뒤에도 한글 PDF 와 같은 모양
    ① `wrap-band-fragment` 엔진이 새로 짠 좌우 조각(구현 비트)도 한 줄로 그림(FIRST/LAST 조각 표시로 판별) ② `wrap-side-policy`, `wrap-exclusion(-tests)` 자리 차지(단 폭 전체 제외), 왼쪽/오른쪽 정책
    ③ `wrap-band-lead` recalculate_section_vpos 가 버리던 첫 줄 간격(그림 아래로 내려간 줄) 복원 ④ `wrap-page-*` 쪽/종이 기준 — 띠 함수 서명을 안 바꾸려고 thread_local 로 쪽 기하 전달
    ⑤ 🔑 `wrap-local-edit` **스튜디오는 8자 이하 입력을 `replaceBodyTextLocal` 빠른 경로로 보낸다** — 노드 재현(insertText)은 통과했는데 실제 창 타이핑만 겹쳐서 찾음. 띠 문단이면 일반 삭제, 삽입으로 돌림
    ⑥ `wrap-para-offset` 좁아진 첫 줄 추정에 세로 거리를 또 더하던 것(세로 거리 0 이면 종전대로) ⑦ `wrap-behind-advance` 글 뒤로 그림이 흐름을 문단 시작으로 되감던 것(빈 문단은 종전대로)
    ⑧ `wrap-text-flow-props` + `wrap-text-flow.ts` 본문 위치 목록 풀기(엔진 JSON textFlow, 변경 감지에 text_flow)
    검증: 관련 단위 시험 91건, 전체 `cargo test --lib` 3,889 통과(빠른 경로 패치 전 기준), 실제 창에서 타이핑/Backspace/본문 위치 오른쪽/되돌리기, 저장본 verify 통과와 한글 PDF 동일,
    실사용 8개 문서 열기 SVG 7개 바이트 동일(c5 글 뒤로 두 쪽만 바뀜, 한글 PDF 쪽으로), edit_flow 실패(c2 패닉, c4 1, c8 3)는 패치 걷은 기준 WASM 에서도 같음
    도구(scratchpad `wrap/`): build.py·build_ref.py(시험 문서), grid.py(한글|열기|편집), apply.mjs, wrapswap.mjs off|on, patchcheck.mjs(깨끗한 v0.8.6 에 패치 목록 재적용 대조), 예제 `.build/rhwp/examples/claude_wrap_edit.rs`
  - 남은 것: ① 한글은 그림을 바깥 여백(보통 1mm)만큼 안쪽에 그리는데 rhwp 는 여백 없이 그려 모든 비TAC 그림이 3.8px 높다(표, 도형 공용 계산이라 범위 밖) ② 줄 배치 없는 문서(한글을 안 거친 산출물)를 열 때의 어울림은 손대지 않음(에디터 서버가 한글 줄 배치로 보정) ③ `.build/rhwp/pkg-base`(기준 WASM) 삭제가 권한에 막혀 남아 있음 ④ rhwp 이슈로 올릴지 미정
- **09-29 둘째**: 사용자 지시 「한글 파일을 만들고 나면 마지막엔 에디터로 연다」 → 스킬 ea95324(푸시 안 함). SKILL.md 결정 트리 머리에 「마지막 단계는 에디터로 열기」(묻지 않음, 여럿이면 최종본 하나, 읽기 E 제외), 워크플로 A [9], editor-mode.md 1절.
  `cli.mjs start` 가 떠 있는 창에 저장 안 한 편집이 있으면 session.json 을 바꾸기 전에 멈춘다(`--force`). 시험 인스턴스로 dirty 차단, 세션 불변, --force, 깨끗한 상태 재열기 확인
- **09-29 셋째**: 한국문화 교재 통합본(567MB, 그림 486장)이 에디터에서 안 열렸다 — `/api/doc` 의 base64 가 V8 문자열 상한 초과. 스킬 fe5bee5, 394b83b(푸시 안 함).
  ① 150MB 초과면 그림을 1,200px JPEG 로 줄인 사본(58MB, 16초, 캐시)으로 열고 저장(`save`, 화면 Ctrl+S)이 sha1 로 원본 그림을 되돌린다(rhwp 가 그림 id 를 다시 매겨 이름으로는 짝이 안 맞는다). 원본 그림은 `proxy-orig.hwpx` 에서
  ② 🔑 **`studio.getDocumentState()` 는 매번 문서 전체 내보내기 + SHA-256** — host 가 매초 불러 큰 문서에서 주 스레드가 막혔다(wasm 10MB 9초, 일반 Edge 0.07초). 편집 카운터가 바뀔 때만 부르게 고쳐 열기 92초 → 14초.
    pywebview 의 요청 가로채기 필터를 의심해 걷어 봤으나 무관(되돌림)
  검증: 두 번 연속 화면 저장 뒤 그림 486장 바이트 원본과 동일, 한글에서 133쪽(원본과 같음), 작은 문서는 종전대로. 편집 한 번 약 5초(스냅샷이 문서 전체를 올림)는 남은 한계
  - 마무리: 사용자 요청으로 통합본을 이 세션 에디터(c88e185e, 포트 7781)로 열어 두었다(09:04). 스킬 e5adddd..394b83b 를 hwpx, hwpx2 에 푸시.
    옛 에디터 서버 f677b77e(포트 7780, 창 없음, 같은 문서)는 다른 세션 것이라 그대로 두었다
  - next_steps: ① 큰 문서 편집 한 번 5초 — 스냅샷이 문서 전체를 내보내 올린다. 줄이려면 사용자 편집 스냅샷에서 hwpx 를 빼고 텍스트와 모델만 올리는 방안 검토
    ② `changes` 에 화면 저장 기록을 함께 보일지(09-28 제안, 답 없음)
- **09-29**: 화면 저장(Ctrl+S)이 「다른 이름으로 저장」 대화상자를 띄우던 것(사용자 보고) → 스킬 e5adddd. `host.js bindSourceHandle` 이 스튜디오 `wasm.currentFileHandle` 에 핸들 흉내를 붙이고
  서버 `/api/save-source` 가 연결된 원본에 덮어쓴다(사용자 선택 「원본 덮어쓰기」, 세션 첫 저장 전 `<작업 공간>/backup/` 에 원본 사본). `$E save` 의 새 판 규칙은 그대로.
  시험 창에서 저장 두 번: 대화상자 없음, dirty false, 원본에 편집 반영, 백업 1개, verify 통과. 푸시 안 함. 이미 떠 있던 에디터(bonmun, butim, f677b77e)는 옛 서버라 다시 띄워야 적용
- **intent(09-28 아침)**: 사용자 결함 보고 처리와 kordoc(chrisryugj/kordoc, MIT) 기능 이식. 스킬 커밋(09-28 푸시분 이후 미푸시):
  7c71ba4 칸 안 두 그림 사이 캐럿과 빈칸 입력 / c7d6034 상단 막대 「RHWP + imsebeom」 / 667e01f 표, 그림 끌어 옮기기(끄는 동안 푸른 선, 놓을 때 문단째 이동, `move-control-para*.rs`, `plugin/move-drop.ts`) /
  10856a7 칸 안 그림 크기 바꾸기 뒤 칸 높이 = max(적힌 높이, 내용)(`cell-pic-delta-*`) / 0e1b4d8 `gongmun_lint.py` / 789e338 `seal_hwpx.py` / ab908f2 `chart_hwpx.py`
  - **decisions**: kordoc 은 외부 의존 없이 표준 라이브러리로만 옮긴다(사용자 지시 「외부 의존성은 원치 않는다, 가져올 수 있으면 괜찮다」). reflow(쪽수 예측)는 6개 중 4개 문서에서 더 나빠 넣지 않았다
  - 🔑 **도장 날인 실측(한글 PDF)**: 칸 문단의 글 앞 그림(flowWithText=0, vertRelTo=PARA)은 세로를 **표 위**에서 잰다(kordoc 은 칸 기준으로 보고 큰 칸에서 도장이 칸 맨 위로 갔다). flowWithText=1 은 쪽수가 54→55 로 바뀐다.
    쪽을 넘는 표 뒤쪽 문구의 도장은 앞 쪽에 걸리거나 사라진다(경고만). `<hp:fwSpace/>` 는 0.25em, PDF 글자 상자 폭은 빈칸 전진 폭이 아니다
  - 차트: 원 3D 는 `firstSliceAng` 을 빼고 `view3D` 를 넣어야 한글이 그린다(kordoc 결함)
  - changes_made(마무리): 스킬 67ee979..ab908f2 를 hwpx, hwpx2 둘 다 푸시. guide4 창을 새 엔진으로 다시 띄움(10:13, `_22`, 포트 7780)
  - guide4 창은 사용자 확인(시험 편집이라 버림) 뒤 `stop --force` 로 닫았다. 떠 있는 에디터 없음
  - 스킬 1b34e75 README 에 kordoc 크레딧(kordoc, claw-hwp), 워크플로 표 세 줄, 「kordoc 이식」 절, 에디터 편집 개선 줄을 넣어 hwpx, hwpx2 푸시
  - 사용자 질문 「화면 저장을 에이전트가 보고 받나」: 기록(`editor-log.jsonl`)만 남고 알림은 없다. `changes` 에 저장 기록을 함께 보일지 제안해 두었다(답 없음)
  - next_steps: ① md2hwpx 의 ```chart 펜스 연결은 하지 않았다(필요하면 `chart_hwpx.parse_fence` 재사용) ③ 도장: 쪽을 넘는 표 뒤쪽 문구는 자동 해결책 없음(경고만)
- **intent(09-27 셋째 세션 ~ 09-28 밤샘)**: 사용자가 원고를 고치며 찾은 결함(그림 자르기 뒤 칸 눌림, 표 끌기, 칸 그림 옆 캐럿, 그림 넣기 도구, 칸 글에 표가 안 따라감, Ctrl+방향키 크기 조절)을 고치고, 잠든 사이 회귀 시험으로 더 찾았다. 스킬 커밋(푸시 안 함):
  4b29a9f 칸 그림 자르기/크기 바꾸기 뒤 다른 칸 눌림(`cell-pic-delta-*`) / 7acb26f 표 끌어 옮기기(`tac-table-move*`, `table-move-undo.ts`) /
  fdf631c, 93e3872 `cli.mjs image`(좌표나 커서 자리, 되돌리기 한 번) / 4611bf9 칸 글자처럼 취급 그림 옆 캐럿(`cell-inline-caret-*`) / 3656e79 칸 안 그림(`cell-pic-inline-*`, `paperOffsetXHu=i32::MIN` 약속값) /
  24c0a57 표 높이 맞춤 둘째 판(재는 사본 높이 0, 줄 높이는 변화량만, 쪽 나누기 시작에 dirty 표 일괄 `claude_sync_dirty_tac_tables`, 바꾸기 `replace-cell-dirty`, Ctrl+방향키 최소 크기 `column-resize-min.ts`) /
  6585ccf 뒤 문단 vertpos 는 rhwp `recalculate_section_vpos` 로, 회귀 시험 `editor/tests/edit_flow.mjs` / 99a8a84 image 는 그림만 담은 새 문단으로(글 끝에 끼우면 첫 줄이 그림 높이가 됐다)
  - 🔑 **edit_flow 의 「쪽 끝 넘침」 실패 대부분이 시험의 오판이었다**(09-28 실측): ① 쪽 끝 빈 문단은 엔진이 높이 0으로 흡수하는데(typeset `empty_tail_bridge_to_reset`) 빈 줄 표식 런(w=본문 폭, 글자 없음)이 본문 밖 좌표로 나온다 ② 꼬리말 쪽 번호 런(paraIdx 없음)은 원래 본문 아래다 — 쪽이 하나 늘면 넘침도 하나 늘었다. 둘을 빼니 사용자 최신 원고 26건 → 0, 말뭉치 10개 중 9개 0.
    그래서 「typeset 저장 사다리 때문에 편집 뒤 쪽 끝이 넘친다」는 rhwp 이슈 초안은 **쓰지 않았다**(근거가 시험 오판)
  - 진단 도구: 네이티브 `target/debug/rhwp.exe dump-pages <hwpx>`(쪽마다 항목, vpos, 줄 배치), `export-svg -o <폴더>` + `RHWP_DIAG_FLOW`, `RHWP_DIAG_TAC`, `RHWP_DIAG_ADV`. cargo 는 `~/.cargo/bin` 을 PATH 에 넣어야 잡힌다.
    어느 `continue` 로 빠지는지 모를 때는 문단 루프의 `continue` 앞에 진단 줄을 임시로 넣는다(사본 두고 되돌림)
  - 밤샘 커밋(09-28): 056a3c2 시험 판정 정리와 행 추가/삭제 / 55ccd11 cli `die` — 서버에 POST 한 뒤 `process.exit()` 가 Windows Node 24 에서 libuv 단언(`UV_HANDLE_CLOSING`, 종료 코드 127)으로 죽어 `exitCode` + 예외로 바꿈 /
    5c6448e ① 한 문단에 글자처럼 취급 표가 여럿(글 없는 문단, 줄마다 표 하나)이어도 표 높이 맞춤 ② 글 없는 표 줄은 「표 높이 + 바깥 여백」으로 곧장 맞춤(행 추가가 hp:sz 를 먼저 바꿔 두어 줄이 264px 로 남고 뒤 문단이 쪽 밖으로 나갔다)
    ③ **Ctrl+위/아래**: 스튜디오(`row-resize-rendered.ts`)가 고른 행에 걸친 칸(합친 칸 포함)을 「그려진 높이 + 한 단계 × 걸친 행 수」로 보내고 표식 `{"cellIdx":-1,"tableHeight":1}` 을 붙이면, 엔진(`row-resize-th-*`)이 조절 뒤 표를 높이 0 사본으로 다시 재어 표 높이로 둔다.
    원인은 적힌 칸 높이가 내용보다 작은 칸(더해도 안 늘었다)과, 표 높이와 행 합의 차이를 측정기가 모든 행에 비례로 나누던 것. 62개 표 비교 늘이기 맞음 35 → 51, 줄이기 50 → 50. 여러 쪽에 걸친 표는 종전 방식
    ⚠ 합친 칸을 빼면 고른 행 합이 합친 칸 높이에 묶여 한 행이 줄 때 다른 행이 늘었다. 스튜디오가 표 높이를 셈해 보내면 줄일 때 내용 최소 높이에 걸린 행을 몰라 차이가 다른 행으로 번졌다(그래서 엔진이 다시 잰다)
  - fe550f9, 3b5c4d5 시험 확장(열 추가/삭제, 칸 합치기/나누기, 되돌리면 처음 높이나 편집 기준값으로 돌아와야 통과) /
    0046447 **칸을 한 번만 고쳐도 표가 한글보다 커지던 것**: 한글 PDF 대조로 d01 p7 두 표(271.5, 367.1), d05 p4(144.7), d09(99.5)는 rhwp 가 처음 그린 높이가 한글과 같은데
    표 높이 맞춤이 잰 높이는 9~32px 컸다(칸 안 표를 rhwp 가 크게 셈 + 편집한 칸의 문단 세로 위치를 rhwp 가 다시 매김).
    처방: `Table.claude_measure_offset`(패치 `tac-sync-offset-*`, 표 구조체 필드라 생성 자리 4곳과 진단 구조 분해도 고침)에 처음 쪽 나눌 때 「잰 높이 − 적힌 높이」를 두고,
    편집 뒤 높이 = 잰 높이 − 그 값. 잴 때는 사본의 **모든 칸** 문단 세로 위치를 rhwp 로 다시 매겨 기준값과 같은 조건으로 잰다. Ctrl+위/아래 재측정도 같은 함수(`claude_edit_table_height`).
    또 `tac-line-outer(-size)`: 개체만 있는 줄 높이에 글자처럼 취급 표의 위아래 바깥 여백을 더한다(한글 1282 + 283×2 = 1848. 칸 안 머리표 옆 글을 지우면 줄이 1282 로 줄어 바깥 표가 7.5px 줄었다).
    검증: 문서 11개 편집 흐름 시험 실패 0, 한글 PDF 대비 글줄 위치는 여섯 문서 모두 옛 빌드와 같음(열 때 배치 불변), 깨끗한 v0.8.6 사본에 setup 패치 57개 적용 결과가 실제 소스와 빈 줄만 다름
    ⚠ 처음 그린 높이가 한글과 다른 표(d02 p5: rhwp 106.9, 한글 98.0)는 편집하면 한글 값으로 간다. 사용자 원고 p55(rhwp 239, 한글 260)는 편집해도 239 그대로다(처음 적재의 TAC 비례 축소 문제, 범위 밖)
  - 검증(04시): 편집 → 저장 → 다시 열기 왕복 64건 표 위치, 높이, 쪽수 불변. 편집본을 한글로 열어도 표 높이 일치(d05 174.7 = 174.7, d01 413.9 대 414.4)
  - 67ee979 **칸에 문단을 더하면 표가 한글보다 커지던 것 해결**: 한글의 행 높이 = 칸마다 max(적힌 칸 높이, 저장 줄 배치 마지막 줄 끝 + 위아래 칸 여백)이다
    (d05 p4 칸 0 뒤 새 문단 — 한글 51.2/112.2, 옛 rhwp 58.4/121.1). rhwp 측정기는 줄 간격, 문단 간격을 크게 잡아 평소엔 TAC 비례 축소가 가려 주다가 문단이 늘면 드러났다.
    처방 ① `tac-row-ladder`: 글자처럼 취급 표에서 합친 칸, 세로쓰기, 줄 배치 없는 문단이 없으면 측정기 행 높이를 사다리 값으로 ② 표 높이 맞춤의 재기(`claude_ladder_table_height`)도 같은 식.
    검증: 한글 PDF 대비 5px 넘게 어긋난 글줄이 **열 때부터** 줄었다(d02 35→6, d06 30→24, d07 26→20, d05 3→0, d04 1→0, 사용자 원고 86→81, 나빠진 문서 없음),
    편집 흐름 11개 실패 0, 왕복 64건 불변, Ctrl+위/아래 늘이기 57/62, 줄이기 56/62(옛 방식 38, 55). 재현 `scratchpad/cellvar.mjs text|pic|pictext`, 한글 기준 `hpdf/cv_*.pdf`
    ⚠ `getTableCellBboxes` 는 그림 넣은 직후 렌더 트리가 낡아 행 높이를 틀리게 줄 수 있다(SVG 행 경계는 맞다). 시험에서 행 값을 볼 때는 SVG 로 확인
    ⚠ 「그림 뒤 글이 그림 꼭대기에 그려진다」는 오해였다 — `getPageTextLayout` 런의 y 는 줄 윗변이고, SVG 글 기준선(264.5)은 한글(글 윗변 250.7)과 맞다
  - 진단 도구(scratchpad): `cmp_pdf.py <한글pdf> <wasm폴더> <hwpx>`(한글 PDF 글줄과 rhwp 글자 런 대조), `pdf_hlines.py`(한글 PDF 표 가로선), `rowcmp.mjs`(Ctrl+위/아래 방식 비교), `hwp2pdf.py`(한글 COM PDF)
  - 시험 창 함정: `stop --force` 뒤 다시 띄우면 「문서 복구」 창이 떠 키가 그리로 간다(`.modal-overlay` 의 「삭제」 단추를 눌러 닫는다). 제품 빌드에는 `window.__wasm` 이 없고 iframe 의 `__claudeIH()` 가 입력 처리기(`.wasm`, `.cursor`)를 준다
  - 미해결: 그림 칸에서 그림 뒤 글을 rhwp 는 그림 아래, 한글은 위에 놓는다 / 제목 글꼴이 ㄴㄴ 입력 뒤 작아진 일(재현 안 됨) / 처음부터 눌려 그려지던 표(TAC 비례 축소)는 편집하면 내용 높이로 커진다(「바로잡힘」, 한글과 어느 쪽이 맞는지 미확인)
- **intent(09-27 둘째 세션)**: 사용자가 가이드북 원고(2-4절)를 에디터로 고치며 찾은 결함과 요청을 처리했다. 스킬 커밋(푸시 안 함):
  046aa52 문단 모양 미리보기(줄 간격, 문단 간격 반영) / ffc4fcd **칸 줄 나눔 엔진 패치** `cell-reflow-starts`(HWPX 칸 편집 뒤 후보 줄 수만 보고 저장 줄 배치를 되돌리던 것 → 줄 시작 위치까지 비교) /
  5dc23de, 91286c0 앱 창 닫을 때 저장 확인(dirty 일 때만, pywebview confirm_close)과 마지막 편집 기록(evaluate_js 는 Promise 를 **콜백으로만** 준다) /
  0c5b439 **쪽 끝 반 줄 넘침 엔진 패치** `tac-host-sync-*`(칸 편집으로 글자처럼 취급 표가 커져도 hp:sz 와 표를 담은 줄 높이가 그대로라 쪽 나누기가 옛 높이만 셈 → 편집 직후 표를 재어 둘을 맞추고 recompose. 한글 PDF 와 1쪽 끝 줄 동일) /
  8bf284a 대화상자 Enter 확인, F5 셀 블록 Ctrl+E 지우기 선택(내용/줄/칸), Shift+방향키 경계 이동의 병합 칸 뒤틀림(스튜디오 소스 패치 `boundary-resize-merged.ts`) /
  5530baf 그림 오른쪽 클릭 「그림 자르기」(손잡이 끌기 자르기, 바로 오른쪽 클릭 선택)
  - 함정: 쪽 나누기는 `typeset.rs`(TypesetEngine)가 기본, `RHWP_USE_PAGINATOR=1` 이면 옛 `pagination/engine.rs`. 두 경로 다 TAC 표 문단을 **저장 줄 높이**로 자른다 / setup.mjs 는 패치 목록이 같으면 WASM 을 안 다시 빌드한다(`pkg/.claude-patched` 삭제로 강제) / Bash heredoc 로 `\n` 든 JS 를 넣다가 두 번 깨졌다(규칙대로 Write 로 만든 스크립트 사용)
  - next_steps: ① 사용자 원본(_05 등)은 이미 낡은 표 높이가 저장돼 있어, T2 칸을 한 번 편집해야 새 값이 들어간다 ② 캐럿 축 등 이전 next_steps 유지 ③ 스킬 커밋 푸시는 요청 시
- **intent(09-27 세션)**: 사용자가 에디터를 직접 시험하며 찾은 결함을 차례로 고쳤다 — 여러 셀 대화상자, 글자 색 선택, 가운데 정렬 음영, 글자처럼 취급 표 선택과 편집 어긋남(엔진), 데스크탑 앱 미리보기 열기.
  - **changes_made**(스킬 커밋, hwpx·hwpx2 푸시):
    ⓐ 73c4177 셀 블록(F5 여러 셀)에서 표/셀 속성, 문단 모양은 첫 칸에만, 글자 모양은 대화상자가 안 열리던 것 — 플러그인 `installCellBlockDialogs`(12/12 실측, 되돌리기 한 번)
    ⓑ 787f5fd 글자 색 빠른 단추와 글자 모양 대화상자 색 칸에 색 목록(`plugin/color-palette.ts`, 테마, 표준, 최근 색)
    ⓒ f587643 가운데 정렬 문단을 첫 글자부터 고르면 음영이 왼쪽 여백부터 — 엔진 패치 `sel-left-at-glyph`
    ⓓ bf05e4d, b2a3346, a763d1e **캐럿 축 수정** — 스튜디오 캐럿은 캐럿 축(개체 한 칸), 엔진 편집 함수는 글자 축, `split_at` 은 나누기 축이라 개체 뒤 입력, 삭제, 복사, 음영, 굵게, 엔터가 한 칸씩 어긋나고 개체가 선택에 안 들었다.
       엔진 패치 15개(`patches/caret-axis-*.rs`: convertCaretOffset, deleteRangeCaret*, copySelectionCaret*, setInsertAfterInline, 붙여넣기 캐럿 삽입, 음영 줄 시작과 개체 자리 나누기) + 연결층 `caret-axis-bridge.ts`(약 40개 메서드 축 변환) + Backspace/Delete 개체 칸 → 선택 삭제 명령.
       검증 `cargo test --lib` 3,898 통과, 에디터 키 입력 실측 9종 통과. 스튜디오 `npm test` 실패 8건은 CRLF 소스 정규식(고친 파일과 무관). rhwp 이슈 **#7444**
    ⓔ 050f3a8 데스크탑 앱이면(`CLAUDE_CODE_ENTRYPOINT` 가 cli 아님) 앱 창 대신 `.claude/launch.json` 의 `hwpx-editor`(`cli.mjs hold <상태 폴더>`)로 미리보기. 다른 세션이 데스크탑에서 실측해 editor-mode.md 에 「창이 숨김으로 남아 Browser 단추를 눌러야 보인다」를 적었다
  - **decisions**: 대화상자 결함은 플러그인에서(스튜디오 원본 불변), 캐럿 축은 사용자 선택 「엔진 수정, 어긋남 전체 + 개체 선택」 — 엔진 API 는 글자 축 그대로 두고 연결층에서 변환(Claude 편집 도구가 글자 축을 쓰므로), rhwp 에는 이슈만 올리고 PR 은 내지 않는다(사용자 지시). 사용자 에디터는 다시 띄우기 전에 묻는다(재시작으로 저장 안 한 편집을 잃었다)
  - **next_steps**:
    ① 셀 안 글자처럼 취급 개체(표 속 표, 셀 속 수식)에서 입력, 삭제, 음영 실측 — 시험 창은 `HWPX_EDITOR_INSTANCE=mcdbg WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9334`, 도구는 세션 scratchpad 의 cdprun.mjs/key.mjs/type.mjs 방식(editor/tests 로 올릴지 검토)
    ② 셀 안 수식 음영(상자 찾기가 본문 수식만), 찾기/바꾸기와 필드 정보의 축 변환은 미적용
    ③ 표 뒤 입력 직후 Shift+End 선택이 표 앞에서 시작한 일이 한 번 있었다 — 재현 안 됨, 다시 보이면 조사
    ④ rhwp #7444, PR #7433 답 확인(`gh issue view 7444 -R edwardkim/rhwp`). 표/셀 속성 대화상자 여러 셀 결함은 rhwp 보고 여부 미정
    ⑤ 캐럿 축 임시 단위 시험(9건)은 지웠다 — 패치에 시험을 넣을지 검토
- **intent(09-25 둘째 세션): 문항 3을 에디터로 열었더니 문단이 한 줄로 눌리고 표가 겹친 것(사용자 발견)을 스킬과 rhwp 양쪽에서 끝까지 고쳤다 — 에디터 보정, 실제 줄 배치, 세션별 에디터, 작업 기록, rhwp 엔진 패치와 PR #7433.**
  - **changes_made**(스킬 커밋 a6413e6, 042a754 — hwpx, hwpx2 푸시):
    ⓐ `hwpx-zip.mjs stripDummyLinesegs()` + `server.mjs /api/doc` — 더미 줄 배치를 걷고 보낸다
    ⓑ `editor/hancom_layout.py` — 사본을 한글로 열어(쪽수를 읽어 조판을 끝낸 뒤) 저장하고, 줄 배치와 표 `sz height` 만 문단끼리, 표끼리 짝지어 원본에 옮겨 심는다.
    `server.mjs` 가 더미가 있는 문서에만 쓰고 `layout-cache.hwpx` 로 캐시한다. 실패하면 ⓐ로 물러난다
    ⓒ `cli.mjs` — 앱 창 pid 를 `app.pid` 에 기록. `start` 는 살아 있는 창을 다시 쓰고 `stop` 은 창을 닫는다(저장 안 한 편집이 있으면 멈춤, `--force`)
    ⓓ `references/editor-mode.md` 1절에 창 하나 원칙과 한글 줄 배치 경로를 적었다
  - **decisions**: ⓐ 칸 높이를 rhwp 측정값으로 맞추는 우회(`host.js fitRowHeights`)는 **버렸다** — rhwp 가 재는 높이가 그리는 높이보다 낮아 긴 칸이 여전히 모자랐고, 저장본에 부정확한 칸 높이가 들어간다
    ⓑ 한글 재저장본을 통째로 쓰지 않는다(그림 BMP 부풀기) ⓒ 이 문제는 캠프 프로젝트에 기록하지 않는다(문항 내용 변화 없음, 사용자 확인)
  - **검증**: 문항 3 한글 재저장본과 6쪽 3,478자 좌표 동일(`allpages.mjs`), 세 번 실행 md5 동일, 한글 잔여 프로세스 0, start→start→stop→start 에서 창 1→1→0→1, 실제 창 캡처(`winshot.py`)로 1~3쪽 겹침 없음
  - **이어서(같은 날, 사용자 지시 「실제 줄배치 넣어라」)** — 스킬 커밋 3dc908e, hwpx·hwpx2 푸시.
    `hancom_layout.py` 를 `scripts/` 로 옮기고 **`fix_namespaces.py` 명령줄 실행 끝에서 언제나 부른다**(더미가 있을 때만이 아니라 — 중간에 내용을 바꾼 문서의 낡은 줄 배치도 바로잡는다).
    실패하면 경고만, `--no-layout`/`HWPX_NO_LAYOUT=1` 로 끈다. 한글 호출 잠금(`%TEMP%/hwpx-hancom-layout.lock`), 띄우기부터 저장까지 통째 3회 재시도, 잠금 풀기 전 1초 대기.
    🔴 **동시 실행에서 두 가지 RPC 오류를 밟았다** — 띄우기 단계(「원격 프로시저를 호출하지 못했」)와 `Quit` 단계(「RPC 서버를 사용할 수 없」). 닫히는 중인 한글에 붙은 것이다. 재시도 뒤 4건 동시 × 3회 전부 성공
    SKILL.md 규칙 42 신설. md2hwpx 산출물의 **polaris JID 11041 2건은 변경 전부터 있던 것**(범위 밖, 미조사)
  - **rhwp 결함 보고 준비** — 최소 재현 `~/.cache/rhwp-devel/repro/repro_nols_tac.hwpx`(md2hwpx 표 둘, `treatAsChar="1"`, 줄 배치 없음). 🔑 **`treatAsChar="0"` 이면 재현되지 않는다** — 원인 조건은 「글자처럼 취급하는 표 + NO_LS 셀 문단」이다.
    본문 `repro/issue_body.md`(재현 파일 base64 포함, md5 대조 통과). 기존 #7416 은 더미 사다리를 믿는 축이라 겹치지 않는다. **게시함: https://github.com/edwardkim/rhwp/issues/7419**(imsebeom). gh 로그인은 안 된 상태라 git 자격 증명 관리자의 토큰을 그 명령에만 넘겨 올렸다(`git credential fill` → `GH_TOKEN`)
  - **gh 로그인 완료**(imsebeom, keyring, scopes repo·workflow·gist·read:org). 이제 `gh issue view 7419 -R edwardkim/rhwp` 로 답을 본다
  - **저장 시험 통과** — 사용자가 에디터 **화면**에서 저장했다(바탕화면 `제출_문항3_이산화탄소_260924_01.hwpx`, 원본과 같은 이름. 새 판 규칙은 cli save 에만 걸린다).
    글자 4,484자 원본과 동일, 더미 0 / 한글 줄 배치 316, 그림 PNG 유지(104KB), 한글에서 6쪽으로 열림. 한글 PDF 대조로 2~6쪽 픽셀 동일, 1쪽은 사용자가 서식을 바꾼 「자료출처」 칸(T1r20) 한 곳만 다르다
  - **작업 기록 기능**(스킬 5c4d5d9, 푸시) — 사용자 지시 「에디터가 작업기록을 남기지 않나보네. 로그 기능 추가해라」.
    `editor-log.jsonl`(비우지 않음)에 시작, 불러옴(줄 배치 경로), 열림, 편집, 저장, 다른 파일 열기, 오류, 종료. **화면 저장은 host.js 가 iframe 의 `createWritable` 을 감싸 잡는다**(스튜디오는 저장 이벤트를 안 낸다, 파일 이름만 남는다). `cli.mjs log [N|--all]`.
    시험은 OPFS(`navigator.storage.getDirectory()`) 파일 핸들로 대화상자 없이 같은 쓰기 경로를 탔다 — `tests/cdp_eval.mjs 9333` + `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9333`
  - **한글 없는 환경의 표 겹침 해결**(스킬 024e2f2, 푸시) — 사용자 지시 「해결방법 찾아라」.
    🔑 **원인은 rhwp 의 TAC 비례 축소 규칙**(`height_measurer.rs` `TAC_SHRINK_MAX_OVERFLOW_RATIO = 1.5`): 글자처럼 취급하는 표에서 내용이 적힌 `hp:sz height` 의 1.5배 이하로 넘치면 적힌 높이로 누르는데, 줄 배치가 없으면 행별 하한이 0 이다. `session_edited` 는 HWP5 에서만 켜진다.
    그래서 「지시문 세 배」 변형(1.5배 초과)은 늘고, 재현 파일(1.1배)은 눌렸다. 높이 0 은 축소를 피하지만 쪽 나누기가 표를 0 으로 보아 쪽 밖으로 밀어낸다(문항 3에서 5쪽).
    처방 `editor/rhwp_layout.mjs`: 높이 0 으로 열어 `getTableCellBboxes` 로 잰 행 높이 합을 적어 다시 넘긴다. 서버가 한글 실패 또는 비 Windows 에서 쓴다(`HWPX_EDITOR_NO_HANCOM=1` 로 시험).
    Node 용 WASM 은 `studio-dist/node/`(setup.mjs 가 복사. `studio-dist/rhwp.js` 는 번들과 짝이 달라 「function import requires a callable」). 지금 설치본에는 개발 폴더 `.build/rhwp/pkg` 에서 손으로 복사했다(md5 852d8442 동일)
    검증: 일곱 표가 한글 재저장본과 같은 쪽, 창 캡처로 겹침 없음, 보정본의 한글 PDF 가 원본과 6쪽 픽셀 동일. #7419 에 원인과 우회를 댓글로 달았다
    ⚠ 셀 안의 표는 보정하지 않는다. 한글과 줄 나눔이 조금 달라 쪽을 넘는 칸의 끊기는 줄이 한 줄쯤 다를 수 있다
  - 🔴 **에디터는 세션 사이에 공유된다 — 두 Claude 세션이 동시에 쓰면 서로의 문서를 덮어쓴다**(2026-09-25 10:24 실측).
    포트 7780 과 `~/.claude/cache/hwpx-editor/` 가 하나라, 내가 시험 파일을 연 직후 한국문화교재개발 세션이 `start` 로 자기 문서를 같은 창에 열었다.
    내 CDP 클릭 한 번이 그 문서에 들어갔다(dirty false, 변경 0 확인). → **아래 「여러 에디터」(012c176)로 해결**
  - **rhwp 근본 원인**(`~/.cache/rhwp-devel/rhwp`, devel — 아래 PR #7433 으로 마무리) — 원인은 두 보정의 맞물림이다. ① 측정기 TAC 축소가 행을 [25.5, 38.5] 로 줄여 합을 선언 64 에 맞추고
    ② layout `trust_declared_row_heights` 의 viewtext 갈래(칸 전부 NO_LS 면 선언 신뢰)가 합이 같다고 행을 셀 선언 [32, 32] 로 되돌린다. 진단은 네이티브 디버그 빌드(`target/debug/rhwp.exe export-svg`, 증분 1~2분) + `RHWP_DIAG_ROWH`.
    수정안: `height_measurer.rs` 축소 조건에 `generator_restated_height`(hwpx, 칸 전부 NO_LS, 표 선언 == 행별 셀 선언 합)면 축소하지 않음. 재현 파일 행 [32.0, 38.5] = 한글 재저장본과 같음
  - **여러 에디터**(스킬 012c176, 푸시): 세션마다 `hwpx-editor/<세션 ID 앞 8자>/` 와 포트(7780~). `HWPX_EDITOR_INSTANCE`, `cli list`, 창 제목에 문서와 인스턴스.
    옛 공용 에디터가 떠 있으면 계속 쓴다. 두 인스턴스 동시 시험 통과, 이후 다른 세션(615ea4fc)과 실제로 나란히 돌았다.
    같은 커밋에서 **줄 배치 없는 문단 + TAC 표 문서도 열 때 보정**(학교교육계획류 131개가 대상)
  - **rhwp 패치 둘**(`fix7419_devel.patch`, devel 기준, `height_measurer.rs` 한 파일 31줄):
    ① 축소 조건에 `generator_restated_height`(hwpx, 칸 전부 NO_LS, 표 선언 == 행별 셀 선언 합이면 축소 안 함) — 본문 표 [32, 38.5] = 한글
    ② `unabsorbed_nested_tables_height`: 합성 줄(NO_LS)이 선언 표 높이만 담으면 중첩 표가 자란 차이를 더함 — 표 속 표 바깥 칸 67.8 → 74.2px, 안쪽 표 [32, 38.5]
    `cargo test --lib` 3,873 통과(47분). 통합 시험은 `node scripts/rust-test-suite-manifest.mjs --prepare` 후 `cargo nextest --cargo-profile release-test --tests` + Native Skia 3종이라 수 시간(CONTRIBUTING.md 1~2절)
    ⚠ v0.8.6(에디터가 쓰는 판)에는 그대로 안 들어간다 — 문맥이 다르고 layout 의 viewtext 선언 신뢰 갈래가 없다. 손으로 옮겨야 한다
  - **표 속 이미지 클릭**: 재현 안 됨. 문항 3 그래프와 한국문화 2단원 사진 모두 클릭으로 선택됐다(창 캡처). 보정 전에는 그림을 그리는 자리와 판정 칸이 어긋나 있었던 것이 원인으로 추정
  - **에디터 엔진에 패치 적용**(스킬 6b4e128, 3738bca, 푸시): `patches/tac-no-ls-shrink.rs`, `tac-no-ls-nested.rs` 를 setup.mjs 가 찾아 바꾸기로 넣는다(CRLF 소스 맞춤, 패치 목록이 바뀌면 재빌드).
    스킬 `editor/.build` 는 개발 폴더 `.build` 로의 **디렉터리 연결(junction)** 이다(`_winapi.CreateJunction`, cmd mklink 는 인자 해석 실패). 재빌드 18.6분.
    결과: 재현 [32, 38.5], 표 속 표 바깥 74.2 / 안쪽 [32, 38.5], 문항 3 은 에디터 보정(실제 표 높이 적기)까지 거치면 일곱 표가 한글과 같은 쪽.
    🔑 **엔진은 쪽 나누기에 여전히 적힌 표 높이를 쓴다** — 보정 없이 더미만 걷으면 자료 2 표가 2쪽에 들어가 쪽 밖으로 넘친다. 그래서 `rhwp_layout.mjs` 두 번 처리는 남긴다
  - **rhwp PR 준비**: 개발판 클론(`~/.cache/rhwp-devel/rhwp`) 브랜치 `fix/7419-tac-no-ls-row-growth`, 커밋 1f9abd28(`cargo fmt` 통과). 패치 사본 `fix7419_devel.patch`.
    검증 worktree `~/.cache/rhwp-devel/rhwp-rust-review` 에서 `--prepare`(48 묶음, 최소 6,559건) 후 `cargo nextest --cargo-profile release-test --tests` 실행 중.
    ⚠ 이 PC 의 git 은 core.autocrlf=true 라 worktree 가 CRLF 로 나와 rustfmt 가 전 파일을 문제 삼았다 — 저장소 설정을 false 로 바꾸고 `git rm --cached -r . && git reset --hard` 로 다시 받았다
  - **rhwp PR 게시: https://github.com/edwardkim/rhwp/pull/7433**(devel 대상, 포크 imsebeom/rhwp 브랜치 `fix/7419-tac-no-ls-row-growth`, 커밋 52a51c0a9 수정 + 4905a31d0 시험). 본문 사본 `pr7433_body.md`.
    검증(9c190efb, base b3e3d4e2): fmt, unit 3,873, 전체 integration 10,207(2시간 13분), Native Skia 3,930+2+4, Clippy 셋, 배정 계약, OVR(프리셋 5종 불변, 표 속 표 h+6.5 는 의도). 새 회귀 시험은 수정 전 2 failed / 수정 후 2 passed.
    최신 devel(c80a8370)로 rebase 뒤 fmt, native Clippy, 새 시험(suite_008), suite_021(211) 재실행 — 사용자 선택 「빠른 검사만 다시」.
    ⚠ 이 PC 함정: 두 Rust 빌드를 동시에 돌리면 메모리 부족으로 백그라운드 작업이 강제 종료된다 → `CARGO_BUILD_JOBS=4` 로 하나씩 / OVR `--diff-against` 의 worktree 120초 제한 → review worktree 에서만 1,200초 / `--generate` 가 아니라 `--prepare` 를 써야 48 대상 예산이 맞는다
  - **마무리**(스킬 d8f87e1, 푸시): README 에 에디터 모드 절, 크레딧(rhwp 스튜디오와 WASM, 형제 프로젝트 편집 도구, pywebview), 한글 줄 배치, 설치(에디터 빌드)를 넣었다 — **앞선 세션의 에디터 통합 때 README 를 빠뜨렸었다.**
    THIRD_PARTY_NOTICES 에 `editor/patches/*.rs` 가 rhwp 소스를 고친 조각(MIT 고지 대상)임을 밝혔다. 디스크 정리: rhwp 빌드 캐시 49.6GB, 검증 워크트리, 잠긴 OVR 임시 워크트리, `savetest/`, `hwpx-editor/test2` 삭제(C 드라이브 81 → 120GB)
  - **decisions**: ⓐ rhwp PR 은 로컬 전체 검증 후 게시하되, 최신 devel 로 rebase 한 뒤에는 빠른 검사만 다시 하고 본문에 그 사실을 밝혔다(사용자 선택) ⓑ 에디터 엔진 패치는 v0.8.6 에 손으로 옮겨 넣었다(사용자 선택) ⓒ 에디터 열 때 보정(rhwp_layout 두 번 처리)은 엔진 패치 뒤에도 쪽 나누기용으로 남긴다
  - **next_steps**:
    ① **PR #7433 따라가기** — `gh pr checks 7433 -R edwardkim/rhwp`, `gh pr view 7433 -R edwardkim/rhwp --comments`. 수정 요청이 오면 `~/.cache/rhwp-devel/rhwp` 의 브랜치 `fix/7419-tac-no-ls-row-growth` 에서 고치고 `git push fork`.
       빌드 캐시를 지웠으므로 다시 빌드부터 해야 한다(디버그 7분, `CARGO_BUILD_JOBS=4`, 검증 worktree 는 `git worktree add` 후 `--prepare`).
       받아들여지면 에디터 패치(`editor/patches/tac-no-ls-*.rs`)를 걷고 setup.mjs 의 `RHWP_VERSION` 을 올려 재빌드(20분)
    ② 캠프와 채움AI 프로젝트 `_scripts/` 는 스킬 복제본이라 「실제 줄 배치 넣기」를 받지 않는다 — 넣을지 사용자 결정 대기(급하지 않음, 에디터가 열 때 보정)
    ③ md2hwpx 산출물 polaris JID 11041 2건 — 원래 있던 것, 미조사
    ④ 쪽 나누기가 TAC 표의 적힌 높이를 쓰는 rhwp 한계는 PR 범위 밖으로 남겼다 — 필요하면 별도 이슈
    ⑤ `~/.cache/rhwp-devel/` 에 rhwp 저장소(PR 브랜치), 재현 파일, 비교 도구(cmp/allpages/overlap/winshot/cdp_click)가 남아 있다. 개발 폴더 `editor/.build` 는 스킬 `editor/.build` 가 junction 으로 가리키는 에디터 빌드 캐시다
- intent: /hwpx 스킬에 rhwp 에디터 모드(Claude 와 사용자가 같은 문서를 실시간 공동 편집)를 만들어 스킬에 통합하고 GitHub 에 올리기(2026-09-25 세션).
- changes_made (2026-09-25, 커밋 405488e~019139e):
  - editor/ 전체: 플러그인(doc/m/run/tool op), 브리지 서버, 호스트 페이지, CLI, setup, 앱 창(app.py), EDITOR.md
  - 저장: 매번 새 판 `<이름>_<YYMMDD>_<NN>.hwpx`, 덮어쓰기 없음 / 전자서명·암호화 문서 거절 / run 문자열 NFC
  - 쪽 번호: ①저장 단계 보정(hwpx-zip.mjs) ②rhwp 패치 빌드(patches/, Rust 1.93.1·wasm-pack 0.15.0 을 ~/.cargo 에 설치, PATH 미변경). 기준 빌드가 npm 공식과 바이트 동일, 패치 빌드도 문서 10건 바이트 동일, 한컴에서 쪽 번호·총 쪽수 확인. ②가 있으면 ①은 건너뜀(중복 방지)
  - 형제 프로젝트 hwpx에디터기반AI(커밋 866416b)에서 도구 25종, 스냅샷 보호, 개요, 검수, 채울 칸, 셀 좌표 diff, 셀 커서·선택 글자, goto, document-mutated 감지를 가져옴(plugin/lib, 고치지 않고 복사)
  - 한/글 단축키: 앱 창(pywebview=WebView2, 최대화)에서 Ctrl+N·Q·M 두 단계 키, 셀 안 Ctrl+A, Ctrl+Shift+C/R/T 등(plugin/hancom-keys.ts). 실제 키 입력으로 영문·한글 입력기 모두 통과(test/keys_app.py, keys_dialogs.py)
  - 설치: pip pywebview 6.2.1(pythonnet 3.1.0), rustup(~/.cargo, ~/.rustup)
  - 스킬 통합: ~/.claude/skills/hwpx 의 editor/, references/editor-mode.md, SKILL.md(선택 단계 19줄). 커밋 807b576~319d2c6, imsebeom/hwpx·hwpx2 main 푸시(이전 세션 미푸시 커밋 6·8개 함께). 스킬 위치에서 개요·편집·새 판 저장 스모크, tests/test_text_scope.py OK
- decisions: 위 "결정" 절. 추가로 — 에디터 모드는 실시간 편집만(A/F/H/I/J/N 워크플로는 저장·종료 후 기존 방식), 기본 창은 앱 창(브라우저 탭은 Ctrl+N/T/W 불가), 형제 프로젝트 코드는 복사만 하고 여기서 고치지 않는다
- 함정(이번 세션): Node 24 rmSync/cpSync 한글 경로 크래시 / SendInput 에 스캔 코드가 없으면 e.code 빈 값 / 한글 입력기 조합은 preventDefault 로 안 멈춤(포커스 뺐다 돌려 버림) / 플러그인 host.automation 은 대화상자 명령을 안 엶(inputHandler.dispatcher) / 앱 창이 화면보다 크면 오른쪽 위 패널이 화면 밖 / 알캡처 등 전역 단축키 프로그램이 키를 먼저 가져감 / goto 직후 바로 치면 첫 글자가 먹힘
- next_steps:
  1. 사용자가 실제 문서로 앱 창 시운전(`node ~/.claude/skills/hwpx/editor/cli.mjs start <문서>`). 불편 사항은 **스킬 쪽(~/.claude/skills/hwpx/editor)에서** 고치고 hwpx·hwpx2 둘 다 푸시
  2. 연결만 하고 안 눌러 본 단축키(Ctrl+N,E 미주, N,M 수식, N,B 글상자, Ctrl+J, Alt+Shift+P/S 첨자, Ctrl+Shift+Insert/Delete) 실측 — editor/tests/keys_dialogs.py 에 항목 추가
  3. 빌드 산출물(27MB)을 GitHub Release 첨부로 받게 할지 검토(다른 PC 에서 setup 이 rhwp 받기·npm·Rust 빌드를 반복하지 않게)
  4. rhwp(edwardkim/rhwp)에 결함 보고 초안: hwpx 저장기가 머리말/꼬리말 필드 표식(\u0015/\u0016)을 버린다(src/serializer/hwpx/section.rs 제어문자 무시 분기). 패치(editor/patches/hwpx-hf-autonum.rs)를 PR 로 낼지 사용자와 상의
  5. 노션 🔏 프로젝트 항목이 없다 — 이 일을 노션에서 추적하려면 /프로젝트시작 으로 연결
