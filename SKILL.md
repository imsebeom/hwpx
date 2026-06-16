---
name: hwpx
description: "HWPX 문서(.hwpx) 생성·읽기·편집 통합 스킬. '한글 문서', 'hwpx', 'HWPX', '한글파일', '.hwpx 만들어줘', '보고서', '공문', '기안문', '한글로 작성', '회의록', '제안서', '이미지 포함 문서' 등의 키워드 시 반드시 사용. 마크다운·텍스트·URL 자료를 HWPX 문서로 변환하는 '콘텐츠→문서화' 워크플로우와 템플릿 치환 워크플로우를 지원한다."
allowed-tools: Bash(python3 *), Read, Write, Glob, Grep
---

# HWPX 통합 문서 스킬

HWPX는 한컴오피스 한글의 개방형 문서 포맷이다. **ZIP 패키지 + XML 파트** 구조.

## 스킬 디렉토리

```
${CLAUDE_SKILL_DIR}/
├── SKILL.md
├── scripts/
│   ├── hwpx_helpers.py        # ★ 헬퍼 라이브러리 (+ local_name/utf16/zip 상한)
│   ├── table_calc.py          # ★ 표 계산식 엔진 (SUM/AVG/IF 등, rhwp 포팅)
│   ├── build_hwpx.py          # 템플릿+XML → .hwpx 조립
│   ├── fix_namespaces.py      # ★ 필수: 네임스페이스 후처리
│   ├── validate.py            # HWPX 구조 검증
│   ├── analyze_template.py    # HWPX 심층 분석 (xpath_local 사용)
│   ├── clone_form.py           # ★ 양식 복제 (Workflow F)
│   ├── verify_hwpx.py         # ★ 서브에이전트 검수 도구 (+ zip bomb·secPr 완전성·글자 테두리 버그)
│   ├── text_extract.py        # 텍스트 추출
│   ├── md2hwpx.py             # 마크다운→HWPX 자동 변환
│   ├── hwpx_modifier.py       # ★ 양식 세밀 수정 (+ collect_all_fields)
│   ├── hwpx_form_filler.py    # ★ 양식 부분 추출/표 조작 (Workflow H)
│   ├── hwpx_writer.py         # 줄간격 XML 생성 유틸리티
│   ├── exam_builder.py          # ★ 시험 문제지 생성 (Workflow J)
│   ├── convert_hwp.py           # HWP(바이너리) → HWPX 변환 (Workflow K, jkf87 포팅)
│   ├── writing_optimizer.py     # ★ 공공기관 보고서 글쓰기 자동 변환 (Workflow P, public-doc-to-hwpx 포팅)
│   └── office/{unpack,pack}.py
├── templates/
│   ├── base/                  # 베이스 Skeleton
│   ├── report/                # 보고서
│   ├── gonmun/                # 공문
│   ├── minutes/               # 회의록
│   ├── proposal/              # 제안서
│   └── government/            # ★ 관공서 (컬러 섹션 바/표지 배너)
├── assets/
│   ├── report-template.hwpx
│   └── government-reference.hwpx
└── references/
    ├── xml-structure.md       # XML 구조, 이미지 삽입, 표지/섹션 바 패턴
    ├── template-styles.md     # 템플릿별 스타일 ID 맵
    ├── troubleshooting.md     # 트러블슈팅
    ├── report-style.md        # 보고서 양식 상세
    ├── official-doc-style.md  # 공문서 양식 상세 (서식 위주)
    ├── gonmunseo-2025-writing-rules.md  # ★ 2025-01-08 개정 행정업무규정 룰셋 (수신·항목기호 등, jkf87 차용)
    ├── xml-internals.md       # 저수준 XML 구조
    ├── rhwp-benchmark.md      # rhwp 포팅 배경·표 수식·필드 API 사용법
    ├── python-hwpx-api.md     # python-hwpx 라이브러리 API 시그니처 + 1.9 ↔ 2.x 마이그레이션
    ├── writing-principles.md  # ★ 공공기관 보고서 작성 원칙 (개조식·두괄식·적의것들, public-doc-to-hwpx 포팅)
    └── layout-rules.md        # ★ 레이아웃 최적화 규칙 + 자동 변환 12개 표 (public-doc-to-hwpx 포팅)
```

## rhwp 포팅 요약 (2026-04-18)

외부 의존성 없이 rhwp (edwardkim/rhwp, MIT) 에서 **알고리즘·패턴**만 추출·포팅.
자세한 배경은 `references/rhwp-benchmark.md` 참조.

| 새 기능 | 파일 | 용도 |
|--------|------|------|
| 표 계산식 엔진 | `scripts/table_calc.py` | SUM/AVG/MIN/MAX/COUNT/IF + 범위·방향 참조. 표 셀 수식 평가 |
| **HWPX FORMULA 필드 주입** | `hwpx_helpers.py` — `apply_formula_to_cell()`, `build_formula_run_inner_xml()` | HwpOffice 실스펙 구조로 필드 삽입. F9로 재계산 가능 (2026-04-19 검증) |
| **셀 시맨틱 편집 6종** | `hwpx_modifier.py` — `set_cell_bg/border/size/inner_margin`, `set_table_border_color`, `merge_cells` | 표 셀 시각 속성을 좌표 기반으로 직접 편집. borderFill 풀 자동 등록·dedup. (2026-05-04, woo773/hangle 어휘 차용) |
| **단위 변환 + borderFill 빌더** | `hwpx_helpers.py` — `mm_to_hwpunit`, `pt_to_hwpunit`, `rgb_to_hex`, `build_border_fill_xml`, `border_fill_signature` | mm·pt → HWPUNIT 변환 + borderFill XML 단독 빌더 (2026-05-04) |
| `local_name()` / `xpath_local()` | `hwpx_helpers.py` | 네임스페이스 prefix 무관 XPath 검색 |
| `utf16_len()` / `tab_aware_offset()` | `hwpx_helpers.py` | 탭 8 코드유닛 동기화 (charShape 경계 계산용) |
| zip bomb 상한 체크 | `verify_hwpx.py`, `hwpx_helpers.py` | XML 32MB / BinData 64MB |
| `collect_all_fields()` | `hwpx_modifier.py` | `<hp:fieldBegin>` 전수 조회 (fieldName/Command/params) |

## 환경 설정

```bash
pip install python-hwpx lxml --break-system-packages
```

---

## ★ 워크플로우 선택 (Decision Tree)

> **반드시 아래 판단을 따른다.**

```
사용자 요청
 ├─ "마크다운/텍스트/URL → HWPX" → 워크플로우 A (콘텐츠→HWPX)
 ├─ "양식에 내용 채워줘" → 워크플로우 B (템플릿 치환)
 ├─ "HWPX 수정해줘" → 워크플로우 C (기존 문서 편집)
 ├─ "이 HWPX 양식으로 만들어줘" → 워크플로우 D (레퍼런스 기반)
 ├─ "이 양식 복제해서 내용 바꿔줘" → 워크플로우 F (양식 복제) ★
 ├─ "들여쓰기 조정/정규식 치환/인덱스 수정" → 워크플로우 G (세밀 수정)
 ├─ "붙임 추출/표 행 추가/셀 채우기" → 워크플로우 H (표 조작)
 ├─ "여러 HWPX를 하나로 합쳐줘" → 워크플로우 I (병합)
 ├─ "시험 문제지/PDF 시험지 → HWPX" → 워크플로우 J (시험 문제지)
 ├─ ".hwp(바이너리) → HWPX 변환" → 워크플로우 K (HWP→HWPX 순수 Python)
 ├─ "{학교명}/{담당자} 일괄 치환 (양식 표 셀 포함)" → 워크플로우 L (zip-level 전역 치환)
 ├─ "빨간 글씨 일괄 검정으로/스타일별 부분 치환" → 워크플로우 M (스타일 필터 치환)
 ├─ "학생 작품 첨삭 메모 자동 삽입" → 워크플로우 N (자동 첨삭 메모)
 ├─ "레퍼런스 양식 그대로/쪽수 동일하게 만들어줘" → 워크플로우 O (레퍼런스 99% 복원 + 쪽수 가드)
 └─ "HWPX 읽어줘" → 워크플로우 E (읽기/추출)
```

### ⚠️ 자동 판별 규칙 (사용자가 양식 파일을 제공한 경우)

> **사용자가 `.hwpx` 파일을 주고 "이걸로 테스트", "내용 바꿔줘", "이 양식으로" 등을 요청하면
> 먼저 `clone_form.py --analyze`로 구조를 확인한다.**

```
양식 분석 결과
 ├─ 테이블 ≥ 1개 또는 이미지 ≥ 1개 → 워크플로우 F (양식 복제) ★★★
 ├─ 테이블 0개, 이미지 0개, 단순 텍스트 → 워크플로우 C 또는 D 가능
 └─ 판단 불가 → 워크플로우 F를 기본으로 사용 (가장 안전)
```

> **절대 하지 말 것:**
> - `<hp:t>` 노드를 순차적으로 새 텍스트로 덮어쓰기 — **런(run) 소실, 서식 파괴**
> - lxml로 텍스트 노드를 직접 조작 — **네임스페이스/속성 손실 위험**
> - 새 section0.xml을 처음부터 작성 (Workflow A/D) — **구조 97.5% 손실**
>
> **반드시 할 것:**
> - `clone_form.py`의 `clone()` 함수 또는 ZIP-level 문자열 치환 사용
> - 치환은 `str.replace()` 기반으로 XML 구조를 건드리지 않음

---

## 워크플로우 A: 콘텐츠 → HWPX (가장 중요!)

> **마크다운·텍스트·URL → 구조화된 HWPX 문서. 이 워크플로우가 핵심.**

> **⚠️ md2hwpx.py를 직접 실행하지 마라.** md2hwpx.py는 base/report 템플릿만 지원하며,
> government 템플릿의 컬러 배너·섹션 바·표지 페이지를 생성할 수 없다.
> **반드시 `hwpx_helpers.py`를 import하고 아래 흐름을 따른다.**

### 전체 흐름

```
[1] 소스 자료 읽기
[2] 구조 파싱 (제목, 섹션, 본문, 이미지)
[3] 템플릿 선택 → 해당 템플릿의 스타일 ID만 사용 (references/template-styles.md)
    ⚠️ 템플릿 간 ID는 호환되지 않음! government charPr를 report에 쓰면 깨짐
[4] hwpx_helpers.py를 import하여 Python 빌드 스크립트 작성
[5] build_hwpx.py로 .hwpx 조립
[6] 이미지가 있으면 add_images_to_hwpx() + update_content_hpf()
[7] fix_namespaces.py 후처리 (필수!)
[8] validate.py 검증
```

> **government 템플릿**: `from hwpx_helpers import *` → `make_cover_page()` → `make_section_bar()` → `make_body_para()`
> **report/base/gonmun/minutes/proposal 템플릿**: `python3 md2hwpx.py input.md --template report --output out.hwpx` 직접 사용 가능

