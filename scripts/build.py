#!/usr/bin/env python3
"""Builds the Film Teorisi site from the content/*.json files.

Usage (from the repo root):  python3 scripts/build.py

Generates: index.html, dersler.html, program.html, sozluk.html, filmler.html,
arsiv.html (redirects to dersler.html), feed.xml and
ders/<slug>.html. See README.md for the lesson content format.
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
SITE_URL = "https://sguven.github.io/film-theory/"
SITE_NAME = "Film Teorisi"
START = dt.date(2026, 10, 5)  # Monday of Week 1 (shifted); Week n = START + 7(n-1)
TOTAL_WEEKS = 52

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
TUR_ETIKET = {"ders": "Ders", "tekrar": "Tekrar", "film": "Film", "sinav": "Test"}

TR_ORDER = "aâbcçdefgğhıiîjklmnoöprsştuûüvyzqwx"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def strip_tags(s):
    return re.sub("<[^>]+>", "", s or "")


def tr_key(s):
    s = (s or "").replace("I", "ı").replace("İ", "i").lower()
    return [TR_ORDER.index(c) if c in TR_ORDER else 100 + ord(c) for c in s]


def tarih_tr(d, gun_adi=False):
    s = f"{d.day} {AYLAR[d.month - 1]} {d.year}"
    return f"{GUNLER[d.weekday()]}, {s}" if gun_adi else s


def today():
    return dt.datetime.now(TZ).date() if TZ else dt.date.today()


def week_of(d):
    if d < START:
        return 1
    return (d - START).days // 7 + 1


def slug(L):
    g = L["gun"]
    return f"hafta-{L['hafta']:02d}-" + ("tekrar" if g == "tekrar" else f"gun-{g}")


def label(L):
    g = L["gun"]
    if g == "tekrar":
        return f"Hafta {L['hafta']} · Tekrar"
    return f"Hafta {L['hafta']} · Gün {g}"


def day_label(L):
    g = L["gun"]
    return "Tekrar" if g == "tekrar" else f"Gün {g}"


def sort_key(L):
    g = L["gun"]
    # The review day comes after Day 5 and before Day 6
    order = 5.5 if g == "tekrar" else float(g)
    return (L["hafta"], order, L["_date"])


# ---------------------------------------------------------------- loading
def load_lessons():
    lessons = []
    for p in sorted((ROOT / "content").glob("*.json")):
        try:
            L = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"HATA: {p.name} geçerli JSON değil: {e}")
        for k in ("hafta", "gun", "tarih", "tur", "baslik"):
            if k not in L:
                sys.exit(f"HATA: {p.name} içinde '{k}' alanı eksik")
        if L["tur"] not in TUR_ETIKET:
            sys.exit(f"HATA: {p.name}: tur ders/tekrar/film/sinav olmalı")
        L["_date"] = dt.date.fromisoformat(L["tarih"])
        L["_slug"] = slug(L)
        for i, q in enumerate(L.get("quiz") or []):
            if not (0 <= q.get("dogru", -1) < len(q.get("secenekler", []))):
                sys.exit(f"HATA: {p.name} quiz sorusu {i+1}: 'dogru' seçenek sırası (0'dan başlar) hatalı")
        lessons.append(L)
    lessons.sort(key=sort_key)
    seen = set()
    for i, L in enumerate(lessons):
        if L["_slug"] in seen:
            sys.exit(f"HATA: aynı ders iki kez var: {L['_slug']}")
        seen.add(L["_slug"])
        L["_n"] = i + 1
    return lessons


def load_program():
    p = ROOT / "data" / "program.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def phase_of(program, week):
    for f in program:
        if f["baslangic"] <= week <= f["bitis"]:
            return f
    return None


def week_info(program, week):
    for f in program:
        for w in f["haftalar"]:
            end = w.get("hafta_bitis") or w["hafta"]
            if w["hafta"] <= week <= end:
                return w
    return None


# ---------------------------------------------------------------- template
def page(title, body, active, depth=0, description="", wide=False):
    up = "../" * depth
    nav = [("index.html", "Son ders", "ana"), ("dersler.html", "Dersler", "dersler"),
           ("program.html", "Program", "program"), ("sozluk.html", "Sözlük", "sozluk"),
           ("filmler.html", "Filmler", "filmler")]
    nav_html = "".join(
        f'<a href="{up}{h}"{" aria-current=\"page\"" if k == active else ""}>{t}</a>' for h, t, k in nav)
    full_title = f"{title} | {SITE_NAME}" if title != SITE_NAME else f"{SITE_NAME}: 52 haftalık okuma programı"
    desc = esc(description or "52 haftalık bir film teorisi programı: günlük kısa dersler, haftalık filmler, testler ve terim sözlüğü.")
    w = "wrap-wide" if wide else "wrap"
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#FAF8F4">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{up}feed.xml">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%232F5D73'/%3E%3Ctext x='16' y='22' font-family='Georgia,serif' font-size='17' text-anchor='middle' fill='%23FAF8F4'%3EFT%3C/text%3E%3C/svg%3E">
</head>
<body>
<a class="skip" href="#icerik">İçeriğe geç</a>
<header class="site-head"><div class="wrap-wide">
<a class="brand" href="{up}index.html">Film Teorisi</a>
<nav class="nav" aria-label="Site">{nav_html}</nav>
</div></header>
<main id="icerik"><div class="{w}">
{body}
</div></main>
<footer class="site-foot"><div class="wrap-wide">
<span>52 haftalık bir film teorisi programı. Dersler her gün Claude ile hazırlanıyor.</span>
<a href="{up}feed.xml">RSS ile takip et</a>
</div></footer>
<script src="{up}assets/site.js" defer></script>
</body>
</html>
"""


