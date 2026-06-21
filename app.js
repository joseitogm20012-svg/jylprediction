// Predictor Mundial 2026 - Frontend Client Logic
// Communicates with the FastAPI Python Backend for all computations, simulations, and betting odds analysis.

// Mapping of Slugs to Country Details (Flags)
const TEAM_METADATA = {
  "argentina": { name: "Argentina", flag: "🇦🇷", rank: 1 },
  "france": { name: "Francia", flag: "🇫🇷", rank: 3 },
  "spain": { name: "España", flag: "🇪🇸", rank: 2 },
  "brazil": { name: "Brasil", flag: "🇧🇷", rank: 6 },
  "england": { name: "Inglaterra", flag: "🇬🇧", rank: 4 },
  "portugal": { name: "Portugal", flag: "🇵🇹", rank: 5 },
  "netherlands": { name: "Países Bajos", flag: "🇳🇱", rank: 8 },
  "germany": { name: "Alemania", flag: "🇩🇪", rank: 10 },
  "austria": { name: "Austria", flag: "🇦🇹", rank: 24 },
  "belgium": { name: "Bélgica", flag: "🇧🇪", rank: 9 },
  "italy": { name: "Italia", flag: "🇮🇹", rank: 12 },
  "colombia": { name: "Colombia", flag: "🇨🇴", rank: 13 },
  "croatia": { name: "Croacia", flag: "🇭🇷", rank: 11 },
  "morocco": { name: "Marruecos", flag: "🇲🇦", rank: 7 },
  "usa": { name: "Estados Unidos", flag: "🇺🇸", rank: 17 },
  "switzerland": { name: "Suiza", flag: "🇨🇭", rank: 19 },
  "uruguay": { name: "Uruguay", flag: "🇺🇾", rank: 16 },
  "japan": { name: "Japón", flag: "🇯🇵", rank: 18 },
  "mexico": { name: "México", flag: "🇲🇽", rank: 14 },
  "senegal": { name: "Senegal", flag: "🇸🇳", rank: 15 },
  "denmark": { name: "Dinamarca", flag: "🇩🇰", rank: 21 },
  "iran": { name: "Irán", flag: "🇮🇷", rank: 20 },
  "ecuador": { name: "Ecuador", flag: "🇪🇨", rank: 23 },
  "australia": { name: "Australia", flag: "🇦🇺", rank: 27 },
  "south-korea": { name: "Corea del Sur", flag: "🇰🇷", rank: 25 },
  "poland": { name: "Polonia", flag: "🇵🇱", rank: 36 },
  "wales": { name: "Gales", flag: "🏴󠁧󠁢󠁷󠁬󠁳󠁿", rank: 38 },
  "nigeria": { name: "Nigeria", flag: "🇳🇬", rank: 26 },
  "peru": { name: "Perú", flag: "🇵🇪", rank: 52 },
  "serbia": { name: "Serbia", flag: "🇷🇸", rank: 43 },
  "qatar": { name: "Catar", flag: "🇶🇦", rank: 56 },
  "czech-republic": { name: "República Checa", flag: "🇨🇿", rank: 40 },
  "egypt": { name: "Egipto", flag: "🇪🇬", rank: 29 },
  "ivory-coast": { name: "Costa de Marfil", flag: "🇨🇮", rank: 33 },
  "scotland": { name: "Escocia", flag: "🏴\u200d%7F", rank: 42 },
  "canada": { name: "Canadá", flag: "🇨🇦", rank: 30 },
  "tunisia": { name: "Túnez", flag: "🇹🇳", rank: 45 },
  "chile": { name: "Chile", flag: "🇨🇱", rank: 51 },
  "algeria": { name: "Argelia", flag: "🇩🇿", rank: 28 },
  "panama": { name: "Panamá", flag: "🇵🇦", rank: 34 },
  "cameroon": { name: "Camerún", flag: "🇨🇲", rank: 45 },
  "jamaica": { name: "Jamaica", flag: "🇯🇲", rank: 71 },
  "venezuela": { name: "Venezuela", flag: "🇻🇪", rank: 48 },
  "paraguay": { name: "Paraguay", flag: "🇵🇾", rank: 41 },
  "south-africa": { name: "Sudáfrica", flag: "🇿🇦", rank: 60 },
  "saudi-arabia": { name: "Arabia Saudita", flag: "🇸🇦", rank: 61 },
  "ghana": { name: "Ghana", flag: "🇬🇭", rank: 73 },
  "jordan": { name: "Jordania", flag: "🇯🇴", rank: 63 },
  "bosnia-and-herzegovina": { name: "Bosnia & Herzegovina", flag: "🇧🇦", rank: 64 },
  "honduras": { name: "Honduras", flag: "🇭🇳", rank: 65 },
  "el-salvador": { name: "El Salvador", flag: "🇸🇻", rank: 100 },
  "new-zealand": { name: "Nueva Zelanda", flag: "🇳🇿", rank: 85 },
  "haiti": { name: "Haití", flag: "🇭🇹", rank: 83 },
  "trinidad-and-tobago": { name: "Trinidad y Tobago", flag: "🇹🇹", rank: 102 },
  "guatemala": { name: "Guatemala", flag: "🇬🇹", rank: 97 },
  "norway": { name: "Noruega", flag: "🇳🇴", rank: 31 },
  "sweden": { name: "Suecia", flag: "🇸🇪", rank: 38 },
  "turkey": { name: "Turquía", flag: "🇹🇷", rank: 27 },
  "uae": { name: "Emiratos Árabes Unidos", flag: "🇦🇪", rank: 68 },
  "iraq": { name: "Irak", flag: "🇮🇶", rank: 57 },
  "cape-verde": { name: "Cabo Verde", flag: "🇨🇻", rank: 67 },
  "dr-congo": { name: "República Dem. del Congo", flag: "🇨🇩", rank: 43 },
  "curacao": { name: "Curazao", flag: "🇨🇼", rank: 82 }
};

// State Variables
let ratingsData = {};
let selectedTeamA = "uruguay";
let selectedTeamB = "saudi-arabia";
let goalsChart = null;
let outcomeChart = null;
let radarChart = null;
let lastSimulationResult = null; // Global to store the latest simulation result for logging (Fase 6)

// DOM Elements
const selectA = document.getElementById("select-team-a");
const selectB = document.getElementById("select-team-b");

const rankSliderA = document.getElementById("input-rank-a");
const rankSliderB = document.getElementById("input-rank-b");

const weightFifaSlider = document.getElementById("input-weight-fifa");
const weightH2hSlider = document.getElementById("input-weight-h2h");
const decaySlider = document.getElementById("input-decay");
const simsSlider = document.getElementById("input-sims");

const inputOverrideA = document.getElementById("input-override-a");
const inputOverrideB = document.getElementById("input-override-b");
const inputAltitude = document.getElementById("input-altitude");

const btnSimulate = document.getElementById("btn-simulate");
const simSpinner = document.getElementById("sim-spinner");
const btnLogPick = document.getElementById("btn-log-pick");
const logPickSpinner = document.getElementById("log-pick-spinner");

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

// Result display elements (Circular Gauges)
const gaugePathA = document.getElementById("gauge-path-a");
const gaugePathDraw = document.getElementById("gauge-path-draw");
const gaugePathB = document.getElementById("gauge-path-b");
const gaugeTextA = document.getElementById("gauge-text-a");
const gaugeTextDraw = document.getElementById("gauge-text-draw");
const gaugeTextB = document.getElementById("gauge-text-b");
const gaugeLabelA = document.getElementById("gauge-label-a");
const gaugeLabelB = document.getElementById("gauge-label-b");

