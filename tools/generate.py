#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASSC 29 notes companion — page generator.

Data source of truth : data/program.json   (session metadata / speakers / talks)
Notes source of truth : the .html files themselves (content between NOTES markers)

Usage:
  python3 tools/generate.py index                 # build index.html + the 4 day index pages
  python3 tools/generate.py session <ref>         # build/refresh ONE session page (+ its day index)
  python3 tools/generate.py all                   # build everything (index + days + every session page)
  python3 tools/generate.py list                  # print every session id / slug / title

<ref> may be a session id ("d2-sym-2"), a slug, or fuzzy text ("day2 symposium 2",
"day 2 session 6", "keynote 3", "poster 1"). Regenerating a page PRESERVES existing notes.
"""
import json, os, re, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "program.json")

def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)

def esc(s): return html.escape(s or "", quote=True)

NOTE_BLOCKS = [
    ("abstract",  "📄 발표·초록 메모",  "발표 내용 / 초록 요약을 여기에 (Claude에게 말하거나 이 파일을 직접 편집)."),
    ("mynotes",   "📝 내 메모",        "핵심 주장 · 방법 · 인상 깊은 점을 여기에."),
    ("questions", "❓ 질문",           "궁금한 점 · 저자에게 물어볼 것."),
    ("followups", "🔖 팔로업",         "읽을 논문 · 연락할 사람 · 후속 아이디어."),
]

def note_markers(key): return (f"<!-- NOTES:{key}:START -->", f"<!-- NOTES:{key}:END -->")

def extract_notes(path):
    """Return {key: inner_html} for existing NOTES blocks in a file (empty dict if new)."""
    if not os.path.exists(path): return {}
    txt = open(path, encoding="utf-8").read()
    out = {}
    for key, _, _ in NOTE_BLOCKS:
        s, e = note_markers(key)
        m = re.search(re.escape(s) + r"(.*?)" + re.escape(e), txt, re.S)
        if m: out[key] = m.group(1)
    return out

def render_notes(existing):
    parts = []
    for key, label, placeholder in NOTE_BLOCKS:
        s, e = note_markers(key)
        inner = existing.get(key)
        if inner is None or inner.strip() in ("", '<p class="empty">%s</p>' % placeholder):
            inner = '\n      <p class="empty">%s</p>\n    ' % placeholder
        parts.append(
            '  <section class="notes">\n'
            '    <h2>%s</h2>\n'
            '    %s\n    %s\n    %s\n'
            '  </section>' % (label, s, inner, e))
    return "\n".join(parts)

PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · ASSC 29</title>
<link rel="stylesheet" href="{css}">
</head>
<body>
<div class="wrap" id="top">
{topbar}
{body}
<footer>{footer}</footer>
</div>
<a href="#top" class="totop" aria-label="맨 위로 (제목·발표 목록)" title="맨 위로">↑</a>
</body>
</html>
"""

def topbar(crumbs, css_prefix, day_href=None):
    nav = ['<a href="%sindex.html">🏠 홈</a>' % css_prefix]
    if day_href: nav.append('<a href="%s">📅 이 날</a>' % day_href)
    return ('<div class="topbar">'
            '<a class="home" href="%sindex.html">ASSC 29</a>'
            '<span class="crumbs">%s</span>'
            '<nav>%s</nav></div>' % (css_prefix, crumbs, "".join(nav)))

def day_of(prog, day_id):
    return next(d for d in prog["days"] if d["id"] == day_id)

def is_satellite(day): return bool(day) and day.get("track") == "satellite"

def footer_text(prog, day=None):
    """Footer line — ASSC 29 for main pages, the satellite meeting for satellite pages."""
    if is_satellite(day):
        s = prog.get("satellite", {})
        head = " · ".join(x for x in (s.get("name"), s.get("city"), s.get("dates")) if x)
    else:
        c = prog["conference"]
        head = "%s · %s · %s" % (c["short"], c["city"], c["dates"])
    return head + " · 이 페이지는 메모용입니다 — 자유롭게 편집하세요."

