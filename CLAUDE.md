# hwpx 에디터 기반 에이전트 스킬

`/hwpx` 스킬(`~/.claude/skills/hwpx`, 저장소 imsebeom/hwpx2)에 rhwp 에디터 모드를 붙이는 개발 폴더.
사용자는 브라우저의 rhwp 에디터로 문서를 보고, 터미널 Claude 가 같은 문서를 실시간으로 고친다.
완성되면 `editor/` 를 스킬의 `editor/` 로 옮기고 SKILL.md 에 선택 단계를 넣는다.

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

## 컨텍스트 앵커
- intent: /hwpx 스킬에 rhwp 에디터 모드(Claude 와 사용자가 같은 문서를 실시간 공동 편집) 추가. 2026-09-25 한 세션에서 구현부터 한/글 단축키까지.
- changes_made (2026-09-25, 커밋 405488e~019139e):
  - editor/ 전체: 플러그인(doc/m/run/tool op), 브리지 서버, 호스트 페이지, CLI, setup, 앱 창(app.py), EDITOR.md
  - 저장: 매번 새 판 `<이름>_<YYMMDD>_<NN>.hwpx`, 덮어쓰기 없음 / 전자서명·암호화 문서 거절 / run 문자열 NFC
  - 쪽 번호: ①저장 단계 보정(hwpx-zip.mjs) ②rhwp 패치 빌드(patches/, Rust 1.93.1·wasm-pack 0.15.0 을 ~/.cargo 에 설치, PATH 미변경). 기준 빌드가 npm 공식과 바이트 동일, 패치 빌드도 문서 10건 바이트 동일, 한컴에서 쪽 번호·총 쪽수 확인. ②가 있으면 ①은 건너뜀(중복 방지)
  - 형제 프로젝트 hwpx에디터기반AI(커밋 866416b)에서 도구 25종, 스냅샷 보호, 개요, 검수, 채울 칸, 셀 좌표 diff, 셀 커서·선택 글자, goto, document-mutated 감지를 가져옴(plugin/lib, 고치지 않고 복사)
  - 한/글 단축키: 앱 창(pywebview=WebView2, 최대화)에서 Ctrl+N·Q·M 두 단계 키, 셀 안 Ctrl+A, Ctrl+Shift+C/R/T 등(plugin/hancom-keys.ts). 실제 키 입력으로 영문·한글 입력기 모두 통과(test/keys_app.py, keys_dialogs.py)
  - 설치: pip pywebview 6.2.1(pythonnet 3.1.0), rustup(~/.cargo, ~/.rustup)
- decisions: 위 "결정" 절. 추가로 — 에디터 모드는 실시간 편집만(A/F/H/I/J/N 워크플로는 저장·종료 후 기존 방식), 기본 창은 앱 창(브라우저 탭은 Ctrl+N/T/W 불가), 형제 프로젝트 코드는 복사만 하고 여기서 고치지 않는다
- 함정(이번 세션): Node 24 rmSync/cpSync 한글 경로 크래시 / SendInput 에 스캔 코드가 없으면 e.code 빈 값 / 한글 입력기 조합은 preventDefault 로 안 멈춤(포커스 뺐다 돌려 버림) / 플러그인 host.automation 은 대화상자 명령을 안 엶(inputHandler.dispatcher) / 앱 창이 화면보다 크면 오른쪽 위 패널이 화면 밖 / 알캡처 등 전역 단축키 프로그램이 키를 먼저 가져감 / goto 직후 바로 치면 첫 글자가 먹힘
- next_steps:
  1. 원격 저장소 연결 후 push (2026-09-25 요청, 원격 없음·gh 미로그인으로 보류)
  2. 사용자가 실제 문서로 앱 창 시운전(`node editor/cli.mjs start <문서>`), 불편 사항 반영
  3. 그 뒤 ~/.claude/skills/hwpx 로 옮기고 SKILL.md 에 "에디터로 보면서 작업할까요?" 단계 추가, 기존 tests 통과 확인. 빌드 산출물(27MB)은 저장소 대신 GitHub Release 첨부 검토
  4. 연결만 하고 안 눌러 본 단축키(미주, 수식, 글상자, Ctrl+J, 첨자 등) 실측
  5. rhwp 에 쪽 번호 필드 저장 누락 결함 보고(이슈 초안 작성 후 사용자가 게시)