const xgValA = document.getElementById("xg-val-a");
const xgValB = document.getElementById("xg-val-b");
const xgSourceA = document.getElementById("xg-source-a");
const xgSourceB = document.getElementById("xg-source-b");
const dcRhoValue = document.getElementById("dc-rho-value");

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

// New markets and corners DOM elements
const goalsMarketsCard = document.getElementById("goals-markets-card");
const cornersPredictionCard = document.getElementById("corners-prediction-card");

const bttsYes = document.getElementById("market-btts-yes");
const bttsNo = document.getElementById("market-btts-no");
const dc1X = document.getElementById("market-dc-1X");
const dc12 = document.getElementById("market-dc-12");
const dcX2 = document.getElementById("market-dc-X2");
const dnb1 = document.getElementById("market-dnb-1");
const dnb2 = document.getElementById("market-dnb-2");
const labelDnb1 = document.getElementById("label-dnb-1");
const labelDnb2 = document.getElementById("label-dnb-2");
const ouGoalsTbody = document.getElementById("ou-goals-tbody");
const ahTbody = document.getElementById("ah-tbody");
const thAhA = document.getElementById("th-ah-a");
const thAhB = document.getElementById("th-ah-b");

const expectedCornersValA = document.getElementById("expected-corners-val-a");
const expectedCornersValB = document.getElementById("expected-corners-val-b");
const expectedCornersTotal = document.getElementById("expected-corners-total");
const expectedCornersLabelA = document.getElementById("expected-corners-label-a");
const expectedCornersLabelB = document.getElementById("expected-corners-label-b");
const ouCornersTbody = document.getElementById("ou-corners-tbody");
const probMostCornersA = document.getElementById("prob-most-corners-a");
const probMostCornersDraw = document.getElementById("prob-most-corners-draw");
const probMostCornersB = document.getElementById("prob-most-corners-b");
const labelMostCornersA = document.getElementById("label-most-corners-a");
const labelMostCornersB = document.getElementById("label-most-corners-b");

// Tabs switching will be handled dynamically in bindListeners

// Logged Picks Elements (Fase 6)
const btnUpdateLogged = document.getElementById("btn-update-logged");
const loggedUpdateSpinner = document.getElementById("logged-update-spinner");
const loggedSummaryContainer = document.getElementById("logged-summary-container");
const loggedAccuracy = document.getElementById("logged-accuracy");
const loggedRps = document.getElementById("logged-rps");
const loggedTotalCount = document.getElementById("logged-total-count");
const loggedCompletedCount = document.getElementById("logged-completed-count");
const loggedMatchList = document.getElementById("logged-match-list");

// Backtest Elements
const btnRunBacktest = document.getElementById("btn-run-backtest");
const backtestSpinner = document.getElementById("backtest-spinner");
const backtestResultsContainer = document.getElementById("backtest-results-container");
const btRoi = document.getElementById("bt-roi");
const btProfit = document.getElementById("bt-profit");
const btBets = document.getElementById("bt-bets");
const btHitrate = document.getElementById("bt-hitrate");
const btFavAcc = document.getElementById("bt-fav-acc");
const btBrier = document.getElementById("bt-brier");
const btLogloss = document.getElementById("bt-logloss");
const btMatches = document.getElementById("bt-matches");
const btDate = document.getElementById("bt-date");

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

    // Initialize TomSelect for searchable dropdowns
    try {
      if (typeof TomSelect !== 'undefined') {
        new TomSelect("#select-team-a", {
          create: false,
          sortField: { field: "text", direction: "asc" }
        });
        
        new TomSelect("#select-team-b", {
          create: false,
          sortField: { field: "text", direction: "asc" }
        });
      } else {
        console.warn("TomSelect no está definido. Cargando selectores normales.");
      }
    } catch (e) {
      console.error("Error inicializando TomSelect:", e);
    }

    // 3. Bind UI listeners
    bindListeners();

    // 4. Load backtest metrics
    loadBacktestMetrics();

    // 5. Update UI for the initial match
    updateMatchCard();

    // 6. Ready (Wait for manual simulation)

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

  // Tab switching logic for the results panel (Dynamic based on index.html)
  const resultsTabHeader = document.getElementById("results-tab-header");
  if (resultsTabHeader) {
    const tabButtons = resultsTabHeader.querySelectorAll(".tab-btn");
    tabButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        // Remove active class from all buttons in the header
        tabButtons.forEach(b => b.classList.remove("active"));
        // Add active class to clicked button
        btn.classList.add("active");
        
        // Hide all tab contents in the results section
        const tabContents = document.querySelectorAll(".results-tabs-panel .tab-content");
        tabContents.forEach(tc => tc.classList.add("hidden"));
        
        // Show targeted tab content
        const targetId = btn.id.replace("tab-btn-", "tab-");
        const targetContent = document.getElementById(targetId);
        if (targetContent) {
          targetContent.classList.remove("hidden");
        }
      });
    });
  }

  // Defensively bind optional/deleted UI elements to prevent TypeErrors
  if (btnRunBacktest) {
    btnRunBacktest.addEventListener("click", () => {
      runBacktestFlow();
    });
  }

  if (btnLogPick) {
    btnLogPick.addEventListener("click", () => {
      logCurrentPick();
    });
  }

  if (btnUpdateLogged) {
    btnUpdateLogged.addEventListener("click", () => {
      updateLoggedPicksResults();
    });
  }

  // Dynamic refresh on overrides/altitude change (only if simulation was already run once)
  inputOverrideA.addEventListener("change", () => {
    const resultsTabHeader = document.getElementById("results-tab-header");
    if (resultsTabHeader && !resultsTabHeader.classList.contains("hidden")) {
      runPredictionFlow();
    }
  });
  inputOverrideB.addEventListener("change", () => {
    const resultsTabHeader = document.getElementById("results-tab-header");
    if (resultsTabHeader && !resultsTabHeader.classList.contains("hidden")) {
      runPredictionFlow();
    }
  });
  inputAltitude.addEventListener("change", () => {
    const resultsTabHeader = document.getElementById("results-tab-header");
    if (resultsTabHeader && !resultsTabHeader.classList.contains("hidden")) {
      runPredictionFlow();
    }
  });

  // Collapsible Parameter Guide Panel Toggle
  const btnToggleGuide = document.getElementById("btn-toggle-guide");
  const configGuideContent = document.getElementById("config-guide-content");
  const configGuideContainer = document.querySelector(".config-guide-container");
  
  if (btnToggleGuide && configGuideContent && configGuideContainer) {
    btnToggleGuide.addEventListener("click", () => {
      configGuideContainer.classList.toggle("expanded");
      configGuideContent.classList.toggle("expanded");
      
      const spanText = btnToggleGuide.querySelector("span");
      if (spanText) {
        if (configGuideContainer.classList.contains("expanded")) {
          spanText.textContent = "Ocultar Guía Explicativa de Parámetros";
        } else {
          spanText.textContent = "Ver Guía Explicativa de Parámetros";
        }
      }
    });
  }

  // Exact Scores view toggle (List vs 5x5 Heatmap Grid)
  const btnShowList = document.getElementById("btn-show-list");
  const btnShowHeatmap = document.getElementById("btn-show-heatmap");
  const scoreListContainer = document.getElementById("score-list-container");
  const scoreHeatmapContainer = document.getElementById("score-heatmap-container");

  if (btnShowList && btnShowHeatmap && scoreListContainer && scoreHeatmapContainer) {
    btnShowList.addEventListener("click", () => {
      btnShowList.classList.add("active");
      btnShowHeatmap.classList.remove("active");
      scoreListContainer.classList.remove("hidden");
      scoreHeatmapContainer.classList.add("hidden");
    });

    btnShowHeatmap.addEventListener("click", () => {
      btnShowHeatmap.classList.add("active");
      btnShowList.classList.remove("active");
      scoreListContainer.classList.add("hidden");
      scoreHeatmapContainer.classList.remove("hidden");
    });
  }

  // Theme Toggle (Light / Dark mode)
  const themeToggleBtn = document.getElementById("theme-toggle");
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      try {
        console.log("Theme toggle button clicked.");
        document.body.classList.toggle("light-theme");
        
        const isLight = document.body.classList.contains("light-theme");
        console.log("Toggled light-theme class. Active:", isLight);
        
        // Save setting
        localStorage.setItem("theme", isLight ? "light" : "dark");
        
        // Update Chart colors reactively
        refreshChartColors();
      } catch (err) {
        console.error("Error in theme toggle click handler:", err);
      }
    });
  }
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

  if (gaugeLabelA) gaugeLabelA.textContent = `Victoria ${metaA.name}`;
  if (gaugeLabelB) gaugeLabelB.textContent = `Victoria ${metaB.name}`;
  
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

    // Mostrar primeros 8 partidos y ocultar el resto tras un botón
    data.history.forEach((m, index) => {
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

      const isHiddenClass = index >= 8 ? "hidden-match" : "";
      const card = document.createElement("div");
      card.className = `match-card ${outcomeClass} ${isHiddenClass}`;
      card.style.opacity = Math.max(0.35, m.weight).toFixed(2);

      card.innerHTML = `
        <span class="match-date">${m.date}</span>
        <span class="match-opp" style="display: flex; align-items: center; gap: 6px;">${m.opponentName} ${badgeHtml}</span>
        <span class="match-score">${goalsScored} - ${goalsConceded}</span>
      `;

      listElement.appendChild(card);
    });

    if (data.history.length > 8) {
      const btnMore = document.createElement("button");
      btnMore.className = "btn-view-more";
      btnMore.textContent = `Ver los ${data.history.length - 8} partidos anteriores`;
      btnMore.onclick = () => {
        const hiddenMatches = listElement.querySelectorAll('.hidden-match');
        hiddenMatches.forEach(el => el.classList.remove('hidden-match'));
        btnMore.remove();
      };
      listElement.appendChild(btnMore);
    }

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

