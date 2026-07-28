# HWPX 트러블슈팅

## "한글에서 빈 페이지로 열림"

| 원인 | 해결 |
|------|------|
| fix_namespaces.py 미실행 | 반드시 후처리 실행 |
| section0.xml에 secPr 없음 | 첫 문단 첫 run에 secPr + colPr 포함 |
| charPrIDRef가 header.xml에 없는 ID 참조 | 템플릿에 정의된 ID만 사용 |
| mimetype이 첫 ZIP 엔트리 아님 | build_hwpx.py 사용 시 자동 처리 |

## "내용은 있지만 서식이 깨짐"

| 원인 | 해결 |
|------|------|
| 템플릿과 section0.xml의 스타일 ID 불일치 | analyze_template.py로 실제 ID 확인 |
| header.xml의 itemCnt 불일치 | charPr/paraPr/borderFill 수와 맞추기 |
| 글꼴 미설치 | 함초롬돋움, 함초롬바탕 등 필요 |

## "표가 잘려서 보임"

| 원인 | 해결 |
|------|------|
| 열 너비 합 ≠ 본문폭 | 열 너비의 합을 본문폭과 일치 |
| rowCnt/colCnt 불일치 | 실제 행/열 수와 속성값 맞추기 |

## "이미지 포함 문서에서 한컴오피스 크래시"

| 원인 | 해결 |
|------|------|
| `<hp:pic>`에 필수 자식 요소 누락 | xml-structure.md의 `<hp:pic>` 전체 구조 사용 |
| `href=""`, `groupLevel="0"`, `instid`, `reverse="0"` 누락 | `<hp:pic>` 속성에 반드시 포함 |
| `<hp:renderingInfo>` 미포함 | transMatrix, scaMatrix, rotMatrix 전부 포함 |
| `<hp:imgClip>`, `<hp:imgDim>`, `<hp:effects/>` 누락 | 전부 포함 |
| `<hp:sz>`, `<hp:pos>` 순서 잘못 | `<hp:effects/>` 뒤에 배치 |
| `</hp:pic>` 뒤 `<hp:t/>` 누락 | run 안에 빈 텍스트 노드 추가 |
| content.hpf에 이미지 미등록 | `<opf:item>` 추가 (isEmbeded="1") |

## "문단마다 가로선이 표시됨"

| 원인 | 해결 |
|------|------|
| paraPr의 `<hh:border borderFillIDRef="X">`가 SOLID 테두리를 가진 borderFill을 참조 | paraPr의 `borderFillIDRef`를 `"1"` (테두리 없음)으로 변경 |
| borderFill의 `<hh:diagonal type="SOLID">` | `type="NONE"`으로 변경 |
| report 템플릿 원본에 이 문제가 있었음 (2026-03-21 수정 완료) | 수정 후에도 발생하면 header.xml에서 `borderFillIDRef="2"` 이상인 paraPr border를 모두 `"1"`로 변경 |

확인 방법:
```python
# header.xml에서 borderFill 확인
for m in re.finditer(r'<hh:borderFill id="(\d+)".*?</hh:borderFill>', header, re.DOTALL):
    if 'SOLID' in m.group(0) and 'Border' in m.group(0):
        print(f'borderFill id={m.group(1)}: SOLID 테두리 있음')

# paraPr에서 해당 borderFill 참조 확인
for m in re.finditer(r'<hh:border borderFillIDRef="([2-9])"', header):
    print(f'paraPr → borderFillIDRef={m.group(1)} (제거 필요)')
```

## "이미지가 ZIP에는 있지만 문서에 안 보임"

| 원인 | 해결 |
|------|------|
| BinData에 이미지 파일만 추가하고 section0.xml에 `<hp:pic>` 미삽입 | `make_image_para()`로 이미지 문단 XML 생성 후 section0.xml에 삽입 |
| content.hpf에 이미지 미등록 | `update_content_hpf()`로 등록 |
| 이미지 크기(HWPUNIT)가 0이거나 비정상 | PIL로 원본 비율 계산: `w_hu = int(mm * 283.5)`, `h_hu = int(w_hu * h_px / w_px)` |

이미지 인라인 삽입 절차:
```python
from hwpx_helpers import make_image_para, add_images_to_hwpx, update_content_hpf

# 1. ZIP에 이미지 추가
add_images_to_hwpx("output.hwpx", [{"file": "photo.png", "id": "photo", "src_path": "/path/photo.png"}])
update_content_hpf("output.hwpx", [{"file": "photo.png", "id": "photo", "src_path": "/path/photo.png"}])

# 2. section0.xml에 hp:pic 삽입
from PIL import Image
with Image.open("/path/photo.png") as img:
    w_px, h_px = img.size
w_hu = int(120 * 283.5)  # 120mm 폭
h_hu = int(w_hu * h_px / w_px)
pic_xml = make_image_para("photo", width=w_hu, height=h_hu)

# 3. section0.xml에서 원하는 위치에 삽입 (정규식으로 문단 찾기)
import re
match = re.search(r'삽입할_위치_텍스트', section_xml)
p_start = section_xml.rfind('<hp:p', 0, match.start())
section_xml = section_xml[:p_start] + pic_xml + "\n" + section_xml[p_start:]

# 4. 재패킹 + fix_namespaces
```

