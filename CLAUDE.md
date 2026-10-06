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
- **10-05 둘째 ~ 10-06**: 사용자 보고 넷 → 스킬 6fa4f78, 892b48b, d55a0da, 릴리스 editor-ad1179241115(7c6bd72). 이어 사용자 「1, 2, 3 그래」, 「다 끝나면 푸시도 해라」 → 글꼴 폭 3671c82, 메모 bc4e3c6, ad74376, 릴리스 editor-89eadf817bad(26cab51). 이어 메모 스크립트 b37dcc4, 글꼴 파일 폭 표 읽기 56687c3, 2bfa8c0, 릴리스 editor-f40a3b201997(2445c9c), 표 속 표 번호 오인 3ac4ddc, 릴리스 editor-08b2ac806e2d(bea1cdb), 표 속 표 칸 그림 크기 조절 47a12ee, 릴리스 **editor-f9dd411d4321**(e29bcba 까지 hwpx, hwpx2 푸시, 새 사본 설치 확인)
  - ① 「표 안에서 Alt+Shift+A/Z 줄 간격이 안 된다」(6fa4f78): 플러그인 칸 Ctrl+A 가 1단 칸에서 `cellPath[0].cellParaIndex` 를 누른 자리로 남겨, 문단 서식이 누른 문단 하나에만 들어가고 증감 키가 매번 같은 값을 넣었다. 🔑 `cli goto`, 방향키 커서는 cellPath 가 비어 재현 안 됨 — **마우스 클릭**(CDP)으로 놓는다
  - ② 「문항카드가 에디터에서만 깨져 보인다」(892b48b): 엔진 `cell-load-inline`(RowBreak 표 보강 줄이 한 줄 문단의 끝 글자를 밀던 것, 표 안 표의 그림 문단 높이 0) + `rhwp_layout.mjs`(칸 안 표 높이도 잼, 줄 배치가 섞인 칸은 걷음, 본문 표 상자를 그 표의 쪽 범위로만 받음 — 엔진 `getTableCellBboxes` 가 (문단, 컨트롤) 번호가 같은 **다른 표 속의 표**까지 집는다)
  - ③ 「가정통신문 4학년, 5학년이 한글과 쪽 구성이 다르다, 원인 해결」(d55a0da). 🔑 **한/글의 조판 단위는 4 HWPUNIT(1/1800 인치)다.** 실측으로 확정한 규칙과 패치:
    - `hancom-quantum`: 글자 폭 = 장평 100% 면 반올림, 아니면 (폭 x 장평) 버림. 띄어쓰기 = 반 칸 버림(장평이면 곱해 반올림). 자간 = 그 글자 폭의 % 반올림(줄 끝 글자 것은 안 셈). 허용치 0
    - `char-kinsoku`: 글자 단위 줄 나눔에서도 줄 머리 금칙 문자를 앞 글자와 묶음. `bullet-advance`: 글머리표 자리 = 반올림(글머리 칸[전각 em, ASCII 는 em/2, 글꼴 실제 폭과 무관] + em x 본문과의 거리 %) + 너비 보정, 자동 내어쓰기면 모든 줄
    - `line-spacing-quantum`: 줄 간격 4 단위 반올림(9pt 130% = 272). `affectLSpacing="1"` 인 글자처럼 취급 개체 줄은 줄 간격 % 를 **개체 높이**에 건다(5학년 문서 원인: 107% 문단의 머리 표 아래 584). `cell-trailing-ls-synth`: 줄 기록 없는 문단은 TAC 표 여러 문단 칸에서도 칸 마지막 줄 간격 제외
    - 검증: 한/글 재저장 317개 문단 51,813개 줄 나눔 일치 95.05 → 96.69%, 쪽수 일치 292 → 294(멀어짐 0), `cargo test --lib` 3,889 통과
  - ④ 「에디터에서 메모 볼 수 있나」 → 만들었다(bc4e3c6, ad74376). 엔진 `getMemoList`(`patches/memo-list*.rs` — 본문, 작성자, 일시, 걸린 글 범위. `getFieldList` 는 문단을 넘는 메모를 빠뜨린다), 플러그인 `memo-panel.ts`(오른쪽 패널, 걸린 글 노란 바탕과 번호 표, 누르면 이동, 메모가 있으면 저절로 열림), `cli memos [번호]`. 읽기만 한다
    - 🔴 **한/글은 메모 필드 `zorder` 가 메모 번호와 같아야 끝 표식(fieldEnd)을 남긴다.** rhwp 저장기가 이 속성을 안 써 에디터 저장본을 한/글로 열면 메모 13개가 범위를 모두 잃었다 → `memo-zorder`(변형 시험: 없음, 0, 99 는 사라짐. metaTag, 본문 문단 id 는 무관)
    - 🔴 **워크플로 N(`add_review_memo.py`, python-hwpx)이 만든 메모는 한/글에서 본문 대신 메모 id 숫자가 보인다.** 본문을 구역 끝 `<hp:memogroup>` 에 두는데 한/글은 읽지 않는다(다시 저장하면 사라짐). 에디터는 `memogroup-read` 로 읽어 같은 id 의 메모에 붙이고, 저장하면 한/글 모양으로 나간다(한/글 재저장에서 본문 유지 확인).
      사용자 「고쳐」 → 스킬 **b37dcc4(푸시 안 함)**: `add_review_memo.py` 가 저장 뒤 `memos_to_hancom_shape` 로 한/글 모양으로 바꾼다(본문을 subList 로, 번호는 기존 메모 다음부터, zorder = Number, fieldid 623209829, Command FILETIME, 「메모」 스타일). 고치기 전 산출물은 한/글 재저장에서 본문이 숫자로, 끝 표식 0개였다
    - 🔴 같은 스크립트의 `paragraph_text` 는 찾기가 아니었다 — python-hwpx 인자는 **문서 끝에 그 글로 새 문단을 만든다**. 그 글이 든 첫 문단(표 칸 안 포함)을 찾아 걸게 고쳤다
    - 🔴 **한/글은 메모 작성자를 Command 의 작성자 칸에서 읽는다**(Author 매개변수는 거기서 다시 만든다). 그 칸의 `: ; \ ? |` 는 메모 매개변수를 통째로 깨뜨리고 `/` 는 이름을 자른다. 글자, 숫자, 공백과 `. , ( ) & = ' " ! @ * % + ~ - _` 는 안전(변형 시험 `test/memo/cmd_var.py`)
    - 한/글 `CreateDateTime` 의 Z 는 지역 시각이다(FILETIME 과 9시간 차). `.hwp` 메모 본문은 rhwp 가 안 읽는다. 도구와 결과 `test/memo/`
  - ⑤ 글꼴 폭과 최소 공백(3671c82): `font-metrics-extra`(한컴산뜻돋움, 한컴 고딕, 나눔스퀘어의 hmtx 폭. 생성기 `test/linebreak/gen_font_patch.py`, 사다리 84건 일치), `condense-pull`(쪼개지는 낱말은 공백을 줄여 마저 담고, 새 낱말 첫 토큰은 「바로 앞 띄어쓰기를 뺀 줄 내용」이 자연 폭 안일 때만 담는다).
    줄 나눔 일치 96.69 → **97.99%**(한컴산뜻돋움 12.9 → 4.1%, 나눔스퀘어 17.7 → 0.9%), 쪽수 일치 294 → **295**(멀어짐 0), `cargo test --lib` 3,889, 원고 세 개 편집 흐름 실패 0(넷째 문서의 실패 25건은 직전 릴리스 엔진에서도 같다 — 전처리 없는 생성기 줄 배치)
  - ⑥ 사용자 「한/글은 실제 글꼴 폭 표를 읽는다 → 에디터도 그러면 근원 해결 아닌가」, 「그래」 → **설치된 글꼴 파일에서 폭 표 읽기**(스킬 56687c3, 2bfa8c0, 릴리스 **editor-f40a3b201997**, 2445c9c 까지 hwpx, hwpx2 푸시 — 메모 스크립트 b37dcc4 포함).
    엔진 패치 `font-metrics-runtime`(실행 중 등록 저장소, **내장 표에 없는 이름만** 찾는다. `registerFontMetrics`, `hasBuiltinFontMetric`) + `editor/font-metrics.mjs`(글꼴 폴더 색인[시스템, 사용자, 🔑 **한/글 자기 폴더 `HNC\…\Shared\TTF`** — HY크리스탈M, 한컴 윤고딕은 여기에만 있다], 이름표로 맞춤, cmap 4/12 + hmtx 읽기, 의존성 없음) + 서버 `/api/doc` 가 폭 표를 함께 보내고 호스트가 문서를 열기 전에 등록, `rhwp_layout` 도 같은 표 등록.
    검증: 읽은 폭이 fontTools 와 17개 얼굴 30만 자 모두 같음, 대조 문서에서 표 없던 30종 등록 → 고침 5 망침 0(97.99 → 98.00%), HY엽서M 문단 다시 나누기 [0,50] → [0,49](한/글과 같음, 화면 쪽 엔진도), 쪽수 직전 빌드와 같음(295, 달라진 문서 0), 3,889 통과.
    🔑 이 문서 묶음에서 표 없는 글꼴은 글자의 0.4%(설치됨) + 0.4%(미설치)뿐이라 숫자는 작다(엔진 조회로 셈: 33종이 글자의 99.2%). 값어치는 새 글꼴 문서에서 표를 빌드에 안 넣어도 되는 것. HY엽서M 에 남은 10건은 폭이 아니라 「'26.○.○.」 기호 줄 나눔 규칙
    한계: 화면 「파일 > 열기」와 `.hwp` 는 등록을 안 거침, `.hft` 못 읽음, 미설치 글꼴은 한/글의 대체 글꼴 규칙을 모름. 내장 표보다 설치된 파일을 우선하는 것은 안 했다(회귀 확인 뒤 따로 정할 일)
  - ⑦ 사용자 「메모 열었을 때 그림이나 표 개체 선택에 문제는 없었나」 → 시험 안 했었다. 보이지 않는 크로미움(`test/objselect/`)으로 패널 열림/닫힘 네 번씩 비교: 그림, 본문 표, 칸 커서 모두 같음(**메모 영향 없음**). 그러다 **메모와 무관한 결함** 발견: 3쪽 본문 표를 고르면 2쪽 그래프 상자(표 속 표)에도 선택 상자가 생기고 그 안의 그림이 눌리지 않음 → 사용자 「그래 고쳐라」 → 스킬 3ac4ddc, 릴리스 **editor-08b2ac806e2d**(bea1cdb 까지 hwpx, hwpx2 푸시, 새 사본 3초 설치 확인).
    원인: 번호(구역, 문단, 컨트롤) 조회(`getTableBBoxAtPage`, `getTableCellBboxes`, 칸 커서)가 그리기 나무에서 표 속 표도 같은 번호로 집음(표 속 표는 칸 안 문단 번호 — 둘 다 문단 7, 컨트롤 0). 패치 `nested-table-skip-*`: `TableNode.cell_context` 가 None 인 최외곽 표만 맞춘다. rhwp_layout.mjs 의 쪽 범위 우회(10-05)도 같은 뿌리였다
    🔑 시험 함정: 문서를 연 직후 첫 바퀴 결과가 흔들린다(두 바퀴 이상). CDP 클릭이 헤드리스 크로미움에서는 rhwp 클릭 처리에 닿는다(앱 창의 옛 메모와 다름). 미확인: 깊이 3 표 속 표의 왼쪽 선 클릭이 바깥 칸 커서로 떨어짐(전후 같음, 좌표 허용 범위 문제일 수 있음)
  - ⑧ 사용자 보고(새 빌드 창에서) 「표 속의 이미지 크기 줄였을 때 표의 크기 자동 조절이나 다음 단락 위치 조정이 안 된다」 → 스킬 47a12ee, 릴리스 **editor-f9dd411d4321**(e29bcba 까지 hwpx, hwpx2 푸시, 새 사본 3초 설치 확인). 도구 `test/picresize/`.
    원인 둘: ① 경로 판 그림 속성 설정(`setCellPicturePropertiesByPath`)의 줄 다시 나누기 보정(09-28 `cell-pic-delta`)이 1단 칸에만 → `cell-pic-resize-nested`(칸 문단 다시 나누기, 뒤 문단 위치, 안쪽 표 다시 재기 직접 호출) ② `tac-nested-sync` 가 쪽 나누기 앞 맞춤에서 **글자처럼 취급 바깥 표에만** 불려, 문항카드처럼 바깥 표가 쪽 크기 상자(글자처럼 취급 아님)면 그림을 줄이거나 글을 지워도 안쪽 표가 옛 높이 → `nested-sync-nontac`.
    🔑 한/글 기준은 그림 `hp:sz` 만 바꾼 사본을 재저장해 얻었다(안쪽 상자 24976 → 16378, 다음 문단 23694 → 15096, 바깥 표 그대로). 고친 엔진 218.4px = 16378 정확히 일치. 🔑 진단은 `CLAUDE_DBG` env 로 감싼 임시 eprintln 을 예제(`cargo run --example`)와 함께 썼다(걷었음). `claude_sync_dirty_tac_tables` 의 targets 가 비어 있던 것이 결정적 단서
    ⚠ 시험 함정: hold.py 포트를 그대로 7780 으로 돌려 **사용자 창 서버에 붙을 뻔했다**(memotest 가 7781 로 뜬 것을 못 봄). 시험 전에 `cli list` 로 포트를 확인한다
  - 🔑 측정 방법(`test/linebreak/`): **사다리** `wl.py`, `wlb.py` — 한 문서에 1×1 표 수천 개를 칸 폭 4 씩 바꿔 넣고 `hidden_desktop.py` + `hwp_resave_many.py` 로 한/글 재저장해 줄 수를 읽는다(폭 한 건 = 표 15개, 3천 개도 5분). **한/글 기준 사본** `hres_driver.py`(317개 재저장), 엔진 진단 `claude_lb_probe.rs`(line_breaking.rs 끝에 `#[cfg(test)] #[path] mod` 로 붙여 `CLAUDE_LB_FILES`, `CLAUDE_LB_VERBOSE`, `CLAUDE_LB_HEAD`, `CLAUDE_LB_ONE/KEY`), 분류 `resid2.py`, 쪽수 세 방향 `cmp3.py`
  - 🔑 함정: 대조 문서에 에디터 저장판이 섞이면 줄 기록이 rhwp 것이라 기준이 못 된다(한/글 재저장본만 기준). Git Bash `grep -c $'\r'` 는 CRLF 를 0 으로 센다(height_measurer.rs 는 CRLF — 파이썬 `newline=""` 로 본다). 진단 중 `cargo build` 가 디스크를 채워 `No space left` 가 한 번 났다(`.build` 16GB)
  - 🔑 함정(10-06): Bash heredoc 에 담은 파이썬 패치의 `\\n`, `\\d` 가 한 겹 풀려 실제 줄바꿈이 박혔다(호스트 CRLF 파일에서 우연히 멈춤) — 이스케이프가 든 수정은 Edit 도구로. `grep -v '[자바연]'` 은 바이트로 걸러 한글 줄을 다 지운다
  - 남은 원인(미해결): 번호 문단 표식 자리, 들여쓰기 첫 줄(약 255건), 칸 「한 줄로 입력」, 한컴바탕 글머리표 문단(12.1%), 휴먼명조 최소 공백 10건(한/글이 낱말 일부를 안 당김), 나눔스퀘어 한자 폭과 ㆍ(U+318D), 붙임표 연속과 `!` 폭, 그리는 쪽 글머리표 글 시작 x, 쪽수가 다른 문서 22개
  - next_steps: ① 사용자가 메모 보기, 개체 선택, 표 속 표 그림 크기 조절을 더 써 보고 알려 주는 결함부터(10-06 「좋아. 잘되네」까지 확인, 창은 닫힘) ② 미확인 둘: 깊이 3 표 속 표의 왼쪽 선 클릭이 바깥 칸 커서로 떨어짐(고치기 전후 같음, 좌표 허용 범위일 수 있음 — `test/objselect/`), 칸 끝 글자처럼 취급 **표**의 Ctrl+A(그런 칸이 있는 문서로) ③ 요청이 오면: `.hwp` 메모 본문 읽기(HWP5 MEMO_LIST), 미설치 글꼴의 한/글 대체 규칙, 설치 파일을 내장 표보다 우선할지, HY엽서M 「'26.○.○.」 기호 줄 나눔 10건 ④ rhwp 에 보고할 만한 것: 메모 zorder 누락, getFieldList 의 문단 넘는 메모 누락, 표 속 표 번호 조회 오인(bbox, cells, cursor 셋이 `cell_context` 를 안 봄), 비TAC 바깥 표 안쪽 표 높이 다시 재기 누락, 경로 판 그림 속성의 줄 다시 나누기 1단 칸 한정, affectLSpacing 무시, 4 단위 폭 ⑤ 이전 next_steps(rhwp 이슈 #7535~7537, #7492, #7484 답 확인 등)는 아래 10-03 블록
