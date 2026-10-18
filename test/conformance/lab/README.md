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

- 🔴 실험 문서의 글꼴 type 이 결과를 바꾼다. base.hwpx 는 TTF 라 파일 없는 한컴 글꼴을 TTF 로 적으면 한/글이 다른 글꼴로 바꿔 쓴다.
  문서가 쓰는 type 을 먼저 세고(`<hh:font face type>`), HFT 면 변형에 `"fontType": "HFT"` 를 준다(e22, e23)

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
| e19 | 줄 끝 빈칸은 시작 위치가 줄 폭 이하이면 앞줄에 남고(자기 폭만큼 넘침) 나머지는 다음 줄 앞으로 간다. 글자만으로 줄 폭을 넘어 빈칸 압축으로 들어온 줄은 끝 빈칸을 모두 앞줄에 둔다 | `space-no-overflow-*` |
| 정답본 | 글자 단위(KEEP_WORD) 문단은 「AI|를」 「10|문항」처럼 ASCII 영문자, 숫자 바로 뒤 한글 앞에서도 꺾는다(97곳). 어절 단위 문단의 같은 자리는 칸보다 긴 어절을 억지로 자른 것이라 넣지 않는다 | `latin-hangul-break-*` |
| d114 | 블록처럼 다루는 글자처럼 취급 표(flowWithText=0)의 줄 높이 = 선언 높이 + 바깥 여백 위아래. 쪽 끝 맞춤도 그 높이로 본다 | `tac-outer-margin-fit-*` |
| d242, d221 | 글자처럼 취급 표의 줄 높이 = 표 높이 + 바깥 여백 위아래 + 위, 아래 캡션 높이(마지막 줄 간격 제외) + 캡션 간격(8412 + 283×2 + 1000 + 283 = 10261). 한 줄짜리 표 문단은 쪽 끝에서 문단 아래 간격 없이 위 간격 + 줄 높이만 들어가면 된다 | `tac-caption-line-*` |
| e20 | 글꼴 파일에 있는 글자는 파일 폭 그대로(HY 글꼴, 바탕체, 굴림체의 전각 · ‘ ’ “ ” …, 모든 글꼴의 ㆍ 도 1em). 파일에 없는 글자는 함초롬바탕 폭(‧ 290, ◦ 970, − 970, ‣ 369, • 399). 엔진의 문장 부호 덮어쓰기(0.3em, 0.5em)와 ㆍ 0.5em 대체는 등록 표에서 끈다 | font-metrics.mjs(함초롬 대체), `runtime-no-overlay-*` |
| e21, e22 | 한양신명조, 한양중고딕, 한양견고딕, 한양견명조(파일 없음) 3,072자 실측 표. 글꼴 type 이 TTF 면 한/글이 견고딕, 견명조의 기호를 함초롬으로 바꿔 쓰므로 문서에 많은 type HFT 로 잰다 | hft-metrics.json |
| e23 | HFT 글꼴 9종(명조, HCI Poppy, HCI Hollyhock, 신명 계열 4, #태고딕, 산세리프)을 type HFT 로 다시 잼. e9(TTF)와 일반 문장 부호 78자가 다르다(HFT 는 1em) | hft-metrics.json |
| e24, e25 | 빈칸: 「글꼴에 어울리는 빈칸」 끔은 모든 글꼴 0.5em(한양중고딕, 한양신명조도 크기와 상관없이 0.5em — 엔진의 0.55em, 0.40em 예외는 다른 판의 값). 켬은 글꼴마다 다르다(함초롬 300, 윤 계열 333, 한양 4종과 명조 500, 신명 계열 400, HCI Poppy 251) | hft-metrics.json 빈칸, `runtime-no-space-overlay-*` |
| d160 | 글 줄 뒤에 붙은 어울림 표(문단 기준)의 흐름 전진 = max(글 줄, 오프셋 + 바깥 여백 위 + 선언 높이 + 바깥 여백 아래). 표 전체 높이에 든 문단 줄 간격을 쓰지 않는다 | `para-float-text-host-*` |
| e26 | 고정폭 빈칸(fwSpace)은 글꼴, 설정과 상관없이 0.25em, 묶음 빈칸(nbSpace)은 늘 0.5em(「글꼴에 어울리는 빈칸」을 켜도). U+3000 은 글꼴 폭 | `fixed-spaces-*` |
| e27 | 글자 겹치기(동그라미 안 글자, compose)의 폭 = max(겹친 글자의 글꼴 폭, 동그라미 ◯ 폭 — 대개 함초롬 대체 0.970em). 함초롬바탕 「유」 0.970, 맑은 고딕 「유」 1.0, 「1」 0.970. 엔진은 폭 0 으로 둔다(아직 안 고침) | 없음 |
| e29 | 번호 문단(heading NUMBER)의 본문 시작 = 번호 글의 실제 폭(글꼴마다 다름, 「1.」 함초롬바탕 17.4pt, 맑은 고딕 15.4pt, 20pt) + 본문과의 거리(PERCENT 면 글자 크기 x %, HWPUNIT 이면 그 값) + 너비 보정값. 자동 내어쓰기면 이어지는 줄도 그 자리, 아니면 첫 줄만 좁다. useInstWidth=0 은 글꼴과 상관없이 약 1em(규칙 미확정, 엔진은 안 다룸) | `number-head-*` |
| d089 | 표만 담은 빈 문단(위아래 배치)은 문단 아래 간격을 흐름에 더하지 않는다(정답본 15건 중 15건, `harvest_tblnext.py`) | `empty-host-no-after-*` |
| d089 | 한/글 vertpos 는 문단 위아래 간격을 품는다. 엔진이 줄 배치 없는 문단의 vpos 를 줄 높이와 줄 간격만으로 이어 만들어, 둘째 쪽부터 스냅이 문단마다 간격만큼 끌어올렸다 | `synth-vpos-spacing-*` |
| d124 | 「표 나눔」(pageBreak=TABLE) 표는 행 경계에서만 나뉜다(정답본 쪽 넘는 TABLE 표 12건 중 10건, 나머지 2건은 칸 안 표가 든 행이라 높이 추정이 어긋남. `harvest_tblsplit.py`). 「셀 단위로 나눔」(CELL)은 행 안에서도 가른다(81건). 엔진은 TABLE 을 CellBreak 로 읽어 쪽 끝 행을 칸 안에서 갈랐다. 쪽 첫 행이 아니면 통째로 넘긴다 | `table-whole-rows-*` |
| d309 | 줄 시작 = 앞 줄 마지막 글자 바로 다음(UTF-16). 줄 경계의 조판 부호(하이퍼링크 시작 8칸 등)는 새 줄에 든다. 강제 줄바꿈 뒤로만 좁히면 2줄, 모든 줄 경계에 쓰면 7줄이 맞고 새로 틀린 줄 0 | `break-ctrl-start-*` |
| e30 | 글머리표 칸: ASCII(-, o)는 반각, ▶ ● ※ 와 기호 글꼴 전용 영역(U+F06C 등)은 전각. 글꼴과 무관(엔진 규칙과 같음) | 없음(확인) |
| e31 | 글머리표 글자 모양 크기가 0 이면 문단 글자 크기로 자리를 잡는다(11pt 면 11pt) | `bullet-zero-size-*` |
| e32, e33 | 「•」(U+2022)는 줄머리 금칙이 아니다. KEEP_WORD 문단에서 한/글은 「•」 뒤에서 꺾고, 안 들어가면 앞에서 꺾는다. 엔진은 「•」 뒤 한글 앞을 꺾는 자리로 보지 않아 「•」 앞까지 되돌아갔다. 「·」 「‧」는 줄머리 금칙(엔진과 같음) | `bullet-dot-word-*` |
| e34, e35 | 빈칸 2개 이상 묶음 가운데서 줄을 꺾으면 앞줄에 빈칸을 적어도 둘 남긴다(남는 폭이 빈칸 하나보다 좁아도). 폭이 남으면 e19 규칙대로 더 남긴다. 정답본 약 150곳 중 한/글이 하나만 남긴 곳 0(`harvest_spacerun.py`). 정렬(양쪽, 왼쪽)과 상관없음 | `space-run-keep2-*` |
| d113 | 동그라미 글자 겹치기(`hp:compose` SHAPE_CIRCLE)는 「◯」 글리프와 작게 줄인 안 글자로 그리고, 그 자리 글자 모양의 ◯ 폭(장평 반영, 자간 빼고)만큼 차지한다(9.24pt = 10pt x 0.95 x 함초롬바탕 0.97em). 엔진은 줄 나눔에서 폭 0 이었다. 사각형 등 다른 테두리는 실측 없음 | `char-overlap-width-*` |
| 빌더 차트 | `c:title` 이 없어도 `autoTitleDeleted=0` 이고 이름 있는 계열이 하나면 그 이름을 제목으로 그린다(한/글 PDF). 여러 계열은 실측 없음 | `chart-auto-title-*` |
| 정답본, d078 | 쪽 나눔(pageBreak=1) 문단 바로 앞 빈 문단이 현재 쪽에 안 들어가면 한/글 2024 는 다음 쪽 첫머리로 넘긴다(그래서 빈 쪽이 생긴다). 그런 빈 문단 11개 중 9개, 흡수 1개(`harvest_emptybreak.py`). 엔진의 흡수 분기(Task #967, HWP5 표본)는 HWP5 출처에만 | `empty-before-break-*` |
| e36, e37 | 1단 구역의 단 나누기(columnBreak=1) 문단은 글이든 빈 문단이든 새 쪽을 연다(다음이 쪽 나눔이면 빈 쪽). 단 여러 쪽에 걸쳐 나뉜 표 바로 다음 문단이면 무시한다(d058 사본 변형 셋: 원본 무시, 표를 한 쪽으로 줄이면 지킴, 사이에 글 문단을 넣으면 지킴). e37 변형은 `apply_ops.mjs` 로 만들었다(표 T6 행 3~30 지우기, p11 뒤 글 문단 넣기) | `colbreak-after-split-table-*` |
| d076, d133 | Word 호환 문서(`compatibleDocument targetProgram="MS_WORD"` 에 `adjustLineheightToFont`)의 비율 간격 줄: 줄 높이 = 크기 x 글꼴 hhea (ascender + descender + lineGap)/em x 1.3(맑은 고딕 1.729, Pretendard 1.551), 기준선 = ascender x 크기 + (줄 높이 - hhea 높이)/2, 간격은 그 줄 높이에 기존 4 단위 식(`harvest_wordcompat.py`). 문단 끝 빈 run 이 글보다 크면 줄 높이 = 빈 run 줄 높이 + 글 아랫부분, 기준선과 간격 기준은 빈 run 의 것(d133 한 줄 문단 126줄, `harvest_wordmix.py`). 세로 수치는 `font-metrics.mjs` 가 글꼴 파일에서 읽어 `vm` 으로 넘긴다. 두 문서 본문 줄 217개 모두 일치(`segcmp.py`), 쪽수 94.5 → 95.1% | `word-compat-lineheight-*` |
| 정답본 | 글 없는 줄(글자처럼 취급 개체만 든 줄, 빈 문단)의 줄 높이와 간격은 그 줄에 걸친 run 가운데 가장 큰 글자 크기로 셈한다. 구역 정의만 든 첫 run 과 끝 빈 run 도 친다(`secpr_engine.py`: 첫 문단 일치 292 → 307, d001 1900, 1900, 2200 → 간격 1320. `harvest_emptyruns.py`: 빈 문단 11건 중 10건, 예외 d174). 문단 쪽 6887 → 6888 | `ctrl-line-max-charpr-*` |
| 정답본, 회귀 | 글자처럼 취급 표만 든 한 줄 문단은 다음 문단까지 「줄 높이 + 줄 간격 전체」만큼 내려간다(`harvest_tacstep.py`: 1,700건 중 1,685건, 엔진 cap 「줄 높이 + 줄 간격/2 + 바깥 위 여백」은 0건). 엔진이 만든 줄(줄 배치 없는 문서, 편집 뒤)에서 cap 을 풀었다. 함께 드러난 쪽 끝 판정 둘: 한 줄짜리 글자처럼 취급 표(블록 표 경로 포함)와 글 없이 개체만 든 문단은 「위 간격 + 줄 높이」만 들어가면 된다(d292 p75, d034 p400). 쪽수 95.1 → 96.0%, 문단 쪽 98.7 → 99.2%, 줄바꿈 그대로. 회귀 코퍼스 바뀐 4개 문서를 한/글로 열어 보니 쪽수 모두 일치(전에는 2개 틀림) | `tac-cap-synth-*` |
| 정답본 | 글 없는 문단에 문단 기준 위아래 배치 개체 하나만 있으면 다음 문단 vpos - 이 문단 vpos = 세로 오프셋 + 바깥 여백 위아래 + 개체 높이 - 이 문단 위 간격(`harvest_floatpic.py`: 그림 6건 모두, 표 241건). 개체 위치는 위 간격을 빼기 전 문단 시작 기준이고 다음 문단 위 간격은 겹쳐 사라진다. 엔진의 그림, 도형 경로는 빈 줄에 개체 높이 + 아래 여백을 더해 오프셋과 위 여백을 빼먹었다(d266 p7 +1700). 쪽수 96.0 → 96.3%(d114) | `empty-host-float-pic-*` |
| d193 사본 실험 | 나눔 「나누지 않음」에 flowWithText=0 인 문단 기준 위아래 배치 표는 남은 자리에 안 들어가도 한/글이 다음 쪽으로 넘기지 않고 그 쪽에 넘쳐 둔다. 앞에 빈 문단을 넣어 용지 밖까지 밀어도 그대로이고, 가로 기준(PARA, COLUMN)과는 무관하다. flowWithText=1 이거나 나눔이 CELL, TABLE 이면 다음 쪽 맨 위로 넘긴다(`harvest_overflowtbl.py`, `exp/make_push.py`, `exp/make_attr.py`, `exp/make_fwt.py`). 쪽수 96.3 → 96.6%(d193) | `unbounded-float-table-*` |
| d087 | 칸 안 분할에서 마지막 가시 줄이 본문 아래로 넘칠 수 있는 양은 그 줄의 줄 간격까지다(한/글 마지막 줄 규칙). 엔진의 `visible_tail_fits_before_spacer` 는 단위 높이 전체를 허용해 171px 그림 줄을 135px 넘쳐 담았다(1x1 CELL 표, 한/글은 그 그림부터 다음 쪽). 쪽수 96.6 → 96.9% | `tail-overfill-spacing-*` |
| d309, 회귀 HWP5 셋 | 중첩 표가 든 칸의 높이에도 위아래 배치(문단 기준) 그림, 도형의 바닥을 넣는다(d309 행 3: 한/글 PDF 괘선 593.0px = 줄 끝 27569 + 그림 16672 + 여백 282, 엔진 384.7px). 줄 배치 없는 칸(합산 분기)은 개체 흐름 높이를 더하고 빈 앵커 문단 줄과의 겹침을 뺀다. 쪽수 96.9 → 97.2%. 회귀 코퍼스에서 바뀐 HWP5 셋을 한/글로 열어 보니 쪽수, 쪽 첫 글 모두 같다(전에는 하나 6 대 7) | `nested-cell-flow-pic-*` |
| d159, d201, d331 | 빈칸만 든 문단에 글자처럼 취급 표가 둘 이상이면 한/글은 글 없는 문단처럼 표 폭으로 줄을 나눈다(d159 p0: 줄 폭에 가까운 표 둘이 두 줄, 둘째 줄은 표 2 의 원래 위치 34 에서 시작). 엔진 줄 나눔은 표 폭을 세지 않아 한 줄에 겹쳤다. 줄바꿈 불일치 272 → 269, 쪽수 97.2 → 97.6% | `ws-multi-tac-*` |
| 정답본 | 100% 미만 비율 줄 간격 = round(줄 높이 x (비율 - 100)% / 4) x 4(0 에서 먼 쪽 반올림, 수백 줄 모두). 0% 는 간격 = -줄 높이(24줄). HWPX 문단 모양 32,618개에 줄 간격 요소 없는 것이 0개라 HWPX 의 0 은 명시값으로 본다. d201 p74(0%)가 1100 내려가던 것을 고쳐 쪽수 97.6 → 97.9% | `percent-below-100-*` |
| d194, 쪽번호시험 사본 실험 | CELL 표의 한 줄짜리(분할 불가) 행도 「위 여백 + 줄들(마지막 줄 간격 빼고) + 아래 여백」이 쪽 끝 남은 자리에 들어가면 한/글은 그 행을 이 쪽에 본문 바닥까지 잘라 담고 다음 행부터 넘긴다. 32px 행(여백 142, 줄 1000)이 남은 17.42px 에서 담기고 17.1px 에서 넘어간다(= 1284 HWPUNIT, 세로 정렬과 선언 행 높이 무관, `exp/make_rowfit2.py`, `exp/make_rowfit3.py`). 쪽수 97.9 → 98.2%. 회귀 코퍼스에서 바뀐 6개 가운데 스킬이 만든 더미 줄 배치 문서는 저장 줄로 그리면 원래 위치가 틀려 줄 배치를 지우고 대조했다(넷 모두 같거나 나음, 나머지 둘은 전후 같음) | `row-visible-fit-*` |

## 남은 것 (2026-10-18)

- 좁은 칸에서 한/글이 문단 여백을 무시하는 경우(d034: 칸 2447, 여백 500+200, 한/글 horzpos 0)
- 한/글 줄 폭이 칸 폭보다 큰 경우(d010 칸 45: horzsize 44601 > 칸 45038 − 여백)
- Word 호환 문서 줄 높이는 넣었다(위 표 d076, d133). 고정, 최소 줄 간격과 줄 안에서 크기가 다른 글 run 이 섞인 경우는 정답본에 없어
  실측하지 않았다. 문단 모양 `fontLineHeight="1"` 도 함초롬바탕에서 1.3
- d266(13 대 14쪽): p19 CELL 표(17행, 63010)를 한/글은 3쪽 끝에서 행 안을 갈라 넘기고 rhwp 는 13행 경계에서 나눈다(아래 CELL 표 항목과 같은 결함)
- `!` 뒤에 한/글이 PDF 에 찍는 빈칸은 글자 위치 비교(advances, pdfadv)에서 빈칸으로 잡힌다
- 쪽수 지표 93.6%, 문단 쪽 96.4%(네이티브 6726/6976, wasm 96.4%), 불일치 줄 327. 남은 쪽수 불일치 21개 문서.
- d302/d314 본문 p100, p229(글머리표 문단, condense=20): 한/글 첫 줄 글 폭 46,356 이 줄 폭 46,988 에서 글머리표 자리 1,650 을 빼면
  넘치는데 담는다. 빈칸 9개를 20% 줄이면(1,260) 들어가니 「낱말 가운데서 글자 단위로 꺾을 때도 빈칸 줄이기를 쓴다」로 보이나 엔진 내부
  수치를 아직 못 뽑았다. 칸 249(글머리표 크기 0, bullet-zero-size 뒤 새로 틀림)도 한/글 줄 폭으로 역산하면 자리가 434~568 이어야
  하는데 규칙상 900 이라 칸 글자 폭(장평 96%, 자간 −15%) 계산부터 확인할 것
- 번호 폭(e29)은 넣었다. 번호 값은 줄 나눔 단계에 계수기가 없어 시작 번호로 잰다(두 자리 번호 문단만 다를 수 있다).
  글머리표 문단 첫 줄 불일치 14건(자동 내어쓰기 끈 글머리표 포함)은 아직
- d124(TABLE 표 행을 칸 안에서 가름)는 `table-whole-rows` 로 해결. 반대로 CELL 표(엔진 RowBreak)는 rhwp 가 행 경계에서만 나누는데
  한/글은 행 안에서도 가른다(81건). 파서 대응을 통째로 뒤집으면 쪽수가 91.4% 로 떨어졌으니, RowBreak 경로에 행 안 분할을 따로 넣어야 한다
  - d243(한/글 2쪽, rhwp 3쪽, CELL 표). 한/글 PDF 와 rhwp SVG 를 맞대 본 결과(2026-10-18):
    - 머리 0, 1행 높이는 둘 다 늘어난다(괘선 47.4pt 대 47.8pt). 앞서 적은 「한/글은 늘리지 않는다」는 틀렸다 — cellSz 는 사용자 최솟값이라
      한/글이 실제 행 높이로 다시 적지 않는다(282 로 남은 칸들). 정답본 cellSz 로 행 높이를 재는 집계(`harvest_cellmargin.py`,
      `harvest_overflow.py` 의 「행이 작음」, `rowcmp.py` 의 한글 열)는 그래서 믿을 수 없다. 행 높이는 PDF 괘선으로 잰다
    - 1쪽 끝: 한/글은 2행 첫째, 둘째 칸에서 줄 하나(기준선 744pt)를 더 담고 조각 바닥이 753.6pt, rhwp 는 751.1pt. 판정 차이 0.3pt 안팎
      (마지막 줄 뒤 줄 간격을 넣는지로 보이나 확정 못 함)
    - 🔴 그리기 결함: 2~5행에 걸친 셋째 칸(rowSpan 4)을 rhwp 는 1쪽에서 자르지 않고 쪽 아래로 822pt 까지 넘쳐 그린 뒤 2쪽에 처음부터 다시
      그린다. 한/글은 이 칸도 줄 단위로 갈라 1쪽 750pt 까지 담고 2쪽에서 이어 간다(「는다.」 158pt). 지표에는 안 잡히지만 꼬리말과 겹칠 수 있다
  - `harvest_cellmargin.py`: hasMargin=0 칸은 위아래에 표 안쪽 여백을 쓴다(372건, 칸 값 14건 — rhwp 와 같음)
- e28: 맑은 고딕 진하게는 자간(0, −5, −9%)이 있어도 보통 폭과 같다(bold-regular 규칙 확인)
- 글자 겹치기(compose) 폭(e27)을 엔진에 넣지 못했다. 줄 나눔이 개체 폭을 받는 `flow_inline_controls` 에 스타일이 없어, 겹친 글자의
  글꼴 폭을 재려면 호출부 세 곳을 함께 바꿔야 한다. 불일치 18줄(d073, d113, d127, d144, d145 의 동그라미 글머리 칸)
- 글 없이 개체만 든 줄의 줄 간격 기준 글자 크기(d126 p0: 개체 run 18pt 를 써야 하는데 줄 시작 run 11pt)는 고쳐도 조판의 합성 vpos 스냅이 되돌려 지표가 안 움직였다. 스냅을 함께 봐야 한다 쪽 끝 표 배치, 표 행 높이(d201 의 41행 표),
  (글자처럼 취급 표 둘이 든 문단을 한 줄에 겹쳐 놓던 d159 는 `ws-multi-tac` 로 해결) 등
- ⚠ `pagediff.py` 의 한/글 쪽은 vertpos 되감김으로 센다. 쪽을 넘는 큰 표 뒤 문단은 새 쪽 기준 vertpos 라 되감김이 안 보여
  한/글 쪽을 한 쪽 적게 센다(d201 p9). 쪽 나눔(pageBreak=1) 문단도 앞 문단이 vertpos 0 이면 못 센다(d347, d309)
- 합성 줄 vpos 로 누적 높이를 되맞추는 스냅(vpos_snap_current_height)을 끄면 문단 쪽은 6개 늘지만 쪽수 지표가 0.3%p 떨어져 넣지 않았다.
  스냅이 틀린 것이 아니라 합성 vpos 에 문단 간격이 빠져 있던 것이었다(synth-vpos-spacing 으로 해결)
- 「35,000*8차시*4학급」 처럼 기호가 낀 덩어리 안의 숫자|한글은 한/글도 꺾지 않는다(d007). ㎡ 앞 꺾기(4곳)는 아직

## 진단 도구 (2026-10-18 추가)

- `pagediff.py <id>`: 쪽이 처음 어긋나는 본문 문단과 앞뒤
- `curhdiff.py <id> [시작] [개수]`: 한/글 vertpos 와 rhwp 조판 누적 높이(cur_h)를 문단마다 맞댄다. 표 뒤에서도 흔들리지 않는다
- `vydiff.py <id> [시작] [개수]`: 문단 사이 간격(한/글 vertpos 대 rhwp 커서 y)
- `mmstat.py <불일치.jsonl>`: 불일치를 방향(먼저, 늦게 꺾음)과 글꼴로 묶는다
- `harvest_spacing.py`, `harvest_lineheight.py`: 정답본 줄 기록에서 줄 간격, 줄 높이 배율을 모은다
- `headstat.py <불일치.jsonl> [--list NUMBER]`: 불일치를 문단 머리 종류(번호, 글머리표)와 어긋난 줄(첫 줄, 이후)로 묶는다
- `showmm.py <불일치.jsonl> <id> [본문|칸] [칸] [문단]`: 불일치 줄을 한/글과 rhwp 줄 나눔으로 펼쳐 글로 보인다(조판 부호 ¤)
- `linecheck.py` 에 `LINECHECK_ALL=1`: 모든 줄의 계산 폭과 줄 폭을 찍는다
- `harvest_overflow.py`, `harvest_cellmargin.py`: 칸 내용 대 행 높이 집계. ⚠ cellSz 를 행 높이로 쓰므로 판정은 참고만
- `harvest_tblsplit.py [--list]`: 쪽을 넘는 표가 한/글에서 행 경계로 나뉘었는지(첫 조각 높이 = 행 높이 누적합) pageBreak 별로 센다
- `harvest_tblnext.py`: 표만 담은 문단에서 한/글이 문단 아래 간격을 더하는지 정답본으로 센다
- `secpr_engine.py`: 구역 정의 run 으로 시작하는 첫 문단 셋의 첫 줄 높이/간격을 엔진과 한/글로 맞대고 어긋난 문단의 run 구성을 찍는다
- `harvest_tacstep.py`, `harvest_emptyruns.py`: 표만 든 문단의 한/글 전진량, 빈 문단의 줄 높이 기준 run
- 엔진 임시 진단(넣고 빼기, `exp/instr_adv.py`, `exp/instr_ch.py`, `exp/instr_units.py`: `<백업 경로>` 로 넣고 `<백업 경로> restore` 로 되돌린다): 쪽 넘김 호출 스택(`advance_column_or_new_page` 에 Backtrace), 누적 높이 대입마다 출력, 칸 단위 높이(`advance_row_cut_inner` 의 units). 진단 출력 `RHWP_DIAG_SCAN`, `RHWP_DIAG_SPLITSCAN`, `RHWP_TABLE_DRIFT`, `RHWP_DIAG_TAC`, `RHWP_FLOW_DBG`
- `exp/`: 한/글 실험 변형 생성기(오라클이나 회귀 사본을 고쳐 `in/` 에 둔다) → `REA/hwp2024/hwpx_lab/measure.py`(HWP5 는 `exp/measure_hwp.py`)를 `~/.claude/references/hidden_desktop.py` 로 돌려 PDF 를 얻는다. `exp/copy_reg.py`(회귀 코퍼스 사본과 줄 배치 지운 사본), `exp/svgpdf.mjs`(claude-linestarts `CLAUDE_SVG` 쪽 SVG 를 한/글 PDF 와 쪽 첫 글로 대조), `exp/pagecmp_hwp.mjs`(HWP5 판 pagecmp)
- `nativescore.py` 에 `NATIVE_PP=1`: 문단 쪽이 어긋난 문서와 개수를 찍는다
- `segcmp.py <id>`: 첫 구역 본문 문단 줄마다 한/글 줄 기록(높이/간격)과 엔진 값을 맞댄다
- `pagecmp.mjs <id>`: 쪽마다 첫 글자를 한/글 PDF(`../out/lab/hanpdf/rt/<id>.pdf`)와 rhwp SVG 로 맞대 처음 갈리는 쪽을 찾는다
- `linecmp.mjs <id> <쪽>`: 한 쪽의 글줄 세로 위치를 한/글 PDF 와 rhwp 로 나란히 찍고 차이가 바뀌는 줄을 표시한다
- `claude-linestarts` 환경 변수: `CLAUDE_SEGV`(엔진이 가진 본문 문단 줄 배치 vpos), `CLAUDE_VY`(문단 y), `CLAUDE_XP=<문단|all>`(글자 x), `CLAUDE_ITEMS`(쪽 항목), `CLAUDE_SVG=<폴더>`(쪽 SVG), `CLAUDE_METRICS_DIR`(문서별 폭 표, `dump_metrics.mjs` 로 만든다)
