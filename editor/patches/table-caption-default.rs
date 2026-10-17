// ==== find ====
                cap_para.text = "표  ".to_string();
                cap_para.char_count = 13;
                cap_para.char_count_msb = true;
                cap_para.control_mask = 1u32 << 0x12;
                cap_para.char_offsets = vec![0, 1, 2, 11];
// ==== replace ====
                // [claude-hwpx table-caption-default] 한/글 2024 가 만드는 표 캡션과 같게 「표 {번호} 」:
                // "표" 0, 빈칸 1, 자동 번호 자리표시 빈칸 2(번호 슬롯 2~9, #1382 규칙), 빈칸 10, 문단 끝 → 12.
                // 종전 글은 빈칸이 하나 모자라고(「표  」) 위치표 끝이 11 이라, 캡션 끝에 글을 넣으면 위치표를 넘겨 읽어
                // 패닉 났다(2026-10-17, 한/글 저장본 <hp:t>표 </hp:t>{번호}<hp:t> 제목</hp:t>).
                cap_para.text = "표   ".to_string();
                cap_para.char_count = 12;
                cap_para.char_count_msb = true;
                cap_para.control_mask = 1u32 << 0x12;
                cap_para.char_offsets = vec![0, 1, 2, 10];