- **10-05**: 사용자 보고 「표 속 표에서 Ctrl+A 오작동」, 「표 속 글머리표가 글자인 듯 아닌 듯」 → 스킬 e3dc644, c5e53d3, b8508ae, 1508e9e, 릴리스 editor-c49ee314737f(3f75b05 까지 hwpx, hwpx2 푸시)
  - ① 플러그인 `selectCellContents` 가 표 속 표 칸(cellPath 2단 이상)을 rhwp 기본(문서 전체 선택)에 넘겨 커서가 문서 끝으로 튀었다 → `*ByPath` API 로 그 칸만 고른다(평평한 좌표는 바깥 칸 것이라 두고 경로 끝만 바꿈)
  - ② 엔진 패치 `sel-skip-marker`: 글머리표 런은 `char_start: None` 인데 `cursor_nav.rs` 선택 음영 두 곳이 `unwrap_or(0)` 으로 0번 글자로 셌다(캐럿은 건너뜀). 「과정」을 골라도 글머리표만 칠해지던 것 해결
  - 검증: 아궁이 문항카드 사본, `start --no-browser` + 보이지 않는 크로미움(CDP 9333, scratchpad `hold.py`, `cdp.mjs` 키, 클릭, 캡처). 1단 칸, 본문, 표 속 표 회귀 확인. `cargo test --lib` 3,889 통과
  - 사용자 「선택해 복사, 붙여넣기, 지우기도 잘 안 된다」 → 스킬 b8508ae 엔진 패치 `cell-caret-skip-marker`(`cursor_rect.rs` 1단 칸, 표 속 표 칸 캐럿 두 곳이 같은 `unwrap_or(0)`). 「• 」 런 때문에 0~2번 캐럿이 글머리표 위에 그려져 화면 캐럿이 실제 편집 위치보다 두 글자까지 앞섰다. 편집 자체는 바른 위치였다(Delete, 복사, 붙여넣기 실측)
  - 사용자 「끝 문단에 그림만 있어도 글자처럼 취급이면 선택돼야지. 표도」 → 스킬 1508e9e: 칸 Ctrl+A 끝을 `convertCaretOffset` mode 5(캐럿 축 길이)로. 표 속 표 칸의 끝 그림에 음영 확인, 1단 칸 Ctrl+A → 복사 → 지우기 → 붙여넣기 왕복 원문 그대로. ⚠ 칸 끝 글자처럼 취급 **표**는 시험 문서에 없어 실측하지 않았다(같은 길이 계산)
  - 남은 것: CLI `state` 의 `selectedText` 는 여러 문단 칸 선택을 빈 값으로 보인다
  - next_steps: ① 사용자가 guide3, guide4 를 저장 뒤 다시 열어 표 속 글머리표 편집을 써 보고 알려 주는 결함부터 ② 칸 끝 글자처럼 취급 표의 Ctrl+A 실측(그런 칸이 있는 문서로) ③ 그 밖의 남은 일은 10-03 블록 next_steps ①~⑤
