"""
HWPX 파일 수정 모듈
- 기존 HWPX 양식을 읽어서 내용만 수정
- 원본 서식/레이아웃 유지
"""

import zipfile
import shutil
import os
import re
import tempfile
from copy import deepcopy
from typing import Any, Dict, List, Tuple, Optional
from lxml import etree


class HwpxModifier:
    """
    HWPX 파일을 읽고 수정하는 클래스
    
    사용법:
        with HwpxModifier("/path/to/template.hwpx") as doc:
            # 문서 내용 확인
            print(doc.get_text_summary())
            
            # 텍스트 치환
            doc.replace_text("기존텍스트", "새텍스트")
            
            # 저장
            doc.save("/path/to/output.hwpx")
    """
    
    HP = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
    HH = 'http://www.hancom.co.kr/hwpml/2011/head'
    HC = 'http://www.hancom.co.kr/hwpml/2011/core'

    def __init__(self, hwpx_path: str):
        """
        Args:
            hwpx_path: HWPX 파일 경로
        """
        self.hwpx_path = hwpx_path
        self.temp_dir = None
        self.section_xml = None
        self.section_tree = None
        self.header_tree = None
        self._header_modified = False
        self._indent_style_cache = {}  # left_value -> paraPrID
        self._max_parapr_id = None
        
    def open(self) -> 'HwpxModifier':
        """HWPX 파일 열기"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp(prefix='hwpx_mod_')
        
        # ZIP 압축 해제
        with zipfile.ZipFile(self.hwpx_path, 'r') as zf:
            zf.extractall(self.temp_dir)
        
        # section0.xml 파싱
        section_path = os.path.join(self.temp_dir, 'Contents', 'section0.xml')
        with open(section_path, 'rb') as f:
            self.section_xml = f.read()
        
        # lxml로 파싱 (네임스페이스 보존)
        self.section_tree = etree.fromstring(self.section_xml)

        # header.xml 파싱
        header_path = os.path.join(self.temp_dir, 'Contents', 'header.xml')
        if os.path.exists(header_path):
            with open(header_path, 'rb') as f:
                self.header_tree = etree.fromstring(f.read())

        return self
    
    def get_all_texts(self) -> List[Tuple[int, str]]:
        """
        모든 텍스트 요소를 인덱스와 함께 반환

        Returns:
            [(인덱스, 텍스트), ...] 형태의 리스트
        """
        texts = []
        for idx, elem in enumerate(self.section_tree.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}t')):
            if elem.text:
                texts.append((idx, elem.text))
        return texts

    def collect_all_fields(self) -> List[Dict[str, Any]]:
        """문서 내 모든 HWPX 필드를 수집한다.

        rhwp `src/document_core/queries/field_query.rs` 의 ``collect_all_fields()``
        와 동일한 역할. ``<hp:fieldBegin>`` 요소에서 Command·fieldName·value 를
        추출한다. 양식 치환, 필드 일괄 값 변경(set_field_value_by_name 기반)의 토대.

        Returns:
            리스트. 각 항목::

                {
                    "index": 0,              # 문서 내 등장 순서
                    "fieldName": "학교명",    # <hp:fieldBegin name=...>
                    "command": "HYPERLINK",   # <stringParam name="Command">
                    "fieldType": "user",      # <hp:fieldBegin type=...> (없으면 None)
                    "fieldId": 42,            # id 속성 (없으면 None)
                    "params": {"Target": "..."},  # 기타 stringParam
                }
        """
        fields: List[Dict[str, Any]] = []
        HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"

        for idx, fb in enumerate(self.section_tree.iter(f"{HP}fieldBegin")):
            name = fb.get("name")
            ftype = fb.get("type")
            fid_str = fb.get("id")
            try:
                fid = int(fid_str) if fid_str is not None else None
            except ValueError:
                fid = None

            command = None
            params: Dict[str, str] = {}

            # <hp:parameters><hp:stringParam name="...">value</hp:stringParam>
            for sp in fb.iter(f"{HP}stringParam"):
                sp_name = sp.get("name")
                sp_val = (sp.text or "").strip()
                if sp_name == "Command":
                    command = sp_val
                elif sp_name:
                    params[sp_name] = sp_val

            fields.append({
                "index": idx,
                "fieldName": name,
                "command": command,
                "fieldType": ftype,
                "fieldId": fid,
                "params": params,
            })

        return fields
    
    def get_text_summary(self, max_items: int = 50) -> str:
        """
        문서 텍스트 요약 반환 (Claude가 분석용으로 사용)
        
        Args:
            max_items: 최대 출력 항목 수
            
        Returns:
            텍스트 요약 문자열
        """
        texts = self.get_all_texts()
        lines = []
        for idx, text in texts[:max_items]:
            # 긴 텍스트는 축약
            display = text[:60] + "..." if len(text) > 60 else text
            # 개행 제거
            display = display.replace('\n', '\\n')
            lines.append(f"[{idx}] {display}")
        
        if len(texts) > max_items:
            lines.append(f"... 외 {len(texts) - max_items}개 텍스트 요소")
        
        return "\n".join(lines)
    
    def replace_text(self, old_text: str, new_text: str, count: int = -1) -> int:
        """
        텍스트 치환 (부분 일치)
        
        Args:
            old_text: 찾을 텍스트
            new_text: 바꿀 텍스트
            count: 치환 횟수 제한 (-1이면 모두)
            
        Returns:
            치환된 횟수
        """
        replaced = 0
        for elem in self.section_tree.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}t'):
            if elem.text and old_text in elem.text:
                elem.text = elem.text.replace(old_text, new_text)
                replaced += 1
                if count > 0 and replaced >= count:
                    break
        return replaced
    
    def replace_text_exact(self, old_text: str, new_text: str) -> int:
        """
        정확히 일치하는 텍스트만 치환
        
        Args:
            old_text: 찾을 텍스트 (정확히 일치해야 함)
            new_text: 바꿀 텍스트
            
        Returns:
            치환된 횟수
        """
        replaced = 0
        for elem in self.section_tree.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}t'):
            if elem.text == old_text:
                elem.text = new_text
                replaced += 1
        return replaced
    
    def replace_text_by_index(self, index: int, new_text: str) -> bool:
        """
        특정 인덱스의 텍스트 전체를 교체
        
        Args:
            index: 텍스트 요소 인덱스 (get_text_summary()에서 확인)
            new_text: 새 텍스트
            
        Returns:
            성공 여부
        """
        for idx, elem in enumerate(self.section_tree.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}t')):
            if idx == index:
                elem.text = new_text
                return True
        return False
    
    def replace_by_pattern(self, pattern: str, replacement: str) -> int:
        """
        정규식 패턴으로 치환
        
        Args:
            pattern: 정규식 패턴
            replacement: 치환 문자열 (그룹 참조 가능: \\1, \\2 등)
            
        Returns:
            치환된 요소 수
        """
        replaced = 0
        regex = re.compile(pattern)
        for elem in self.section_tree.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}t'):
            if elem.text and regex.search(elem.text):
                elem.text = regex.sub(replacement, elem.text)
                replaced += 1
        return replaced
    
    def find_text(self, search_text: str) -> List[Tuple[int, str]]:
        """
        텍스트 검색
        
        Args:
            search_text: 검색할 텍스트
            
        Returns:
            [(인덱스, 전체텍스트), ...] 형태의 리스트
        """
        results = []
        for idx, elem in enumerate(self.section_tree.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}t')):
            if elem.text and search_text in elem.text:
                results.append((idx, elem.text))
        return results
    
    def batch_replace(self, replacements: Dict[str, str]) -> Dict[str, int]:
        """
        여러 텍스트를 한번에 치환
        
        Args:
            replacements: {찾을텍스트: 바꿀텍스트} 딕셔너리
            
        Returns:
            {텍스트: 치환횟수} 딕셔너리
        """
        results = {}
        for old_text, new_text in replacements.items():
            count = self.replace_text(old_text, new_text)
            results[old_text] = count
        return results
    
    # ── 문단 들여쓰기 (왼쪽 여백) ──

    def _find_base_parapr(self) -> Optional[etree._Element]:
        """heading=NONE인 paraPr을 찾아 반환 (복제 원본용)"""
        if self.header_tree is None:
            return None
        for ppr in self.header_tree.iter(f'{{{self.HH}}}paraPr'):
            for child in ppr:
                if child.tag.split('}')[-1] == 'heading':
                    if child.get('type') == 'NONE':
                        return ppr
        return None

    def _get_max_parapr_id(self) -> int:
        """header.xml에서 paraPr 최대 id 반환 (캐싱)"""
        if self._max_parapr_id is not None:
            return self._max_parapr_id
        max_id = 0
        if self.header_tree is None:
            return max_id
        for ppr in self.header_tree.iter(f'{{{self.HH}}}paraPr'):
            pid = int(ppr.get('id', '0'))
            if pid > max_id:
                max_id = pid
        self._max_parapr_id = max_id
        return max_id

    def _create_indent_style(self, left_value: int, intent_value: int = 0) -> str:
        """
        주어진 왼쪽 여백 값으로 새 paraPr을 header.xml에 생성한다.

        HWPX의 paraPr 안에는 hp:switch 분기가 있다:
        - hp:case (HwpUnitChar): 새 엔진용 값
        - hp:default: 이전 엔진용 값 (case의 2배)
        한글이 두 분기를 모두 참조하므로, 양쪽에 올바른 값을 넣어야 한다.

        Args:
            left_value: 왼쪽 여백 (HWPUNIT). 한글 UI의 "왼쪽 10" = 1000.
            intent_value: 첫 줄 들여쓰기 (같은 단위). 음수면 내어쓰기("내어쓰기 10" = -1000).

        Returns:
            새로 생성된 paraPr의 id 문자열
        """
        key = left_value if not intent_value else (left_value, intent_value)
        if key in self._indent_style_cache:
            return self._indent_style_cache[key]

        base = self._find_base_parapr()
        if base is None:
            raise RuntimeError("header.xml에서 heading=NONE인 paraPr을 찾을 수 없습니다")

        new_id = self._get_max_parapr_id() + 1
        self._max_parapr_id = new_id
        new_ppr = deepcopy(base)
        new_ppr.set('id', str(new_id))

        # hp:switch 내의 case/default 분기에서 hc:left 값 설정
        for sw_child in new_ppr.iter():
            tag = sw_child.tag.split('}')[-1]
            if tag in ('case', 'default'):
                k = 1 if tag == 'case' else 2
                for left_elem in sw_child.iter(f'{{{self.HC}}}left'):
                    left_elem.set('value', str(left_value * k))
                for intent_elem in sw_child.iter(f'{{{self.HC}}}intent'):
                    intent_elem.set('value', str(intent_value * k))

        base.getparent().append(new_ppr)

        # paraPrList count 업데이트
        for elem in self.header_tree.iter():
            if elem.tag.split('}')[-1] == 'paraPrList':
                elem.set('count', str(int(elem.get('count', '0')) + 1))
                break

        self._header_modified = True
        self._indent_style_cache[key] = str(new_id)
        return str(new_id)

    def _get_all_paragraphs(self, table_index: int = -1, row_index: int = -1
                            ) -> List[etree._Element]:
        """문단 요소 리스트 반환. table/row 지정 시 해당 셀 내부만."""
        if table_index >= 0:
            tables = self.section_tree.findall(f'.//{{{self.HP}}}tbl')
            if table_index >= len(tables):
                return []
            tbl = tables[table_index]
            rows = tbl.findall(f'{{{self.HP}}}tr')
            if row_index >= 0:
                if row_index >= len(rows):
                    return []
                cells = rows[row_index].findall(f'{{{self.HP}}}tc')
                paras = []
                for cell in cells:
                    paras.extend(cell.findall(f'.//{{{self.HP}}}p'))
                return paras
            else:
                return tbl.findall(f'.//{{{self.HP}}}p')
        return list(self.section_tree.iter(f'{{{self.HP}}}p'))

    def set_indent_rules(self, rules: Dict[str, int],
                         table_index: int = -1, row_index: int = -1) -> int:
        """
        정규식 패턴별로 문단 왼쪽 여백(들여쓰기)을 일괄 설정한다.

        Args:
            rules: {정규식패턴: 왼쪽여백값(HWPUNIT)} 딕셔너리.
                   한글 UI 기준 "왼쪽 10" = 1000 HWPUNIT.
                   예: {r'^\\d+\\.': 0, r'^[가-힣]\\.': 1000, r'^-': 2000}
            table_index: 특정 표 내부만 적용 (-1이면 문서 전체)
            row_index: 특정 행 내부만 적용 (table_index 필요, -1이면 표 전체)

        Returns:
            변경된 문단 수

        Example:
            with HwpxModifier("회의록.hwpx") as doc:
                doc.set_indent_rules({
                    r'^\\d+\\.': 0,       # "1." "2." → 들여쓰기 없음
                    r'^[가-힣]\\.': 1000,  # "가." "나." → 왼쪽 10
                    r'^-': 2000,          # "-" 항목 → 왼쪽 20
                })
                doc.save("output.hwpx")
        """
        if self.header_tree is None:
            raise RuntimeError("header.xml이 없습니다")

        # 각 left_value에 대응하는 paraPr id 준비
        compiled = []
        for pattern, left_value in rules.items():
            regex = re.compile(pattern)
            if left_value == 0:
                # left=0: heading=NONE인 기존 base paraPr 사용
                base = self._find_base_parapr()
                prid = base.get('id') if base is not None else '0'
            else:
                prid = self._create_indent_style(left_value)
            compiled.append((regex, prid))

        paras = self._get_all_paragraphs(table_index, row_index)
        modified = 0
        for p in paras:
            texts = ''.join(
                t.text or '' for t in p.findall(f'.//{{{self.HP}}}t'))
            t = texts.strip()
            if not t:
                continue
            for regex, prid in compiled:
                # 앞 공백으로 수준을 표시한 패턴(r'^  -')도 맞도록 원문과 둘 다 본다
                if regex.match(texts) or regex.match(t):
                    if p.get('paraPrIDRef') != prid:
                        p.set('paraPrIDRef', prid)
                        modified += 1
                    break
        return modified

    OUTLINE_LABELS = [
        (re.compile(r'^\[.+\]$'), 'bracket'),     # [결정 사항] [향후 계획]
        (re.compile(r'^\d+\.'), 0),               # 1.
        (re.compile(r'^[가-하]\.'), 1),            # 가.
        (re.compile(r'^\d+\)'), 2),               # 1)
        (re.compile(r'^[가-하]\)'), 3),            # 가)
    ]

    def set_outline_indent(self, step_pt: float = 10, table_index: int = -1,
                           row_index: int = -1, hang_pt: float = 10) -> int:
        """
        개조식 본문의 수준마다 왼쪽 여백을 step_pt(기본 10pt)씩 더한다(2026-10-01 사용자 지시, 20pt는 너무 넓어 10pt로).

        수준: 「1.」 0, 「가.」 1, 「1)」 2, 「가)」 3. 「-」 항목은 바로 앞 번호 문단보다 한 수준,
        「→」 부연은 그보다 한 수준 더 들어간다. 「[결정 사항]」 같은 대괄호 머리는 0이고,
        그 아래 번호와 「-」는 한 수준 들어간다. 문단 앞 공백은 보지 않는다.
        모든 문단(0수준 포함)에 내어쓰기 hang_pt(기본 10pt)를 준다 — 둘째 줄이 번호 뒤 글자에
        맞춰 들어간다(2026-10-01 사용자 지시, 수준이 있는 글에 공통). 0이면 주지 않는다.
        값은 _create_indent_style 단위(한글 UI 1pt = 100)로 넘긴다. 그 함수가 한글이 읽는 default 분기에 두 배를 넣는다(2026-10-01 한글 PDF 실측).

        Returns:
            변경된 문단 수
        """
        if self.header_tree is None:
            raise RuntimeError("header.xml이 없습니다")
        base = self._find_base_parapr()
        base_id = base.get('id') if base is not None else '0'
        unit = int(round(step_pt * 100))
        hang = int(round(hang_pt * 100))

        modified, last, in_bracket = 0, 0, False
        for p in self._get_all_paragraphs(table_index, row_index):
            t = ''.join(x.text or '' for x in p.findall(f'.//{{{self.HP}}}t')).strip()
            if not t:
                continue
            level = None
            for regex, lv in self.OUTLINE_LABELS:
                if regex.match(t):
                    if lv == 'bracket':
                        level, in_bracket, last = 0, True, 0
                    else:
                        level = lv + (1 if in_bracket else 0)
                        last = level
                    break
            if level is None:
                if t.startswith('-'):
                    level = last + 1
                elif t.startswith('→'):
                    level = last + 2
                else:
                    level = 0
            left = max(level, 0) * unit
            if hang:
                prid = self._create_indent_style(left, -hang)
            else:
                prid = base_id if left == 0 else self._create_indent_style(left)
            if p.get('paraPrIDRef') != prid:
                p.set('paraPrIDRef', prid)
                modified += 1
        return modified

    def set_paragraph_indent(self, search_text: str, left_value: int) -> int:
        """
        특정 텍스트를 포함하는 문단의 왼쪽 여백을 설정한다.

        Args:
            search_text: 찾을 텍스트 (부분 일치)
            left_value: 왼쪽 여백 (HWPUNIT). 0이면 들여쓰기 제거.

        Returns:
            변경된 문단 수
        """
        if self.header_tree is None:
            raise RuntimeError("header.xml이 없습니다")

        if left_value == 0:
            base = self._find_base_parapr()
            prid = base.get('id') if base is not None else '0'
        else:
            prid = self._create_indent_style(left_value)

        modified = 0
        for p in self.section_tree.iter(f'{{{self.HP}}}p'):
            texts = ''.join(
                t.text or '' for t in p.findall(f'.//{{{self.HP}}}t'))
            if search_text in texts:
                if p.get('paraPrIDRef') != prid:
                    p.set('paraPrIDRef', prid)
                    modified += 1
        return modified

    # ── 셀 시맨틱 편집 (woo773/hangle 어휘에서 차용) ──────────────
    #
    # 모든 셀 메서드는 (table_index, row, col) 좌표를 받는다.
    # row/col 은 ``<hp:cellAddr>`` 의 rowAddr/colAddr 기반(0-base)이며
    # 병합된 셀은 그 시작 좌표 한 점만 가진다.

    def _get_table(self, table_index: int) -> Optional[etree._Element]:
        tables = self.section_tree.findall(f'.//{{{self.HP}}}tbl')
        if 0 <= table_index < len(tables):
            return tables[table_index]
        return None

    def _iter_cells(self, table):
        """``<hp:tc>`` 와 (rowAddr, colAddr, rowSpan, colSpan) 을 차례로 yield."""
        for tr in table.findall(f'{{{self.HP}}}tr'):
            for tc in tr.findall(f'{{{self.HP}}}tc'):
                addr = tc.find(f'{{{self.HP}}}cellAddr')
                span = tc.find(f'{{{self.HP}}}cellSpan')
                r = int(addr.get('rowAddr')) if addr is not None else -1
                c = int(addr.get('colAddr')) if addr is not None else -1
                rs = int(span.get('rowSpan')) if span is not None else 1
                cs = int(span.get('colSpan')) if span is not None else 1
                yield tr, tc, r, c, rs, cs

    def _get_cell(self, table_index: int, row: int, col: int):
        """좌표 (row, col) 의 셀을 찾는다. 병합 영역 안에 들어가면 그 anchor 셀 반환."""
        table = self._get_table(table_index)
        if table is None:
            return None
        for tr, tc, r, c, rs, cs in self._iter_cells(table):
            if r <= row < r + rs and c <= col < c + cs:
                return tc
        return None

    def _get_max_borderfill_id(self) -> int:
        if self.header_tree is None:
            return 0
        max_id = 0
        for bf in self.header_tree.iter(f'{{{self.HH}}}borderFill'):
            try:
                bid = int(bf.get('id', '0'))
                if bid > max_id:
                    max_id = bid
            except ValueError:
                pass
        return max_id

    def _register_border_fill(self, *, left=None, right=None, top=None, bottom=None,
                              border_color=None, bg_rgb=None) -> str:
        """header.xml 의 borderFill 풀에 새 항목을 등록하고 id 를 반환한다.

        같은 시각 속성이면 기존 borderFill 을 재사용한다(시그니처 dedup). header 가
        수정되면 ``_header_modified`` 가 True 로 설정되어 save() 에서 함께 기록된다.
        """
        if self.header_tree is None:
            raise RuntimeError("header.xml 이 없어 borderFill 을 등록할 수 없습니다")

        from hwpx_helpers import (
            build_border_fill_xml, border_fill_signature,
        )
        cache = getattr(self, '_borderfill_cache', None)
        if cache is None:
            cache = {}
            self._borderfill_cache = cache

        sig = border_fill_signature(
            left=left, right=right, top=top, bottom=bottom,
            border_color=border_color, bg_rgb=bg_rgb,
        )
        if sig in cache:
            return cache[sig]

        new_id = self._get_max_borderfill_id() + 1
        xml = build_border_fill_xml(
            new_id, left=left, right=right, top=top, bottom=bottom,
            border_color=border_color, bg_rgb=bg_rgb,
        )
        # NS_DECL 가 필요하지만 header_tree 에 이미 hh/hc 가 선언돼 있으므로
        # fromstring 시 명시 prefix 만 풀어 주면 된다.
        new_bf = etree.fromstring(
            f'<root xmlns:hh="{self.HH}" xmlns:hc="{self.HC}">{xml}</root>'
        )[0]

        # borderFill 컨테이너에 append (실측: <hh:borderFills itemCnt="N">)
        for elem in self.header_tree.iter():
            if elem.tag.split('}')[-1] in ('borderFills', 'borderFillList'):
                elem.append(new_bf)
                cnt_attr = 'itemCnt' if elem.get('itemCnt') is not None else 'count'
                elem.set(cnt_attr, str(int(elem.get(cnt_attr, '0')) + 1))
                break
        else:
            raise RuntimeError("header.xml 에서 borderFills 컨테이너를 찾을 수 없습니다")

        self._header_modified = True
        cache[sig] = str(new_id)
        return str(new_id)

    def _get_cell_borderfill_props(self, tc) -> Dict[str, Any]:
        """셀이 현재 참조하는 borderFill 의 4면 + 색 + 배경을 dict 로 추출."""
        if self.header_tree is None:
            return {}
        bf_id = tc.get('borderFillIDRef')
        if bf_id is None:
            return {}
        for bf in self.header_tree.iter(f'{{{self.HH}}}borderFill'):
            if bf.get('id') != bf_id:
                continue
            props: Dict[str, Any] = {}
            for side in ('left', 'right', 'top', 'bottom'):
                el = bf.find(f'{{{self.HH}}}{side}Border')
                if el is not None:
                    props[side] = (el.get('type'), el.get('width'),
                                   el.get('color'))
                else:
                    props[side] = None
            wb = bf.find(f'.//{{{self.HC}}}winBrush')
            if wb is not None and (wb.get('faceColor') or '').lower() != 'none':
                props['bg'] = wb.get('faceColor')
            else:
                props['bg'] = None
            return props
        return {}

    def set_cell_bg(self, table_index: int, row: int, col: int,
                    r: int, g: int, b: int) -> bool:
        """셀의 배경을 RGB 색으로 설정. 기존 테두리는 유지."""
        tc = self._get_cell(table_index, row, col)
        if tc is None:
            return False
        cur = self._get_cell_borderfill_props(tc)
        new_id = self._register_border_fill(
            left=cur.get('left'), right=cur.get('right'),
            top=cur.get('top'), bottom=cur.get('bottom'),
            bg_rgb=(r, g, b),
        )
        tc.set('borderFillIDRef', new_id)
        return True

    # style → (HWPX type, default width mm) 매핑.
    # 'thick' 은 별도 type 이 아니라 SOLID + 0.4mm 의 조합이다.
    _BORDER_STYLE_MAP = {
        'none':   ('NONE',        0.1),
        'solid':  ('SOLID',       0.12),
        'thick':  ('SOLID',       0.4),    # 굵은 실선
        'dotted': ('DOT',         0.12),
        'dashed': ('DASH',        0.12),
        'double': ('DOUBLE_SLIM', 0.4),
    }

    def set_cell_border(self, table_index: int, row: int, col: int,
                        side: str, style: str = 'solid',
                        color=None, width_mm: Optional[float] = None) -> bool:
        """셀의 한 면 테두리를 변경.

        Args:
            side: 'top'/'bottom'/'left'/'right' 또는 'all'
            style: 'none'/'solid'/'thick'/'dotted'/'dashed'/'double'
            color: ``(r,g,b)`` 또는 ``"#RRGGBB"``. None 이면 검정.
            width_mm: 사용자 지정 두께(mm). None 이면 ``style`` 기본값 사용.
                예: ``style='solid', width_mm=1.0`` → 1mm 굵은 실선.
        """
        tc = self._get_cell(table_index, row, col)
        if tc is None:
            return False
        cur = self._get_cell_borderfill_props(tc)

        key = style.lower()
        if key not in self._BORDER_STYLE_MAP:
            raise ValueError(f"Unknown border style: {style!r}")
        btype, default_w = self._BORDER_STYLE_MAP[key]
        w = width_mm if width_mm is not None else default_w
        bcolor = _color_to_hex(color) if color else '#000000'
        spec = (btype, f'{w:g} mm', bcolor)

        sides = {k: cur.get(k) for k in ('left', 'right', 'top', 'bottom')}
        targets = ['left', 'right', 'top', 'bottom'] if side == 'all' else [side]
        for s in targets:
            sides[s] = spec
        new_id = self._register_border_fill(
            left=sides['left'], right=sides['right'],
            top=sides['top'], bottom=sides['bottom'],
            bg_rgb=cur.get('bg'),
        )
        tc.set('borderFillIDRef', new_id)
        return True

    def set_cell_size(self, table_index: int, row: int, col: int,
                      width_mm: Optional[float] = None,
                      height_mm: Optional[float] = None) -> bool:
        """셀의 폭/높이를 mm 단위로 설정. width 만 또는 height 만 지정 가능.

        주의: HWPX 표는 모든 행에서 열 너비가 일관되어야 한다. 한 셀의 width 만
        바꾸면 표 전체가 깨질 수 있으므로 보통 ``set_table_column_width`` 같은
        고수준 헬퍼를 권장. 본 메서드는 단일 셀의 ``cellSz`` 만 수정한다.
        """
        from hwpx_helpers import mm_to_hwpunit
        tc = self._get_cell(table_index, row, col)
        if tc is None:
            return False
        sz = tc.find(f'{{{self.HP}}}cellSz')
        if sz is None:
            sz = etree.SubElement(tc, f'{{{self.HP}}}cellSz')
        if width_mm is not None:
            sz.set('width', str(mm_to_hwpunit(width_mm)))
        if height_mm is not None:
            sz.set('height', str(mm_to_hwpunit(height_mm)))
        return True

    def set_cell_inner_margin(self, table_index: int, row: int, col: int,
                              top_mm: float = 0.4, bottom_mm: float = 0.4,
                              left_mm: float = 0.4, right_mm: float = 0.4
                              ) -> bool:
        """셀 안쪽 여백을 mm 단위로 설정 (woo773 ``안쪽여백``)."""
        from hwpx_helpers import mm_to_hwpunit
        tc = self._get_cell(table_index, row, col)
        if tc is None:
            return False
        cm = tc.find(f'{{{self.HP}}}cellMargin')
        if cm is None:
            cm = etree.SubElement(tc, f'{{{self.HP}}}cellMargin')
        cm.set('left',   str(mm_to_hwpunit(left_mm)))
        cm.set('right',  str(mm_to_hwpunit(right_mm)))
        cm.set('top',    str(mm_to_hwpunit(top_mm)))
        cm.set('bottom', str(mm_to_hwpunit(bottom_mm)))
        tc.set('hasMargin', '1')
        return True

    def set_table_border_color(self, table_index: int, r: int, g: int, b: int
                               ) -> bool:
        """표 안 모든 셀의 SOLID 테두리 색상을 일괄 변경 (woo773 ``테두리색``).

        각 셀의 현재 borderFill 을 새 색상으로 복제한 borderFill 로 교체한다.
        NONE 면(투명)은 색상이 영향을 주지 않으므로 그대로 둔다.
        """
        table = self._get_table(table_index)
        if table is None:
            return False
        new_color = _color_to_hex((r, g, b))
        for _, tc, _, _, _, _ in self._iter_cells(table):
            cur = self._get_cell_borderfill_props(tc)
            sides = {}
            for k in ('left', 'right', 'top', 'bottom'):
                v = cur.get(k)
                if v is None or v[0] == 'NONE':
                    sides[k] = v
                else:
                    sides[k] = (v[0], v[1], new_color)
            new_id = self._register_border_fill(
                left=sides['left'], right=sides['right'],
                top=sides['top'], bottom=sides['bottom'],
                bg_rgb=cur.get('bg'),
            )
            tc.set('borderFillIDRef', new_id)
        return True

    # ── charPr 변형 등록 (장평·자간·진하게·기울임·글자색) ───────────

    def _get_max_charpr_id(self) -> int:
        if self.header_tree is None:
            return 0
        max_id = 0
        for cp in self.header_tree.iter(f'{{{self.HH}}}charPr'):
            try:
                cid = int(cp.get('id', '0'))
                if cid > max_id:
                    max_id = cid
            except ValueError:
                pass
        return max_id

    def _register_charpr_variant(self, base_id: str, **kwargs) -> str:
        """기존 charPr 을 복제·변형해 header.xml 에 등록하고 새 id 반환.

        kwargs: width, letter_spacing, bold, italic, underline, text_color.
        같은 (base_id, kwargs) 조합이면 캐시된 id 재사용.
        """
        if self.header_tree is None:
            raise RuntimeError("header.xml 이 없어 charPr 을 등록할 수 없습니다")

        from hwpx_helpers import (
            apply_charpr_variant, charpr_variant_signature,
        )
        cache = getattr(self, '_charpr_cache', None)
        if cache is None:
            cache = {}
            self._charpr_cache = cache

        sig = charpr_variant_signature(base_id, **kwargs)
        if sig in cache:
            return cache[sig]

        # 원본 charPr 찾기
        base = None
        for cp in self.header_tree.iter(f'{{{self.HH}}}charPr'):
            if cp.get('id') == str(base_id):
                base = cp
                break
        if base is None:
            raise RuntimeError(f"charPr id={base_id} 를 찾을 수 없습니다")

        new_id = self._get_max_charpr_id() + 1
        new_cp = deepcopy(base)
        new_cp.set('id', str(new_id))
        apply_charpr_variant(new_cp, **kwargs)

        # charPr 컨테이너에 append (실측: <hh:charProperties itemCnt="N">)
        for elem in self.header_tree.iter():
            tag = elem.tag.split('}')[-1]
            if tag in ('charProperties', 'charPrs', 'charPrList'):
                elem.append(new_cp)
                cnt_attr = 'itemCnt' if elem.get('itemCnt') is not None else 'count'
                elem.set(cnt_attr, str(int(elem.get(cnt_attr, '0')) + 1))
                break
        else:
            raise RuntimeError("header.xml 에서 charProperties 컨테이너를 찾을 수 없습니다")

        self._header_modified = True
        cache[sig] = str(new_id)
        return str(new_id)

    def apply_run_charpr_variant(self, table_index: int, row: int, col: int,
                                 **kwargs) -> bool:
        """셀 안의 모든 ``<hp:run>`` 의 charPrIDRef 를 새 변형 charPr 로 교체.

        kwargs: width, letter_spacing, bold, italic, underline, text_color.
        각 run 의 기존 charPrIDRef 를 base 로 삼아 변형 charPr 을 등록한다.
        """
        tc = self._get_cell(table_index, row, col)
        if tc is None:
            return False
        runs = list(tc.iter(f'{{{self.HP}}}run'))
        for run in runs:
            base = run.get('charPrIDRef', '0')
            new_id = self._register_charpr_variant(base, **kwargs)
            run.set('charPrIDRef', new_id)
        return bool(runs)

    def table_cursor(self, table_index: int = 0) -> 'TableCursor':
        """표 ``table_index`` 에 대한 :class:`TableCursor` 를 반환.

        메서드 체이닝으로 셀 편집 시퀀스를 짧게 표현하는 데 사용.
        ``at(r,c).bg(...).border(...).text(...)`` 처럼 호출.
        """
        return TableCursor(self, table_index)

    def merge_cells(self, table_index: int, row: int, col: int,
                    rowspan: int = 1, colspan: int = 1) -> bool:
        """``(row,col)`` 부터 ``rowspan × colspan`` 영역을 하나로 병합.

        anchor 셀(rowspan 1, colspan 1 외 첫 셀)은 ``cellSpan`` 이 갱신되고
        ``cellSz.width`` 가 가려진 셀들의 width 합으로, height 는 가려진 행들의
        height 합으로 늘어난다. 가려지는 셀들은 DOM 에서 제거된다.
        """
        if rowspan < 1 or colspan < 1 or (rowspan == 1 and colspan == 1):
            return False
        table = self._get_table(table_index)
        if table is None:
            return False

        cells_to_remove = []
        anchor = None
        total_w = 0
        col_widths_by_row = {}  # row → sum of widths in that row across span
        row_heights = {}        # row → height (anchor row width-sum used to determine)

        for tr, tc, r, c, rs, cs in self._iter_cells(table):
            if r < row or r >= row + rowspan:
                continue
            if c < col or c >= col + colspan:
                continue
            sz = tc.find(f'{{{self.HP}}}cellSz')
            w = int(sz.get('width', '0')) if sz is not None else 0
            h = int(sz.get('height', '0')) if sz is not None else 0
            col_widths_by_row.setdefault(r, 0)
            col_widths_by_row[r] += w
            row_heights.setdefault(r, h)
            if r == row and c == col:
                anchor = tc
            else:
                cells_to_remove.append((tr, tc))

        if anchor is None:
            return False

        # anchor 의 cellSpan 갱신
        span = anchor.find(f'{{{self.HP}}}cellSpan')
        if span is None:
            span = etree.SubElement(anchor, f'{{{self.HP}}}cellSpan')
        span.set('colSpan', str(colspan))
        span.set('rowSpan', str(rowspan))

        # anchor 의 cellSz 갱신: width 는 anchor 행의 합, height 는 모든 행 합
        if rowspan > 0:
            total_w = col_widths_by_row.get(row, 0)
        total_h = sum(row_heights.values())
        sz = anchor.find(f'{{{self.HP}}}cellSz')
        if sz is None:
            sz = etree.SubElement(anchor, f'{{{self.HP}}}cellSz')
        if total_w:
            sz.set('width', str(total_w))
        if total_h:
            sz.set('height', str(total_h))

        for tr, tc in cells_to_remove:
            tr.remove(tc)
        return True

    def save(self, output_path: str) -> str:
        """
        수정된 HWPX 파일 저장

        Args:
            output_path: 저장할 파일 경로

        Returns:
            저장된 파일 경로
        """
        # linesegarray 제거 (텍스트 수정 후 레이아웃 캐시 무효화 → 한글이 자동 재계산)
        # 단, 빈 lineSegArray 가 polaris-dvc JID 11004 를 트리거하므로 더미를 다시 박는다
        # (HwpOffice 는 텍스트 변경 시 어차피 재계산하므로 시각 영향 없음)
        for lsa in list(self.section_tree.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}linesegarray')):
            lsa.getparent().remove(lsa)
        from hwpx_helpers import ensure_dummy_linesegs_etree
        ensure_dummy_linesegs_etree(self.section_tree)

        # section0.xml 저장
        section_path = os.path.join(self.temp_dir, 'Contents', 'section0.xml')

        # XML 선언 + 내용
        xml_bytes = etree.tostring(
            self.section_tree,
            encoding='UTF-8',
            xml_declaration=True,
            standalone=True
        )

        with open(section_path, 'wb') as f:
            f.write(xml_bytes)

        # header.xml 저장 (수정된 경우)
        if self._header_modified and self.header_tree is not None:
            header_path = os.path.join(self.temp_dir, 'Contents', 'header.xml')
            header_bytes = etree.tostring(
                self.header_tree,
                encoding='UTF-8',
                xml_declaration=True,
                standalone=True
            )
            with open(header_path, 'wb') as f:
                f.write(header_bytes)
        
        # 새 ZIP 파일로 압축 (mimetype을 첫 엔트리로, 비압축 — HWPX 표준)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            mimetype_path = os.path.join(self.temp_dir, 'mimetype')
            if os.path.exists(mimetype_path):
                zf.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if file == 'mimetype':
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.temp_dir)
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


def modify_hwpx_template(
    template_path: str,
    output_path: str,
    replacements: Dict[str, str]
) -> str:
    """
    HWPX 템플릿 파일의 텍스트를 치환하여 새 파일 생성
    
    Args:
        template_path: 템플릿 HWPX 파일 경로
        output_path: 출력 파일 경로
        replacements: {찾을텍스트: 바꿀텍스트} 딕셔너리
        
    Returns:
        저장된 파일 경로
        
    Example:
        modify_hwpx_template(
            "/mnt/user-data/uploads/template.hwpx",
            "/mnt/user-data/outputs/result.hwpx",
            {
                "{{학교명}}": "서울중광초등학교",
                "{{날짜}}": "2026. 1. 7.",
                "{{담당자}}": "임세범"
            }
        )
    """
    with HwpxModifier(template_path) as doc:
        results = doc.batch_replace(replacements)
        doc.save(output_path)
        
        # 결과 출력
        for old_text, count in results.items():
            print(f"'{old_text}' → {count}개 치환됨")
    
    return output_path


class TableCursor:
    """표 셀에 대한 stateful 커서. 메서드 체이닝으로 셀 편집·이동을 표현한다.

    woo773/hangle 의 ``셀선택→셀확장→셀병합→셀배경색→텍스트삽입`` 시퀀스를
    한 줄로 옮기기 위한 추상화::

        cur = doc.table_cursor(0)
        cur.at(0, 0).bg(218,229,243).text("단원").right()
        cur.at(1, 2).merge(rowspan=2, colspan=2).text("200")
        cur.at(3, 0).size(height_mm=20).text("C")

    모든 편집 메서드는 ``self`` 를 반환해 체이닝 가능. ``at(r,c)``/``right(n)``/
    ``down(n)`` 등 이동 메서드도 동일.
    """

    def __init__(self, modifier: 'HwpxModifier', table_index: int = 0):
        self.doc = modifier
        self.table_index = table_index
        self.row = 0
        self.col = 0

    # ── 이동 ──
    def at(self, row: int, col: int) -> 'TableCursor':
        self.row, self.col = row, col
        return self

    def right(self, n: int = 1) -> 'TableCursor':
        self.col += n
        return self

    def left(self, n: int = 1) -> 'TableCursor':
        self.col -= n
        return self

    def down(self, n: int = 1) -> 'TableCursor':
        self.row += n
        return self

    def up(self, n: int = 1) -> 'TableCursor':
        self.row -= n
        return self

    # ── 편집 (HwpxModifier 의 좌표 기반 메서드를 thin wrap) ──
    def bg(self, r: int, g: int, b: int) -> 'TableCursor':
        self.doc.set_cell_bg(self.table_index, self.row, self.col, r, g, b)
        return self

    def border(self, side: str = 'all', style: str = 'solid',
               color=None, width_mm: Optional[float] = None) -> 'TableCursor':
        self.doc.set_cell_border(self.table_index, self.row, self.col,
                                 side, style, color=color, width_mm=width_mm)
        return self

    def size(self, width_mm: Optional[float] = None,
             height_mm: Optional[float] = None) -> 'TableCursor':
        self.doc.set_cell_size(self.table_index, self.row, self.col,
                               width_mm=width_mm, height_mm=height_mm)
        return self

    def inner_margin(self, top_mm: float = 0.4, bottom_mm: float = 0.4,
                     left_mm: float = 0.4, right_mm: float = 0.4
                     ) -> 'TableCursor':
        self.doc.set_cell_inner_margin(self.table_index, self.row, self.col,
                                       top_mm, bottom_mm, left_mm, right_mm)
        return self

    def merge(self, rowspan: int = 1, colspan: int = 1) -> 'TableCursor':
        """현재 위치에서 ``rowspan × colspan`` 영역을 병합."""
        self.doc.merge_cells(self.table_index, self.row, self.col,
                             rowspan=rowspan, colspan=colspan)
        return self

    # ── 폰트 변형 (셀 안 모든 run 의 charPr 을 새 변형으로 교체) ──
    def bold(self, on: bool = True) -> 'TableCursor':
        """진하게 (woo773 ``진하게``)."""
        self.doc.apply_run_charpr_variant(
            self.table_index, self.row, self.col, bold=on)
        return self

    def italic(self, on: bool = True) -> 'TableCursor':
        self.doc.apply_run_charpr_variant(
            self.table_index, self.row, self.col, italic=on)
        return self

    def underline(self, on: bool = True) -> 'TableCursor':
        self.doc.apply_run_charpr_variant(
            self.table_index, self.row, self.col, underline=on)
        return self

    def width(self, percent: int) -> 'TableCursor':
        """장평 (가로 배율 %, woo773 ``장평(95)``)."""
        self.doc.apply_run_charpr_variant(
            self.table_index, self.row, self.col, width=percent)
        return self

    def letter_spacing(self, percent: int) -> 'TableCursor':
        """자간 (% — 음수=좁게, woo773 ``자간(-12)``)."""
        self.doc.apply_run_charpr_variant(
            self.table_index, self.row, self.col, letter_spacing=percent)
        return self

    def text_color(self, color) -> 'TableCursor':
        """글자색. ``(r,g,b)`` 또는 ``"#RRGGBB"``."""
        self.doc.apply_run_charpr_variant(
            self.table_index, self.row, self.col, text_color=color)
        return self

    def text(self, s: str) -> 'TableCursor':
        """셀의 첫 ``<hp:p>`` 첫 ``<hp:run>`` 첫 ``<hp:t>`` 텍스트를 교체.

        텍스트 노드가 없으면 새로 만들어 추가한다. 다중 문단은 미지원.
        """
        tc = self.doc._get_cell(self.table_index, self.row, self.col)
        if tc is None:
            return self
        HP = self.doc.HP
        # 첫 <hp:t> 찾기
        t = tc.find(f'.//{{{HP}}}t')
        if t is not None:
            t.text = s
            return self
        # 없으면 가장 단순한 구조로 추가: 첫 p/run 에 <hp:t> 삽입
        run = tc.find(f'.//{{{HP}}}run')
        if run is None:
            p = tc.find(f'.//{{{HP}}}p')
            if p is None:
                return self
            run = etree.SubElement(p, f'{{{HP}}}run', charPrIDRef='0')
        new_t = etree.SubElement(run, f'{{{HP}}}t')
        new_t.text = s
        return self


def _color_to_hex(color):
    """``(r,g,b)`` 튜플 또는 ``"#RRGGBB"`` 문자열을 정규화."""
    if color is None:
        return '#000000'
    if isinstance(color, str):
        return color if color.startswith('#') else '#' + color
    if isinstance(color, tuple) and len(color) == 3:
        from hwpx_helpers import rgb_to_hex
        return rgb_to_hex(*color)
    raise ValueError(f"Invalid color: {color!r}")


def analyze_hwpx_template(template_path: str, max_items: int = 100) -> str:
    """
    HWPX 템플릿 파일의 텍스트 구조 분석
    
    Args:
        template_path: HWPX 파일 경로
        max_items: 최대 출력 항목 수
        
    Returns:
        텍스트 요약 문자열
    """
    with HwpxModifier(template_path) as doc:
        return doc.get_text_summary(max_items)