function poissonProbability(k, lambda) {
  if (lambda <= 0) return k === 0 ? 1.0 : 0.0;
  let factorial = 1;
  for (let i = 2; i <= k; i++) {
    factorial *= i;
  }
  return (Math.pow(lambda, k) * Math.exp(-lambda)) / factorial;
}

function getPoissonDistribution(lambda) {
  const dist = [];
  let sum = 0;
  for (let k = 0; k < 5; k++) {
    const p = poissonProbability(k, lambda);
    dist.push(p);
    sum += p;
  }
  dist.push(Math.max(0, 1.0 - sum));
  return dist;
}

function renderScoreHeatmap(heatmapData, nameA, nameB) {
  const tbody = document.getElementById("heatmap-tbody");
  const table = tbody ? tbody.closest("table") : null;
  if (!tbody || !table) return;

  // Generate table header
  let theadHTML = `
    <tr>
      <th style="padding: 10px; border-bottom: 2px solid var(--panel-border); color: var(--color-text-secondary); width: 80px;">${nameA.slice(0, 3)} \\ ${nameB.slice(0, 3)}</th>
      <th style="padding: 10px; border-bottom: 2px solid var(--panel-border); font-family: var(--font-family-title); color: var(--color-team-b);">0</th>
      <th style="padding: 10px; border-bottom: 2px solid var(--panel-border); font-family: var(--font-family-title); color: var(--color-team-b);">1</th>
      <th style="padding: 10px; border-bottom: 2px solid var(--panel-border); font-family: var(--font-family-title); color: var(--color-team-b);">2</th>
      <th style="padding: 10px; border-bottom: 2px solid var(--panel-border); font-family: var(--font-family-title); color: var(--color-team-b);">3</th>
      <th style="padding: 10px; border-bottom: 2px solid var(--panel-border); font-family: var(--font-family-title); color: var(--color-team-b);">4</th>
    </tr>
  `;
  const thead = table.querySelector("thead");
  if (thead) thead.innerHTML = theadHTML;

  // Populate tbody
  tbody.innerHTML = "";
  for (let a = 0; a < 5; a++) {
    const tr = document.createElement("tr");
    
    // Row header (Home Goals)
    let trHTML = `<td style="padding: 10px; font-weight: 700; border-right: 2px solid var(--panel-border); color: var(--color-team-a); font-family: var(--font-family-title);">${a}</td>`;
    
    for (let b = 0; b < 5; b++) {
      const prob = heatmapData[a][b];
      const probPct = (prob * 100).toFixed(1);
      
      // Determine background color intensity and borders based on probability
      let bgStyle = "";
      let textStyle = "color: var(--color-text-secondary);";
      
      if (prob >= 0.08) {
        // High probability (gold)
        bgStyle = "background: rgba(240, 179, 16, 0.85); border: 1px solid rgba(240, 179, 16, 0.95);";
        textStyle = "color: #111827; font-weight: 700;";
      } else if (prob >= 0.03) {
        // Medium probability (mid-gold translucent)
        bgStyle = "background: rgba(240, 179, 16, 0.45); border: 1px solid rgba(240, 179, 16, 0.55);";
        textStyle = "color: var(--color-text-primary); font-weight: 700;";
      } else {
        // Low probability
        bgStyle = "background: rgba(240, 179, 16, 0.05); border: 1px solid rgba(255, 255, 255, 0.02);";
        textStyle = "color: var(--color-text-secondary);";
      }
      
      trHTML += `
        <td style="padding: 12px 10px; font-family: var(--font-family-mono); transition: all 0.2s; ${bgStyle} ${textStyle}">
          ${probPct}%
        </td>
      `;
    }
    
    tr.innerHTML = trHTML;
    tbody.appendChild(tr);
  }
}

function updateSideBySideBar(metricValA, metricValB, idValA, idBarA, idValB, idBarB, decimals = 2) {
  const elValA = document.getElementById(idValA);
  const elBarA = document.getElementById(idBarA);
  const elValB = document.getElementById(idValB);
  const elBarB = document.getElementById(idBarB);
  
  if (!elValA || !elBarA || !elValB || !elBarB) return;
  
  const valA = parseFloat(metricValA || 0);
  const valB = parseFloat(metricValB || 0);
  
  elValA.textContent = valA.toFixed(decimals);
  elValB.textContent = valB.toFixed(decimals);
  
  const total = valA + valB;
  if (total > 0) {
    const pctA = (valA / total) * 100;
    const pctB = (valB / total) * 100;
    elBarA.style.width = `${pctA}%`;
    elBarB.style.width = `${pctB}%`;
  } else {
    elBarA.style.width = "0%";
    elBarB.style.width = "0%";
  }
}

