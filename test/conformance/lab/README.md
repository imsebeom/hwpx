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

## 남은 것 (2026-10-18)

- 좁은 칸에서 한/글이 문단 여백을 무시하는 경우(d034: 칸 2447, 여백 500+200, 한/글 horzpos 0)
- 한/글 줄 폭이 칸 폭보다 큰 경우(d010 칸 45: horzsize 44601 > 칸 45038 − 여백)
- Word 호환 문서(`compatibleDocument targetProgram="MS_WORD"`, `adjustLineheightToFont`)는 줄 높이가 글꼴 세로 지표 × 1.3 이다
  (Pretendard 1.1934 → 1.551, 맑은 고딕 1.3301 → 1.73). 정답본 2개(d076, d133)뿐이라 미뤘다. 문단 모양 `fontLineHeight="1"` 도 함초롬바탕에서 1.3
- `!` 뒤에 한/글이 PDF 에 찍는 빈칸은 글자 위치 비교(advances, pdfadv)에서 빈칸으로 잡힌다
- 쪽수 지표 93.6%, 문단 쪽 96.4%(네이티브 6726/6976, wasm 96.4%), 불일치 줄 338. 남은 쪽수 불일치 21개 문서.
- 번호 폭(e29)은 넣었다. 번호 값은 줄 나눔 단계에 계수기가 없어 시작 번호로 잰다(두 자리 번호 문단만 다를 수 있다).
  글머리표 문단 첫 줄 불일치 14건(자동 내어쓰기 끈 글머리표 포함)은 아직
- d124(TABLE 표 행을 칸 안에서 가름)는 `table-whole-rows` 로 해결. 반대로 CELL 표(엔진 RowBreak)는 rhwp 가 행 경계에서만 나누는데
  한/글은 행 안에서도 가른다(81건). 파서 대응을 통째로 뒤집으면 쪽수가 91.4% 로 떨어졌으니, RowBreak 경로에 행 안 분할을 따로 넣어야 한다
  - 정정: rhwp 도 CELL 표를 행 안에서 자르는 경우가 있다(d243). d243(한/글 2쪽, rhwp 3쪽)은 나눔 종류가 아니라 행 높이 문제다.
    2행에 걸친 칸(0,0)의 내용 끝 4,130 + 표 안쪽 여백 566 = 4,696 이 선언 4,530 을 넘어 rhwp 는 1행을 2,298 → 2,464 로 늘리는데,
    한/글은 늘리지 않는다. 그 166 때문에 첫 쪽에 2행을 한 줄 덜 담고, 둘째 쪽 마지막 행이 1.2px 모자라 셋째 쪽이 생긴다
  - `harvest_cellmargin.py`: hasMargin=0 칸은 위아래에 표 안쪽 여백을 쓴다(372건, 칸 값 14건 — rhwp 와 같음). 그런데 내용 + 여백이
    행보다 큰데도 한/글이 행을 늘리지 않은 칸이 수백 건 있다(−1,000, −265 등). 한/글이 칸 내용의 어디까지를 행 높이에 넣는지가 다음 과제
- e28: 맑은 고딕 진하게는 자간(0, −5, −9%)이 있어도 보통 폭과 같다(bold-regular 규칙 확인)
- 글자 겹치기(compose) 폭(e27)을 엔진에 넣지 못했다. 줄 나눔이 개체 폭을 받는 `flow_inline_controls` 에 스타일이 없어, 겹친 글자의
  글꼴 폭을 재려면 호출부 세 곳을 함께 바꿔야 한다. 불일치 18줄(d073, d113, d127, d144, d145 의 동그라미 글머리 칸)
- 글 없이 개체만 든 줄의 줄 간격 기준 글자 크기(d126 p0: 개체 run 18pt 를 써야 하는데 줄 시작 run 11pt)는 고쳐도 조판의 합성 vpos 스냅이 되돌려 지표가 안 움직였다. 스냅을 함께 봐야 한다 쪽 끝 표 배치, 표 행 높이(d201 의 41행 표),
  글자처럼 취급 표 둘이 든 문단을 한 줄에 겹쳐 놓는 문제(d159) 등
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
- `harvest_tblsplit.py [--list]`: 쪽을 넘는 표가 한/글에서 행 경계로 나뉘었는지(첫 조각 높이 = 행 높이 누적합) pageBreak 별로 센다
- `harvest_tblnext.py`: 표만 담은 문단에서 한/글이 문단 아래 간격을 더하는지 정답본으로 센다
- `claude-linestarts` 환경 변수: `CLAUDE_SEGV`(엔진이 가진 본문 문단 줄 배치 vpos), `CLAUDE_VY`(문단 y), `CLAUDE_XP=<문단|all>`(글자 x), `CLAUDE_ITEMS`(쪽 항목), `CLAUDE_SVG=<폴더>`(쪽 SVG), `CLAUDE_METRICS_DIR`(문서별 폭 표, `dump_metrics.mjs` 로 만든다)
