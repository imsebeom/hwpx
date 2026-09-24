# 에디터 모드 (rhwp 실시간 편집)

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
3. 최초 1회 빌드: `studio-dist/` 가 없으면 `node "<스킬>/editor/setup.mjs"` (rhwp 저장소 받기, npm 설치, 빌드. 수 분).
4. `$E start <문서.hwpx>` → 사용자 기본 브라우저에 에디터가 열린다. hwp 도 열리지만 저장은 hwpx 로 한다.
   전자서명 문서(KS X 6101 §16)와 암호화 문서(§15)는 열지 않고 멈춘다. 서명이 무효가 되는 것을 사용자가 알고도 원할 때만 `--force`.
5. `run` 은 보내기 전에 모든 문자열을 NFC 로 정규화한다(§5.3). 맥이나 웹에서 온 자모 분리 글자가 검색을 깨뜨리지 않게 하기 위해서다.

## 2. 대화 규칙

- **사용자가 말을 걸면 답하기 전에 `$E changes` 부터 본다.** 사용자가 에디터에서 고친 내역이 줄 단위 diff 로 나오고, 커서가 있던 문단도 함께 나온다. "이거", "여기"는 그 커서 문단을 가리킬 가능성이 높다.
- 사용자가 에디터에서 고친 부분을 Claude가 되돌리거나 덮어쓰지 않는다. 겹치면 묻는다.
- 수정한 뒤에는 "화면에 반영했다"고만 말하지 말고 무엇을 바꿨는지 한 줄로 적는다. 사용자는 Ctrl+Z 로 Claude의 배치 하나를 통째로 되돌릴 수 있다.

## 3. 편집 명령

`$E run <ops.json>` 또는 `echo '<JSON>' | $E run -`. 배열 하나가 **트랜잭션 하나, undo 1스텝**이다.
op 는 세 가지다.

| 모양 | 뜻 |
|------|----|
| `{"doc": "insertText", "a": [0, 14, 5, "글"]}` | WASM `HwpDocument` 메서드. 객체 인자는 JSON 문자열로 바뀌어 들어가고, JSON 반환은 파싱돼 나온다 |
| `{"m": "PutFieldText", "a": ["기안자", "홍길동"]}` | 한컴 웹한글컨트롤 호환 메서드(`@rhwp/hwpctrl`, 484개 중 339개 구현) |
| `{"run": "BreakPara"}` | HwpCtrl Run 액션 |

**위치는 추측하지 않는다. 먼저 읽는다.** 문단 번호는 0부터, 구역도 0부터다. 글자 오프셋은 문단 안 글자 수 기준이다.

```json
[{"doc":"getParagraphCount","a":[0]},
 {"doc":"getStructure","a":["summary"]},
 {"doc":"searchText","a":["준비물",0,0,0,true,false,true]},
 {"doc":"getParagraphLength","a":[0,14]},
 {"doc":"getTextRange","a":[0,14,0,50]}]
```

### 자주 쓰는 메서드 (시그니처 전체: `.build/rhwp/pkg/rhwp.d.ts`, 439개)

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
| **꼬리말 쪽 번호** | `pageNum` (§10.7.10) | **에디터 모드 불가.** `insertFieldInHf(...,1)` 은 화면에만 보이고 hwpx 저장 시 빠진다. `insertAutoNumberAtCursor` 는 본문 전용, hwpctrl `PageNumPos` 는 미구현 (rhwp 0.8.6) | 사용자에게 알리고 저장, 종료 후 기존 워크플로로 |

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
| 꼬리말 쪽 번호 | 템플릿 또는 한컴 |

rhwp 저장본은 기존 스크립트가 그대로 받는다(왕복 보존력 실측: 22쪽 픽셀 차이 0%, 필드, 표, 그림 개수 동일).

## 5. 저장

- **저장할 때마다 새 판을 만든다**(사용자 지시 2026-09-25). `$E save` → 원본과 같은 폴더에 `<이름>_<YYMMDD>_<NN>.hwpx`.
  원본 이름 끝의 `_YYMMDD`, `_YYMMDD_NN` 은 떼고 오늘 날짜의 최대 순번 + 1 을 붙인다(스킬 `build_version.py` 와 같은 규칙).
  예: `제출_문항1-2_…_임세범_260921.hwpx` → `…_임세범_260925_01.hwpx`, `_02`, `_03` …
- 이미 있는 파일은 어떤 경우에도 덮어쓰지 않는다(`$E save <경로>` 로 지정해도 같다). 원본도 그대로 둔다.
- 저장 전에도 `~/.claude/cache/hwpx-editor/latest.hwpx` 는 수정할 때마다 갱신된다(검증용 사본).
- 저장본은 기존 검증 도구를 그대로 쓴다: `verify_hwpx.py --result`, `/pdf` 로 한컴 렌더 확인.
- 끝나면 `$E stop`.

## 6. 한계 (0.8.6 기준 실측)

- hwpctrl 의 `HAction.Execute` 는 파라미터셋 값을 아직 읽지 않고, `InsertCtrl("tbl")` 은 항상 5×5 다. 표와 서식은 `doc` 경로로 한다.
- 수정 내역 diff 는 글자 기준이다. 서식만 바뀐 변경은 "서식이나 개체만 바뀜"으로만 기록된다.
- 빈 문단에 긴 텍스트를 대치하면 `char_offset 범위 초과`가 날 수 있다(master-of-hwp 보고). 이때는 insertText 로 넣는다.
- 한컴 전용 글꼴은 웹 글꼴로 대체되어 화면의 줄바꿈이 한컴과 조금 다를 수 있다. 쪽수가 중요한 문서는 저장 후 `/pdf` 로 확인한다.
- 에디터 탭을 닫으면 명령이 60초 뒤 "브라우저 응답 없음"으로 실패한다. `$E start` 를 다시 부르면 된다.