### md2hwpx.py 사용법 (report/base 등 일반 템플릿)

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/md2hwpx.py" input.md \
  --template report --output result.hwpx --title "문서 제목"
python3 "${CLAUDE_SKILL_DIR}/scripts/fix_namespaces.py" result.hwpx
python3 "${CLAUDE_SKILL_DIR}/scripts/validate.py" result.hwpx
```

- 표 열 너비: 내용 길이에 비례하여 자동 배분 (한글=2, ASCII=1 가중치)
- 셀 여백: 좌우 1mm, 상하 0.5mm
- 줄간격: 160% (report 템플릿 기본값)
- 표/이미지: `treatAsChar="1"` (글자처럼 취급)

### 서식 후처리 (빈 줄 삽입)

md2hwpx.py는 모든 문단을 연속 배치한다. 대단원(`##`) 앞 빈 줄 2개, 중단원(`###`) 앞 빈 줄 1개, 표 뒤 빈 줄 1개는 section0.xml을 후처리하여 삽입한다. 페이지넘김은 사용하지 않는다 — 강제 페이지 분리는 레이아웃을 흐트러뜨리므로, 구분은 공백으로만 표현한다.

```python
import zipfile, re, os

def format_spacing(hwpx_path):
    """
    report 템플릿 기준:
    - ## (charPrIDRef="8") 앞에 빈 줄 2개
    - ### (charPrIDRef="13") 앞에 빈 줄 1개
    - 표(</hp:tbl>) 뒤에 빈 줄 1개
    """
    with zipfile.ZipFile(str(hwpx_path), "r") as z:
        section = z.read("Contents/section0.xml").decode("utf-8")

    pid = 900000

    def empty_para():
        nonlocal pid; pid += 1
        return (f'<hp:p id="{pid}" paraPrIDRef="0" styleIDRef="0" '
                f'pageBreak="0" columnBreak="0" merged="0">'
                f'<hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>')

    # 1. ## 헤딩 앞에 빈 줄 2개 (문서 선두의 ## 제외)
    h2_pos = [m.start() for m in re.finditer(
        r'<hp:p\s[^>]*?pageBreak="[01]"[^>]*>', section)
        if 'charPrIDRef="8"' in section[m.start():m.start()+500]]
    body_start = section.find('<hs:sec')
    body_start = section.find('>', body_start) + 1 if body_start != -1 else 0
    for pos in reversed(h2_pos):
        # 문서 맨 앞의 첫 ## 에는 공백 삽입 안 함
        if pos <= body_start + 200:
            continue
        section = section[:pos] + empty_para() + "\n" + empty_para() + "\n" + section[pos:]

    # 2. ### 헤딩 앞에 빈 줄 (뒤→앞 삽입)
    h3_pos = [m.start() for m in re.finditer(
        r'<hp:p\s[^>]*?pageBreak="[01]"[^>]*>', section)
        if 'charPrIDRef="13"' in section[m.start():m.start()+500]]
    for pos in reversed(h3_pos):
        section = section[:pos] + empty_para() + "\n" + section[pos:]

    # 3. 표 뒤 빈 줄
    tbl_ends = [section.find('</hp:p>', m.end()) + 7
                for m in re.finditer(r'</hp:tbl>', section)]
    for pos in reversed(tbl_ends):
        if pos > 0 and not section[pos:pos+50].strip().startswith('</hs:sec>'):
            section = section[:pos] + "\n" + empty_para() + section[pos:]

    # ZIP 재패킹
    tmp = str(hwpx_path) + ".tmp"
    with zipfile.ZipFile(str(hwpx_path), "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "Contents/section0.xml":
                    zout.writestr(item, section.encode("utf-8"))
                elif item.filename == "mimetype":
                    zout.writestr(item, zin.read(item.filename),
                                  compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, zin.read(item.filename))
    os.replace(tmp, str(hwpx_path))
```

> charPrIDRef 값은 템플릿에 따라 다르다. report 기준: `8`=##, `13`=###. 다른 템플릿은 `references/template-styles.md` 참조.

### 이미지 인라인 삽입 (md2hwpx.py 생성 후)

md2hwpx.py는 이미지를 자동 삽입하지 않는다. 생성 후 별도로 삽입해야 한다.

```python
import zipfile, re, os, sys, subprocess
from pathlib import Path
from PIL import Image

SKILL_DIR = Path("${CLAUDE_SKILL_DIR}")
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from hwpx_helpers import make_image_para, add_images_to_hwpx, update_content_hpf

HWPX = Path("result.hwpx")

# 1. ZIP에 이미지 추가
imgs = [{"file": "photo.png", "id": "photo", "src_path": "/abs/path/photo.png"}]
add_images_to_hwpx(str(HWPX), imgs)
update_content_hpf(str(HWPX), imgs)

# 2. section0.xml에 hp:pic 인라인 삽입
with zipfile.ZipFile(str(HWPX), "r") as z:
    section = z.read("Contents/section0.xml").decode("utf-8")

with Image.open("/abs/path/photo.png") as im:
    w_px, h_px = im.size
w_hu = int(120 * 283.5)  # 목표 폭 120mm
h_hu = int(w_hu * h_px / w_px)  # 비율 유지
pic_xml = make_image_para("photo", width=w_hu, height=h_hu, parapr="0")

# 삽입할 위치 찾기 (특정 텍스트 앞에 삽입)
match = re.search(r"삽입_위치_텍스트", section)
p_start = section.rfind("<hp:p", 0, match.start())
section = section[:p_start] + pic_xml + "\n" + section[p_start:]

# 3. 재패킹
tmp = str(HWPX) + ".tmp"
with zipfile.ZipFile(str(HWPX), "r") as zin:
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "Contents/section0.xml":
                zout.writestr(item, section.encode("utf-8"))
            elif item.filename == "mimetype":
                zout.writestr(item, zin.read(item.filename), compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(item, zin.read(item.filename))
os.replace(tmp, str(HWPX))

# 4. 후처리
subprocess.run([sys.executable, str(SKILL_DIR/"scripts/fix_namespaces.py"), str(HWPX)], check=True)
```

### section0.xml 핵심 규칙

1. **첫 문단 첫 run에 secPr + colPr 필수** — 없으면 문서가 안 열림
2. **모든 문단 id는 고유 정수**
3. **XML 특수문자 `<>&"` 반드시 이스케이프**
4. **표지→본문 사이 `pageBreak="1"` 문단 삽입**

> XML 구조 상세: [references/xml-structure.md](references/xml-structure.md)

### 빌드 명령

```bash
# 1. section0.xml을 임시 파일로 작성 (Python 스크립트로 생성)

# 2. 빌드 (government 템플릿 사용 시)
python3 "${CLAUDE_SKILL_DIR}/scripts/build_hwpx.py" \
  --header "${CLAUDE_SKILL_DIR}/templates/government/header.xml" \
  --section /tmp/section0.xml \
  --title "문서 제목" \
  --output result.hwpx

# 3. 네임스페이스 후처리 (필수!)
python3 "${CLAUDE_SKILL_DIR}/scripts/fix_namespaces.py" result.hwpx

# 4. 검증
python3 "${CLAUDE_SKILL_DIR}/scripts/validate.py" result.hwpx
```

### Python 빌드 스크립트 패턴

> **`scripts/hwpx_helpers.py`를 import하여 검증된 함수를 재사용한다.**

```python
import subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path("${CLAUDE_SKILL_DIR}/scripts")))
from hwpx_helpers import *

SKILL_DIR = Path("${CLAUDE_SKILL_DIR}")
REF_HWPX = SKILL_DIR / "assets" / "government-reference.hwpx"
OUTPUT = Path("output.hwpx")

# 0. government header 검증 (잘못된 header 사용 방지)
GOV_HEADER = SKILL_DIR / "templates/government/header.xml"
validate_header_for_government(GOV_HEADER)

# 1. secPr 추출
secpr, colpr = extract_secpr_and_colpr(REF_HWPX)

# 2. section0.xml 조립
parts = []
parts.append(f'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>')
parts.append(f'<hs:sec {NS_DECL}>')
parts.append(make_first_para(secpr, colpr))
parts.extend(make_cover_page("문서 제목", subtitle="(부제)", date="2026. 3."))
parts.append(make_cover_banner("문서 제목"))  # 본문 페이지 배너
parts.append(make_empty_line())
parts.append(make_section_bar("1", "섹션 제목"))
parts.append(make_body_para("가.", "본문 내용"))
parts.append(f'</hs:sec>')
section_xml = "\n".join(parts)

# 3. 빌드
Path("/tmp/section0.xml").write_text(section_xml, encoding="utf-8")
subprocess.run(["python3", str(SKILL_DIR/"scripts/build_hwpx.py"),
    "--header", str(SKILL_DIR/"templates/government/header.xml"),
    "--section", "/tmp/section0.xml", "--output", str(OUTPUT)], check=True)

# 4. (이미지 있으면) add_images_to_hwpx() + update_content_hpf()

# 5. 후처리 + 검증
subprocess.run(["python3", str(SKILL_DIR/"scripts/fix_namespaces.py"), str(OUTPUT)], check=True)
subprocess.run(["python3", str(SKILL_DIR/"scripts/validate.py"), str(OUTPUT)])
```

### hwpx_helpers.py 제공 함수

| 함수 | 설명 |
|------|------|
| `next_id()` | 고유 ID 생성 |
| `xml_escape(text)` | XML 특수문자 이스케이프 |
| `validate_header_for_government(path)` | header.xml이 government용인지 검증 (크기·charPr 수 체크) |
| `extract_secpr_and_colpr(hwpx)` | HWPX에서 secPr+colPr 추출 |
| `make_first_para(secpr, colpr)` | 첫 문단 (secPr 포함) |
| `make_empty_line()` | 빈 줄 |
| `make_page_break()` | 페이지 넘김 |
| `make_text_para(text, charpr, parapr)` | 텍스트 문단 |
| `make_body_para(marker, text)` | 본문 (마커+내용) |
| `make_cover_banner(title)` | 표지 배너 (3×2 컬러 테이블) |
| `make_section_bar(number, title)` | 섹션 바 (1×3 컬러 테이블) |
| `make_cover_page(title, subtitle, date)` | 표지 전체 + pageBreak |
| `make_image_para(binary_item_id, w, h)` | 이미지 (전체 hp:pic 구조) |
| `add_images_to_hwpx(path, images)` | ZIP에 이미지 추가 |
| `update_content_hpf(path, images)` | content.hpf에 이미지 등록 |
| `NS_DECL` | 네임스페이스 선언 상수 |

> 스타일 ID 상세: [references/template-styles.md](references/template-styles.md)

### 이미지 포함 시

> **이미지 `<hp:pic>` 구조가 불완전하면 한컴오피스가 크래시한다.**
> 반드시 [references/xml-structure.md](references/xml-structure.md)의 "이미지 삽입" 섹션을 읽고 전체 구조를 사용할 것.