# ---------------- session page ----------------
def session_body(s, day):
    typ = s["type"]
    label = {"tutorial":"Tutorial","keynote":"Keynote","symposium":"Symposium",
             "concurrent":"Concurrent Session","poster":"Poster Session","special":"Event",
             "contributed":"Contributed Talks","experiential":"Experiential Session"}[typ]
    if s.get("number"): label += " %d" % s["number"]
    meta = ['<span><b>%s</b></span>' % esc(day["label"])]
    t = (s.get("start","") + (" – "+s["end"] if s.get("end") else "")).strip(" –")
    if t: meta.append('<span>🕑 %s</span>' % esc(t))
    if s.get("room"): meta.append('<span>📍 %s</span>' % esc(s["room"]))
    head = ('<span class="pill %s">%s</span>\n<h1>%s</h1>\n'
            '<div class="meta-row">%s</div>' % (typ, esc(label), esc(s["title"]), "".join(meta)))

    sec = []
    if s.get("bio"):
        who = " · ".join("%s (%s)" % (sp["name"], sp.get("affiliation","")) for sp in s.get("speakers",[]))
        sec.append('<h2>발표자</h2>\n<div class="card"><h3>%s</h3></div>\n<p class="bio">%s</p>' % (esc(who), esc(s["bio"])))
    elif s.get("speakers"):
        title = "패널" if typ=="special" else "발표자 · 좌장"
        lis = []
        if s.get("chair"):
            lis.append('<li><b>%s</b> <span class="aff">— %s · 좌장(chair)</span></li>' %
                       (esc(s["chair"]["name"]), esc(s["chair"].get("affiliation",""))))
        for sp in s["speakers"]:
            extra = (' — <span class="aff">%s</span>' % esc(sp["affiliation"])) if sp.get("affiliation") else ""
            talk = ('<br><span class="p">%s</span>' % esc(sp["talkTitle"])) if sp.get("talkTitle") else ""
            lis.append('<li><b>%s</b>%s%s</li>' % (esc(sp["name"]), extra, talk))
        sec.append('<h2>%s</h2>\n<ul class="speakers">%s</ul>' % (title, "".join(lis)))
    elif s.get("chair"):
        sec.append('<h2>좌장</h2>\n<ul class="speakers"><li><b>%s</b> <span class="aff">— %s</span></li></ul>'
                   % (esc(s["chair"]["name"]), esc(s["chair"].get("affiliation",""))))

    if s.get("talks"):
        def _talk_row(i, t):
            pres = esc(t["presenter"])
            if t.get("time"): pres = '%s · %s' % (esc(t["time"]), pres)
            return ('<div class="talk" id="talk-%d"><div class="t"><a href="#note-%d">%s</a></div>'
                    '<div class="p">%s</div></div>' % (i, i, esc(t["title"]), pres))
        rows = "".join(_talk_row(i, t) for i, t in enumerate(s["talks"], 1))
        sec.append('<h2>발표 (%d)</h2>\n<div class="card">%s</div>' % (len(s["talks"]), rows))

    if typ == "poster":
        sec.append('<div class="hint">포스터 %s편. 전체 목록은 <code>data/source/fullprogram.txt</code>의 해당 세션을 참고하세요. '
                   '특정 포스터 페이지가 필요하면 Claude에게 요청하세요.</div>' % s.get("posterCount","?"))
    if s.get("note"):
        sec.append('<div class="hint">%s</div>' % esc(s["note"]))
    return head + "\n" + "\n".join(sec)

