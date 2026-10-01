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
- **10-02 둘째**: 사용자 화면 「그림이 엉뚱한 데 가 있고 문단이 다 어그러짐」(아궁이 문항카드, <자료 1> 그림을 <자료 2> 여러 줄 문단 끝으로 옮김) → 스킬 6eb9ff3. 원인 셋: 줄 나누기가 문단 끝 글자처럼 취급 개체 높이를 첫 줄에 붙임(`tac-end-line`), 칸 붙여넣기, 그림 넣기 뒤 칸 안 뒤 문단 vpos 안 매김(`cell-paste-vpos`, `cell-pic-nested`), 표 높이 맞추기가 맨 바깥 표만 다뤄 표 속 표가 비례 축소(`tac-nested-sync`). 한글 PDF 와 같은 모양, `cargo test --lib` 3,889 통과
  - 🔴 **사고**: 시험 스크립트가 시작 전마다 `stop --force` 했는데, cli 는 stop 이 포트 파일을 지운 인스턴스에 기본 포트 7780 으로 명령을 보냈다 → 교육력제고 실적 창(60ded568)의 서버를 내렸고, 그 창이 내 시험 서버에 붙어 `save` 가 그 문서를 내보냈다(scratchpad m5.hwpx, 그 창 내용 사본). 60ded568 서버를 `hold` 로 다시 띄워 창이 붙음(dirty false, 6쪽). 스킬 b732cb2: 그 포트 서버의 stateDir 이 이 인스턴스가 아니면 stop 은 아무것도 안 내리고 다른 명령은 멈춘다
  - 이산화탄소(card3), 아궁이(card2) 창은 각각 언제인가 닫혔다(창 프로세스 없음, card2 는 02:10 종료 기록). 내가 닫은 흔적은 못 찾음. 아궁이는 새 빌드로 다시 열었다(card2, 7781)
  - 다른 세션이 스킬에서 한글 COM 의존을 걷어 냄(85bab48, `scripts/hidden_desktop.py` 삭제). 한글 PDF 확인은 지운 판을 scratchpad 에 꺼내 썼다
  - 푸시: 스킬 b732cb2 까지 hwpx, hwpx2(hwpx2 에는 다른 세션의 85bab48, c238ea9 도 함께)
  - next_steps: ① 사용자가 아궁이 문항카드(card2, 7781)로 표 속 표, 칸 그림 조작을 다시 써 보고 남은 결함을 알려 주면 그것부터 ② 시험 도구는 scratchpad `run_agung.sh`(mv|place), `mouse.mjs`(CDP 9333 실제 마우스), `shot.mjs`, `place.sh` — 시험 인스턴스는 nesttest, 띄울 때 `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9333` ③ 한글 PDF 대조는 스킬에서 hidden_desktop.py 가 빠졌으니 `git show 85bab48^:scripts/hidden_desktop.py` 로 꺼내 쓴다
- **10-02**: 사용자 보고 둘 ① 「표 속 표는 클릭, 크기 조절 등 마우스로 할 수 없다」 ② 「표 속, 표 속 표 속 그림의 삽입, 크기 조절, 이동이 안 된다」 → 스킬 6149e29, 9b705eb. 설명은 `references/editor-mode.md` 6절 두 항목
  - ①: 상류 devel #7214(9/17, #7237 통합에 섞임), #7442(9/27)를 v0.8.6 에 옮김. 엔진 `nested-table-hit/-path/-wasm.rs`(경로 크기 조절은 thread_local 로 대상 표만 바꿔 끼워 row-resize-th 와 공존), 스튜디오 `nested-table-*.ts` 6개, 플러그인 `installTableClickSelect` 가 경로를 버리던 것. 상류에 없는 보완: 안쪽 표 테두리 바깥쪽 0.5px 부터 hitTest 가 바깥 칸이라 둘레 ±4px 를 찔러 판정
  - ②: 그림 넣기, 파일 끌어 놓기가 칸이면 본문의 떠 있는 그림(표 위에 얹힘)으로 들어가던 것 → 칸 문단 안 글자처럼 취급(`cell-pic-place/-drop.ts`, 표 속 표 칸 줄 배치 `cell-pic-nested.rs`). 칸 안 글자처럼 취급 그림은 끌기가 시작조차 안 되던 것 → 놓은 글자 자리로 잘라 붙이기(`cell-pic-move*.ts`, `convertCaretOffset` 모드 7 `cell-pic-caret*.rs`). 크기 조절은 원래 됐다
  - 🔑 결정(사용자 확인 「그래」): 칸에 그림을 넣으면 「글자처럼 취급」으로 칸 안에 넣는다(한글 기본 동작 기준). 상류 #1151 의 「표 옆 떠 있는 그림(종이 기준)」은 따르지 않는다
  - 푸시: 스킬 9b705eb 까지 hwpx, hwpx2. 다른 세션(에디터 외 작업, 사용자가 「참고하라」고 알림)의 커밋 5371e78 과 hwpx2 쪽 a20fe18..68b44df 도 함께 올라갔다
  - 검증: 문항카드 사본과 상류 시험 문서(18×9 표 속 표)로 CDP 실제 마우스, 되돌리기, 저장본 verify 통과, 한글 PDF 4쪽 같은 모양, `cargo test --lib` 3,889 통과
  - 🔴 시험 도구 함정: scratchpad `mouse.mjs` 가 한 점 클릭에서 x2 가 undefined 라 NaN 좌표로 이동, 놓기를 보내 CDP 가 거절 → mouseup 이 안 와 텍스트 선택 끌기가 남았다. 한동안 이것을 에디터 결함으로 오해했다(`Number.isNaN(undefined)` 은 false). CDP 응답의 error 를 찍게 고쳤다
  - 🔑 스킬 저장소는 다른 세션도 커밋하므로 푸시 전에 `git log <원격>/main..HEAD` 로 남의 커밋이 섞였는지 보고 알린다
