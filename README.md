# Film Teorisi

52 haftalık bir film teorisi okuma programının günlük dersleri, testleri ve terim sözlüğü.

**Site:** https://sguven.github.io/film-teorisi/

Dersler her gün zamanlanmış bir görevle (Claude) hazırlanır, `content/` klasörüne JSON olarak eklenir ve
`scripts/build.py` siteyi yeniden üretir. Sayfalar düz HTML'dir; GitHub Pages `main` dalının kökünden yayımlar.

## Klasörler

| Yol | Ne |
|---|---|
| `content/YYYY-MM-DD-hafta-XX-gun-Y.json` | Her dersin içeriği (kaynak) |
| `data/program.json` | 52 haftalık programın faz ve hafta başlıkları |
| `pdf/` | Derslerin PDF sürümleri |
| `scripts/build.py` | Siteyi üretir (yalnızca Python standart kütüphanesi) |
| `assets/` | Stil ve küçük JS (test, sözlük arama) |
| `index.html`, `dersler.html`, `program.html`, `sozluk.html`, `filmler.html`, `feed.xml`, `ders/` | Üretilen sayfalar; elle düzenleme, `build.py` üzerine yazar (`arsiv.html` → `dersler.html` yönlendirmesi) |

## Ders dosyası biçimi

Dosya adı: `content/<tarih>-hafta-<XX>-gun-<Y>.json` (tekrar günü için `...-hafta-01-tekrar.json`).

```json
{
  "hafta": 3,
  "gun": 2,
  "tarih": "2026-10-20",
  "tur": "ders",
  "baslik": "Konu başlığı",
  "okuma": "Kaynak ve bölüm (isteğe bağlı)",
  "film": "Haftanın filmi (isteğe bağlı)",
  "pdf": "film-teorisi-hafta-03-gun-2.pdf",
  "tek_cumle": "Bugünün tek cümlesi",
  "bolumler": [{"baslik": "Anlatım", "html": "<p>...</p>"}],
  "sorular": ["Soru 1", "Soru 2", "Soru 3"],
  "soru_baslik": "Bugünün soruları",
  "ipuclari": ["İsteğe bağlı; katlanmış kutuda gösterilir"],
  "gozlem": "Gözlem görevi",
  "quiz": [{"soru": "...", "secenekler": ["A", "B", "C", "D"], "dogru": 1, "aciklama": "..."}],
  "analiz": "<p>Analiz görevi (sınav günü)</p>",
  "terimler": [{"tr": "Derin odak", "en": "deep focus", "orijinal": "isteğe bağlı", "tanim": "Tek cümle"}],
  "filmler": [{"ad": "Citizen Kane", "yil": 1941, "yonetmen": "Orson Welles", "not": "isteğe bağlı"}],
  "yarin": "Yarının konusu"
}
```

- `gun`: 1–7 arası sayı ya da `"tekrar"`. `tur`: `ders` (Gün 1–5), `tekrar`, `film` (Gün 6), `sinav` (Gün 7).
- `quiz[].dogru`: doğru seçeneğin sırası, **0'dan başlar**.
- `html`, `sorular`, `gozlem`, `tek_cumle`, `yarin` alanlarında basit HTML (`<p> <b> <i> <ul> <ol> <li> <h3>`) kullanılabilir.
- Tanımlanmamış alanlar atlanır. Terimler ve filmler sözlük ve film sayfalarında otomatik toplanır.

## Yayımlama (çakışmasız)

```bash
git add -A && git commit -m "Hafta X · Gün Y: konu"
git fetch origin main && git -c merge.ours.driver=true rebase origin/main
python3 scripts/build.py && git add -A && (git diff --cached --quiet || git commit -m "Siteyi yeniden üret")
git push origin main
```

`.gitattributes` üretilen dosyalardaki çakışmaları otomatik geçer; `build.py` onları içerikten yeniden üretir.

## Ana sayfa

Ana sayfa her zaman en güncel dersin kendisini gösterir. Diğer dersler "Bütün dersler" sayfasında, en yeni hafta en üstte.

## Yerelde üretmek

```bash
python3 scripts/build.py
```

Ders kaynaklarındaki kitap ve makaleler bu repoya konmaz; dersler fikirleri kendi cümleleriyle anlatır.
