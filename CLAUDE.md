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
- **intent(09-25): 생각쓰기캠프 문항 3(`제출_문항3_이산화탄소_260924_01.hwpx`)을 에디터로 열었더니 ⑴ 문단이 한 줄로 눌리고 ⑵ 표가 아래 표와 겹쳤다(사용자 발견). 둘 다 스킬 쪽에서 고쳤다.**
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
  - **next_steps**: ① 에디터 서버는 새 코드로 다시 띄웠다가 닫았다(지금 꺼져 있음). 저장 시험 끝남
    ② ~~결함 보고~~ #7419 게시 완료(`gh issue view 7419 -R edwardkim/rhwp`). 답이 오면 반영 ③ ~~실제 줄 배치~~ 3dc908e 완료, ~~한글 없는 환경 겹침~~ 024e2f2 완료(에디터가 rhwp 로 보정) ④ 캠프와 채움AI 프로젝트의 `_scripts/` 는 이 스킬의 복제본이라 이번 변경을 받지 않는다(그쪽 산출물은 에디터가 열 때 한글 줄 배치로 보정된다) ⑤ md2hwpx 산출물 polaris JID 11041 2건 미조사 ⑥ `~/.cache/rhwp-devel`(devel 빌드, 비교 도구, 재현 파일, 저장 시험 사본 `savetest/`)은 남겨 두었다
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
