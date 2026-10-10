#!/usr/bin/env python3
"""Film Teorisi sitesini content/*.json dosyalarından üretir.

Kullanım (repo kökünden):  python3 scripts/build.py

Üretilenler: index.html, program.html, arsiv.html, sozluk.html, filmler.html,
feed.xml ve ders/<slug>.html. Ders içeriğinin biçimi için README.md'ye bak.
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
SITE_NAME = "Film Teorisi"
START = dt.date(2026, 10, 5)  # Hafta 1'in (kaydırılmış) ilk günü; Hafta n = START + 7(n-1)
TOTAL_WEEKS = 52

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
TUR_ETIKET = {"ders": "Ders", "tekrar": "Tekrar günü", "film": "Film günü", "sinav": "Sınav günü"}

TR_ORDER = "aâbcçdefgğhıiîjklmnoöprsştuûüvyzqwx"


def esc(s):
    return html.escape(str(s or ""), quote=True)


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
        return f"Hafta {L['hafta']} · Tekrar günü"
    return f"Hafta {L['hafta']} · Gün {g}"


# ---------------------------------------------------------------- yükleme
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
    lessons.sort(key=lambda L: (L["_date"], L["_slug"]))
    seen = {}
    for L in lessons:
        if L["_slug"] in seen:
            sys.exit(f"HATA: aynı ders iki kez var: {L['_slug']}")
        seen[L["_slug"]] = L
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


# ---------------------------------------------------------------- şablon
def page(title, body, active, depth=0, description="", wide=False):
    up = "../" * depth
    nav = [("index.html", "Bugün", "bugun"), ("program.html", "Program", "program"),
           ("arsiv.html", "Arşiv", "arsiv"), ("sozluk.html", "Sözlük", "sozluk"),
           ("filmler.html", "Filmler", "filmler")]
    nav_html = "".join(
        f'<a href="{up}{h}"{" class=\"active\"" if k == active else ""}>{t}</a>' for h, t, k in nav)
    full_title = f"{title} · {SITE_NAME}" if title != SITE_NAME else SITE_NAME
    desc = esc(description or "52 haftalık bir film teorisi okuma programının günlük dersleri, sınavları ve terim sözlüğü.")
    w = "wrap-wide" if wide else "wrap"
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{up}feed.xml">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%238b2a1e'/%3E%3Ccircle cx='16' cy='16' r='9' fill='none' stroke='%23f5f0e6' stroke-width='2.5'/%3E%3Ccircle cx='16' cy='16' r='2.5' fill='%23f5f0e6'/%3E%3C/svg%3E">
</head>
<body>
<header class="site-head"><div class="wrap-wide">
<a class="brand" href="{up}index.html">Film <span>Teorisi</span></a>
<nav class="nav">{nav_html}</nav>
</div></header>
<main><div class="{w}">
{body}
</div></main>
<footer class="site-foot"><div class="wrap-wide">
<span>52 haftalık bir film teorisi programı · Dersler Claude ile hazırlanır.</span>
<span><a href="{up}feed.xml">RSS</a></span>
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
<div class="quiz-score">Puan: <b class="val"></b> <button type="button" class="btn btn-ghost" data-quiz-reset>Baştan başla</button></div>
</section>"""


# ---------------------------------------------------------------- sayfalar
def lesson_page(L, prev, nxt):
    d = L["_date"]
    parts = [f'<p class="kicker">{esc(label(L))} · {esc(tarih_tr(d, True))}</p>',
             f'<h1>{esc(L["baslik"])}</h1>']
    meta = []
    if L.get("okuma"):
        meta.append(f"<b>Okuma:</b> {esc(L['okuma'])}")
    if L.get("film"):
        meta.append(f"<b>Haftanın filmi:</b> <i>{esc(L['film'])}</i>")
    if L.get("pdf"):
        meta.append(f'<a class="pdf-link" href="../pdf/{esc(L["pdf"])}">PDF olarak indir</a>')
    if meta:
        parts.append(f'<p class="meta">{" · ".join(meta)}</p>')
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
        parts.append(f'<section class="box"><h2>Gözlem görevi <small style="font-family:var(--sans);font-size:0.8rem;color:var(--muted);font-weight:400">2 dakika</small></h2><p>{L["gozlem"]}</p></section>')
    if L.get("terimler"):
        parts.append("<h2>Bugünün terimleri</h2>" + terms_table(L["terimler"]))
    if L.get("yarin"):
        parts.append(f'<h2>Sırada</h2><p>{L["yarin"]}</p>')
    pv = (f'<a href="{prev["_slug"]}.html"><small>← Önceki</small>{esc(label(prev))}: {esc(prev["baslik"])}</a>'
          if prev else "<span></span>")
    nx = (f'<a class="next" href="{nxt["_slug"]}.html"><small>Sonraki →</small>{esc(label(nxt))}: {esc(nxt["baslik"])}</a>'
          if nxt else "<span></span>")
    parts.append(f'<nav class="pager">{pv}{nx}</nav>')
    desc = re.sub("<[^>]+>", "", L.get("tek_cumle") or "")
    return page(f'{label(L)}: {L["baslik"]}', "\n".join(parts), "arsiv", depth=1, description=desc)


