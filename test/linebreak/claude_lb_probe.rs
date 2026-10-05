// [claude-hwpx 임시 진단] 한글이 저장한 줄 배치와 rhwp 재조판의 줄 시작 위치를 문단마다 비교한다.
//   CLAUDE_LB_FILES=<목록 파일> CLAUDE_LB_VERBOSE=1 cargo test --lib claude_lb_probe -- --ignored --nocapture
// 문단마다 한글 저장 줄의 상자(column_start..+segment_width)를 그대로 주고 다시 나눈다. 쪽 배치와 무관한 줄 나누기만 본다.
use super::*;
use crate::document_core::DocumentCore;
use crate::renderer::style_resolver::resolve_styles_for_document;

fn walk<'a>(paras: &'a [Paragraph], out: &mut Vec<&'a Paragraph>) {
    for p in paras {
        out.push(p);
        for c in &p.controls {
            if let Control::Table(t) = c {
                for cell in &t.cells {
                    walk(&cell.paragraphs, out);
                }
            }
        }
    }
}

#[test]
#[ignore]
fn claude_lb_probe() {
    if let Ok(path) = std::env::var("CLAUDE_FONT_METRICS") {
        let json = std::fs::read_to_string(path).unwrap();
        let n = crate::renderer::font_metrics_data::claude_register_font_metrics(&json).unwrap();
        println!("폭 표 등록 {n}");
    }
    let list = std::env::var("CLAUDE_LB_FILES").expect("CLAUDE_LB_FILES");
    let verbose = std::env::var("CLAUDE_LB_VERBOSE").is_ok();
    let (mut tot_p, mut tot_same, mut tot_lines, mut tot_lines_same) = (0usize, 0usize, 0usize, 0usize);
    for path in std::fs::read_to_string(&list).unwrap().lines().filter(|l| !l.trim().is_empty()) {
        let Ok(bytes) = std::fs::read(path.trim()) else { continue };
        let Ok(core) = DocumentCore::from_bytes(&bytes) else {
            println!("열기 실패\t{path}");
            continue;
        };
        let styles = resolve_styles_for_document(&core.document, core.dpi);
        let mut paras = Vec::new();
        for s in &core.document.sections {
            walk(&s.paragraphs, &mut paras);
        }
        let (mut np, mut same, mut lines, mut lines_same) = (0usize, 0usize, 0usize, 0usize);
        for p in paras {
            if p.line_segs.len() < 1 || p.text.chars().count() < 2 || !p.controls.is_empty() {
                continue;
            }
            let s0 = &p.line_segs[0];
            if s0.segment_width <= 0
                || p.line_segs.iter().any(|s| s.column_start != s0.column_start || s.segment_width != s0.segment_width)
                || p.line_segs.windows(2).any(|w| w[1].text_start <= w[0].text_start)
            {
                continue;
            }
            let want: Vec<u32> = p.line_segs.iter().map(|s| s.text_start).collect();
            if std::env::var("CLAUDE_LB_HEAD").is_ok() {
                // 글머리표, 번호 문단: 한글 줄마다 표식 자리의 범위(남긴 자리 - 다음 덩이 폭 < 표식 <= 남긴 자리)를 찍는다
                let ps = styles.para_styles.get(p.para_shape_id as usize);
                let head = ps.map(|s| s.head_type).unwrap_or_default();
                if !matches!(head, crate::model::style::HeadType::None) && p.char_shapes.len() == 1 {
                    let chars: Vec<char> = p.text.chars().collect();
                    let idx_of = |u: u32| p.char_offsets.iter().position(|o| *o == u).unwrap_or(chars.len());
                    let mut lang = 0usize;
                    let sid = p.char_shapes[0].char_shape_id;
                    let widths: Vec<i32> = chars
                        .iter()
                        .map(|ch| {
                            if !is_lang_neutral(*ch) {
                                lang = detect_lang_category(*ch);
                            }
                            let ts = resolved_to_text_style(&styles, sid, lang);
                            to_hwp(estimate_text_width_unrounded(&ch.to_string(), &ts))
                        })
                        .collect();
                    let kbu = ps.map(|s| s.korean_break_unit).unwrap_or(0);
                    let nid = ps.map(|s| s.numbering_id).unwrap_or(0);
                    let indent = ps.map(|s| (s.indent * 75.0).round() as i32).unwrap_or(0);
                    let bullet = nid.checked_sub(1).and_then(|i| styles.bullets.get(i as usize));
                    let cs = styles.char_styles.get(sid as usize);
                    for li in 0..want.len() {
                        let s = idx_of(want[li]);
                        let e = want.get(li + 1).map(|u| idx_of(*u)).unwrap_or(chars.len());
                        let mut te = e;
                        while te > s && chars[te - 1] == ' ' {
                            te -= 1;
                        }
                        let used: i32 = widths[s..te].iter().sum();
                        let slack = s0.segment_width - used;
                        let lower = if li + 1 < want.len() {
                            // 다음 덩이: 줄 끝 공백 + (글자 단위면 한 글자와 금칙, 어절 단위면 다음 공백까지)
                            let mut ne = e;
                            if kbu == 1 && chars.get(e).copied().is_some_and(is_hangul) {
                                ne = e + 1;
                                while ne < chars.len() && is_line_start_forbidden(chars[ne]) {
                                    ne += 1;
                                }
                            } else {
                                while ne < chars.len() && chars[ne] != ' ' {
                                    ne += 1;
                                }
                            }
                            let gap: i32 = widths[te..e].iter().sum();
                            let next: i32 = widths[e..ne].iter().sum();
                            (slack - gap - next).to_string()
                        } else {
                            "-".to_string()
                        };
                        println!(
                            "  머리	{head:?}	{nid}	{}	{:.2}	{}	{lower}	{slack}	indent{indent}	attr{:?}	dist{:?}	adj{:?}	ch{:?}	kbu{kbu}",
                            cs.map(|c| c.font_family.clone()).unwrap_or_default(),
                            cs.map(|c| c.font_size).unwrap_or(0.0),
                            if li == 0 { "첫줄" } else { "이어짐" },
                            bullet.map(|b| b.attr), bullet.map(|b| b.text_distance), bullet.map(|b| b.width_adjust), bullet.map(|b| b.bullet_char as u32),
                        );
                    }
                }
            }
            let mut q = p.clone();
            q.line_segs.clear();
            let bx = ParagraphBox::column(s0.column_start..s0.column_start + s0.segment_width);
            reflow_line_segs(&mut q, bx, &styles, core.dpi);
            let got: Vec<u32> = q.line_segs.iter().map(|s| s.text_start).collect();
            np += 1;
            if verbose {
                let f = styles.char_styles.get(p.char_shapes.first().map(|c| c.char_shape_id as usize).unwrap_or(0)).map(|c| c.font_family.clone()).unwrap_or_default();
                println!("  전체	{f}	{}", want.len());
            }
            lines += want.len();
            lines_same += want.iter().filter(|t| got.contains(t)).count();
            if got == want {
                same += 1;
            } else if verbose {
                // 처음 갈린 줄을 분석한다: 한글이 더 담았는가(넘친 양), 덜 담았는가(남긴 자리와 다음 글자)
                let chars: Vec<char> = p.text.chars().collect();
                let idx_of = |u: u32| p.char_offsets.iter().position(|o| *o == u).unwrap_or(chars.len());
                let k = want.iter().zip(got.iter()).position(|(a, b)| a != b).unwrap_or(want.len().min(got.len()));
                if k >= 1 {
                    let s = idx_of(want[k - 1]);
                    let eh = want.get(k).map(|u| idx_of(*u)).unwrap_or(chars.len());
                    let er = got.get(k).map(|u| idx_of(*u)).unwrap_or(chars.len());
                    let mut lang = 0usize;
                    let widths: Vec<i32> = chars
                        .iter()
                        .enumerate()
                        .map(|(i, ch)| {
                            if !is_lang_neutral(*ch) {
                                lang = detect_lang_category(*ch);
                            }
                            let utf16 = p.char_offsets.get(i).copied().unwrap_or(i as u32);
                            let sid = find_active_char_shape(&p.char_shapes, utf16);
                            let ts = resolved_to_text_style(&styles, sid, lang);
                            to_hwp(estimate_text_width_unrounded(&ch.to_string(), &ts))
                        })
                        .collect();
                    let width = |a: usize, b: usize| -> i32 {
                        let mut e = b.min(chars.len());
                        while e > a && chars[e - 1] == ' ' {
                            e -= 1;
                        }
                        widths[a.min(e)..e].iter().sum()
                    };
                    let ps = styles.para_styles.get(p.para_shape_id as usize);
                    let indent = ps.map(|s| (s.indent * 75.0).round() as i32).unwrap_or(0);
                    let head = ps.map(|s| format!("{:?}", s.head_type)).unwrap_or_default();
                    let kbu = ps.map(|s| s.korean_break_unit).unwrap_or(0);
                    let at = |i: usize| chars.get(i).copied().unwrap_or('∅');
                    let kind = if eh > er { "더담음" } else { "덜담음" };
                    let amount = s0.segment_width - width(s, eh);
                    let font0 = styles.char_styles.get(p.char_shapes.first().map(|c| c.char_shape_id as usize).unwrap_or(0)).map(|c| c.font_family.clone()).unwrap_or_default();
                    println!(
                        "  분석	{kind}	{amount}	줄{k}	indent{indent}	{head}	kbu{kbu}	한글끝[{}|{}]	rhwp끝[{}|{}]	다음폭{}	shapes{}	ctl{}	{font0}",
                        at(eh.saturating_sub(1)), at(eh), at(er.saturating_sub(1)), at(er),
                        widths.get(eh).copied().unwrap_or(0), p.char_shapes.len(), p.controls.len()
                    );
                }
                let t: String = p.text.chars().take(40).collect();
                let cs = p.char_shapes.first().map(|c| c.char_shape_id as usize).unwrap_or(0);
                let (font, size, ls, ratio) = styles
                    .char_styles
                    .get(cs)
                    .map(|c| (c.font_family.clone(), c.font_size, c.letter_spacing, c.ratio))
                    .unwrap_or_default();
                let nshapes = p.char_shapes.len();
                println!("  다름	{path}	{font}	{size:.2}	{ls:.2}	{ratio:.0}	{nshapes}	{}	{:?}	{:?}	{t}", s0.segment_width, want, got);
            }
        }
        println!("{np}\t{same}\t{lines}\t{lines_same}\t{path}");
        tot_p += np;
        tot_same += same;
        tot_lines += lines;
        tot_lines_same += lines_same;
    }
    println!(
        "합계 문단 {tot_p} 같음 {tot_same} ({:.2}%) 줄 {tot_lines} 시작 일치 {tot_lines_same} ({:.2}%)",
        100.0 * tot_same as f64 / tot_p.max(1) as f64,
        100.0 * tot_lines_same as f64 / tot_lines.max(1) as f64
    );
}

