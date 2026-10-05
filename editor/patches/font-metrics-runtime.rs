// ==== find ====
    let (alias_resolved_name, alias_rule_id) = resolve_projected_metric_alias(name);
    let slots = metric_index().get(alias_resolved_name)?;
    let selected = slots[metric_slot_index(bold, italic)];
// ==== replace ====
    let (alias_resolved_name, alias_rule_id) = resolve_projected_metric_alias(name);
    // [claude-hwpx font-metrics-runtime] 내장 표에 없는 글꼴은 실행 중에 등록한 폭 표(설치된 글꼴 파일에서 읽은 것)를 본다
    let Some(slots) = metric_index().get(alias_resolved_name) else {
        return claude_runtime_metric_decision(name, alias_resolved_name, alias_rule_id, bold);
    };
    let selected = slots[metric_slot_index(bold, italic)];
// ==== next ====
/// [#4709] 이 스타일의 글자폭 배치에 실제로 쓰인 내장 메트릭 face 이름.
// ==== replace ====
/// 실행 중에 등록한 글꼴 폭 표(이름마다 보통, 굵은 얼굴).
///
/// 한/글은 설치된 글꼴 파일의 전진 폭(hmtx)으로 줄을 나눈다(2026-10-06 폭 사다리: 글꼴 파일 폭 + 4 HWPUNIT 규칙이
/// 84건 모두 일치). 내장 표에 없는 글꼴은 한글 1.0em, 그 밖 0.5em 으로 어림해 줄 나눔이 어긋났고, 글꼴마다 표를
/// 빌드에 넣어야 했다. 에디터 서버가 문서가 쓰는 글꼴의 파일을 읽어(editor/font-metrics.mjs) `registerFontMetrics` 로
/// 넘기면 여기 담는다. 내장 표가 있는 글꼴에는 쓰지 않는다(이미 맞는 문서를 건드리지 않는다).
struct ClaudeRuntimeFaces {
    regular: Option<&'static FontMetric>,
    bold: Option<&'static FontMetric>,
}

static CLAUDE_RUNTIME_METRICS: OnceLock<std::sync::RwLock<HashMap<String, ClaudeRuntimeFaces>>> =
    OnceLock::new();
/// 하나라도 등록했는가 — 등록이 없을 때 글자마다 잠금을 잡지 않으려고 둔다.
static CLAUDE_RUNTIME_ANY: std::sync::atomic::AtomicBool =
    std::sync::atomic::AtomicBool::new(false);
static CLAUDE_ZERO_MAP: [u8; 28] = [0; 28];
static CLAUDE_IDENTITY_MAP: [u8; 28] = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
    27,
];

fn claude_runtime_metric_decision<'a>(
    requested_name: &'a str,
    alias_resolved_name: &'a str,
    alias_rule_id: Option<&'static str>,
    bold: bool,
) -> Option<MetricLookupDecision<'a>> {
    if !CLAUDE_RUNTIME_ANY.load(std::sync::atomic::Ordering::Relaxed) {
        return None;
    }
    let map = CLAUDE_RUNTIME_METRICS.get()?.read().ok()?;
    let faces = map
        .get(requested_name)
        .or_else(|| map.get(alias_resolved_name))?;
    // 굵은 얼굴이 없으면 보통 얼굴로(내장 표의 3단 폴백과 같게 bold_fallback 을 켠다)
    let (metric, bold_fallback, match_kind) = match (bold, faces.bold, faces.regular) {
        (true, Some(metric), _) | (false, _, Some(metric)) => (metric, false, MetricMatchKind::Exact),
        (true, None, Some(metric)) => (metric, true, MetricMatchKind::NameFirst),
        (false, Some(metric), None) => (metric, false, MetricMatchKind::NameFirst),
        _ => return None,
    };
    Some(MetricLookupDecision {
        requested_name,
        alias_resolved_name,
        alias_rule_id,
        metric,
        bold_fallback,
        match_kind,
        entry_index: usize::MAX,
    })
}

/// 이 글꼴 이름의 폭 표가 빌드에 들어 있는가(별칭 포함). 서버가 파일에서 읽을 글꼴을 고를 때 묻는다.
pub fn claude_has_builtin_metric(name: &str) -> bool {
    metric_index().contains_key(resolve_projected_metric_alias(name).0)
}

