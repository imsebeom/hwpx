            // [claude-hwpx 패치] 머리말/꼬리말 필드 표식(\u0015 현재 쪽, \u0016 총 쪽수 —
            // insertFieldInHf, applyHfTemplate 이 넣는다)을 한컴 자동 번호 컨트롤로 방출한다.
            // 종전에는 바로 아래 "기타 제어문자 무시" 분기에서 버려져 저장본에서 쪽 번호가
            // 사라졌다. 표식은 머리말/꼬리말 전용이다(본문 쪽 번호 자리 표시는 "\u0002pf").
            '\u{0015}' | '\u{0016}' => {
                flush_buf(&mut t_xml, &mut buf);
                let num_type = if c == '\u{0015}' { "PAGE" } else { "TOTAL_PAGE" };
                t_xml.push_str(&format!(
                    r#"</hp:t><hp:ctrl><hp:autoNum num="1" numType="{}"><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar="" supscript="0"/></hp:autoNum></hp:ctrl><hp:t>"#,
                    num_type
                ));
            }
