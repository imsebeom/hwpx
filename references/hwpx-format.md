# HWPX (OWPML) 파일 포맷 레퍼런스

## 개요

HWPX는 한글(Hancom Office)의 차세대 문서 포맷으로, **OWPML**(Open Word-Processor Markup Language) 표준(KS X 6101:2024)을 따른다. ZIP 기반 XML 컨테이너 형식이며, DOCX/XLSX와 유사한 OPC(Open Packaging Conventions) 구조를 사용한다.

## 파일 내부 구조

```
document.hwpx (ZIP archive)
├── mimetype                    # "application/hwp+zip" (첫 번째 엔트리, 비압축)
├── META-INF/
│   ├── container.xml           # 패키지 루트 파일 위치
│   ├── container.rdf           # 관계 정보
│   └── manifest.xml            # 파일 목록
├── Contents/
│   ├── content.hpf             # 매니페스트 (OPF 형식, 섹션/헤더 목록)
│   ├── header.xml              # 문서 헤더 (스타일, 폰트, CharShape, ParaShape 정의)
│   ├── section0.xml            # 본문 섹션 (문단, 표, 그림 등)
│   ├── section1.xml            # 추가 섹션 (있는 경우)
│   └── ...
├── Preview/
│   ├── PrvImage.png            # 미리보기 이미지
│   └── PrvText.txt             # 미리보기 텍스트
├── settings.xml                # 편집 설정
└── version.xml                 # 버전 정보
```

### 핵심 규칙

- **mimetype**: 반드시 ZIP 아카이브의 **첫 번째 엔트리**여야 하며 **ZIP_STORED**(비압축)로 저장
- **content.hpf**: OPF 형식의 매니페스트. 모든 콘텐츠 파일 참조
- **header.xml**: 문서 전역 스타일 정의 (CharShape, ParaShape, BorderFill 등)
- **section*.xml**: 실제 문서 콘텐츠

## XML 네임스페이스

| 접두사 | URI | 용도 |
|--------|-----|------|
| `hp` | `http://www.hancom.co.kr/hwpml/2011/paragraph` | 문단, 런, 텍스트, 표, 컨트롤 |
| `hs` | `http://www.hancom.co.kr/hwpml/2011/section` | 섹션 루트 |
| `hc` | `http://www.hancom.co.kr/hwpml/2011/core` | 핵심 데이터 타입 |
| `hh` | `http://www.hancom.co.kr/hwpml/2011/head` | 헤더 (스타일/속성 정의) |
| `ha` | `http://www.hancom.co.kr/hwpml/2011/app` | 앱 메타데이터 |
| `hp10` | `http://www.hancom.co.kr/hwpml/2016/paragraph` | 확장 문단 요소 |
| `hpf` | `http://www.hancom.co.kr/schema/2011/hpf` | 매니페스트 (content.hpf) |
| `opf` | `http://www.idpf.org/2007/opf/` | OPF 패키지 |

## 주요 XML 요소

### 섹션 (section*.xml)

```xml
<hs:sec xmlns:hp="..." xmlns:hs="...">
  <hp:p>...</hp:p>     <!-- 문단 -->
  <hp:p>...</hp:p>     <!-- 문단 -->
</hs:sec>
```

### 문단 (Paragraph)

```xml
<hp:p id="..." paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0">
    <hp:t>텍스트 내용</hp:t>
  </hp:run>
</hp:p>
```

- `paraPrIDRef`: header.xml의 ParaShape 참조 ID
- `styleIDRef`: header.xml의 Style 참조 ID
- `charPrIDRef`: header.xml의 CharShape 참조 ID (run 레벨)

### 텍스트 런 (Run)

```xml
<hp:run charPrIDRef="2">
  <hp:t>볼드 텍스트</hp:t>
</hp:run>
```

- 하나의 문단에 여러 런 가능 (서식이 다른 텍스트)
- `charPrIDRef`로 글자 서식 참조

### 테이블 (Table)

```xml
<hp:tbl id="..." rowCnt="2" colCnt="3" cellSpacing="0" borderFillIDRef="3">
  <hp:sz width="21600" height="7200" />
  <hp:pos treatAsChar="1" />
  <hp:tr>                           <!-- 행 -->
    <hp:tc borderFillIDRef="3">     <!-- 셀 -->
      <hp:cellAddr colAddr="0" rowAddr="0" colSpan="1" rowSpan="1"/>
      <hp:cellSz width="7200" height="3600"/>
      <hp:cellMargin left="510" right="510" top="142" bottom="142"/>
      <hp:subList>
        <hp:p ...>
          <hp:run ...>
            <hp:t>셀 내용</hp:t>
          </hp:run>
        </hp:p>
      </hp:subList>
    </hp:tc>
  </hp:tr>
</hp:tbl>
```

### 섹션 속성 (Section Properties)