---

## 워크플로우 B: 템플릿 치환

> **기존 양식의 플레이스홀더를 교체. 양식 문서에 적합.**

```
[1] 양식 파일 복사 → [2] ObjectFinder로 텍스트 조사
[3] 플레이스홀더 매핑 → [4] ZIP-level 치환 → [5] fix_namespaces.py → [6] 검증
```

### ZIP-level 치환

```python
import zipfile, os

def zip_replace(src, dst, replacements):
    tmp = dst + ".tmp"
    with zipfile.ZipFile(src, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.startswith("Contents/") and item.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    for old, new in replacements.items():
                        text = text.replace(old, new)
                    data = text.encode("utf-8")
                if item.filename == "mimetype":
                    zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, data)
    os.replace(tmp, dst)

# ⚠️ 필수: fix_namespaces 후처리
import subprocess, sys
subprocess.run([sys.executable,
    "C:/Users/hccga/.claude/skills/hwpx/scripts/fix_namespaces.py", dst], check=True)
# 검증
subprocess.run([sys.executable,
    "C:/Users/hccga/.claude/skills/hwpx/scripts/validate.py", dst])
```

> **⚠️ fix_namespaces.py 누락 = 문서 안 열림!**
> ZIP을 재패킹하면 Python의 zipfile/lxml이 XML 네임스페이스 선언을 누락/변형시킨다.
> `fix_namespaces.py`를 실행하지 않으면 한글에서 문서가 열리지 않거나 빈 페이지로 표시된다.
> **ZIP-level로 HWPX를 수정하는 모든 경우(워크플로우 B, C, F, 직접 수정 등)에 반드시 마지막에 실행할 것.**

### BinData 이미지 교체 (ZIP-level)

기존 HWPX의 삽화를 교체할 때는 **원본 BMP 크기와 동일하게** 리사이즈하여 교체한다.

```python
from PIL import Image
import io

def zip_replace_with_images(src, dst, text_replacements, image_replacements):
    """
    text_replacements: {"기존텍스트": "새텍스트", ...}
    image_replacements: {"BinData/image42.BMP": "new_image.png", ...}
    """
    tmp = dst + ".tmp"
    with zipfile.ZipFile(src, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in image_replacements:
                    # 원본 크기 확인 후 동일 크기 BMP로 교체
                    orig = Image.open(io.BytesIO(zin.read(item.filename)))
                    new_img = Image.open(image_replacements[item.filename])
                    new_img = new_img.convert("RGB").resize(orig.size, Image.LANCZOS)
                    buf = io.BytesIO()
                    new_img.save(buf, "BMP")
                    zout.writestr(item, buf.getvalue())
                elif item.filename.startswith("Contents/") and item.filename.endswith(".xml"):
                    text = zin.read(item.filename).decode("utf-8")
                    for old, new in text_replacements.items():
                        text = text.replace(old, new)
                    zout.writestr(item, text.encode("utf-8"))
                elif item.filename == "mimetype":
                    zout.writestr(item, zin.read(item.filename), compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, zin.read(item.filename))
    os.replace(tmp, dst)
    # ⚠️ 필수 후처리
    subprocess.run([sys.executable,
        "C:/Users/hccga/.claude/skills/hwpx/scripts/fix_namespaces.py", dst], check=True)
```

### 양식 선택 정책

1. 사용자 업로드 양식 → 해당 파일 사용
2. `${CLAUDE_SKILL_DIR}/assets/report-template.hwpx`
3. HwpxDocument.new()는 최후의 수단

---

## 워크플로우 C: 기존 문서 편집

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/office/unpack.py" doc.hwpx ./unpacked/
# XML 편집 후
python3 "${CLAUDE_SKILL_DIR}/scripts/office/pack.py" ./unpacked/ edited.hwpx
python3 "${CLAUDE_SKILL_DIR}/scripts/fix_namespaces.py" edited.hwpx
```

## 워크플로우 D: 레퍼런스 기반 생성

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_template.py" reference.hwpx
# header.xml 추출 후 동일 스타일 ID로 새 section0.xml 작성
python3 "${CLAUDE_SKILL_DIR}/scripts/build_hwpx.py" \
  --header /tmp/ref_header.xml --section /tmp/new_section.xml --output result.hwpx
python3 "${CLAUDE_SKILL_DIR}/scripts/fix_namespaces.py" result.hwpx
```

## 워크플로우 E: 읽기/추출

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/text_extract.py" doc.hwpx
python3 "${CLAUDE_SKILL_DIR}/scripts/text_extract.py" doc.hwpx --format markdown
```

---

## 워크플로우 F: 양식 복제 (★ 복잡한 양식에 필수)

> **기존 HWPX를 통째로 복사 + 텍스트만 치환. 테이블·이미지·스타일 100% 보존.**
>
> ⚠️ **테이블 5개 이상 또는 이미지 포함이면 반드시 워크플로우 F 사용.**
> 워크플로우 D는 header만 재활용하고 section을 새로 만들기 때문에 구조의 97.5%를 잃는다.

### 전체 흐름

```
[1] 원본 양식 분석:  clone_form.py --analyze sample.hwpx
[2] 구문 치환 맵 작성 (JSON): {"원본 문구": "새 문구", ...}
[3] (선택) 키워드 폴백 맵 작성: {"재난": "교육위기", "안전": "AI교육", ...}
[4] 복제 실행:  clone_form.py sample.hwpx output.hwpx --map map.json --keywords kw.json
[5] fix_namespaces.py 후처리 (필수!)
[6] validate.py 검증
```

### 2단계 치환 전략

| 단계 | 범위 | 용도 |
|------|------|------|
| Phase 1 (--map) | 전체 XML | 긴 문구·문장 단위 치환 |
| Phase 2 (--keywords) | `<hp:t>` 내부만 | 남은 키워드 개별 치환 (폴백) |

> 키워드는 길이 내림차순 정렬하여 "재난안전관리"가 "재난"보다 먼저 매칭된다.
> Phase 2는 `<hp:t>` 태그 안의 텍스트만 대상이므로 XML 구조를 손상시키지 않는다.

### CLI 사용법

```bash
# 분석
python3 "${CLAUDE_SKILL_DIR}/scripts/clone_form.py" --analyze sample.hwpx

# 복제 (구문 치환만)
python3 "${CLAUDE_SKILL_DIR}/scripts/clone_form.py" \
  sample.hwpx output.hwpx --map replacements.json

# 복제 (구문 + 키워드 폴백)
python3 "${CLAUDE_SKILL_DIR}/scripts/clone_form.py" \
  sample.hwpx output.hwpx --map map.json --keywords keywords.json --validate

# 후처리 (필수!)
python3 "${CLAUDE_SKILL_DIR}/scripts/fix_namespaces.py" output.hwpx
python3 "${CLAUDE_SKILL_DIR}/scripts/validate.py" output.hwpx
```

### Python API

```python
from clone_form import clone, analyze, extract_texts, validate_result

# 분석
texts = analyze("sample.hwpx")

# 복제
clone("sample.hwpx", "output.hwpx",
      replacements={"원본 문구": "새 문구"},
      keywords={"재난": "교육위기"},
      title="새 문서 제목", creator="작성자")

# 검증
result = validate_result("sample.hwpx", "output.hwpx",
                         replacements={...}, keywords={...})
print(f"커버리지: {result['coverage_pct']:.1f}%")
```

### 워크플로우 D vs F 비교

| 항목 | D (레퍼런스 기반) | F (양식 복제) |
|------|------------------|--------------|
| 원본 구조 보존 | ~2.5% | **100%** |
| 테이블 | ❌ 재구성 필요 | ✅ 그대로 |
| 이미지 | ❌ BinData 누락 | ✅ 그대로 |
| 스타일 | ⚠️ ID 매칭 필요 | ✅ 그대로 |
| 적합한 경우 | 간단한 텍스트 문서 | **복잡한 양식** |

---

## 워크플로우 G: 양식 세밀 수정 (HwpxModifier)

> **기존 양식의 텍스트를 정규식/인덱스로 정밀 치환하고, 문단 들여쓰기를 조정한다.**
> 워크플로우 B(단순 치환)로 부족하고, 워크플로우 F(전체 복제)가 과할 때 사용.
>
> ⚠️ **단순 텍스트 치환은 워크플로우 B/F 사용.** 이 워크플로우는 문단 속성 변경, 정규식 치환 등 구조적 수정이 필요할 때만 사용.

### Python API

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("${CLAUDE_SKILL_DIR}/scripts")))
from hwpx_modifier import HwpxModifier, modify_hwpx_template

# 방법 1: Context Manager
with HwpxModifier("양식.hwpx") as doc:
    # 문서 구조 확인
    print(doc.get_text_summary())          # 인덱스 포함 텍스트 요약
    texts = doc.get_all_texts()            # [(인덱스, 텍스트), ...]

    # 텍스트 치환
    doc.replace_text("기존텍스트", "새텍스트")           # 부분 일치
    doc.replace_text_exact("정확히일치", "새텍스트")     # 정확히 일치
    doc.replace_text_by_index(5, "인덱스5의 새 텍스트")  # 인덱스 지정
    doc.replace_by_pattern(r'\d{4}년', '2026년')        # 정규식

    # 들여쓰기 (한글 "왼쪽 10" = 1000 HWPUNIT)
    doc.set_indent_rules({
        r'^[가-힣]\.': 1000,   # "가." "나." 등: 왼쪽 10
        r'^-': 2000,           # 하이픈 항목: 왼쪽 20
    })
    doc.set_paragraph_indent("특정 텍스트", 3000)  # 특정 문단만

    doc.save("결과.hwpx")

# 방법 2: 편의 함수 (단순 치환)
modify_hwpx_template(
    template_path="양식.hwpx",
    output_path="결과.hwpx",
    replacements={"{{제목}}": "새 제목", "{{날짜}}": "2026-03-21"}
)
```

### HwpxModifier 제공 메서드

| 메서드 | 설명 |
|--------|------|
| `get_text_summary(max_items=50)` | 문서 텍스트 구조 요약 (인덱스 포함) |
| `get_all_texts()` | 모든 텍스트를 `[(인덱스, 텍스트), ...]`로 반환 |
| `replace_text(old, new)` | 부분 일치 텍스트 치환 |
| `replace_text_exact(old, new)` | 정확히 일치하는 텍스트만 치환 |
| `replace_text_by_index(idx, new)` | 특정 인덱스 위치 수정 |
| `replace_by_pattern(pattern, repl)` | 정규식 패턴 기반 치환 |
| `batch_replace(dict)` | 여러 텍스트 일괄 치환 |
| `set_indent_rules(rules)` | 정규식 패턴별 들여쓰기 일괄 적용 |
| `set_paragraph_indent(text, left)` | 특정 텍스트 포함 문단 들여쓰기 |

> **들여쓰기 단위**: 한글 "왼쪽 10" = 1000 HWPUNIT, 1mm = 283 HWPUNIT

