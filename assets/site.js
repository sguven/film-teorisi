/* Film Teorisi — interactive parts: language switch, quizzes, glossary search */
(function () {
  "use strict";

  // ---------- Language switch (EN / TR) ----------
  var root = document.documentElement;
  function setLang(l) {
    if (l !== "en" && l !== "tr") return;
    var prev = root.getAttribute("data-lang");
    root.setAttribute("data-lang", l);
    root.lang = l;
    try { localStorage.setItem("ft-lang", l); } catch (e) {}
    var t = root.getAttribute("data-title-" + l);
    if (t) document.title = t;
    // Keep the URL clean, and map week anchors (#week-4 <-> #hafta-4)
    try {
      var u = new URL(location.href);
      u.searchParams.delete("lang");
      var m = u.hash.match(/^#(week|hafta)-(\d+)$/);
      if (m) u.hash = "#" + (l === "en" ? "week" : "hafta") + "-" + m[2];
      history.replaceState(null, "", u.toString());
      if (m && prev !== l) {
        var el = document.getElementById(u.hash.slice(1));
        if (el) el.scrollIntoView();
      }
    } catch (e) {}
    document.querySelectorAll("[data-set-lang]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-set-lang") === l ? "true" : "false");
    });
  }
  document.querySelectorAll("[data-set-lang]").forEach(function (b) {
    b.addEventListener("click", function () { setLang(b.getAttribute("data-set-lang")); });
  });
  setLang(root.getAttribute("data-lang") || "en");
  // If someone arrives at #hafta-4 in English (or #week-4 in Turkish), jump to the right section
  (function () {
    var m = location.hash.match(/^#(week|hafta)-(\d+)$/);
    if (!m) return;
    var want = (root.getAttribute("data-lang") === "en" ? "week" : "hafta") + "-" + m[2];
    if (want !== m[1] + "-" + m[2]) {
      var el = document.getElementById(want);
      if (el) { history.replaceState(null, "", "#" + want); el.scrollIntoView(); }
    }
  })();

  // ---------- Quiz ----------
  document.querySelectorAll("[data-quiz]").forEach(function (box) {
    var dataEl = box.querySelector("script[type='application/json']");
    if (!dataEl) return;
    var questions;
    try { questions = JSON.parse(dataEl.textContent); } catch (e) { return; }
    var okText = box.getAttribute("data-ok") || "Correct.";
    var answerText = box.getAttribute("data-answer") || "Correct answer:";
    var answeredText = box.getAttribute("data-answered") || "answered";
    var list = box.querySelector(".quiz-list");
    var scoreEl = box.querySelector(".quiz-score .val");
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
            exp.innerHTML = (ok ? '<b class="ok">' + okText + "</b> " : '<b class="bad">' + answerText + " " +
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
      if (scoreEl) scoreEl.textContent = correct + " / " + questions.length +
        (answered < questions.length ? "  (" + answered + " " + answeredText + ")" : "");
    }
    var resetQ = box.querySelector("[data-quiz-reset]");
    if (resetQ) resetQ.addEventListener("click", render);
    render();
  });

  // ---------- Glossary search (one per language) ----------
  var norm = function (s) {
    return (s || "").toLocaleLowerCase("tr").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ı/g, "i");
  };
  document.querySelectorAll("[data-filter]").forEach(function (search) {
    var scope = search.closest(".l-en, .l-tr") || document;
    var rows = Array.prototype.slice.call(scope.querySelectorAll("[data-row]"));
    var empty = scope.querySelector("[data-empty]");
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
  });
})();
