// Predictor Mundial 2026 - Frontend Client Logic
// Communicates with the FastAPI Python Backend for all computations, simulations, and betting odds analysis.

// Mapping of Slugs to Country Details (Flags)
const TEAM_METADATA = {
  "argentina": { name: "Argentina", flag: "🇦🇷", rank: 1 },
  "france": { name: "Francia", flag: "🇫🇷", rank: 2 },
  "spain": { name: "España", flag: "🇪🇸", rank: 3 },
  "brazil": { name: "Brasil", flag: "🇧🇷", rank: 4 },
  "england": { name: "Inglaterra", flag: "🇬🇧", rank: 5 },
  "portugal": { name: "Portugal", flag: "🇵🇹", rank: 6 },
  "netherlands": { name: "Países Bajos", flag: "🇳🇱", rank: 7 },
  "germany": { name: "Alemania", flag: "🇩🇪", rank: 8 },
  "belgium": { name: "Bélgica", flag: "🇧🇪", rank: 9 },
  "italy": { name: "Italia", flag: "🇮🇹", rank: 10 },
  "colombia": { name: "Colombia", flag: "🇨🇴", rank: 11 },
  "croatia": { name: "Croacia", flag: "🇭🇷", rank: 12 },
  "morocco": { name: "Marruecos", flag: "🇲🇦", rank: 13 },
  "usa": { name: "Estados Unidos", flag: "🇺🇸", rank: 14 },
  "switzerland": { name: "Suiza", flag: "🇨🇭", rank: 15 },
  "uruguay": { name: "Uruguay", flag: "🇺🇾", rank: 16 },
  "japan": { name: "Japón", flag: "🇯🇵", rank: 17 },
  "mexico": { name: "México", flag: "🇲🇽", rank: 18 },
  "senegal": { name: "Senegal", flag: "🇸🇳", rank: 19 },
  "denmark": { name: "Dinamarca", flag: "🇩🇰", rank: 20 },
  "iran": { name: "Irán", flag: "🇮🇷", rank: 21 },
  "ecuador": { name: "Ecuador", flag: "🇪🇨", rank: 22 },
  "australia": { name: "Australia", flag: "🇦🇺", rank: 23 },
  "south-korea": { name: "Corea del Sur", flag: "🇰🇷", rank: 25 },
  "poland": { name: "Polonia", flag: "🇵🇱", rank: 26 },
  "wales": { name: "Gales", flag: "🏴󠁧󠁢󠁷󠁬󠁳󠁿", rank: 29 },
  "nigeria": { name: "Nigeria", flag: "🇳🇬", rank: 30 },
  "peru": { name: "Perú", flag: "🇵🇪", rank: 31 },
  "serbia": { name: "Serbia", flag: "🇷🇸", rank: 32 },
  "qatar": { name: "Catar", flag: "🇶🇦", rank: 34 },
  "czech-republic": { name: "República Checa", flag: "🇨🇿", rank: 35 },
  "egypt": { name: "Egipto", flag: "🇪🇬", rank: 36 },
  "ivory-coast": { name: "Costa de Marfil", flag: "🇨🇮", rank: 38 },
  "scotland": { name: "Escocia", flag: "🏴\u200d%7F", rank: 39 }, // fallback
  "canada": { name: "Canadá", flag: "🇨🇦", rank: 40 },
  "tunisia": { name: "Túnez", flag: "🇹🇳", rank: 41 },
  "chile": { name: "Chile", flag: "🇨🇱", rank: 42 },
  "algeria": { name: "Argelia", flag: "🇩🇿", rank: 43 },
  "panama": { name: "Panamá", flag: "🇵🇦", rank: 45 },
  "cameroon": { name: "Camerún", flag: "🇨🇲", rank: 51 },
  "jamaica": { name: "Jamaica", flag: "🇯🇲", rank: 53 },
  "venezuela": { name: "Venezuela", flag: "🇻🇪", rank: 54 },
  "paraguay": { name: "Paraguay", flag: "🇵🇾", rank: 56 },
  "south-africa": { name: "Sudáfrica", flag: "🇿🇦", rank: 59 },
  "saudi-arabia": { name: "Arabia Saudita", flag: "🇸🇦", rank: 61 },
  "ghana": { name: "Ghana", flag: "🇬🇭", rank: 64 },
  "jordan": { name: "Jordania", flag: "🇯🇴", rank: 68 },
  "bosnia-and-herzegovina": { name: "Bosnia & Herzegovina", flag: "🇧🇦", rank: 74 },
  "honduras": { name: "Honduras", flag: "🇭🇳", rank: 79 },
  "el-salvador": { name: "El Salvador", flag: "🇸🇻", rank: 81 },
  "new-zealand": { name: "Nueva Zelanda", flag: "🇳🇿", rank: 85 },
  "haiti": { name: "Haití", flag: "🇭🇹", rank: 86 },
  "trinidad-and-tobago": { name: "Trinidad y Tobago", flag: "🇹🇹", rank: 98 },
  "guatemala": { name: "Guatemala", flag: "🇬🇹", rank: 103 }
};

