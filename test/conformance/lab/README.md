# 조판 규칙 실험실 (2026-10-17)

채점기(`../score.mjs`)가 찾은 불일치를 한/글 2024 블랙박스 실측으로 규칙까지 좁히고, 엔진 패치로 옮기는 곳이다.
한/글 바이너리는 보지 않는다. 입력 문서를 바꿔 한/글이 낸 결과(다시 저장한 HWPX 의 줄 배치, PDF 글자 위치)만 본다.

## 한 바퀴

1. 불일치 하나 보기: `node ../diag.mjs <id> <문단> [목록 ID]` (목록 ID 는 `mismatches.jsonl` 의 `list`)
2. 가설에 맞춘 실험 문서: 변형 목록 JSON 을 만들고 `python make.py e?.json ../out/lab/e?`
   - 바꿀 수 있는 것: 글꼴, 크기, 장평, 자간, useFontSpace, 정렬, condense, 줄 나눔 기준, 들여쓰기, 왼쪽과 오른쪽 여백, 문단 글
3. 한/글로 열어 다시 저장하고 PDF 로: `python hidden_desktop.py python <REA>/hwp2024/hwpx_lab/measure.py <입력> <재저장> <결과.json>`
4. 비교
   - 줄 나눔: `node cmplines.mjs <재저장 폴더> --show` (wasm 엔진), `python nativecmp.py <재저장 폴더> --show` (네이티브, 빌드 1분)
   - 글자 폭: `ALL=1 python pdfadv.py <재저장 폴더> han.json`, `ALL=1 node rhwpadv.mjs <입력 폴더> rhwp.json`, `python cmpadv.py han.json rhwp.json 0.3`
   - 칸 문단의 rhwp 줄 정보: `node cellprobe.mjs <id> <칸 순번> <문단>`
5. 엔진 수정: `apply_*.py` 의 EDITS 로 소스(`editor/.build/rhwp`)를 고치고 네이티브로 확인한 뒤 `python export_patches.py apply_x <id 접두사>` 로 `editor/patches/*.rs` 를 만들어 `setup.mjs` 에 등록
6. 확인: `node ../score.mjs out/score_bN`, 회귀 `node ../../linebreak/svghash.mjs <pkg> ../../linebreak/results/reg_corpus_1014.txt <출력.json>` 을 패치 전과 후 엔진으로

## 네이티브 확인 도구

`claude-linestarts.rs` 를 `editor/.build/rhwp/src/bin/` 에 두고 `cargo build --bin claude-linestarts` (약 1분). wasm 빌드(10분)를 기다리지 않고 줄 나눔을 본다.
칸까지 보려면 `CLAUDE_CELLS=1`.

## 함정

- 🔴 `setup.mjs --build` 는 `rhwp/pkg/.claude-patched` 에 패치 ID 가 있으면 Rust 빌드를 통째로 건너뛴다. 이미 넣은 패치를 고쳤으면 표지에서 그 ID 를 지운다.
- 한/글 PDF 좌표는 글자 크기 대비 0.9955 배이고 눈금이 약 0.12pt 다(`cmpadv.py` 가 되돌린다). 0.1pt 문턱은 잡음이 많아 0.3pt 를 쓴다.
- rhwp 의 줄 시작 값은 첫 문단의 구역 정의와 단 정의 조판 부호(각 8)를 센다. 한/글 textpos 도 같다.
- HWPX `breakNonLatinWord="KEEP_WORD"` 는 한/글에서 **글자 단위**, `BREAK_WORD` 가 어절 단위다(e3).

## 찾은 규칙