function refreshChartColors() {
  const isLight = document.body.classList.contains("light-theme");
  const textColor = isLight ? "#1f2937" : "#ffffff";
  const mutedColor = isLight ? "#4b5563" : "#9ca3af";
  const gridColor = isLight ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.05)";
  const gridColorRadar = isLight ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.08)";
  const tickColorRadar = isLight ? "#4b5563" : "#6b7280";

  try {
    if (goalsChart && goalsChart.options) {
      if (!goalsChart.options.plugins) goalsChart.options.plugins = {};
      if (!goalsChart.options.plugins.legend) goalsChart.options.plugins.legend = {};
      if (!goalsChart.options.plugins.legend.labels) goalsChart.options.plugins.legend.labels = {};
      goalsChart.options.plugins.legend.labels.color = textColor;
      
      if (goalsChart.options.scales) {
        if (goalsChart.options.scales.x) {
          if (!goalsChart.options.scales.x.grid) goalsChart.options.scales.x.grid = {};
          if (!goalsChart.options.scales.x.ticks) goalsChart.options.scales.x.ticks = {};
          goalsChart.options.scales.x.grid.color = gridColor;
          goalsChart.options.scales.x.ticks.color = mutedColor;
        }
        if (goalsChart.options.scales.y) {
          if (!goalsChart.options.scales.y.grid) goalsChart.options.scales.y.grid = {};
          if (!goalsChart.options.scales.y.ticks) goalsChart.options.scales.y.ticks = {};
          goalsChart.options.scales.y.grid.color = gridColor;
          goalsChart.options.scales.y.ticks.color = mutedColor;
        }
      }
      goalsChart.update();
    }
  } catch (e) {
    console.error("Error updating goalsChart colors:", e);
  }

  try {
    if (outcomeChart && outcomeChart.options) {
      if (!outcomeChart.options.plugins) outcomeChart.options.plugins = {};
      if (!outcomeChart.options.plugins.legend) outcomeChart.options.plugins.legend = {};
      if (!outcomeChart.options.plugins.legend.labels) outcomeChart.options.plugins.legend.labels = {};
      outcomeChart.options.plugins.legend.labels.color = textColor;
      outcomeChart.update();
    }
  } catch (e) {
    console.error("Error updating outcomeChart colors:", e);
  }

  try {
    if (radarChart && radarChart.options) {
      if (!radarChart.options.plugins) radarChart.options.plugins = {};
      if (!radarChart.options.plugins.legend) radarChart.options.plugins.legend = {};
      if (!radarChart.options.plugins.legend.labels) radarChart.options.plugins.legend.labels = {};
      radarChart.options.plugins.legend.labels.color = textColor;

      if (radarChart.options.scales && radarChart.options.scales.r) {
        const r = radarChart.options.scales.r;
        if (!r.angleLines) r.angleLines = {};
        if (!r.grid) r.grid = {};
        if (!r.pointLabels) r.pointLabels = {};
        if (!r.ticks) r.ticks = {};
        r.angleLines.color = gridColorRadar;
        r.grid.color = gridColorRadar;
        r.pointLabels.color = mutedColor;
        r.ticks.color = tickColorRadar;
      }
      radarChart.update();
    }
  } catch (e) {
    console.error("Error updating radarChart colors:", e);
  }
}