// State Variables
let ratingsData = {};
let selectedTeamA = "uruguay";
let selectedTeamB = "saudi-arabia";

// DOM Elements
const selectA = document.getElementById("select-team-a");
const selectB = document.getElementById("select-team-b");

const rankSliderA = document.getElementById("input-rank-a");
const rankSliderB = document.getElementById("input-rank-b");

const weightFifaSlider = document.getElementById("input-weight-fifa");
const weightH2hSlider = document.getElementById("input-weight-h2h");
const decaySlider = document.getElementById("input-decay");
const simsSlider = document.getElementById("input-sims");

const btnSimulate = document.getElementById("btn-simulate");
const simSpinner = document.getElementById("sim-spinner");

// Odds Inputs
const inputOddsA = document.getElementById("input-odds-a");
const inputOddsDraw = document.getElementById("input-odds-draw");
const inputOddsB = document.getElementById("input-odds-b");
const oddsLabelA = document.getElementById("odds-label-a");
const oddsLabelB = document.getElementById("odds-label-b");

// Match Card display elements
const eloDisplayA = document.getElementById("elo-display-a");
const eloDisplayB = document.getElementById("elo-display-b");
const fifaDisplayA = document.getElementById("fifa-display-a");
const fifaDisplayB = document.getElementById("fifa-display-b");
const flagA = document.getElementById("flag-a");
const flagB = document.getElementById("flag-b");
const nameA = document.getElementById("name-a");
const nameB = document.getElementById("name-b");

// Result display elements
const pctWinA = document.getElementById("pct-win-a");
const pctDraw = document.getElementById("pct-draw");
const pctWinB = document.getElementById("pct-win-b");
const barWinA = document.getElementById("bar-win-a");
const barDraw = document.getElementById("bar-draw");
const barWinB = document.getElementById("bar-win-b");
const labelWinA = document.getElementById("label-win-a");
const labelWinB = document.getElementById("label-win-b");

const xgValA = document.getElementById("xg-val-a");
const xgValB = document.getElementById("xg-val-b");

const scoreListContainer = document.getElementById("score-list-container");

// Betting results elements
const oddsHelperText = document.getElementById("odds-helper-text");
const oddsAnalysisContainer = document.getElementById("odds-analysis-container");
const evPctA = document.getElementById("ev-pct-a");
const evPctDraw = document.getElementById("ev-pct-draw");
const evPctB = document.getElementById("ev-pct-b");
const evLabelA = document.getElementById("ev-label-a");
const evLabelB = document.getElementById("ev-label-b");
const oddsAlertMessage = document.getElementById("odds-alert-message");

// Tabs Elements
const tabHistoryBtn = document.getElementById("tab-btn-history");
const tabH2hBtn = document.getElementById("tab-btn-h2h");
const tabHistoryContent = document.getElementById("tab-history");
const tabH2hContent = document.getElementById("tab-h2h");

