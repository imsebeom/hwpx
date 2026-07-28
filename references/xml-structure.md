# HWPX XML 구조 상세

## section0.xml 필수 구조

> **⚠️ 이 구조를 정확히 따르지 않으면 한글에서 문서가 열리지 않는다.**

### 첫 번째 문단에 반드시 secPr + colPr 포함

```xml
<?xml version='1.0' encoding='UTF-8'?>
<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"
        xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"
        xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"
        xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head">

  <hp:p id="1" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0">
      <hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000"
                tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="1"
                memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0">
        <!-- 하위 요소: grid, startNum, visibility, lineNumberShape, pagePr, footNotePr, endNotePr, pageBorderFill×3 -->
      </hp:secPr>
      <hp:ctrl>
        <hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>
      </hp:ctrl>
    </hp:run>
  </hp:p>
</hs:sec>
```

> **TIP**: 레퍼런스 HWPX에서 secPr을 추출하려면:
> ```python
> import zipfile, re
> with zipfile.ZipFile(hwpx_path, "r") as z:
>     data = z.read("Contents/section0.xml").decode("utf-8")
> secpr = re.search(r"<hp:secPr.*?</hp:secPr>", data, re.DOTALL).group()
> colpr = re.search(r"<hp:ctrl>.*?</hp:ctrl>", data[end:end+500], re.DOTALL).group()
> ```

### 일반 문단

```xml
<hp:p id="고유ID" paraPrIDRef="문단스타일ID" styleIDRef="0"
      pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="글자스타일ID">
    <hp:t>텍스트 내용</hp:t>
  </hp:run>
</hp:p>
```

### 빈 줄

```xml
<hp:p id="고유ID" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0"><hp:t/></hp:run>
</hp:p>
```

### 혼합 서식 (한 문단에 볼드+일반)

```xml
<hp:p id="고유ID" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0"><hp:t>일반 </hp:t></hp:run>
  <hp:run charPrIDRef="9"><hp:t>볼드</hp:t></hp:run>
  <hp:run charPrIDRef="0"><hp:t> 다시 일반</hp:t></hp:run>
</hp:p>
```

### 페이지 넘김

```xml
<hp:p id="ID" paraPrIDRef="18" styleIDRef="0" pageBreak="1" columnBreak="0" merged="0">
  <hp:run charPrIDRef="41"><hp:t/></hp:run>
</hp:p>
```

### ID 규칙

- 문단 id: 순차 증가 (고유 정수)
- 표 id: 별도 범위 권장
- **모든 id는 문서 내 고유해야 함**

### XML 특수문자 이스케이프

| 문자 | 이스케이프 |
|------|----------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `&` | `&amp;` |
| `"` | `&quot;` |

---

## 표(테이블) 작성법

```xml
<hp:p id="고유ID" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0">
    <hp:tbl id="표ID" zOrder="0" numberingType="TABLE"
            textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES"
            lock="0" dropcapstyle="None" pageBreak="CELL"
            repeatHeader="0" rowCnt="행수" colCnt="열수"
            cellSpacing="0" borderFillIDRef="3" noAdjust="0">
      <hp:sz width="42520" widthRelTo="ABSOLUTE"
             height="전체높이" heightRelTo="ABSOLUTE" protect="0"/>
      <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1"
              allowOverlap="0" holdAnchorAndSO="0"
              vertRelTo="PARA" horzRelTo="COLUMN"
              vertAlign="TOP" horzAlign="LEFT"
              vertOffset="0" horzOffset="0"/>
      <hp:outMargin left="0" right="0" top="0" bottom="0"/>
      <hp:inMargin left="0" right="0" top="0" bottom="0"/>

      <hp:tr>
        <hp:tc name="" header="1" hasMargin="0" protect="0"
               editable="0" dirty="1" borderFillIDRef="4">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK"
                      vertAlign="CENTER" linkListIDRef="0"
                      linkListNextIDRef="0" textWidth="0" textHeight="0"
                      hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="21" styleIDRef="0" pageBreak="0"
                  columnBreak="0" merged="0" id="셀문단ID">
              <hp:run charPrIDRef="9"><hp:t>헤더 텍스트</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="0" rowAddr="0"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="열너비" height="행높이"/>
          <hp:cellMargin left="170" right="170" top="0" bottom="0"/>
        </hp:tc>
      </hp:tr>
    </hp:tbl>
  </hp:run>
</hp:p>
```

### 표 크기 계산

| 항목 | 값 | 설명 |
|------|-----|------|
| A4 본문폭 | 42520 HWPUNIT | 59528 - 8504×2 |
| 열 너비 합 | = 42520 | 반드시 본문폭과 일치 |
| 3열 균등 | 14173 + 14173 + 14174 | |
| 행 높이 | 2400~3600 | 셀당 보통 값 |

### 표가 페이지 경계에서 잘릴 때 (`tbl@pageBreak`)

KS X 6101:2024 표 194가 정의하는 세 값이다. 위 예시의 `CELL`이 기본이지만, 잘림이 문제라면 값을 바꾸는 것이 정공법이다.

| 값 | 동작 | 언제 |
|----|------|------|
| `CELL` | 셀 내부 텍스트까지 나뉜다 | 긴 표의 기본값 |
| `TABLE` | 표는 나뉘되 **셀은 나뉘지 않는다** | 셀 하나가 두 쪽에 걸치는 것만 막고 싶을 때 |
| `NONE` | **나뉘지 않는다** — 표 전체가 다음 쪽으로 넘어간다 | 작은 표가 페이지 끝에서 쪼개질 때 |