첫 번째 문단의 첫 번째 런에 포함됨:

```xml
<hp:secPr textDirection="HORIZONTAL" ...>
  <hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY">
    <hp:margin header="4252" footer="4252" gutter="0"
               left="8504" right="8504" top="5668" bottom="4252"/>
  </hp:pagePr>
</hp:secPr>
```

- 단위: HWPUNIT (1/7200 인치). 예: 59528 ≈ A4 폭(210mm)
- `width="59528"` = A4 가로, `height="84186"` = A4 세로
- 여백: `left/right/top/bottom` 값 (HWPUNIT)

### 인라인 컨트롤

```xml
<hp:run>
  <hp:ctrl>
    <hp:colPr type="NEWSPAPER" colCount="1" />
  </hp:ctrl>
</hp:run>
```

```xml
<hp:run>
  <hp:lineBreak/>    <!-- 줄바꿈 -->
  <hp:tab/>          <!-- 탭 -->
</hp:run>
```

## header.xml 주요 구조

### CharShape (글자 서식)

```xml
<hh:charProperties itemCnt="...">
  <hh:charPr id="0" height="1000" textColor="#000000" shadeColor="none"
             useFontSpace="0" useKerning="0" symMark="NONE"
             borderFillIDRef="2">
    <hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
    <hh:ratio hangul="100" latin="100" .../>
    <hh:spacing hangul="0" latin="0" .../>
    <hh:relSz hangul="100" latin="100" .../>
    <hh:offset hangul="0" latin="0" .../>
    <hh:underline type="NONE" shape="SOLID" color="#000000"/>
    <hh:strikeout shape="NONE" color="#000000"/>
    <hh:outline type="NONE"/>
    <hh:shadow type="NONE" color="#C0C0C0" offsetX="10" offsetY="10"/>
  </hh:charPr>
</hh:charProperties>
```