### 셀 시맨틱 편집 메서드 (woo773/hangle 어휘 차용, 2026-05-04)

> **표 셀의 시각 속성을 좌표 기반으로 직접 편집한다. borderFill 풀에 자동 등록·dedup 되며 lineSegArray 더미 처리와 호환.**
> 의존성 추가 없음 (순수 Python + lxml). win32com 미사용.

| 메서드 | 설명 |
|--------|------|
| `set_cell_bg(table_index, row, col, r, g, b)` | 셀 배경 RGB. 기존 테두리 유지. (woo773 `셀배경색`) |
| `set_cell_border(table_index, row, col, side, style, color=None, width_mm=None)` | 셀 한 면 테두리. side: top/bottom/left/right/all, style: none/solid/thick/dotted/dashed/double. `width_mm` 으로 임의 두께 지정 가능 (기본: solid 0.12mm, thick 0.4mm). 'thick' 은 type=SOLID + width=0.4mm 의 조합. **THICK 은 HWPX 에 존재하지 않는 type 이므로 사용 금지** |
| `set_cell_size(table_index, row, col, width_mm=None, height_mm=None)` | 셀 폭·높이 mm. (woo773 `셀너비/셀높이`) |
| `set_cell_inner_margin(table_index, row, col, top_mm, bottom_mm, left_mm, right_mm)` | 셀 안쪽 여백 mm. (woo773 `안쪽여백`) |
| `set_table_border_color(table_index, r, g, b)` | 표 안 모든 SOLID 테두리 색 일괄 변경. NONE은 그대로. (woo773 `테두리색`) |
| `merge_cells(table_index, row, col, rowspan, colspan)` | 영역 병합 — anchor `cellSpan` 갱신 + 가려진 `<hp:tc>` 삭제 + width/height 합산 |
| `apply_run_charpr_variant(table_index, row, col, **kwargs)` | 셀 안 모든 `<hp:run>` 에 charPr 변형 적용. kwargs: `width`(장평 %), `letter_spacing`(자간 %), `bold`, `italic`, `underline`, `text_color` |
| `table_cursor(table_index)` | 메서드 체이닝 인터페이스 (TableCursor 반환) |

### TableCursor — 메서드 체이닝 인터페이스 (2026-05-04)

좌표 + 셀 편집을 점(.)으로 이어 부르는 fluent 인터페이스. 외부 의존성 0,
순수 Python wrapper.

| 메서드 | 설명 |
|---|---|
| `at(row, col)` | 좌표 이동 |
| `right(n)` / `left(n)` / `up(n)` / `down(n)` | 상대 이동 |
| `bg(r,g,b)` | 배경 RGB |
| `border(side, style, color, width_mm)` | 셀 테두리 |
| `size(width_mm, height_mm)` | 셀 크기 |
| `inner_margin(top, bot, left, right)` | 셀 안쪽 여백 mm |
| `merge(rowspan, colspan)` | 영역 병합 |
| `bold(on)` / `italic(on)` / `underline(on)` | 진하게/기울임/밑줄 |
| `width(percent)` | 장평 % (woo773 `장평`) |
| `letter_spacing(percent)` | 자간 % (woo773 `자간`) |
| `text_color(color)` | 글자색 |
| `text(s)` | 셀 텍스트 교체 |

```python
with HwpxModifier("template.hwpx") as doc:
    cur = doc.table_cursor(0)
    # 헤더 4셀 진하게 + 옅은 파랑 배경
    for c in range(4):
        cur.at(0, c).bg(218,229,243).bold().text(f"열{c}")
    # 강조 셀
    cur.at(1, 1).text_color((220,20,60)).bold().letter_spacing(-12).text("100")
    # 영역 병합
    cur.at(1, 2).merge(rowspan=2, colspan=2).text("MERGED")
    doc.save("output.hwpx")
```

```python
with HwpxModifier("표양식.hwpx") as doc:
    # 헤더 행 진한 파랑 배경
    for c in range(4):
        doc.set_cell_bg(0, 0, c, 218, 229, 243)
    # 표 전체 테두리색 진한 파랑
    doc.set_table_border_color(0, 25, 54, 87)
    # (1,1) 셀 위·아래 굵은선
    doc.set_cell_border(0, 1, 1, 'all', 'thick')
    # (2,2) 셀 안쪽 여백 2mm
    doc.set_cell_inner_margin(0, 2, 2, 2, 2, 2, 2)
    # (3,0) 셀 높이 20mm
    doc.set_cell_size(0, 3, 0, height_mm=20)
    # (1,2)~(2,3) 영역을 2x2 로 병합
    doc.merge_cells(0, 1, 2, rowspan=2, colspan=2)
    doc.save("output.hwpx")
```

> **borderFill dedup**: 같은 시각 속성(테두리 4면 + 색 + 배경)이면 동일 borderFill id 를 재사용한다. `border_fill_signature()` 키 기반.
> **단위 변환**: `hwpx_helpers.mm_to_hwpunit(mm)`, `pt_to_hwpunit(pt)`, `rgb_to_hex(r,g,b)`.
> **borderFill 빌더**: `hwpx_helpers.build_border_fill_xml(id, left, right, top, bottom, border_color, bg_rgb)` 단독 사용 가능.

---

## 워크플로우 H: 양식 부분 추출 및 표 조작 (HwpxFormFiller)

> **문서에서 붙임/별지 섹션만 추출하고, 표 구조를 분석하고, 좌표 기반으로 셀을 채운다.**
> clone_form.py가 전체 문서 복제라면, HwpxFormFiller는 부분 추출 + 구조 변경.

### 전체 흐름

```
[1] 문서 열기 → [2] 양식 섹션 추출 (optional)
[3] 표 구조 분석 (analyze_form_table)
[4] 플레이스홀더 템플릿 생성 → ★ STOP: 사용자 검토
[5] 검토 완료 후 좌표 기반 셀 채우기 / 행 추가
[6] 저장
```

> **⚠️ 템플릿 활용 시 필수 프로토콜 (Step 4)**
>
> 기존 HWPX를 양식으로 사용하여 `fill_cells_directly()`로 내용을 채울 때:
> 1. 먼저 `analyze_form_table()`로 행/열 좌표를 확인한다.
> 2. 내용 셀에 `{{제목}}`, `{{일시}}` 등 플레이스홀더를 넣어 템플릿을 생성한다.
> 3. **생성된 템플릿을 열어 사용자에게 보여주고, 좌표가 맞는지 검토를 받는다.**
> 4. 사용자가 확인한 후에만 실제 내용을 채운다.
>
> 이미 검증된 플레이스홀더 템플릿이 있으면 Step 4를 건너뛸 수 있다.

### Python API

```python
from hwpx_form_filler import HwpxFormFiller

with HwpxFormFiller("공문.hwpx") as doc:
    # 섹션 추출 (문서의 특정 부분만 작업)
    section = doc.find_section_by_keyword("붙임 2")
    doc.extract_form_section("붙임 2", "붙임2만.hwpx")

    # 표 구조 분석
    info = doc.analyze_table_structure(0)  # 첫 번째 표
    # → {'rows': 5, 'cols': 3, 'labels': [(0,0,'항목'), ...], 'contents': [(0,1,''), ...]}

    # 좌표 기반 셀 채우기 (\n으로 다중 문단 지원)
    doc.fill_cells_directly({
        (1, 1): "홍길동",
        (2, 1): "첫째줄\n둘째줄\n셋째줄",
    }, table_index=0)

    # 행 추가
    doc.add_table_row(table_index=0, after_row=3, contents=["", "새 항목", ""])

    # 행 복제 후 내용 수정
    doc.duplicate_row_with_content(
        table_index=0, source_row=2,
        mapping={0: "새 번호", 1: "새 내용"}
    )

    doc.save("결과.hwpx")
```

### HwpxFormFiller 제공 메서드

| 메서드 | 설명 |
|--------|------|
| `find_section_by_keyword(keyword)` | "붙임 2", "별지 제1호" 등으로 섹션 범위 찾기 |
| `extract_form_section(keyword, output)` | 섹션 추출하여 새 파일로 저장 |
| `analyze_table_structure(table_index)` | 표 구조 분석 (행/열, 레이블/내용 셀 구분) |
| `fill_cells_directly(cell_data, table_index)` | 좌표 기반 셀 채우기 `{(행,열): "내용"}` |
| `add_table_row(table_index, after_row, contents)` | 행 추가 (cellAddr/rowSpan/rowCnt 자동 업데이트) |
| `duplicate_row_with_content(table_index, source_row, mapping)` | 행 복제 후 내용 수정 |

> **셀 채우기 시 `\n`**은 각 줄이 별도 `<hp:p>` 문단으로 생성된다.
> **행 추가/복제** 시 `rowCnt`, `<sz height>`, `cellAddr` 속성이 자동으로 업데이트된다.

---

## 워크플로우 I: HWPX 병합 (여러 파일을 하나로)

> 반드시 **lxml 파서**를 사용하여 문단 단위로 복사. 정규식으로 XML을 자르면 태그 불일치 오류 발생.

### 케이스 A: 같은 템플릿으로 만든 파일끼리 (간단)

같은 header.xml을 공유하므로 charPr/paraPr 리맵 불필요.

```python
from lxml import etree
from copy import deepcopy
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"

# 1. Part 2 첫 문단(secPr/ctrl) 건너뛰기
# 2. Part 2 문단 ID 오프셋 (충돌 방지)
# 3. 페이지 넘김 문단 삽입 후 Part 2 문단 추가
# 4. Part 1 기반으로 ZIP 조립 (section0.xml만 교체)
# 5. ★ content.hpf에 모든 BinData 등록 (아래 참조)
```

> **⚠️ 이미지 포함 파일 병합 시 content.hpf 필수 업데이트**
>
> 기반 파일의 content.hpf만 복사하면, **다른 파일의 이미지가 hpf에 미등록되어 한컴에서 엑스박스로 표시된다.**
> 병합 후 반드시 모든 BinData를 스캔하여 누락 항목을 content.hpf에 등록해야 한다.
>
> ```python
> import re
> # 병합 완료 후
> with zipfile.ZipFile(output, "r") as z:
>     hpf = z.read("Contents/content.hpf").decode("utf-8")
>     existing = set(re.findall(r'<opf:item id="([^"]+)"[^>]*BinData', hpf))
>     new_items = ""
>     for name in z.namelist():
>         if name.startswith("BinData/"):
>             fname = name.split("/", 1)[1]
>             img_id = fname.rsplit(".", 1)[0]
>             if img_id not in existing:
>                 ext = fname.rsplit(".", 1)[-1].lower()
>                 mime = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png",
>                         "bmp":"image/bmp"}.get(ext, "image/png")
>                 new_items += (f'<opf:item id="{img_id}" href="BinData/{fname}" '
>                               f'media-type="{mime}" isEmbeded="1"/>')
>     if new_items:
>         hpf = hpf.replace("</opf:manifest>", new_items + "</opf:manifest>")
>         # ZIP 재패킹하여 content.hpf 교체
> ```