function updateCharts(nameAVal, nameBVal, xgAVal, xgBVal, winA, draw, winB, fullData = null) {
  const distA = getPoissonDistribution(xgAVal);
  const distB = getPoissonDistribution(xgBVal);

  const isLight = document.body.classList.contains("light-theme");
  const textColor = isLight ? "#1f2937" : "#ffffff";
  const mutedColor = isLight ? "#4b5563" : "#9ca3af";
  const gridColor = isLight ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.05)";
  const gridColorRadar = isLight ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.08)";
  const tickColorRadar = isLight ? "#4b5563" : "#6b7280";

  if (goalsChart) {
    goalsChart.data.datasets[0].label = nameAVal;
    goalsChart.data.datasets[0].data = distA;
    goalsChart.data.datasets[1].label = nameBVal;
    goalsChart.data.datasets[1].data = distB;
    goalsChart.update();
  } else {
    const ctx = document.getElementById('goalsDistributionChart');
    if (ctx) {
      goalsChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
          labels: ['0', '1', '2', '3', '4', '5+'],
          datasets: [
            {
              label: nameAVal,
              data: distA,
              backgroundColor: 'rgba(59, 130, 246, 0.65)',
              borderColor: 'rgba(59, 130, 246, 1)',
              borderWidth: 1.5,
              borderRadius: 4
            },
            {
              label: nameBVal,
              data: distB,
              backgroundColor: 'rgba(16, 185, 129, 0.65)',
              borderColor: 'rgba(16, 185, 129, 1)',
              borderWidth: 1.5,
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: {
                color: textColor,
                boxWidth: 12,
                padding: 10,
                font: { family: 'Inter', size: 10 }
              }
            },
            tooltip: {
              backgroundColor: 'rgba(15, 22, 42, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: 'rgba(255, 255, 255, 0.1)',
              borderWidth: 1,
              callbacks: {
                label: function(context) {
                  return ` ${context.dataset.label}: ${(context.raw * 100).toFixed(1)}%`;
                }
              }
            }
          },
          scales: {
            x: {
              grid: { color: gridColor },
              ticks: { color: mutedColor, font: { family: 'Inter', size: 10 } }
            },
            y: {
              grid: { color: gridColor },
              ticks: {
                color: mutedColor,
                font: { family: 'Inter', size: 10 },
                callback: function(value) { return (value * 100).toFixed(0) + '%'; }
              }
            }
          }
        }
      });
    }
  }

  if (outcomeChart) {
    outcomeChart.data.labels = [`Victoria ${nameAVal}`, 'Empate', `Victoria ${nameBVal}`];
    outcomeChart.data.datasets[0].data = [winA, draw, winB];
    outcomeChart.update();
  } else {
    const ctx = document.getElementById('outcomeDonutChart');
    if (ctx) {
      outcomeChart = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
          labels: [`Victoria ${nameAVal}`, 'Empate', `Victoria ${nameBVal}`],
          datasets: [{
            data: [winA, draw, winB],
            backgroundColor: [
              'rgba(59, 130, 246, 0.75)',
              'rgba(107, 114, 128, 0.75)',
              'rgba(16, 185, 129, 0.75)'
            ],
            borderColor: [
              'rgba(59, 130, 246, 1)',
              'rgba(107, 114, 128, 1)',
              'rgba(16, 185, 129, 1)'
            ],
            borderWidth: 1.5,
            hoverOffset: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '65%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                color: textColor,
                boxWidth: 12,
                padding: 8,
                font: { family: 'Inter', size: 10 }
              }
            },
            tooltip: {
              backgroundColor: 'rgba(15, 22, 42, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: 'rgba(255, 255, 255, 0.1)',
              borderWidth: 1,
              callbacks: {
                label: function(context) {
                  return ` ${context.label}: ${(context.raw * 100).toFixed(1)}%`;
                }
              }
            }
          }
        }
      });
    }
  }

  // Update/Render Radar Comparison Chart (Hexagon)
  if (fullData && fullData.comparisonStats) {
    const statsA = fullData.comparisonStats.teamA;
    const statsB = fullData.comparisonStats.teamB;

    // Normalizations for Radar (0-100)
    // 1. Attack (xg_overall normalized, 3.0 = 100)
    const attackA = Math.min(100, Math.max(0, (statsA.xg_overall / 3.0) * 100));
    const attackB = Math.min(100, Math.max(0, (statsB.xg_overall / 3.0) * 100));

    // 2. Defense (xga_overall normalized, 3.0 = 0, 0.0 = 100)
    const defenseA = Math.min(100, Math.max(0, ((3.0 - statsA.xga_overall) / 3.0) * 100));
    const defenseB = Math.min(100, Math.max(0, ((3.0 - statsB.xga_overall) / 3.0) * 100));

    // 3. Form (gs and gc combined, gs - gc from -2.0 to 2.0 mapped to 0 to 100)
    const formDiffA = statsA.form_gs - statsA.form_gc;
    const formDiffB = statsB.form_gs - statsB.form_gc;
    const formA = Math.min(100, Math.max(0, (formDiffA + 2.0) * 25));
    const formB = Math.min(100, Math.max(0, (formDiffB + 2.0) * 25));

    // 4. H2H (Direct matchup win rate)
    const wA = parseInt(h2hWinsA.textContent) || 0;
    const wB = parseInt(h2hWinsB.textContent) || 0;
    const dr = parseInt(h2hDraws.textContent) || 0;
    const totalMatches = wA + wB + dr;
    let h2hA = 50;
    let h2hB = 50;
    if (totalMatches > 0) {
      h2hA = Math.round(((wA + 0.5 * dr) / totalMatches) * 100);
      h2hB = Math.round(((wB + 0.5 * dr) / totalMatches) * 100);
    }

    // 5. Prestige / ELO (1300 ELO = 0, 2200 ELO = 100)
    const eloScoreA = Math.min(100, Math.max(0, ((statsA.elo - 1300) / 900) * 100));
    const eloScoreB = Math.min(100, Math.max(0, ((statsB.elo - 1300) / 900) * 100));

    // 6. Match xG (xg_a projected by model normalized, 3.0 = 100)
    const matchXgScoreA = Math.min(100, Math.max(0, (statsA.match_xg / 3.0) * 100));
    const matchXgScoreB = Math.min(100, Math.max(0, (statsB.match_xg / 3.0) * 100));

    const radarDataA = [attackA, defenseA, formA, h2hA, eloScoreA, matchXgScoreA];
    const radarDataB = [attackB, defenseB, formB, h2hB, eloScoreB, matchXgScoreB];

    if (radarChart) {
      radarChart.data.datasets[0].label = nameAVal;
      radarChart.data.datasets[0].data = radarDataA;
      radarChart.data.datasets[1].label = nameBVal;
      radarChart.data.datasets[1].data = radarDataB;
      radarChart.update();
    } else {
      const ctx = document.getElementById('radarComparisonChart');
      if (ctx) {
        radarChart = new Chart(ctx.getContext('2d'), {
          type: 'radar',
          data: {
            labels: ['Ataque', 'Defensa', 'Forma', 'Historial H2H', 'Prestigio (Elo)', 'xG Directo'],
            datasets: [
              {
                label: nameAVal,
                data: radarDataA,
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(59, 130, 246, 1)'
              },
              {
                label: nameBVal,
                data: radarDataB,
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                borderColor: 'rgba(16, 185, 129, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(16, 185, 129, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(16, 185, 129, 1)'
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
              padding: 15
            },
            plugins: {
              legend: {
                labels: {
                  color: textColor,
                  font: { family: 'Inter', size: 10 }
                }
              },
              tooltip: {
                backgroundColor: 'rgba(15, 22, 42, 0.9)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                callbacks: {
                  label: function(context) {
                    return ` ${context.dataset.label}: ${Math.round(context.raw)}/100`;
                  }
                }
              }
            },
            scales: {
              r: {
                angleLines: {
                  color: gridColorRadar
                },
                grid: {
                  color: gridColorRadar
                },
                pointLabels: {
                  color: mutedColor,
                  font: { family: 'Outfit', size: 9, weight: '600' }
                },
                ticks: {
                  color: tickColorRadar,
                  backdropColor: 'transparent',
                  font: { size: 8 },
                  stepSize: 20
                },
                min: 0,
                max: 100
              }
            }
          }
        });
      }
    }
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
    oddsB: inputOddsB.value ? parseFloat(inputOddsB.value) : null,
    strengthOverrideA: inputOverrideA.value ? parseFloat(inputOverrideA.value) : 1.0,
    strengthOverrideB: inputOverrideB.value ? parseFloat(inputOverrideB.value) : 1.0,
    altitude: inputAltitude.value ? parseInt(inputAltitude.value) : 0
  };

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    lastSimulationResult = data; // Save globally for logging (Fase 6)

    // Render results (Circular Gauges)
    const pctA = (data.probWinA * 100).toFixed(1);
    const pctD = (data.probDraw * 100).toFixed(1);
    const pctB = (data.probWinB * 100).toFixed(1);

    if (gaugeTextA) gaugeTextA.textContent = `${pctA}%`;
    if (gaugeTextDraw) gaugeTextDraw.textContent = `${pctD}%`;
    if (gaugeTextB) gaugeTextB.textContent = `${pctB}%`;

    if (gaugePathA) gaugePathA.setAttribute("stroke-dasharray", `${pctA}, 100`);
    if (gaugePathDraw) gaugePathDraw.setAttribute("stroke-dasharray", `${pctD}, 100`);
    if (gaugePathB) gaugePathB.setAttribute("stroke-dasharray", `${pctB}, 100`);

    // Hide first-time placeholder banner and reveal results tab header/active tab
    const firstTimePlaceholder = document.getElementById("first-time-placeholder");
    const resultsTabHeader = document.getElementById("results-tab-header");
    if (firstTimePlaceholder && !firstTimePlaceholder.classList.contains("hidden")) {
      firstTimePlaceholder.classList.add("hidden");
    }
    if (resultsTabHeader && resultsTabHeader.classList.contains("hidden")) {
      resultsTabHeader.classList.remove("hidden");
      
      // Also show the default active tab content (Análisis)
      const activeTabBtn = resultsTabHeader.querySelector(".tab-btn.active");
      if (activeTabBtn) {
        const tabId = activeTabBtn.id.replace("tab-btn-", "tab-");
        const tabContent = document.getElementById(tabId);
        if (tabContent) tabContent.classList.remove("hidden");
      }
    }

    xgValA.textContent = data.xgA.toFixed(2);
    xgValB.textContent = data.xgB.toFixed(2);
    
    // Mostrar fuente de xG (Mejora 2)
    if (xgSourceA && xgSourceB) {
        const getSourceLabel = (src) => {
          if (src === 'fbref') return '🔵 xG FBref';
          if (src === 'real')  return '🟢 xG Real';
          return '⚪ Estimado';
        };
        xgSourceA.textContent = getSourceLabel(data.xgSourceA);
        xgSourceB.textContent = getSourceLabel(data.xgSourceB);
    }
    
    // Mostrar correlación Dixon-Coles rho (Mejora 3)
    if (dcRhoValue && data.dcRho !== undefined) {
        dcRhoValue.textContent = data.dcRho.toFixed(2);
    }

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

    // --- Render new markets (Block 1) ---
    goalsMarketsCard.classList.remove("hidden");
    
    bttsYes.textContent = `${(data.goalsMarkets.btts.yes * 100).toFixed(1)}%`;
    bttsNo.textContent = `${(data.goalsMarkets.btts.no * 100).toFixed(1)}%`;
    document.getElementById('in-btts-yes').dataset.prob = data.goalsMarkets.btts.yes;
    document.getElementById('in-btts-no').dataset.prob = data.goalsMarkets.btts.no;
    
    dc1X.textContent = `${(data.goalsMarkets.doubleChance['1X'] * 100).toFixed(1)}%`;
    dc12.textContent = `${(data.goalsMarkets.doubleChance['12'] * 100).toFixed(1)}%`;
    dcX2.textContent = `${(data.goalsMarkets.doubleChance['X2'] * 100).toFixed(1)}%`;
    document.getElementById('in-dc-1X').dataset.prob = data.goalsMarkets.doubleChance['1X'];
    document.getElementById('in-dc-12').dataset.prob = data.goalsMarkets.doubleChance['12'];
    document.getElementById('in-dc-X2').dataset.prob = data.goalsMarkets.doubleChance['X2'];
    
    labelDnb1.textContent = `${nameAVal.slice(0, 8)}:`;
    labelDnb2.textContent = `${nameBVal.slice(0, 8)}:`;
    dnb1.textContent = `${(data.goalsMarkets.dnb['1'] * 100).toFixed(1)}%`;
    dnb2.textContent = `${(data.goalsMarkets.dnb['2'] * 100).toFixed(1)}%`;
    document.getElementById('in-dnb-1').dataset.prob = data.goalsMarkets.dnb['1'];
    document.getElementById('in-dnb-2').dataset.prob = data.goalsMarkets.dnb['2'];
    
    ouGoalsTbody.innerHTML = "";
    data.goalsMarkets.overUnder.forEach(ou => {
      const tStr = ou.threshold.toString().replace('.', '');
      
      const idOver = `in-ou-goles-${tStr}-over`;
      const idUnder = `in-ou-goles-${tStr}-under`;
      
      const inO = document.getElementById(idOver);
      const inU = document.getElementById(idUnder);
      
      if (inO) inO.dataset.prob = ou.over;
      if (inU) inU.dataset.prob = ou.under;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${ou.threshold.toFixed(1)} Goles</strong></td>
        <td style="color: var(--color-team-b); font-weight: 700;">${(ou.over * 100).toFixed(1)}% <span id="ev-ou-goles-${tStr}-over" class="ev-mini"></span></td>
        <td style="color: rgba(244, 63, 94, 0.8); font-weight: 700;">${(ou.under * 100).toFixed(1)}% <span id="ev-ou-goles-${tStr}-under" class="ev-mini"></span></td>
      `;
      ouGoalsTbody.appendChild(tr);
    });

    if (data.goalsMarkets.asianHandicap) {
      thAhA.textContent = "Sí (%)";
      thAhB.textContent = "No (%)";
      ahTbody.innerHTML = "";

      const ahLinesData = [
        {
          label: `${nameAVal} -1.5`,
          probYes: data.goalsMarkets.asianHandicap["-1.5"].teamA,
          probNo: data.goalsMarkets.asianHandicap["-1.5"].teamB,
          tStrYes: "m15-a",
          tStrNo: "m15-b",
          idYes: "in-ah-m15-a",
          idNo: "in-ah-m15-b"
        },
        {
          label: `${nameBVal} -1.5`,
          probYes: data.goalsMarkets.asianHandicap["+1.5"].teamB,
          probNo: data.goalsMarkets.asianHandicap["+1.5"].teamA,
          tStrYes: "p15-b",
          tStrNo: "p15-a",
          idYes: "in-ah-p15-b",
          idNo: "in-ah-p15-a"
        },
        {
          label: `${nameAVal} -0.5`,
          probYes: data.goalsMarkets.asianHandicap["-0.5"].teamA,
          probNo: data.goalsMarkets.asianHandicap["-0.5"].teamB,
          tStrYes: "m05-a",
          tStrNo: "m05-b",
          idYes: "in-ah-m05-a",
          idNo: "in-ah-m05-b"
        },
        {
          label: `${nameBVal} -0.5`,
          probYes: data.goalsMarkets.asianHandicap["+0.5"].teamB,
          probNo: data.goalsMarkets.asianHandicap["+0.5"].teamA,
          tStrYes: "p05-b",
          tStrNo: "p05-a",
          idYes: "in-ah-p05-b",
          idNo: "in-ah-p05-a"
        }
      ];

      ahLinesData.forEach(row => {
        // Update dataset prob on the input elements dynamically
        const inYes = document.getElementById(row.idYes);
        const inNo = document.getElementById(row.idNo);
        if (inYes) inYes.dataset.prob = row.probYes;
        if (inNo) inNo.dataset.prob = row.probNo;

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${row.label}</strong></td>
          <td style="color: var(--color-team-b); font-weight: 700;">${(row.probYes * 100).toFixed(1)}% <span id="ev-ah-${row.tStrYes}" class="ev-mini"></span></td>
          <td style="color: rgba(244, 63, 94, 0.8); font-weight: 700;">${(row.probNo * 100).toFixed(1)}% <span id="ev-ah-${row.tStrNo}" class="ev-mini"></span></td>
        `;
        ahTbody.appendChild(tr);
      });
    }

    // --- Render corners prediction (Block 2) ---
    cornersPredictionCard.classList.remove("hidden");
    
    expectedCornersLabelA.textContent = `Córners ${nameAVal}`;
    expectedCornersLabelB.textContent = `Córners ${nameBVal}`;
    expectedCornersValA.textContent = data.cornersPrediction.expectedA.toFixed(1);
    expectedCornersValB.textContent = data.cornersPrediction.expectedB.toFixed(1);
    expectedCornersTotal.textContent = data.cornersPrediction.expectedTotal.toFixed(1);
    
    ouCornersTbody.innerHTML = "";
    data.cornersPrediction.overUnder.forEach(ou => {
      const tStr = ou.threshold.toString().replace('.', '');
      
      const idOver = `in-ou-corn-${tStr}-over`;
      const idUnder = `in-ou-corn-${tStr}-under`;
      
      const inO = document.getElementById(idOver);
      const inU = document.getElementById(idUnder);
      
      if (inO) inO.dataset.prob = ou.over;
      if (inU) inU.dataset.prob = ou.under;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${ou.threshold.toFixed(1)} Córners</strong></td>
        <td style="color: var(--color-team-b); font-weight: 700;">${(ou.over * 100).toFixed(1)}% <span id="ev-ou-corn-${tStr}-over" class="ev-mini"></span></td>
        <td style="color: rgba(244, 63, 94, 0.8); font-weight: 700;">${(ou.under * 100).toFixed(1)}% <span id="ev-ou-corn-${tStr}-under" class="ev-mini"></span></td>
      `;
      ouCornersTbody.appendChild(tr);
    });
    
    labelMostCornersA.textContent = `${nameAVal.slice(0, 8)}:`;
    labelMostCornersB.textContent = `${nameBVal.slice(0, 8)}:`;
    probMostCornersA.textContent = `${(data.cornersPrediction.probMostA * 100).toFixed(1)}%`;
    probMostCornersDraw.textContent = `${(data.cornersPrediction.probMostDraw * 100).toFixed(1)}%`;
    probMostCornersB.textContent = `${(data.cornersPrediction.probMostB * 100).toFixed(1)}%`;
    document.getElementById('in-most-corners-a').dataset.prob = data.cornersPrediction.probMostA;
    document.getElementById('in-most-corners-draw').dataset.prob = data.cornersPrediction.probMostDraw;
    document.getElementById('in-most-corners-b').dataset.prob = data.cornersPrediction.probMostB;

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

    // Render score heatmap matrix
    if (data.scoreHeatmap) {
      renderScoreHeatmap(data.scoreHeatmap, nameAVal, nameBVal);
    }

    // Render side-by-side comparative bars
    if (data.comparisonStats) {
      const statsA = data.comparisonStats.teamA;
      const statsB = data.comparisonStats.teamB;
      
      updateSideBySideBar(statsA.match_xg, statsB.match_xg, "comp-val-a-xg", "comp-bar-fill-a-xg", "comp-val-b-xg", "comp-bar-fill-b-xg", 2);
      updateSideBySideBar(statsA.xg_overall, statsB.xg_overall, "comp-val-a-xghist", "comp-bar-fill-a-xghist", "comp-val-b-xghist", "comp-bar-fill-b-xghist", 2);
      updateSideBySideBar(statsA.shots_per_90, statsB.shots_per_90, "comp-val-a-shots", "comp-bar-fill-a-shots", "comp-val-b-shots", "comp-bar-fill-b-shots", 1);
      updateSideBySideBar(statsA.crosses_per_90, statsB.crosses_per_90, "comp-val-a-crosses", "comp-bar-fill-a-crosses", "comp-val-b-crosses", "comp-bar-fill-b-crosses", 1);
      updateSideBySideBar(data.cornersPrediction.expectedA, data.cornersPrediction.expectedB, "comp-val-a-corners", "comp-bar-fill-a-corners", "comp-val-b-corners", "comp-bar-fill-b-corners", 1);
    }

    // Update analytical charts (including the radar chart)
    updateCharts(nameAVal, nameBVal, data.xgA, data.xgB, data.probWinA, data.probDraw, data.probWinB, data);

  } catch (error) {
    console.error("Prediction API error:", error);
  } finally {
    btnSimulate.disabled = false;
    simSpinner.classList.add("hidden");
    const numSimsFormatted = parseInt(simsSlider.value || 100000).toLocaleString();
    btnSimulate.querySelector(".btn-text").textContent = `🚀 SIMULAR ${numSimsFormatted} PARTIDOS`;
  }
}

async function loadBacktestMetrics() {
  try {
    const res = await fetch("/api/backtest-metrics");
    const json = await res.json();
    if (json.status === "ok") {
      renderBacktestMetrics(json.data);
    }
  } catch (error) {
    console.error("Error loading backtest metrics:", error);
  }
}

async function runBacktestFlow() {
  btnRunBacktest.disabled = true;
  backtestSpinner.classList.remove("hidden");
  btnRunBacktest.querySelector(".btn-text").textContent = "EJECUTANDO SCRIPT (Espera ~5s)...";

  try {
    const res = await fetch("/api/run-backtest", { method: "POST" });
    const json = await res.json();
    
    if (json.status === "success") {
      renderBacktestMetrics(json.data);
    } else {
      alert("Error ejecutando el backtest: " + (json.detail || "Error desconocido"));
    }
  } catch (error) {
    console.error("Error trigger backtest:", error);
    alert("Error de red ejecutando backtest.");
  } finally {
    btnRunBacktest.disabled = false;
    backtestSpinner.classList.add("hidden");
    btnRunBacktest.querySelector(".btn-text").textContent = "🚀 EJECUTAR BACKTEST (Tarda ~5s)";
  }
}

function renderBacktestMetrics(data) {
  if (backtestResultsContainer) backtestResultsContainer.classList.remove("hidden");
  
  if (data.financials) {
    if (btRoi) {
      btRoi.textContent = `${data.financials.roiPercent > 0 ? '+' : ''}${data.financials.roiPercent}%`;
      btRoi.style.color = data.financials.roiPercent >= 0 ? '#10B981' : '#EF4444';
    }
    if (btProfit) {
      btProfit.textContent = `${data.financials.profitUnits > 0 ? '+' : ''}${data.financials.profitUnits}`;
      btProfit.style.color = data.financials.profitUnits >= 0 ? '#10B981' : '#EF4444';
    }
    if (btBets) btBets.textContent = data.financials.betsPlaced.toLocaleString();
    
    if (btHitrate) {
      if (data.financials.betsPlaced > 0) {
        btHitrate.textContent = `${((data.financials.betsWon / data.financials.betsPlaced) * 100).toFixed(1)}%`;
      } else {
        btHitrate.textContent = "--%";
      }
    }
  }
  
  if (data.model) {
    if (btFavAcc) btFavAcc.textContent = `${(data.model.favouriteAccuracy * 100).toFixed(1)}%`;
    if (btBrier) btBrier.textContent = data.model.brier.toFixed(3);
    if (btLogloss) btLogloss.textContent = data.model.logloss.toFixed(3);
  }
  
  if (btMatches) btMatches.textContent = data.evaluated.toLocaleString();
  
  if (btDate) {
    const d = new Date(data.generatedAt);
    btDate.textContent = d.toLocaleString();
  }
}



/* ==========================================================================
   LOGGED PICKS FLOW (FASE 6)
   ========================================================================== */
async function logCurrentPick() {
  if (!lastSimulationResult) {
    alert("Primero debes realizar una simulación ejecutando el botón 🚀 SIMULAR.");
    return;
  }

  btnLogPick.disabled = true;
  logPickSpinner.classList.remove("hidden");
  btnLogPick.querySelector(".btn-text").textContent = "GUARDANDO...";

  const payload = {
    teamA: selectedTeamA,
    teamB: selectedTeamB,
    probWinA: lastSimulationResult.probWinA,
    probDraw: lastSimulationResult.probDraw,
    probWinB: lastSimulationResult.probWinB,
    xgA: lastSimulationResult.xgA,
    xgB: lastSimulationResult.xgB,
    strengthOverrideA: inputOverrideA.value ? parseFloat(inputOverrideA.value) : 1.0,
    strengthOverrideB: inputOverrideB.value ? parseFloat(inputOverrideB.value) : 1.0,
    altitude: inputAltitude.value ? parseInt(inputAltitude.value) : 0
  };

  try {
    const res = await fetch("/api/log-prediction", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (json.status === "success") {
      alert("✅ Pick guardado exitosamente en el historial.");
    } else {
      alert("Error al guardar pick: " + json.detail);
    }
  } catch (error) {
    console.error("Error logging pick:", error);
    alert("Error de red al guardar pick.");
  } finally {
    btnLogPick.disabled = false;
    logPickSpinner.classList.add("hidden");
    btnLogPick.querySelector(".btn-text").textContent = "📥 GUARDAR PICK";
  }
}

async function loadLoggedPicks() {
  loggedMatchList.innerHTML = `<div class="loading-placeholder">Cargando picks...</div>`;
  try {
    const res = await fetch("/api/logged-predictions");
    const json = await res.json();
    renderLoggedPicks(json.predictions);
  } catch (error) {
    console.error("Error loading logged picks:", error);
    loggedMatchList.innerHTML = `<div class="loading-placeholder">Error al cargar picks.</div>`;
  }
}

async function updateLoggedPicksResults() {
  btnUpdateLogged.disabled = true;
  loggedUpdateSpinner.classList.remove("hidden");
  btnUpdateLogged.querySelector(".btn-text").textContent = "ACTUALIZANDO...";

  try {
    const res = await fetch("/api/update-prediction-results", { method: "POST" });
    const json = await res.json();
    if (json.status === "success") {
      renderLoggedPicks(json.predictions, json.summary);
    } else {
      alert("Error al actualizar: " + json.detail);
    }
  } catch (error) {
    console.error("Error updating logged results:", error);
    alert("Error al conectar con la API de actualización.");
  } finally {
    btnUpdateLogged.disabled = false;
    loggedUpdateSpinner.classList.add("hidden");
    btnUpdateLogged.querySelector(".btn-text").textContent = "🔄 ACTUALIZAR RESULTADOS";
  }
}

function renderLoggedPicks(predictions, summary = null) {
  loggedMatchList.innerHTML = "";

  if (!predictions || predictions.length === 0) {
    loggedMatchList.innerHTML = `<div class="loading-placeholder">No hay picks registrados aún. Guarda un pick usando el botón "Guardar Pick" en el panel de simulación.</div>`;
    loggedSummaryContainer.classList.add("hidden");
    return;
  }

  // Handle summary rendering
  if (summary) {
    loggedSummaryContainer.classList.remove("hidden");
    loggedAccuracy.textContent = `${summary.accuracyPercent}%`;
    loggedRps.textContent = summary.avgRps.toFixed(4);
    loggedTotalCount.textContent = summary.totalLogged;
    loggedCompletedCount.textContent = summary.totalCompleted;
  } else {
    // Try to compute simple summary if not provided
    const completed = predictions.filter(p => p.status === "completed");
    if (completed.length > 0) {
      loggedSummaryContainer.classList.remove("hidden");
      const correct = completed.filter(p => p.isCorrect).length;
      const accVal = (correct / completed.length * 100).toFixed(1);
      const rpsSum = completed.reduce((sum, p) => sum + (p.rps || 0), 0);
      const avgRpsVal = rpsSum / completed.length;
      
      loggedAccuracy.textContent = `${accVal}%`;
      loggedRps.textContent = avgRpsVal.toFixed(4);
      loggedTotalCount.textContent = predictions.length;
      loggedCompletedCount.textContent = completed.length;
    } else {
      loggedSummaryContainer.classList.add("hidden");
    }
  }

  predictions.forEach(p => {
    const metaA = TEAM_METADATA[p.teamA] || { name: p.teamA.toUpperCase(), flag: "🏳️" };
    const metaB = TEAM_METADATA[p.teamB] || { name: p.teamB.toUpperCase(), flag: "🏳️" };

    const card = document.createElement("div");
    
    let outcomeClass = "match-outcome-draw";
    let statusText = "Pendiente";
    let statusColor = "var(--color-text-secondary)";
    
    if (p.status === "completed") {
      outcomeClass = p.isCorrect ? "match-outcome-win" : "match-outcome-loss";
      statusText = `${p.isCorrect ? '✅ Acierto' : '❌ Fallo'} (Pick: ${p.pick === 'A' ? metaA.name.slice(0,6) : p.pick === 'B' ? metaB.name.slice(0,6) : 'Emp.'} / Real: ${p.actualScore})`;
      statusColor = p.isCorrect ? "#10b981" : "#ef4444";
    }

    const d = new Date(p.timestamp);
    const dateStr = d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    card.className = `match-card ${outcomeClass}`;
    card.style.flexDirection = "column";
    card.style.alignItems = "stretch";
    card.style.gap = "6px";
    card.style.padding = "12px";

    let actionButtonsHtml = "";
    if (p.status === "pending") {
      actionButtonsHtml = `
        <div style="display: flex; gap: 8px; margin-top: 8px; justify-content: flex-end; border-top: 1px solid rgba(255,255,255,0.03); padding-top: 8px;">
          <button class="btn btn-resolve-win" data-id="${p.id}" style="padding: 4px 10px; font-size: 0.75rem; background: #059669; border: none; border-radius: 4px; color: white; cursor: pointer; font-weight: 600; transition: opacity 0.2s;">✅ GANADO</button>
          <button class="btn btn-resolve-loss" data-id="${p.id}" style="padding: 4px 10px; font-size: 0.75rem; background: #dc2626; border: none; border-radius: 4px; color: white; cursor: pointer; font-weight: 600; transition: opacity 0.2s;">❌ PERDIDO</button>
        </div>
      `;
    }

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted);">
        <span>${dateStr}</span>
        <span style="font-weight: 600; color: ${statusColor};">${statusText}</span>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 2px;">
        <span style="font-weight: 600; font-size: 0.95rem;">${metaA.flag} ${metaA.name} vs ${metaB.flag} ${metaB.name}</span>
        <span class="badge" style="font-size: 0.8rem; background: rgba(255,255,255,0.06);">${p.xgA.toFixed(1)} - ${p.xgB.toFixed(1)} xG</span>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--color-text-secondary); margin-top: 4px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.03);">
        <span>Probs: ${metaA.name.slice(0,5)} ${(p.probWinA*100).toFixed(0)}% / Emp ${(p.probDraw*100).toFixed(0)}% / ${metaB.name.slice(0,5)} ${(p.probWinB*100).toFixed(0)}%</span>
        ${p.altitude > 0 ? `<span style="font-size: 0.75rem; color: #a5b4fc;">🏔️ ${p.altitude}m</span>` : ''}
      </div>
      ${actionButtonsHtml}
    `;

    loggedMatchList.appendChild(card);
  });
}

