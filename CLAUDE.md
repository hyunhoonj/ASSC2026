# ASSC 29 노트 컴패니언 — 작업 방식 (Claude Code용)

이 저장소는 **ASSC 29 학회(산티아고, 2026-06-30 ~ 07-03) 세션 메모장**이다.
목표: 참석한 세션마다 HTML 페이지를 만들고 거기에 메모를 쌓는다. 폰(claude.ai/code)과 PC 양쪽에서 편집하며 git으로 동기화한다.

본 학회 직후 열리는 **부속(위성) 워크숍 — Neurophenomenology Satellite Meeting (7/4~5)** 도 같은 방식으로 포함되어 있다.
`day: sat1`(토, 7/4) · `sat2`(일, 7/5), 세션 id는 `sat1-key-1`, `sat2-sym` 처럼 `sat` 접두. 홈 화면 아래쪽 "🛰 부속 워크숍" 카드로 연결된다.
참조 예: `python3 tools/generate.py session "satellite keynote 3"` 또는 id `sat2-key-3`. 나머지(메모·재생성·보존)는 본 학회와 100% 동일.

## 데이터 원천 (신뢰의 근거)
- **`data/program.json`** — 모든 세션의 제목·시간·룸·발표자·발표목록. **페이지 생성의 유일한 소스.**
- **`data/source/fullprogram.txt`** — 공식 프로그램 PDF에서 뽑은 원문. 포스터 개별 목록(P1/P2/P3), 그리고 program.json에 없는 세부는 여기서 찾는다. (원본 PDF도 `data/source/`에 있음)
- 사실을 **지어내지 말 것.** program.json / fullprogram.txt에 없으면 "프로그램에 없음"이라고 표시하고, 사용자가 주는 정보로 채운다.

## 세션 페이지 만들기 / 새로고침 — 명령 하나
```bash
python3 tools/generate.py session "<참조>"      # 예: "day2 symposium 2", "day2 session 6", "keynote 3", "day4 poster 3"
python3 tools/generate.py session d2-cs-6        # 세션 id로도 가능 (가장 정확)
python3 tools/generate.py list                   # 전체 id/slug/제목 보기
python3 tools/generate.py index                  # 홈 + Day 인덱스만 다시 빌드
python3 tools/generate.py all                    # 홈 + 모든 Day + 모든 세션 페이지
```
- 페이지는 `Day?_*/{slug}.html`에 생성되고, 해당 Day 인덱스 링크가 자동으로 "✓ 메모"로 바뀐다.
- 참조 표기는 program.json의 `id`가 가장 안전하다. 애매하면 `list`로 확인.

## ⚠️ 메모 보존 규칙 (반드시 지킬 것)
- 세션 페이지의 메모는 다음 마커 **사이**에 있다:
  `<!-- NOTES:mynotes:START -->` … `<!-- NOTES:mynotes:END -->` (키: `abstract`, `mynotes`, `questions`, `followups`)
- **기존 메모는 절대 삭제·요약·재작성하지 않는다.** 추가만 한다.
- `generate.py`로 페이지를 다시 만들어도 이 마커 사이 내용은 **그대로 보존**된다 (메타데이터만 갱신). 안심하고 재생성해도 된다.

## 메모 추가하는 법
사용자가 "Day 2 Symposium 2에 메모: …" 라고 하면:
1. 페이지가 없으면 먼저 `python3 tools/generate.py session "day2 symposium 2"`로 만든다.
2. 해당 `.html`을 열어 알맞은 NOTES 블록(보통 `mynotes`) **안의 기존 내용 아래에** 메모를 덧붙인다. 빈 페이지면 `<p class="empty">…</p>` 자리를 실제 메모로 교체.
   - 형식은 자유롭게 (`<ul><li>…</li></ul>`, `<p>…</p>`). 발표 요약은 `abstract`, 질문은 `questions`, 후속은 `followups` 블록으로.
3. 저장 → 커밋 → push.

## ⚓ 발표 목록 → 메모 앵커 이동 (매번 반드시!)
`talks`가 있는 세션(Contributed Talks, Concurrent 등)은 상단 "발표 목록" 카드의 각 제목이
`<a href="#note-N">`(N = 발표 순서, 1부터)로 링크된다. 따라서 발표별 요약을 `abstract` 블록에
쓸 때는 **각 발표 소제목에 `id="note-N"`를 반드시 붙여야** 제목 클릭 시 해당 영역으로 이동한다.
```html
<h3 id="note-1">① 발표자 — 제목</h3> … <h3 id="note-2">② …</h3> …
```
- 규칙: 상단 카드의 `#note-N` 개수 = abstract의 `id="note-N"` 개수(발표 수와 일치). 하나라도 빠지면 그 제목은 클릭해도 안 넘어감.
- 확인: `grep -oE 'href="#note-[0-9]+"' <page>` 와 `grep -oE 'id="note-[0-9]+"' <page>` 개수가 같아야 함.
- (이 앵커는 abstract 블록 안에 있으므로 재생성해도 보존된다.)

