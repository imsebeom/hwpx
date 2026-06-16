# Third-Party Notices

이 스킬은 다음 오픈소스 프로젝트의 알고리즘과 아이디어를 참조·이식하여 사용합니다.
각 원저작자와 라이선스 전문을 아래에 명시합니다.

---

## 1. rhwp — HWPX/HWP Viewer and Editor (Rust + WebAssembly)

- **저장소**: https://github.com/edwardkim/rhwp
- **저작권**: Copyright (c) 2025-2026 Edward Kim
- **라이선스**: MIT License

### 참조·이식 범위

다음 알고리즘·패턴을 Python으로 재작성하여 본 스킬에 포함하였습니다. 원본 소스 코드
자체는 포함하지 않으며, 설계 의도·상수·제어 흐름을 참고한 독립 구현입니다.

| 스킬 내 파일 | 참조한 rhwp 파일 | 이식 내용 |
|--------------|-------------------|-----------|
| `scripts/table_calc.py` | `src/document_core/table_calc/{tokenizer,parser,evaluator}.rs` | 3-layer 수식 엔진 (토크나이저/파서/평가기). SUM/AVG/MIN/MAX/COUNT/IF + 단항 수학 함수 + 셀 참조(A1, A1:B5, ?1, A?, above·below·left·right) |
| `scripts/hwpx_helpers.py` — `local_name()`, `xpath_local()` | `src/parser/hwpx/utils.rs:10-18` | 네임스페이스 prefix 무관 XPath 패턴 |
| `scripts/hwpx_helpers.py` — `utf16_len()`, `tab_aware_offset()` | `src/parser/hwpx/section.rs:299-322` | UTF-16 코드유닛 + 탭 8-unit 오프셋 규칙 |
| `scripts/hwpx_helpers.py` — `read_zip_entry_limited()`, 상수 | `src/parser/hwpx/reader.rs:19-26` | zip bomb 방어 상한 (XML 32MB / BinData 64MB) |
| `scripts/verify_hwpx.py` | 동상 | zip bomb 상한 체크 통합 |
| `scripts/hwpx_modifier.py` — `collect_all_fields()` | `src/document_core/queries/field_query.rs` + `src/parser/hwpx/section.rs::parse_ctrl_field_begin` | `<hp:fieldBegin>` 파싱 패턴 |

### 라이선스 전문 (MIT License)

