// ==== find ====
    match field.instance_id {
        Some(fieldid) => format!(
            r#"<hp:fieldBegin id="{}" type="{}" name="{}" editable="{}" dirty="{}" fieldid="{}""#,
            id_str,
            ft,
            name,
            bool01(field.is_editable_in_form()),
            bool01(field.is_dirty()),
            fieldid,
        ),
        None => format!(
            r#"<hp:fieldBegin id="{}" type="{}" name="{}" editable="{}" dirty="{}""#,
            id_str,
            ft,
            name,
            bool01(field.is_editable_in_form()),
            bool01(field.is_dirty()),
        ),
    }
}
// ==== replace ====
    let tag = match field.instance_id {
        Some(fieldid) => format!(
            r#"<hp:fieldBegin id="{}" type="{}" name="{}" editable="{}" dirty="{}" fieldid="{}""#,
            id_str,
            ft,
            name,
            bool01(field.is_editable_in_form()),
            bool01(field.is_dirty()),
            fieldid,
        ),
        None => format!(
            r#"<hp:fieldBegin id="{}" type="{}" name="{}" editable="{}" dirty="{}""#,
            id_str,
            ft,
            name,
            bool01(field.is_editable_in_form()),
            bool01(field.is_dirty()),
        ),
    };
    tag + &claude_memo_zorder_attr(field)
}

/// [claude-hwpx memo-zorder] 메모 필드의 `zorder` 속성. 한/글은 이 값이 메모 번호(`Number`)와 같아야 메모를 온전히 읽는다.
///
/// 한/글 2024 실측(2026-10-06, 메모 13개 문서를 rhwp 로 저장한 뒤 속성만 바꿔 한/글로 다시 저장):
/// zorder 가 없거나 0, 99 처럼 번호와 다르면 메모 13개의 끝 표식(fieldEnd)이 모두 사라지고 그 문단의 줄 기록도 빠진다
/// (메모가 걸린 글의 범위를 잃는다). 번호와 같으면 13개가 그대로 남는다. metaTag 속성은 있든 없든 같았다.
/// 한/글 저장본은 늘 zorder = Number 다(메모 문서 네 개, 메모 32개 확인).
fn claude_memo_zorder_attr(field: &Field) -> String {
    let from_command = || {
        field
            .command
            .strip_prefix("MEMO/")
            .and_then(|rest| rest.split('/').nth(1))
            .and_then(|token| token.parse::<u32>().ok())
    };
    let number = if field.field_type == FieldType::Memo {
        Some(if field.memo_index > 0 {
            field.memo_index
        } else {
            from_command().unwrap_or(0)
        })
    } else {
        // 종류를 못 알아본 채 command 만 MEMO 인 필드(HWP5 에서 온 메모)
        from_command()
    };
    number
        .map(|n| format!(r#" zorder="{}""#, n))
        .unwrap_or_default()
}