## 🎙 녹음 전사 (OpenAI 음성 인식)
세션 녹음을 텍스트로 옮길 때 `tools/transcribe.py`를 쓴다 (OpenAI `gpt-4o-transcribe`). 표준 라이브러리만 사용 — 추가 설치 불필요.

**API 키** (아래 순서로 찾음, git에는 절대 안 올라감):
1. 환경변수 `OPENAI_API_KEY` ← **권장.** 폰(claude.ai/code)은 환경(Environment) 설정에 시크릿으로, PC는 셸 프로필에 `export OPENAI_API_KEY=sk-...`
2. 파일 `.secrets/openai_api_key` (`.gitignore`에 포함됨 — 이 저장소 로컬 전용, 기기마다 따로 둬야 함)

```bash
python3 tools/transcribe.py --check                              # 키·연결 점검
python3 tools/transcribe.py rec.m4a                              # 전사만 (화면 출력)
python3 tools/transcribe.py rec.m4a -o rec.txt                   # .txt 로 저장
python3 tools/transcribe.py rec.m4a --session "day2 symposium 2" # 세션 페이지 abstract에 삽입
python3 tools/transcribe.py talk.m4a --session d3-ct-1 --note 2  # N번째 발표 아래 앵커(id="note-N")로 삽입
```
- 주요 옵션: `--block abstract|mynotes|questions|followups`(기본 abstract), `--language en|ko`, `--prompt "ASSC, IIT, GNWT"`(용어 힌트), `--model gpt-4o-transcribe|gpt-4o-mini-transcribe|whisper-1`.
- `--prompt`는 **문장("keynote by 홍길동")보다 용어 나열**("neurophenomenology, embodiment, affect …")이 안전하다. 문장을 넣으면 도입부 정적에서 whisper가 그 문구를 되뇌는 환각이 날 수 있는데, 이 경우 도구가 **자동 감지해 프롬프트 없이 한 번 재전사**한다.
- **삽입은 항상 "추가"만** 한다 — 기존 메모 보존 규칙 그대로. 빈 블록이면 자리표시자만 치우고 넣는다.
- `--note N`을 쓰면 발표 앵커 규칙(위 ⚓ 섹션)에 맞춰 처리한다: `id="note-N"`이 **이미 있으면**(사전조사 메모 등) 중복 id 없이 그 발표 섹션 **바로 아래**에, 없으면 새 `id="note-N"`을 붙여 넣는다.
- **녹음 원본(mp3/m4a/wav…)은 커밋하지 않는다** (`.gitignore` 처리됨). 전사 텍스트만 페이지에 남긴다.
- **긴 녹음·큰 파일은 자동 처리** — 모델을 신경 쓸 필요 없다:
  - `gpt-4o-transcribe` 계열은 1회 최대 약 23분(1400초), `whisper-1`은 길이 제한 없음. 공통 업로드 한도 25MB.
  - `ffmpeg`가 있으면 15분 조각으로 분할해 고른 모델 그대로 전사·이어붙임. 없으면 길이만 초과한 경우(25MB 이하) **자동으로 `whisper-1`로 전환**해 한 번에 전사한다.
  - 용량이 25MB를 넘고 ffmpeg도 없으면 직접 압축 안내(`ffmpeg -i in.m4a -ac 1 -b:a 32k out.mp3`) 후 멈춘다.

## 포스터 개별 페이지가 필요하면
`data/source/fullprogram.txt`의 `POSTER SESSION 1/2/3`에서 해당 포스터(예: P1-050)의 제목·발표자를 찾아 페이지/메모에 넣는다.

## 심포지엄 내부 연사
Symposium 1–8의 개별 연사는 프로그램 PDF에 없다. 현장 프로그램/사용자 입력으로 채우고, program.json의 해당 세션 `speakers`에 넣은 뒤 재생성하면 반영된다.

## git 흐름 (폰·PC 충돌 방지)
```bash
git pull --rebase        # 편집 전에 항상 먼저 (다른 기기에서 한 메모 받아오기)
# …편집…
git add -A && git commit -m "notes: Day2 Symposium 2 메모 추가"
git push
```
- 커밋 메시지: `notes: …`(메모), `page: …`(새 세션 페이지), `data: …`(program.json 수정).

## 스타일
공통 CSS는 `assets/style.css` 하나. 개별 페이지에 인라인 스타일을 넣지 말 것 — 스타일 변경은 이 파일만 고친다.
