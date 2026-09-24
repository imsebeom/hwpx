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
| 서식 있는 덩어리 | `pasteHtml(sec, para, offset, html)` — 제목, 목록, 표를 한 번에 |
| 필드 | `{"m":"GetFieldList"}`, `{"m":"PutFieldText","a":[이름,값]}`, `setFieldValueByName(name, value)` |
| 본문 전체 | `$E text` (표 셀 포함 UNICODE 텍스트) |

글자 서식 키 전체: bold italic underline strikethrough fontSize fontId textColor shadeColor underlineType underlineColor
outlineType shadowType shadowColor shadowOffsetX shadowOffsetY strikeColor subscript superscript emboss engrave emphasisDot
underlineShape strikeShape kerning fontIds ratios relativeSizes.
문단 서식 키 전체: alignment lineSpacing lineSpacingType indent marginLeft marginRight spacingBefore spacingAfter headType
paraLevel numberingId widowOrphan keepWithNext keepLines pageBreakBefore fontLineHeight singleLine autoSpaceKrEn
autoSpaceKrNum verticalAlign englishBreakUnit koreanBreakUnit borderConnect borderIgnoreMargin tabAutoLeft tabAutoRight.
(출처: rhwp `src/document_core/helpers.rs` 의 parse_char_shape_mods, parse_para_shape_mods. 실측 확인은 bold 만.)

## 4. 저장

- `$E save` → `<원본>_편집본.hwpx`. `$E save <경로>` 로 지정할 수 있다. **원본 덮어쓰기는 사용자 확인 후에만.**
- 저장 전에도 `~/.claude/cache/hwpx-editor/latest.hwpx` 는 수정할 때마다 갱신된다(검증용 사본).
- 저장본은 기존 검증 도구를 그대로 쓴다: `verify_hwpx.py --result`, `/pdf` 로 한컴 렌더 확인.
- 끝나면 `$E stop`.

## 5. 한계 (0.8.6 기준 실측)

- hwpctrl 의 `HAction.Execute` 는 파라미터셋 값을 아직 읽지 않고, `InsertCtrl("tbl")` 은 항상 5×5 다. 표와 서식은 `doc` 경로로 한다.
- 수정 내역 diff 는 글자 기준이다. 서식만 바뀐 변경은 "서식이나 개체만 바뀜"으로만 기록된다.
- 빈 문단에 긴 텍스트를 대치하면 `char_offset 범위 초과`가 날 수 있다(master-of-hwp 보고). 이때는 insertText 로 넣는다.
- 한컴 전용 글꼴은 웹 글꼴로 대체되어 화면의 줄바꿈이 한컴과 조금 다를 수 있다. 쪽수가 중요한 문서는 저장 후 `/pdf` 로 확인한다.
- 에디터 탭을 닫으면 명령이 60초 뒤 "브라우저 응답 없음"으로 실패한다. `$E start` 를 다시 부르면 된다.
