# rhwp 벤치마크 및 포팅 가이드

**업데이트**: 2026-09-08 (원 작성 2026-04-18)

[edwardkim/rhwp](https://github.com/edwardkim/rhwp) (Rust + WASM, MIT) 저장소의 HWPX
역공학 결과와 알고리즘을 **외부 의존성 없이** hwpx 스킬에 이식했다.
이 문서는 포팅 배경·사용법·한계를 정리한다.

## 왜 포팅했나

rhwp는 141K 라인 규모의 성숙한 HWPX 구현체로 다음 영역에서 Python 스킬보다 앞선다:

1. **표 계산식 엔진** (`src/document_core/table_calc/`) — 22개 함수
2. **네임스페이스 탄력 처리** (`src/parser/hwpx/utils.rs:10-18`)
3. **UTF-16 / 탭 오프셋 동기화** (`src/parser/hwpx/section.rs:299-322`)
4. **zip bomb 방어** (`src/parser/hwpx/reader.rs:19-26`)
5. **필드 API** (`src/document_core/queries/field_query.rs`)

포팅 당시(v0.7.x) CLI 바이너리·WASM 패키지는 사용자 환경에 Rust/Node.js 설치를
요구했으므로, 본 스킬은 **알고리즘과 데이터 구조만** Python으로 포팅했다.
rhwp 프로젝트는 read-only 참조.

> ⚠ **이 전제는 2026-09-08 기준으로 더 이상 사실이 아니다.** v0.8.4(08-12)가
> "공식 배포 채널 복원"을 내걸었고 v0.8.6(09-02) 릴리스에는 5개 플랫폼 prebuilt가
> 붙어 있다 — `rhwp-v0.8.6-windows-x86_64.zip`(9.8MB), linux x86_64/aarch64,
> macOS x86_64/aarch64, `SHA256SUMS.txt`. Rust 툴체인 없이 실행 파일을 바로 쓸 수 있다.
>
> 그래도 **알고리즘 포팅 결과물은 그대로 둔다.** 이미 동작하고 의존성이 0이며,
> 바이너리를 붙이면 9.8MB 자산과 버전 추적 부담이 생긴다. 다시 검토할 만한 경우는
> 아래 둘뿐이다.
> - 렌더링·조판 정합처럼 Python 재구현 비용이 큰 기능이 필요해질 때
> - 산출물을 한컴 없이 PDF/이미지로 뽑아야 할 때 → **2026-10-02 실현**: `scripts/rhwp_convert.py` 가 CLI 미리 빌드본을 받아 HWP→HWPX 와 PDF 를 맡는다
>
> 참고로 jkf87/hwpx-skill 은 `scripts/vendor/rhwp/` 에 WASM 번들을 vendoring 하는
> 쪽을 택했다. 노선이 다르므로 따라가지 않는다.

## 1. 표 계산식 엔진 (`scripts/table_calc.py`)

### 구조 (3-layer, rhwp와 동일)

```
tokenize()         → List[Token]       (문자열 → 토큰)
parse_formula()    → FormulaNode AST   (토큰 → AST)
evaluate_formula() → float             (AST → 값)
```

### 지원 함수

| 카테고리 | 함수 |
|----------|------|
| 집계 | SUM, AVG/AVERAGE, PRODUCT, MIN, MAX, COUNT |
| 수학(단항) | ABS, SQRT, EXP, LOG, LOG10, SIN, COS, TAN, ASIN, ACOS, ATAN, RADIAN, SIGN, INT, CEILING, FLOOR, ROUND, TRUNC |
| 이항 | MOD(a, b) |
| 분기 | IF(cond, true, false) |

### 셀 참조

- 절대: `A1`, `B3`, `Z99`
- 범위: `A1:B5`
- 와일드카드: `?5` (현재 열, 5행), `A?` (A열, 현재 행)
- 방향: `left`, `right`, `above`, `below` (현재 셀 기준)

### 사용 예

```python
from table_calc import evaluate_formula, TableContext

# 5x5 표: 값 = (row+1)*10 + (col+1)
def get_cell(col, row):
    if 0 <= col < 5 and 0 <= row < 5:
        return (row + 1) * 10.0 + (col + 1)
    return None

ctx = TableContext(row_count=5, col_count=5, current_row=4, current_col=0)
print(evaluate_formula("=SUM(A1:A3)", ctx, get_cell))         # 63.0
print(evaluate_formula("=AVG(B1,B2)", ctx, get_cell))          # 17.0
print(evaluate_formula("=IF(A1>10, SUM(A1:A3), 0)", ctx, ...)) # 미지원: IF 조건은 비영/영만
print(evaluate_formula("=a1+(b3-3)*2+sum(a1:b5,avg(c3,e5-3))", ctx, get_cell))  # 426.5
```

### 주의사항

- **비교 연산자(`>`, `<`, `=`) 미구현**: IF 조건은 "0이 아니면 참"으로만 동작
- **문자열 함수 없음**: 숫자 계산 전용
- 단위 테스트 38개 동봉: `python table_calc.py` 실행 시 전체 통과

## 2. 네임스페이스 헬퍼 (`hwpx_helpers.py`)

HWPX XML은 `hp:`, `hc:`, `hs:`, `hh:` 등 다양한 prefix가 혼재한다. lxml로 편집하면
종종 `ns0:`, `ns1:` 같은 임의 prefix가 붙어 `fix_namespaces.py` 후처리가 필요했다.
rhwp는 **prefix를 무시하고 로컬 이름만 비교**하는 패턴으로 이 문제를 회피한다.

### API

```python
from hwpx_helpers import local_name, xpath_local

# tag 문자열에서 prefix/namespace 제거
local_name("{http://...}p")  # "p"
local_name("hp:p")           # "p"
local_name("p")              # "p"

# lxml 루트에서 prefix 무관 검색
for p in xpath_local(root, "p"):           # 모든 <*:p>
    ...
for t in xpath_local(root, "tbl/t"):       # <*:tbl> 내부의 모든 <*:t>
    ...
```

### 채택 지점

`analyze_template.py::get_text()` 가 이 패턴을 사용한다. 향후 lxml 기반 스크립트
(`clone_form.py`, `hwpx_modifier.py`)에서도 prefix 비교를 대체하면 `fix_namespaces.py`
호출을 **필수 → 선택**으로 낮출 수 있다.

## 3. UTF-16 / 탭 헬퍼 (`hwpx_helpers.py`)

HWP 바이너리는 `char_shape` 경계를 **UTF-16 코드 유닛** 기준으로 계산한다.
Python `len()`는 코드포인트 기준이라 이모지·일부 한자(surrogate pair)에서 어긋난다.
또한 탭 문자(`\t`)는 8 코드 유닛으로 계산된다.

### API

```python
from hwpx_helpers import utf16_len, tab_aware_offset

utf16_len("가")            # 1 (BMP)
utf16_len("\U0001F600")    # 2 (surrogate pair)
utf16_len("abc가나다")      # 6

tab_aware_offset("abc")    # 3
tab_aware_offset("a\tb")   # 10 = 1 + 8 + 1
tab_aware_offset("\t\t")   # 16
```

### 언제 쓰나

`hp:charPr` 경계 조작, `linesegarray` 재계산, rhwp의 `ir-diff` 수준 정밀 비교.
현재 스킬은 이 정밀도가 필요한 시나리오가 드물지만, 향후 Command 추상화·표 수식
필드 배치 시 필수가 된다.

## 4. zip bomb 방어 (`verify_hwpx.py`, `hwpx_helpers.py`)

외부에서 받은 HWPX를 열 때 악의적 압축률로 메모리 폭증을 유발할 수 있다.
rhwp 상한 적용:

- XML/HPF 엔트리: **32 MB**
- BinData 엔트리: **64 MB**

### 자동 체크

`verify_hwpx.py`가 각 엔트리 `file_size`를 검사하여 위반 시 FAIL 처리.

```
$ python verify_hwpx.py --result suspicious.hwpx
❌ FAIL: 엔트리 크기 상한 초과 (Contents/section0.xml: 50MB > 32MB) — zip bomb 가능성
```

### 안전 읽기 함수

```python
from hwpx_helpers import read_zip_entry_limited
import zipfile

with zipfile.ZipFile(path) as zf:
    data = read_zip_entry_limited(zf, "Contents/section0.xml")
    # 상한 초과 시 ValueError
```

## 5. 필드 API (`hwpx_modifier.py`)

HWPX `<hp:fieldBegin>` 는 양식 필드(하이퍼링크, 사용자 변수, 메일 머지 등)의 시작점.
구조는 rhwp `src/parser/hwpx/section.rs::parse_ctrl_field_begin` 참조.

### API

```python
from hwpx_modifier import HwpxModifier

with HwpxModifier("form.hwpx") as m:
    fields = m.collect_all_fields()
    for f in fields:
        print(f)
    # {'index': 0, 'fieldName': '학교명', 'command': 'HYPERLINK',
    #  'fieldType': 'user', 'fieldId': 42,
    #  'params': {'Target': 'http://example.kr'}}
```

### 반환 형식

각 필드는 dict:

| 키 | 의미 | 예시 |
|----|------|------|
| `index` | 문서 내 등장 순서 | `0` |
| `fieldName` | `<fieldBegin name=...>` | `"학교명"` |
| `command` | `<stringParam name="Command">` | `"HYPERLINK"` |
| `fieldType` | `<fieldBegin type=...>` | `"user"` / `None` |
| `fieldId` | `<fieldBegin id=...>` (int) | `42` / `None` |
| `params` | 기타 `stringParam` 키-값 | `{"Target": "..."}` |

### 활용 시나리오

1. **양식 분석**: `clone_form.py --analyze` 확장 시 필드 목록까지 출력
2. **일괄 치환**: `Command == "USERNAME"` 인 필드 전부 찾아 사용자명 삽입
3. **검증**: `verify_hwpx.py`에서 원본 vs 결과 필드 수 비교

## HWPX FORMULA 필드 실스펙 (2026-04-19 검증)

table_calc 엔진의 **최종 목표 시나리오**는 HWPX 표 셀에 FORMULA 필드를 **실제로 주입**하여
HwpOffice에서 필드 업데이트(F9)로 재계산 가능하게 만드는 것. HwpOffice가 직접 저장한
파일을 역공학하여 정확한 스펙을 확보하고, `hwpx_helpers.py`에 공식 헬퍼를 등록했다.

### 실제 XML 구조

```xml
<hp:run charPrIDRef="...">
  <hp:ctrl>                                     ← 필수 래퍼
    <hp:fieldBegin id="..." type="FORMULA" name=""
                   editable="0" dirty="0" zorder="-1"
                   fieldid="627469685" metaTag="">
      <hp:parameters cnt="5" name="">
        <hp:integerParam name="Prop">8</hp:integerParam>
        <hp:stringParam name="Command">=SUM(B?:E?)??%g,;;5,710</hp:stringParam>
        <hp:stringParam name="Formula">=SUM(B?:E?)</hp:stringParam>
        <hp:stringParam name="ResultFormat">%g,</hp:stringParam>
        <hp:stringParam name="LastResult">5,710</hp:stringParam>
      </hp:parameters>
    </hp:fieldBegin>
  </hp:ctrl>
  <hp:t>5,710</hp:t>
  <hp:ctrl><hp:fieldEnd beginIDRef="..." fieldid="..."/></hp:ctrl>
  <hp:t/>
</hp:run>
```

### 요점

- **`<hp:ctrl>` 래퍼 필수** — fieldBegin/End가 run의 직접 자식이 아니라 ctrl 자식
- **5-파라미터 고정**: Prop(=8, integer) / Command / Formula / ResultFormat / LastResult
- **Command 패킹**: `"<formula>??<format>;;<result>"` — 레거시 문자열 형식
- **fieldEnd 속성**: `beginIDRef` + `fieldid` (fieldType 아님)
- **와일드카드 `?`**: `=SUM(B?:E?)` — `?`=현재 행 / `=SUM(?2:?4)` — `?`=현재 열
- **모든 FORMULA 필드가 공통 `fieldid` 공유** (그룹 ID, 기본 `627469685`)

### 스킬 헬퍼

`hwpx_helpers.py`:

```python
from hwpx_helpers import apply_formula_to_cell
# tc = lxml <hp:tc> 엘리먼트
apply_formula_to_cell(tc, field_id=2139727780, formula="=SUM(B?:E?)", result_str="5,710")
```

### 지원 확인된 함수 (HwpOffice 렌더 검증)

SUM · AVERAGE · MAX · MIN — 2026-04-18 학급 독서 통계표 테스트에서
34개 셀 전부 정상 렌더·재계산 확인.

### 활용 시나리오 구분

| 시나리오 | 방법 | HWPX에 수식 보존 | 예시 |
|----------|------|------------------|------|
| **A안** — Python 선계산 후 결과만 표에 | `<hp:t>` 텍스트 직접 치환 | ❌ | 학교사업계획서, 학급평가보고서 (이번 세션 초기 생성물) |
| **B안** — FORMULA 필드 주입 (이 문서) | `apply_formula_to_cell()` | ✅ (재계산 가능) | 학급독서통계 (2026-04-18), 셀수식_AB비교/B_real_formula.hwpx |

A안은 고정 수치 배포용, B안은 데이터 갱신이 예상되는 양식에 적합.

---

## 한계 & 향후

현재 포팅하지 않았거나 추후 고려할 항목:

| 항목 | 상태 | 비고 |
|------|------|------|
| IF 비교 연산자 (>, <, =) | 미구현 | rhwp 원본도 동일 — 상위 계층에서 처리 권장 |
| `set_field_value_by_name()` (쓰기) | 미구현 | 다음 단계 후보. `<fieldResult>` 텍스트 교체 로직 필요 |
| 편집 Command 추상화 (CQRS) | 미구현 | 작업량 크고 효과 간접적 — 보류 |
| 수식(MathML) 생성 | 미구현 | 독립 스캐폴드 필요 |
| SVG 렌더 기반 시각 검증 | 미구현 | rhwp CLI 필요 (외부 의존성) |
| 렌더러/페이지네이션 | 불가 | 49K LoC, Python 재현 비용 과다 |

## 라이선스 고지

rhwp는 **MIT License (Copyright (c) 2025-2026 Edward Kim)**. 본 스킬의 포팅 코드는
알고리즘을 참조하여 Python으로 재작성한 것이며, 각 파일에 rhwp 출처를 명시한다.

## 참고 경로

- rhwp 저장소: <https://github.com/edwardkim/rhwp>
- 로컬 clone (분석용): `C:/Users/hccga/Desktop/code/test/20260418-rhwp-분석/rhwp/`
- 분석 보고서: `C:/Users/hccga/Desktop/code/test/20260418-rhwp-분석/분석보고서.md`
- 주요 rhwp 참조 파일:
  - `src/document_core/table_calc/{tokenizer,parser,evaluator}.rs`
  - `src/parser/hwpx/utils.rs` (local_name)
  - `src/parser/hwpx/section.rs` (필드·탭 오프셋)
  - `src/parser/hwpx/reader.rs` (zip bomb 상한)