- **10-04**: 사용자 보고 「한자 버튼이 작동되지 않는다」(한 글자 치고 바로 한자 키) → 스킬 216d5f7, 21d46ec, 릴리스 editor-9c8dbed2ac09(d7a5a54 까지 hwpx, hwpx2 푸시). 사용자가 실제 입력기로 확인 「이제 문제없군」
  - ① 후보 창이 안 보였다: rhwp 숨은 입력칸이 `left:-9999px` 라 입력기 후보 창도 화면 밖에 떴다 → 플러그인 `installImeAnchor` 가 키를 누를 때마다 입력칸을 캐럿(조합 중이면 조합 상자) 자리로 옮긴다(투명, 클릭 통과)
  - ② 그러자 「한韓」이 됐다. 시험 페이지(이벤트 기록)로 실측한 입력기 순서: 한자 키(이 PC 는 **오른쪽 Ctrl**, `code: ControlRight`) → compositionend 「한」 → deleteContentBackward → compositionstart → 「한」 → 「韓」 compositionend.
    rhwp 는 확정 때 입력칸을 비워 지우기가 문서에 닿지 않는다 → 한자 키 300ms 안의 확정 뒤 새 조합이 열리면 확정 글자 수만큼 `handleBackspace`
  - 검증: 보이지 않는 크로미움 + CDP `Input.imeSetComposition`/`insertText` 로 같은 순서 재현 → 「가韓」, 보통 입력 「가한글」 그대로. 시험 스크립트 scratchpad `ime_hanja.py`, `ime_trace/`
  - ⚠ 시험 중 cli 를 `HWPX_EDITOR_INSTANCE=imetest` 로 띄울 때 옛 port 파일을 읽어 엉뚱한 포트로 붙을 뻔했다 — 시험 인스턴스는 port 파일을 지우고 start 가 새로 쓸 때까지 기다린다