### 케이스 B: 다른 템플릿/스타일의 파일 병합 (★ 복잡)

header.xml의 charPr/paraPr/borderFill/fontRef ID가 다르므로, 한쪽 스타일을 다른 쪽 header에 추가하고 리맵해야 한다.

#### 전체 절차

```
[1] 양쪽 header.xml + section0.xml 파싱
[2] 추가할 파일(FILE1)의 charPr/paraPr을 기반 파일(FILE2)의 header에 새 ID로 추가
    - charPr: borderFillIDRef="1" (테두리 없음으로 고정, 박스 방지)
    - paraPr: border borderFillIDRef="1"
    - fontRef: 폰트 이름 기반으로 ID 리맵 (중요!)
[3] 표 전용 깨끗한 borderFill 생성 (SOLID 테두리, 배경 없음)
[4] FILE1 section의 charPrIDRef/paraPrIDRef/표 borderFillIDRef를 새 ID로 리맵
[5] FILE1 section의 이미지 참조명을 접두어로 변경 (충돌 방지)
[6] 기반 파일(FILE2)의 secPr 문단에서 제목 텍스트 run 제거
    ⚠️ secPr 문단 안에 제목 텍스트가 포함된 경우 있음 (한글 특성)
[7] FILE2의 모든 styleIDRef → "0" (바탕글 통일, 스타일 기반 재정렬 방지)
[8] section 병합: secPr 직후에 FILE1 내용 → 페이지넘김 → FILE2 내용
[9] ZIP 조립: FILE2를 완전한 기반으로 사용 (header/settings/META-INF 모두)
[10] content.hpf 업데이트 + fix_namespaces + validate
```

#### 핵심 코드 패턴

```python
HH = "http://www.hancom.co.kr/hwpml/2011/head"

# 폰트 이름 기반 ID 매핑 구축
font_id_map = {}  # (lang, old_id) → new_id
for ff2 in header2.iter(f"{{{HH}}}fontface"):
    lang = ff2.get("lang")
    name_to_id = {f.get("face"): f.get("id") for f in ff2.iter(f"{{{HH}}}font")}
    for ff1 in header1.iter(f"{{{HH}}}fontface"):
        if ff1.get("lang") == lang:
            for f in ff1.iter(f"{{{HH}}}font"):
                if f.get("face") in name_to_id:
                    font_id_map[(lang, f.get("id"))] = name_to_id[f.get("face")]

# charPr 복사 시 fontRef 리맵
lang_to_attr = {"HANGUL":"hangul", "LATIN":"latin", "HANJA":"hanja",
                "JAPANESE":"japanese", "OTHER":"other", "SYMBOL":"symbol", "USER":"user"}
fr = new_charpr.find(f"{{{HH}}}fontRef")
if fr is not None:
    for lang, attr in lang_to_attr.items():
        old_fid = fr.get(attr)
        if old_fid and (lang, old_fid) in font_id_map:
            fr.set(attr, font_id_map[(lang, old_fid)])

# secPr 문단에서 제목 텍스트 run 제거
first_para = list(root2)[0]
for run in list(first_para.iter(f"{{{HP}}}run")):
    t = run.find(f"{{{HP}}}t")
    if t is not None and t.text and t.text.strip():
        first_para.remove(run)

# 표 전용 깨끗한 borderFill 생성
clean_bf = etree.fromstring(f'''<hh:borderFill xmlns:hh="{HH}" id="{new_id}" ...>
    <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>
    ...
    <hh:diagonal type="NONE" .../>
</hh:borderFill>''')

# 표 셀(tc/tbl)만 borderFill 리맵, 나머지는 건드리지 않음
tag = elem.tag.split("}")[-1]
if tag in ("tc", "tbl"):
    bf = elem.get("borderFillIDRef")
    if bf and int(bf) in borderFill_map:
        elem.set("borderFillIDRef", str(borderFill_map[int(bf)]))
```

> 실제 구현: `scripts/merge_hwpx.py` — CLI로 직접 실행 가능:
> ```bash
> python3 "${CLAUDE_SKILL_DIR}/scripts/merge_hwpx.py" file1.hwpx file2.hwpx -o merged.hwpx --base 2 --order 12 --img-prefix "plan_"
> ```

### 주의사항 (공통)

- **반드시 lxml 파서 사용** — 정규식 불가 (표 내부 `</hp:p>` 매칭 문제)
- **셀 내 줄바꿈은 별도 `<hp:p>`로 분리** — 단일 `<hp:t>` text 안의 `\n`은 한글에서 줄바꿈으로 렌더링되지 않는다. 권장: `_set_cell_multi_paragraph`(lxml). 정규식이 꼭 필요하면 `hwpx_helpers.replace_placeholder_multiline` (innermost hp:p만 매치)
- **nested hp:p 폭발 함정** — 표는 `외부 hp:p > hp:tbl > hp:tc > hp:subList > 내부 hp:p` 구조라 단순 `<hp:p>[\s\S]*?</hp:p>` 정규식은 외부+내부 둘 다 매치된다. multi-line value 치환 시 paragraph가 곱셈으로 폭발(실측: 50KB → 244MB). 반드시 `(?:(?!<hp:p\b)[\s\S])*?` 부정 lookahead 또는 lxml 사용
- **secPr 문단에 제목 텍스트가 포함될 수 있음** — run을 확인하고 텍스트 있는 run 제거
- **styleIDRef → "0" 통일 필수** — 한글이 스타일 기반으로 내용을 재정렬할 수 있음
- **charPr의 borderFillIDRef="1"** — 다른 값이면 글자마다 박스 생김
- **fontRef 리맵 필수** — 같은 폰트라도 header마다 ID가 다름 (함초롬돋움이 0일 수도 10일 수도)
- **표 borderFill은 직접 생성** — 다른 header의 borderFill 복사하면 배경색/테두리가 의도와 다를 수 있음
- **이미지 파일명 충돌 방지** — 접두어(plan_, dept_ 등)로 BinData 파일명 변경 + section 참조도 변경
- **ZIP 기반 파일 선택** — header가 큰(스타일 많은) 파일을 기반으로 사용. 메타파일(settings.xml, META-INF)도 같은 파일에서 가져와야 호환

---

## 워크플로우 J: 시험 문제지 생성 (★ 시험/평가 전용)

> **PDF 시험지 또는 구조화된 문항 데이터를 HWPX 문제지로 변환.**
> 엔드노트 정답, 탭 정렬 선택지, 그룹 레이블/지문 등 시험 전용 XML 패턴을 지원한다.

### 전체 흐름

```
[1] PDF 읽기 → 텍스트/이미지 추출 (Read 도구 또는 text_extract.py)
[2] Claude가 내용 분석 → JSON 구조화 (아래 스키마)
[3] JSON 파일 저장
[4] exam_builder.py 실행
    → 내부에서 build_hwpx.py + fix_namespaces.py 자동 호출
[5] validate.py 검증
```

### JSON 입력 스키마

```json
{
  "title": "2026학년도 3월 모의고사 영어",
  "columns": 2,
  "style": {
    "group_label": {"charPr": "9", "paraPr": "0"},
    "passage":     {"charPr": "0", "paraPr": "0"},
    "question":    {"charPr": "0", "paraPr": "0"},
    "choice":      {"charPr": "0", "paraPr": "0"},
    "endnote_ref": {"charPr": "0"},
    "endnote_body":{"charPr": "0", "paraPr": "0"},
    "empty":       {"charPr": "0", "paraPr": "0"}
  },
  "items": [
    {
      "group": "[1-2] 다음 글을 읽고 물음에 답하시오.",
      "passage": "지문 텍스트...",
      "questions": [
        {
          "num": 1,
          "text": "윗글의 주제로 가장 적절한 것은?",
          "choices": ["선택지1", "선택지2", "선택지3", "선택지4", "선택지5"],
          "answer": "③"
        }
      ]
    },
    {
      "num": 3,
      "text": "독립 문항 텍스트",
      "choices": ["A", "B", "C", "D", "E"],
      "answer": "①"
    }
  ]
}
```

- `style`: 선택적. 생략 시 report 템플릿 기본값 사용. `--ref`로 양식 HWPX를 주면 해당 양식의 ID 사용
- `columns`: 1 또는 2 (기본 1). 시험지는 보통 2단
- `items`: 그룹 문항(`group` + `questions`)과 독립 문항(`num` + `text`) 혼합 가능
- `choices` 길이가 모두 15자 이하 → 탭 정렬 2줄 (①②③ / ④⑤), 아니면 각 1줄

### CLI 사용법

```bash
# 기본 (report 템플릿)
python3 "${CLAUDE_SKILL_DIR}/scripts/exam_builder.py" data.json -o exam.hwpx

# 양식 참조 (양식의 스타일 ID + secPr/colPr + header 사용)
python3 "${CLAUDE_SKILL_DIR}/scripts/exam_builder.py" data.json --ref form.hwpx -o exam.hwpx

# 템플릿 지정
python3 "${CLAUDE_SKILL_DIR}/scripts/exam_builder.py" data.json -t base -o exam.hwpx

# 검증
python3 "${CLAUDE_SKILL_DIR}/scripts/validate.py" exam.hwpx
```

### Python API

```python
from exam_builder import build_exam, build_section_xml

# 전체 파이프라인
build_exam("data.json", "exam.hwpx", template="report")

# 양식 참조
build_exam("data.json", "exam.hwpx", ref_hwpx="form.hwpx")

# section0.xml만 생성 (커스텀 파이프라인용)
import json
data = json.load(open("data.json", encoding="utf-8"))
xml = build_section_xml(data)
```

### 엔드노트 정답

각 질문 문단 끝에 `<hp:endNote>`로 정답을 삽입한다. 문서 끝에 미주(endnote) 목록으로 표시됨.
- `answer` 값이 빈 문자열이면 엔드노트는 생성되지만 내용이 비어있음
- 엔드노트 번호는 문항 순서대로 1부터 자동 증가

### 선택지 레이아웃

| 조건 | 레이아웃 | 예시 |
|------|---------|------|
| 모든 선택지 ≤ 15자 | `inline` (탭 정렬 2줄) | ① apple ② banana ③ cherry |
| 하나라도 > 15자 | `stacked` (각 1줄) | ① 긴 선택지 내용... |

---

## 워크플로우 K: HWP(바이너리) → HWPX 변환

> **레거시 .hwp 바이너리 파일을 .hwpx 개방형 XML로 변환.**
> jkf87/hwp2hwpx-python-refactor 래퍼. 한컴오피스/LibreOffice 미설치 환경(서버·리눅스)에서 유일한 순수 Python 경로.

### 언제 사용

- 사용자가 `.hwp` (바이너리) 파일을 주고 "이걸로 작업" 또는 "HWPX로 바꿔줘" 라고 할 때
- 한컴오피스 COM·LibreOffice headless 모두 쓸 수 없는 환경
- 한글 미설치 서버 자동화 파이프라인

