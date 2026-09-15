# hwpx-skill

HWPX(한컴오피스 한글 개방형 문서) 생성, 편집, 병합을 위한 Claude Code 커스텀 스킬.

## 참조 및 크레딧

이 스킬은 다음 오픈소스 프로젝트·문서·라이브러리를 참조·활용하여 만들어졌습니다.
각 프로젝트 저자와 기여에 감사드립니다.

| 구분 | 프로젝트 / 자료 | 라이선스 | 기여 / 참조 범위 |
|------|-----------------|----------|------------------|
| 기반 fork | [jkf87/hwpx-skill](https://github.com/jkf87/hwpx-skill) | 원본 라이선스 | 최초 기반. ZIP-level 치환 워크플로우, 템플릿 구조, 기본 빌드 패턴 |
| 알고리즘 포팅 | [edwardkim/rhwp](https://github.com/edwardkim/rhwp) | MIT (© 2025-2026 Edward Kim) | 표 계산식 엔진, 네임스페이스 헬퍼, UTF-16 오프셋, zip bomb 방어, 필드 API 포팅 (2026-04-18) |
| 외부 검증 도구 | [PolarisOffice/polaris_dvc](https://github.com/PolarisOffice/polaris_dvc) | Apache-2.0 | `bin/polaris-dvc.exe` (v0.1.0 prebuilt) — `verify_hwpx --strict` 의 JID 위반 검출 백엔드 (2026-04-26) |
| 스크립트 이식 | [airmang/hwpx-skill](https://github.com/airmang/hwpx-skill) | Apache-2.0 (© 2026 airmang) | `scripts/zip_replace_all.py` ZIP-level 전역 치환 + temp 안전 처리 + `mimetype ZIP_STORED` 보존 (2026-05-05). lineSegArray 더미 주입은 자체 보강 |
| 알고리즘 재구현 | [Canine89/hwpxskill](https://github.com/Canine89/hwpxskill) | 라이선스 미지정 | `scripts/page_guard.py` 레퍼런스 대비 페이지 드리프트 가드 (메트릭 비교 알고리즘 참조 후 다중 섹션·`xpath_local`·zip bomb 상한 추가하여 독립 재구현) (2026-05-05) |
| 스펙 자료 | 한글과컴퓨터 HWP 파일 형식 공개 문서 | 공개 | HWPX XML 스키마 해석 기준 |
| Python 라이브러리 | `lxml` / `python-hwpx 2.9.1+` / `Pillow` | 각 라이브러리 라이선스 | XML 파싱·편집, HWPX 읽기·`HwpxDocument` API, 이미지 처리 |

**상세 참조**: 원본 fork 대비 변경 사항은 아래 "원본(jkf87) 대비 변경 사항" 참조.
rhwp 포팅 상세는 [`references/rhwp-benchmark.md`](references/rhwp-benchmark.md),
제3자 라이선스 전문은 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 참조.

## 원본(jkf87) 대비 변경 사항

### 추가된 모듈

| 파일 | 기능 | 원본에 없는 이유 |
|------|------|------------------|
| `hwpx_modifier.py` | 기존 양식 세밀 수정 (정규식 치환, 인덱스 기반 수정, 문단 들여쓰기 제어) | 원본은 새 문서 생성 중심. 기존 문서의 문단 속성 세밀 조작 기능 없음 |
| `hwpx_form_filler.py` | 양식 부분 추출, 표 구조 분석, 좌표 기반 셀 채우기, 행 추가/복제 | 원본은 ZIP-level 문자열 치환만 지원. 표 구조 변경 불가 |
| `hwpx_writer.py` | hp:switch 구조 줄간격 XML 생성 | 원본에 줄간격 관련 함수 없음 |

### 코드 수정

| 파일 | 변경 내용 |
|------|-----------|
| `md2hwpx.py` | 표 열 너비: 균등 배분 → **내용 길이 비례 배분** (한글=2, ASCII=1 가중치). 셀 여백 확대 (좌우 1mm, 상하 0.5mm). `hasMargin="1"` 활성화 |
| `templates/report/header.xml` | 모든 paraPr의 `borderFillIDRef`를 `"1"`로 변경 (문단 가로선 제거). `diagonal type="SOLID"` → `"NONE"` |
| `zip_replace_all.py`, `clone_form.py` (2026-09-15) | 텍스트 치환 범위를 **`<hp:t>` 안의 글자만**으로 바꿈(`hwpx_helpers.replace_in_text_nodes`). XML 전체 치환은 `--raw` 로만. AI가 만든 편집 스크립트가 「7→4」 같은 짧은 키로 XML 전체를 치환해 쪽 높이·여백·셀 주소가 깨지고 한글이 멈춘 사고에서 |
| `validate.py` (2026-09-15) | XML 유효성에 더해 **쪽 크기 상식 검사**(pagePr 10,000~300,000 HWPUNIT)와 **표 격자 검사**(cellAddr 중복·빈 칸)를 넣음. 위 사고 파일이 유효성만으로는 「정상」이었다 |

### 추가된 워크플로우

| 워크플로우 | 용도 |
|-----------|------|
| **G** (HwpxModifier) | 기존 양식의 정규식 치환, 인덱스 수정, 들여쓰기 조정 |
| **H** (HwpxFormFiller) | 붙임/별지 섹션 추출, 표 좌표 기반 셀 채우기, 행 추가/복제 |
| **I** (병합) | 여러 HWPX 파일을 lxml 파서로 안전하게 병합 |

### SKILL.md 확장

- md2hwpx.py 직접 사용법 (`--template` 옵션) 문서화
- 이미지 인라인 삽입 전체 코드 예시 (ZIP 추가 + section0.xml hp:pic 삽입 2단계)
- HWPX 병합 코드 예시 (lxml 기반, ID 오프셋, 페이지 넘김)
- Critical Rules #16~22 추가

### 트러블슈팅 추가 (references/troubleshooting.md)

- "문단마다 가로선이 표시됨" — paraPr borderFillIDRef 원인 및 해결
- "이미지가 ZIP에는 있지만 문서에 안 보임" — 인라인 삽입 절차

## 설치

```bash
# Claude Code 스킬 디렉토리에 클론
git clone https://github.com/imsebeom/hwpx.git ~/.claude/skills/hwpx

# 의존성
pip install lxml Pillow
```

## 워크플로우 요약

| 워크플로우 | 용도 | 주요 도구 |
|-----------|------|-----------|
| A | 마크다운/텍스트 → HWPX | hwpx_helpers.py, md2hwpx.py |
| B | 템플릿 플레이스홀더 치환 | ZIP-level str.replace() |
| C | 기존 문서 XML 편집 | office/unpack.py → pack.py |
| D | 참조 양식 기반 새 문서 | analyze_template.py + build_hwpx.py |
| E | 읽기/텍스트 추출 | text_extract.py |
| F | 양식 복제 (구조 100% 보존) | clone_form.py |
| G | 세밀 수정 (정규식, 들여쓰기) | hwpx_modifier.py |
| H | 표 조작 (셀 채우기, 행 추가) | hwpx_form_filler.py |
| I | 여러 HWPX 병합 | lxml 기반 문단 복사 |
| J | 시험 문제지 생성 (PDF→HWPX) | exam_builder.py |
| K | HWP(바이너리) → HWPX 순수 Python 변환 | convert_hwp.py (jkf87/hwp2hwpx-python-refactor) |
| L | ZIP-level 전역 치환 (양식 표 셀 포함) | zip_replace_all.py (airmang 이식 + lineseg 통합) |
| M | 스타일 필터 텍스트 치환 (글자 색·밑줄·charPrIDRef·limit) | style_filter_replace.py (python-hwpx 2.x) |
| N | 자동 첨삭 메모 batch 삽입 (학생 작품 평가 자동화) | add_review_memo.py (python-hwpx 2.x) |
| O | 레퍼런스 99% 복원 + 쪽수 드리프트 가드 | page_guard.py (Canine89 알고리즘 재구현) |

## airmang/hwpx-skill 이식 + python-hwpx 2.x 활용 (2026-05-05)

`python-hwpx` 라이브러리 저자가 운영하는 [airmang/hwpx-skill](https://github.com/airmang/hwpx-skill)
(Apache-2.0) 의 슬림 ZIP 치환 도구를 이식하고, 동시에 `python-hwpx` 를 1.9 → 2.9.1
로 글로벌 업그레이드하여 `HwpxDocument` 신규 API (`replace_text_in_runs` 스타일 필터,
`add_memo_with_anchor`) 를 활용한 워크플로우 M·N 을 추가했습니다.

| 추가 | 출처 / 활용 API |
|------|-----------------|
| `scripts/zip_replace_all.py` (워크플로 L) | airmang 이식. lineSegArray 더미 자동 주입 통합 (polaris-dvc strict JID 11004 방지) |
| `scripts/style_filter_replace.py` (워크플로 M) | `HwpxDocument.replace_text_in_runs(text_color=..., underline_type=..., limit=...)` |
| `scripts/add_review_memo.py` (워크플로 N) | `HwpxDocument.add_memo_with_anchor(...)` + 저장 후 lineseg 후처리 |
| `references/python-hwpx-api.md` | 라이브러리 1.9 ↔ 2.x API 시그니처 + 마이그레이션 노트 |

자세한 검증·회귀 테스트 결과는 작업 폴더 `.test/20260505-085332-airmang-스킬반영/CHANGES.md`
참조. 라이선스 의무 (Apache-2.0 NOTICE 보존, SPDX 헤더 유지) 는
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 4번 항목 참조.

## Canine89/hwpxskill 알고리즘 차용 (2026-05-05)

[Canine89/hwpxskill](https://github.com/Canine89/hwpxskill) (라이선스 미지정)
의 **레퍼런스 99% 복원 + 쪽수 가드** 워크플로 철학을 받아들여, `page_guard.py`
의 메트릭 비교 알고리즘만 참조해 본 스킬 스타일로 독립 재구현했습니다.
원본 코드는 라이선스 부재로 직접 복사하지 않았습니다.

| 추가 | 차용 범위 |
|------|-----------|
| `scripts/page_guard.py` | 문단·표 구조·`pageBreak`·텍스트 길이 메트릭 비교 + 임계값(15%/25%) 기반 드리프트 검출. 본 스킬은 `xpath_local()` (네임스페이스 무관) + 다중 섹션 순회 + zip bomb 상한 추가 |
| SKILL.md "워크플로우 O" | 레퍼런스 보존 체크리스트 + page_guard 통합 흐름 |

자세한 라이선스 고지는 `THIRD_PARTY_NOTICES.md` 5번 항목.

## rhwp 포팅 (2026-04-18)

Rust + WebAssembly HWPX 역공학 프로젝트 [edwardkim/rhwp](https://github.com/edwardkim/rhwp)
(MIT License) 의 알고리즘·패턴을 **외부 의존성 없이** Python으로 이식하여 스킬을 확장했습니다.

| 추가/보강 | 참조한 rhwp 모듈 |
|-----------|------------------|
| `scripts/table_calc.py` (표 계산식 엔진, SUM/AVG/IF + 범위/방향 참조) | `src/document_core/table_calc/` |
| `hwpx_helpers.py` — `local_name()`, `xpath_local()` (네임스페이스 무관 XPath) | `src/parser/hwpx/utils.rs` |
| `hwpx_helpers.py` — `utf16_len()`, `tab_aware_offset()` | `src/parser/hwpx/section.rs` |
| `verify_hwpx.py` — zip bomb 상한 (XML 32MB / BinData 64MB) | `src/parser/hwpx/reader.rs` |
| `hwpx_modifier.py` — `collect_all_fields()` | `src/document_core/queries/field_query.rs` |

배경·API·한계는 `references/rhwp-benchmark.md`, 라이선스 고지는 `THIRD_PARTY_NOTICES.md` 참조.

## 라이선스

원본 [jkf87/hwpx-skill](https://github.com/jkf87/hwpx-skill)의 라이선스를 따릅니다.

제3자 코드의 라이선스 고지는 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)를 참조하세요.
