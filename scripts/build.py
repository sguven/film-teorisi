#!/usr/bin/env python3
"""Film Teorisi sitesini content/*.json dosyalarından üretir.

Kullanım (repo kökünden):  python3 scripts/build.py

Üretilenler: index.html, dersler.html, program.html, sozluk.html, filmler.html,
arsiv.html (dersler.html'e yönlendirir), feed.xml, assets/manifest.js ve
ders/<slug>.html. Ders içeriğinin biçimi için README.md'ye bak.
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
START = dt.date(2026, 10, 5)  # Hafta 1'in (kaydırılmış) Pazartesi'si; Hafta n = START + 7(n-1)
TOTAL_WEEKS = 52

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
TUR_ETIKET = {"ders": "Okuma", "tekrar": "Tekrar", "film": "Film", "sinav": "Test"}

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
    # Tekrar günü Gün 5'ten sonra, Gün 6'dan önce gelir
    order = 5.5 if g == "tekrar" else float(g)
    return (L["hafta"], order, L["_date"])


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


# ---------------------------------------------------------------- şablon
def page(title, body, active, depth=0, description="", wide=False):
    up = "../" * depth
    nav = [("index.html", "Ana sayfa", "ana"), ("dersler.html", "Dersler", "dersler"),
           ("program.html", "Program", "program"), ("sozluk.html", "Sözlük", "sozluk"),
           ("filmler.html", "Filmler", "filmler")]
    nav_html = "".join(
        f'<a href="{up}{h}"{" class=\"active\"" if k == active else ""}>{t}</a>' for h, t, k in nav)
    full_title = f"{title} · {SITE_NAME}" if title != SITE_NAME else f"{SITE_NAME} · 52 haftalık okuma programı"
    desc = esc(description or "52 haftalık, baştan sona izlenebilen bir film teorisi programı: günlük kısa dersler, haftalık filmler, testler ve terim sözlüğü.")
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
<body data-root="{up}">
<header class="site-head"><div class="wrap-wide">
<a class="brand" href="{up}index.html">Film <span>Teorisi</span></a>
<nav class="nav">{nav_html}</nav>
</div></header>
<main><div class="{w}">
{body}
</div></main>
<footer class="site-foot"><div class="wrap-wide">
<span>52 haftalık bir film teorisi programı · Dersler Claude ile hazırlanır. İlerlemen yalnızca bu tarayıcıda saklanır.</span>
<span><a href="{up}feed.xml">RSS</a></span>
</div></footer>
<script src="{up}assets/manifest.js"></script>
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


def tag(L):
    t = L["tur"]
    return f'<span class="type type-{t}">{TUR_ETIKET[t]}</span>'


# ---------------------------------------------------------------- sayfalar
def lesson_page(L, prev, nxt, total, program):
    wi = week_info(program, L["hafta"])
    week_title = f": {wi['baslik']}" if wi else ""
    pct = round(100 * L["_n"] / max(total, 1), 1)
    parts = [
        f'<p class="crumb"><a href="../dersler.html#hafta-{L["hafta"]}">Hafta {L["hafta"]}{esc(week_title)}</a>'
        f' <span aria-hidden="true">›</span> {esc(day_label(L))} {tag(L)}</p>',
        f'<h1>{esc(L["baslik"])}</h1>',
        f'<div class="seq"><span>Ders {L["_n"]} / {total}</span><span data-read-badge hidden>✓ Okundu</span></div>'
        f'<div class="progress thin"><span style="width:{pct}%"></span></div>',
    ]
    meta = []
    if L.get("okuma"):
        meta.append(f"<b>Okuma:</b> {esc(L['okuma'])}")
    if L.get("film"):
        meta.append(f"<b>Haftanın filmi:</b> <i>{esc(L['film'])}</i>")
    meta.append(f"Yayın: {esc(tarih_tr(L['_date']))}")
    if L.get("pdf"):
        meta.append(f'<a class="pdf-link" href="../pdf/{esc(L["pdf"])}">PDF indir</a>')
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
        title = L.get("soru_baslik") or "Düşünme soruları"
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
        parts.append("<h2>Bu dersin terimleri</h2>" + terms_table(L["terimler"]))
    if L.get("yarin"):
        parts.append(f'<h2>Sıradaki ders</h2><p>{L["yarin"]}</p>')
    # bitiş kutusu
    if nxt:
        finish = (f'<section class="finish"><p class="finish-text">Dersi bitirdin mi?</p>'
                  f'<a class="btn btn-big" href="{nxt["_slug"]}.html" data-mark-read="{L["_slug"]}">Okudum, sonraki derse geç →</a>'
                  f'<p class="finish-next">Sıradaki: <b>{esc(label(nxt))}</b> · {esc(nxt["baslik"])}</p></section>')
    else:
        finish = (f'<section class="finish"><p class="finish-text">Bu, şu ana kadar yayımlanan son ders. Yeni dersler her gün ekleniyor.</p>'
                  f'<button type="button" class="btn btn-big" data-mark-read="{L["_slug"]}">Okudum ✓</button>'
                  f'<p class="finish-next"><a href="../dersler.html">Bütün derslere dön</a></p></section>')
    parts.append(finish)
    pv = (f'<a href="{prev["_slug"]}.html"><small>← Önceki</small>{esc(label(prev))}</a>' if prev else "<span></span>")
    nx = (f'<a class="next" href="{nxt["_slug"]}.html"><small>Sonraki →</small>{esc(label(nxt))}</a>' if nxt else "<span></span>")
    parts.append(f'<nav class="pager">{pv}<a class="mid" href="../dersler.html#hafta-{L["hafta"]}"><small>Dersler</small>Hafta {L["hafta"]}</a>{nx}</nav>')
    desc = strip_tags(L.get("tek_cumle"))
    body = "\n".join(parts)
    return page(f'{label(L)}: {L["baslik"]}', f'<article data-lesson="{L["_slug"]}">{body}</article>',
                "dersler", depth=1, description=desc)


def lesson_rows(lessons, prefix=""):
    items = []
    for L in lessons:
        one = f'<div class="one">{L["tek_cumle"]}</div>' if L.get("tek_cumle") else ""
        items.append(
            f'<li data-slug="{L["_slug"]}"><span class="check" aria-hidden="true"></span>'
            f'<div class="when"><b>{esc(day_label(L))}</b>{tag(L)}</div>'
            f'<div><a class="title" href="{prefix}ders/{L["_slug"]}.html">{esc(L["baslik"])}</a>{one}</div></li>')
    return f'<ul class="list lessons">{"".join(items)}</ul>'


def group_weeks(lessons):
    weeks = {}
    for L in lessons:
        weeks.setdefault(L["hafta"], []).append(L)
    return weeks


def dersler_page(lessons, program):
    weeks = group_weeks(lessons)
    total = len(lessons)
    parts = ['<p class="kicker">Dersler</p>', "<h1>Baştan sona bütün dersler</h1>",
             f'<p>Dersler programdaki sırayla dizili. Her hafta beş kısa okuma, bir tekrar ya da film günü ve bir test var. '
             f'Okuduğun dersler bu tarayıcıda işaretlenir; istediğin zaman kaldığın yerden devam edebilirsin.</p>',
             f'<div class="progress-row"><div class="progress"><span data-overall-bar style="width:0%"></span></div>'
             f'<span class="progress-label"><b data-overall-count>0</b> / {total} ders okundu</span></div>',
             (f'<p><a class="btn" href="ders/{lessons[0]["_slug"]}.html" data-continue-link>Baştan başla →</a></p>' if lessons else '')]
    if not lessons:
        parts.append('<p class="empty">Henüz ders yok.</p>')
    # haftalara hızlı geçiş
    if len(weeks) > 1:
        chips = "".join(f'<a class="chip" href="#hafta-{w}">Hafta {w}</a>' for w in sorted(weeks))
        parts.append(f'<nav class="chips">{chips}</nav>')
    for w in sorted(weeks):
        wi = week_info(program, w)
        ph = phase_of(program, w)
        title = wi["baslik"] if wi else ""
        film = f'<p class="meta" style="margin-bottom:0.6rem">Haftanın filmi: <i>{esc(wi["film"])}</i></p>' if wi and wi.get("film") else ""
        ph_txt = f'Faz {ph["faz"]} · {esc(ph["ad"])}' if ph else ""
        parts.append(f'<section class="week" id="hafta-{w}"><p class="kicker" style="margin-top:2.4rem">{ph_txt}</p>'
                     f'<div class="week-head"><h2>Hafta {w}: {esc(title)}</h2>'
                     f'<span class="week-count" data-week-count="{w}" data-week-total="{len(weeks[w])}"></span></div>{film}'
                     f'{lesson_rows(weeks[w])}</section>')
    parts.append('<p class="reset-row"><button type="button" class="linklike" data-reset-progress>İlerlememi sıfırla</button></p>')
    return page("Dersler", "\n".join(parts), "dersler")


def index_page(lessons, program, terms, films):
    t = today()
    wk = min(week_of(t), TOTAL_WEEKS)
    weeks = group_weeks(lessons)
    total = len(lessons)
    first = lessons[0] if lessons else None
    parts = []
    # karşılama
    parts.append('<section class="welcome">')
    parts.append('<p class="kicker">52 haftalık bir okuma programı</p>')
    parts.append('<h1 class="display">Film teorisini baştan, adım adım öğren.</h1>')
    parts.append('<p class="intro">Bordwell ve Thompson\'ın film dilinden başlayıp Eisenstein ve Bazin\'e, auteur kuramına, '
                 'göstergebilim ve psikanalize, Deleuze\'e, belgesele, dijital sinemaya ve Türkiye sinemasına uzanan bir yol. '
                 'Her ders 10–15 dakikalık bir okuma; her hafta bir film ve kısa bir test.</p>')
    if first:
        parts.append(f'<div class="cta" data-cta>'
                     f'<a class="btn btn-big" href="ders/{first["_slug"]}.html" data-continue-link>Baştan başla: {esc(label(first))} →</a>'
                     f'<a class="btn btn-ghost" href="ders/{first["_slug"]}.html" data-start-link hidden>Baştan başla</a>'
                     f'</div><p class="cta-note" data-continue-note>İlk ders: {esc(first["baslik"])}</p>')
    parts.append('</section>')
    # nasıl çalışır
    parts.append('<section class="how"><h2>Nasıl çalışır?</h2><ol class="steps">'
                 '<li><b>Her gün bir ders.</b> Pazartesiden cumaya 10–15 dakikalık kısa bir okuma: bir kuramcının ana iddiası, '
                 'neye karşı çıktığı ve bir film sahnesi üzerinden örneği.</li>'
                 '<li><b>Cumartesi film.</b> Haftanın filmi için spoiler vermeyen bir izleme rehberi.</li>'
                 '<li><b>Pazar test.</b> Haftayı toparlayan etkileşimli bir test ve kısa bir analiz görevi.</li>'
                 '<li><b>Kendi hızında.</b> Takvime yetişmek zorunda değilsin. Okuduğun dersler işaretlenir, '
                 'döndüğünde kaldığın yerden devam edersin.</li></ol></section>')
    # haftalar özeti
    if weeks:
        parts.append('<h2>Haftalar</h2>')
        rows = []
        for w in sorted(weeks):
            wi = week_info(program, w)
            title = wi["baslik"] if wi else ""
            rows.append(f'<li><a href="dersler.html#hafta-{w}"><span class="wn">Hafta {w}</span>'
                        f'<span class="wt">{esc(title)}</span>'
                        f'<span class="week-count" data-week-count="{w}" data-week-total="{len(weeks[w])}">{len(weeks[w])} ders</span></a></li>')
        parts.append(f'<ul class="week-list">{"".join(rows)}</ul>')
        parts.append('<p class="more"><a href="dersler.html">Bütün dersler →</a> · <a href="program.html">52 haftalık programın tamamı →</a></p>')
    # en yeni ders
    if lessons:
        L = max(lessons, key=lambda x: (x["_date"], sort_key(x)))
        parts.append('<section class="latest">')
        parts.append(f'<p class="kicker">En yeni ders · {esc(tarih_tr(L["_date"]))}</p>')
        parts.append(f'<h3><a href="ders/{L["_slug"]}.html">{esc(label(L))}: {esc(L["baslik"])}</a></h3>')
        if L.get("tek_cumle"):
            parts.append(f'<p>{L["tek_cumle"]}</p>')
        ph = phase_of(program, wk)
        ph_txt = f" (Faz {ph['faz']}: {ph['ad']})" if ph else ""
        parts.append(f'<p class="meta" style="margin:0">Program şu an Hafta {wk}\'te{esc(ph_txt)}. Yeni dersler her gün ekleniyor.</p>')
        parts.append('</section>')
    parts.append(f'<div class="stats"><div class="stat"><b>{total}</b><span>ders</span></div>'
                 f'<div class="stat"><b>{len(terms)}</b><span>terim</span></div>'
                 f'<div class="stat"><b>{len(films)}</b><span>film</span></div>'
                 f'<div class="stat"><b>{TOTAL_WEEKS}</b><span>hafta</span></div></div>')
    return page(SITE_NAME, "\n".join(parts), "ana")


def redirect_page(target):
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}">
<title>{SITE_NAME}</title></head><body><a href="{target}">{target}</a></body></html>
"""