### 한계 ⚠️ 중요

2026-05-04 5MB 정부 보고서 24페이지 변환 실측 결과:
- **표 셀 텍스트 통째 누락** — 표 외곽선만 남고 내부 콘텐츠가 사라짐. 목차·예산표 등 셀 기반 페이지가 빈 표로 변환됨
- **이미지·캘리그래피 손실** — 일부 이미지는 누락, 일부는 다른 placeholder로 대체. 캘리그래피 효과(외곽선·그림자) 미보존
- **자간·장평 서식 흐트러짐** — `서 울 특 별 시 교 육 청` 처럼 자간이 임의로 늘어남
- PDF 크기 비교: 원본 5.0MB → 변환 0.86MB (≈83% 콘텐츠 손실)
- `verify_hwpx.py` 는 구조만 체크하므로 통과해도 **시각 렌더링은 깨질 수 있음**. 반드시 PDF 변환 후 육안 비교 필요

**권장 사용 범위**: 단순 텍스트 위주의 짧은 .hwp (질문지·메모·간단한 공문 본문). 표·이미지·서식이 풍부한 보고서에는 사용 부적합 — 한컴/LibreOffice 가 가능하면 그쪽 우선.

### 기타
- 처음 호출 시 `pyhwp5/olefile/lxml` + `hwp2hwpx-python-refactor` 자동 설치/클론 (네트워크 필요)

### CLI 사용법

```bash
# 기본 변환 (입력 .hwp 옆에 동일명 .hwpx 생성)
python3 "${CLAUDE_SKILL_DIR}/scripts/convert_hwp.py" input.hwp

# 출력 경로 지정
python3 "${CLAUDE_SKILL_DIR}/scripts/convert_hwp.py" input.hwp -o out.hwpx

# 메타데이터만 조회 (변환 X)
python3 "${CLAUDE_SKILL_DIR}/scripts/convert_hwp.py" input.hwp --info --json
```

### Python API

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/hwpx/scripts"))
from convert_hwp import convert, info

out = convert("input.hwp", "out.hwpx")
meta = info("input.hwp")  # title, author, version, section_count, embedded_bindata_count
```

### 변환 후 권장 후처리

```bash
# 1) 네임스페이스 정합 (한글 Viewer 호환)
python3 "${CLAUDE_SKILL_DIR}/scripts/fix_namespaces.py" out.hwpx

# 2) 글자 테두리 버그 제거 (★ 변환기가 모든 글자에 네모 테두리를 박는 경우)
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_hwpx.py" --result out.hwpx --fix-borders

# 3) 구조 검증 + polaris-dvc strict 검증
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_hwpx.py" --result out.hwpx --strict
```

> **⚠️ 글자 테두리**: hwp2hwpx 변환 엔진은 charPr 다수에 SOLID 테두리 borderFill을 참조시켜
> **모든 글자에 네모 테두리**가 보이는 산출물을 만들 때가 있다. 위 2)의 `--fix-borders`로 제거한다
> (표 셀 테두리는 보존). 이 보정을 거치지 않으면 사용자에게 테두리투성이 문서가 전달된다.

### 출처

[jkf87/hwpx-skill](https://github.com/jkf87/hwpx-skill) Workflow H (2026-04-02) 차용. 변환 엔진은 [jkf87/hwp2hwpx-python-refactor](https://github.com/jkf87/hwp2hwpx-python-refactor). 글자 테두리 자동 제거는 jkf87 v1.0.5(2026-06) 차용.

---

## 워크플로우 L: ZIP-level 전역 텍스트 치환

> **양식 hwpx 의 본문·표 셀에 흩어진 단순 플레이스홀더 (`{학교명}`, `{기관명}` 등)
> 를 한 줄로 일괄 치환할 때 사용.** lxml 트리를 거치지 않아 가장 빠르고, 표 셀까지
> 빠짐없이 잡는다.

### 언제 워크플로우 B/G/H 가 아닌 L 을 쓰는가

| 상황 | 권장 |
|---|---|
| 본문 + 표 셀의 **단순 텍스트 키** 일괄 치환 | **L** |
| 본문 run 색상·밑줄 등 스타일 필터 함께 | B (`replace_text_in_runs`) |
| 표 행 추가, 셀 병합, 부분 추출 | H (`HwpxFormFiller`) |
| 문단 속성·정규식·인덱스 기반 구조 수정 | G (`HwpxModifier`) |

### 사용

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/zip_replace_all.py" \
    template.hwpx output.hwpx \
    --replace "{학교명}=중대초등학교" "{담당자}=임세범" \
    --auto-fix-ns
```

옵션:

- `--inplace --backup` : 입력 파일 자체 덮어쓰기 + `.bak` 생성
- `--auto-fix-ns` : 치환 직후 `fix_hwpx_namespaces` 자동 실행 (정규식 기반 ns 정리 + itemCnt 보정)
- `--no-ensure-linesegs` : 더미 lineSegArray 주입 비활성화 (기본은 자동 주입)

### 통합된 안전망

치환과 동시에 `Contents/section*.xml` 의 빈 lineSegArray 에 대해 자동으로 더미를
주입한다. 이 덕분에 외부 빌더로 만들어진 hwpx 도 본 워크플로 1회 실행만으로
polaris-dvc strict (JID 11004) 통과 상태로 끌어올릴 수 있다 (실측: 사업계획서 185
건, 학급독서통계 142 건 자동 보정 → 모두 0 건).

### Python 함수 임포트

```python
from zip_replace_all import zip_replace_all

stats = zip_replace_all(
    "template.hwpx",
    "output.hwpx",
    {"{학교명}": "중대초등학교", "{담당자}": "임세범"},
    ensure_linesegs=True,
)
print(stats)
# {'parts': 11, 'xml_parts': 6, 'changed_xml': 1, 'replacements': 2,
#  'decode_failed': 0, 'lineseg_injected': 0}
```

### 안전 가드

- 입력=출력 경로면 자동으로 임시 파일 사용
- `<`, `>`, `</` 가 포함된 치환 키는 경고 (XML 손상 가능)
- `mimetype` 엔트리는 항상 `ZIP_STORED` 로 보존 (HWPX 스펙 요구)

### 출처