def lesson_list(lessons, upcoming=()):
    items = []
    for L in lessons:
        one = f'<div class="one">{L["tek_cumle"]}</div>' if L.get("tek_cumle") else ""
        items.append(f'<li><div class="when"><b>{esc(label(L))}</b>{esc(tarih_tr(L["_date"]))}</div>'
                     f'<div><a class="title" href="ders/{L["_slug"]}.html">{esc(L["baslik"])}</a>{one}</div></li>')
    for when, what in upcoming:
        items.append(f'<li class="upcoming"><div class="when"><b>{esc(when[0])}</b>{esc(when[1])}</div>'
                     f'<div><span class="title">{esc(what)}</span></div></li>')
    return f'<ul class="list">{"".join(items)}</ul>'


def index_page(lessons, program, terms, films):
    t = today()
    wk = min(week_of(t), TOTAL_WEEKS)
    ph = phase_of(program, wk)
    wi = week_info(program, wk)
    parts = []
    pct = round(100 * (wk - 1 + (t - (START + dt.timedelta(days=7 * (wk - 1)))).days / 7) / TOTAL_WEEKS, 1) if t >= START else 0
    ph_txt = f" · Faz {ph['faz']}: {ph['ad']}" if ph else ""
    parts.append(f'<p class="kicker">Hafta {wk} / {TOTAL_WEEKS}{esc(ph_txt)}</p>')
    parts.append(f'<div class="progress" aria-label="Program ilerlemesi"><span style="width:{max(pct, 1)}%"></span></div>')
    if lessons:
        L = lessons[-1]
        is_today = L["_date"] == t
        when = "Bugünün dersi" if is_today else f"Son ders · {tarih_tr(L['_date'])}"
        parts.append('<section class="hero">')
        parts.append(f'<p class="kicker" style="color:var(--muted)">{esc(when)} · {esc(label(L))}</p>')
        parts.append(f'<h1><a href="ders/{L["_slug"]}.html">{esc(L["baslik"])}</a></h1>')
        if L.get("tek_cumle"):
            parts.append(f'<p class="lead">{L["tek_cumle"]}</p>')
        parts.append(f'<a class="btn" href="ders/{L["_slug"]}.html">Dersi oku</a>')
        parts.append('</section>')
    else:
        parts.append("<h1>Program yakında başlıyor</h1>")
    # bu hafta
    this_week = [L for L in lessons if L["hafta"] == wk]
    upcoming = []
    week_start = START + dt.timedelta(days=7 * (wk - 1))
    have_dates = {L["_date"] for L in this_week}
    for i in range(7):
        d = week_start + dt.timedelta(days=i)
        if d > t and d not in have_dates:
            what = {5: "Film günü", 6: "Sınav günü"}.get(i, "Okuma günü")
            upcoming.append(((GUNLER[i], tarih_tr(d)), what))
    title = f"Bu hafta: {wi['baslik']}" if wi else "Bu hafta"
    parts.append(f"<h2>{esc(title)}</h2>")
    if wi and wi.get("film"):
        parts.append(f'<p class="meta">Haftanın filmi: <i>{esc(wi["film"])}</i></p>')
    parts.append(lesson_list(this_week, upcoming))
    if len(lessons) > len(this_week):
        parts.append('<p style="margin-top:1rem;font-family:var(--sans);font-size:0.9rem"><a href="arsiv.html">Tüm dersler →</a></p>')
    parts.append(f'<div class="stats"><div class="stat"><b>{len(lessons)}</b><span>ders</span></div>'
                 f'<div class="stat"><b>{len(terms)}</b><span>terim</span></div>'
                 f'<div class="stat"><b>{len(films)}</b><span>film</span></div></div>')
    parts.append('<h2>Bu site nedir?</h2><p>Kendi kendine yürüttüğüm 52 haftalık bir film teorisi programının '
                 'defteri. Her gün kısa bir ders (10–15 dakikalık okuma), cumartesileri haftanın filmi için izleme '
                 'rehberi, pazarları bir test ve analiz görevi yayımlanıyor. Program Bordwell ve Thompson\'ın film '
                 'dilinden başlayıp klasik teori, auteur ve tür, göstergebilim ve psikanaliz, bilişsel kuram, belgesel, '
                 'dijital sinema ve Türkiye sinemasına uzanıyor. <a href="program.html">Programın tamamı</a>.</p>')
    return page(SITE_NAME, "\n".join(parts), "bugun")


