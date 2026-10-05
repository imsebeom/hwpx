# 메모 실측 도구 (2026-10-06)

에디터의 메모 보기(스킬 `editor/plugin/memo-panel.ts`, 엔진 패치 `patches/memo-*.rs`, `memogroup-read.rs`)를 만들며 쓴 도구다.
한/글은 `../linebreak/hidden_desktop.py` 로 보이지 않는 데스크톱에서 돌리고, 사본만 연다.

| 파일 | 하는 일 |
| --- | --- |
| `claude_memo.rs` | rhwp `examples/` 에 두고 `cargo run --example claude_memo -- <in.hwpx> [out.hwpx]`. 메모 목록 JSON(`get_memo_list_json`)을 찍고 hwpx 로 다시 내보낸다 |
| `memo_show.py` | 위 JSON 을 한 줄씩 보기 좋게(번호, 작성자, 자리, 걸린 글, 본문) |
| `memo_xml.py` | hwpx 의 메모 필드 수, 끝 표식(fieldEnd) 수, 메모 묶음(memogroup) 수, 메모 본문 앞머리 |
| `memo_ctx.py` | n 번째 메모 필드의 앞뒤 XML 을 여러 파일에서 나란히 |
| `memo_var.py`, `memo_var2.py` | rhwp 저장본의 메모 필드 속성을 하나씩 바꾼 변형(zorder, metaTag, 본문 문단 id, 빈 글 조각). 한/글로 다시 저장해 끝 표식이 남는지 본다 |

| `memo_fields.py` | 메모 필드마다 id, zorder, Number, 작성자, 일시, 끝 표식 유무, Command, 본문 문단(스타일) |
| `cmd_var.py` | 메모 Command 의 작성자 칸을 여러 표기로 바꾼 변형(`variants` 를 고쳐 쓴다). 한/글로 다시 저장해 `memo_fields.py` 로 읽는다 |

실측 결과
- 한/글 2024 는 메모 필드의 `zorder` 가 메모 번호(`Number`)와 같아야 끝 표식을 남긴다. 없거나 0, 99 면 메모 13개의 끝 표식이 모두 사라진다. `metaTag`, 본문 문단 id, 빈 글 조각은 무관하다
- python-hwpx `add_memo_with_anchor` 는 본문을 구역 끝 `<hp:memogroup>` 에 두고 필드 subList 에는 메모 id 만 적는다. 한/글은 묶음을 읽지 않아 메모 풍선에 id 숫자가 보이고, 다시 저장하면 묶음이 사라진다
- 한/글 저장본의 `CreateDateTime` 은 끝에 Z 가 붙지만 지역 시각이다(Command 의 FILETIME 과 9시간 차)
- 한/글은 작성자를 Command 의 작성자 칸에서 읽고 Author 매개변수를 거기서 다시 만든다. 그 칸의 `:` `;` `\` `?` `|` 는 메모 매개변수를 통째로 깨뜨리고(Prop 와 잘린 Command 만 남는다) `/` 는 그 앞에서 이름이 잘린다. 글자, 숫자, 공백과 `. , ( ) & = ' " ! @ * % + ~ - _` 는 그대로 남는다
- python-hwpx `paragraph_text` 인자는 찾기가 아니라 구역 끝에 그 글로 새 문단을 만든다. `Number` 는 모든 메모에 1 을 준다
- 고친 `add_review_memo.py` 산출물(본문 문단, 표 칸, 한 문단에 메모 둘, 여러 줄, 기존 한/글 메모 7개 문서에 추가)은 한/글 재저장에서 본문, 번호, 작성자, 일시, 끝 표식이 쓴 그대로 남는다