def program_page(program, lessons):
    t = today()
    wk = week_of(t)
    have = {L["hafta"] for L in lessons}
    parts = ['<p class="kicker">Program</p>', "<h1>52 hafta, 9 faz</h1>",
             '<p>Her hafta beş kısa okuma günü, bir film günü ve bir sınav günü var. Sıra hem kronolojik hem '
             'kavramsal: her faz bir öncekinin üstüne kurulur. Dersleri yayımlanmış haftalar bağlantılıdır.</p>']
    for f in program:
        parts.append(f'<section class="phase"><p class="kicker">Faz {esc(f["faz"])} · Hafta {f["baslangic"]}–{f["bitis"]}</p>'
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


def manifest_js(lessons):
    data = [{"s": L["_slug"], "l": label(L), "t": L["baslik"], "w": L["hafta"]} for L in lessons]
    return "window.FT_LESSONS = " + json.dumps(data, ensure_ascii=False) + ";\n"


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
        f.write_text(lesson_page(L, prev, nxt, total, program), encoding="utf-8")
        keep.add(f.name)
    for f in out.glob("*.html"):
        if f.name not in keep:
            f.unlink()
    (ROOT / "assets" / "manifest.js").write_text(manifest_js(lessons), encoding="utf-8")
    (ROOT / "index.html").write_text(index_page(lessons, program, terms, films), encoding="utf-8")
    (ROOT / "dersler.html").write_text(dersler_page(lessons, program), encoding="utf-8")
    (ROOT / "arsiv.html").write_text(redirect_page("dersler.html"), encoding="utf-8")
    (ROOT / "program.html").write_text(program_page(program, lessons), encoding="utf-8")
    (ROOT / "sozluk.html").write_text(glossary_page(terms), encoding="utf-8")
    (ROOT / "filmler.html").write_text(films_page(films), encoding="utf-8")
    (ROOT / "feed.xml").write_text(feed(lessons), encoding="utf-8")
    print(f"Tamam: {len(lessons)} ders, {len(terms)} terim, {len(films)} film.")


if __name__ == "__main__":
    main()