| 실험 | 규칙 | 엔진 |
|---|---|---|
| e1 | 빈칸 폭: useFontSpace=0 이면 글자 크기의 절반(장평, 자간 적용), 1 이면 글꼴 파일의 빈칸 폭. 자간은 장평 적용 뒤 폭에 대한 비율 | `use-font-space-*` 패치 |
| e3 | 줄 나눔 기준(위 함정) | 이미 같음 |
| e2, e5 | 기호 폭: 굴림, 바탕, 돋움, 나눔고딕, 맑은 고딕은 글꼴 파일 폭 그대로(엔진 내장 표의 `…`, `▪`, `◦`, `■` 등이 틀림). 휴먼명조는 `·`, `…`, 따옴표가 전각. 함초롬돋움 `…` 는 파일(0.702em)과 달리 0.964em | `font-file-first-*`(함초롬 계열 제외), `hft-symbol-widths-*` |
| e6, e7, e8 | 글자의 언어 범주는 문맥과 상관없이 고정: 빈칸, ASCII 문장 부호, Latin-1 기호, 따옴표는 라틴 글꼴, `– — ― † ‡ • … ‰ ′ ″ ※ ‼ ™ ℃` 는 기호 글꼴. rhwp 는 이들을 앞 글자 범주로 쟀다 | `lang-category-*` |
| e9 | 글꼴 파일이 없는 한컴 내장 글꼴 11종(HCI Poppy, 윤명조, 신명 계열 등)의 글자 폭을 40pt 로 실측해 표로 둔다(`editor/hft-metrics.json`). 대체 글꼴(HCI Poppy → Palatino Linotype)과 대부분 같고 `·`, `'`, `/` 가 다르다 | `hft-source-name-*`, font-metrics.mjs |
| d014 | 칸 문단도 줄 폭에서 문단 왼쪽, 오른쪽 여백을 뺀다(칸 폭 − 칸 여백 − 문단 여백, 한/글 값은 4 단위로 내림). rhwp 는 편집 경로만 빼고 문서를 여는 경로는 안 뺐다 | `cell-para-margin-*` |
| e10, e11 | 진하게도 보통 글꼴의 폭으로 조판한다(글꼴 8종 중 7종은 폭이 같고, 맑은 고딕은 보통 파일 값). 그리기만 굵게 | `bold-regular-width-*` |
| 정답본 | 비율 줄 간격 = 반올림(내림(줄 높이/4) × (비율−100)/100) × 4. 105,341줄 중 96.60% 일치(종전 식 95.93%) | `spacing-quantum-*` |
| e13 | 쪽 끝 마지막 줄은 남은 높이가 줄 높이(줄 간격 제외)를 넘기만 하면 넣는다. 같으면 넘긴다 | `page-end-fit-*` |
| d134 | 제목 외톨이 보정(저장 vpos 로 쪽 넘침 판단)은 한/글이 저장한 줄 위치가 있을 때만 쓴다. 엔진이 만든 합성 줄의 vpos 는 쪽 나눔을 모른다 | `heading-orphan-stored-*` |
| 정답본 | 줄 기록 하나뿐인 칸 문단에 합성 줄을 덧붙이지 않는다. 표 하나만 든 빈 문단의 높이는 선언한 표 높이 | `no-synth-cell-line-*`, `empty-host-block-*` |
| e14, e15 | 함초롬바탕, 함초롬돋움: 한글 음절은 모두 0.970em. 엔진 내장 표에 없는 기호(①, →, Ⅰ, ℃, ─ 등 121자)를 엔진은 1em 이나 0.5em 으로 어림했는데 한/글은 대부분 0.970em. 함초롬돋움은 내장 표의 일반 문장 부호 67자(…, —, •, ※ 등)도 다르다. 40pt 로 2,872자를 잰 표를 `hft-metrics.json` 에 둔다. PDF 좌표는 조판 값의 0.99946 배 | font-metrics.mjs |
| e16, e17 | `!` 의 전진 폭은 글꼴과 상관없이 0.5em(글꼴 6종). PDF 에는 글리프 뒤에 빈칸 글자를 하나 더 찍어 채운다 | `exclam-half-*` |
| d076 | 한 이름에 굵기 파일이 여럿인 글꼴(Pretendard)은 굵게 비트가 꺼져 있어 Black 파일이 보통으로 뽑혔다. OS/2 usWeightClass 400, 700 에 가까운 얼굴을 고른다 | font-metrics.mjs |
| 정답본 | 문단 모양 `lineWrap="SQUEEZE"`(한 줄로 입력) 문단 818개 중 812개가 한 줄(나머지는 강제 줄바꿈). 엔진은 칸 subList 의 lineWrap 만 봤고, 직렬화는 문단 모양 lineWrap 을 늘 BREAK 로 썼다 | `para-line-wrap-*` |

## 남은 것 (2026-10-18)

- 좁은 칸에서 한/글이 문단 여백을 무시하는 경우(d034: 칸 2447, 여백 500+200, 한/글 horzpos 0)
- 한/글 줄 폭이 칸 폭보다 큰 경우(d010 칸 45: horzsize 44601 > 칸 45038 − 여백)
- Word 호환 문서(`compatibleDocument targetProgram="MS_WORD"`, `adjustLineheightToFont`)는 줄 높이가 글꼴 세로 지표 × 1.3 이다
  (Pretendard 1.1934 → 1.551, 맑은 고딕 1.3301 → 1.73). 정답본 2개(d076, d133)뿐이라 미뤘다. 문단 모양 `fontLineHeight="1"` 도 함초롬바탕에서 1.3
- `!` 뒤에 한/글이 PDF 에 찍는 빈칸은 글자 위치 비교(advances, pdfadv)에서 빈칸으로 잡힌다
- 쪽수 지표 91.1%, 문단 쪽 94.1%(네이티브). 남은 쪽수 불일치 29개 문서

## 진단 도구 (2026-10-18 추가)

- `pagediff.py <id>`: 쪽이 처음 어긋나는 본문 문단과 앞뒤
- `vydiff.py <id> [시작] [개수]`: 문단 사이 간격(한/글 vertpos 대 rhwp 커서 y)
- `mmstat.py <불일치.jsonl>`: 불일치를 방향(먼저, 늦게 꺾음)과 글꼴로 묶는다
- `harvest_spacing.py`, `harvest_lineheight.py`: 정답본 줄 기록에서 줄 간격, 줄 높이 배율을 모은다
- `claude-linestarts` 환경 변수: `CLAUDE_VY`(문단 y), `CLAUDE_XP=<문단|all>`(글자 x), `CLAUDE_ITEMS`(쪽 항목), `CLAUDE_SVG=<폴더>`(쪽 SVG), `CLAUDE_METRICS_DIR`(문서별 폭 표, `dump_metrics.mjs` 로 만든다)
