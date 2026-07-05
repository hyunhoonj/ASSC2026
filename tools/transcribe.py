#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASSC 29 노트 컴패니언 — 녹음 전사 (OpenAI Speech-to-Text).

세션 녹음 파일을 OpenAI 음성 인식으로 전사하고, 원하면 그 결과를
세션 페이지의 메모 블록(기본: 📄 발표·초록 메모)에 바로 붙여 넣는다.
기존 메모는 절대 건드리지 않고 "추가"만 한다 (CLAUDE.md 규칙 준수).

의존성 없음 — 파이썬 표준 라이브러리(urllib)만 사용. `openai`/`requests` 불필요.

■ API 키 (아래 순서로 찾음)
  1) 환경변수  OPENAI_API_KEY          ← 권장 (기기마다 durable)
     · 폰(claude.ai/code): 환경(Environment) 설정에서 시크릿으로 추가
     · PC: 셸 프로필에  export OPENAI_API_KEY=sk-...
  2) 파일  .secrets/openai_api_key     ← 이 저장소 로컬 (git 무시됨, 커밋 안 됨)
  3) 파일  ~/.openai_api_key

■ 사용법
  python3 tools/transcribe.py <오디오파일> [옵션]

  옵션:
    --session <참조>   전사 결과를 해당 세션 페이지 메모에 삽입
                       (참조 = generate.py와 동일: "day2 symposium 2", "d2-sym-2" 등)
    --block <키>       삽입할 메모 블록 (abstract|mynotes|questions|followups, 기본 abstract)
    --note <N>         N번째 발표 아래에 삽입. id="note-N" 앵커가 이미 있으면(사전조사 메모 등)
                       중복 없이 그 발표 섹션 바로 아래에, 없으면 새로 앵커를 붙여 넣는다.
    --model <이름>     기본 gpt-4o-transcribe (대안: gpt-4o-mini-transcribe, whisper-1)
    --language <코드>  예: en, ko (생략 시 자동 감지)
    --prompt <텍스트>  전문 용어/이름 힌트 (예: "ASSC, IIT, GNWT, phenomenology")
    -o, --out <파일>   전사 텍스트를 .txt 로 저장
    --check            키·연결만 점검하고 종료 (오디오 불필요)

  예:
    python3 tools/transcribe.py --check
    python3 tools/transcribe.py recordings/sym2.m4a
    python3 tools/transcribe.py recordings/sym2.m4a --session "day2 symposium 2"
    python3 tools/transcribe.py talk.m4a --session d3-ct-1 --note 2 --language en

■ 긴 녹음 / 큰 파일 — 자동 처리
  · gpt-4o-transcribe 계열은 1회 최대 약 23분(1400초). whisper-1은 길이 제한 없음.
  · 업로드 한도는 공통 25MB.
  모델·길이·용량에 따라 알아서 처리한다:
    - ffmpeg 있음  → 조각(15분)으로 분할해 고른 모델 그대로 전사 후 이어붙임
    - ffmpeg 없음  → 길이만 초과(25MB 이하)면 whisper-1로 자동 전환해 한 번에 전사
                     용량이 25MB를 넘으면 압축 방법을 안내하고 멈춤
  길이를 미리 못 재도(ffprobe 없음), gpt-4o가 길이 초과로 실패하면 그때 자동 폴백한다.
  (ffmpeg가 있으면 ffprobe도 대개 함께 있어 미리 판단한다.)
