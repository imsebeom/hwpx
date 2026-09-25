# 에디터 모드 (rhwp 실시간 편집)

> 코드: `editor/`(스킬 폴더 기준). 개발 이력: `Desktop/code/hwpx 에디터기반 에이전트스킬`(2026-09-25). 시험: `editor/tests/`.

사용자가 브라우저의 rhwp 에디터로 문서를 보면서, 터미널의 Claude와 같은 문서를 함께 고치는 모드다.
Claude의 수정은 다시 열지 않고 화면에 바로 반영되고, 사용자가 에디터에서 고친 내역은 Claude가 읽을 수 있다.

```
Claude ─(cli.mjs)─▶ server.mjs(localhost:7780) ◀─(long-poll)─ host 페이지 ─▶ rhwp-studio iframe(claude 플러그인)
                         └─ ~/.claude/cache/hwpx-editor/  latest.hwpx · changes.jsonl · session.json
```

CLI 경로는 아래에서 `$E` 로 적는다: `node "<스킬>/editor/cli.mjs"`.

## 1. 시작

1. `/hwpx` 작업이 **이미 있는 문서를 고치는 일**이면 먼저 묻는다: "에디터로 보면서 작업할까요?" 아니면 기존 파이프라인 그대로 간다.
2. 새 문서를 처음부터 만드는 일이면 기존 파이프라인(md2hwpx, 템플릿, 양식 채우기)으로 **초안 파일을 먼저 만들고**, 그 파일을 에디터로 연다. 에디터 모드는 초안 이후의 다듬기를 맡는다.
3. 최초 1회 빌드: `editor/studio-dist/` 가 없으면 `node "<스킬>/editor/setup.mjs"` (rhwp 저장소 받기, npm 설치, 빌드. 수 분).
4. `$E start <문서.hwpx>` → **에디터 앱 창**(`editor/app.py`, WebView2, 최대화)이 열린다. 파이썬 `pywebview` 가 없으면 기본 브라우저 탭으로 연다(`--browser` 로 강제 가능). hwp 도 열리지만 저장은 hwpx 로 한다.
   앱 창이어야 한/글 단축키가 다 된다 — 브라우저 탭에서는 Ctrl+N, Ctrl+T, Ctrl+W 가 브라우저 예약키라 페이지에 오지 않는다(크롬 보안 제한). 7절.
   전자서명 문서(KS X 6101 §16)와 암호화 문서(§15)는 열지 않고 멈춘다. 서명이 무효가 되는 것을 사용자가 알고도 원할 때만 `--force`.
   **에디터는 세션마다 하나다**(2026-09-25 — 공용 하나였을 때 두 Claude 세션이 서로의 문서를 덮어썼다). 상태 폴더는 `~/.claude/cache/hwpx-editor/<세션 ID 앞 8자>/`, 포트는 7780 부터 빈 것을 골라 그 폴더의 `port` 에 적는다. 모든 명령이 자기 세션의 에디터만 본다. 한 세션에서 둘을 쓰려면 `HWPX_EDITOR_INSTANCE=<이름>` 을 준다. 창 제목은 「HWPX 에디터 · <문서> · <인스턴스>」. **떠 있는 에디터 전부는 `$E list`**(`*` 가 이 세션의 것). 이 세션의 에디터가 없고 옛 공용 에디터(포트 7780, 공용 폴더)가 떠 있으면 그것을 계속 쓴다.
   **한 인스턴스 안에서는 앱 창을 하나만 쓴다.** `start` 는 살아 있는 창이 있으면 그 창에 문서를 열고, `stop` 은 서버와 함께 창을 닫는다(저장하지 않은 편집이 있으면 멈춘다. 버리려면 `--force`). 창이 둘이면 명령을 나눠 받아 측정값이 뒤섞인다.
   **스킬 파이프라인 산출물(더미 줄 배치)과, 줄 배치가 빠진 문단에 글자처럼 취급하는 표가 있는 문서(양식 수정 도구가 줄 배치를 지운 문서, 줄 배치 없이 저장하는 생성기)는 한글로 줄 배치를 계산해 연다**(`scripts/hancom_layout.py`, 몇 초 걸린다. 스킬이 이제 빌드 끝에 실제 줄 배치를 넣으므로 주로 다른 도구나 옛 산출물이 이 경로를 탄다). 그 산출물은 모든 문단에 한 줄짜리 더미 줄 배치를 달고 칸 높이를 한 줄 기준으로 적는데, rhwp 는 더미를 믿어 문단을 한 줄로 누르고, 더미를 걷어도 스스로 잰 줄 수가 모자라 표가 아래 표와 겹친다.
   서버가 사본을 한글로 열어 저장한 뒤 **줄 배치와 표 높이(`hp:tbl/hp:sz`)만** 원본에 옮겨 심어 보낸다(그림, 서식은 원본 그대로. 원본 파일은 건드리지 않는다). **한글이 없거나 실패하면 rhwp 로 표 높이를 보정해 연다**(`editor/rhwp_layout.mjs`, 1초 안쪽). 겹침의 원인은 rhwp 의 「글자처럼 취급하는 표는 내용이 적힌 높이의 1.5배 이하로 넘치면 적힌 높이로 비례 축소」 규칙인데, 줄 배치가 없으면 행마다 줄일 수 있는 하한이 0 이라 두 줄이 한 줄 칸에 눌린다(rhwp#7419). 높이를 0 으로 두면 축소는 피하지만 쪽 나누기가 표를 높이 0 으로 보아 쪽 밖으로 밀어낸다. 그래서 **① 높이 0 으로 열어 rhwp 가 내용으로 잰 표 높이를 얻고 ② 그 값을 적어** 넘긴다. 문항 3에서 일곱 표가 한글 재저장본과 같은 쪽에 놓였고, 그 파일을 한글로 열면 원본과 PDF 6쪽이 픽셀까지 같다(한글은 이 값을 다시 계산한다). 셀 안의 표는 건드리지 않는다. 이것까지 실패해야 더미만 걷는다. **에디터의 rhwp 엔진에는 이 결함의 근본 수정 두 가지가 패치로 들어 있다**(`patches/tac-no-ls-shrink.rs`, `tac-no-ls-nested.rs`, setup.mjs 가 찾아 바꾸기로 넣는다) — ① 생성기가 쓴 표(줄 배치 없음, 표 높이 = 칸 높이 합)는 축소하지 않는다 ② 줄 배치 없는 문단이 품은 표 속 표가 자란 만큼 바깥 칸을 키운다. 그래서 행 높이와 표 속 표는 엔진이 바로잡고, 위 보정(실제 높이를 적어 넘기기)은 **쪽 나누기**를 맡는다(엔진은 쪽을 나눌 때 여전히 적힌 표 높이를 쓴다). 한글이 있는 PC 에서 이 경로를 시험하려면 서버를 `HWPX_EDITOR_NO_HANCOM=1` 로 띄운다. Node 에서 돌릴 WASM 은 `studio-dist/node/`(setup.mjs 가 번들과 같은 빌드를 둔다. `studio-dist/rhwp.js` 는 번들과 짝이 달라 쓸 수 없다).
5. `run` 은 보내기 전에 모든 문자열을 NFC 로 정규화한다(§5.3). 맥이나 웹에서 온 자모 분리 글자가 검색을 깨뜨리지 않게 하기 위해서다.

## 2. 대화 규칙

- **사용자가 말을 걸면 답하기 전에 `$E changes` 부터 본다.** 사용자가 에디터에서 고친 내역이 좌표로 나온다(`~ p12 │ 전 → 후`, `~ T1r0c1 │ 전 → 후`, 표 모양이 바뀌면 `! 표`). 커서 자리(셀 안이면 셀 좌표)와 **선택한 글자**도 함께 나온다. "이거", "여기", "선택한 부분"은 그것을 가리킬 가능성이 높다. 지금 커서는 `$E state`.
  **편집 하나가 한 줄로 실시간 기록된다**(`plugin/edit-log.ts`, 2026-09-25). 플러그인이 rhwp 되돌리기 기록(CommandHistory)의 실행, 되돌리기, 다시 실행을 감싸고 글자 모양, 문단 모양 호출에서 **바뀐 속성의 전 → 후**를 잡아 0.2초 안에 `/api/ops` → `ops.jsonl` 로 보낸다. `changes` 는 이것을 먼저 보이고(이어 친 글자는 한 줄로), 그 아래 「글자 변화」로 문단, 셀 단위 글 diff 를 붙인다. 문서 전체를 다시 읽을 필요가 없다. 예:
  ```
  [21:28:45] 지움  T6r1c4 p0:22  「z」
  [21:28:48] 문단 모양  T6r1c3~r3c3  줄 간격 160% → 170%
  [21:28:48] 글자 모양(셀 블록)  T6r1c3~r3c3  글자 크기 10pt → 11pt
  [21:28:49] 셀 합치기  T6r1c3~r3c3
  [21:28:49] 되돌리기 셀 합치기
  ```
  **사용자도 같은 기록을 본다**(2026-09-26): 도구 모음의 「로그 보기」 단추(`plugin/log-panel.ts`)가 오른쪽 패널을 열어 편집 기록(= `changes` 의 줄, Claude 편집은 보라색으로 켜고 끌 수 있다)과 작업 기록(= `log`)을 2초마다 새로 보인다. 줄은 서버 `/api/logview` 가 `editor/log-format.mjs` 로 만든다 — CLI 와 같은 함수라 글이 같다. `ops.jsonl` 은 이제 `start` 때 비우지 않고 최근 5000줄을 남기며 `── 열림 <파일>` 구분 줄을 넣는다(`changes` 는 읽은 자리를 끝으로 옮겨 새 편집만). 도구 모음이 접혀 있으면(메뉴 줄 오른쪽 ⌄) 단추가 안 보인다.
  자리 표기: 문단 `p12:5`(글자 위치), 셀 `T6r1c3 p0:5`, 셀 블록 `T6r1c3~r3c3`, 글 선택 `시작 ~ 끝`. 표 이동, 개체 속성처럼 값이 명령 안에 없는 스냅샷 작업은 이름과 자리만 나온다. Claude 의 `run` 은 기록되지만 `changes` 에서는 뺀다. 원자료 전부는 상태 폴더의 `ops.jsonl`.
- 사용자가 에디터에서 고친 부분을 Claude가 되돌리거나 덮어쓰지 않는다. 겹치면 묻는다.
- 수정한 뒤에는 "화면에 반영했다"고만 말하지 말고 무엇을 바꿨는지 한 줄로 적는다. 사용자는 Ctrl+Z 로 Claude의 배치 하나를 통째로 되돌릴 수 있다.

## 3. 편집 명령

`$E run <ops.json>` 또는 `echo '<JSON>' | $E run -`. 배열 하나가 **트랜잭션 하나, undo 1스텝**이고, 하나라도 실패하면 배치 전체가 되돌려진다.
op 는 네 가지다. **먼저 `tool` 을 쓰고, 도구에 없는 일만 `doc` 으로 내려간다.**

| 모양 | 뜻 |
|------|----|
| `{"tool": "fill_by_label", "args": {"label": "담당 부서", "text": "과학부"}}` | 편집 도구 25종(`editor/plugin/lib/doc-tools.js`, 형제 프로젝트 hwpx에디터기반AI 에서 가져옴). 도구마다 스냅샷을 떠서, 실패하거나 셀 안 표가 사라지면 되돌리고 쪽수가 바뀌면 결과에 `pages` 경고를 싣는다 |
| `{"doc": "insertText", "a": [0, 14, 5, "글"]}` | WASM `HwpDocument` 메서드. 객체 인자는 JSON 문자열로 바뀌어 들어가고, JSON 반환은 파싱돼 나온다 |
| `{"m": "PutFieldText", "a": ["기안자", "홍길동"]}` | 한컴 웹한글컨트롤 호환 메서드(`@rhwp/hwpctrl`, 484개 중 339개 구현) |
| `{"run": "BreakPara"}` | HwpCtrl Run 액션 |

### 편집 도구 25종 (좌표: 문단 `p12`, 표 `T1`(본문 표만 문서 순서로), 셀 `T1r2c1`, 행 `T1r0`, 열 `T1c0`)

`$E outline` 이 이 좌표가 붙은 개요를 준다(스타일, 병합, 누름틀, 메모 위치, 머리말/꼬리말, 쪽수). 인자 전체는 `$E tools`.

- 읽기: `read_document`(from_para, to_para), `search_text`(query) — 위치와 앞뒤 문맥
- 문단: `replace_paragraph`(para, text, keep_bullet, keep_style), `insert_paragraphs`(after_para, texts[]), `delete_paragraphs`, `find_replace`(find, replace, **expected_count**, keep_width)
- 표: `set_cell`, **`fill_by_label`**(label, text, direction, occurrence — 좌표를 몰라도 라벨 옆 칸을 채운다), 행과 열 넣기/지우기, `merge_cells`, `split_cell`, `table_props`(page_break, repeat_header), `table_formula`(=SUM(B2:B5)), `create_table`(after_para, rows[][]), `delete_table`
- 서식: `format_text`(at, text?, bold, size_pt, color …), `format_paragraph`(align, line_spacing, keep_with_next, page_break_before …), `apply_style`, `set_list`(number | bullet | none)
- 문서 요소: `set_header_footer`(글만), `add_footnote`, `set_field`(누름틀)

도구에 들어 있는 안전장치: 글머리 기호 보존(keep_bullet), 마크다운 기호 제거, 빨간 작은 안내 문구 자리에 채우면 검은 본문 서식으로 돌리기, 셀 안 표가 든 셀 통째 교체 거부.
⚠ `set_header_footer` 는 쪽 번호가 든 글을 거부한다(형제 프로젝트는 쪽 번호를 못 살렸다). 쪽 번호는 아래 `doc` 경로의 `applyHfTemplate`/`insertFieldInHf` 로 넣는다 — 이 스킬에서는 저장본에 살아남는다(5절).

`$E inspect` 는 문서 종류(공문, 계획서, 보고서, 가정통신문)를 알아내 날짜, 시간, 금액, 개인정보 표기를 검수하고, `$E slots` 는 아직 안 채운 칸을 좌표로 준다. 양식을 채운 뒤에는 둘 다 돌린다.
`$E goto T1r2c1` 은 사용자 화면의 커서를 그 자리로 옮기고 글자를 선택한다 — "여기를 고쳤다"를 보여 줄 때만 쓴다. ⚠ 이동 직후 키보드로 바로 치면 첫 글자가 먹히고 선택이 바뀌지 않았다(2026-09-25 실측). 사용자에게 "선택된 글자를 바꿔 치라"고 안내하지 않는다.

### WASM 직접 호출과 HwpCtrl

**위치는 추측하지 않는다. 먼저 읽는다.** 문단 번호는 0부터, 구역도 0부터다. 글자 오프셋은 문단 안 글자 수 기준이다.

```json
[{"doc":"getParagraphCount","a":[0]},
 {"doc":"getStructure","a":["summary"]},
 {"doc":"searchText","a":["준비물",0,0,0,true,false,true]},
 {"doc":"getParagraphLength","a":[0,14]},
 {"doc":"getTextRange","a":[0,14,0,50]}]
```

### 자주 쓰는 메서드 (시그니처 전체: `editor/.build/rhwp/pkg/rhwp.d.ts`, 439개)

| 목적 | 호출 |
|------|------|
| 글 넣기 | `insertText(sec, para, offset, text)` |
| 글 바꾸기 | `replaceText(sec, para, offset, length, newText)` / `replaceAll(query, newText, caseSensitive)` |
| 글 지우기 | `deleteText(sec, para, offset, count)` |
| 문단 나누기 | `splitParagraph(sec, para, offset)` — 새 문단을 만들 때. 줄바꿈 문자를 insertText 에 넣지 않는다 |
| 글자 서식 | `applyCharFormat(sec, para, start, end, {bold, italic, underline, strikethrough, fontSize, textColor, fontId, ...})` |
| 문단 서식 | `applyParaFormat(sec, para, {alignment, lineSpacing, indent, marginLeft, spacingBefore, spacingAfter, keepWithNext, pageBreakBefore, ...})` |
| 스타일 | `getStyleList()` → `applyStyle(sec, para, styleId)` |
| 표 | `createTableEx({sectionIdx, paraIdx, charOffset, rowCount, colCount, treatAsChar})`, `insertTextInCell(sec, parentPara, controlIdx, cellIdx, cellPara, offset, text)`, `insertTableRow`, `mergeTableCells` |
| 서식 있는 덩어리 | `pasteHtml(sec, para, offset, html)` — 첫 블록은 대상 문단에 이어 붙고, 목록은 글머리표 문단이 된다. 새 덩어리는 빈 문단을 만든 뒤 그 앞머리에 붙인다 |
| 필드 | `{"m":"GetFieldList"}`, `{"m":"PutFieldText","a":[이름,값]}`, `setFieldValueByName(name, value)` |
| 본문 전체 | `$E text` (표 셀 포함 UNICODE 텍스트) |

글자 서식 키 전체: bold italic underline strikethrough fontSize fontId textColor shadeColor underlineType underlineColor
outlineType shadowType shadowColor shadowOffsetX shadowOffsetY strikeColor subscript superscript emboss engrave emphasisDot
underlineShape strikeShape kerning fontIds ratios relativeSizes.
문단 서식 키 전체: alignment lineSpacing lineSpacingType indent marginLeft marginRight spacingBefore spacingAfter headType
paraLevel numberingId widowOrphan keepWithNext keepLines pageBreakBefore fontLineHeight singleLine autoSpaceKrEn
autoSpaceKrNum verticalAlign englishBreakUnit koreanBreakUnit borderConnect borderIgnoreMargin tabAutoLeft tabAutoRight.
(출처: rhwp `src/document_core/helpers.rs` 의 parse_char_shape_mods, parse_para_shape_mods. 실측 확인은 bold 만.)

### 요청 → 명령 사전 (KS X 6101 기능 목록 기준, 2026-09-25 한컴 렌더로 실측)

| 사용자 요청 | 표준 | 명령 | 결과 |
|------|------|------|------|
| 제목이 쪽 끝에 혼자 남지 않게 | `keepWithNext` (표 78) | `applyParaFormat(s, p, {"keepWithNext": true})` | 속성 적용 확인 |
| 이 문단부터 새 쪽 | `pageBreakBefore` | `applyParaFormat(s, p, {"pageBreakBefore": true})` | 한컴 통과. ⚠ 바로 앞 빈 문단이 이전 쪽을 넘치면 **빈 쪽이 생긴다** — 적용 전후 `pageCount` 를 비교하고, 늘어난 쪽이 비었으면 사용자에게 알린다(빈 문단 제거 방법은 미실측) |
| 문단이 쪽에서 안 쪼개지게 | `keepLines`, `widowOrphan` | `applyParaFormat` 같은 이름 키 | 미실측 |
| 표 제목 행을 쪽마다 반복 | `tbl@repeatHeader` (표 194) | `setTableProperties(s, 표문단, 컨트롤, {"repeatHeader": true})` | 한컴 통과 |
| 표를 행 경계에서만 나누기 | `tbl@pageBreak` | 같은 함수 `{"pageBreak": 2}` — 값 체계가 표준과 다르다: **0 나누지 않음, 1 셀 단위, 2 행 경계** | 속성 적용 확인 |
| 표 캡션과 번호 | `caption` + `autoNum` (§10.9.2.5) | 같은 함수 `{"hasCaption": true, "captionDirection": 2}` (0 왼쪽, 1 오른쪽, 2 위, 3 아래) → "표 N" 자동 번호 | 한컴 통과. 캡션 제목 글자 넣기는 미실측 |
| 책갈피 | `bookmark` | `addBookmark(s, p, offset, 이름)`, `getBookmarks()` | 적용 확인 |
| 수식 | 부속서 I | `insertEquation(s, p, offset, "a over b", 1000, 0)` (글자 크기 HWPUNIT, 색 0) | 한컴 통과 |
| 머리말/꼬리말 글 | `header`/`footer` | `createHeaderFooter(s, isHeader, 0)` → `insertTextInHeaderFooter(s, isHeader, 0, 0, offset, 글)` | 한컴 통과 |
| 머리말/꼬리말 쪽 번호, 총 쪽수 | `autoNum` PAGE, TOTAL_PAGE | 마당: `applyHfTemplate(s, isHeader, 0, 2)` (1 왼쪽, 2 가운데, 3 오른쪽 쪽 번호, 6~8 은 굵게+밑줄). 글 사이: `insertTextInHeaderFooter` 뒤 `insertFieldInHf(s, isHeader, 0, 문단, offset, 1)` (1 쪽 번호, 2 총 쪽수) | 한컴 통과("전체 4쪽", 가운데 "2"). rhwp 0.8.6 은 이 필드를 저장 시 버리지만 이 스킬은 되살린다 — Rust 가 있으면 패치 빌드한 WASM 이, 없으면 `save` 의 보정이. 파일 이름 필드(3)는 아직 저장되지 않는다 |

표 위치 찾기: `searchText(표 안 글자, 0,0,0, true,false, true)` 의 `cellContext.parentPara`, `ctrlIdx` 가 `setTableProperties` 의 둘째, 셋째 인자다.

## 4. 에디터 모드에서 하지 않는 일

에디터 모드는 **실시간 편집만** 한다(사용자 결정, 2026-09-25). rhwp API 가 없는 아래 작업은 에디터에서 흉내 내지 않는다.
요청이 오면 "에디터 모드에서는 안 되는 작업"이라고 알리고, 사용자 동의를 받아 `$E save` → `$E stop` 후 기존 워크플로로 처리한다.

| 작업 | 기존 워크플로 |
|------|---------------|
| 새 문서를 템플릿으로 생성 | A (md2hwpx, build_hwpx) |
| 양식 복제, 양식 부분 추출 | F, H |
| 문서 병합 | I |
| 시험지 생성 | J |
| 첨삭 메모 삽입 | N |

rhwp 저장본은 기존 스크립트가 그대로 받는다(왕복 보존력 실측: 22쪽 픽셀 차이 0%, 필드, 표, 그림 개수 동일).

## 5. 저장

- **저장할 때마다 새 판을 만든다**(사용자 지시 2026-09-25). `$E save` → 원본과 같은 폴더에 `<이름>_<YYMMDD>_<NN>.hwpx`.
  원본 이름 끝의 `_YYMMDD`, `_YYMMDD_NN` 은 떼고 오늘 날짜의 최대 순번 + 1 을 붙인다(스킬 `build_version.py` 와 같은 규칙).
  예: `제출_문항1-2_…_임세범_260921.hwpx` → `…_임세범_260925_01.hwpx`, `_02`, `_03` …
- 이미 있는 파일은 어떤 경우에도 덮어쓰지 않는다(`$E save <경로>` 로 지정해도 같다). 원본도 그대로 둔다.
- 저장 전에도 `~/.claude/cache/hwpx-editor/latest.hwpx` 는 수정할 때마다 갱신된다(검증용 사본).
- 저장본은 기존 검증 도구를 그대로 쓴다: `verify_hwpx.py --result`, `/pdf` 로 한컴 렌더 확인.
- 끝나면 `$E stop`.
- ⚠ **사용자가 에디터 화면에서 저장하면(Ctrl+S, 다른 이름으로 저장) 위 새 판 규칙을 거치지 않는다** — 고른 자리에 고른 이름으로 쓴다(2026-09-25 실측: 원본과 같은 이름으로 바탕화면에 저장).
  **어디에 무엇을 저장했는지는 `$E log` 로 본다.** 브라우저가 전체 경로를 알려 주지 않아 파일 이름만 남으므로, 경로가 필요하면 사용자에게 묻는다.

### 작업 기록 `$E log [N | --all]`

`~/.claude/cache/hwpx-editor/editor-log.jsonl` 에 **비우지 않고 쌓인다**(`changes.jsonl` 은 start 때마다 비우는 「읽지 않은 편집」 큐라 기록이 되지 못한다).
남는 것: 시작(파일 경로) / 불러옴(한글 줄 배치 적용, 캐시, 더미만 걷음 — 표가 겹칠 수 있다, 저장된 줄 배치 그대로) / 편집(사용자와 Claude, 바뀐 좌표, 커서) /
저장(Claude 는 전체 경로, 사용자 화면 저장은 파일 이름과 크기) / 다른 파일 열기 / 오류 / 종료.
화면 저장은 호스트 페이지가 iframe 의 `FileSystemFileHandle.createWritable` 과 `showOpenFilePicker` 를 감싸 잡는다(스튜디오는 저장 이벤트를 내보내지 않는다).
"뭘 저장했지", "아까 뭘 고쳤지" 같은 물음에는 이것부터 본다.

## 7. 한/글 단축키 (editor/plugin/hancom-keys.ts)

근거는 한/글 2020·2022·2024 도움말 「단축키 일람」(help.hancom.com/hoffice130/ko-KR/Hwp/view/toolbar/shortcut(table).htm).
rhwp 는 브라우저 예약키를 피하려고 한컴 키 일부를 옮겨 두었는데(Ctrl+N 계열 → Ctrl+M, Ctrl+Shift+C/R/T → Alt+Shift+C/H/D),
앱 창에서는 한컴 원래 키가 된다. rhwp 가 옮겨 둔 키도 그대로 남아 있다.

2026-09-25 앱 창에서 **실제 키 입력(SendInput, 스캔 코드 포함)으로 실측**, 영문과 한글 입력기 두 상태 모두:

| 키 | 동작 | 실측 |
|----|------|------|
| Ctrl+A (표 셀 안) | 그 셀 글 전체 선택. 본문에서는 문서 전체(rhwp 기본) | 통과 |
| Ctrl+N,N / Ctrl+N,E | 각주 / 미주 | 각주 통과 |
| Ctrl+N,T | 표 만들기(rhwp 는 격자 선택 팝업) | 통과 |
| Ctrl+N,I | 그림(파일 열기 창) | 통과 |
| Ctrl+N,G | 구역 설정 | 통과 |
| Ctrl+N,M, B, C, H, S, K, A, Z, F | 수식, 글상자, 캡션, 머리말, 감추기, 개체 고치기, 표 나누기, 표 붙이기, 계산식 | 연결만(글상자는 그리기 상태라 화면 판정 불가) |
| Ctrl+M,K/R/B/D/G/Y/C/W | 글자 색 검정/빨강/파랑/자주/초록/노랑/청록/흰색 (한컴 값, #993366 등) | 빨강 통과 |
| Ctrl+Q,F / Ctrl+Q,A / Ctrl+H | 찾기 / 찾아 바꾸기 | 통과 |
| Ctrl+K,N / Ctrl+K,B / Ctrl+K,E | 문단 번호 모양 / 책갈피 / 필드 입력 | 셋 다 통과(2026-09-26) |
| Ctrl+K,H / R / D / C / F | 하이퍼링크 / 상호 참조(책갈피 쪽 번호) / 날짜·시간 문자열 / 날짜·시간 코드 / 날짜·시간 형식 | rhwp 에 없어 새로 만들었다(`plugin/k-commands.ts` + 엔진 패치 `field-ex-*.rs`). 다섯 모두 통과, 한/글로 열어 다시 저장해도 필드가 남는다(2026-09-26) |
| Ctrl+Shift+C / R / T | 가운데 / 오른쪽 / 배분 정렬 | 가운데 통과 |
| Ctrl+F10 | 문자표 | 통과 |
| Ctrl+J, Ctrl+Shift+Insert, Ctrl+Shift+Delete, Alt+Shift+P/S, Alt+Insert | 쪽 나누기, 문단 번호, 글머리표, 위/아래 첨자, 줄·칸 추가 | 연결만 |

rhwp 에 기능이 없어 **안 되는 한컴 키**: Ctrl+N,P(쪽 번호 매기기 — 머리말/꼬리말 쪽 번호는 Claude 에게 요청), Ctrl+N,L(문단 띠), Ctrl+N,O(OLE), Ctrl+N,D(호환 문서), Ctrl+Q 의 L/1~0/B/R/I, Ctrl+K 의 H, R, D, C, F(하이퍼링크, 상호 참조, 날짜/시간), Ctrl+G 의 L/Z/R/D, Ctrl+W 계열, F8 맞춤법, F9 한자, Alt+I 상용구, Alt+Shift+C 보통 모양(rhwp 는 이 키를 가운데 정렬로 씀).

- **셀 블록(F5로 여러 셀을 고른 상태)에서도 서식 키가 선택한 셀 전체에 먹는다**(2026-09-25 수정). rhwp 는 셀 선택 중에 온 키를 「그 외 키」로 보고 셀 선택부터 풀어 버려(`input-handler-keyboard.ts`) Alt+Shift+A/Z(줄 간격), Alt+L(글자 모양) 같은 키가 커서 셀 하나에만 들어갔다. `hancom-keys.ts` 가 캡처 단계에서 rhwp 단축키 맵의 `format:*` 명령 전부와 블록 계산, 줄·칸 추가/삭제를 선택을 풀기 전에 부른다. 실측(실제 키 입력): 세 셀 블록에서 Alt+Shift+Z 가 세 셀 모두 160→170%, 블록 밖 셀은 그대로 / Alt+L 이 글자 모양 창을 열고 Esc 뒤에도 블록이 남는다.
  **셀 블록의 한 글쇠 명령**(한/글 도움말 「셀 블록 상태에서 <F5>」)도 같은 층이 받는다. rhwp 는 M, S 만 받았다.

  | 글쇠 | 동작 | 실측 |
  |----|------|------|
  | P | 표/셀 속성(셀 탭) | 통과 |
  | L / C | 각 셀 테두리 / 배경(셀 테두리/배경 창의 해당 탭) | 둘 다 통과, 한글 입력기에서도 |
  | B / F | 여러 셀 테두리 / 배경(하나의 셀처럼 적용) | 연결만 |
  | W / H | 셀 너비 / 높이를 같게 | W 통과(2×2 블록), H 통과(두 줄). 머리 행이 낀 범위에서는 rhwp 의 H 가 아무것도 하지 않았다 |
  | M / S | 셀 합치기 / 나누기 | M 통과, 영문과 한글 입력기 각각 두 번 |

  한/영, 한자 키는 셀 선택을 풀지 않고 입력기만 바꾼다(rhwp 에 넘기면 「그 외 키」라 선택이 풀린다). **안 되는 한/글 키**: A(표 자동 채우기), F7(칸 전체 블록), F8(줄 전체 블록) — rhwp 에 기능이 없다.
  **셀 블록 범위는 걸친 병합 셀이 모두 들어갈 때까지 넓힌다**(`claude-plugin.ts` 의 `installMergedCellRange`, 2026-09-25). rhwp 는 시작 셀과 끝 셀의 첫 행, 첫 열로만 사각형을 만들어, 병합 셀에서 끝나는 드래그가 방향에 따라 다르게 잡히고(왼쪽 위 → 오른쪽 아래는 되고 오른쪽 위 → 왼쪽 아래는 병합 셀 아래 줄이 빠짐) 병합 셀을 반만 걸친 범위의 셀 합치기가 **알림 없이** 실패했다(「되다 안 되다」의 정체). 선택 그리기, 서식, 합치기가 모두 커서의 `getSelectedCellRange` 를 거치므로 그 메서드를 감쌌다. 실측: 문항 3 정보표에서 6학년(r2c4)부터 4행 병합 셀(r9c0)까지 잡고 M → r2~r12 11×6 한 칸으로 합쳐졌다.
- **대화상자 글쇠**(2026-09-25): rhwp 는 글자 모양, 문단 모양 등 이름표에 「기준 크기(Z)」처럼 글쇠를 표시만 하고 받지 않았다. `hancom-keys.ts` 의 `onDialogKey` 가 모든 `.dialog-wrap` 대화상자에서 한/글처럼 받는다 — Alt+글쇠는 입력칸이면 그 칸으로 가 값을 고르고, 체크 상자, 라디오 단추, 단추(설정(D))는 누른다. **보이는 탭 안에 같은 글쇠가 여럿이면 옮기기만 한다**(Windows 규칙. 문단 모양 확장 탭의 한글(K)과 외톨이줄 보호(K)). Ctrl+Tab / Ctrl+Shift+Tab 은 탭 넘기기. 실측: 문단 모양 Alt+S 줄 간격, Ctrl+Tab 확장, Alt+K 두 번 한글(K) → 외톨이줄 보호(누르지 않음) / 글자 모양 Alt+Z 기준 크기, Alt+W 장평, Alt+T 글꼴.
  **문단 모양의 정렬 아이콘**은 글쇠 표시가 없어 따로 받는다 — 한컴 도움말 「문단 정렬 방식」의 단축키 글자(M 양쪽, L 왼쪽, R 오른쪽, C 가운데, T 배분)를 대화상자 안에서 **Ctrl+Shift+글자**와 **Alt+글자**(그 탭에 같은 글쇠 항목이 없을 때만)로 누른다. 도움말은 Ctrl+Shift 만 적고 대화상자 안의 Alt 는 적지 않는다. 나눔 정렬은 도움말에 단축키가 없다. 실측: Alt+C 가운데, Alt+R 오른쪽, Ctrl+Shift+L 왼쪽, Alt+T 배분, Alt+M 양쪽.
  대화상자의 Esc 는 오버레이에 걸려 있어 **포커스가 대화상자 밖이면 먹지 않았다**(열자마자 누르거나, 탭을 누른 뒤). 그때는 닫기 단추를 누른다. 닫힌 뒤 포커스가 페이지 몸통에 남으면 본문 입력칸으로 돌린다(안 그러면 다음 Alt+L 이 안 먹었다).
  **셀 블록 음영은 문서가 바뀔 때마다 다시 그린다**(2026-09-25). rhwp 는 `document-changed` 때 그림, 표 선택 표시만 다시 그려, 셀 블록에 줄 간격이나 글자 크기를 넣어 셀 높이가 바뀌면 음영이 옛 자리에 남았다. 실측: 세 셀 블록에 Alt+Shift+Z 세 번 → 셀 높이 166, 38 → 194, 42 에 음영이 그대로 따라왔다.
  ⚠ 시험 스크립트로 셀 블록을 다시 잡을 때는 Esc 를 두 번 누른다. 되돌리기 직후에는 한 번으로 선택 모드가 안 풀려 F5 가 한 단계 밀리고(셀 하나, 또는 표 전체), M 이 「안 먹는」 것처럼 보이거나 표 전체를 합쳤다.
- 두 단계 키의 두 번째 글쇠가 한글 입력기에 잡히면, 기본 동작을 막아도 조합이 이어지다 「ㄱ」 같은 글자로 확정되어 **선택 영역을 덮어쓴다**(실측). 입력칸 포커스를 뺐다 돌려 조합을 끝내고 그 조합·입력 이벤트를 버린다.
- ⚠ **알캡처 같은 캡처 프로그램이나 매크로 프로그램의 전역 단축키**는 운영체제가 먼저 가져가 에디터에 오지 않는다(실제 한/글에서도 같다). 단축키가 안 먹으면 그런 프로그램부터 의심한다.

## 6. 한계 (0.8.6 기준 실측)

형제 프로젝트 `Desktop/code/hwpx에디터기반AI`(OpenAI API 채팅형, 같은 rhwp 0.8.6)의 실측 중 여기 해당하는 것:

- **문단 모양 대화상자에서 아무것도 안 바꾸고 설정을 누르면 문단에 네 변 실선 상자가 생겼다**(2026-09-25 수정). 두 결함이 겹쳤다 — ① 배경 없는 문단의 `patternType` 이 0 으로 읽히는데 대화상자 무늬 선택지에 0 이 없어(없음 = -1) 「배경이 바뀌었다」고 보고 `fillType` 을 보낸다 ② 엔진은 `fillType` 이 오면 문단의 BorderFill 을 **기본값(네 변 실선)에서** 새로 만든다. 패치 `patches/para-bf-base-*.rs` 가 본문, 셀 문단 모두 **그 문단의 지금 BorderFill 에서** 시작하게 한다(요청에 borderFillId 가 없을 때). ①은 그대로라 편집 기록에 `patternType 0 → -1` 이 찍히지만 문서에는 해가 없다. 각주, 머리말/꼬리말 문단은 패치하지 않았다.
- **표 오른쪽(아래) 끝까지 셀을 합치면 없던 오른쪽(아래) 선이 생겼다**(2026-09-25 수정). rhwp 는 합친 셀에 주 셀(왼쪽 위)의 BorderFill 을 그대로 쓴다. 패치 `patches/merge-edge-*.rs` 가 한/글처럼 오른쪽 선은 오른쪽 가장자리 셀, 아래 선은 아래 가장자리 셀에서 가져온다. 실측: 문항 3 정보표 r9c0~r12c5 합치기 → 오른쪽 선 실선(1) 대신 없음(0), 왼쪽, 위, 아래는 그대로.
- **셀 안에서 Alt+C 모양 붙이기, 글자 모양, 문단 모양 대화상자의 설정이 알림 없이 실패했다**(2026-09-25 수정). 키보드로 만든 셀 안 선택(Home, Shift+End)은 위치에 `cellPath` 가 없는데 서식 명령은 `cellPath` 로만 셀 경로를 만들어 「경로가 비어있습니다」로 던졌다. 플러그인(`installCellPathFill`)이 커서의 `getSelectionOrdered` 에서 빈 `cellPath` 를 평평한 좌표로 채운다(rhwp `cellAxisPath` 규칙, 1단에서는 실제 경로와 같다). 모양 복사는 두 단계다 — 첫 Alt+C 는 커서 자리 모양을 기억만 하고(화면 변화 없음), 블록을 잡고 다시 Alt+C 하면 붙인다. 편집 기록은 서식 호출이 던지면 `글자 모양 실패(오류)` 로 남긴다.
- **표 선을 마우스로 클릭하면 표가 개체로 골라진다**(2026-09-26 수정, `installTableClickSelect`). rhwp 는 ① 선 위 mousedown 을 곧바로 크기 조절 드래그로 잡고 떼었을 때 1 쪽 픽셀 미만, 바깥 선일 때만 표를 골라 확대 화면의 손떨림이 선 이동(편집 기록의 「셀 크기」)이 됐고 ② 바깥 윗선 클릭은 클릭 처리가 표 판정까지 가지 않았다. 누른 자리에서 화면 4px 안에서 떼면 크기 조절 대신 표를 고르고(안쪽 선 포함), 바깥 선 근처(화면 5px)인데 안 골라졌으면 떼는 순간 고른다. 끌면 종전대로 크기 조절이다. 키보드로는 셀 안에서 Esc 한 번이다(F11 은 커서가 든 표가 아니라 다른 개체를 고를 수 있다 — 미수정). 실측(운영체제 실제 마우스): 윗선, 안쪽 선을 흔들림 0/3px 로 누르면 네 번 모두 표 선택, 50px 끌기는 셀 크기 조절, 셀 가운데 클릭은 커서 이동.
  ⚠ **CDP `Input.dispatchMouseEvent` 로 보낸 클릭은 rhwp 클릭 처리에 닿지 않는다**(셀 가운데를 눌러도 커서가 안 움직였다). 마우스 시험은 운영체제 입력(SetCursorPos + mouse_event)으로 하고, 화면 좌표는 CDP 의 CSS 좌표 × devicePixelRatio + 창 클라이언트 원점으로 구한다.
- **표 안에 표 만들기**(2026-09-26, `installNestedTableCreate`). rhwp 의 `table:create` 는 셀 안에서 막혀 있고(canExecute `!inTable`) 셀 안에 표를 만드는 엔진 API 도 없다. `pasteHtmlInCell` 은 `<table>` 을 탭 글로 펴 버린다. 플러그인이 명령 정의를 감싸, 셀 안이면 표 만들기 격자를 띄우고 한 스냅샷 안에서 ① 문서 끝에 임시 표를 **셀 안쪽 폭에 맞춘 colWidths** 로 만들고 ② `copyControl` ③ 임시 표와 그것이 더한 빈 문단 삭제 ④ `pasteInternalInCell(ByPath)` 로 커서 자리에 붙인다. 되돌리기 한 번으로 통째 취소되고, 내부 클립보드는 이 표로 바뀐다. Ctrl+N,T, 도구 모음, 메뉴 모두 이 길을 탄다. 실측: 문항 3 채점표 T6r1c4 에서 2×4 표가 칸 폭 42px(셀 안쪽 12416 HWPUNIT)로 들어가고 문단 수 17 그대로, 되돌리기 한 번에 원상.
  ⚠ `getControls` 의 셀 안 표 `Width` 는 실제 폭이 아니다(본문 폭이 남는다). 실제 폭은 `getTableCellBboxesByPath`.
  ⚠ 에디터를 `stop --force` 로 끄면 rhwp 자동 저장 복구본이 남아 다음 시작 때 「문서 복구」 창이 뜬다. 그 창이 떠 있는 동안의 키 입력은 본문으로 가서 **goto 가 잡은 선택을 지우고 글을 친다**(2026-09-26 시험에서 밟았다, 되돌림). 키 시험 전에 떠 있는 대화상자를 확인한다.
- **Ctrl+K 넣기 기능과 도구 모음**(2026-09-26). 엔진에 「표시 글을 감싼 필드 넣기」가 없어 `insertFieldEx`(패치 `field-ex-helper`, `-method`, `-wasm`)를 더했다 — 본문과 셀(경로) 모두, `{kind: hyperlink|crossref|summary, text, params}`. `params` 는 한/글 HWPX 원문과 같은 `<hp:parameters>` 이고 그 모양은 실물에서 가져왔다: 하이퍼링크, 상호 참조는 rhwp 시료의 한/글 파일(`samples/hwpx_sample2.hwpx`, `issue6284/…charts.hwpx`), **날짜 코드는 한/글 COM(`InsertDateCode`)으로 만든 파일** — 한/글의 날짜/시간 코드는 DATE 가 아니라 **문서 요약 필드(`type="SUMMERY"`, Command `$createtime`, Prop 8)**이고 한/글은 열 때 표시를 문서 작성 일시로 다시 쓴다. 날짜 문자열(D)은 그냥 글이다. 모든 넣기는 스냅샷 하나(되돌리기 한 번). 도구 모음: 하이퍼링크 단추(rhwp 는 data-cmd 가 없어 죽은 단추), 수준▲▼(rhwp 는 「개요 N」 스타일 문단만 → 문단 번호, 글머리표 문단은 `paraLevel` 0~9), 개체 속성(셀 안이면 표/셀 속성)을 고쳤다. 실측: 다섯 키로 넣고 저장한 파일을 한/글이 열고 다시 저장해도 HYPERLINK, SUMMERY, CROSSREF 가 그대로, 단추 셋 모두 통과.
  **필드 경계**(패치 `field-closed-edges`): rhwp 는 필드 끝에 친 글을 필드 안으로 넣었다(누름틀용 규칙). 하이퍼링크, 상호 참조, 날짜, 문서 요약 필드는 경계에 친 글을 밖에 둔다.
  🔴 **빈 머리말이 한/글을 죽이던 것**(패치 `hf-empty-para`): rhwp 는 글 없는 머리말 문단을 `<hp:p></hp:p>`(run 없음)로 저장하고, 그 파일을 다시 열면 그 문단을 버려 **다음 저장에서 문단 없는 subList** 가 되는데 **한/글은 그 파일을 열다 죽는다**(COM 이 「원격 프로시저를 호출하지 못했습니다」). 빈 문단에도 빈 run 을 쓰고, 문단이 없으면 빈 문단 하나를 쓴다. 한/글로 열 수 없는 저장본이 의심되면 `unzip -p <파일> Contents/section0.xml` 에서 `<hp:subList …></hp:subList>` 를 먼저 본다.
  ⚠ 한/글 COM 시험 파일을 만들 때 `zipfile.writestr(원본의 ZipInfo, …)` 를 쓰지 않는다 — 원본 ZipInfo 의 오프셋이 바뀌어 다음 읽기가 「Bad CRC」로 실패한다(손상으로 오인했다). `ZipInfo(이름, 날짜)` 를 새로 만든다. `hwp.Open` 은 절대 경로만 받는다.
- **진단**: 앱 창을 `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9333` 로 띄우면 `node editor/tests/cdp_eval.mjs 9333 "<식>"` 에서 `S.__claudeIH()` 로 입력 처리기(커서, 기록, formatCopyState 등)를 볼 수 있다. 조용히 실패하는 기능은 이것으로 해당 함수를 직접 불러 오류 문구를 받는다.
- `getControls()` 는 **셀 안 표도 돌려준다**(list 2). 본문 표만 세려면 `c.list < 구역 수` 이고 `getTableDimensions` 가 성공하는 것만 센다.
- 표가 든 문단 끝에서 `splitParagraph` 하면 **표가 새 문단으로 딸려 간다.** 표 뒤에 문단을 만들 때는 `insertParagraph(s, idx)`.
- 0번 문단은 구역 정의(secd)를 담고 있다. 지우지 않는다.
- `applyCharFormat` 의 끝 오프셋은 포함되지 않는다. 글자 크기는 1/100 pt(16pt = 1600).
- SDK `getSelectionContext()` 는 커서가 **표 셀 안이면 target 이 null** 이다. `changes` 의 "커서 문단"이 비면 셀 안일 수 있다.
- 한컴 자동 글머리표는 저장 후 한컴에서 기호가 안 보인다. 글머리표가 필요하면 기호를 글자로 넣는다. 자동 번호는 `ensureDefaultNumbering` 으로 정상.
- 빈 문서(`createEmpty`)는 hwpx 내보내기가 실패한다. 새 문서는 템플릿 파일로 시작한다.


- hwpctrl 의 `HAction.Execute` 는 파라미터셋 값을 아직 읽지 않고, `InsertCtrl("tbl")` 은 항상 5×5 다. 표와 서식은 `doc` 경로로 한다.
- 수정 내역 diff 는 글자 기준이다. 서식만 바뀐 변경은 "서식이나 개체만 바뀜"으로만 기록된다.
- 빈 문단에 긴 텍스트를 대치하면 `char_offset 범위 초과`가 날 수 있다(master-of-hwp 보고). 이때는 insertText 로 넣는다.
- 한컴 전용 글꼴은 웹 글꼴로 대체되어 화면의 줄바꿈이 한컴과 조금 다를 수 있다. 쪽수가 중요한 문서는 저장 후 `/pdf` 로 확인한다.
- 에디터 탭을 닫으면 명령이 60초 뒤 "브라우저 응답 없음"으로 실패한다. `$E start` 를 다시 부르면 된다.