## "병합 후 글꼴이 달라짐"

| 원인 | 해결 |
|------|------|
| charPr의 fontRef가 원본 header의 폰트 ID를 참조하지만, 대상 header에서는 같은 ID가 다른 폰트 | 폰트 이름 기반으로 ID 리맵: 원본 header에서 폰트 이름→ID 매핑, 대상 header에서 같은 이름의 ID를 찾아 교체 |

## "병합 후 의도하지 않은 제목이 문서 앞에 표시됨"

| 원인 | 해결 |
|------|------|
| secPr 문단 안에 제목 텍스트 run이 포함되어 있음 | secPr 문단에서 텍스트가 있는 run을 제거: `first_para.remove(run)` |
| styleIDRef가 제목 스타일을 참조하여 한글이 내용을 재정렬 | 모든 styleIDRef를 "0"으로 통일 |

## "병합 후 표가 파란색/배경색으로 물듦"

| 원인 | 해결 |
|------|------|
| 원본 header의 borderFill을 복사했으나 배경색(fillBrush)이 포함 | borderFill을 복사하지 말고, 깨끗한 borderFill을 직접 생성 (SOLID 테두리, 배경 없음) |
| 표 borderFillIDRef가 대상 header의 다른 borderFill을 참조 | 표 셀(tc/tbl)의 borderFillIDRef만 새로 생성한 깨끗한 borderFill ID로 리맵 |

## "병합 후 글자마다 박스가 표시됨"

| 원인 | 해결 |
|------|------|
| charPr의 borderFillIDRef가 테두리가 있는 borderFill을 참조 | charPr 복사 시 `borderFillIDRef="1"` (테두리 없음)으로 고정 |
| paraPr의 border borderFillIDRef가 SOLID 테두리를 참조 | paraPr 복사 시 border `borderFillIDRef="1"`로 고정 |

## "병합 시 파일 오류 (한글에서 열리지 않음)"

| 원인 | 해결 |
|------|------|
| FILE1의 메타파일(settings.xml, META-INF)과 FILE2의 header.xml 혼용 | 하나의 파일을 완전한 기반으로 사용 (header + settings + META-INF 모두 같은 파일에서) |
| ZIP을 두 번 열어서 쓰기 (append 모드 사용) | 단일 패스로 ZIP 조립 |

## "python-hwpx 에러"

| 원인 | 해결 |
|------|------|
| HwpxDocument.open() 실패 | XML-first 접근 또는 ZIP-level 치환 사용 |
| ObjectFinder 에러 | `pip install python-hwpx --break-system-packages` |

## "문서는 열리는데 특정 지점부터 내용이 통째로 사라짐 (표·그림 소실)"

증상: 한글이 오류 없이 문서를 열지만, 특정 문단(주로 표가 든 문단)부터 그 뒤 내용 전체가 렌더링되지 않음. PDF 변환 시 페이지 수가 크게 부족. validate.py·verify_hwpx.py 구조 검사, 표 격자(rowCnt/colCnt/cellSpan) 검증, ID 참조 범위 검사 모두 통과.

| 원인 | 해결 |
|------|------|
| **낡은/불일치 linesegarray** — 다른 문서(특히 용지 방향·폭이 다른 원본)에서 섹션·표를 이식하면 셀 내부 문단의 lineseg 캐시(textpos/vertpos/horzsize)가 실제 내용과 어긋나고, 한글이 해당 문단부터 조용히 파싱을 중단·폐기함 | 해당 섹션의 `<hp:linesegarray>` 전체 제거 → (polaris JID 11004 대응 필요 시) `zip_replace_all(..., ensure_linesegs=True)`로 더미 재주입. 더미 lineseg는 렌더링을 깨지 않음(2026-07-05 실측: 331개 주입 후 11페이지 완전 렌더링) |

**진단법 (한글 재저장 프로브)**: COM으로 열어 HWPX로 재저장한 뒤 섹션별 `<hp:p>`/`<hp:tbl>` 수를 원본과 비교하면, 한글 파서가 어느 문단에서 내용을 버렸는지 정확히 드러난다. 렌더링 문제와 달리 파싱 단계 폐기는 이 방법으로만 확실히 잡힌다.

```python
hwp.Open(src, '', 'forceopen:true')
hwp.HParameterSet.HFileOpenSave.Format = 'HWPX'  # 재저장 후 zip 열어 문단 수 비교
```

**함정**: `zip_replace_all()` 함수를 입력=출력 같은 경로로 직접 호출하면 과거엔 입력이 truncate 되어 파일이 파괴됐다(2026-07-05 수정 완료 — 이제 임시 파일 경유). 수정 전 버전 사용 시 반드시 출력 경로를 분리할 것.