async function resolvePick(id, isCorrect) {
  try {
    const res = await fetch("/api/resolve-prediction", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, isCorrect })
    });
    const json = await res.json();
    if (json.status === "success") {
      renderLoggedPicks(json.predictions, json.summary);
    } else {
      alert("Error al resolver el pick: " + json.detail);
    }
  } catch (error) {
    console.error("Error resolving pick:", error);
    alert("Error de red al resolver el pick.");
  }
}

// Event delegation for resolve buttons
if (loggedMatchList) {
  loggedMatchList.addEventListener("click", async function(e) {
    if (e.target && e.target.classList.contains("btn-resolve-win")) {
      const id = parseInt(e.target.dataset.id);
      await resolvePick(id, true);
    } else if (e.target && e.target.classList.contains("btn-resolve-loss")) {
      const id = parseInt(e.target.dataset.id);
      await resolvePick(id, false);
    }
  });
}

// Start the app on load
document.addEventListener("DOMContentLoaded", initializeApp);

// Dynamic EV calculation for market odds inputs in the left panel
document.addEventListener('input', function(e) {
  if (e.target && e.target.classList.contains('dyn-odds')) {
    const prob = parseFloat(e.target.dataset.prob);
    const odds = parseFloat(e.target.value);
    
    // Buscar el span de destino usando el atributo data-target
    const targetId = e.target.dataset.target;
    if (!targetId) return;
    
    const evSpan = document.getElementById(targetId);
    
    if (evSpan) {
      if (!isNaN(prob) && !isNaN(odds) && odds > 1.0) {
        const ev = (prob * odds) - 1;
        const evPct = (ev * 100).toFixed(1);
        if (ev > 0) {
          evSpan.textContent = `+${evPct}% EV`;
          evSpan.className = 'ev-mini ev-pos';
        } else {
          evSpan.textContent = `${evPct}% EV`;
          evSpan.className = 'ev-mini ev-neg';
        }
      } else {
        evSpan.textContent = '';
        evSpan.className = 'ev-mini';
      }
    }
  }
});