`repeatHeader="1"`을 함께 쓰면 나뉜 쪽에서도 제목 행이 반복된다. 표 앞 문단이 함께 넘어가야 하면 그 문단 paraPr에 `keepWithNext="1"`을 준다.

### 표의 부분 영역 서식 (`cellzone`)

셀마다 `borderFillIDRef`를 지정하는 대신, 사각 영역을 한 번에 지정할 수 있다 (§10.9.3.3). `<hp:tbl>` 안에서 `inMargin` 다음, `tr` 앞에 온다.

```xml
<hp:cellzoneList>
  <hp:cellzone startRowAddr="1" startColAddr="1" endRowAddr="2" endColAddr="3" borderFillIDRef="7"/>
</hp:cellzoneList>
```

---

## 이미지 삽입 (BinData)

> **3단계: ZIP에 파일 추가 → content.hpf에 등록 → section0.xml에 `<hp:pic>` 참조**
> **`<hp:pic>` 요소에 필수 자식 요소가 누락되면 한컴오피스가 크래시한다.**

### 이미지 파일 추가

```python
import zipfile, os

def add_images_to_hwpx(hwpx_path, images):
    """images: [{"file": "photo.jpg", "id": "img1", "src_path": "/path/to/photo.jpg"}, ...]"""
    tmp = hwpx_path + ".tmp"
    with zipfile.ZipFile(hwpx_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "mimetype":
                    zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, data)
            for img in images:
                zout.write(img["src_path"], f"BinData/{img['file']}")
    os.replace(tmp, hwpx_path)
```

### content.hpf에 등록

```python
# </opf:manifest> 앞에 이미지 항목 삽입
for img in images:
    ext = img["file"].rsplit(".", 1)[-1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "bmp": "image/bmp"}[ext]
    item = f'<opf:item id="{img["id"]}" href="BinData/{img["file"]}" media-type="{mime}" isEmbeded="1"/>'
```

### ★ `<hp:pic>` 필수 구조 (크래시 방지)

> **⚠️ 아래 요소가 하나라도 빠지면 한컴오피스가 크래시한다.**

```xml
<hp:pic id="ID" zOrder="0" numberingType="PICTURE"
        textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES"
        lock="0" dropcapstyle="None"
        href="" groupLevel="0" instid="고유ID" reverse="0">
  <hp:offset x="0" y="0"/>
  <hp:orgSz width="W" height="H"/>
  <hp:curSz width="W" height="H"/>
  <hp:flip horizontal="0" vertical="0"/>
  <hp:rotationInfo angle="0" centerX="CX" centerY="CY" rotateimage="0"/>
  <hp:renderingInfo>
    <hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>
    <hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>
    <hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>
  </hp:renderingInfo>
  <hc:img binaryItemIDRef="이미지ID" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>
  <hp:imgRect>
    <hc:pt0 x="0" y="0"/>
    <hc:pt1 x="W" y="0"/>
    <hc:pt2 x="W" y="H"/>
    <hc:pt3 x="0" y="H"/>
  </hp:imgRect>
  <hp:imgClip left="0" right="W" top="0" bottom="H"/>
  <hp:inMargin left="0" right="0" top="0" bottom="0"/>
  <hp:imgDim dimwidth="W" dimheight="H"/>
  <hp:effects/>
  <hp:sz width="W" widthRelTo="ABSOLUTE" height="H" heightRelTo="ABSOLUTE" protect="0"/>
  <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
          holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN"
          vertAlign="TOP" horzAlign="CENTER" vertOffset="0" horzOffset="0"/>
  <hp:outMargin left="0" right="0" top="0" bottom="0"/>
</hp:pic>
```

- **W, H**: HWPUNIT 단위 표시 크기 (예: 16:9 → 40000×22500)
- **CX, CY**: W//2, H//2
- **binaryItemIDRef**: content.hpf의 `<opf:item id="...">` 값과 일치
- **instid**: 문서 내 고유 정수
- **`<hp:t/>`**: `</hp:pic>` 뒤, `</hp:run>` 앞에 빈 텍스트 노드 필수

### 이미지 삽입 전체 흐름

```
build_hwpx.py → add_images_to_hwpx() → update_content_hpf() → fix_namespaces.py → validate.py
```

---

## 표지·섹션 바 패턴

### 컬러 배너 (3×2 테이블)

- **1행**: 얇은 컬러 바 (좌: 파랑 bf=10, 우: 노랑 bf=8), height=382
- **2행**: 제목 셀 (colspan=2, bf=15 회색배경), height=7410
- **3행**: 얇은 컬러 바 (좌: 초록 bf=9, 우: 빨강 bf=11), height=382

### 섹션 바 (1×3 테이블)

- **Cell 0**: 번호 (bf=14 파랑, charPr=81 흰볼드), width=3422
- **Cell 1**: 간격 (bf=13 회색), width=565
- **Cell 2**: 제목 (bf=12 하늘색, charPr=83 볼드), width=제목에 따라 계산

### 표지 페이지 구성

```
빈 줄 × 6 → 배너 → 빈 줄 → 부제 → 빈 줄 × 8 → 날짜 → 빈 줄 × 4 → pageBreak="1" → 본문
```