- **09-30 ~ 10-01**: 한국문화 1단원 마지막 쪽 그림이 두 번 보이던 것(사용자 보고) → 스킬 43de199(푸시 안 함) `patches/cell-pic-split-dup.rs`.
  원인은 rhwp `table_partial.rs`(쪽을 넘는 표): ① 문단 끝 글자처럼 취급 그림이 `abs_pos < line_chars` 판정에 빠져 칸 왼쪽에 덧그려짐 — devel d5fbe8b5d(#7171)가 이미 같은 방식(`get_inline_shape_position`)으로 고침
  ② 문단이 쪽 경계에서 갈라져 그림 줄이 뒷조각에 있으면 앞조각도 그림 — devel 09-25 빌드에도 남음(재현 scratchpad `mkrepro.py` 채움 34줄). 원본 npm 0.8.6 에서도 재현, 우리 패치 탓 아님
  - 🔴 setup 은 패치 id 목록(`pkg/.claude-patched`)이 같으면 WASM 을 다시 빌드하지 않는다 — 이미 들어간 패치 내용만 고쳤으면 그 파일을 지우고 돌린다
  - 검증: 교재 폴더와 시험 문서 40개를 기준 WASM 과 대조, 1단원 두 판의 덧그림 2개만 빠짐. `cargo test --lib` 3,889 통과
  - ②번은 devel b19eb36c4 빌드(`~/.cache/rhwp-devel/latest`, worktree)에서도 재현 → **rhwp 이슈 #7492** 게시(재현 파일 base64, md5 dec6c6d4, 원인 줄 번호, 제안 코드)
  - 사용자 요청 「에디터가 닫힐 때 가상서버도 종료」 → 스킬 723d704: app.py 가 창이 닫혀 webview.start 가 돌아오면 서버에 shutdown. 시험 인스턴스 WM_CLOSE(scratchpad `closewin.py`)로 3초 안 종료 확인
  - 사용자 지시로 창 없이 남아 있던 서버를 모두 닫았다(5d5551bf 7780 은 `stop`, 342dcfbb 7782 는 이미 내려가 있었음). 떠 있는 에디터 없음
  - next_steps: ① `gh issue view 7492 -R edwardkim/rhwp --comments`(#7484 도) 답 확인. 받아들여져 릴리스되면 `patches/cell-pic-split-dup.rs` 를 걷는다 ② 스킬 43de199, 723d704 를 hwpx, hwpx2 에 푸시할지 사용자에게 묻기 ③ `~/.cache/rhwp-devel/latest`(devel b19eb36c4 worktree)는 이슈 확인용이라 필요 없으면 `git worktree remove`
- **09-29 ~ 09-30 밤샘(사용자 지시 「다른 사례들도 다 옮겨가면서 문제 해결해봐」)**: 떠 있는 그림 끌기, 옮기기 결함을 사례 대조로 잡았다. 스킬 5e17116..abea249(푸시 안 함)
  - 사용자가 찾은 것: 자리 차지 그림 한 문단 내리면 빈 자리(`move-float-line`), 어울림 그림 옮기면 겹침(`move-band`, `move-release-band`, `wrap-band-host-ladder`), 7쪽 끄는 방향 반대(`wrap-move-sign.ts`), 2쪽 아래 문단까지 끌면 겹침(`wrap-band-page-end`, `wrap-split-follower`)
  - 대조로 찾은 것: 거리/정렬을 바깥 여백 상자로(`wrap-margin-box`), 속성 변경 전 옛 띠 기억(`wrap-props-release`), 빈 문단 자리 차지는 띠 제외(`wrap-tab-empty-host`), 쪽 기준 그림을 제 문단 위로 올리면 앞 문단도 비킴(`wrap-band-backward*`), **저장본을 다시 열면 겹침**(`wrap-save-mark` 편집 줄에 비트 30 표시 + `wrap-save-band` 저장기가 표시 줄을 비트 떼고 남김)
  - setup.mjs: 여러 조각 패치를 한 묶음으로(첫 조각 표식으로 판단 — 조각마다 판단하면 뒤 패치가 앞 패치 코드를 고쳐 쓸 때 멈추거나 두 번 넣었다), 스튜디오 패치 루프가 파일 여럿을 받게
  - 🔑 **대조 방법**(scratchpad `wrap/`): `scen.py`(101개 시나리오: 옮기기, 세로/가로 거리, 되돌리기, 타이핑) → `claude_wrap_ops` 예제(편집 세션 SVG + 내보낸 hwpx) → `hancom_batch.py`(한글 재조판 hwpx, PDF) → rhwp 로 한글 재조판본을 그려 `compare.py`(글줄 위치, 그림 위치). 저장 왕복은 `reopen.py`. 실제 창은 `livedrag.py <포트> <쪽> <dx> <dy>`(CDP 실제 마우스)
  - 결과: 한글 대조 불일치 40 → 5, 저장 왕복 7 → 4, 남은 것은 모두 **음수 세로 거리**(한글은 쪽 영역 제한 켜진 문단 기준 그림을 문단 윗변에 붙이는데 rhwp 는 음수대로 그린다 — 누르는 패치를 넣었다가 c4 규격서 23쪽이 나빠져 걷었다. 끌기는 0 아래로 못 가게 막음). 줄 끝 글자 차이(위치 같음)는 글꼴 폭 차이
  - 검증: `cargo test --lib` 3,889 통과, 실사용 8개 문서 열기 SVG 불변, 실제 창 8번 끌고 저장 → 다시 연 화면이 한글 재조판과 9쪽 모두 위치 일치, 줄을 남긴 저장본 10건 한글 PDF 동일
  - 함정: Bash heredoc 으로 `\n` 든 JS 를 넣다 또 두 번 깨졌다(규칙대로 Edit/Write). 글 뒤로 그림은 글 위에서 누르면 글 선택이 우선(한글과 같음)
  - 사용자 에디터: 새 엔진으로 `그림배치_시험5.hwpx` 를 띄워 둠(포트 7781)
  - 마무리: 스킬 abea249 까지 hwpx, hwpx2 푸시. #7484 에 추가 결함 7가지 댓글(issuecomment-5903814791, devel 0e8fd49fb 줄 번호). 사용자 지시로 에디터 서버 둘과 로컬 http.server 5178 을 닫음(MCP 서버와 다른 세션의 firebase 배포는 둠)
  - next_steps: ① #7484 답 확인 ② 음수 세로 거리 규칙(한글은 언제 누르나) 조사 ④ 여러 개 선택 끌기의 오른쪽 정렬 부호
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
  - 남은 것: ① 한글은 그림을 바깥 여백(보통 1mm)만큼 안쪽에 그리는데 rhwp 는 여백 없이 그려 모든 비TAC 그림이 3.8px 높다(표, 도형 공용 계산이라 범위 밖) ② 줄 배치 없는 문서(한글을 안 거친 산출물)를 열 때의 어울림은 손대지 않음(에디터 서버가 한글 줄 배치로 보정) ③ `.build/rhwp/pkg-base`(기준 WASM) 삭제가 권한에 막혀 남아 있음
  - 마무리: 스킬 f082aa1..4f48723 을 hwpx, hwpx2 에 푸시. **rhwp 이슈 #7484** 게시(재현 파일 base64 포함, md5 074e1ca4 대조, 원인 7가지와 devel 0e8fd49fb 줄 번호, 우회 패치 링크, 관련 #7282 #6970 #7481).
    게시 전 기준 WASM(`pkg-base`)으로 재현 파일이 결함을 내는지 확인: 왼쪽/오른쪽/쪽 기준 조각 20, 18 → 15, `replaceBodyTextLocal` 18 → 15. 본문 사본 scratchpad `wrap/issue_body.md`
  - next_steps: `gh issue view 7484 -R edwardkim/rhwp --comments` 로 답 확인. 받아들여져 릴리스되면 `patches/wrap-*` 를 걷고 RHWP_VERSION 올려 재빌드
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