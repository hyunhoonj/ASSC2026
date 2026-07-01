# ASSC 29 — 세션 메모 컴패니언 🧠

**29th Annual Meeting of the ASSC** · Santiago de Chile (PUC Casa Central) · **June 30 – July 3, 2026**

참석하는 세션마다 HTML 페이지를 만들고 메모를 쌓는 개인 노트 저장소예요.
폰이든 PC든 [claude.ai/code](https://claude.ai/code)에서 이 repo를 열고 Claude에게 말하면 페이지 생성·메모가 됩니다. git이 동기화를 담당해요.

## 쓰는 법
**폰에서 (노트북 꺼져 있어도):** claude.ai/code → 이 저장소 선택 → 이렇게 말하기
> "Day 2 Symposium 2 페이지 만들어줘"
> "방금 Keynote 3 좋았어. 메모 추가해줘: predictive processing으로 각성 상태를 설명 … 질문은 마취 데이터로 검증했는지"

**PC에서:** 터미널에서 Claude Code로 똑같이. 또는 직접:
```bash
python3 tools/generate.py session "day2 symposium 2"   # 세션 페이지 생성
python3 tools/generate.py list                          # 세션 id 목록
open index.html                                         # 브라우저로 열기(로컬)
```
메모는 각 페이지의 `내 메모 / 발표·초록 / 질문 / 팔로업` 칸에 들어가고, 페이지를 다시 만들어도 **메모는 보존**돼요.

## 구조
```
index.html            홈 — 4일 개요
Day1_Jun30_Tue/ …     Day 인덱스 + 그 날 세션 페이지들
data/program.json     전체 프로그램 데이터(56세션·발표 112개) ← 페이지의 근거
data/source/          공식 프로그램 PDF + 추출 텍스트(포스터 전체 목록 등)
assets/style.css      공통 스타일
tools/generate.py     페이지 생성기
CLAUDE.md             Claude Code 작업 규칙 (메모 보존 규칙 포함)
```

## Day별 프로그램 한눈에
| Day | 주요 세션 |
|---|---|
| **화 6/30** | Tutorial 1–4 · Opening · **Keynote 1** Melloni · **Presidential** Nobre |
| **수 7/1** | **Symp 1–2** · **Keynote 2** Mac Shine · Poster 1 · **Concurrent 1–16** |
| **목 7/2** | **Symp 3–6** · **Keynote 3** Bekinschtein · **Keynote 4** Kuypers · Career Panel · Poster 2 |
| **금 7/3** | **Symp 7–8** · **Keynote 5** De Brigard · **Concurrent 17–28** · Poster 3 · Closing |

전체 세션·발표자·발표목록은 `index.html`을 열거나 `python3 tools/generate.py list`로 확인하세요.

## 참고 — HTML을 브라우저에서 예쁘게 보려면
- GitHub 웹에서 `.html`은 소스로 보여요(렌더링 X). 예쁘게 보려면 (a) 로컬에서 파일 열기, 또는 (b) **GitHub Pages** 활성화(공개 repo는 무료 / 비공개는 Pro 필요).
- 메모 작성·열람은 대부분 Claude Code로 하므로 Pages 없이도 충분해요. Pages가 필요하면 요청하세요.

_Wi-Fi: `UC_CentroExtension` / `uc.20251` — 원본: <https://theassc.org/assc-29/>_