const matchListA = document.getElementById("match-list-a");
const matchListB = document.getElementById("match-list-b");
const historyTitleA = document.getElementById("history-title-a");
const historyTitleB = document.getElementById("history-title-b");

const h2hMatchList = document.getElementById("h2h-match-list");
const h2hWinsA = document.getElementById("h2h-wins-a");
const h2hWinsB = document.getElementById("h2h-wins-b");
const h2hDraws = document.getElementById("h2h-draws");
const h2hLabelA = document.getElementById("h2h-label-a");
const h2hLabelB = document.getElementById("h2h-label-b");
const h2hModifierVal = document.getElementById("h2h-modifier-val");

/* ==========================================================================
   INITIALIZATION & DATA LOADING
   ========================================================================== */
async function initializeApp() {
  try {
    // 1. Fetch ratings from API
    const res = await fetch("/api/teams");
    const data = await res.json();
    ratingsData = data.ratings;
    
    document.getElementById("calibration-status").textContent = "API Python Activa";

    // 2. Populate selectors
    populateSelects();

    // 3. Bind UI listeners
    bindListeners();

    // 4. Update UI for the initial match
    updateMatchCard();

  } catch (error) {
    console.error("Initialization error:", error);
    document.getElementById("calibration-status").textContent = "Error de conexión API";
    document.getElementById("calibration-status").style.color = "#ef4444";
  }
}

function populateSelects() {
  const slugs = Object.keys(TEAM_METADATA).sort((a, b) => 
    TEAM_METADATA[a].name.localeCompare(TEAM_METADATA[b].name)
  );

  slugs.forEach(slug => {
    const optA = document.createElement("option");
    optA.value = slug;
    optA.textContent = `${TEAM_METADATA[slug].flag} ${TEAM_METADATA[slug].name}`;
    if (slug === selectedTeamA) optA.selected = true;
    selectA.appendChild(optA);

    const optB = document.createElement("option");
    optB.value = slug;
    optB.textContent = `${TEAM_METADATA[slug].flag} ${TEAM_METADATA[slug].name}`;
    if (slug === selectedTeamB) optB.selected = true;
    selectB.appendChild(optB);
  });
}

/* ==========================================================================
   UI UPDATES & TABS
   ========================================================================== */
function bindListeners() {
  selectA.addEventListener("change", (e) => {
    selectedTeamA = e.target.value;
    rankSliderA.value = TEAM_METADATA[selectedTeamA].rank;
    updateMatchCard();
  });

  selectB.addEventListener("change", (e) => {
    selectedTeamB = e.target.value;
    rankSliderB.value = TEAM_METADATA[selectedTeamB].rank;
    updateMatchCard();
  });

  rankSliderA.addEventListener("input", (e) => {
    fifaDisplayA.textContent = `FIFA #${e.target.value}`;
  });

  rankSliderB.addEventListener("input", (e) => {
    fifaDisplayB.textContent = `FIFA #${e.target.value}`;
  });

  decaySlider.addEventListener("input", () => {
    updateMatchCard(true); // reload history lists when decay changes
  });

  btnSimulate.addEventListener("click", () => {
    runPredictionFlow();
  });

  // Tab switching
  tabHistoryBtn.addEventListener("click", () => {
    tabHistoryBtn.classList.add("active");
    tabH2hBtn.classList.remove("active");
    tabHistoryContent.classList.remove("hidden");
    tabH2hContent.classList.add("hidden");
  });

  tabH2hBtn.addEventListener("click", () => {
    tabH2hBtn.classList.add("active");
    tabHistoryBtn.classList.remove("active");
    tabH2hContent.classList.remove("hidden");
    tabHistoryContent.classList.add("hidden");
  });
}

