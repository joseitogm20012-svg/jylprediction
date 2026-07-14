(function () {
  "use strict";

  const IDS = {
    inputA: "input-odds-a",
    inputD: "input-odds-draw",
    inputB: "input-odds-b",
    panel: "odds-implied-overround",
    impA: "odds-imp-a",
    impD: "odds-imp-d",
    impB: "odds-imp-b",
    overround: "odds-overround",
    arbBadge: "odds-arb-badge",
    fairA: "odds-fair-a",
    fairD: "odds-fair-d",
    fairB: "odds-fair-b",
  };

  const MIN_ODDS = 1.01;

  function $get(id) {
    return document.getElementById(id);
  }

  function parseOdds(value) {
    if (!value) return null;
    const n = parseFloat(value);
    if (!isFinite(n) || n < MIN_ODDS) return null;
    return n;
  }

  function formatPct(p) {
    return (p * 100).toFixed(1) + "%";
  }

  function formatOdds(o) {
    return o.toFixed(2);
  }

  function recalc() {
    const inputA = $get(IDS.inputA);
    const inputD = $get(IDS.inputD);
    const inputB = $get(IDS.inputB);
    const panel = $get(IDS.panel);
    if (!inputA || !inputD || !inputB || !panel) return;

    const oddsA = parseOdds(inputA.value);
    const oddsD = parseOdds(inputD.value);
    const oddsB = parseOdds(inputB.value);
    const hasAll = oddsA !== null && oddsD !== null && oddsB !== null;

    if (!hasAll) {
      panel.classList.add("hidden");
      return;
    }
    panel.classList.remove("hidden");

    const impA = 1 / oddsA;
    const impD = 1 / oddsD;
    const impB = 1 / oddsB;
    const overround = impA + impD + impB - 1;

    const total = impA + impD + impB;
    const fairA = total > 0 ? 1 / (impA / total) : 0;
    const fairD = total > 0 ? 1 / (impD / total) : 0;
    const fairB = total > 0 ? 1 / (impB / total) : 0;

    const setText = (id, text) => {
      const el = $get(id);
      if (el) el.textContent = text;
    };

    setText(IDS.impA, formatPct(impA));
    setText(IDS.impD, formatPct(impD));
    setText(IDS.impB, formatPct(impB));

    const overEl = $get(IDS.overround);
    if (overEl) {
      const sign = overround >= 0 ? "+" : "";
      overEl.textContent = `${sign}${(overround * 100).toFixed(2)}%`;
      if (overround > 0.08) {
        overEl.style.color = "var(--color-team-b)";
      } else if (overround < 0) {
        overEl.style.color = "#10b981";
      } else {
        overEl.style.color = "var(--color-text-primary)";
      }
    }

    setText(IDS.fairA, formatOdds(fairA));
    setText(IDS.fairD, formatOdds(fairD));
    setText(IDS.fairB, formatOdds(fairB));

    const badgeEl = $get(IDS.arbBadge);
    if (badgeEl) {
      if (overround < -0.001) {
        badgeEl.classList.remove("hidden");
        const arbPct = Math.abs(overround) * 100;
        badgeEl.textContent = `ARBITRAJE ${arbPct.toFixed(2)}%`;
        badgeEl.style.background = "rgba(16, 185, 129, 0.25)";
        badgeEl.style.color = "#a7f3d0";
        badgeEl.style.borderColor = "rgba(16, 185, 129, 0.4)";
      } else {
        badgeEl.classList.add("hidden");
        badgeEl.textContent = "";
      }
    }
  }

  function bind() {
    [IDS.inputA, IDS.inputD, IDS.inputB].forEach((id) => {
      const el = $get(id);
      if (el) {
        el.addEventListener("input", recalc);
        el.addEventListener("change", recalc);
      }
    });
    recalc();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }

  window.updateImpliedOverround = recalc;
})();
