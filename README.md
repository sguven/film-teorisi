# Film Theory

Daily lessons, quizzes and a glossary from a 52-week film theory reading program.
The lessons themselves are written in Turkish, with English terms alongside.

**Site:** https://sguven.github.io/film-theory/

A scheduled task (Claude) prepares each day's lesson, adds it to `content/` as JSON, and
`scripts/build.py` regenerates the site. Pages are plain HTML; GitHub Pages publishes from the
root of the `main` branch.

## Layout

| Path | What it is |
|---|---|
| `content/YYYY-MM-DD-hafta-XX-gun-Y.json` | Source content for each lesson (`hafta` = week, `gun` = day) |
| `data/program.json` | Phase and week titles for the 52-week program |
| `pdf/` | PDF versions of the lessons |
| `scripts/build.py` | Builds the site (Python standard library only) |
| `assets/` | Styles and a little JS (quizzes, glossary search) |
| `index.html`, `dersler.html`, `program.html`, `sozluk.html`, `filmler.html`, `feed.xml`, `ders/` | Generated pages – don't edit by hand, `build.py` overwrites them (`arsiv.html` redirects to `dersler.html`) |

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