"""
import json, os, re, sys, html, subprocess, tempfile, shutil, uuid, mimetypes
import urllib.request, urllib.error
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate  # 세션 해석·페이지 생성 재사용

API_URL = "https://api.openai.com/v1/audio/transcriptions"
MODELS_URL = "https://api.openai.com/v1/models"
SIZE_LIMIT = 24 * 1024 * 1024          # 24MB (한도 25MB보다 살짝 아래)
CHUNK_SECONDS = 15 * 60                 # ffmpeg 분할 길이 (900초 < gpt-4o 1400초 한도)
GPT4O_MAX_SECONDS = 1400                # gpt-4o-transcribe 계열의 1회 최대 길이(약 23분)
OK_EXT = {".flac",".m4a",".mp3",".mp4",".mpeg",".mpga",".oga",".ogg",".wav",".webm",".aac"}

class ApiError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__("HTTP %s: %s" % (status, message))

def is_duration_error(e):
    """gpt-4o 계열의 '길이 초과' 400 에러인지."""
    return (isinstance(e, ApiError) and e.status == 400
            and "longer than" in (e.message or "") and "second" in (e.message or "").lower())

# ---------------- API 키 ----------------
def find_key():
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if k: return k
    for p in (os.path.join(ROOT, ".secrets", "openai_api_key"),
              os.path.expanduser("~/.openai_api_key")):
        if os.path.exists(p):
            k = open(p, encoding="utf-8").read().strip()
            if k: return k
    sys.exit("✗ OpenAI API 키를 찾을 수 없습니다.\n"
             "  환경변수 OPENAI_API_KEY 를 설정하거나 .secrets/openai_api_key 파일을 두세요.")

# ---------------- HTTP ----------------
def _multipart(fields, filename, filebytes, file_field="file"):
    boundary = "----assc29-" + uuid.uuid4().hex
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    body = bytearray()
    for k, v in fields.items():
        if v is None: continue
        body += ("--%s\r\n" % boundary).encode()
        body += ('Content-Disposition: form-data; name="%s"\r\n\r\n' % k).encode()
        body += ("%s\r\n" % v).encode()
    body += ("--%s\r\n" % boundary).encode()
    body += ('Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
             % (file_field, os.path.basename(filename))).encode()
    body += ("Content-Type: %s\r\n\r\n" % ctype).encode()
    body += filebytes + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode()
    return "multipart/form-data; boundary=%s" % boundary, bytes(body)

def _request(url, key, method="GET", data=None, ctype=None):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + key)
    if ctype: req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        try: detail = json.loads(detail)["error"]["message"]
        except Exception: pass
        raise ApiError(e.code, detail)
    except urllib.error.URLError as e:
        raise ApiError(None, "네트워크 오류: %s" % e.reason)

def check():
    key = find_key()
    print("· 키 확인: OK (prefix %s…, len %d)" % (key[:7], len(key)))
    out = _request(MODELS_URL, key)
    ids = {m["id"] for m in json.loads(out).get("data", [])}
    print("· OpenAI 연결: OK (%d개 모델 접근 가능)" % len(ids))
    for m in ("gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"):
        print("   %s %s" % ("✓" if m in ids else "·", m))
    print("준비 완료. `python3 tools/transcribe.py <오디오파일>` 로 전사하세요.")

# ---------------- 전사 ----------------
def transcribe_bytes(key, filename, data, model, language, prompt):
    fields = {"model": model, "response_format": "text"}
    if language: fields["language"] = language
    if prompt:   fields["prompt"] = prompt
    ctype, body = _multipart(fields, filename, data)
    return _request(API_URL, key, "POST", body, ctype).strip()

def looks_looped(text):
    """도입부 정적 등에서 whisper가 같은 어구를 연달아 반복하는 환각을 감지.
    2~6단어 창이 4번 이상 '연속' 반복되면 True (정상 발화에선 거의 없음)."""
    w = text.split()
    if len(w) < 12: return False
    for k in range(2, 7):
        best = run = 1
        i = 0
        while i + 2 * k <= len(w):
            if w[i:i+k] == w[i+k:i+2*k]:
                run += 1; i += k
            else:
                if run > best: best = run
                run = 1; i += 1
        if max(best, run) >= 4:
            return True
    return False

def _norm_words(s):
    return [w for w in (re.sub(r"[^\w-]", "", x.lower()) for x in s.split()) if w]

def prompt_echo(text, prompt, head_words=60, k=4):
    """도입부(앞부분)에 프롬프트의 여러 단어 어구가 그대로 튀어나오면 환각으로 본다.
    자연 발화가 프롬프트 문장을 4단어 연속 그대로 말할 일은 거의 없다."""
    if not prompt: return False
    pw, hw = _norm_words(prompt), _norm_words(text)[:head_words]
    if len(pw) < k or len(hw) < k: return False
    pgrams = {tuple(pw[i:i+k]) for i in range(len(pw)-k+1)}
    return any(tuple(hw[i:i+k]) in pgrams for i in range(len(hw)-k+1))

def is_hallucinated(text, prompt):
    return looks_looped(text) or prompt_echo(text, prompt)

def transcribe_clean(key, filename, data, model, language, prompt):
    """전사 후 반복/프롬프트-되뇌기 환각이 보이면 프롬프트 없이 한 번 재시도한다."""
    text = transcribe_bytes(key, filename, data, model, language, prompt)
    if prompt and is_hallucinated(text, prompt):
        print("   ⚠ 도입부 환각(반복/프롬프트 되뇌기) 감지 → 프롬프트 없이 재시도")
        retry = transcribe_bytes(key, filename, data, model, language, None)
        if not is_hallucinated(retry, None):
            return retry
        return retry if len(retry) >= len(text) else text  # 둘 다 이상하면 더 긴 쪽
    return text

def have_ffmpeg(): return shutil.which("ffmpeg") is not None

def ffprobe_duration(path):
    """오디오 길이(초)를 ffprobe로 측정. ffprobe 없거나 실패 시 None."""
    fp = shutil.which("ffprobe")
    if not fp: return None
    try:
        out = subprocess.run(
            [fp, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nokey=1:noprint_wrappers=1", path],
            capture_output=True, text=True, timeout=60)
        return float(out.stdout.strip())
    except Exception:
        return None

def split_with_ffmpeg(path):
    """큰 파일을 32k mono mp3 조각으로 압축·분할. (파일경로 리스트, 임시디렉토리) 반환."""
    ff = shutil.which("ffmpeg")
    if not ff:
        sys.exit("✗ 파일이 25MB를 넘고 ffmpeg가 없어 분할할 수 없습니다.\n"
                 "  방법 1) ffmpeg 설치 후 다시 실행\n"
                 "  방법 2) 직접 압축:  ffmpeg -i \"%s\" -ac 1 -b:a 32k out.mp3\n"
                 "  방법 3) 짧게 나눠서 각각 전사" % path)
    tmp = tempfile.mkdtemp(prefix="assc-transcribe-")
    pat = os.path.join(tmp, "chunk%03d.mp3")
    cmd = [ff, "-hide_banner", "-loglevel", "error", "-i", path,
           "-ac", "1", "-b:a", "32k", "-f", "segment",
           "-segment_time", str(CHUNK_SECONDS), pat]
    print("· ffmpeg로 압축·분할 중 (%d분 단위)…" % (CHUNK_SECONDS // 60))
    subprocess.run(cmd, check=True)
    parts = sorted(os.path.join(tmp, f) for f in os.listdir(tmp) if f.endswith(".mp3"))
    if not parts:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit("✗ ffmpeg 분할 실패 (조각 없음).")
    return parts, tmp

def _transcribe_split(key, path, model, language, prompt):
    """ffmpeg로 조각내어 조각마다 전사 후 이어붙인다 (모델 품질 유지)."""
    parts, tmp = split_with_ffmpeg(path)
    try:
        texts = []
        for i, p in enumerate(parts, 1):
            print("   조각 %d/%d 전사 중…" % (i, len(parts)))
            # 이전 조각 끝부분을 다음 prompt로 이어 문맥 유지
            carry = (texts[-1][-400:] if texts else "") or prompt
            texts.append(transcribe_clean(key, p, open(p, "rb").read(),
                                          model, language, carry or None))
        return "\n\n".join(t for t in texts if t)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def transcribe_file(path, model, language, prompt):
    if not os.path.exists(path):
        sys.exit("✗ 오디오 파일 없음: %s" % path)
    ext = os.path.splitext(path)[1].lower()
    if ext not in OK_EXT:
        print("⚠ 확장자 %s 는 검증되지 않았습니다. 지원: %s" % (ext, ", ".join(sorted(OK_EXT))))
    key = find_key()
    size = os.path.getsize(path)
    is_gpt4o = model.startswith("gpt-4o")
    dur = ffprobe_duration(path)
    print("· 파일: %s (%.1f MB%s), 모델: %s%s" %
          (os.path.basename(path), size/1024/1024,
           ", %.0f분" % (dur/60) if dur else "", model,
           ", 언어=%s" % language if language else ""))

    too_big  = size > SIZE_LIMIT
    too_long = is_gpt4o and dur is not None and dur > GPT4O_MAX_SECONDS

    # 1) 사전에 분할/전환이 필요한 경우 (용량 초과, 또는 gpt-4o 길이 초과가 미리 확인됨)
    if too_big or too_long:
        why = "25MB 초과" if too_big else "약 %.0f분 > gpt-4o 한도(약 23분)" % (dur/60)
        if have_ffmpeg():
            print("· %s → ffmpeg로 분할해 %s 로 전사" % (why, model))
            return _transcribe_split(key, path, model, language, prompt)
        if too_big:
            split_with_ffmpeg(path)  # ffmpeg 없음 → 안내 출력 후 종료
        # 길이만 초과(용량은 25MB 이하) & ffmpeg 없음 → whisper-1로 자동 전환
        print("· %s, ffmpeg 없음 → 길이 제한이 없는 whisper-1로 자동 전환" % why)
        return transcribe_clean(key, path, open(path, "rb").read(),
                                "whisper-1", language, prompt)

    # 2) 단발 전사. gpt-4o인데 길이를 몰랐다가 길이 초과로 실패하면 여기서 폴백.
    try:
        return transcribe_clean(key, path, open(path, "rb").read(),
                                model, language, prompt)
    except ApiError as e:
        if not is_duration_error(e):
            raise
        if have_ffmpeg():
            print("· 길이 초과 감지 → ffmpeg로 분할 후 %s 로 재전사" % model)
            return _transcribe_split(key, path, model, language, prompt)
        print("· 길이 초과 감지, ffmpeg 없음 → 길이 제한이 없는 whisper-1로 자동 전환")
        return transcribe_clean(key, path, open(path, "rb").read(),
                                "whisper-1", language, prompt)

# ---------------- 세션 페이지 삽입 ----------------
def to_html(text, filename, note_n=None, emit_id=True):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras: paras = [text.strip()]
    body = "\n      ".join("<p>%s</p>" % html.escape(" ".join(p.split()), quote=True)
                           for p in paras)
    hid = ' id="note-%d"' % note_n if (note_n and emit_id) else ""
    label = ("🎙 전사 — %s" % html.escape(filename, quote=True)) if not note_n else \
            ("🎙 전사 %d — %s" % (note_n, html.escape(filename, quote=True)))
    return ('\n      <div class="transcript">\n'
            '      <h3%s>%s <span class="aff">(%s · OpenAI)</span></h3>\n'
            '      %s\n'
            '      </div>\n    ' % (hid, label, stamp, body))

def insert_into_session(prog, ref, block_key, text, filename, note_n=None):
    s = generate.resolve(prog, ref)
    if not s:
        sys.exit("✗ 세션을 못 찾음: '%s'  (python3 tools/generate.py list 로 확인)" % ref)
    day = generate.day_of(prog, s["day"])
    path = os.path.join(ROOT, day["folder"], s["slug"] + ".html")
    if not os.path.exists(path):
        print("· 페이지가 없어 먼저 생성:", generate.build_session(prog, s))
    txt = open(path, encoding="utf-8").read()
    start, end = generate.note_markers(block_key)
    m = re.search(re.escape(start) + r"(.*?)" + re.escape(end), txt, re.S)
    if not m:
        sys.exit("✗ '%s' 블록을 찾을 수 없습니다 (키: abstract|mynotes|questions|followups)." % block_key)
    inner = m.group(1)

    # 이미 이 발표의 앵커(id="note-N")가 페이지에 있으면(사전조사 메모 등),
    # 중복 id를 만들지 않고 그 발표 섹션 바로 아래(= 다음 발표 앵커 앞)에 넣는다.
    has_anchor = bool(note_n and re.search(r'id="note-%d"' % note_n, inner))
    snippet = to_html(text, filename, note_n, emit_id=not has_anchor)

    if has_anchor:
        nxt = re.search(r'\n\s*<h[1-6][^>]*id="note-%d"' % (note_n + 1), inner)
        if nxt:
            new_inner = inner[:nxt.start()] + "\n    " + snippet + inner[nxt.start():]
        else:  # 마지막 발표 → 블록 끝에 추가
            new_inner = inner.rstrip() + "\n    " + snippet
    elif re.search(r'<p class="empty">.*?</p>', inner, re.S) and not re.sub(
            r'<p class="empty">.*?</p>', "", inner, flags=re.S).strip():
        # 빈 자리표시자만 있으면 치우고 넣는다.
        new_inner = "\n    " + snippet
    else:
        new_inner = inner.rstrip() + "\n    " + snippet

    new_block = start + new_inner + end
    txt = txt[:m.start()] + new_block + txt[m.end():]
    open(path, "w", encoding="utf-8").write(txt)
    return os.path.relpath(path, ROOT), s

# ---------------- CLI ----------------
def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    if "--check" in a:
        check(); return

    opts = {"block": "abstract", "model": "gpt-4o-transcribe", "language": None,
            "prompt": None, "session": None, "out": None, "note": None}
    audio = None
    i = 0
    while i < len(a):
        t = a[i]
        if t in ("--session",): opts["session"] = a[i+1]; i += 2
        elif t in ("--block",): opts["block"] = a[i+1]; i += 2
        elif t in ("--model",): opts["model"] = a[i+1]; i += 2
        elif t in ("--language","--lang"): opts["language"] = a[i+1]; i += 2
        elif t in ("--prompt",): opts["prompt"] = a[i+1]; i += 2
        elif t in ("--note",): opts["note"] = int(a[i+1]); i += 2
        elif t in ("-o","--out"): opts["out"] = a[i+1]; i += 2
        else: audio = t; i += 1
    if not audio:
        sys.exit("✗ 오디오 파일을 지정하세요.  예: python3 tools/transcribe.py rec.m4a")

    text = transcribe_file(audio, opts["model"], opts["language"], opts["prompt"])
    if not text:
        sys.exit("✗ 전사 결과가 비어 있습니다.")
    print("\n─── 전사 (%d자) ───" % len(text))

    if opts["out"]:
        open(opts["out"], "w", encoding="utf-8").write(text + "\n")
        print("· 저장:", opts["out"])

    if opts["session"]:
        prog = generate.load()
        rel, s = insert_into_session(prog, opts["session"], opts["block"],
                                     text, os.path.basename(audio), opts["note"])
        # 링크 상태 갱신
        generate.build_day(prog, generate.day_of(prog, s["day"]))
        print("· 세션 페이지에 삽입:", rel, "(블록: %s%s)" %
              (opts["block"], ", note-%d" % opts["note"] if opts["note"] else ""))
        print("  → 커밋/푸시 잊지 마세요.")
    elif not opts["out"]:
        print(text)

if __name__ == "__main__":
    try:
        main()
    except ApiError as e:
        sys.exit("✗ OpenAI API 오류 (%s)" % e)