- **10-03**: 사용자 요청 「오른쪽 아래 한쪽~네쪽 보기 단추」 + 보고 「여러 쪽 보기에서 왼쪽 그림을 눌렀는데 상자가 화면 가운데」 → 스킬 dc8845b.
  단추는 스튜디오에 이미 있는 쪽 배치(`multiple` columns=N rows=1) + 쪽 맞춤을 부른다. 상자 결함은 렌더러 셋(table-object, cell-selection, table-resize)과 플러그인 picture-crop 이 쪽 왼쪽을 `(창 너비 − 쪽 너비) / 2` 로 셈한 것 → `getPageLeftResolved`.
  검증: 보이지 않는 크로미움(scratchpad `pv_click.py`)으로 세 쪽 보기에서 1쪽 그림, 2쪽 그림 각각 상자 위치 확인
  - 사용자 「푸시하고 릴리즈」 + 「공유받은 pc에서 에디터 빌드는 너무 부담」 → 스킬 b2bd82f 까지 hwpx, hwpx2 푸시, 릴리스 editor-884acbd40282.
    릴리스 직후 GitHub 사본의 setup 이 받기에 실패하고 12분 직접 빌드했다(로그를 잘라 원인 오류는 못 봄, 다시 받으니 4초).
    → setup 은 받기를 주소마다 세 번, 지문이 달라도 지난 묶음을 받고 경고, 받지 못하면 멈춤(빌드는 `--build` 만).
    🔑 이 PC 스킬 저장소 `.git/hooks/pre-push`(추적 안 됨)가 원본 지문 ≠ prebuilt.json 이면 푸시를 막는다 — 엔진, 플러그인, setup.mjs 를 고치면 `setup.mjs --build` → `release.mjs` → prebuilt.json 커밋 뒤 푸시
    - 사용자 「추천에 따르겠다」 → 릴리스는 저장소마다 최근 3개만(스킬 05dc934 `release.mjs` 가 올린 뒤 정리, `--prune` 은 정리만). 옛 3개(2ede, b2bd, fe3d) 지움
  - 세션 정리: 앵커 세션 블록을 최근 2개만 남기고 `CLAUDE-ARCHIVE.md` 로 내림(`trim_anchor.py` 가 연도 없는 날짜머리 `- **10-02**` 를 못 읽어 패턴 추가)
  - next_steps(내린 블록의 남은 일까지 모음)
    ① rhwp 이슈 답 확인: `gh issue view <번호> -R edwardkim/rhwp --comments` — #7535~7537(10-02), #7492(칸 그림 덧그림, 받아들여지면 `patches/cell-pic-split-dup.rs` 걷기), #7484(떠 있는 그림 배치, 받아들여지면 `patches/wrap-*` 걷기). #7444 는 #7509 에서 일부 고침 — 반영되면 `caret-axis-*` 정리 검토
    ② 사용자가 아궁이 문항카드(card2)로 표 속 표, 칸 그림을 다시 써 보고 알려 주는 결함부터
    ③ 남은 엔진 결함: 음수 세로 거리 그림(한/글은 문단 윗변에 붙임), 여러 개 선택 끌기의 오른쪽 정렬 부호, 큰 문서 편집 한 번 5초(스냅샷이 문서 전체를 올림)
    ④ 답 없는 제안: `changes` 에 화면 저장 기록 함께 보이기, md2hwpx ```chart 펜스 연결
    ⑤ 정리 거리: `.hwp2hwpx-repo`(78MB) 쓰임 확인, `~/.cache/rhwp-devel/latest` worktree(이슈 확인용), 노션 프로젝트 항목 없음(필요하면 `/프로젝트시작` 의 노션 연결만)
- **10-02 셋째**: 가이드북 세션 수정 요청 메모(`수정요청_20261002_가이드북세션.md`) 1번 「표가 한글과 다른 쪽에」 → 스킬 f982ae4(푸시 안 함), d0e90cf(그 세션의 editor-mode.md 함정 한 줄을 대신 커밋).
  원인은 낡은 저장 리셋(쪽 맨 위 vertpos=0): rhwp 는 편집 뒤에도 리셋을 남기고(`recalculate_section_vpos` delta=0 보존) 저장본에 다시 써, 한/글 원본에서 4쪽 맨 위였던 표 3-1이 내용이 줄어도 계속 다음 쪽으로 갔다.
  패치 `stale-reset-edit`(line_breaking.rs, 흐름이 밀리면 뒤 리셋을 풂), `stale-reset-fill`(typeset.rs, 직전 저장 끝이 본문의 50% 미만/110% 초과 + rhwp 로 반 미만이면 무시, 한 번 무시한 구역은 `st.claude_stale_reset_seen`)
  - 🔑 첫 판(rhwp 로 잰 채움만 보는 조건)은 한/글 쪽수에서 멀어진 문서가 나왔다 — rhwp 가 높이를 작게 재는 문서에서 한/글이 98% 채우고 끊은 리셋까지 무시했다(B_지도안 p5: rhwp 16%, 저장 98%). 저장 좌표를 증거로 함께 본다
  - 🔑 대조는 **에디터와 같은 전처리**(server `editorBytes`: 더미 줄 배치 걷기, rhwp_layout)를 거친 바이트로 해야 한다. 원본을 그대로 넣으니 38개가 바뀌어 보였다(스킬 산출물의 더미 vpos=0)
  - 검증: 문서 300개(scratchpad `pagemap.mjs`, `prep.mjs`, 한/글 쪽수 `hwp_pages.py` 를 `hidden_desktop.py` 로) 바뀐 5개 모두 한/글과 같아짐, 나빠짐 0. 편집 시험 `edit_reset.mjs`(한/글 원본에서 칸 글과 앞 문단 지움) 한/글과 같은 5쪽, 저장 뒤 다시 열어도 같음. `cargo test --lib` 3,889 통과. _06 편집 흐름 실패 17 → 7(줄어든 10건은 낡은 리셋이 만든 넘침). 실제 창에서 _05 표 3-1 제목 아래 확인
  - ⚠ 남은 것: 리셋이 풀린 뒤 rhwp 직접 조판에서 칸 안 각주가 든 표가 쪽 맨 아래에 걸리면 각주와 겹친다(_05 에서 앞 칸 16pt 시험, edit_flow 실패 15 → 73 의 대부분). rhwp 쪽 맞춤이 표 속 각주 높이를 빼지 않는 것으로 보임, 미확인
  - 한/글 COM 이 다시 필요해 `git show 85bab48^:scripts/hidden_desktop.py` 를 scratchpad 에 꺼내 썼다
  - 이어서 메모 2~8번 전부(사용자 「전부」, 6번은 「새 판으로」 선택) → 스킬 135e2f2(푸시 안 함). 플러그인과 CLI 만 바꿨다(엔진 그대로)
    JSON 문자열 공백 정규화(글 받는 메서드 제외), 없는 메서드 비슷한 이름 안내, insert_paragraphs 빈 문단 뒤 글자 모양, `clone_table`, 표 속 표 좌표 `T20r0c0/T1r0c0`(search_text, format_text, set_cell),
    `save` 뒤 세션 연결을 새 판으로, `changes` 한/영 오타 표시(`log-format.mjs dubeolsik`), `image --replace`
  - 🔑 **빌드가 WASM 메서드 매개변수 이름을 지운다**(vite 압축) — `fn.toString()` 으로 `_json` 인자를 가리려던 첫 판이 실패했다. 메서드 이름으로 가린다
  - 🔑 7번은 포커스 탈취가 아니었다: 사용자가 에디터에서 서식을 바꾸고 9초 뒤 같은 창에 영문 상태로 쳤다(guide4 ops.jsonl). 코드로 막을 수 없어 알림으로
  - 🔑 사용자가 다른 창에서 일하는 중이면 시험 창을 띄우지 않는다 — `start --no-browser` 뒤 Playwright 보이지 않는 크로미움(scratchpad `headless.py`)으로 호스트 페이지를 열면 cli 명령이 그대로 돈다
  - 검증: 4절 사본에서 항목마다 전/후 확인, 기존 도구(set_cell, format_text, search_text, replace_paragraph) 스모크 통과, 저장본 validate 통과
  - 푸시: 스킬 135e2f2 까지 hwpx, hwpx2(사용자 지시 「일단 푸시하고」). hwpx 쪽에는 다른 세션의 7c1dded(규칙 43 문서)도 함께
  - 각주 겹침 → 스킬 커밋(푸시 안 함) `patches/tac-table-footnote.rs`: `typeset_tac_table` 의 쪽 맞춤이 칸 각주 높이를 빼지 않았다(블록 표 `typeset_block_table_inner` 는 뺀다).
    한/글도 표를 같은 쪽 맨 아래에 두고 각주를 그 아래에 넣는다 — rhwp 가 앞 내용을 조금 크게 재 자리가 모자라 다음 쪽으로 넘긴다(겹침보다 낫다).
    🔑 첫 판은 `footnote_safety_margin` 까지 빼서 한/글이 같은 쪽에 두는 표(3절 _06 p54, 바닥 992px)도 밀었다 — 각주 실제 높이만 뺀다.
    검증: 문서 300개 중 바뀐 2-9절 두 판은 한/글 PDF 처럼 표 9-2 가 7쪽으로, 3절 세 판 편집 흐름 실패 5건씩(원본 rhwp 에서도 실패하는 p0, p12 큰 표 넘침), `cargo test --lib` 3,889 통과
  - 사용자 질문(스킬 용량): GitHub 저장소 250개 10 MB(pack 4.8 MB, 글꼴 5 MB). 로컬 폴더가 큰 것은 `.hwp2hwpx-repo` 78 MB, `studio-dist` 37 MB, `.git` 22 MB(모두 미추적). 설치가 느린 것은 에디터 setup(rhwp 빌드, Rust 면 8분)
    ⚠ Rust 없는 PC 는 npm 원본 WASM 을 써서 엔진 패치가 다 빠진다 — 빌드한 WASM 을 릴리스로 배포할지 제안해 둠(답 없음)
  - 사용자 「세가지 처리해라」 → ① b3e1ade 푸시 ② 쪽 끝 넘침 ③ 미리 빌드 배포. 스킬 55c96bc, 297aafc 까지 hwpx, hwpx2 푸시
  - ③ 🔑 **미리 빌드한 에디터 배포**(55c96bc): `editor/prebuilt.mjs`(원본 지문 = setup.mjs + patches/ + plugin/, 줄바꿈 LF 로 맞춤), `release.mjs`(studio-dist+sdk zip 17.4MB 를 hwpx, hwpx2 릴리스 `editor-<지문12>` 에 올리고 `prebuilt.json` 갱신), setup.mjs 가 지문이 같으면 받아 sha256 확인 후 풀고 끝(`--build` 면 빌드).
    빌드할 때 Rust 가 있을 때만 `studio-dist/.source-hash` 를 남겨 패치 없는 묶음이 올라가지 않게 했다. GitHub 에서 새로 받은 사본으로 4초 만에 설치, 엔진 패치(_05 6쪽) 확인
    ⚠ **엔진이나 플러그인을 고치면 `setup.mjs --build` → `release.mjs` → prebuilt.json 커밋, 푸시까지 해야 공유 사용자에게 간다**(지문이 다르면 공유 PC 는 직접 빌드로 떨어진다). 현재 릴리스 editor-b2bdd0b35a86
  - ② 패치 `tac-cap-ladder`: 쪽 나누기가 표 줄을 cap(lh + ls/2 + 바깥 위 여백)으로 줄여 셈하고 화면은 저장 vpos 로 그려 표마다 2.2px 어긋났다(진단: `RHWP_DIAG_TACCAP`, 「DIAG_TAC_END 뒤 다음 문단 시작에서 줄어든다」를 임시 eprintln 으로 좁힘).
    🔑 첫 판은 구역 연속 좌표 문서(난산 최종보고서, vpos 1.68M)에서 저장 스텝이 rhwp 자기 값이라 늘 일치해 쪽 끝 빈 문단을 다음 쪽으로 밀었다(한/글 COM `SetPos`+`KeyIndicator` 로 문단 쪽 확인, scratchpad `hwp_parapage.py`) → 쪽 기준 좌표일 때만
    검증: 문서 300개 열 때 바뀐 문서 0, 3절 편집 흐름 5 → 3, `cargo test --lib` 3,889
  - 사용자 질문 「스킬이 엄청 용량이 많네」: 로컬 `editor/.build` 가 16GB(Rust 캐시, 개발 폴더에 링크) — GitHub 와 무관
  - 권한 거부: 시험용 headless 프로세스 종료와 `~/.cache/hwpx-clone-test`(GitHub 사본, 시험 설치) 삭제 명령이 막혔다 — 남아 있다
  - 사용자 「남은 문제도 계속 해결해라」 → 스킬 6c02981(hwpx, hwpx2 푸시, 릴리스 editor-fe3dbeafc3b1). 3절 편집 흐름 실패 0(오늘 처음 73)
    ① 3절 p12 그림 상자가 421px(한/글 441.9px): 그림을 바꾼 칸의 뒤 빈 문단 vertpos 가 옛 값(1600)이라 「max(vpos+lh)」 하한이 빈 줄을 뺐다 → `cell-floor-stack`(비례 축소 하한), `tac-row-ladder`(행 사다리) 모두 줄을 쌓아 잰다
    ② 그러자 편집 뒤 21px 어긋남: `claude_measure_offset` 이 「잰 − 적힌」이라 처음부터 내용대로 그린 표도 깎았다 → `claude_opened_table_height`(max(적힌, 처음 그린), 2% 문턱)
    ③ 칸 합치기/나누기: 새 빈 칸이 원본 첫 문단(그림 줄 28421) 줄 배치를 복사 → `split-empty-stale`(빈 문단 줄 높이 > 10000 이면 다시 계산). 원본 rhwp 도 같은 결함
    🔑 진단: 예제 `cargo run --example <이름>` 로 DocumentCore 를 직접 편집하며 문단 vpos 를 찍는 것이 노드보다 빠르다(임시 예제는 지웠다). 재계산 안은 env 로 감싼 임시 eprintln(사본 두고 되돌림)
  - ❌ 남은 것: 한/글 원본 260927 판 편집 흐름 5건. 대표 p2 칸 Enter → 3쪽 끝 소제목 p38 9.7px 넘침. 쪽 나누기와 화면이 글자처럼 취급 표 뒤 문단 위치를 8~17px 다르게 잡는다.
    원인 후보: 쪽을 넘는 문단 p25 의 **문단 안** 쪽 바뀜(3쪽 첫 줄 vpos 0 근처)이 편집 뒤 이동량만 더해져 남는다. 문단 안 줄을 다시 쌓는 패치, 앞 문단 끝보다 위로 되감기면 잇는 패치를 시도 → 앞의 것은 실패 5 → 10, 뒤의 것은 효과 없음이라 둘 다 걷었다
  - 사용자 「그래」(260927 판 5건 이어서) → 스킬 c3cefd0(hwpx, hwpx2 푸시, 릴리스 editor-1190a7ed1522). 세 원고 편집 흐름 실패 0
    원인: 렌더러만 표 뒤에서 lazy base 를 다시 잡을 때(`height_cursor.rs vpos_adjust`, 진단 `RHWP_VPOS_DEBUG=1 rhwp export-svg`) 빈 문단 뒤 trailing-ls 다리를 놓아 기준이 600 작아지고 저장 위치로 8px 씩 밀었다.
    패치 `lazy-base-empty-bridge`(저장 위치 연속이면 다리 없음, **화면 커서만**(col_area_y > 0) — 쪽 나누기까지 바꾸면 300개 중 5개 쪽 배치가 흔들림, 미주 흐름(suppress_large_forward_jump) 제외 — 단위 시험 2건이 그 동작을 고정)
    + `stale-reset-edit` 에 문단 안 쪽 바뀜 풀기(쪽을 넘는 문단 p25 의 3쪽 첫 줄 vpos 0 근처가 이동량만 더해져 남던 것). 화면 보정 없이 이것만 넣었을 땐 실패 5 → 10 이었다
    🔑 화면 기준 대조 도구 scratchpad `overmap.mjs`(문서별 열 때 넘침, 겹침 수), `cmpflow.sh <hwpx> <쪽>`(쪽 나누기 누적과 화면 위치 나란히)
    🔑 회귀 대조의 전처리(`prep.mjs` → `rhwp_layout`)는 대조하는 엔진으로 다시 해야 한다 — 옛 엔진 전처리본으로는 표 높이가 어긋나 가짜 실패(2-9절 4건)가 났다
    ⚠ 2-9절(생성기 줄 배치) p52 표에 행을 넣었다 지우면 465px(원래 419.7) — rhwp 가 칸 문단을 다시 싸며 줄이 는다. 기준 엔진은 최댓값만 봐 「돌아온」 듯 보였다(내용은 잘렸을 것). 기록만 함
  - 사용자 「권한을 바꿔라」: 삭제가 막힌 원인은 전역 `~/.claude/settings.json` deny `Bash(rm -rf /*)`, `Bash(rm -rf ~*)`(와일드카드라 모든 절대 경로, 홈 아래 경로를 막음). 루트, 홈, `/c`, `/c/Users/hccga` **자체**만 막는 정확한 규칙 7개로 바꿨다(`rm -rf ~/*` 류는 `bash-guard.py` 훅이 계속 승인을 묻는다). 시험용 사본 두 폴더 삭제함
  - 사용자 「보고하라」 → rhwp 이슈 **#7535**(낡은 저장 리셋: 편집 뒤 남김 + 열 때 채움, 저장 좌표 무시), **#7536**(칸 위아래 나누기 빈 칸이 그림 줄 높이 상속), **#7537**(렌더러 lazy base 빈 문단 trailing-ls 이중 다리).
    최신 devel 4a7cf61c8(`~/.cache/rhwp-devel/latest` 를 origin/devel 로 옮겨 `pkg-devel` 빌드, 21분)로 재현 확인. **devel 에서 이미 고쳐진 셋(표 칸 각주 쪽 맞춤, 표 줄 cap, 칸 하한 낡은 vpos)은 보고하지 않았다.** 재현 파일은 scratchpad `shrink.py` 로 그림을 1×1 로 바꾼 20KB 사본, base64 되살림 md5 확인. 재현 스크립트 scratchpad `repro_all.mjs <wasm>`(일곱 결함 한 번에)
  - 푸시: 스킬은 c3cefd0 까지 hwpx, hwpx2 에 올라가 있다(이 폴더 저장소는 원격 없음). 노션: 이 폴더에 `- 노션:` 줄이 없어 프로젝트 기록은 오늘 같은 날 앞 세션 줄(3ecb9a4f-…bbba4)에 이어 적고 3단계는 건너뜀
  - next_steps: ① #7535~7537, #7484, #7492 답 확인(#7444 는 semanticist21 이 #7509 에서 일부 고침 — 반영되면 `caret-axis-*` 패치 정리 검토) ② `.hwp2hwpx-repo`(78MB) 쓰임 확인(정리 요청 시)
    ③ 이 CLAUDE.md 27.5k자(앵커 22.8k) — 30k 를 넘기 전에 09-27~09-30 블록을 `CLAUDE-ARCHIVE.md` 로 내린다(`trim_anchor.py`) ④ 노션 프로젝트 항목이 없다 — 필요하면 `/프로젝트시작` 의 노션 연결만 따로