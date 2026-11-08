#!/usr/bin/env python3
"""Builds the bilingual (English / Turkish) Film Teorisi site from content/*.json.

Usage (from the repo root):  python3 scripts/build.py

Turkish lessons:  content/<date>-hafta-XX-gun-Y.json
English twins:    content/en/<same file name>   (optional; if missing, the English
                  view shows the Turkish lesson with a short note)
Program:          data/program.json (Turkish), data/program.en.json (English, optional)

Every generated page contains both languages. A small script in <head> picks the
language: ?lang=en|tr in the URL, otherwise the visitor's saved choice, otherwise
English. The EN/TR switch in the header saves the choice (localStorage).

Generates: index.html, dersler.html, program.html, sozluk.html, filmler.html,
arsiv.html (redirects to dersler.html), feed.xml (Turkish), feed-en.xml (English)
and ders/<slug>.html. See README.md for the lesson content format.
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    TZ = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE_URL = "https://sguven.github.io/film-teorisi/"
START = dt.date(2026, 10, 5)  # Monday of Week 1 (shifted); Week n = START + 7(n-1)
TOTAL_WEEKS = 52
LANGS = ("en", "tr")  # first one is the default for new visitors

MONTHS = {
    "tr": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
           "Eylül", "Ekim", "Kasım", "Aralık"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}
WEEKDAYS = {
    "tr": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
TYPES = ("ders", "tekrar", "film", "sinav")

# ---------------------------------------------------------------- UI strings
S = {
    "tr": {
        "site": "Film Teorisi",
        "site_full": "Film Teorisi: 52 haftalık okuma programı",
        "site_desc": "52 haftalık bir film teorisi programı: günlük kısa dersler, haftalık filmler, testler ve terim sözlüğü.",
        "nav": ["Son ders", "Dersler", "Program", "Sözlük", "Filmler"],
        "skip": "İçeriğe geç",
        "foot": "52 haftalık bir film teorisi programı. Dersler her gün Claude ile hazırlanıyor.",
        "rss": "RSS ile takip et",
        "week": "Hafta", "day": "Gün", "review": "Tekrar",
        "tag": {"ders": "Ders", "tekrar": "Tekrar", "film": "Film", "sinav": "Test"},
        "long": {"ders": "Okuma", "tekrar": "Tekrar", "film": "Film günü", "sinav": "Sınav günü"},
        "latest_prefix": "En güncel ders, ",
        "reading": "Okuma", "film_of_week": "Haftanın filmi", "pdf": "PDF olarak indir",
        "one": "Bugünün tek cümlesi", "questions": "Bugünün soruları",
        "hints": "Cevap ipuçları (önce kendin dene)", "analysis": "Analiz görevi",
        "observe": "Gözlem görevi", "two_min": "2 dakika", "terms": "Bugünün terimleri",
        "next_topic": "Sıradaki ders", "prev": "Önceki ders", "next": "Sonraki ders",
        "new_daily": "Yeni ders her gün ekleniyor", "archive": "Arşiv", "browse": "Bütün derslere göz at",
        "pager": "Ders gezinme", "week_days": "Bu haftanın günleri", "not_yet": "Henüz yayımlanmadı",
        "days_of_week": "Hafta {w} günleri",
        "quiz": "Test", "quiz_help": "Bir seçeneğe dokun; cevap ve açıklama hemen açılır.",
        "score": "Puan", "reset": "Testi sıfırla", "q_ok": "Doğru.", "q_answer": "Doğru cevap:",
        "q_answered": "cevaplandı",
        "th_first": "Türkçe", "th_second": "English", "th_def": "Tanım", "th_src": "İlk geçtiği",
        "first_soon": "İlk ders yakında",
        "lessons": "Dersler", "go_latest": "En güncel derse git", "go_first": "Programın ilk dersi",
        "lessons_intro": "Haftalar en yenisi üstte olacak şekilde sıralı. Her hafta beş okuma günü, "
                         "bir film günü ve bir sınav gününden oluşuyor.",
        "no_lessons": "Henüz ders yok.",
        "program": "Program",
        "program_intro": "52 hafta, 9 faz. Film dilinden başlayıp klasik teoriye, auteur ve türe, göstergebilim ve "
                         "psikanalize, bilişsel kurama, belgesele, dijital sinemaya ve Türkiye sinemasına uzanıyor. Her faz bir "
                         "öncekinin üstüne kurulu. Dersleri yayımlanmış haftalara tıklayabilirsin.",
        "phase": "Faz", "live": "Yayında",
        "glossary": "Sözlük",
        "glossary_intro": "Derslerde geçen {n} terim: Türkçesi, İngilizcesi (gerekirse orijinal dili) ve tek "
                          "cümlelik tanımı. Her terim ilk geçtiği derse bağlanıyor.",
        "search": "Terim ara (Türkçe ya da İngilizce)…", "search_label": "Terim ara",
        "no_match": "Bu aramayla eşleşen terim yok.",
        "films": "Filmler",
        "films_intro": 'Haftanın filmleri ve derslerde örnek olarak açılan filmler. Programdaki bütün filmlerin '
                       'listesi <a href="program.html">Program</a> sayfasında.',
        "no_films": "Henüz film yok.", "appears_in": "Geçtiği dersler",
        "feed_desc": "52 haftalık film teorisi programının günlük dersleri",
        "fallback": "",
        "anchor": "hafta",
    },
    "en": {
        "site": "Film Theory",
        "site_full": "Film Theory: a 52-week reading program",
        "site_desc": "A 52-week film theory program: short daily lessons, weekly films, quizzes and a glossary of terms.",
        "nav": ["Latest", "Lessons", "Program", "Glossary", "Films"],
        "skip": "Skip to content",
        "foot": "A 52-week film theory program. Lessons are prepared daily with Claude.",
        "rss": "Follow via RSS",
        "week": "Week", "day": "Day", "review": "Review",
        "tag": {"ders": "Lesson", "tekrar": "Review", "film": "Film", "sinav": "Quiz"},
        "long": {"ders": "Reading", "tekrar": "Review", "film": "Film day", "sinav": "Quiz day"},
        "latest_prefix": "Latest lesson, ",
        "reading": "Reading", "film_of_week": "Film of the week", "pdf": "Download PDF (Turkish)",
        "one": "Today in one sentence", "questions": "Today’s questions",
        "hints": "Answer hints (try it yourself first)", "analysis": "Analysis task",
        "observe": "Observation exercise", "two_min": "2 minutes", "terms": "Today’s terms",
        "next_topic": "Next up", "prev": "Previous lesson", "next": "Next lesson",
        "new_daily": "A new lesson is added every day", "archive": "Archive", "browse": "Browse all lessons",
        "pager": "Lesson navigation", "week_days": "Days of this week", "not_yet": "Not published yet",
        "days_of_week": "Days of week {w}",
        "quiz": "Quiz", "quiz_help": "Tap an option; the answer and explanation appear right away.",
        "score": "Score", "reset": "Reset quiz", "q_ok": "Correct.", "q_answer": "Correct answer:",
        "q_answered": "answered",
        "th_first": "English", "th_second": "Turkish", "th_def": "Definition", "th_src": "First appears",
        "first_soon": "The first lesson is coming soon",
        "lessons": "Lessons", "go_latest": "Go to the latest lesson", "go_first": "The program’s first lesson",
        "lessons_intro": "Weeks are listed newest first. Each week has five reading days, "
                         "a film day and a quiz day.",
        "no_lessons": "No lessons yet.",
        "program": "Program",
        "program_intro": "52 weeks, 9 phases. It starts with the language of film and moves through classical theory, "
                         "auteur and genre, semiotics and psychoanalysis, cognitive theory, documentary, digital cinema "
                         "and the cinema of Turkey. Each phase builds on the one before. Weeks with published lessons "
                         "are clickable.",
        "phase": "Phase", "live": "Published",
        "glossary": "Glossary",
        "glossary_intro": "{n} terms from the lessons: the English term, the Turkish term (and the original language "
                          "where relevant) and a one-sentence definition. Each term links to the lesson where it "
                          "first appears.",
        "search": "Search terms (English or Turkish)…", "search_label": "Search terms",
        "no_match": "No terms match this search.",
        "films": "Films",
        "films_intro": 'The films of the week and the films used as examples in the lessons. The full list of the '
                       'program’s films is on the <a href="program.html">Program</a> page.',
        "no_films": "No films yet.", "appears_in": "Appears in",
        "feed_desc": "Daily lessons from a 52-week film theory program",
        "fallback": "The English translation of this lesson is on its way. In the meantime, here is the original "
                    "Turkish version.",
        "anchor": "week",
    },
}

TR_ORDER = "aâbcçdefgğhıiîjklmnoöprsştuûüvyzqwx"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def strip_tags(s):
    return re.sub("<[^>]+>", "", s or "")


def tr_key(s):
    s = (s or "").replace("I", "ı").replace("İ", "i").lower()
    return [TR_ORDER.index(c) if c in TR_ORDER else 100 + ord(c) for c in s]


def date_str(d, lang, weekday=False):
    m = MONTHS[lang][d.month - 1]
    if lang == "en":
        s = f"{m} {d.day}, {d.year}"
        return f"{WEEKDAYS['en'][d.weekday()]}, {s}" if weekday else s
    s = f"{d.day} {m} {d.year}"
    return f"{WEEKDAYS['tr'][d.weekday()]}, {s}" if weekday else s


def today():
    return dt.datetime.now(TZ).date() if TZ else dt.date.today()


def week_of(d):
    if d < START:
        return 1
    return (d - START).days // 7 + 1


def slug(L):
    g = L["gun"]
    return f"hafta-{L['hafta']:02d}-" + ("tekrar" if g == "tekrar" else f"gun-{g}")


def day_label(L, lang):
    g = L["gun"]
    return S[lang]["review"] if g == "tekrar" else f"{S[lang]['day']} {g}"


def label(L, lang):
    return f"{S[lang]['week']} {L['hafta']} · {day_label(L, lang)}"


def sort_key(L):
    g = L["gun"]
    # The review day comes after Day 5 and before Day 6
    order = 5.5 if g == "tekrar" else float(g)
    return (L["hafta"], order, L["_date"])


def C(L, lang):
    """The lesson's content in a language (English falls back to Turkish)."""
    if lang == "en" and L.get("_en"):
        return L["_en"]
    return L


