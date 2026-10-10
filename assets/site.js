/* Film Teorisi — etkileşimli parçalar: ilerleme takibi, test, sözlük arama */
(function () {
  "use strict";

  var ROOT = document.body.getAttribute("data-root") || "";
  var LESSONS = window.FT_LESSONS || [];
  var KEY = "ft-progress-v1";

  // ---------- İlerleme (yalnızca bu tarayıcıda) ----------
  function load() {
    try {
      var raw = window.localStorage.getItem(KEY);
      var p = raw ? JSON.parse(raw) : null;
      if (p && typeof p === "object") return { read: p.read || {}, last: p.last || null };
    } catch (e) {}
    return { read: {}, last: null };
  }
  function save(p) {
    try { window.localStorage.setItem(KEY, JSON.stringify(p)); } catch (e) {}
  }
  var progress = load();
  var index = {};
  LESSONS.forEach(function (L, i) { index[L.s] = i; });
  function url(slug) { return ROOT + "ders/" + slug + ".html"; }
  function readCount() {
    var n = 0;
    LESSONS.forEach(function (L) { if (progress.read[L.s]) n++; });
    return n;
  }
  // Kaldığın yer: okunan en ileri dersin bir sonrakisi; hiç okunmadıysa son açılan ders
  function continueTarget() {
    var maxRead = -1;
    LESSONS.forEach(function (L, i) { if (progress.read[L.s]) maxRead = i; });
    if (maxRead >= 0) {
      if (maxRead + 1 < LESSONS.length) return { lesson: LESSONS[maxRead + 1], done: false };
      return { lesson: LESSONS[maxRead], done: true };
    }
    if (progress.last && index[progress.last] !== undefined) return { lesson: LESSONS[index[progress.last]], done: false };
    return null;
  }

  // Ders sayfası: son açılan dersi kaydet, okundu düğmesi
  var article = document.querySelector("[data-lesson]");
  if (article) {
    var slug = article.getAttribute("data-lesson");
    progress.last = slug;
    save(progress);
    var badge = document.querySelector("[data-read-badge]");
    if (badge && progress.read[slug]) badge.hidden = false;
    document.querySelectorAll("[data-mark-read]").forEach(function (el) {
      if (progress.read[slug] && el.tagName === "BUTTON") el.textContent = "Okundu ✓";
      el.addEventListener("click", function () {
        progress.read[slug] = Date.now();
        save(progress);
        if (badge) badge.hidden = false;
        if (el.tagName === "BUTTON") el.textContent = "Okundu ✓";
      });
    });
  }

  // "Devam et" bağlantıları (ana sayfa, dersler sayfası)
  var target = continueTarget();
  document.querySelectorAll("[data-continue-link]").forEach(function (a) {
    if (!LESSONS.length) return;
    if (!target) {
      a.setAttribute("href", url(LESSONS[0].s));
      return;
    }
    a.setAttribute("href", url(target.lesson.s));
    a.textContent = target.done ? "Son ders: " + target.lesson.l + " →" : "Devam et: " + target.lesson.l + " →";
  });
  if (target) {
    var note = document.querySelector("[data-continue-note]");
    if (note) {
      note.textContent = target.done
        ? "Yayımlanan bütün dersleri okudun. Yeni dersler her gün ekleniyor."
        : "Kaldığın yer: " + target.lesson.t + " · " + readCount() + " / " + LESSONS.length + " ders okundu";
    }
    var start = document.querySelector("[data-start-link]");
    if (start) start.hidden = false;
  }

  // Ders listeleri: okundu işaretleri ve hafta sayaçları
  document.querySelectorAll("[data-slug]").forEach(function (li) {
    if (progress.read[li.getAttribute("data-slug")]) li.classList.add("read");
  });
  document.querySelectorAll("[data-week-count]").forEach(function (el) {
    var w = +el.getAttribute("data-week-count");
    var tot = +el.getAttribute("data-week-total");
    var n = 0;
    LESSONS.forEach(function (L) { if (L.w === w && progress.read[L.s]) n++; });
    if (n > 0) {
      el.textContent = n === tot ? "Tamamlandı ✓" : n + " / " + tot + " okundu";
      if (n === tot) el.classList.add("complete");
    } else if (!el.textContent) {
      el.textContent = tot + " ders";
    }
  });
  var bar = document.querySelector("[data-overall-bar]");
  var cnt = document.querySelector("[data-overall-count]");
  if (bar && LESSONS.length) bar.style.width = (100 * readCount() / LESSONS.length) + "%";
  if (cnt) cnt.textContent = readCount();
  var reset = document.querySelector("[data-reset-progress]");
  if (reset) reset.addEventListener("click", function () {
    if (window.confirm("Bu tarayıcıdaki okuma ilerlemen silinsin mi?")) {
      save({ read: {}, last: null });
      window.location.reload();
    }
  });

  // ---------- Test ----------
  document.querySelectorAll("[data-quiz]").forEach(function (root) {
    var dataEl = root.querySelector("script[type='application/json']");
    if (!dataEl) return;
    var questions;
    try { questions = JSON.parse(dataEl.textContent); } catch (e) { return; }
    var list = root.querySelector(".quiz-list");
    var scoreEl = root.querySelector(".quiz-score .val");
    var answered = 0, correct = 0;

    function render() {
      list.innerHTML = "";
      answered = 0; correct = 0; updateScore();
      questions.forEach(function (q, qi) {
        var wrap = document.createElement("div");
        wrap.className = "quiz-q";
        var qt = document.createElement("div");
        qt.className = "qtext";
        qt.innerHTML = '<span class="qnum">' + (qi + 1) + ".</span>" + q.soru;
        wrap.appendChild(qt);
        var opts = document.createElement("div");
        opts.className = "opts";
        var exp = document.createElement("div");
        exp.className = "explain";
        q.secenekler.forEach(function (s, si) {
          var b = document.createElement("button");
          b.type = "button";
          b.className = "opt";
          b.innerHTML = String.fromCharCode(65 + si) + ") " + s;
          b.addEventListener("click", function () {
            var buttons = opts.querySelectorAll(".opt");
            buttons.forEach(function (x) { x.disabled = true; });
            buttons[q.dogru].classList.add("correct");
            var ok = si === q.dogru;
            if (!ok) b.classList.add("wrong");
            answered++; if (ok) correct++;
            exp.innerHTML = (ok ? '<b class="ok">Doğru.</b> ' : '<b class="bad">Doğru cevap: ' +
              String.fromCharCode(65 + q.dogru) + ".</b> ") + (q.aciklama || "");
            exp.classList.add("show");
            updateScore();
          });
          opts.appendChild(b);
        });
        wrap.appendChild(opts);
        wrap.appendChild(exp);
        list.appendChild(wrap);
      });
    }
    function updateScore() {
      if (scoreEl) scoreEl.textContent = correct + " / " + questions.length + (answered < questions.length ? "  (" + answered + " cevaplandı)" : "");
    }
    var resetQ = root.querySelector("[data-quiz-reset]");
    if (resetQ) resetQ.addEventListener("click", render);
    render();
  });

  // ---------- Sözlük arama ----------
  var search = document.querySelector("[data-filter]");
  if (search) {
    var rows = Array.prototype.slice.call(document.querySelectorAll("[data-row]"));
    var empty = document.querySelector("[data-empty]");
    var norm = function (s) {
      return (s || "").toLocaleLowerCase("tr").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ı/g, "i");
    };
    search.addEventListener("input", function () {
      var q = norm(search.value.trim());
      var shown = 0;
      rows.forEach(function (r) {
        var hit = !q || norm(r.textContent).indexOf(q) !== -1;
        r.hidden = !hit;
        if (hit) shown++;
      });
      if (empty) empty.hidden = shown !== 0;
    });
  }
})();