def build_session(prog, s):
    day = day_of(prog, s["day"])
    path = os.path.join(ROOT, day["folder"], s["slug"] + ".html")
    existing = extract_notes(path)
    body = session_body(s, day) + "\n" + render_notes(existing)
    tb = topbar("%s · %s" % (esc(day["label"]), esc(s["title"][:38])), "../", "./index.html")
    out = PAGE.format(title=esc(s["title"]), css="../assets/style.css", topbar=tb, body=body,
                      footer=esc(footer_text(prog, day)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(out)
    return os.path.relpath(path, ROOT)

# ---------------- day index ----------------
def build_day(prog, day):
    sess = [s for s in prog["sessions"] if s["day"] == day["id"]]
    # group by start time
    slots = {}
    for s in sess:
        slots.setdefault(s.get("start","") or "—", []).append(s)
    rows = []
    for start in sorted(slots, key=lambda x: (x=="—", x)):
        rows.append('<div class="slot">%s</div>' % esc(start if start!="—" else "일정"))
        for s in slots[start]:
            fp = os.path.join(ROOT, day["folder"], s["slug"] + ".html")
            t = (s.get("start","") + (" – "+s["end"] if s.get("end") else "")).strip(" –")
            num = ("#%d " % s["number"]) if s.get("number") else ""
            if os.path.exists(fp):
                status = '<span class="status ready">✓ 메모</span>'
                ttl = '<a href="./%s.html">%s%s</a>' % (esc(s["slug"]), esc(num), esc(s["title"]))
            else:
                status = '<span class="status">＋ 만들려면 Claude에게</span>'
                ttl = '%s%s' % (esc(num), esc(s["title"]))
            rows.append('<div class="sess"><div class="time">%s<br><span class="pill %s">%s</span></div>'
                        '<div class="body"><div class="ttl">%s</div><div class="rm">%s</div></div>%s</div>'
                        % (esc(t), s["type"], esc(s["type"]), ttl, esc(s.get("room","")), status))
    body = ('<h1>%s</h1>\n<p class="sub">%s · %s</p>\n%s'
            % (esc(day["label"]), esc(day["weekday"]), esc(day["date"]), "\n".join(rows)))
    tb = topbar(esc(day["label"]), "../")
    out = PAGE.format(title=esc(day["label"]), css="../assets/style.css", topbar=tb, body=body,
                      footer=esc(footer_text(prog, day)))
    path = os.path.join(ROOT, day["folder"], "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(out)
    return os.path.relpath(path, ROOT)

# ---------------- home ----------------
def day_card(prog, d):
    n = sum(1 for s in prog["sessions"] if s["day"] == d["id"])
    return ('<a class="dcard" href="%s/index.html"><div class="d">%s · %s</div>'
            '<div class="n">%s</div><div class="d">%d개 세션 →</div></a>'
            % (d["folder"], esc(d["weekday"]), esc(d["date"]), esc(d["label"]), n))

def build_index(prog):
    c = prog["conference"]
    main_days = [d for d in prog["days"] if not is_satellite(d)]
    sat_days  = [d for d in prog["days"] if is_satellite(d)]
    cards = "".join(day_card(prog, d) for d in main_days)

    sat_block = ""
    if sat_days:
        sat = prog.get("satellite", {})
        sub = " · ".join(x for x in (
            ("“%s”" % sat["subtitle"]) if sat.get("subtitle") else None,
            sat.get("city"), sat.get("dates")) if x)
        sat_cards = "".join(day_card(prog, d) for d in sat_days)
        sat_block = (
            '<h2>🛰 부속 워크숍 — %s</h2>\n'
            '<p class="sub">%s</p>\n'
            '<div class="grid-days">%s</div>\n'
            '<div class="hint">본 학회(6/30–7/3) 직후 열리는 위성 워크숍입니다. 세션 페이지·메모 방식은 본 학회와 동일해요.</div>'
            % (esc(sat.get("name", "Satellite Meeting")), esc(sub), sat_cards))

    body = ('<h1>%s</h1>\n<p class="sub">%s · %s · %s</p>\n'
            '<div class="meta-row"><span>📶 Wi-Fi <b>%s</b> / %s</span><span>🔗 <a href="%s">공식 프로그램</a></span></div>\n'
            '<div class="grid-days">%s</div>\n'
            '<div class="grid-days"><a class="dcard" href="research-ideas.html">'
            '<div class="d">메모장</div><div class="n">💡 연구 방향 아이디어</div>'
            '<div class="d">학회에서 떠오른 연구 아이디어 모음 →</div></a></div>\n'
            '<div class="hint">세션 페이지는 필요할 때 만들어요. 폰이든 PC든 Claude Code에게 '
            '<b>“Day 2 Symposium 2 페이지 만들어줘”</b> 처럼 말하면 됩니다. 자세한 방식은 <code>CLAUDE.md</code> 참고.</div>\n'
            '%s'
            % (esc(c["name"]), esc(c["city"]), esc(c["venue"]), esc(c["dates"]),
               esc(c["wifi"]["network"]), esc(c["wifi"]["password"]), esc(c["site"]), cards, sat_block))
    tb = ('<div class="topbar"><span class="home">ASSC 29</span>'
          '<span class="crumbs">메모 컴패니언</span></div>')
    out = PAGE.format(title="메모 컴패니언", css="assets/style.css", topbar=tb, body=body,
                      footer=esc(footer_text(prog)))
    path = os.path.join(ROOT, "index.html")
    open(path, "w", encoding="utf-8").write(out)
    return "index.html"

# ---------------- resolver ----------------
def resolve(prog, ref):
    ref = ref.strip()
    for s in prog["sessions"]:
        if s["id"] == ref or s["slug"] == ref: return s
    low = ref.lower()
    want_sat = "satellite" in low or "위성" in low or "부속" in low
    sat_ids = {d["id"] for d in prog["days"] if d.get("track") == "satellite"}
    # fuzzy: day + type/number
    dm = re.search(r"day\s*([1-6])", low)
    if dm:
        day = ("sat%s" % dm.group(1)) if want_sat else ("day%s" % dm.group(1))
        rest = low[:dm.start()] + low[dm.end():]  # drop the "dayN" token first
    else:
        day, rest = None, low
    nm = re.search(r"(\d+)", rest)
    number = int(nm.group(1)) if nm else None
    if "keynote" in low: typ="keynote"
    elif "experiential" in low: typ="experiential"
    elif "contributed" in low: typ="contributed"
    elif "symposium" in low or "symp" in low: typ="symposium"
    elif "tutorial" in low: typ="tutorial"
    elif "poster" in low: typ="poster"
    elif "session" in low or "concurrent" in low: typ="concurrent"
    else: typ=None
    pool = [s for s in prog["sessions"] if (s["day"] in sat_ids) == want_sat]
    cand = [s for s in pool
            if (day is None or s["day"]==day)
            and (typ is None or s["type"]==typ)
            and (number is None or s.get("number")==number)]
    if len(cand)==1: return cand[0]
    # keynotes/contributed within a satellite day carry their number in the title, not `number`
    if want_sat and number is not None and typ:
        cand2 = [s for s in cand or pool
                 if s["type"]==typ and (" %d" % number) in s["title"]]
        if len(cand2)==1: return cand2[0]
    # last resort: title substring
    tsub=[s for s in pool if low in s["title"].lower()]
    if len(tsub)==1: return tsub[0]
    return None

def main():
    prog = load()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "index"
    if cmd == "list":
        for s in prog["sessions"]:
            print("%-14s %-46s %s" % (s["id"], s["slug"], s["title"][:50]))
        return
    if cmd == "index":
        print("built", build_index(prog))
        for d in prog["days"]: print("built", build_day(prog, d))
        return
    if cmd == "all":
        print("built", build_index(prog))
        for d in prog["days"]: print("built", build_day(prog, d))
        for s in prog["sessions"]: print("built", build_session(prog, s))
        return
    if cmd == "session":
        if len(sys.argv) < 3: sys.exit("usage: generate.py session <ref>")
        ref = " ".join(sys.argv[2:])
        s = resolve(prog, ref)
        if not s:
            sys.exit("cannot resolve '%s'. try: python3 tools/generate.py list" % ref)
        print("built", build_session(prog, s))
        print("built", build_day(prog, day_of(prog, s["day"])))  # refresh link status
        return
    sys.exit("unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