function updateMatchCard(fullReload = true) {
  const metaA = TEAM_METADATA[selectedTeamA];
  const metaB = TEAM_METADATA[selectedTeamB];

  // Update names, flags and stats
  nameA.textContent = metaA.name;
  nameB.textContent = metaB.name;
  flagA.textContent = metaA.flag;
  flagB.textContent = metaB.flag;

  const eloA = ratingsData[selectedTeamA] || 1500;
  const eloB = ratingsData[selectedTeamB] || 1500;

  eloDisplayA.textContent = `Elo ${Math.round(eloA)}`;
  eloDisplayB.textContent = `Elo ${Math.round(eloB)}`;

  fifaDisplayA.textContent = `FIFA #${rankSliderA.value}`;
  fifaDisplayB.textContent = `FIFA #${rankSliderB.value}`;

  labelWinA.textContent = `Victoria ${metaA.name}`;
  labelWinB.textContent = `Victoria ${metaB.name}`;
  
  oddsLabelA.textContent = `Cuota ${metaA.name.slice(0, 5)}.`;
  oddsLabelB.textContent = `Cuota ${metaB.name.slice(0, 5)}.`;
  evLabelA.textContent = `${metaA.name.slice(0, 5)}. EV%`;
  evLabelB.textContent = `${metaB.name.slice(0, 5)}. EV%`;

  if (fullReload) {
    // Reload recent matches lists and H2H calculations from Python API
    loadRecentMatches(selectedTeamA, matchListA, historyTitleA, "Uruguay");
    loadRecentMatches(selectedTeamB, matchListB, historyTitleB, "Arabia Saudita");
    loadH2HData();
  }
}

/* ==========================================================================
   API DATA CALLS (HISTORY, H2H, PREDICT)
   ========================================================================== */
async function loadRecentMatches(teamSlug, listElement, titleElement, defaultName) {
  const meta = TEAM_METADATA[teamSlug] || { name: defaultName, flag: "" };
  titleElement.textContent = `Partidos de ${meta.name}`;
  listElement.innerHTML = `<div class="loading-placeholder">Cargando partidos...</div>`;

  try {
    const decay = parseInt(decaySlider.value);
    const res = await fetch(`/api/history/${teamSlug}?decay_months=${decay}`);
    const data = await res.json();
    
    listElement.innerHTML = "";

    if (!data.history.length) {
      listElement.innerHTML = `<div class="loading-placeholder">No hay historial de partidos recientes.</div>`;
      return;
    }

    data.history.forEach(m => {
      const goalsScored = m.goalsScored;
      const goalsConceded = m.goalsConceded;
      
      let outcomeClass = "match-outcome-draw";
      if (goalsScored > goalsConceded) outcomeClass = "match-outcome-win";
      else if (goalsScored < goalsConceded) outcomeClass = "match-outcome-loss";

      let badgeHtml = "";
      if (m.opponentLevel !== "Normal") {
        const style = m.opponentLevel === "Top Nivel" 
          ? "background: rgba(244, 63, 94, 0.12); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.2);"
          : "background: rgba(99,102,241,0.1); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.2);";
        badgeHtml = `<span class="difficulty-badge" style="${style}">${m.opponentLevel}</span>`;
      }

      const card = document.createElement("div");
      card.className = `match-card ${outcomeClass}`;
      card.style.opacity = Math.max(0.35, m.weight).toFixed(2);

      card.innerHTML = `
        <span class="match-date">${m.date}</span>
        <span class="match-opp" style="display: flex; align-items: center; gap: 6px;">${m.opponentName} ${badgeHtml}</span>
        <span class="match-score">${goalsScored} - ${goalsConceded}</span>
      `;

      listElement.appendChild(card);
    });

  } catch (error) {
    console.error("Error loading recent matches:", error);
    listElement.innerHTML = `<div class="loading-placeholder">Error al cargar partidos de la API.</div>`;
  }
}