- `height`: 글자 크기 (HWPUNIT, 1000 = 10pt) — KS X 6101:2024 표 46
- `textColor`: 글자 색상 (#RRGGBB)
- `fontRef`: 언어별 **글꼴 ID 참조값**(fontface 내 id). 글꼴 이름이 아니다
- `borderFillIDRef`: 글자 테두리를 쓸 때만 존재하는 조건부 속성. 테두리 있는 borderFill을 가리키면 글자마다 네모가 그려진다 (Critical Rule 24)

**⚠️ 요소 존재 = 속성 활성 (KS X 6101:2024 표 46)**

`italic`, `bold`, `emboss`(양각), `engrave`(음각), `supscript`(위첨자), `subscript`(아래첨자)는 **속성 없는 빈 요소이며, 존재하는 것만으로 그 서식이 켜진다.** `type="NONE"`을 붙여 나열하면 안 된다 — 실제로 양각·위첨자가 적용된다. 필요할 때만 `<hh:bold/>` 처럼 넣는다.

**하위 요소 순서는 스키마상 강제**(부속서 C `CharShapeType`은 `xs:sequence`):

```
fontRef → ratio → spacing → relSz → offset → italic? → bold? → underline?
       → strikeout? → outline? → shadow? → emboss? → engrave? → supscript? → subscript?
```

앞의 5개는 필수, 나머지는 선택. **italic이 bold보다 앞**이다.

### ParaShape (문단 서식)

정렬·여백은 **속성이 아니라 자식 요소**다. 아래는 한컴 실제 출력 순서(KS X 6101:2024 §9.3.8 샘플 34와 동일).

```xml
<hh:paraProperties itemCnt="...">
  <hh:paraPr id="0" tabPrIDRef="0" condense="0" fontLineHeight="0" snapToGrid="1"
             suppressLineNumbers="0" checked="0" textDir="LTR">
    <hh:align horizontal="JUSTIFY" vertical="BASELINE"/>
    <hh:heading type="NONE" idRef="0" level="0"/>
    <hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="KEEP_WORD"
                     widowOrphan="0" keepWithNext="0" keepLines="0"
                     pageBreakBefore="0" lineWrap="BREAK"/>
    <hh:autoSpacing eAsianEng="0" eAsianNum="0"/>
    <hh:margin>
      <hc:intent value="0" unit="HWPUNIT"/>   <!-- >0 들여쓰기, <0 내어쓰기 -->
      <hc:left value="0" unit="HWPUNIT"/>
      <hc:right value="0" unit="HWPUNIT"/>
      <hc:prev value="0" unit="HWPUNIT"/>     <!-- 문단 위 간격 -->
      <hc:next value="0" unit="HWPUNIT"/>     <!-- 문단 아래 간격 -->
    </hh:margin>
    <hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/>
    <hh:border borderFillIDRef="2" offsetLeft="0" offsetRight="0"
               offsetTop="0" offsetBottom="0" connect="0" ignoreMargin="0"/>
  </hh:paraPr>
</hh:paraProperties>
```

- `align@horizontal`: `JUSTIFY`, `LEFT`, `RIGHT`, `CENTER`, `DISTRIBUTE`(배분), `DISTRIBUTE_SPACE`(나눔)
- `lineSpacing`: `type="PERCENT"`, `value="160"` = 160% 줄간격. PERCENT일 때 0~500% 제한
- `margin` 하위는 **`hc:` 접두사**이며 값과 단위를 `value`/`unit`으로 함께 쓴다. 문단 위/아래 간격은 `prev`/`next`이고, `<hp:spacing before= after=>` 같은 요소는 실물에 없다
- `breakSetting`으로 쪽 나눔을 제어한다: `keepLines`(문단 보호), `keepWithNext`(다음 문단과 함께 — 제목이 페이지 끝에 홀로 남는 것 방지), `pageBreakBefore`, `widowOrphan`(외톨이줄 보호)

> **자식 순서 주의**: 부속서 C 스키마는 `align → heading → breakSetting → margin → lineSpacing → border → autoSpacing` 순서를 규정하지만, **한컴 실물과 표준 본문 샘플은 `autoSpacing`을 `breakSetting` 바로 뒤**에 둔다. 실물 순서를 따른다.

## 단위 변환

KS X 6101:2024 §7.2.4 전체 환산표:

| 단위 | 설명 | 변환 |
|------|------|------|
| HWPUNIT | 한글 내부 단위 | 1 HWPUNIT = 1/7200 인치 |
| pt (포인트) | 글꼴 크기 | 1pt = 100 HWPUNIT |
| mm (밀리미터) | 용지/여백 | 1mm = 283.456 HWPUNIT |
| cm | | 1cm = 2834.56 HWPUNIT |
| inch | | 1inch = 7200 HWPUNIT |
| pixel | | 1px = 75 HWPUNIT |
| char | 글자 단위 | 1char = 500 HWPUNIT |
| twips | | 1twip = 5 HWPUNIT |

> **⚠️ `unit` 속성의 기본값은 CHAR이다** (§7.2.5 표 2). `value`/`unit` 쌍을 쓰는 요소(`hc:intent`, `hc:left`, `lineSpacing` 등)에서 `unit`을 생략하면 HWPUNIT이 아니라 **CHAR(=500 HWPUNIT)로 해석**되어 값이 500배가 된다. 항상 `unit="HWPUNIT"`을 명시할 것. (단위 표기가 아예 없는 일반 속성 — `width`, `height`, `cellSz` 등 — 은 HWPUNIT으로 해석한다.)

### 일반적인 값

- A4 용지: width=59528, height=84186
- 10pt 글꼴: height=1000
- 12pt 글꼴: height=1200
- 기본 여백 (좌/우): 8504 (≈ 30mm)
- 기본 여백 (상): 5668 (≈ 20mm)
- 기본 여백 (하): 4252 (≈ 15mm)

## python-hwpx API 매핑

| 작업 | python-hwpx 메서드 | 비고 |
|------|---------------------|------|
| 새 문서 | `HwpxDocument.new()` | 빈 Skeleton 템플릿 사용 |
| 파일 열기 | `HwpxDocument.open(path)` | 경로, bytes, BinaryIO 모두 가능 |
| 문단 추가 | `doc.add_paragraph(text, section=)` | charPrIDRef로 서식 지정 가능 |
| 표 추가 | `doc.add_table(rows, cols, section=)` | borderFillIDRef 자동 생성 |
| 셀 텍스트 | `table.set_cell_text(row, col, text)` | 0-indexed |
| 머리글 | `doc.set_header_text(text, section=)` | |
| 바닥글 | `doc.set_footer_text(text, section=)` | |
| 메모 | `doc.add_memo_with_anchor(text, ...)` | MEMO 필드 자동 생성 |
| 볼드/이탤릭 런 스타일 | `doc.ensure_run_style(bold=True)` | charPrIDRef 반환 |
| 텍스트 추출 | `TextExtractor(path).extract_text()` | 테이블 포함 옵션 |
| 저장 | `doc.save_to_path(path)` | |
| bytes 반환 | `doc.to_bytes()` | |

## low-level XML 접근

python-hwpx의 고수준 API로 처리할 수 없는 경우:

1. **unpack** → XML 직접 편집 → **pack** 워크플로우 사용
2. `doc.oxml` 속성으로 low-level XML 트리 접근 가능
3. `doc.sections[0].element` 로 lxml Element 직접 조작

### 예: 용지 크기 변경 (A4 → B5)

```python
# unpack 후 section0.xml 편집
# <hp:pagePr> 의 width, height 속성 변경
# B5: width=51592, height=72850
```

### 예: 글꼴 변경 (header.xml)

```python
# <hh:charPr id="0"> 의 <hh:fontRef> 속성 변경
# hangul="맑은 고딕" latin="Arial"
```