#[test]
#[ignore]
fn claude_lb_one() {
    if let Ok(path) = std::env::var("CLAUDE_FONT_METRICS") {
        let json = std::fs::read_to_string(path).unwrap();
        let n = crate::renderer::font_metrics_data::claude_register_font_metrics(&json).unwrap();
        println!("폭 표 등록 {n}");
    }
    let Ok(path) = std::env::var("CLAUDE_LB_ONE") else { return };
    let key = std::env::var("CLAUDE_LB_KEY").unwrap_or_default();
    let core = DocumentCore::from_bytes(&std::fs::read(&path).unwrap()).unwrap();
    let styles = resolve_styles_for_document(&core.document, core.dpi);
    let mut paras = Vec::new();
    for s in &core.document.sections {
        walk(&s.paragraphs, &mut paras);
    }
    for p in paras.into_iter().filter(|p| p.text.starts_with(&key)).take(2) {
        let Some(s0) = p.line_segs.first() else { continue };
        let want: Vec<u32> = p.line_segs.iter().map(|s| s.text_start).collect();
        let mut q = p.clone();
        q.line_segs.clear();
        reflow_line_segs(&mut q, ParagraphBox::column(s0.column_start..s0.column_start + s0.segment_width), &styles, core.dpi);
        let got: Vec<u32> = q.line_segs.iter().map(|s| s.text_start).collect();
        let ps = styles.para_styles.get(p.para_shape_id as usize);
        println!(
            "box cs={} sw={} 한글{:?} rhwp{:?} indent={:?} margin_l={:?} head={:?} kbu={:?} ebu={:?} condense={:?} shapes={:?}",
            s0.column_start, s0.segment_width, want, got,
            ps.map(|s| (s.indent * 75.0).round()), ps.map(|s| (s.margin_left * 75.0).round()), ps.map(|s| s.head_type),
            ps.map(|s| s.korean_break_unit), ps.map(|s| s.english_break_unit), ps.map(|s| s.condense_min_space),
            p.char_shapes.iter().map(|c| (c.start_pos, c.char_shape_id)).collect::<Vec<_>>()
        );
        let chars: Vec<char> = p.text.chars().collect();
        let mut lang = 0usize;
        let mut cum = 0i32;
        let mut line = String::new();
        for (i, ch) in chars.iter().enumerate() {
            let utf16 = p.char_offsets.get(i).copied().unwrap_or(i as u32);
            if want.contains(&utf16) && i > 0 {
                println!("  한글 줄 끝: 누적 {cum}  {line}");
                cum = 0;
                line.clear();
            }
            if !is_lang_neutral(*ch) {
                lang = detect_lang_category(*ch);
            }
            let sid = find_active_char_shape(&p.char_shapes, utf16);
            let ts = resolved_to_text_style(&styles, sid, lang);
            let w = to_hwp(estimate_text_width_unrounded(&ch.to_string(), &ts));
            cum += w;
            line.push_str(&format!("{ch}{w} "));
        }
        println!("  마지막 줄: 누적 {cum}  {line}");
    }
}