async function loadH2HData() {
  h2hMatchList.innerHTML = `<div class="loading-placeholder">Cargando cara a cara...</div>`;
  
  try {
    const res = await fetch(`/api/h2h/${selectedTeamA}/${selectedTeamB}`);
    const data = await res.json();
    
    h2hWinsA.textContent = data.winsA;
    h2hWinsB.textContent = data.winsB;
    h2hDraws.textContent = data.draws;
    
    const metaA = TEAM_METADATA[selectedTeamA];
    const metaB = TEAM_METADATA[selectedTeamB];
    h2hLabelA.textContent = `${metaA.name.slice(0, 8)}. victorias`;
    h2hLabelB.textContent = `${metaB.name.slice(0, 8)}. victorias`;

    h2hMatchList.innerHTML = "";

    if (!data.matches.length) {
      h2hMatchList.innerHTML = `<div class="no-matches-message">No se registran enfrentamientos previos oficiales recientes.</div>`;
      h2hModifierVal.textContent = "1.00x";
      return;
    }

    data.matches.forEach(m => {
      let outcomeClass = "match-outcome-draw";
      // determine from perspective of selectedTeamA
      const isAHome = m.homeName === metaA.name || m.homeName.includes(metaA.name) || metaA.name.includes(m.homeName);
      const gsA = isAHome ? m.hg : m.ag;
      const gsB = isAHome ? m.ag : m.hg;

      if (gsA > gsB) outcomeClass = "match-outcome-win";
      else if (gsA < gsB) outcomeClass = "match-outcome-loss";

      const card = document.createElement("div");
      card.className = `match-card ${outcomeClass}`;
      card.innerHTML = `
        <span class="match-date">${m.date}</span>
        <span class="match-opp">${m.homeName} vs ${m.awayName}</span>
        <span class="match-score">${m.hg} - ${m.ag}</span>
      `;
      h2hMatchList.appendChild(card);
    });

    // We will let the predict calculation return H2H modifier val on the actual run, or set it statically here
    const avgGd = data.avgGd;
    const h2hWeight = parseInt(weightH2hSlider.value) / 100.0;
    const h2hMultA = 1.0 + (avgGd / 4.0) * h2hWeight;
    const h2hMultB = 1.0 - (avgGd / 4.0) * h2hWeight;
    h2hModifierVal.textContent = `${h2hMultA.toFixed(2)}x / ${h2hMultB.toFixed(2)}x`;

  } catch (error) {
    console.error("Error loading H2H data:", error);
    h2hMatchList.innerHTML = `<div class="loading-placeholder">Error al cargar H2H de la API.</div>`;
  }
}