```
MIT License

Copyright (c) 2025-2026 Edward Kim

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 2. jkf87/hwpx-skill

- **저장소**: https://github.com/jkf87/hwpx-skill
- **역할**: 본 스킬의 최초 기반(base fork). 이후 독자적으로 확장됨.
- **변경 사항 요약**: `README.md` 참조.
- **추가 차용 (2026-06-16, jkf87 v1.0.5 기준)**: 아래 안전장치를 본 스킬 스타일(정규식 + lxml, 표준 라이브러리)로 재구현.

| 스킬 내 위치 | 참조한 jkf87 구현 | 재구현 내용 |
|---|---|---|
| `verify_hwpx.py` `detect_char_border_bug`/`strip_char_borders` | `fill_hwpx.py` 동명 함수 | 변환기/LLM이 charPr 다수에 SOLID 테두리 borderFill을 박는 "모든 글자 네모 테두리" 버그 탐지·제거 (표 셀 테두리 보존, idempotent) |
| `verify_hwpx.py` `check_secpr_openable` | `fill_hwpx.py` `check_openable` 의 secPr 점검부 | secPr 자식요소(pagePr/margin) 누락 + 가짜 secPr(비표준 속성) 휴리스틱 검출 — 한컴 '손상된 문서' 사고 방지 |

> raw LLM 파일 탐지(`detect_raw_llm`)와 PreToolUse 가드 훅은 본 스킬의 더미 lineSegArray 주입 전략(polaris-dvc 통과용)과 상충하므로 의도적으로 미차용.

---

## 3. PolarisOffice/polaris_dvc

- **저장소**: https://github.com/PolarisOffice/polaris_dvc
- **역할**: HWPX 검증 Rust CLI v0.1.0 prebuilt 바이너리 번들 (`bin/polaris-dvc.exe`).
- **라이선스**: 원본 저장소 LICENSE/NOTICE 참조 (별도 파일로 보관).
- **사용**: `verify_hwpx.py --strict` 가 외부 호출.

---

## 4. airmang/hwpx-skill

- **저장소**: https://github.com/airmang/hwpx-skill
- **저작권**: Copyright (c) 2026 airmang (고규현, `python-hwpx` 라이브러리 저자)
- **라이선스**: Apache License 2.0 (2026-04-24 MIT → Apache 재라이선싱)

### 참조·이식 범위

| 스킬 내 파일 | 참조한 airmang 파일 | 이식 내용 |
|--------------|---------------------|-----------|
| `scripts/zip_replace_all.py` | 동명 파일 | ZIP-level 전역 텍스트 치환 + `mimetype` ZIP_STORED 보존 + temp 파일 안전 처리 + `--inplace --backup --auto-fix-ns` 플래그 + `<,>,</` 키 경고. **이식 시 `inject_dummy_linesegs()` 통합 (lineSegArray 더미 자동 주입)** 추가. |
| `references/python-hwpx-api.md` | `references/api.md` | `python-hwpx` 2.x API 시그니처 (`HwpxDocument`, `replace_text_in_runs`, `add_memo_with_anchor` 등) 발췌 + 본 스킬 1.9 ↔ 2.x 마이그레이션 노트 |

원본 파일 자체에는 SPDX-License-Identifier 헤더가 보존돼 있고, 이식판에도
`SPDX-License-Identifier: Apache-2.0` 헤더와 출처 주석을 유지하였습니다.

### 라이선스 전문 (Apache-2.0)

전문은 https://www.apache.org/licenses/LICENSE-2.0 참조. 핵심 의무:

1. 라이선스 사본 동봉 (본 파일에 이 섹션으로 갈음)
2. 변경 사항 표시 (위 표의 "이식 내용" 컬럼)
3. NOTICE 파일이 있으면 보존 (airmang 의 NOTICE 본문은 `bin/airmang-NOTICE` 등으로 별도 보관 권장)
4. 보증 부인

---

## 5. Canine89/hwpxskill

- **저장소**: https://github.com/Canine89/hwpxskill
- **저작권**: Copyright (c) 2026 Canine89
- **라이선스**: **명시 없음** (저장소에 LICENSE 파일 미존재, 2026-05-05 기준)

### 참조·이식 범위

라이선스가 명시되지 않은 저장소이므로 **원본 코드는 직접 복사하지 않았습니다**.
"레퍼런스 99% 복원 + 쪽수 가드" 워크플로 철학과 메트릭 비교 알고리즘만 참조하여
본 스킬 스타일 (`xpath_local()` 기반 네임스페이스 무관 XPath, 다중 섹션 순회,
`verify_hwpx` 와 동일한 zip bomb 상한) 으로 독립 재구현했습니다.

| 스킬 내 파일 | 참조한 Canine89 파일 | 재구현 내용 |
|--------------|---------------------|-------------|
| `scripts/page_guard.py` | `scripts/page_guard.py` | 메트릭(문단·표 구조·pageBreak·텍스트 길이) 비교 + 임계값 기반 드리프트 검출 알고리즘. 본 스킬은 다중 섹션 순회·`xpath_local`·zip bomb 상한 추가 |
| SKILL.md "워크플로우 O" 섹션 | `SKILL.md` 의 "기본 동작 모드" + "쪽수 동일(100%) 필수 기준" | 레퍼런스 보존 체크리스트 + page_guard 통합 흐름 |

### 라이선스 부재 시 권고

저장소에 LICENSE 가 추가되면 본 항목을 갱신하고 필요 시 의무 사항을 반영합니다.
원저작자가 다른 형태의 표기·수정·이식 중단을 요청하면 즉시 반영합니다.

---

## 6. Kminer2053/public-doc-to-hwpx

- **저장소**: https://github.com/Kminer2053/public-doc-to-hwpx
- **저작권**: Copyright (c) 2026 public-doc-to-hwpx contributors
- **라이선스**: MIT License

### 참조·이식 범위

| 스킬 내 파일 | 참조한 public-doc-to-hwpx 파일 | 이식 내용 |
|--------------|--------------------------------|-----------|
| `references/writing-principles.md` | 동명 파일 | 공공기관 보고서 작성 원칙 (개조식·두괄식·Why→How→What·「적의를 보이는 것들」 4종) 전체 그대로 흡수. 상단에 출처 헤더 추가. |
| `references/layout-rules.md` | 동명 파일 | 레이아웃 최적화 규칙 (한 문장 35–45자·페이지 걸침·글머리 위계·시각 스타일·12개 자동 변환 표) 전체 그대로 흡수. 상단에 출처 헤더 추가. |
| `scripts/writing_optimizer.py` | `references/layout-rules.md` 8장 표 + 원본 SKILL.md `layout_optimizer` 동작 명세 | 정규식 12개 (R1·R3·R4·R5·R6a·R6b·R8·R12a·R12b 자동 + R2·R7·R9·R10·R11 검토 권장) 를 독립 재구현. 한국어 조사 받침 처리(`이/가`, `은/는`, `을/를` 자동 짝맞춤) 보강. **원본 소스 코드는 포함하지 않음** — 알고리즘·규칙 표·신뢰도 분류만 참조. |
| `scripts/hwpx_helpers.py` — `remove_linesegarray_in_paragraphs_matching()` | `scripts/fix_toc_dots.py::remove_linesegarray_from_dotted_paragraphs` | 목차 점선·자간 압축 단락의 lineseg 캐시 통째 제거 → 한글 폰트 메트릭 재계산 위임 패턴. predicate 인자로 일반화 (목차 점선·단일 lineseg 단락 등 다양한 트리거 조건 지원). `inject_dummy_linesegs()` 의 **보완 관계** (빈 lineseg → 더미 주입 / 잘못된 lineseg → 통째 제거). |

### 라이선스 전문 (MIT License)

```
MIT License

Copyright (c) 2026 public-doc-to-hwpx contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 문의

추가 고지·수정 요청이 있으면 이슈로 알려주세요.
