"""
HWPX 양식 채우기 모듈
- 문서에서 양식 부분만 추출
- 표 구조 분석 (레이블/내용 셀 구분)
- 플레이스홀더 배치 및 채우기
- 표 행/열 추가
"""

import zipfile
import shutil
import os
import re
import tempfile
from typing import Dict, List, Tuple, Optional, Any
from lxml import etree
from copy import deepcopy


class HwpxFormFiller:
    """
    HWPX 양식 채우기 클래스
    
    워크플로우:
    1. extract_form_section() - 문서에서 양식 부분만 추출
    2. analyze_table_structure() - 표 구조 분석 (레이블/내용 구분)
    3. set_placeholders() - 플레이스홀더 배치
    4. fill_placeholders() - 실제 내용으로 채우기
    5. add_table_row() - 필요시 행 추가
    6. save() - 저장
    """
    
    NAMESPACES = {
        'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
        'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
        'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    }
    
    def __init__(self, hwpx_path: str):
        self.hwpx_path = hwpx_path
        self.temp_dir = None
        self.section_tree = None
        self._is_extracted = False  # 전체 문서인지 추출된 양식인지
        
    def open(self) -> 'HwpxFormFiller':
        """HWPX 파일 열기"""
        self.temp_dir = tempfile.mkdtemp(prefix='hwpx_form_')
        
        with zipfile.ZipFile(self.hwpx_path, 'r') as zf:
            zf.extractall(self.temp_dir)
        
        section_path = os.path.join(self.temp_dir, 'Contents', 'section0.xml')
        self.section_tree = etree.parse(section_path).getroot()
        
        return self
    
    # =========================================================================
    # 1단계: 양식 추출
    # =========================================================================
    
    def find_section_by_keyword(self, keyword: str) -> Tuple[int, int]:
        """
        키워드로 섹션 범위 찾기 (paragraph 요소만 대상)
        
        Args:
            keyword: 시작 키워드 (예: "붙임 2", "별지 제1호")
            
        Returns:
            (시작_인덱스, 끝_인덱스) - paragraph 인덱스
        """
        # paragraph 요소만 추출
        all_p = [child for child in self.section_tree if child.tag.endswith('}p')]
        
        start_idx = None
        end_idx = len(all_p)
        
        for i, p in enumerate(all_p):
            texts = p.findall('.//{*}t')
            text_content = ''.join([t.text for t in texts if t.text])
            
            # 시작점 찾기
            if keyword in text_content and start_idx is None:
                start_idx = i
                continue
            
            # 끝점 찾기 (다음 붙임/별지 또는 새로운 섹션)
            if start_idx is not None:
                # 다른 "붙임" 또는 "별지"가 나오면 끝
                if re.search(r'붙임\s*\d|별지\s*제?\d', text_content):
                    end_idx = i
                    break
        
        if start_idx is None:
            raise ValueError(f"키워드 '{keyword}'를 찾을 수 없습니다.")
        
        return (start_idx, end_idx)
    
    def extract_form_section(self, keyword: str, output_path: str) -> str:
        """
        문서에서 특정 양식 부분만 추출하여 새 파일로 저장
        (페이지 설정, 여백 등 문서 양식은 유지)
        
        Args:
            keyword: 추출할 섹션의 키워드 (예: "붙임 2")
            output_path: 저장할 경로
            
        Returns:
            저장된 파일 경로
        """
        start_idx, end_idx = self.find_section_by_keyword(keyword)
        
        # paragraph 요소만 추출 (secPr이 첫 번째 p에 포함되어 있음)
        p_elements = [(i, child) for i, child in enumerate(self.section_tree) 
                      if child.tag.endswith('}p')]
        
        # 제거할 paragraph 결정:
        # - 인덱스 0은 secPr(페이지 설정)을 포함하므로 유지
        # - 나머지는 범위 밖이면 제거
        for p_idx, (orig_idx, p_elem) in enumerate(p_elements):
            # 첫 번째 paragraph는 secPr 포함하므로 유지
            if p_idx == 0:
                # 단, 텍스트 내용은 비우기 (페이지 설정만 유지)
                for t in p_elem.findall('.//{*}t'):
                    if t.text:
                        t.text = ""
                continue
            
            # 범위 밖이면 제거
            if p_idx < start_idx or p_idx >= end_idx:
                self.section_tree.remove(p_elem)
        
        self._is_extracted = True
        
        # 저장
        return self.save(output_path)
    
    # =========================================================================
    # 2단계: 표 구조 분석
    # =========================================================================
    
    def get_tables(self) -> List[etree._Element]:
        """문서의 모든 테이블 반환"""
        return self.section_tree.findall('.//{*}tbl')
    
    def analyze_table_structure(self, table_index: int = 0) -> Dict[str, Any]:
        """
        표 구조 분석 - 레이블 셀과 내용 셀 구분
        
        Args:
            table_index: 분석할 테이블 인덱스
            
        Returns:
            {
                "rows": 행 수,
                "cols": 열 수,
                "structure": [
                    {
                        "row": 행번호,
                        "cells": [
                            {"col": 열번호, "type": "label|content", "text": "텍스트"}
                        ]
                    }
                ],
                "label_cells": [(행, 열, 텍스트), ...],
                "content_cells": [(행, 열, 텍스트), ...]
            }
        """
        tables = self.get_tables()
        if table_index >= len(tables):
            raise ValueError(f"테이블 인덱스 {table_index}가 범위를 벗어남 (총 {len(tables)}개)")
        
        table = tables[table_index]
        rows = table.findall('.//{*}tr')
        
        result = {
            "rows": len(rows),
            "cols": 0,
            "structure": [],
            "label_cells": [],
            "content_cells": []
        }
        
        for row_idx, row in enumerate(rows):
            cells = row.findall('.//{*}tc')
            result["cols"] = max(result["cols"], len(cells))
            
            row_data = {"row": row_idx, "cells": []}
            
            for col_idx, cell in enumerate(cells):
                texts = cell.findall('.//{*}t')
                cell_text = ''.join([t.text for t in texts if t.text])
                
                # 셀 타입 판단:
                # - 레이블: 첫 번째 열, 또는 짧은 고정 텍스트
                # - 내용: 빈 셀, 예시 텍스트, 또는 긴 텍스트
                cell_type = self._determine_cell_type(col_idx, cell_text, len(cells))
                
                cell_data = {
                    "col": col_idx,
                    "type": cell_type,
                    "text": cell_text
                }
                row_data["cells"].append(cell_data)
                
                if cell_type == "label":
                    result["label_cells"].append((row_idx, col_idx, cell_text))
                else:
                    result["content_cells"].append((row_idx, col_idx, cell_text))
            
            result["structure"].append(row_data)
        
        return result
    
    def _determine_cell_type(self, col_idx: int, text: str, total_cols: int) -> str:
        """셀 타입 결정 (label 또는 content)"""
        text = text.strip()
        
        # 빈 셀 = content
        if not text:
            return "content"
        
        # 예시/플레이스홀더 패턴 = content
        if re.search(r'\{\{.*\}\}|예시|작성하|입력하', text):
            return "content"
        
        # 4열 구조: 레이블|내용|레이블|내용 패턴
        if total_cols == 4:
            if col_idx in [0, 2]:  # 0, 2열 = label
                return "label"
            else:  # 1, 3열 = content
                return "content"
        
        # 2열 구조: 레이블|내용 패턴
        if total_cols == 2:
            if col_idx == 0:
                return "label"
            else:
                return "content"
        
        # 첫 번째 열이면서 짧은 텍스트 = label
        if col_idx == 0 and len(text) < 30:
            return "label"
        
        # 일반적인 레이블 키워드 (첫 번째 열이 아니어도)
        label_keywords = ['이름', '소속', '연구목적', '연구방법', '연구내용', '연구결론', 
                         '분야', '대상', '대회명', '입상등급', '제목', '날짜', '향후계획',
                         '기간', '장소', '연락처', '담당', '비고', '연구주제']
        for kw in label_keywords:
            if text == kw or text.startswith(kw) and len(text) < 20:
                return "label"
        
        # 긴 텍스트 = content
        if len(text) > 30:
            return "content"
        
        # 나머지는 위치 기반
        if col_idx == 0:
            return "label"
        return "content"
    
    def print_table_analysis(self, table_index: int = 0) -> str:
        """표 구조 분석 결과를 보기 좋게 출력"""
        analysis = self.analyze_table_structure(table_index)
        
        lines = [
            f"=== 테이블 {table_index} 분석 ===",
            f"행: {analysis['rows']}, 열: {analysis['cols']}",
            "",
            "[ 레이블 셀 ]"
        ]
        
        for row, col, text in analysis['label_cells']:
            lines.append(f"  ({row},{col}) {text[:30]}")
        
        lines.append("")
        lines.append("[ 내용 셀 (채워야 할 부분) ]")
        
        for row, col, text in analysis['content_cells']:
            display = text[:30] if text else "(빈 셀)"
            lines.append(f"  ({row},{col}) {display}")
        
        return "\n".join(lines)
    
    # =========================================================================
    # 3단계: 플레이스홀더 배치
    # =========================================================================
    
    def set_placeholders(self, table_index: int = 0, 
                        mapping: Optional[Dict[Tuple[int,int], str]] = None) -> Dict[str, Tuple[int,int]]:
        """
        내용 셀에 플레이스홀더 배치
        
        Args:
            table_index: 테이블 인덱스
            mapping: {(행,열): "플레이스홀더명"} - None이면 자동 생성
            
        Returns:
            {"{{플레이스홀더명}}": (행,열)} 매핑
        """
        tables = self.get_tables()
        table = tables[table_index]
        rows = table.findall('.//{*}tr')
        
        analysis = self.analyze_table_structure(table_index)
        placeholders = {}
        
        for row_idx, col_idx, current_text in analysis['content_cells']:
            # 자동 매핑: 왼쪽 또는 위의 레이블 셀 이름 사용
            if mapping and (row_idx, col_idx) in mapping:
                ph_name = mapping[(row_idx, col_idx)]
            else:
                ph_name = self._find_label_for_cell(analysis, row_idx, col_idx)
            
            placeholder = f"{{{{{ph_name}}}}}"
            placeholders[placeholder] = (row_idx, col_idx)
            
            # 실제 셀에 플레이스홀더 설정
            cell = rows[row_idx].findall('.//{*}tc')[col_idx]
            t_elements = cell.findall('.//{*}t')
            if t_elements:
                t_elements[0].text = placeholder
        
        return placeholders
    
    def _find_label_for_cell(self, analysis: Dict, row: int, col: int) -> str:
        """내용 셀에 해당하는 레이블 찾기"""
        # 같은 행의 왼쪽 레이블 찾기
        for r, c, text in analysis['label_cells']:
            if r == row and c < col:
                return text.replace('\n', '_').strip()
        
        # 같은 열의 위쪽 레이블 찾기
        for r, c, text in analysis['label_cells']:
            if c == col and r < row:
                return text.replace('\n', '_').strip()
        
        return f"cell_{row}_{col}"
    
    # =========================================================================
    # 4단계: 내용 채우기
    # =========================================================================
    
    def fill_placeholders(self, data: Dict[str, str], table_index: int = 0) -> int:
        """
        플레이스홀더를 실제 내용으로 채우기
        - linesegarray 제거 (한글이 자동으로 줄간격 재계산하도록)
        
        Args:
            data: {"{{플레이스홀더}}": "내용"} 또는 {"플레이스홀더": "내용"}
            table_index: 테이블 인덱스
            
        Returns:
            채워진 셀 수
        """
        # 플레이스홀더 형식 정규화
        normalized_data = {}
        for key, value in data.items():
            if not key.startswith("{{"):
                key = f"{{{{{key}}}}}"
            normalized_data[key] = value
        
        filled = 0
        modified_cells = set()
        
        for t_elem in self.section_tree.findall('.//{*}t'):
            if t_elem.text:
                for placeholder, content in normalized_data.items():
                    if placeholder in t_elem.text:
                        t_elem.text = t_elem.text.replace(placeholder, content)
                        filled += 1
                        
                        # 해당 셀의 linesegarray 제거를 위해 상위 tc 찾기
                        parent = t_elem.getparent()
                        while parent is not None:
                            if parent.tag.endswith('}tc'):
                                modified_cells.add(parent)
                                break
                            parent = parent.getparent()
        
        # 수정된 셀들의 linesegarray 제거
        for cell in modified_cells:
            for p in cell.findall('.//{*}p'):
                for linesegarray in p.findall('.//{*}linesegarray'):
                    p.remove(linesegarray)
        
        return filled
    
    def _set_cell_multi_paragraph(self, cell, lines: List[str]):
        """
        셀 내용을 여러 문단(paragraph)으로 설정.
        기존 첫 번째 문단의 스타일을 복제하여 각 줄마다 별도 <hp:p>를 생성한다.

        [HWPX 셀 줄바꿈 — 권장 방식]
        HWPX에서 한 셀 내 줄바꿈은 **별도 <hp:p>로 분리**해 표현한다. 단일 <hp:t>의
        text 안에 '\\n'을 넣어도 한글 프로그램은 줄바꿈으로 렌더링하지 **않는다**.
        이 함수는 lxml etree로 hp:p를 추가해 위 권장 방식을 따른다.

        [nested 안전성]
        lxml의 `cell.find('.//{*}subList')`로 셀 안의 subList만 정확히 가져오므로
        외부 paragraph(표를 포함한 hp:p) 와 섞일 위험은 없다. 정규식
        `<hp:p>[\\s\\S]*?</hp:p>` 기반 치환은 nested 구조에서 외부+내부 둘 다 매치되어
        paragraph 곱셈 폭발을 일으킬 수 있다 — string-기반 치환이 필요하면
        :func:`hwpx_helpers.replace_placeholder_multiline` (innermost hp:p만 매치)
        사용을 권장.

        [빈 줄 정책]
        현재 구현은 ``line.strip()``으로 빈 줄을 스킵한다. 의도된 빈 줄을 보존해야
        하는 경우(예: 단락 사이 간격) 호출 측에서 사전 처리하거나 본 함수를
        수정한다.
        """
        HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'

        sublist = cell.find(f'.//{HP.replace("{","").replace("}","")}subList'.replace(
            'http://www.hancom.co.kr/hwpml/2011/paragraph',
            '{http://www.hancom.co.kr/hwpml/2011/paragraph}').replace(
            '{http://www.hancom.co.kr/hwpml/2011/paragraph}',
            '').replace('subList', '') + 'dummy_never_match')
        # Use wildcard namespace search
        sublist = cell.find('.//{*}subList')
        if sublist is None:
            return False

        existing_paras = sublist.findall('{*}p')
        if not existing_paras:
            return False

        template_para = existing_paras[0]
        template_run = template_para.find('.//{*}run')
        char_pr_id = template_run.get('charPrIDRef', '0') if template_run is not None else '0'
        para_pr_id = template_para.get('paraPrIDRef', '0')
        style_id = template_para.get('styleIDRef', '0')

        for p in existing_paras:
            sublist.remove(p)

        for line in lines:
            line = line.strip()
            if not line:
                continue
            new_p = etree.SubElement(sublist, f'{HP}p')
            new_p.set('paraPrIDRef', para_pr_id)
            new_p.set('styleIDRef', style_id)
            new_run = etree.SubElement(new_p, f'{HP}run')
            new_run.set('charPrIDRef', char_pr_id)
            new_t = etree.SubElement(new_run, f'{HP}t')
            new_t.text = line

        return True

    def fill_cells_directly(self, cell_data: Dict[Tuple[int,int], str],
                           table_index: int = 0) -> int:
        """
        좌표로 직접 셀 내용 채우기 (레이블은 유지, 내용 셀만 수정)
        - 내용에 줄바꿈(\\n)이 포함되면 각 줄을 별도 문단(paragraph)으로 생성
        - 줄바꿈이 없으면 기존 첫 번째 텍스트 요소만 교체
        - linesegarray 제거 (한글이 자동으로 줄간격 재계산하도록)

        Args:
            cell_data: {(행,열): "내용"} — 내용에 \\n 포함 시 각 줄이 별도 문단이 됨
            table_index: 테이블 인덱스

        Returns:
            채워진 셀 수
        """
        tables = self.get_tables()
        table = tables[table_index]
        rows = table.findall('.//{*}tr')

        filled = 0
        for (row_idx, col_idx), content in cell_data.items():
            if row_idx < len(rows):
                cells = rows[row_idx].findall('.//{*}tc')
                if col_idx < len(cells):
                    cell = cells[col_idx]

                    # 줄바꿈이 있으면 별도 문단으로 분리
                    if '\n' in content:
                        lines = [l for l in content.split('\n') if l.strip()]
                        if self._set_cell_multi_paragraph(cell, lines):
                            filled += 1
                            continue
                        # fallback: 멀티 문단 실패 시 단일 텍스트로 처리

                    t_elements = cell.findall('.//{*}t')

                    if t_elements:
                        # 첫 번째 텍스트 요소에 내용 설정
                        t_elements[0].text = content

                        # 나머지 텍스트 요소는 비우기 (삭제하면 구조 깨질 수 있음)
                        for t in t_elements[1:]:
                            t.text = ""

                        filled += 1
                    else:
                        # 텍스트 요소가 없는 경우: run 요소 찾아서 t 추가
                        runs = cell.findall('.//{*}run')
                        if runs:
                            # 기존 run에 t 요소 추가
                            ns = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
                            t_new = etree.SubElement(runs[0], f'{ns}t')
                            t_new.text = content
                            filled += 1
                        else:
                            # run도 없으면 p > run > t 구조 생성
                            p_elements = cell.findall('.//{*}p')
                            if p_elements:
                                ns = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
                                run = etree.SubElement(p_elements[0], f'{ns}run')
                                t_new = etree.SubElement(run, f'{ns}t')
                                t_new.text = content
                                filled += 1

                    # linesegarray 제거 (한글이 자동으로 줄간격 재계산)
                    for p in cell.findall('.//{*}p'):
                        for linesegarray in p.findall('.//{*}linesegarray'):
                            p.remove(linesegarray)

        return filled
    
    # =========================================================================
    # 5단계: 표 행/열 추가
    # =========================================================================
    
    def add_table_row(self, table_index: int, after_row: int, 
                     cell_contents: Optional[List[str]] = None) -> bool:
        """
        테이블에 행 추가 (이전 행 스타일 복제)
        - cellAddr의 rowAddr 값도 올바르게 업데이트
        - 테이블의 rowCnt 속성도 +1 업데이트
        - 삽입 위치를 포함하는 세로 병합 셀의 rowSpan도 +1 업데이트
        
        Args:
            table_index: 테이블 인덱스
            after_row: 이 행 다음에 추가
            cell_contents: 셀 내용 리스트 (None이면 빈 행)
            
        Returns:
            성공 여부
        """
        tables = self.get_tables()
        table = tables[table_index]
        rows = table.findall('.//{*}tr')
        
        if after_row >= len(rows):
            return False
        
        # 삽입될 위치 (after_row 다음)
        insert_pos = after_row + 1
        
        # 1. 삽입 위치를 포함하는 세로 병합 셀의 rowSpan 업데이트
        for row in rows:
            for cell in row.findall('.//{*}tc'):
                cell_addr = cell.find('.//{*}cellAddr')
                cell_span = cell.find('.//{*}cellSpan')
                
                if cell_addr is not None and cell_span is not None:
                    row_addr = int(cell_addr.get('rowAddr', 0))
                    row_span = int(cell_span.get('rowSpan', 1))
                    
                    if row_span > 1:
                        merge_end = row_addr + row_span - 1
                        if row_addr <= insert_pos <= merge_end:
                            cell_span.set('rowSpan', str(row_span + 1))
        
        # 2. 기준 행 복제
        source_row = rows[after_row]
        new_row = deepcopy(source_row)
        
        # 3. 새 행의 cellAddr rowAddr 업데이트
        new_row_addr = after_row + 1
        for cell in new_row.findall('.//{*}tc'):
            cell_addr = cell.find('.//{*}cellAddr')
            if cell_addr is not None:
                cell_addr.set('rowAddr', str(new_row_addr))
        
        # 4. 셀 내용 설정
        if cell_contents:
            cells = new_row.findall('.//{*}tc')
            for i, content in enumerate(cell_contents):
                if i < len(cells):
                    t_elements = cells[i].findall('.//{*}t')
                    if t_elements:
                        t_elements[0].text = content
                        for t in t_elements[1:]:
                            t.text = ""
        
        # 5. 삽입 위치 이후의 모든 행의 rowAddr +1 업데이트
        for row_idx in range(after_row + 1, len(rows)):
            for cell in rows[row_idx].findall('.//{*}tc'):
                cell_addr = cell.find('.//{*}cellAddr')
                if cell_addr is not None:
                    old_addr = int(cell_addr.get('rowAddr', row_idx))
                    cell_addr.set('rowAddr', str(old_addr + 1))
        
        # 6. 삽입
        parent = source_row.getparent()
        idx = list(parent).index(source_row)
        parent.insert(idx + 1, new_row)
        
        # 7. 테이블의 rowCnt 속성 업데이트
        current_row_cnt = int(table.get('rowCnt', len(rows)))
        table.set('rowCnt', str(current_row_cnt + 1))

        # 8. 테이블 높이(hp:sz height) 업데이트
        source_cells = source_row.findall('.//{*}tc')
        row_height = 0
        for cell in source_cells:
            cell_sz = cell.find('.//{*}cellSz')
            if cell_sz is not None:
                row_height = int(cell_sz.get('height', '0'))
                break
        if row_height > 0:
            sz_elem = table.find('.//{*}sz')
            if sz_elem is not None:
                old_height = int(sz_elem.get('height', '0'))
                sz_elem.set('height', str(old_height + row_height))

        return True

    def duplicate_row_with_content(self, table_index: int, source_row: int,
                                   content_mapping: Dict[int, str]) -> bool:
        """
        특정 행을 복제하고 일부 셀 내용만 변경
        - cellAddr의 rowAddr 값도 올바르게 업데이트
        - 삽입 이후 행들의 rowAddr도 +1 업데이트
        - 테이블의 rowCnt 속성도 +1 업데이트
        - 삽입 위치를 포함하는 세로 병합 셀의 rowSpan도 +1 업데이트
        
        Args:
            table_index: 테이블 인덱스
            source_row: 복제할 행 인덱스
            content_mapping: {열인덱스: "새내용"} - 변경할 셀만 지정
            
        Returns:
            성공 여부
        """
        tables = self.get_tables()
        table = tables[table_index]
        rows = table.findall('.//{*}tr')
        
        if source_row >= len(rows):
            return False
        
        # 삽입될 위치 (source_row 다음)
        insert_pos = source_row + 1
        
        # 1. 복제 대상 행이 세로 병합 범위 안에 있으면 rowSpan 업데이트
        for row in rows:
            for cell in row.findall('.//{*}tc'):
                cell_addr = cell.find('.//{*}cellAddr')
                cell_span = cell.find('.//{*}cellSpan')
                
                if cell_addr is not None and cell_span is not None:
                    row_addr = int(cell_addr.get('rowAddr', 0))
                    row_span = int(cell_span.get('rowSpan', 1))
                    
                    # 세로 병합이 있고, 복제 대상 행이 병합 범위 안에 있으면
                    # 병합 시작 <= source_row <= 병합 끝
                    if row_span > 1:
                        merge_end = row_addr + row_span - 1
                        if row_addr <= source_row <= merge_end:
                            cell_span.set('rowSpan', str(row_span + 1))
        
        # 2. 행 복제
        new_row = deepcopy(rows[source_row])
        
        # 3. 새 행의 cellAddr rowAddr 업데이트
        new_row_addr = source_row + 1
        for cell in new_row.findall('.//{*}tc'):
            cell_addr = cell.find('.//{*}cellAddr')
            if cell_addr is not None:
                cell_addr.set('rowAddr', str(new_row_addr))
        
        # 4. 지정된 셀 내용 변경
        cells = new_row.findall('.//{*}tc')
        for col_idx, content in content_mapping.items():
            if col_idx < len(cells):
                t_elements = cells[col_idx].findall('.//{*}t')
                if t_elements:
                    t_elements[0].text = content
                    # 나머지 텍스트 요소 비우기
                    for t in t_elements[1:]:
                        t.text = ""
        
        # 5. 삽입 위치 이후의 모든 행의 rowAddr +1 업데이트
        for row_idx in range(source_row + 1, len(rows)):
            for cell in rows[row_idx].findall('.//{*}tc'):
                cell_addr = cell.find('.//{*}cellAddr')
                if cell_addr is not None:
                    old_addr = int(cell_addr.get('rowAddr', row_idx))
                    cell_addr.set('rowAddr', str(old_addr + 1))
        
        # 6. 새 행 삽입
        parent = rows[source_row].getparent()
        idx = list(parent).index(rows[source_row])
        parent.insert(idx + 1, new_row)
        
        # 7. 테이블의 rowCnt 속성 업데이트
        current_row_cnt = int(table.get('rowCnt', len(rows)))
        table.set('rowCnt', str(current_row_cnt + 1))

        # 8. 테이블 높이(hp:sz height) 업데이트
        source_cells = rows[source_row].findall('.//{*}tc')
        row_height = 0
        for cell in source_cells:
            cell_sz = cell.find('.//{*}cellSz')
            if cell_sz is not None:
                row_height = int(cell_sz.get('height', '0'))
                break
        if row_height > 0:
            sz_elem = table.find('.//{*}sz')
            if sz_elem is not None:
                old_height = int(sz_elem.get('height', '0'))
                sz_elem.set('height', str(old_height + row_height))

        return True

    # =========================================================================
    # 저장 및 정리
    # =========================================================================
    
    def save(self, output_path: str) -> str:
        """수정된 HWPX 파일 저장"""
        # linesegarray 제거 (텍스트 수정 후 레이아웃 캐시 무효화 → 한글이 자동 재계산)
        # 단, 빈 lineSegArray 가 polaris-dvc JID 11004 를 트리거하므로 더미를 다시 박는다
        for lsa in list(self.section_tree.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}linesegarray')):
            lsa.getparent().remove(lsa)
        from hwpx_helpers import ensure_dummy_linesegs_etree
        ensure_dummy_linesegs_etree(self.section_tree)

        section_path = os.path.join(self.temp_dir, 'Contents', 'section0.xml')

        xml_bytes = etree.tostring(
            self.section_tree,
            encoding='UTF-8',
            xml_declaration=True,
            standalone=True
        )
        
        with open(section_path, 'wb') as f:
            f.write(xml_bytes)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.temp_dir)
                    # KS X 6101:2024 8.3 — version.xml도 mimetype과 함께 비압축
                    if arcname.replace('\\', '/') in ('mimetype', 'version.xml'):
                        zf.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
                    else:
                        zf.write(file_path, arcname)
        
        return output_path
    
    def close(self):
        """임시 파일 정리"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def __enter__(self):
        return self.open()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# =============================================================================
# 편의 함수
# =============================================================================

def extract_form_from_document(
    source_path: str,
    keyword: str,
    output_path: str
) -> str:
    """
    문서에서 양식 부분만 추출
    
    Args:
        source_path: 원본 문서 경로
        keyword: 추출할 섹션 키워드 (예: "붙임 2", "별지 제1호")
        output_path: 저장할 경로
        
    Returns:
        저장된 파일 경로
    """
    with HwpxFormFiller(source_path) as form:
        return form.extract_form_section(keyword, output_path)


def analyze_form_table(hwpx_path: str, table_index: int = 0) -> str:
    """
    양식 파일의 표 구조 분석
    
    Args:
        hwpx_path: 양식 파일 경로
        table_index: 분석할 테이블 인덱스
        
    Returns:
        분석 결과 문자열
    """
    with HwpxFormFiller(hwpx_path) as form:
        return form.print_table_analysis(table_index)


def fill_form_with_placeholders(
    template_path: str,
    output_path: str,
    data: Dict[str, str],
    table_index: int = 0
) -> str:
    """
    플레이스홀더가 있는 양식 채우기
    
    Args:
        template_path: 양식 파일 경로
        output_path: 저장할 경로
        data: {"플레이스홀더명": "내용"} 또는 {"{{플레이스홀더명}}": "내용"}
        table_index: 테이블 인덱스
        
    Returns:
        저장된 파일 경로
    """
    with HwpxFormFiller(template_path) as form:
        filled = form.fill_placeholders(data, table_index)
        form.save(output_path)
        print(f"{filled}개 플레이스홀더 채움")
        return output_path


def fill_form_with_coordinates(
    template_path: str,
    output_path: str,
    cell_data: Dict[Tuple[int,int], str],
    table_index: int = 0
) -> str:
    """
    좌표로 직접 양식 채우기
    
    Args:
        template_path: 양식 파일 경로
        output_path: 저장할 경로
        cell_data: {(행,열): "내용"}
        table_index: 테이블 인덱스
        
    Returns:
        저장된 파일 경로
    """
    with HwpxFormFiller(template_path) as form:
        filled = form.fill_cells_directly(cell_data, table_index)
        form.save(output_path)
        print(f"{filled}개 셀 채움")
        return output_path
