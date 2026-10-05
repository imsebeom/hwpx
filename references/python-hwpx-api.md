# python-hwpx API 레퍼런스

`python-hwpx` 라이브러리 (PyPI: `python-hwpx`, import: `hwpx`) 의 핵심 API 시그니처와
주의사항을 빠르게 확인하기 위한 노트. 본 스킬은 라이브러리의 일부 기능만 의존하며,
대부분의 hwpx 조작은 자체 헬퍼 (`hwpx_modifier`, `hwpx_form_filler`, `md2hwpx`,
`hwpx_helpers`) 와 ZIP/lxml 직접 조작으로 처리한다. 이 문서는 `TextExtractor` /
`ObjectFinder` 등 라이브러리에 위임하는 부분과, 향후 메이저 업그레이드 시 활용
가능한 신규 API 를 함께 정리한다.

## 버전 매트릭스

**현재 설치: 2.9.1** / PyPI 최신: 6.3.0 (2026-08-22). 마지막 대조 2026-09-08.

| python-hwpx | 본 스킬 호환 | 비고 |
|---|---|---|
| 2.9.1 (현재 설치) | ✅ 검증됨 | 기본 동작 확인 |
| 6.0 ~ 6.3.0 | ✅ 검증됨 (2026-09-08) | 쓰는 API 전부 존재. 격리 venv 에서 `create_document.py` 생성 + `verify_hwpx.py` 전 항목 통과 |
| 7.0 이후 | ⚠️ 미출시 | `set_header_text`/`set_footer_text` 제거 예고 — 아래 참조 |
| 1.x | ❌ 비호환 | API 미존재 |

### 본 스킬이 실제로 쓰는 API

`hwpx` 를 직접 import 하는 곳은 세 군데뿐이다. 나머지는 자체 헬퍼와 ZIP/lxml 직접 조작이다.

| 파일 | 사용 심볼 |
|---|---|
| `create_document.py` | `HwpxDocument.new/add_paragraph/add_table/save_to_path`, 머리말·꼬리말 |
| `add_review_memo.py` | `HwpxDocument.open/add_memo_with_anchor/save_to_path` |
| `text_extract.py` | `TextExtractor` |

5.0 이 `hwpx.agent`, `hwpx.authoring`, `hwpx.exam`, `hwpx.form_fill` 등을 별도 패키지
`python-hwpx-automation` 으로 옮겼으나 **본 스킬은 그것들을 쓰지 않아 영향이 없다**.
표·메모·머리말은 core 에 남았다.

### 7.0 에서 깨질 지점 (대비 완료)

6.0 이 머리말·꼬리말 API 를 옮겼고 구 API 는 7.0 에서 제거된다.

```
DeprecationWarning: HwpxDocument.set_header_text은(는) python-hwpx 6.0에서
doc.page.set_header(text=...)(으)로 이동했습니다. 7.0에서 제거됩니다.
```

| 구 API (~6.x, 7.0 제거) | 신 API (6.0~) |
|---|---|
| `doc.set_header_text(text, section=…)` | `doc.page.set_header(text=…, section=…)` |
| `doc.set_footer_text(text, section=…)` | `doc.page.set_footer(text=…, section=…)` |

`create_document.py` 의 `_set_running_text()` 가 `hasattr(doc, "page")` 로 분기해
두 버전 모두를 처리한다. 2.9.1 과 6.3.0 에서 머리말이 실제로 삽입되는 것을 확인했다.

> 글로벌 업그레이드는 별도 venv 에서 회귀(학급평가보고서·학급독서통계·사업계획서
> strict PASS) 통과 후 결정한다. 6.3.0 은 위 세 스크립트 범위에서는 통과했으나
> 전체 회귀는 아직이므로 시스템 설치는 2.9.1 을 유지한다.

## 사용 중인 API 상세

### 설치와 import

```bash
pip install -U python-hwpx lxml
```

```python
from hwpx import TextExtractor, ObjectFinder, FoundElement, ParagraphInfo, SectionInfo
```

`hwpx` top-level 노출 심볼: `__version__`, `DEFAULT_NAMESPACES`, `ParagraphInfo`,
`SectionInfo`, `TextExtractor`, `FoundElement`, `ObjectFinder`.

### TextExtractor

```python
with TextExtractor("input.hwpx") as ext:
    full = ext.extract_text(include_nested=True)        # 표 셀까지 포함
    for sec in ext.iter_sections():
        for para in ext.iter_paragraphs(sec, include_nested=True):
            print(para.path, para.text(object_behavior="nested"))
```

메서드 (1.9):

- `extract_text(*, include_nested=False, object_behavior="skip", skip_empty=False) -> str`
- `iter_sections() -> Iterable[SectionInfo]`
- `iter_paragraphs(section, *, include_nested=False) -> Iterable[ParagraphInfo]`
- `iter_document_paragraphs(*, include_nested=False) -> Iterable[ParagraphInfo]`
- `paragraph_text(paragraph, *, object_behavior="skip") -> str`
- `open()` / `close()` (with-block 권장)

`object_behavior` 값: `"skip"` (기본, 표 등 inline object 본문 무시), `"nested"`
(객체 내부 문단까지 직렬화), `"placeholder"` (객체 위치를 기호로 표시).

### ObjectFinder