def is_fallback(L, lang):
    return lang == "en" and not L.get("_en")


def title_of(L, lang):
    return C(L, lang)["baslik"]


# ---------------------------------------------------------------- loading
def check_quiz(name, L):
    for i, q in enumerate(L.get("quiz") or []):
        if not (0 <= q.get("dogru", -1) < len(q.get("secenekler", []))):
            sys.exit(f"HATA: {name} quiz sorusu {i+1}: 'dogru' seçenek sırası (0'dan başlar) hatalı")


def load_lessons():
    lessons = []
    en_dir = ROOT / "content" / "en"
    for p in sorted((ROOT / "content").glob("*.json")):
        try:
            L = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"HATA: {p.name} geçerli JSON değil: {e}")
        for k in ("hafta", "gun", "tarih", "tur", "baslik"):
            if k not in L:
                sys.exit(f"HATA: {p.name} içinde '{k}' alanı eksik")
        if L["tur"] not in TYPES:
            sys.exit(f"HATA: {p.name}: tur ders/tekrar/film/sinav olmalı")
        check_quiz(p.name, L)
        L["_date"] = dt.date.fromisoformat(L["tarih"])
        L["_slug"] = slug(L)
        L["_en"] = None
        ep = en_dir / p.name
        if ep.exists():
            try:
                E = json.loads(ep.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                sys.exit(f"HATA: en/{p.name} geçerli JSON değil: {e}")
            if not E.get("baslik"):
                sys.exit(f"HATA: en/{p.name} içinde 'baslik' alanı eksik")
            check_quiz("en/" + p.name, E)
            L["_en"] = E
        lessons.append(L)
    for ep in sorted(en_dir.glob("*.json")) if en_dir.exists() else []:
        if not (ROOT / "content" / ep.name).exists():
            print(f"UYARI: en/{ep.name} için Türkçe ders dosyası yok; atlandı.")
    lessons.sort(key=sort_key)
    seen = set()
    for i, L in enumerate(lessons):
        if L["_slug"] in seen:
            sys.exit(f"HATA: aynı ders iki kez var: {L['_slug']}")
        seen.add(L["_slug"])
        L["_n"] = i + 1
    return lessons


def load_program():
    out = {}
    for lang, name in (("tr", "program.json"), ("en", "program.en.json")):
        p = ROOT / "data" / name
        out[lang] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    if out["tr"] is None:
        out["tr"] = []
    if out["en"] is None:
        out["en"] = out["tr"]
    return out


def week_info(program, week):
    for f in program:
        for w in f["haftalar"]:
            end = w.get("hafta_bitis") or w["hafta"]
            if w["hafta"] <= week <= end:
                return w
    return None


# ---------------------------------------------------------------- template
HEAD_SCRIPT = """<script>(function(){var d=document.documentElement,l=null;try{var q=new URLSearchParams(location.search).get("lang");if(q==="en"||q==="tr"){l=q;localStorage.setItem("ft-lang",q)}else{l=localStorage.getItem("ft-lang")}}catch(e){}if(l!=="en"&&l!=="tr")l="en";d.setAttribute("data-lang",l);d.lang=l;var t=d.getAttribute("data-title-"+l);if(t)document.title=t})();</script>
<style>html[data-lang="en"] .l-tr,html[data-lang="tr"] .l-en{display:none!important}</style>"""


def both(fn):
    """Renders fn(lang) once per language into .l-en / .l-tr wrappers."""
    return "".join(f'<div class="l-{lg}" lang="{lg}">{fn(lg)}</div>' for lg in LANGS)


def inline(d):
    """{lang: text} -> spans."""
    return "".join(f'<span class="l-{lg}" lang="{lg}">{d[lg]}</span>' for lg in LANGS)


def page(titles, bodies, active, depth=0, descs=None, wide=False):
    """titles/bodies/descs: {lang: str}. titles are plain text (page title without the site name)."""
    up = "../" * depth
    keys = ["ana", "dersler", "program", "sozluk", "filmler"]
    hrefs = ["index.html", "dersler.html", "program.html", "sozluk.html", "filmler.html"]
    nav_html = "".join(
        f'<a href="{up}{h}"{" aria-current=\"page\"" if k == active else ""}>'
        f'{inline({lg: S[lg]["nav"][i] for lg in LANGS})}</a>'
        for i, (h, k) in enumerate(zip(hrefs, keys)))
    full = {}
    for lg in LANGS:
        t = titles.get(lg)
        full[lg] = f"{t} | {S[lg]['site']}" if t else S[lg]["site_full"]
    descs = descs or {}
    desc = {lg: esc(descs.get(lg) or S[lg]["site_desc"]) for lg in LANGS}
    dl = LANGS[0]
    w = "wrap-wide" if wide else "wrap"
    lang_btns = "".join(f'<button type="button" data-set-lang="{lg}" lang="{lg}" '
                        f'aria-label="{"English" if lg == "en" else "Türkçe"}">{lg.upper()}</button>' for lg in LANGS)
    main = "".join(f'<div class="l-{lg}" lang="{lg}">{bodies[lg]}</div>' for lg in LANGS)
    return f"""<!doctype html>
<html lang="{dl}" data-lang="{dl}" data-title-en="{esc(full['en'])}" data-title-tr="{esc(full['tr'])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full[dl])}</title>
{HEAD_SCRIPT}
<meta name="description" content="{desc[dl]}">
<meta name="theme-color" content="#FAF8F4">
<meta property="og:title" content="{esc(full[dl])}">
<meta property="og:description" content="{desc[dl]}">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
<link rel="alternate" type="application/rss+xml" title="Film Theory (English)" href="{up}feed-en.xml">
<link rel="alternate" type="application/rss+xml" title="Film Teorisi (Türkçe)" href="{up}feed.xml">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%232F5D73'/%3E%3Ctext x='16' y='22' font-family='Georgia,serif' font-size='17' text-anchor='middle' fill='%23FAF8F4'%3EFT%3C/text%3E%3C/svg%3E">
</head>
<body>
<a class="skip" href="#icerik">{inline({lg: S[lg]["skip"] for lg in LANGS})}</a>
<header class="site-head"><div class="wrap-wide">
<a class="brand" href="{up}index.html">{inline({lg: S[lg]["site"] for lg in LANGS})}</a>
<nav class="nav" aria-label="Site">{nav_html}</nav>
<div class="lang-switch" role="group" aria-label="Language / Dil">{lang_btns}</div>
</div></header>
<main id="icerik"><div class="{w}">
{main}
</div></main>
<footer class="site-foot"><div class="wrap-wide">
{inline({lg: S[lg]["foot"] for lg in LANGS})}
<span class="l-en" lang="en"><a href="{up}feed-en.xml">{S["en"]["rss"]}</a></span><span class="l-tr" lang="tr"><a href="{up}feed.xml">{S["tr"]["rss"]}</a></span>
</div></footer>
<script src="{up}assets/site.js" defer></script>
</body>
</html>
"""


def terms_table(terms, lang, with_source=False):
    if not terms:
        return ""
    s = S[lang]
    head = (f"<th>{s['th_first']}</th><th>{s['th_second']}</th><th>{s['th_def']}</th>"
            + (f"<th>{s['th_src']}</th>" if with_source else ""))
    rows = []
    for t in terms:
        orig = f'<span class="orig">{esc(t["orijinal"])}</span>' if t.get("orijinal") else ""
        src = f'<td class="src">{t["_src"]}</td>' if with_source else ""
        if lang == "en":
            first = f'<td class="en">{esc(t.get("en"))}{orig}</td>'
            second = f'<td lang="tr">{esc(t.get("tr"))}</td>'
        else:
            first = f'<td>{esc(t.get("tr"))}</td>'
            second = f'<td class="en" lang="en">{esc(t.get("en"))}{orig}</td>'
        rows.append(f'<tr data-row>{first}{second}<td>{esc(t.get("tanim"))}</td>{src}</tr>')
    return (f'<div class="table-scroll"><table class="terms"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def quiz_block(quiz, lang):
    s = S[lang]
    data = json.dumps(quiz, ensure_ascii=False).replace("</", "<\\/")
    return f"""<section class="box" data-quiz data-ok="{esc(s['q_ok'])}" data-answer="{esc(s['q_answer'])}" data-answered="{esc(s['q_answered'])}">
<h2>{s['quiz']}</h2>
<p class="meta" style="margin-bottom:0.5rem">{s['quiz_help']}</p>
<script type="application/json">{data}</script>
<div class="quiz-list"></div>
<div class="quiz-score">{s['score']}: <b class="val"></b> <button type="button" class="btn btn-ghost" data-quiz-reset>{s['reset']}</button></div>
</section>"""


# ---------------------------------------------------------------- pages
def week_strip(week, week_lessons, ders_prefix, lang, current=None):
    """Shows the days of the week as a 7-frame film strip."""
    s = S[lang]
    by = {str(x["gun"]): x for x in week_lessons}
    slots = ["1", "2", "3", "4", "5"] + (["tekrar"] if "tekrar" in by else []) + ["6", "7"]
    items = []
    for sl in slots:
        num = ("R" if lang == "en" else "T") if sl == "tekrar" else sl
        x = by.get(sl)
        if x:
            title = esc(f'{day_label(x, lang)}: {title_of(x, lang)}')
            cur = ' aria-current="page"' if x is current else ""
            items.append(f'<a href="{ders_prefix}{x["_slug"]}.html" title="{title}"{cur}>{num}</a>')
        else:
            items.append(f'<span title="{s["not_yet"]}">{num}</span>')
    aria = s["days_of_week"].format(w=week)
    return (f'<nav class="days" aria-label="{esc(aria)}"><span class="days-label">{s["week_days"]}</span>'
            f'{"".join(items)}</nav>')


def lesson_header(L, program, up, lang, latest=False):
    s = S[lang]
    X = C(L, lang)
    wi = week_info(program[lang], L["hafta"])
    week_title = f"{s['week']} {L['hafta']}" + (f": {wi['baslik']}" if wi else "")
    when = (s["latest_prefix"] if latest else "") + date_str(L["_date"], lang)
    meta = []
    if X.get("okuma"):
        meta.append(f"<span>{s['reading']}: {esc(X['okuma'])}</span>")
    if X.get("film"):
        meta.append(f"<span>{s['film_of_week']}: <i>{esc(X['film'])}</i></span>")
    if L.get("pdf"):
        meta.append(f'<span><a href="{up}pdf/{esc(L["pdf"])}">{s["pdf"]}</a></span>')
    meta_html = f'<p class="meta">{"".join(meta)}</p>' if meta else ""
    return (f'<header class="lesson-head">'
            f'<p class="eyebrow"><a href="{up}dersler.html#{s["anchor"]}-{L["hafta"]}">{esc(week_title)}</a>'
            f'<span>{esc(day_label(L, lang))}, {esc(s["long"][L["tur"]].lower())}</span></p>'
            f'<h1>{esc(X["baslik"])}</h1><p class="date">{esc(when)}</p>{meta_html}</header>')


def lesson_body(L, prev, nxt, program, ders_prefix, up, week_lessons, lang, latest=False):
    """Lesson content. ders_prefix: prefix of the path to lesson pages ("" from inside ders/, "ders/" from the root)."""
    s = S[lang]
    X = C(L, lang)
    parts = [lesson_header(L, program, up, lang, latest)]
    parts.append(week_strip(L["hafta"], week_lessons, ders_prefix, lang, current=L))
    content = []
    if X.get("tek_cumle"):
        content.append(f'<p class="lead"><span class="lead-label">{s["one"]}</span>{X["tek_cumle"]}</p>')
    for b in X.get("bolumler", []):
        if b.get("baslik"):
            content.append(f'<h2>{esc(b["baslik"])}</h2>')
        content.append(b.get("html", ""))
    if X.get("quiz"):
        content.append(quiz_block(X["quiz"], lang))
    if X.get("sorular"):
        title = X.get("soru_baslik") or s["questions"]
        items = "".join(f"<li>{q}</li>" for q in X["sorular"])
        hints = ""
        if X.get("ipuclari"):
            hi = "".join(f"<li>{h}</li>" for h in X["ipuclari"])
            hints = f"<details><summary>{s['hints']}</summary><ol>{hi}</ol></details>"
        content.append(f'<section class="box box-accent"><h2>{esc(title)}</h2><ol>{items}</ol>{hints}</section>')
    if X.get("analiz"):
        content.append(f'<section class="box"><h2>{s["analysis"]}</h2>{X["analiz"]}</section>')
    if X.get("gozlem"):
        content.append(f'<section class="box"><h2>{s["observe"]} <small class="muted-small">{s["two_min"]}</small></h2>'
                       f'<p>{X["gozlem"]}</p></section>')
    if X.get("terimler"):
        content.append(f"<h2>{s['terms']}</h2>" + terms_table(X["terimler"], lang))
    if X.get("yarin"):
        content.append(f'<h2>{s["next_topic"]}</h2><p>{X["yarin"]}</p>')
    if is_fallback(L, lang):
        parts.append(f'<p class="note-lang">{s["fallback"]}</p><div lang="tr">{"".join(content)}</div>')
    else:
        parts.extend(content)
    links = []
    if prev:
        links.append(f'<a class="prev" href="{ders_prefix}{prev["_slug"]}.html"><small>{s["prev"]}</small>'
                     f'<span>{esc(label(prev, lang))}</span><b>{esc(title_of(prev, lang))}</b></a>')
    else:
        links.append("<span></span>")
    if nxt:
        links.append(f'<a class="next" href="{ders_prefix}{nxt["_slug"]}.html"><small>{s["next"]}</small>'
                     f'<span>{esc(label(nxt, lang))}</span><b>{esc(title_of(nxt, lang))}</b></a>')
    else:
        links.append(f'<a class="next" href="{up}dersler.html"><small>{s["new_daily"]}</small>'
                     f'<span>{s["archive"]}</span><b>{s["browse"]}</b></a>')
    parts.append(f'<nav class="pager" aria-label="{s["pager"]}">{"".join(links)}</nav>')
    return "\n".join(parts)


def latest_of(lessons):
    return max(lessons, key=lambda x: (x["_date"], sort_key(x))) if lessons else None


def lesson_page(L, prev, nxt, program, lessons):
    wl = [x for x in lessons if x["hafta"] == L["hafta"]]
    latest = L is latest_of(lessons)
    bodies = {lg: lesson_body(L, prev, nxt, program, "", "../", wl, lg, latest) for lg in LANGS}
    titles = {lg: f'{label(L, lg)}: {title_of(L, lg)}' for lg in LANGS}
    descs = {lg: strip_tags(C(L, lg).get("tek_cumle")) for lg in LANGS}
    return page(titles, bodies, "dersler", depth=1, descs=descs)


def index_page(lessons, program):
    if not lessons:
        return page({}, {lg: f"<h1>{S[lg]['first_soon']}</h1>" for lg in LANGS}, "ana")
    L = latest_of(lessons)
    i = lessons.index(L)
    prev = lessons[i - 1] if i > 0 else None
    nxt = lessons[i + 1] if i + 1 < len(lessons) else None
    wl = [x for x in lessons if x["hafta"] == L["hafta"]]
    bodies = {lg: lesson_body(L, prev, nxt, program, "ders/", "", wl, lg, True) for lg in LANGS}
    descs = {lg: strip_tags(C(L, lg).get("tek_cumle")) for lg in LANGS}
    return page({}, bodies, "ana", descs=descs)


def lesson_rows(lessons, lang, prefix=""):
    items = []
    for L in lessons:
        X = C(L, lang)
        one = f'<p class="one">{X["tek_cumle"]}</p>' if X.get("tek_cumle") else ""
        items.append(
            f'<li><a class="row" href="{prefix}ders/{L["_slug"]}.html">'
            f'<span class="when"><b>{esc(day_label(L, lang))}</b><span>{S[lang]["long"][L["tur"]]}</span></span>'
            f'<span class="what"><span class="title">{esc(X["baslik"])}</span>{one}</span></a></li>')
    return f'<ul class="lessons">{"".join(items)}</ul>'


def group_weeks(lessons):
    weeks = {}
    for L in lessons:
        weeks.setdefault(L["hafta"], []).append(L)
    return weeks


def dersler_body(lessons, program, lang):
    s = S[lang]
    weeks = group_weeks(lessons)
    parts = [f'<h1 class="page-title">{s["lessons"]}</h1>']
    if lessons:
        first = lessons[0]
        latest = latest_of(lessons)
        parts.append('<div class="jump">'
                     f'<a class="btn" href="ders/{latest["_slug"]}.html">{s["go_latest"]}</a>'
                     f'<a class="btn btn-ghost" href="ders/{first["_slug"]}.html">{s["go_first"]}</a></div>')
        parts.append(f'<p class="intro">{s["lessons_intro"]}</p>')
    else:
        parts.append(f'<p class="empty">{s["no_lessons"]}</p>')
    for w in sorted(weeks, reverse=True):
        wi = week_info(program[lang], w)
        title = wi["baslik"] if wi else ""
        film = (f'<p class="week-film">{s["film_of_week"]}: <i>{esc(wi["film"])}</i></p>'
                if wi and wi.get("film") else "")
        parts.append(f'<section class="week" id="{s["anchor"]}-{w}"><h2>{s["week"]} {w}: {esc(title)}</h2>{film}'
                     f'{lesson_rows(weeks[w], lang)}</section>')
    return "\n".join(parts)


def dersler_page(lessons, program):
    return page({lg: S[lg]["lessons"] for lg in LANGS},
                {lg: dersler_body(lessons, program, lg) for lg in LANGS}, "dersler")


def redirect_page(target):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}">
<title>Film Theory</title></head><body><a href="{target}">{target}</a></body></html>
"""


def program_body(program, lessons, lang):
    s = S[lang]
    t = today()
    wk = week_of(t)
    have = {L["hafta"] for L in lessons}
    parts = [f'<h1 class="page-title">{s["program"]}</h1>', f'<p class="intro">{s["program_intro"]}</p>']
    for f in program[lang]:
        parts.append(f'<section class="phase"><p class="kicker">{s["phase"]} {esc(f["faz"])}, '
                     f'{s["week"]} {f["baslangic"]}–{f["bitis"]}</p>'
                     f'<h2>{esc(f["ad"])}</h2><p class="desc">{esc(f["aciklama"])}</p><ul class="weeks">')
        for w in f["haftalar"]:
            end = w.get("hafta_bitis") or w["hafta"]
            wn = f"{s['week']} {w['hafta']}" + (f"–{end}" if end != w["hafta"] else "")
            cls = "now" if w["hafta"] <= wk <= end else ("done" if end < wk else "")
            tg = f'<span class="tag">{s["live"]}</span>' if w["hafta"] in have else ""
            title = esc(w["baslik"])
            if w["hafta"] in have:
                title = f'<a href="dersler.html#{s["anchor"]}-{w["hafta"]}">{title}</a>'
            film = f'<span class="film">{esc(w["film"])}</span>' if w.get("film") else ""
            parts.append(f'<li class="{cls}"><span class="wn">{wn}</span><span><span class="wt">{title}</span>{tg}{film}</span></li>')
        parts.append("</ul></section>")
    return "\n".join(parts)


def program_page(program, lessons):
    return page({lg: S[lg]["program"] for lg in LANGS},
                {lg: program_body(program, lessons, lg) for lg in LANGS}, "program")


def collect_terms(lessons, lang):
    seen = {}
    for L in lessons:
        for t in C(L, lang).get("terimler") or []:
            key = ((t.get("en") if lang == "en" else t.get("tr")) or "").strip().lower()
            if not key or key in seen:
                continue
            t = dict(t)
            t["_src"] = f'<a href="ders/{L["_slug"]}.html">{esc(label(L, lang))}</a>'
            seen[key] = t
    if lang == "en":
        return sorted(seen.values(), key=lambda t: (t.get("en") or "").lower())
    return sorted(seen.values(), key=lambda t: tr_key(t["tr"]))


def glossary_body(lessons, lang):
    s = S[lang]
    terms = collect_terms(lessons, lang)
    parts = [f'<h1 class="page-title">{s["glossary"]}</h1>',
             f'<p class="intro">{s["glossary_intro"].format(n=len(terms))}</p>',
             f'<input class="search" type="search" placeholder="{s["search"]}" data-filter aria-label="{s["search_label"]}">']
    parts.append(terms_table(terms, lang, with_source=True))
    parts.append(f'<p class="empty" data-empty hidden>{s["no_match"]}</p>')
    return "\n".join(parts), len(terms)


def glossary_page(lessons):
    bodies = {}
    n = 0
    for lg in LANGS:
        bodies[lg], c = glossary_body(lessons, lg)
        n = max(n, c)
    return page({lg: S[lg]["glossary"] for lg in LANGS}, bodies, "sozluk"), n


def collect_films(lessons, lang):
    films = {}
    for L in lessons:
        for f in C(L, lang).get("filmler") or []:
            key = re.sub(r"\W+", "", (f.get("ad") or "").lower())
            if not key:
                continue
            if key not in films:
                films[key] = {**f, "_refs": []}
            ref = f'<a href="ders/{L["_slug"]}.html">{esc(label(L, lang))}</a>'
            if ref not in films[key]["_refs"]:
                films[key]["_refs"].append(ref)
            if f.get("not") and not films[key].get("not"):
                films[key]["not"] = f["not"]
    return list(films.values())


def films_body(lessons, lang):
    s = S[lang]
    films = collect_films(lessons, lang)
    parts = [f'<h1 class="page-title">{s["films"]}</h1>', f'<p class="intro">{s["films_intro"]}</p>']
    if not films:
        parts.append(f'<p class="empty">{s["no_films"]}</p>')
    for f in films:
        bits = [str(f[k]) for k in ("yonetmen", "yil") if f.get(k)]
        meta = ", ".join(bits)
        note = f'<p style="margin:0.3rem 0 0.4rem">{f["not"]}</p>' if f.get("not") else ""
        parts.append(f'<div class="film-card"><h3><i>{esc(f["ad"])}</i></h3>'
                     f'<div class="fmeta">{esc(meta)}</div>{note}'
                     f'<div class="fmeta">{s["appears_in"]}: {", ".join(f["_refs"])}</div></div>')
    return "\n".join(parts), len(films)


def films_page(lessons):
    bodies = {}
    n = 0
    for lg in LANGS:
        bodies[lg], c = films_body(lessons, lg)
        n = max(n, c)
    return page({lg: S[lg]["films"] for lg in LANGS}, bodies, "filmler"), n


def feed(lessons, lang):
    s = S[lang]
    items = []
    for L in sorted(lessons, key=lambda x: x["_date"], reverse=True)[:30]:
        link = f"{SITE_URL}ders/{L['_slug']}.html?lang={lang}"
        d = dt.datetime.combine(L["_date"], dt.time(15, 0))
        pub = d.strftime("%a, %d %b %Y %H:%M:%S -0400")
        desc = strip_tags(C(L, lang).get("tek_cumle"))
        items.append(f"<item><title>{esc(label(L, lang) + ': ' + title_of(L, lang))}</title><link>{esc(link)}</link>"
                     f"<guid>{esc(link)}</guid><pubDate>{pub}</pubDate><description>{esc(desc)}</description></item>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>{s['site']}</title><link>{SITE_URL}?lang={lang}</link>"
            f"<description>{s['feed_desc']}</description><language>{lang}</language>"
            + "".join(items) + "</channel></rss>\n")


def main():
    lessons = load_lessons()
    program = load_program()
    out = ROOT / "ders"
    out.mkdir(exist_ok=True)
    keep = set()
    total = len(lessons)
    for i, L in enumerate(lessons):
        prev = lessons[i - 1] if i > 0 else None
        nxt = lessons[i + 1] if i + 1 < total else None
        f = out / f"{L['_slug']}.html"
        f.write_text(lesson_page(L, prev, nxt, program, lessons), encoding="utf-8")
        keep.add(f.name)
    for f in out.glob("*.html"):
        if f.name not in keep:
            f.unlink()
    mf = ROOT / "assets" / "manifest.js"
    if mf.exists():
        mf.unlink()
    glossary_html, n_terms = glossary_page(lessons)
    films_html, n_films = films_page(lessons)
    (ROOT / "index.html").write_text(index_page(lessons, program), encoding="utf-8")
    (ROOT / "dersler.html").write_text(dersler_page(lessons, program), encoding="utf-8")
    (ROOT / "arsiv.html").write_text(redirect_page("dersler.html"), encoding="utf-8")
    (ROOT / "program.html").write_text(program_page(program, lessons), encoding="utf-8")
    (ROOT / "sozluk.html").write_text(glossary_html, encoding="utf-8")
    (ROOT / "filmler.html").write_text(films_html, encoding="utf-8")
    (ROOT / "feed.xml").write_text(feed(lessons, "tr"), encoding="utf-8")
    (ROOT / "feed-en.xml").write_text(feed(lessons, "en"), encoding="utf-8")
    missing = [L["_slug"] for L in lessons if not L.get("_en")]
    if missing:
        print(f"UYARI: İngilizce çevirisi olmayan {len(missing)} ders: {', '.join(missing)}")
    print(f"Tamam: {len(lessons)} ders ({total - len(missing)} İngilizce), {n_terms} terim, {n_films} film.")


if __name__ == "__main__":
    main()