async function runPredictionFlow() {
  btnSimulate.disabled = true;
  simSpinner.classList.remove("hidden");
  btnSimulate.querySelector(".btn-text").textContent = "SIMULANDO CON PYTHON...";

  // Prepare parameters
  const payload = {
    teamA: selectedTeamA,
    teamB: selectedTeamB,
    rankA: parseInt(rankSliderA.value),
    rankB: parseInt(rankSliderB.value),
    fifaWeight: parseFloat(weightFifaSlider.value),
    h2hWeight: parseFloat(weightH2hSlider.value),
    decayMonths: parseInt(decaySlider.value),
    numSims: parseInt(simsSlider.value),
    oddsA: inputOddsA.value ? parseFloat(inputOddsA.value) : null,
    oddsDraw: inputOddsDraw.value ? parseFloat(inputOddsDraw.value) : null,
    oddsB: inputOddsB.value ? parseFloat(inputOddsB.value) : null
  };

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    // Render results
    const pctA = (data.probWinA * 100).toFixed(1);
    const pctD = (data.probDraw * 100).toFixed(1);
    const pctB = (data.probWinB * 100).toFixed(1);

    pctWinA.textContent = `${pctA}%`;
    pctDraw.textContent = `${pctD}%`;
    pctWinB.textContent = `${pctB}%`;

    barWinA.style.width = `${pctA}%`;
    barDraw.style.width = `${pctD}%`;
    barWinB.style.width = `${pctB}%`;

    xgValA.textContent = data.xgA.toFixed(2);
    xgValB.textContent = data.xgB.toFixed(2);

    // Render top scores
    scoreListContainer.innerHTML = "";
    const nameAVal = TEAM_METADATA[selectedTeamA].name;
    const nameBVal = TEAM_METADATA[selectedTeamB].name;

    data.topScores.forEach((s, idx) => {
      let desc = "";
      if (s.goalsA > s.goalsB) desc = `(A favor de ${nameAVal})`;
      else if (s.goalsA === s.goalsB) desc = "(Empate)";
      else desc = `(A favor de ${nameBVal})`;

      const pctScore = (s.probability * 100).toFixed(1);

      const li = document.createElement("li");
      li.className = "score-item";
      li.innerHTML = `
        <span class="score-rank">#${idx + 1}</span>
        <span class="score-numbers badge">${s.goalsA} - ${s.goalsB}</span>
        <span class="score-type">${desc}</span>
        <span class="score-prob" style="flex-grow: 1; text-align: right; font-weight: 700;">${pctScore}%</span>
      `;
      scoreListContainer.appendChild(li);
    });

    // Render Betting analysis (+EV)
    const ba = data.bettingAnalysis;
    if (ba.hasOdds) {
      oddsHelperText.classList.add("hidden");
      oddsAnalysisContainer.classList.remove("hidden");

      const printEv = (evVal, element, statCard) => {
        const evPctStr = (evVal * 100).toFixed(1);
        if (evVal > 0) {
          element.textContent = `+${evPctStr}%`;
          element.style.color = "var(--color-team-b)"; // Emerald
          statCard.style.background = "rgba(16, 185, 129, 0.08)";
          statCard.style.borderColor = "rgba(16, 185, 129, 0.15)";
        } else {
          element.textContent = `${evPctStr}%`;
          element.style.color = "var(--color-text-secondary)";
          statCard.style.background = "rgba(255, 255, 255, 0.01)";
          statCard.style.borderColor = "var(--card-border-inner)";
        }
      };

      const cardA = document.getElementById("ev-stat-a");
      const cardDraw = document.getElementById("ev-stat-draw");
      const cardB = document.getElementById("ev-stat-b");

      printEv(ba.edgeA, evPctA, cardA);
      printEv(ba.edgeDraw, evPctDraw, cardDraw);
      printEv(ba.edgeB, evPctB, cardB);

      // Create alert banner
      let alertMsg = "⚠️ No se detectan apuestas de valor positivo.";
      let hasValuable = false;
      let valMatches = [];

      if (ba.valuableA) { hasValuable = true; valMatches.push(nameAVal); }
      if (ba.valuableDraw) { hasValuable = true; valMatches.push("Empate"); }
      if (ba.valuableB) { hasValuable = true; valMatches.push(nameBVal); }

      if (hasValuable) {
        alertMsg = `🔥 VALOR DETECTADO EN: ${valMatches.join(" / ").toUpperCase()}`;
        oddsAlertMessage.style.background = "rgba(16, 185, 129, 0.25)";
        oddsAlertMessage.style.color = "#a7f3d0";
        oddsAlertMessage.style.borderColor = "rgba(16, 185, 129, 0.4)";
      } else {
        oddsAlertMessage.style.background = "rgba(255, 255, 255, 0.05)";
        oddsAlertMessage.style.color = "var(--color-text-secondary)";
        oddsAlertMessage.style.borderColor = "var(--card-border-inner)";
      }
      oddsAlertMessage.textContent = alertMsg;

    } else {
      oddsHelperText.classList.remove("hidden");
      oddsAnalysisContainer.classList.add("hidden");
    }

  } catch (error) {
    console.error("Prediction API error:", error);
  } finally {
    btnSimulate.disabled = false;
    simSpinner.classList.add("hidden");
    const numSimsFormatted = parseInt(simsSlider.value || 100000).toLocaleString();
    btnSimulate.querySelector(".btn-text").textContent = `🚀 SIMULAR ${numSimsFormatted} PARTIDOS`;
  }
}

// Start the app on load
document.addEventListener("DOMContentLoaded", initializeApp);