[airmang/hwpx-skill](https://github.com/airmang/hwpx-skill) (Apache-2.0, 2026-04-24)
의 `scripts/zip_replace_all.py` 이식. lineSegArray 더미 주입 통합은 본 스킬 자체
보강.

---

## 워크플로우 M: 스타일 필터 텍스트 치환

> **글자 색·밑줄·charPrIDRef 같은 스타일 조건에 맞는 run 만 골라 치환.**
> python-hwpx 2.x 의 `HwpxDocument.replace_text_in_runs()` 스타일 필터를 활용.

### 언제 L 이 아닌 M 을 쓰는가

- 본문에서 **빨간 글씨로 표시된 단어만** 골라 치환 (학생 작품 빨간 첨삭 처리)
- **밑줄 친 단어만** 굵게 강조로 변경
- 특정 charPrIDRef (제목 스타일·인용 스타일 등) 의 텍스트만 일괄 교정
- 본문에 같은 단어가 여러 번 나오지만 **앞쪽 N개만** 치환 (`--limit`)

### 사용

```bash
# 빨간 TODO → DONE
python3 "${CLAUDE_SKILL_DIR}/scripts/style_filter_replace.py" \
    student.hwpx graded.hwpx \
    "TODO" "DONE" --color "#FF0000"

# 매칭 사전 점검
python3 "${CLAUDE_SKILL_DIR}/scripts/style_filter_replace.py" \
    input.hwpx /dev/null \
    "검토" "완료" --color "#FF0000" --underline SOLID --dry-run

# 첫 1회만 치환 (limit)
python3 "${CLAUDE_SKILL_DIR}/scripts/style_filter_replace.py" \
    input.hwpx output.hwpx "학교명" "기관명" --limit 1
```

옵션:

- `--color "#RRGGBB"` : 글자 색 필터
- `--underline SOLID` : 밑줄 타입 (`SOLID/DOTTED/DASH/...`)
- `--underline-color "#RRGGBB"` : 밑줄 색 필터
- `--char-pr <id>` : charPrIDRef 직접 지정
- `--limit N` : 최대 치환 횟수
- `--dry-run` : 매칭 run 텍스트만 출력

### Python 함수

```python
from style_filter_replace import style_replace, list_styled_runs

# 매칭 run 미리보기
matches = list_styled_runs("input.hwpx", text_color="#FF0000")
print(matches)

# 실제 치환
n = style_replace(
    "input.hwpx", "output.hwpx",
    "TODO", "DONE",
    text_color="#FF0000", underline_type="SOLID", limit=3,
)
print(f"{n}개 치환됨")
```

### 요구사항

- python-hwpx >= 2.6 (HwpxDocument API)
- 색상 필터는 입력 hwpx 의 charPr 정의에 textColor 가 명시돼 있어야 매칭됨

---

## 워크플로우 N: 자동 첨삭 메모 batch 삽입

> **JSON 으로 메모 위치·본문·작성자 목록을 주면 한 번에 메모를 추가.**
> 학생 작품 평가, 보고서 검토, 협업 코멘트 자동화에 사용.

### 사용

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/add_review_memo.py" \
    student.hwpx graded.hwpx \
    --memos memos.json \
    --default-author "임세범"
```

`memos.json` 스키마 (배열):

```json
[
  {
    "section": 0,
    "paragraph": 3,
    "text": "여기 보충 필요",
    "author": "임세범"
  },
  {
    "paragraph_text": "학습 목표:",
    "text": "구체적 행동동사 사용 권장"
  }
]
```

위치 지정 두 가지:

- `paragraph_text`: 해당 텍스트가 들어 있는 첫 paragraph 자동 매칭 (간편)
- `section + paragraph` 인덱스: 정밀 지정 (0-based)

`paragraph_text` 가 우선 적용되며, 둘 다 있으면 paragraph_text 우선.

### Python 함수

```python
from add_review_memo import add_memos_batch

added = add_memos_batch(
    "student.hwpx", "graded.hwpx",
    memos=[
        {"section": 0, "paragraph": 0, "text": "잘 썼어요", "author": "교사"},
        {"paragraph_text": "결론", "text": "근거 한 줄 더 필요"},
    ],
)
print(f"{added}개 메모 추가됨")
```

### 안전망

- 저장 직후 `inject_dummy_linesegs()` 자동 적용 → polaris-dvc strict (JID 11004) 통과
- paragraph 인덱스 범위 밖이면 WARN 출력 후 skip (전체 실패 X)
- text 누락된 메모 spec 도 WARN + skip

### 요구사항

- python-hwpx >= 2.6 (`add_memo_with_anchor` API)

### 활용 예시

수업 시나리오 — 학생 hwpx 작품 모음을 수합 → Claude 가 각 작품 분석 → 평가 코멘트
JSON 생성 → `add_review_memo` batch 적용 → 첨삭본 일괄 배포.

---

## 워크플로우 O: 레퍼런스 99% 복원 + 쪽수 가드

> **사용자가 `.hwpx` 양식을 첨부하고 "이 양식 그대로 / 쪽수 동일하게" 요청할 때.**
> 결과 문서가 레퍼런스와 **동일한 페이지 수**를 유지해야 하는 보고서·공문 작업의 기본 안전망.

### 핵심 원칙

1. **구조 보존**: `charPrIDRef` / `paraPrIDRef` / `borderFillIDRef` 참조 체계, 표 `rowCnt`/`colCnt`/`cellSz`, `secPr` 모두 동일하게 유지.
2. **텍스트만 교체**: 문단 수·표 수·`pageBreak`·`columnBreak` 변경 금지. 사용자 요청 범위(본문 텍스트, 값, 항목명)로 한정.
3. **쪽수 가드 필수**: 빌드 직후 `page_guard.py`로 레퍼런스 대비 드리프트 위험 검사. FAIL 시 결과 제출 금지.

### 기본 흐름

```bash
# 1) 워크플로우 F (양식 복제) 또는 G (세밀 수정) 또는 L (zip-level 치환) 으로 결과 빌드
python3 "${CLAUDE_SKILL_DIR}/scripts/clone_form.py" reference.hwpx \
  --replace '{"기존":"새내용"}' --output result.hwpx

# 2) 구조 검수
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_hwpx.py" \
  --source reference.hwpx --result result.hwpx --strict

# 3) 쪽수 드리프트 가드 (필수)
python3 "${CLAUDE_SKILL_DIR}/scripts/page_guard.py" \
  --reference reference.hwpx --output result.hwpx
```

### page_guard.py 가 검사하는 것

| 검사 | 임계값 (기본) | 의미 |
|---|---|---|
| 섹션 수 | 정확히 일치 | section\*.xml 개수 |
| 문단 수 | 정확히 일치 | `<hp:p>` 총 개수 (다중 섹션 합산) |
| `pageBreak` 속성 | 정확히 일치 | 명시적 페이지 넘김 문단 수 |
| `columnBreak` 속성 | 정확히 일치 | 명시적 단 넘김 |
| 표 수 + 형태 | 정확히 일치 | (rowCnt, colCnt, width, height, repeatHeader, pageBreak) 튜플 |
| 전체 텍스트 길이 | ±15% 편차 | 공백 제외 전체 글자 수 |
| 문단별 텍스트 길이 | ±25% 편차 | 같은 인덱스 문단끼리 비교 |

임계값은 `--max-text-delta-ratio`, `--max-paragraph-delta-ratio` 로 조정.
원본보다 텍스트가 압축되어야 하는 작업이면 임계값을 좁혀(0.05 등) 더 빡빡하게 검출 가능.

### Anti-pattern

- ❌ `validate.py` PASS 만으로 완료 처리 → 구조 검증일 뿐 쪽수 보장 아님
- ❌ 임계값을 무한대(`2.0` 등)로 풀어서 무조건 PASS 만들기 → 가드 기능 상실
- ❌ 사용자 명시 요청 없이 `<hp:p>`, `<hp:tbl>`, `rowCnt`, `colCnt`, `pageBreak`, `secPr` 변경

### 알고리즘 출처

레퍼런스 99% 복원 철학과 메트릭 비교 알고리즘은 [`Canine89/hwpxskill`](https://github.com/Canine89/hwpxskill) 의 `page_guard.py` 를 참조해 본 스킬 스타일(`xpath_local()` + 다중 섹션 + zip bomb 상한)로 재구현. 자세한 고지는 `THIRD_PARTY_NOTICES.md` 5번 항목.

---

## 워크플로우 P: 공공기관 보고서 글쓰기 최적화

> 보고서·기획서·시행문 초안을 빌드하기 **직전**에 글쓰기 품질 규칙을 자동 적용한다.
> 「적의를 보이는 것들」(`-적`/`의`/`것`/`들`) + 한 문장 한 줄 + 두괄식 원칙을 정규식으로 점검.

### 언제 사용

- 공공기관 보고서(`/hwpx`)·학교 학급평가보고서·교육과정 계획서 등 **무게감 있는 행정 문서**의 텍스트 초안
- AI가 생성한 마크다운/도움말 본문이 산만하거나 늘어질 때 빠르게 다듬는 전처리
- 워크플로우 A (md→HWPX) 직전에 input.md 를 한 번 통과시키는 권장 단계

### CLI 사용

```bash
# 텍스트 자동 정리 + 검토 권장 리포트 (stderr)
python3 "${CLAUDE_SKILL_DIR}/scripts/writing_optimizer.py" input.md \
    --output cleaned.md \
    --report writing_report.md

# dry-run (제안만 보고 텍스트는 보존)
python3 "${CLAUDE_SKILL_DIR}/scripts/writing_optimizer.py" input.md \
    --dry-run --report writing_report.md > /dev/null
```

### Python API

```python
import sys
sys.path.insert(0, "${CLAUDE_SKILL_DIR}/scripts")
from writing_optimizer import optimize_text, format_report

cleaned_text, suggestions = optimize_text(raw_md)
print(format_report(suggestions))
# cleaned_text 를 md2hwpx.py 입력으로 전달
```

### 자동 적용 9건 + 검토 권장 5건

| ID | 패턴 | 처리 |
|---|---|---|
| R1 | `~와/과 관련된` | → `~ 관련` 자동 |
| R3 | `~할/될 것으로 보입니다/보인다` | → `~ 예상` 자동 |
| R4 | `~한/된/진 것으로 판단됩니다/된다` | → `~ 판단` 자동 |
| R5 | `~할 예정이었으나 이를 유예하였습니다` | → `~ 예정 → 유예` 자동 |
| R6a | `~하는 것이 필요합니다` | → `~이/가 필요합니다` 자동 (받침 짝조사 자동) |
| R6b | `~하는 것이 중요합니다` | → `~이/가 중요합니다` 자동 |
| R8 | `여러/많은/각/모든 ~들이/들을/들은` | → `~이/가 / ~을/를 / ~은/는` 자동 (조사 받침 재맞춤) |
| R12 | 영문+한글 / 한글+영문 띄어쓰기 누락 | → 띄어쓰기 추가 자동 |
| R2 | `~에 대한` | 검토 권장 (생략 또는 동사형) |
| R7 | `~ 중 하나인` | 검토 권장 |
| R9 | `사회적/경제적/정치적/행정적/조직적/…` | 검토 권장 (-적 제거) |
| R10 | `~의 ~의 ~` (의 연쇄) | 검토 권장 |
| R11 | 한 문장 46자 초과 | 검토 권장 (분리 후보 표시) |

근거·원칙: `references/writing-principles.md` + `references/layout-rules.md`.

### 권장 흐름 (Workflow A 통합 예시)

```bash
# 1. 글쓰기 정리
python3 "${CLAUDE_SKILL_DIR}/scripts/writing_optimizer.py" \
    input.md --output cleaned.md --report writing_report.md

# 2. 사용자에게 검토 권장 항목 확인 시키기 (writing_report.md)
#    R2/R9/R10/R11 은 의미 손실 위험으로 자동 적용 안 됨 → 사용자 판단

# 3. md → HWPX 빌드
python3 "${CLAUDE_SKILL_DIR}/scripts/md2hwpx.py" cleaned.md output.hwpx
```

### 출처

- 정규식 규칙·신뢰도 분류: public-doc-to-hwpx v3.6.11 (Kminer2053, MIT)
  `references/layout-rules.md` 8장 표 독립 재구현
- 한국어 조사 받침 짝맞춤 처리 (`이/가`, `은/는`, `을/를`) 는 본 스킬에서 추가 보강

## 서브에이전트 검수 (★ 권장)

> **문서 생성 후 별도 서브에이전트를 생성하여 품질 검증을 수행한다.**
> 생성 에이전트와 검수 에이전트를 분리하면 실수를 줄일 수 있다.

### 검수 도구

```bash
# 원본과 비교 검수 (구조 보존 확인)
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_hwpx.py" \
  --source original.hwpx --result output.hwpx

# 단독 검수 (XML 유효성 + 구조 체크)
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_hwpx.py" --result output.hwpx

# JSON 리포트 출력 (자동화용)
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_hwpx.py" \
  --source original.hwpx --result output.hwpx --json report.json

# polaris-dvc strict 검증 (JID 위반 검출)
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_hwpx.py" --result output.hwpx --strict

# 글자 테두리 버그 자동 제거 (검사 전 보정 — 대상 파일 직접 수정)
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_hwpx.py" --result output.hwpx --fix-borders

# 쪽수 드리프트 가드 (레퍼런스 양식 보존이 중요한 경우, 워크플로 O 참조)
python3 "${CLAUDE_SKILL_DIR}/scripts/page_guard.py" \
  --reference reference.hwpx --output output.hwpx
```

> **글자 테두리 버그**: hwp→hwpx 변환(워크플로우 K) 또는 외부에서 받은 hwpx 양식을 편집할 때,
> 원본 charPr 다수가 SOLID 테두리 borderFill을 참조해 **모든 글자에 네모 테두리**가 표시되는
> 경우가 있다. `verify_hwpx.py`가 자동 경고하며, `--fix-borders`로 제거한다(표 셀 테두리는 보존, idempotent).
> **secPr 완전성**: 검수 시 첫 섹션 secPr의 `pagePr`/`margin` 자식과 가짜 secPr(비표준 속성)를 점검해
> 한컴 '손상된 문서' 사고를 사전 차단한다(XML 유효성 검사로는 못 잡음).

### 검수 항목

| 검사 | 내용 | FAIL 조건 |
|------|------|-----------|
| mimetype | 첫 엔트리 + ZIP_STORED | 위치·압축 불일치 |
| 필수 파일 | header.xml, section0.xml 등 | 누락 시 |
| XML 유효성 | 모든 XML 파싱 가능 | 파싱 오류 |
| 런 보존 | 원본 대비 런(run) 수 | **감소 시 FAIL** |
| 테이블·이미지 | 원본 대비 수량 | 감소 시 FAIL |
| section 크기 | 원본 대비 비율 | 50% 미만 시 FAIL |
| **secPr 완전성** | 첫 섹션 secPr의 pagePr/margin 자식 + 가짜 secPr 휴리스틱 | 누락·가짜 시 FAIL (한컴 '손상 문서' 방지) |
| **글자 테두리 버그** | charPr 절반 이상이 SOLID 테두리 borderFill 참조 | 검출 시 WARN (`--fix-borders`로 제거) |
| **polaris-dvc** (`--strict`) | JID 위반 (구조·컨테이너·규칙) | 위반 1건 이상 |

### polaris-dvc strict 모드

`--strict` 플래그를 주면 [PolarisOffice/polaris_dvc](https://github.com/PolarisOffice/polaris_dvc) 바이너리(`bin/polaris-dvc.exe`)가 호출되어 JID 위반을 검출한다. 4축 검증:

| 축 | JID | 내용 |
|---|---|---|
| 규칙 적합성 | 1000–7999 | 폰트·크기·스타일 (spec JSON 필요, `--spec` 으로 전달) |
| 구조 무결성 | 11000–11999 | charPrIDRef cross-ref, lineSegArray, manifest ↔ BinData |
| 컨테이너 건전성 | 12000–12999 | ZIP mimetype, 필수 entry, `__MACOSX/` 금지 |
| 스키마 적합성 | 13000–13999 | KS X 6101 XSD (오탐 多 — 기본 비활성) |

바이너리 미설치 시 graceful 폴백 (warning만 남기고 통과). 사후 발견된 알려진 패턴: hwpx 스킬이 만든 문서는 paragraph의 lineSegArray가 비어 JID 11004를 다수 발생시킨다 — HwpOffice는 보정해서 열지만 다른 구현체에는 깨진 파일로 보일 수 있음.

### 서브에이전트 워크플로우 예시

```
[메인 에이전트]
  1. clone_form.py로 문서 생성
  2. fix_namespaces.py 후처리
  ↓
[검수 서브에이전트 생성]
  3. verify_hwpx.py --source --result 실행
  4. text_extract.py로 텍스트 추출 확인
  5. PASS/FAIL 리포트 반환
  ↓
[메인 에이전트]
  6. FAIL이면 수정 후 재검수
  7. PASS이면 사용자에게 전달
```

---

## 네임스페이스 후처리 (★ 필수)

> **⚠️ 빠뜨리면 한글 Viewer에서 빈 페이지로 표시된다!**

```python
import subprocess
subprocess.run(["python3", f"{SKILL_DIR}/scripts/fix_namespaces.py", "output.hwpx"], check=True)
```

| URI | 프리픽스 |
|-----|---------|
| `.../2011/head` | `hh` |
| `.../2011/core` | `hc` |
| `.../2011/paragraph` | `hp` |
| `.../2011/section` | `hs` |

---

## 단위 변환

| 값 | HWPUNIT | 의미 |
|----|---------|------|
| 1pt | 100 | 기본 단위 |
| 1mm | 283.5 | 밀리미터 |
| A4 폭 | 59528 | 210mm |
| A4 높이 | 84186 | 297mm |
| 좌우여백 | 8504 | 30mm |
| 본문폭 | 42520 | 150mm |

---

## Critical Rules

1. **HWPX만 지원**: `.hwp`(바이너리)는 미지원
2. **secPr 필수**: 첫 문단 첫 run에 secPr + colPr
3. **mimetype**: 첫 ZIP 엔트리, ZIP_STORED
4. **네임스페이스**: `hp:`, `hs:`, `hh:`, `hc:` 접두사 유지
5. **fix_namespaces 필수**: 모든 빌드 후 반드시 실행
6. **fix_namespaces 호출법**: `subprocess.run()` 사용 (`exec()` 금지)
7. **build_hwpx.py 우선**: 새 문서는 build_hwpx.py 사용
8. **검증 필수**: 생성 후 validate.py 실행
9. **XML 이스케이프**: `<>&"` 반드시 이스케이프
10. **ID 고유성**: 모든 문단 id는 문서 내 고유
11. **이미지**: `<hp:pic>` 필수 구조 준수 → [xml-structure.md](references/xml-structure.md)
12. **템플릿 ID 호환 불가**: government charPr/paraPr/borderFill ID를 report/base 등 다른 템플릿에 사용하면 깨짐. 반드시 해당 템플릿의 ID만 사용. base charPr 3은 "16pt 제목"이 아니라 "9pt 각주"임에 주의
13. **hwpx_helpers.py 사용 필수**: md2hwpx.py 직접 실행 금지. 반드시 `from hwpx_helpers import *`로 함수를 사용하여 빌드 스크립트를 작성할 것. md2hwpx.py는 government 템플릿(컬러 배너/섹션 바)을 지원하지 않음
14. **양식 복제 시 Workflow F 필수**: 사용자가 `.hwpx` 양식을 제공하고 내용 변경을 요청하면 `clone_form.py` 사용. 절대로 `<hp:t>` 노드를 순차 덮어쓰기하거나 lxml로 텍스트를 직접 조작하지 말 것 (런 소실·서식 파괴 원인)
15. **서브에이전트 검수 권장**: 문서 생성 후 별도 서브에이전트로 `validate.py` + `text_extract.py` + 구조 비교를 실행하여 품질 검증
16. **워크플로우 G/H는 구조 변경 전용**: 단순 텍스트 치환에는 워크플로우 B/F 사용. HwpxModifier/HwpxFormFiller는 들여쓰기 조정, 정규식 치환, 표 행 추가 등 clone_form.py로 불가능한 작업에만 사용
17. **워크플로우 G/H 사용 후에도 linesegarray 자동 제거**: hwpx_modifier.py, hwpx_form_filler.py는 저장 시 linesegarray를 자동 제거하여 줄바꿈 캐시 무효화를 처리
18. **report 템플릿 borderFill 수정 완료 (2026-03-21)**: 원본 report 템플릿의 paraPr이 SOLID 테두리를 가진 borderFill을 참조하여 문단마다 가로선이 표시되던 문제를 수정. 모든 paraPr의 `borderFillIDRef`를 `"1"` (테두리 없음)으로 변경, diagonal도 `NONE`으로 수정
19. **표 열 너비는 내용 비례 배분**: md2hwpx.py의 `add_table()`이 열별 최대 텍스트 길이(한글=2, ASCII=1)에 비례하여 열 너비를 자동 배분. 최소 열 너비 2800 HWPUNIT (~10mm)
20. **이미지는 ZIP 추가 + section0.xml 인라인 삽입 2단계**: `add_images_to_hwpx()`로 BinData에 파일만 추가하면 안 보임. 반드시 `make_image_para()`로 `<hp:pic>` XML을 생성하여 section0.xml에 삽입해야 함
21. **HWPX 병합 시 lxml 필수**: 정규식으로 `<hp:p>...</hp:p>`를 추출하면 표 내부의 `</hp:p>`와 매칭되어 태그 불일치 발생. 반드시 `etree.fromstring()` → `deepcopy()` → `root.append()`로 문단 단위 복사
22. **병합 시 secPr 문단 처리**: secPr 문단 안에 제목 텍스트 run이 포함될 수 있음. 텍스트가 있는 run을 제거해야 의도치 않은 제목 표시 방지
23. **다른 템플릿 병합 시 5가지 리맵 필수**: (1) charPr ID (2) paraPr ID (3) fontRef ID (폰트 이름 기반) (4) 표 borderFillIDRef (깨끗한 borderFill 직접 생성) (5) 이미지 파일명 접두어
24. **charPr borderFillIDRef="1" 고정**: 다른 값이면 글자마다 박스 표시됨
25. **styleIDRef="0" 통일**: 다른 파일 병합 시 모든 문단의 styleIDRef를 "0"으로 변경 (스타일 기반 재정렬 방지)
26. **ZIP 기반 파일 선택**: header가 큰(스타일 많은) 파일을 기반으로 사용. settings.xml/META-INF도 같은 파일에서 가져와야 호환
28. **병합 시 content.hpf 필수 업데이트**: 기반 파일의 content.hpf만 복사하면 다른 파일의 이미지가 hpf에 미등록되어 엑스박스 표시. 병합 후 모든 BinData를 스캔하여 누락 항목을 `<opf:item>` 태그로 content.hpf에 등록해야 한다
29. **시험 문제지는 워크플로우 J**: PDF 시험지/문제지/평가지 변환 시 `exam_builder.py` 사용. 엔드노트 정답, 탭 정렬 선택지 등 시험 전용 XML 패턴 지원. JSON 데이터를 입력받아 section0.xml을 동적 생성
27. **글머리기호/번호는 텍스트로 삽입**: 한글의 `<hp:numbering>` 구조를 사용하지 않는다. 목록은 `"- 항목"`, `"1. 항목"` 텍스트를 직접 넣고 paraPr 들여쓰기로 단계를 표현. 의도적 설계 — 호환성과 단순성을 위해 네이티브 글머리기호를 사용하지 않음
30. **템플릿 활용 시 플레이스홀더 검토 필수**: `fill_cells_directly()`로 기존 HWPX에 내용을 채울 때, 검증된 템플릿이 없으면 반드시 (1) `analyze_form_table()`로 구조 분석 → (2) 플레이스홀더(`{{제목}}` 등) 템플릿 생성 → (3) **STOP하여 사용자에게 열어 보여주고 검토** → (4) 확인 후 실제 내용 채우기 순서를 따른다. 이미 검증된 플레이스홀더 템플릿이 존재하면 이 단계를 건너뛸 수 있다
31. **글자 테두리 버그·secPr 완전성 검수**: hwp→hwpx 변환(워크플로우 K)이나 외부 hwpx 양식 편집 후에는 `verify_hwpx.py`가 (a) charPr 절반 이상이 SOLID 테두리 borderFill을 참조하는 "모든 글자 네모 테두리" 버그를 자동 경고하고 → `--fix-borders`로 제거(표 셀 테두리 보존, idempotent), (b) 첫 섹션 secPr의 pagePr/margin 누락·가짜 secPr를 FAIL로 검출(한컴 '손상된 문서' 사고 방지)한다. XML 유효성(validate.py)으로는 둘 다 못 잡으므로 변환·외부양식 경로에서는 반드시 verify_hwpx.py까지 거친다 (jkf87/hwpx-skill v1.0.5 차용, THIRD_PARTY_NOTICES 2번)

---

## 상세 참조

- **XML 구조·이미지·표지 패턴**: [references/xml-structure.md](references/xml-structure.md)
- **템플릿별 스타일 ID 맵**: [references/template-styles.md](references/template-styles.md)
- **트러블슈팅**: [references/troubleshooting.md](references/troubleshooting.md)
- **보고서 양식**: [references/report-style.md](references/report-style.md)
- **공문서 양식**: [references/official-doc-style.md](references/official-doc-style.md)
- **python-hwpx API**: [references/python-hwpx-api.md](references/python-hwpx-api.md) — 라이브러리 시그니처 + 1.9 ↔ 2.x 마이그레이션
- **글쓰기 원칙 (공공기관)**: [references/writing-principles.md](references/writing-principles.md) — 개조식·두괄식·Why→How→What·「적의를 보이는 것들」 (Workflow P 근거)
- **레이아웃 최적화 규칙**: [references/layout-rules.md](references/layout-rules.md) — 한 문장 35–45자·페이지 걸침·12개 자동 변환 표 (Workflow P 근거)
- **보고서 기호**: □(16pt) → ○(15pt) → ―(15pt) → ※(13pt)
- **공문서 번호**: 1. → 가. → 1) → 가) → (1) → (가) → ① → ㉮