/// 폭 표 등록. 반환: 새로 등록한 얼굴 수. 내장 표가 있는 이름과 이미 등록한 (이름, 굵기)는 건너뛴다.
///
/// JSON: `[{"name": 글꼴 이름, "bold": 굵은 얼굴인가, "em": unitsPerEm,
///   "hangul": 음절 폭 하나 | 음절 11172개의 폭 | null,
///   "ranges": [[시작 코드, [폭…]]…], "uniform": [[시작 코드, 끝 코드, 폭]…]}]`
/// 폭은 글꼴 단위(em 기준)다. 폭 0 은 글리프 없음으로 보고 어림값을 쓴다.
pub fn claude_register_font_metrics(json: &str) -> Result<usize, String> {
    let parsed: serde_json::Value = serde_json::from_str(json).map_err(|e| e.to_string())?;
    let list = parsed.as_array().ok_or("폭 표 목록이 배열이 아니다")?;
    let lock = CLAUDE_RUNTIME_METRICS.get_or_init(|| std::sync::RwLock::new(HashMap::new()));
    let mut map = lock.write().map_err(|e| e.to_string())?;
    let width = |v: &serde_json::Value| v.as_u64().unwrap_or(0).min(u64::from(u16::MAX)) as u16;
    let mut added = 0;
    for face in list {
        let Some(name) = face.get("name").and_then(|v| v.as_str()) else {
            continue;
        };
        let em = face.get("em").and_then(|v| v.as_u64()).unwrap_or(0);
        if name.is_empty() || em == 0 || em > u64::from(u16::MAX) || claude_has_builtin_metric(name)
        {
            continue;
        }
        let bold = face.get("bold").and_then(|v| v.as_bool()).unwrap_or(false);
        let already = map
            .get(name)
            .is_some_and(|faces| if bold { faces.bold.is_some() } else { faces.regular.is_some() });
        if already {
            continue;
        }
        let mut ranges: Vec<LatinRange> = Vec::new();
        for range in face.get("ranges").and_then(|v| v.as_array()).into_iter().flatten() {
            let (Some(start), Some(widths)) = (
                range.get(0).and_then(|v| v.as_u64()),
                range.get(1).and_then(|v| v.as_array()),
            ) else {
                continue;
            };
            if widths.is_empty() || start > 0x10FFFF {
                continue;
            }
            let widths: &'static [u16] =
                Box::leak(widths.iter().map(width).collect::<Vec<u16>>().into_boxed_slice());
            ranges.push(LatinRange {
                start: start as u32,
                end: start as u32 + widths.len() as u32 - 1,
                widths,
            });
        }
        for range in face.get("uniform").and_then(|v| v.as_array()).into_iter().flatten() {
            let (Some(start), Some(end)) = (
                range.get(0).and_then(|v| v.as_u64()),
                range.get(1).and_then(|v| v.as_u64()),
            ) else {
                continue;
            };
            let Some(value) = range.get(2).map(width).filter(|w| *w > 0) else {
                continue;
            };
            if end < start || end > 0x10FFFF || end - start > 0x10000 {
                continue;
            }
            let widths: &'static [u16] =
                Box::leak(vec![value; (end - start + 1) as usize].into_boxed_slice());
            ranges.push(LatinRange {
                start: start as u32,
                end: end as u32,
                widths,
            });
        }
        let hangul = match face.get("hangul") {
            Some(serde_json::Value::Array(all)) if all.len() == 11172 => Some(HangulMetric {
                cho_groups: 19,
                jung_groups: 21,
                jong_groups: 28,
                cho_map: &CLAUDE_IDENTITY_MAP[..19],
                jung_map: &CLAUDE_IDENTITY_MAP[..21],
                jong_map: &CLAUDE_IDENTITY_MAP,
                widths: Box::leak(all.iter().map(width).collect::<Vec<u16>>().into_boxed_slice()),
            }),
            Some(single) if single.as_u64().is_some_and(|w| w > 0) => Some(HangulMetric {
                cho_groups: 1,
                jung_groups: 1,
                jong_groups: 1,
                cho_map: &CLAUDE_ZERO_MAP[..19],
                jung_map: &CLAUDE_ZERO_MAP[..21],
                jong_map: &CLAUDE_ZERO_MAP,
                widths: Box::leak(vec![width(single)].into_boxed_slice()),
            }),
            _ => None,
        };
        let hangul: Option<&'static HangulMetric> = hangul.map(|h| &*Box::leak(Box::new(h)));
        let metric: &'static FontMetric = Box::leak(Box::new(FontMetric {
            name: Box::leak(name.to_string().into_boxed_str()),
            bold,
            italic: false,
            em_size: em as u16,
            latin_ranges: Box::leak(ranges.into_boxed_slice()),
            hangul,
        }));
        let faces = map.entry(name.to_string()).or_insert(ClaudeRuntimeFaces {
            regular: None,
            bold: None,
        });
        if bold {
            faces.bold = Some(metric);
        } else {
            faces.regular = Some(metric);
        }
        added += 1;
    }
    if !map.is_empty() {
        CLAUDE_RUNTIME_ANY.store(true, std::sync::atomic::Ordering::Relaxed);
    }
    Ok(added)
}

/// [#4709] 이 스타일의 글자폭 배치에 실제로 쓰인 내장 메트릭 face 이름.
