# Film Theory

Daily lessons, quizzes and a glossary from a 52-week film theory reading program.
The site is bilingual: **English** (shown by default to first-time visitors) and **Turkish**. The lessons are
written in Turkish first, and each one gets an English twin.

**Site:** https://sguven.github.io/film-teorisi/ (add `?lang=tr` or `?lang=en` to a link to open it in that language)

A scheduled task (Claude) prepares each day's lesson, emails it, then adds it to `content/` (Turkish) and
`content/en/` (English) as JSON, and `scripts/build.py` regenerates the site. Pages are plain HTML; GitHub Pages publishes from the
root of the `main` branch.

## Layout

| Path | What it is |
|---|---|
| `content/YYYY-MM-DD-hafta-XX-gun-Y.json` | Source content for each lesson in Turkish (`hafta` = week, `gun` = day) |
| `content/en/<same file name>` | The English version of the same lesson (same keys, see below) |
| `data/program.json`, `data/program.en.json` | Phase and week titles for the 52-week program (Turkish, English) |
| `pdf/` | PDF versions of the lessons |
| `scripts/build.py` | Builds the site (Python standard library only); the Contact section links are in `CONTACT_LINKS` |
| `assets/` | Styles and a little JS (quizzes, glossary search) |
| `index.html`, `dersler.html`, `program.html`, `sozluk.html`, `filmler.html`, `feed.xml`, `feed-en.xml`, `ders/` | Generated pages – don't edit by hand, `build.py` overwrites them (`arsiv.html` redirects to `dersler.html`) |

Generated page names are Turkish because they are part of the site's public URLs:
`dersler` = all lessons, `sozluk` = glossary, `filmler` = films, `ders/` = individual lessons.

## Lesson file format

File name: `content/<date>-hafta-<XX>-gun-<Y>.json` (for a review day: `...-hafta-01-tekrar.json`).
Field names are Turkish because the build script and the scheduled task use them; the English
meaning is in the comments below.

```jsonc
{
  "hafta": 3,                     // week
  "gun": 2,                       // day of the week, 1–7, or "tekrar" (review)
  "tarih": "2026-10-20",          // date
  "tur": "ders",                  // type: ders (lesson, days 1–5), tekrar (review), film (day 6), sinav (quiz, day 7)
  "baslik": "Topic title",
  "okuma": "Reading and chapter (optional)",
  "film": "Film of the week (optional)",
  "pdf": "film-teorisi-hafta-03-gun-2.pdf",
  "tek_cumle": "Today's one sentence",
  "bolumler": [{"baslik": "Lecture", "html": "<p>...</p>"}],      // sections
  "sorular": ["Question 1", "Question 2", "Question 3"],          // questions
  "soru_baslik": "Today's questions",                             // heading for the questions
  "ipuclari": ["Optional; shown in a collapsed box"],             // hints
  "gozlem": "Observation exercise",
  "quiz": [{"soru": "...", "secenekler": ["A", "B", "C", "D"], "dogru": 1, "aciklama": "..."}],
  "analiz": "<p>Analysis task (quiz day)</p>",
  "terimler": [{"tr": "Derin odak", "en": "deep focus", "orijinal": "optional", "tanim": "One sentence"}],
  "filmler": [{"ad": "Citizen Kane", "yil": 1941, "yonetmen": "Orson Welles", "not": "optional"}],
  "yarin": "Tomorrow's topic"
}
```

- `quiz[].dogru` is the index of the correct option and **starts at 0**.
- `html`, `sorular`, `gozlem`, `tek_cumle` and `yarin` accept simple HTML (`<p> <b> <i> <ul> <ol> <li> <h3>`).
- Fields that aren't defined are skipped. Terms and films are collected automatically into the
  glossary and film pages.

## Languages

Every generated page contains both languages; a small script in `<head>` shows one of them:
`?lang=en|tr` in the URL first, otherwise the visitor's saved choice (the EN/TR switch in the header,
stored in `localStorage` as `ft-lang`), otherwise **English**. Links in the Turkish lesson emails add
`?lang=tr`. If a lesson has no English file yet, the English view shows the Turkish lesson with a short note.

### English lesson files (`content/en/`)

- Same file name, **same keys, same list lengths and order** as the Turkish file. Don't add or drop keys.
- Don't change: `hafta`, `gun`, `tarih`, `tur`, `pdf`, every `quiz[].dogru`, `filmler[].ad`, `filmler[].yil`,
  `filmler[].yonetmen`, `terimler[].tr`. Keep `terimler[].en` / `orijinal` (fix only if clearly wrong).
- Translate every other text value (titles, section headings, HTML, questions, quiz options and explanations,
  `tanim`, `okuma`, `film`, `yarin`...) into natural, publishable English — the full lesson, not a summary.
  Keep the HTML tags. Where the Turkish says "Türkçe terim (*English term*)", just use the English term; keep
  original-language terms (French, Russian, ...) in italics. Self-references like "write in this project" become
  reader-neutral ("write down your thoughts"); no mentions of email, PDF, Claude or Drive.
- Valid UTF-8 JSON; use “ ” and ’ inside text, never a raw `"`.
- Check: the structure of both files must match key for key (see `scripts/check_en.py`).

## Publishing (conflict-free)

```bash
git add -A && git commit -m "Hafta X · Gün Y: topic"
git fetch origin main && git -c merge.ours.driver=true rebase origin/main
python3 scripts/build.py && git add -A && (git diff --cached --quiet || git commit -m "Rebuild site")
git push origin main
```

`.gitattributes` resolves conflicts in generated files automatically; `build.py` regenerates them
from the content.

## Home page

The home page always shows the latest lesson itself. All other lessons are on the "all lessons"
page, newest week first.

## Building locally

```bash
python3 scripts/build.py
```

The books and articles used as sources are not stored in this repo; the lessons explain the ideas
in their own words.