def archive_page(lessons):
    parts = ['<p class="kicker">Arşiv</p>', "<h1>Bütün dersler</h1>"]
    if not lessons:
        parts.append('<p class="empty">Henüz ders yok.</p>')
    weeks = {}
    for L in lessons:
        weeks.setdefault(L["hafta"], []).append(L)
    for w in sorted(weeks, reverse=True):
        parts.append(f"<h2>Hafta {w}</h2>")
        parts.append(lesson_list(weeks[w]))
    return page("Arşiv", "\n".join(parts), "arsiv")


def program_page(program, lessons):
    t = today()
    wk = week_of(t)
    have = {}
    for L in lessons:
        have.setdefault(L["hafta"], L)
    parts = ['<p class="kicker">Program</p>', "<h1>52 hafta, 9 faz</h1>",
             '<p>Her hafta beş kısa okuma günü, bir film günü ve bir sınav günü var. Sıra hem kronolojik hem '
             'kavramsal: her faz bir öncekinin üstüne kurulur.</p>']
    for f in program:
        parts.append(f'<section class="phase"><p class="kicker">Faz {esc(f["faz"])} · Hafta {f["baslangic"]}–{f["bitis"]}</p>'
                     f'<h2>{esc(f["ad"])}</h2><p class="desc">{esc(f["aciklama"])}</p><ul class="weeks">')
        for w in f["haftalar"]:
            end = w.get("hafta_bitis") or w["hafta"]
            wn = f"Hafta {w['hafta']}" + (f"–{end}" if end != w["hafta"] else "")
            cls = "now" if w["hafta"] <= wk <= end else ("done" if end < wk else "")
            tag = '<span class="tag">Bu hafta</span>' if cls == "now" else ""
            title = esc(w["baslik"])
            if w["hafta"] in have:
                title = f'<a href="arsiv.html">{title}</a>'
            film = f'<span class="film">{esc(w["film"])}</span>' if w.get("film") else ""
            parts.append(f'<li class="{cls}"><span class="wn">{wn}</span><span><span class="wt">{title}</span>{tag}{film}</span></li>')
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
    parts = ['<p class="kicker">Sözlük</p>', "<h1>Terimler</h1>",
             '<p>Derslerde geçen bütün terimler; Türkçe karşılık, İngilizce (gerekirse orijinal dil) ve tek cümlelik tanım. '
             'Her terim ilk geçtiği derse bağlanır.</p>',
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
    parts = ['<p class="kicker">Filmler</p>', "<h1>Derslerde konuşulan filmler</h1>",
             '<p>Haftanın filmleri ve derslerde örnek olarak açılan filmler. Programdaki bütün film listesi '
             '<a href="program.html">Program</a> sayfasında.</p>']
    if not films:
        parts.append('<p class="empty">Henüz film yok.</p>')
    for f in films:
        bits = [str(f[k]) for k in ("yonetmen", "yil") if f.get(k)]
        meta = " · ".join(bits)
        note = f'<p style="margin:0.3rem 0 0.4rem">{f["not"]}</p>' if f.get("not") else ""
        parts.append(f'<div class="film-card"><h3><i>{esc(f["ad"])}</i></h3>'
                     f'<div class="fmeta">{esc(meta)}</div>{note}'
                     f'<div class="fmeta">Geçtiği dersler: {", ".join(f["_refs"])}</div></div>')
    return page("Filmler", "\n".join(parts), "filmler")


def feed(lessons):
    items = []
    for L in reversed(lessons[-30:]):
        link = f"{SITE_URL}ders/{L['_slug']}.html"
        d = dt.datetime.combine(L["_date"], dt.time(15, 0))
        pub = d.strftime("%a, %d %b %Y %H:%M:%S -0400")
        desc = re.sub("<[^>]+>", "", L.get("tek_cumle") or "")
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
    for i, L in enumerate(lessons):
        prev = lessons[i - 1] if i > 0 else None
        nxt = lessons[i + 1] if i + 1 < len(lessons) else None
        f = out / f"{L['_slug']}.html"
        f.write_text(lesson_page(L, prev, nxt), encoding="utf-8")
        keep.add(f.name)
    for f in out.glob("*.html"):
        if f.name not in keep:
            f.unlink()
    (ROOT / "index.html").write_text(index_page(lessons, program, terms, films), encoding="utf-8")
    (ROOT / "arsiv.html").write_text(archive_page(lessons), encoding="utf-8")
    (ROOT / "program.html").write_text(program_page(program, lessons), encoding="utf-8")
    (ROOT / "sozluk.html").write_text(glossary_page(terms), encoding="utf-8")
    (ROOT / "filmler.html").write_text(films_page(films), encoding="utf-8")
    (ROOT / "feed.xml").write_text(feed(lessons), encoding="utf-8")
    print(f"Tamam: {len(lessons)} ders, {len(terms)} terim, {len(films)} film.")


if __name__ == "__main__":
    main()