def terms_table(terms, with_source=False):
    if not terms:
        return ""
    head = "<th>Türkçe</th><th>English</th><th>Tanım</th>" + ("<th>İlk geçtiği</th>" if with_source else "")
    rows = []
    for t in terms:
        orig = f'<span class="orig">{esc(t["orijinal"])}</span>' if t.get("orijinal") else ""
        src = f'<td class="src">{t["_src"]}</td>' if with_source else ""
        rows.append(f'<tr data-row><td>{esc(t["tr"])}</td><td class="en">{esc(t["en"])}{orig}</td>'
                    f'<td>{esc(t["tanim"])}</td>{src}</tr>')
    return (f'<div class="table-scroll"><table class="terms"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def quiz_block(quiz):
    data = json.dumps(quiz, ensure_ascii=False).replace("</", "<\\/")
    return f"""<section class="box" data-quiz>
<h2>Test</h2>
<p class="meta" style="margin-bottom:0.5rem">Bir seçeneğe dokun; cevap ve açıklama hemen açılır.</p>
<script type="application/json">{data}</script>
<div class="quiz-list"></div>
<div class="quiz-score">Puan: <b class="val"></b> <button type="button" class="btn btn-ghost" data-quiz-reset>Testi sıfırla</button></div>
</section>"""


TUR_UZUN = {"ders": "Okuma", "tekrar": "Tekrar", "film": "Film günü", "sinav": "Sınav günü"}
SLOT_VARSAYILAN = {"1": "Okuma", "2": "Okuma", "3": "Okuma", "4": "Okuma", "5": "Okuma",
                   "tekrar": "Tekrar", "6": "Film", "7": "Sınav"}


def tag(L):
    t = L["tur"]
    return f'<span class="type type-{t}">{TUR_ETIKET[t]}</span>'


# ---------------------------------------------------------------- sayfalar
def week_strip(week, week_lessons, ders_prefix, current=None):
    """Shows the days of the week as a 7-frame film strip."""
    by = {str(x["gun"]): x for x in week_lessons}
    slots = ["1", "2", "3", "4", "5"] + (["tekrar"] if "tekrar" in by else []) + ["6", "7"]
    items = []
    for s in slots:
        num = "T" if s == "tekrar" else s
        x = by.get(s)
        if x:
            title = esc(f'{day_label(x)}: {x["baslik"]}')
            cur = ' aria-current="page"' if x is current else ""
            items.append(f'<a href="{ders_prefix}{x["_slug"]}.html" title="{title}"{cur}>{num}</a>')
        else:
            items.append(f'<span title="Henüz yayımlanmadı">{num}</span>')
    return (f'<nav class="days" aria-label="Hafta {week} günleri"><span class="days-label">Bu haftanın günleri</span>'
            f'{"".join(items)}</nav>')


def lesson_header(L, program, up, latest=False):
    wi = week_info(program, L["hafta"])
    week_title = f"Hafta {L['hafta']}" + (f": {wi['baslik']}" if wi else "")
    when = ("En güncel ders, " if latest else "") + tarih_tr(L["_date"])
    meta = []
    if L.get("okuma"):
        meta.append(f"<span>Okuma: {esc(L['okuma'])}</span>")
    if L.get("film"):
        meta.append(f"<span>Haftanın filmi: <i>{esc(L['film'])}</i></span>")
    if L.get("pdf"):
        meta.append(f'<span><a href="{up}pdf/{esc(L["pdf"])}">PDF olarak indir</a></span>')
    meta_html = f'<p class="meta">{"".join(meta)}</p>' if meta else ""
    return (f'<header class="lesson-head">'
            f'<p class="eyebrow"><a href="{up}dersler.html#hafta-{L["hafta"]}">{esc(week_title)}</a>'
            f'<span>{esc(day_label(L))}, {esc(TUR_UZUN[L["tur"]].lower())}</span></p>'
            f'<h1>{esc(L["baslik"])}</h1><p class="date">{esc(when)}</p>{meta_html}</header>')


def lesson_body(L, prev, nxt, program, ders_prefix, up, week_lessons, latest=False, total=0):
    """Lesson content. ders_prefix: prefix of the path to lesson pages ("" from inside ders/, "ders/" from the root)."""
    parts = [lesson_header(L, program, up, latest)]
    parts.append(week_strip(L["hafta"], week_lessons, ders_prefix, current=L))
    if L.get("tek_cumle"):
        parts.append(f'<p class="lead"><span class="lead-label">Bugünün tek cümlesi</span>{L["tek_cumle"]}</p>')
    for b in L.get("bolumler", []):
        if b.get("baslik"):
            parts.append(f'<h2>{esc(b["baslik"])}</h2>')
        parts.append(b.get("html", ""))
    if L.get("quiz"):
        parts.append(quiz_block(L["quiz"]))
    if L.get("sorular"):
        title = L.get("soru_baslik") or "Bugünün soruları"
        items = "".join(f"<li>{q}</li>" for q in L["sorular"])
        hints = ""
        if L.get("ipuclari"):
            hi = "".join(f"<li>{h}</li>" for h in L["ipuclari"])
            hints = f"<details><summary>Cevap ipuçları (önce kendin dene)</summary><ol>{hi}</ol></details>"
        parts.append(f'<section class="box box-accent"><h2>{esc(title)}</h2><ol>{items}</ol>{hints}</section>')
    if L.get("analiz"):
        parts.append(f'<section class="box"><h2>Analiz görevi</h2>{L["analiz"]}</section>')
    if L.get("gozlem"):
        parts.append(f'<section class="box"><h2>Gözlem görevi <small class="muted-small">2 dakika</small></h2><p>{L["gozlem"]}</p></section>')
    if L.get("terimler"):
        parts.append("<h2>Bugünün terimleri</h2>" + terms_table(L["terimler"]))
    if L.get("yarin"):
        parts.append(f'<h2>Sıradaki ders</h2><p>{L["yarin"]}</p>')
    links = []
    if prev:
        links.append(f'<a class="prev" href="{ders_prefix}{prev["_slug"]}.html"><small>Önceki ders</small>'
                     f'<span>{esc(label(prev))}</span><b>{esc(prev["baslik"])}</b></a>')
    else:
        links.append("<span></span>")
    if nxt:
        links.append(f'<a class="next" href="{ders_prefix}{nxt["_slug"]}.html"><small>Sonraki ders</small>'
                     f'<span>{esc(label(nxt))}</span><b>{esc(nxt["baslik"])}</b></a>')
    else:
        links.append(f'<a class="next" href="{up}dersler.html"><small>Yeni ders her gün ekleniyor</small>'
                     f'<span>Arşiv</span><b>Bütün derslere göz at</b></a>')
    parts.append(f'<nav class="pager" aria-label="Ders gezinme">{"".join(links)}</nav>')
    return "\n".join(parts)


def latest_of(lessons):
    return max(lessons, key=lambda x: (x["_date"], sort_key(x))) if lessons else None


def lesson_page(L, prev, nxt, program, lessons):
    wl = [x for x in lessons if x["hafta"] == L["hafta"]]
    body = lesson_body(L, prev, nxt, program, ders_prefix="", up="../", week_lessons=wl,
                       latest=L is latest_of(lessons), total=len(lessons))
    return page(f'{label(L)}: {L["baslik"]}', body, "dersler", depth=1,
                description=strip_tags(L.get("tek_cumle")))


def index_page(lessons, program):
    if not lessons:
        return page(SITE_NAME, "<h1>İlk ders yakında</h1>", "ana")
    L = latest_of(lessons)
    i = lessons.index(L)
    prev = lessons[i - 1] if i > 0 else None
    nxt = lessons[i + 1] if i + 1 < len(lessons) else None
    wl = [x for x in lessons if x["hafta"] == L["hafta"]]
    body = lesson_body(L, prev, nxt, program, ders_prefix="ders/", up="", week_lessons=wl,
                       latest=True, total=len(lessons))
    return page(SITE_NAME, body, "ana", description=strip_tags(L.get("tek_cumle")))


def lesson_rows(lessons, prefix=""):
    items = []
    for L in lessons:
        one = f'<p class="one">{L["tek_cumle"]}</p>' if L.get("tek_cumle") else ""
        items.append(
            f'<li><a class="row" href="{prefix}ders/{L["_slug"]}.html">'
            f'<span class="when"><b>{esc(day_label(L))}</b><span>{TUR_UZUN[L["tur"]]}</span></span>'
            f'<span class="what"><span class="title">{esc(L["baslik"])}</span>{one}</span></a></li>')
    return f'<ul class="lessons">{"".join(items)}</ul>'


def group_weeks(lessons):
    weeks = {}
    for L in lessons:
        weeks.setdefault(L["hafta"], []).append(L)
    return weeks


def dersler_page(lessons, program):
    weeks = group_weeks(lessons)
    parts = ['<h1 class="page-title">Dersler</h1>']
    if lessons:
        first = lessons[0]
        latest = latest_of(lessons)
        parts.append('<div class="jump">'
                     f'<a class="btn" href="ders/{latest["_slug"]}.html">En güncel derse git</a>'
                     f'<a class="btn btn-ghost" href="ders/{first["_slug"]}.html">Programın ilk dersi</a></div>')
        parts.append('<p class="intro">Haftalar en yenisi üstte olacak şekilde sıralı. Her hafta beş okuma günü, '
                     'bir film günü ve bir sınav gününden oluşuyor.</p>')
    else:
        parts.append('<p class="empty">Henüz ders yok.</p>')
    for w in sorted(weeks, reverse=True):
        wi = week_info(program, w)
        title = wi["baslik"] if wi else ""
        film = f'<p class="week-film">Haftanın filmi: <i>{esc(wi["film"])}</i></p>' if wi and wi.get("film") else ""
        parts.append(f'<section class="week" id="hafta-{w}"><h2>Hafta {w}: {esc(title)}</h2>{film}'
                     f'{lesson_rows(weeks[w])}</section>')
    return page("Dersler", "\n".join(parts), "dersler")


def redirect_page(target):
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}">
<title>{SITE_NAME}</title></head><body><a href="{target}">{target}</a></body></html>
"""


def program_page(program, lessons):
    t = today()
    wk = week_of(t)
    have = {L["hafta"] for L in lessons}
    parts = ['<h1 class="page-title">Program</h1>',
             '<p class="intro">52 hafta, 9 faz. Film dilinden başlayıp klasik teoriye, auteur ve türe, göstergebilim ve '
             'psikanalize, bilişsel kurama, belgesele, dijital sinemaya ve Türkiye sinemasına uzanıyor. Her faz bir '
             'öncekinin üstüne kurulu. Dersleri yayımlanmış haftalara tıklayabilirsin.</p>']
    for f in program:
        parts.append(f'<section class="phase"><p class="kicker">Faz {esc(f["faz"])}, Hafta {f["baslangic"]}–{f["bitis"]}</p>'
                     f'<h2>{esc(f["ad"])}</h2><p class="desc">{esc(f["aciklama"])}</p><ul class="weeks">')
        for w in f["haftalar"]:
            end = w.get("hafta_bitis") or w["hafta"]
            wn = f"Hafta {w['hafta']}" + (f"–{end}" if end != w["hafta"] else "")
            cls = "now" if w["hafta"] <= wk <= end else ("done" if end < wk else "")
            tg = '<span class="tag">Yayında</span>' if w["hafta"] in have else ""
            title = esc(w["baslik"])
            if w["hafta"] in have:
                title = f'<a href="dersler.html#hafta-{w["hafta"]}">{title}</a>'
            film = f'<span class="film">{esc(w["film"])}</span>' if w.get("film") else ""
            parts.append(f'<li class="{cls}"><span class="wn">{wn}</span><span><span class="wt">{title}</span>{tg}{film}</span></li>')
        parts.append("</ul></section>")
    return page("Program", "\n".join(parts), "program")


def collect_terms(lessons):
    seen = {}
    for L in lessons:
        for t in L.get("terimler") or []:
            key = (t.get("tr") or "").strip().lower()
            if not key or key in seen:
                continue
            t = dict(t)
            t["_src"] = f'<a href="ders/{L["_slug"]}.html">{esc(label(L))}</a>'
            seen[key] = t
    return sorted(seen.values(), key=lambda t: tr_key(t["tr"]))


def glossary_page(terms):
    parts = ['<h1 class="page-title">Sözlük</h1>',
             f'<p class="intro">Derslerde geçen {len(terms)} terim: Türkçesi, İngilizcesi (gerekirse orijinal dili) ve tek '
             'cümlelik tanımı. Her terim ilk geçtiği derse bağlanıyor.</p>',
             '<input class="search" type="search" placeholder="Terim ara (Türkçe ya da İngilizce)…" data-filter aria-label="Terim ara">']
    parts.append(terms_table(terms, with_source=True))
    parts.append('<p class="empty" data-empty hidden>Bu aramayla eşleşen terim yok.</p>')
    return page("Sözlük", "\n".join(parts), "sozluk")


def collect_films(lessons):
    films = {}
    for L in lessons:
        for f in L.get("filmler") or []:
            key = re.sub(r"\W+", "", (f.get("ad") or "").lower())
            if not key:
                continue
            if key not in films:
                films[key] = {**f, "_refs": []}
            ref = f'<a href="ders/{L["_slug"]}.html">{esc(label(L))}</a>'
            if ref not in films[key]["_refs"]:
                films[key]["_refs"].append(ref)
            if f.get("not") and not films[key].get("not"):
                films[key]["not"] = f["not"]
    return list(films.values())


def films_page(films):
    parts = ['<h1 class="page-title">Filmler</h1>',
             '<p class="intro">Haftanın filmleri ve derslerde örnek olarak açılan filmler. Programdaki bütün filmlerin '
             'listesi <a href="program.html">Program</a> sayfasında.</p>']
    if not films:
        parts.append('<p class="empty">Henüz film yok.</p>')
    for f in films:
        bits = [str(f[k]) for k in ("yonetmen", "yil") if f.get(k)]
        meta = ", ".join(bits)
        note = f'<p style="margin:0.3rem 0 0.4rem">{f["not"]}</p>' if f.get("not") else ""
        parts.append(f'<div class="film-card"><h3><i>{esc(f["ad"])}</i></h3>'
                     f'<div class="fmeta">{esc(meta)}</div>{note}'
                     f'<div class="fmeta">Geçtiği dersler: {", ".join(f["_refs"])}</div></div>')
    return page("Filmler", "\n".join(parts), "filmler")


def feed(lessons):
    items = []
    for L in sorted(lessons, key=lambda x: x["_date"], reverse=True)[:30]:
        link = f"{SITE_URL}ders/{L['_slug']}.html"
        d = dt.datetime.combine(L["_date"], dt.time(15, 0))
        pub = d.strftime("%a, %d %b %Y %H:%M:%S -0400")
        desc = strip_tags(L.get("tek_cumle"))
        items.append(f"<item><title>{esc(label(L) + ': ' + L['baslik'])}</title><link>{link}</link>"
                     f"<guid>{link}</guid><pubDate>{pub}</pubDate><description>{esc(desc)}</description></item>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>{SITE_NAME}</title><link>{SITE_URL}</link>"
            "<description>52 haftalık film teorisi programının günlük dersleri</description><language>tr</language>"
            + "".join(items) + "</channel></rss>\n")


def main():
    lessons = load_lessons()
    program = load_program()
    terms = collect_terms(lessons)
    films = collect_films(lessons)
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
    (ROOT / "index.html").write_text(index_page(lessons, program), encoding="utf-8")
    (ROOT / "dersler.html").write_text(dersler_page(lessons, program), encoding="utf-8")
    (ROOT / "arsiv.html").write_text(redirect_page("dersler.html"), encoding="utf-8")
    (ROOT / "program.html").write_text(program_page(program, lessons), encoding="utf-8")
    (ROOT / "sozluk.html").write_text(glossary_page(terms), encoding="utf-8")
    (ROOT / "filmler.html").write_text(films_page(films), encoding="utf-8")
    (ROOT / "feed.xml").write_text(feed(lessons), encoding="utf-8")
    print(f"Tamam: {len(lessons)} ders, {len(terms)} terim, {len(films)} film.")


if __name__ == "__main__":
    main()