```python
with TextExtractor("input.hwpx") as ext:
    finder = ObjectFinder(ext)
    tables = finder.find_all("hp:tbl")
    for t in tables[:3]:
        print(t.path, t.attrib)
```

메서드:

- `find_all(tag) -> list[FoundElement]`
- `find_first(tag) -> FoundElement | None`
- `iter(tag) -> Iterable[FoundElement]`
- `iter_annotations() -> Iterable[FoundElement]`

`tag` 는 namespace prefix 포함 형태 (`"hp:tbl"`, `"hp:p"`, `"hp:tcell"` 등).
`DEFAULT_NAMESPACES` 가 자동 매핑된다.

### 본 스킬에서 사용 위치

- `scripts/text_extract.py` — `TextExtractor` 만 wrap
- 그 외 모든 hwpx 조작 (`hwpx_modifier`, `hwpx_form_filler`, `md2hwpx`,
  `build_hwpx`, `table_calc`, `hwpx_helpers`) 은 자체 구현 + `lxml` 사용

## 2.x — 향후 활용 가능한 신규 API (참고)

> airmang/hwpx-skill (2.9.0 기준) 의 `references/api.md` 발췌. 본 스킬은 아직 미사용.

### HwpxDocument (2.0+ 신규 클래스)

```python
from hwpx import HwpxDocument

doc = HwpxDocument.new()                                # 빈 문서 생성
doc.add_paragraph("자동 생성 문서")
table = doc.add_table(2, 2)
table.set_cell_text(0, 0, "학년", logical=True)         # 병합 셀은 logical=True
table.set_cell_text(0, 1, "1학년")
doc.save_to_path("output.hwpx")                         # 기본 저장 API

with HwpxDocument.open("input.hwpx") as doc:
    doc.add_paragraph("추가 문단")
    doc.save_to_path("edited.hwpx")
```

- `HwpxDocument.new()` / `HwpxDocument.open(source)` / `to_bytes()`
- `save()` 는 deprecated wrapper, `save_to_path(path)` 사용
- `add_table(rows, cols, *, section=None, width=None, height=None, ...) -> HwpxOxmlTable`
- 표 객체의 `set_cell_text(row, col, text, *, logical=False, split_merged=False)`

### 메모 추가 (2.x)

```python
memo, anchor_paragraph, field_value = doc.add_memo_with_anchor(
    "표현을 한 번 더 확인하세요.",
    paragraph=paragraph,
    author="검토자",
)
```

`add_memo_with_anchor(text="", *, paragraph=None, section=None, paragraph_text=None,
author=None, ...) -> tuple[HwpxOxmlMemo, HwpxOxmlParagraph, str]`

→ 학생 작품 자동 첨삭 헬퍼로 활용 가치 있음.

⚠ 함정 두 가지(2026-10-06 한/글 2024 실측) — **직접 부르지 말고 `scripts/add_review_memo.py` 를 거친다**:

- 이 함수가 쓴 메모는 한/글에서 본문 대신 메모 id 숫자가 보인다. 본문을 구역 끝 `<hp:memogroup>` 에 두고 필드 subList 에는 id 만 적는데 한/글은 그 묶음을 읽지 않는다. `Number` 도 모두 1 이다. `add_review_memo.memos_to_hancom_shape` 가 저장 뒤 한/글 모양으로 바꾼다.
- `paragraph_text` 는 「그 글이 든 문단 찾기」가 아니다. `paragraph` 없이 주면 **구역 끝에 그 글로 새 문단을 만들어** 메모를 걸고, `paragraph` 와 함께 주면 그 문단의 글을 바꾼다.

### 스타일 필터 치환 (2.x)

```python
with HwpxDocument.open("input.hwpx") as doc:
    red_runs = doc.find_runs_by_style(text_color="#FF0000")
    replaced = doc.replace_text_in_runs(
        "TODO", "DONE",
        text_color="#FF0000", underline_type="SOLID", limit=3,
    )
    doc.save_to_path("output.hwpx")
```

→ "빨간 TODO만 검정으로" 같은 조건부 일괄 치환에 강점.

## 마이그레이션 노트 (1.9 → 2.x)

본 스킬을 2.x 로 올릴 때 영향받는 표면:

1. `scripts/text_extract.py` — `TextExtractor` 만 사용. 1.9 ↔ 2.x 시그니처 변화
   거의 없음 (호환성 높음).
2. 자체 hwpx 조작 코드 (`hwpx_modifier` 등) — 라이브러리 의존도 0, 영향 없음.
3. **신규 활용 후보**: `HwpxDocument` 의 `replace_text_in_runs(text_color=, ...)` 와
   `add_memo_with_anchor()` 는 본 스킬에 동등 기능이 없으므로 추가 헬퍼로 도입 가치.

권장 회귀 테스트 셋:

- `.test/20260418-rhwp-분석/학급평가보고서/2026_2학기_5학년3반_학급평가_종합보고서.hwpx`
- `.test/20260418-rhwp-분석/학교사업계획/2026_AI디지털교육혁신_사업계획서.hwpx`
- `.test/20260418-rhwp-분석/학급독서통계/2026_1학기_학급독서기록_통계표.hwpx`

각각에 대해 `verify_hwpx.py --strict --json` 로 polaris-dvc strict PASS 확인.

## 참고

- airmang/hwpx-skill (Apache-2.0): https://github.com/airmang/hwpx-skill
- python-hwpx: https://github.com/airmang/python-hwpx
