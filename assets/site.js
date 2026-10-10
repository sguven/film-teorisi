/* Film Teorisi — etkileşimli parçalar (quiz, sözlük arama) */
(function () {
  "use strict";

  // ---------- Quiz ----------
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
    var reset = root.querySelector("[data-quiz-reset]");
    if (reset) reset.addEventListener("click", render);
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
