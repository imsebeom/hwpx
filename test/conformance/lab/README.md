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

## 남은 것 (2026-10-17)

- 좁은 칸에서 한/글이 문단 여백을 무시하는 경우(d034: 칸 2447, 여백 500+200, 한/글 horzpos 0)
- 한/글 줄 폭이 칸 폭보다 큰 경우(d010 칸 45: horzsize 44601 > 칸 45038 − 여백)
- 함초롬돋움 `…` 등 한/글이 Windows 글꼴 파일과 다른 값을 쓰는 글자
- 쪽수(88.4%)와 문단 쪽 일치율은 아직 줄 나눔만큼 다루지 않았다
