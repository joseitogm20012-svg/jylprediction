// Interceptor global de fetch para redireccionar al backend local si se abre como archivo local o puerto distinto
const originalFetch = window.fetch;
window.fetch = function(input, init) {
  if (typeof input === 'string' && input.startsWith('/api')) {
    const isLocalFile = window.location.protocol === 'file:';
    const isDifferentPort = window.location.port !== '3000' && window.location.port !== '';
    if (isLocalFile || isDifferentPort) {
      input = 'http://localhost:3000' + input;
    }
  }
  return originalFetch(input, init);
};

// Supabase Configuration — loaded from /api/config (env vars on server)
let supabaseUrl = "";
let supabaseAnonKey = "";
let supabaseClient = null;
let configLoaded = false;

async function loadPublicConfig() {
  if (configLoaded) return;
  const res = await fetch("/api/config");
  if (!res.ok) {
    console.warn("No se pudo cargar la configuración pública:", await res.text());
    return;
  }
  const data = await res.json();
  supabaseUrl = data.supabaseUrl || "";
  supabaseAnonKey = data.supabaseAnonKey || "";
  configLoaded = true;
}

function getSupabase() {
  if (!supabaseUrl || !supabaseAnonKey) return null;
  if (!supabaseClient) {
    if (typeof supabase !== 'undefined') {
      supabaseClient = supabase.createClient(supabaseUrl, supabaseAnonKey);
    } else if (window.supabase) {
      supabaseClient = window.supabase.createClient(supabaseUrl, supabaseAnonKey);
    }
  }
  return supabaseClient;
}

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
let currentUser = null;
let currentSessionToken = null;

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
const inputHostCountry = document.getElementById("input-host-country");

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
    await loadPublicConfig();

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
        window.tsSelectA = new TomSelect("#select-team-a", {
          create: false,
          sortField: { field: "text", direction: "asc" }
        });
        
        window.tsSelectB = new TomSelect("#select-team-b", {
          create: false,
          sortField: { field: "text", direction: "asc" }
        });

        window.tsAiTeamA = new TomSelect("#ai-team-a", {
          create: false,
          sortField: { field: "text", direction: "asc" }
        });

        window.tsAiTeamB = new TomSelect("#ai-team-b", {
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

    // 4.5. Load Presets listeners
    initPresets();
    updateWeightsPreview();

    // 5. Update UI for the initial match
    updateMatchCard();

    // 6. Ready (Wait for manual simulation)
    initBetBuilder();

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
    const textContent = `${TEAM_METADATA[slug].flag} ${TEAM_METADATA[slug].name}`;

    const optA = document.createElement("option");
    optA.value = slug;
    optA.textContent = textContent;
    if (slug === selectedTeamA) optA.selected = true;
    selectA.appendChild(optA);

    const optB = document.createElement("option");
    optB.value = slug;
    optB.textContent = textContent;
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
    const rank = TEAM_METADATA[selectedTeamA].rank;
    rankSliderA.value = rank;
    updateMatchCard();
  });

  selectB.addEventListener("change", (e) => {
    selectedTeamB = e.target.value;
    const rank = TEAM_METADATA[selectedTeamB].rank;
    rankSliderB.value = rank;
    updateMatchCard();
  });

  rankSliderA.addEventListener("input", (e) => {
    fifaDisplayA.textContent = `FIFA #${e.target.value}`;
  });

  rankSliderB.addEventListener("input", (e) => {
    fifaDisplayB.textContent = `FIFA #${e.target.value}`;
  });

  // Sync Sliders and Numeric Fields from Card 2
  const sliderFifa = document.getElementById("slider-weight-fifa");
  if (sliderFifa) {
    sliderFifa.addEventListener("input", (e) => {
      weightFifaSlider.value = e.target.value;
      updateWeightsPreview();
    });
  }
  weightFifaSlider.addEventListener("input", (e) => {
    if (sliderFifa) sliderFifa.value = e.target.value;
    updateWeightsPreview();
  });

  const sliderH2h = document.getElementById("slider-weight-h2h");
  if (sliderH2h) {
    sliderH2h.addEventListener("input", (e) => {
      weightH2hSlider.value = e.target.value;
      updateWeightsPreview();
    });
  }
  weightH2hSlider.addEventListener("input", (e) => {
    if (sliderH2h) sliderH2h.value = e.target.value;
    updateWeightsPreview();
  });

  const sliderDecay = document.getElementById("slider-decay");
  if (sliderDecay) {
    sliderDecay.addEventListener("input", (e) => {
      decaySlider.value = e.target.value;
      updateMatchCard(true);
    });
  }
  decaySlider.addEventListener("input", (e) => {
    if (sliderDecay) sliderDecay.value = e.target.value;
    updateMatchCard(true);
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
        if (targetId === "tab-analysis") {
          fetchAITacticalAnalysis(selectedTeamA, selectedTeamB);
        } else if (targetId === "tab-favorites") {
          loadUserFavorites();
          loadUserPresets();
        } else if (targetId === "tab-leaderboard") {
          loadLeaderboard();
        }
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
  if (inputHostCountry) {
    inputHostCountry.addEventListener("change", () => {
      const resultsTabHeader = document.getElementById("results-tab-header");
      if (resultsTabHeader && !resultsTabHeader.classList.contains("hidden")) {
        runPredictionFlow();
      }
    });
  }

  // Real-time update for manual weight changes
  if (weightFifaSlider) {
    weightFifaSlider.addEventListener("input", () => {
      updateWeightsPreview();
      const resultsTabHeader = document.getElementById("results-tab-header");
      if (resultsTabHeader && !resultsTabHeader.classList.contains("hidden")) {
        runPredictionFlow();
      }
    });
  }

  if (weightH2hSlider) {
    weightH2hSlider.addEventListener("input", () => {
      updateWeightsPreview();
      const resultsTabHeader = document.getElementById("results-tab-header");
      if (resultsTabHeader && !resultsTabHeader.classList.contains("hidden")) {
        runPredictionFlow();
      }
    });
  }

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
  
  // ----------------------------------------------------
  // Bind new user action listeners
  // ----------------------------------------------------
  const btnSaveFav = document.getElementById("btn-save-favorite");
  if (btnSaveFav) {
    btnSaveFav.addEventListener("click", async () => {
      if (!currentSessionToken || !lastSimulationResult) return;
      
      const txtNotes = document.getElementById("textarea-private-notes");
      const notesVal = txtNotes ? txtNotes.value.trim() : "";
      
      btnSaveFav.disabled = true;
      btnSaveFav.textContent = "Guardando...";
      
      try {
        const res = await fetch("/api/user/favorites", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${currentSessionToken}`
          },
          body: JSON.stringify({
            teamA: selectedTeamA,
            teamB: selectedTeamB,
            xgA: lastSimulationResult.xgA,
            xgB: lastSimulationResult.xgB,
            probWinA: lastSimulationResult.probWinA,
            probDraw: lastSimulationResult.probDraw,
            probWinB: lastSimulationResult.probWinB,
            notes: notesVal
          })
        });
        const json = await res.json();
        if (json.status === "success") {
          btnSaveFav.textContent = "⭐ ¡Guardado!";
          loadUserFavorites();
          setTimeout(() => {
            btnSaveFav.disabled = false;
            btnSaveFav.textContent = "⭐ Guardar en Favoritos";
          }, 1500);
        } else {
          alert("Error al guardar favorito: " + json.detail);
          btnSaveFav.disabled = false;
          btnSaveFav.textContent = "⭐ Guardar en Favoritos";
        }
      } catch (err) {
        console.error("Error saving favorite:", err);
        btnSaveFav.disabled = false;
        btnSaveFav.textContent = "⭐ Guardar en Favoritos";
      }
    });
  }

  // Poll Vote Buttons
  const btnVoteA = document.getElementById("btn-vote-a");
  const btnVoteDraw = document.getElementById("btn-vote-draw");
  const btnVoteB = document.getElementById("btn-vote-b");
  
  const castPollVote = async (voteVal) => {
    if (!currentSessionToken) return;
    try {
      const res = await fetch("/api/match/vote", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${currentSessionToken}`
        },
        body: JSON.stringify({
          teamA: selectedTeamA,
          teamB: selectedTeamB,
          vote: voteVal
        })
      });
      const json = await res.json();
      if (json.status === "success") {
        loadPollData();
      }
    } catch (err) {
      console.error("Error casting vote:", err);
    }
  };

  if (btnVoteA) btnVoteA.addEventListener("click", () => castPollVote("A"));
  if (btnVoteDraw) btnVoteDraw.addEventListener("click", () => castPollVote("Draw"));
  if (btnVoteB) btnVoteB.addEventListener("click", () => castPollVote("B"));

  // Presets Save Button
  const btnSavePreset = document.getElementById("btn-save-preset");
  if (btnSavePreset) {
    btnSavePreset.addEventListener("click", async () => {
      if (!currentSessionToken) return;
      const presetName = prompt("Introduce un nombre para tu preset personalizado (ej. 'Mi Modelo Ofensivo'):");
      if (!presetName || !presetName.trim()) return;
      
      const wFifa = document.getElementById("input-weight-fifa");
      const wH2h = document.getElementById("input-weight-h2h");
      const decay = document.getElementById("input-decay");
      const ovrA = document.getElementById("input-override-a");
      const ovrB = document.getElementById("input-override-b");
      const altitude = document.getElementById("input-altitude");
      
      const payload = {
        presetName: presetName.trim(),
        fifaWeight: parseFloat(wFifa ? wFifa.value : 30),
        h2hWeight: parseFloat(wH2h ? wH2h.value : 20),
        decayMonths: parseFloat(decay ? decay.value : 18),
        strengthOverrideA: parseFloat(ovrA ? ovrA.value : 1.0),
        strengthOverrideB: parseFloat(ovrB ? ovrB.value : 1.0),
        altitude: parseInt(altitude ? altitude.value : 0)
      };
      
      try {
        const res = await fetch("/api/user/presets", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${currentSessionToken}`
          },
          body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.status === "success") {
          loadUserPresets();
        } else {
          alert("Error al guardar preset: " + json.detail);
        }
      } catch (err) {
        console.error("Error saving preset:", err);
      }
    });
  }

  // Pronóstico Oficial Leaderboard Button
  const btnSubmitPronostic = document.getElementById("btn-submit-pronostic");
  if (btnSubmitPronostic) {
    btnSubmitPronostic.addEventListener("click", async () => {
      if (!currentSessionToken) return;
      const metaA = TEAM_METADATA[selectedTeamA] || { name: selectedTeamA.toUpperCase() };
      const metaB = TEAM_METADATA[selectedTeamB] || { name: selectedTeamB.toUpperCase() };
      
      const choice = prompt(`Selecciona tu pronóstico oficial para el ranking:\nEscribe 'A' para victoria de ${metaA.name}\nEscribe 'D' para Empate\nEscribe 'B' para victoria de ${metaB.name}`);
      if (!choice) return;
      
      let guessVal = "";
      if (choice.trim().toUpperCase() === "A") guessVal = "A";
      else if (choice.trim().toUpperCase() === "D") guessVal = "Draw";
      else if (choice.trim().toUpperCase() === "B") guessVal = "B";
      else {
        alert("Opción no válida. Escribe 'A', 'D' o 'B'.");
        return;
      }
      
      btnSubmitPronostic.disabled = true;
      btnSubmitPronostic.textContent = "Enviando...";
      
      try {
        const res = await fetch("/api/match/pronostic", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${currentSessionToken}`
          },
          body: JSON.stringify({
            teamA: selectedTeamA,
            teamB: selectedTeamB,
            guess: guessVal
          })
        });
        const json = await res.json();
        if (json.status === "success") {
          loadUserPronosticStatus();
          loadLeaderboard();
        } else {
          alert(json.detail || "Error al registrar pronóstico.");
          loadUserPronosticStatus();
        }
      } catch (err) {
        console.error("Error submitting pronostic:", err);
        loadUserPronosticStatus();
      }
    });
  }
  
  // Initialize Supabase User Authentication bindings (Login, Register, Session)
  initSupabaseAuth();
}

function updateMatchCard(fullReload = true) {
  const metaA = TEAM_METADATA[selectedTeamA];
  const metaB = TEAM_METADATA[selectedTeamB];

  // Update names, flags and stats
  nameA.textContent = metaA.name;
  nameB.textContent = metaB.name;
  flagA.textContent = metaA.flag;
  flagB.textContent = metaB.flag;

  const largeFlagA = document.getElementById("bb-flag-a-large");
  const largeFlagB = document.getElementById("bb-flag-b-large");
  if (largeFlagA) largeFlagA.textContent = metaA.flag;
  if (largeFlagB) largeFlagB.textContent = metaB.flag;

  // Make sure Select dropdowns are in sync
  if (window.tsSelectA && window.tsSelectA.getValue() !== selectedTeamA) {
    window.tsSelectA.setValue(selectedTeamA, true);
  }
  if (window.tsSelectB && window.tsSelectB.getValue() !== selectedTeamB) {
    window.tsSelectB.setValue(selectedTeamB, true);
  }

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

  // Update DNB placeholders
  const inDnb1 = document.getElementById("in-dnb-1");
  const inDnb2 = document.getElementById("in-dnb-2");
  if (inDnb1) inDnb1.placeholder = `${metaA.name.slice(0, 8)} DNB`;
  if (inDnb2) inDnb2.placeholder = `${metaB.name.slice(0, 8)} DNB`;

  // Update Asian Handicap placeholders
  const inAhM15a = document.getElementById("in-ah-m15-a");
  const inAhM15b = document.getElementById("in-ah-m15-b");
  const inAhM05a = document.getElementById("in-ah-m05-a");
  const inAhM05b = document.getElementById("in-ah-m05-b");
  const inAhP05a = document.getElementById("in-ah-p05-a");
  const inAhP05b = document.getElementById("in-ah-p05-b");
  const inAhP15a = document.getElementById("in-ah-p15-a");
  const inAhP15b = document.getElementById("in-ah-p15-b");

  if (inAhM15a) inAhM15a.placeholder = `${metaA.name.slice(0, 8)} -1.5`;
  if (inAhM15b) inAhM15b.placeholder = `${metaB.name.slice(0, 8)} +1.5`;
  if (inAhM05a) inAhM05a.placeholder = `${metaA.name.slice(0, 8)} -0.5`;
  if (inAhM05b) inAhM05b.placeholder = `${metaB.name.slice(0, 8)} +0.5`;
  if (inAhP05a) inAhP05a.placeholder = `${metaA.name.slice(0, 8)} +0.5`;
  if (inAhP05b) inAhP05b.placeholder = `${metaB.name.slice(0, 8)} -0.5`;
  if (inAhP15a) inAhP15a.placeholder = `${metaA.name.slice(0, 8)} +1.5`;
  if (inAhP15b) inAhP15b.placeholder = `${metaB.name.slice(0, 8)} -1.5`;

  if (fullReload) {
    // Reload recent matches lists and H2H calculations from Python API
    loadRecentMatches(selectedTeamA, matchListA, historyTitleA, "Uruguay");
    loadRecentMatches(selectedTeamB, matchListB, historyTitleB, "Arabia Saudita");
    loadH2HData();
    loadAdvancedH2HData();
    
    // Check and load AI analysis if it was already saved for this match
    fetchAITacticalAnalysis(selectedTeamA, selectedTeamB);
    
    // Load community poll and official predictions status
    loadPollData();
    loadUserPronosticStatus();
  }

  if (typeof updateBetBuilderLabels === 'function') {
    updateBetBuilderLabels();
  }
  if (typeof runBetBuilderSimulation === 'function') {
    runBetBuilderSimulation();
  }
}

/* ==========================================================================
   API DATA CALLS (HISTORY, H2H, PREDICT)
   ========================================================================== */
function updateRecentFormAndSparkline(teamSlug, dataHistory, prefix) {
  const badgeContainer = document.getElementById(`bb-form-badges-${prefix}`);
  const svgElement = document.getElementById(`bb-sparkline-${prefix}`);
  if (!badgeContainer || !svgElement) return;

  badgeContainer.innerHTML = "";
  
  const matches = dataHistory.slice(0, 5);
  if (matches.length === 0) {
    badgeContainer.innerHTML = `<span style="font-size:0.72rem; color:var(--color-text-secondary);">Sin partidos</span>`;
    svgElement.innerHTML = "";
    return;
  }

  const outcomes = [];
  const points = [];
  
  matches.forEach((m, idx) => {
    let outcome = "D";
    let y = 25;
    let badgeClass = "draw";
    if (m.goalsScored > m.goalsConceded) {
      outcome = "W";
      y = 10;
      badgeClass = "win";
    } else if (m.goalsScored < m.goalsConceded) {
      outcome = "L";
      y = 30;
      badgeClass = "loss";
    }
    outcomes.push({ outcome, badgeClass });
    points.push({ x: 10 + idx * 20, y });
  });

  outcomes.forEach(o => {
    const badge = document.createElement("span");
    badge.className = `bb-form-badge ${o.badgeClass}`;
    badge.textContent = o.outcome;
    badgeContainer.appendChild(badge);
  });

  let pathD = `M ${points[0].x} ${points[0].y}`;
  let circlesHtml = `<circle cx="${points[0].x}" cy="${points[0].y}" r="3" fill="${getOutcomeColor(outcomes[0].badgeClass)}" />`;
  
  for (let i = 1; i < points.length; i++) {
    pathD += ` L ${points[i].x} ${points[i].y}`;
    circlesHtml += `<circle cx="${points[i].x}" cy="${points[i].y}" r="3" fill="${getOutcomeColor(outcomes[i].badgeClass)}" />`;
  }

  svgElement.innerHTML = `
    <path d="${pathD}" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    ${circlesHtml}
  `;
}

function getOutcomeColor(badgeClass) {
  if (badgeClass === "win") return "#10b981";
  if (badgeClass === "draw") return "#f59e0b";
  return "#ef4444";
}

async function loadRecentMatches(teamSlug, listElement, titleElement, defaultName) {
  const meta = TEAM_METADATA[teamSlug] || { name: defaultName, flag: "" };
  if (titleElement) titleElement.textContent = `Partidos de ${meta.name}`;
  if (listElement) listElement.innerHTML = `<div class="loading-placeholder">Cargando partidos...</div>`;

  try {
    const decay = parseInt(decaySlider.value);
    const res = await fetch(`/api/history/${teamSlug}?decay_months=${decay}`);
    const data = await res.json();
    
    // Update visual Recent Form badges and sparkline chart
    if (teamSlug === selectedTeamA) {
      updateRecentFormAndSparkline(teamSlug, data.history, "a");
    } else if (teamSlug === selectedTeamB) {
      updateRecentFormAndSparkline(teamSlug, data.history, "b");
    }
    
    if (listElement) {
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
    }

  } catch (error) {
    console.error("Error loading recent matches:", error);
    if (listElement) {
      listElement.innerHTML = `<div class="loading-placeholder">Error al cargar partidos de la API.</div>`;
    }
  }
}

async function loadH2HData() {
  // Keep the old H2H modifier for backward compatibility with predict calculation
  try {
    const res = await fetch(`/api/h2h/${selectedTeamA}/${selectedTeamB}`);
    const data = await res.json();
    // Update old H2H modifier display in analysis tab
    const h2hModifierValEl = document.getElementById('h2h-modifier-val');
    if (h2hModifierValEl) {
      const avgGd = data.avgGd;
      const h2hWeight = parseInt(weightH2hSlider.value) / 100.0;
      const h2hMultA = 1.0 + (avgGd / 4.0) * h2hWeight;
      const h2hMultB = 1.0 - (avgGd / 4.0) * h2hWeight;
      h2hModifierValEl.textContent = `${h2hMultA.toFixed(2)}x / ${h2hMultB.toFixed(2)}x`;
    }
    // Old h2h elements (if still referenced in analyze tab)
    if (h2hWinsA) h2hWinsA.textContent = data.winsA;
    if (h2hWinsB) h2hWinsB.textContent = data.winsB;
    if (h2hDraws) h2hDraws.textContent = data.draws;
  } catch(e) {
    console.warn('Error loading basic H2H for modifier:', e);
  }
}

// ===== ADVANCED H2H CENTER =====
let h2hAdvancedCharts = { radar: null, doughnut: null, period: null };

function switchH2HSubTab(name) {
  document.querySelectorAll('.h2h-subtab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.h2h-subtab-content').forEach(c => c.classList.remove('active'));
  const btn = document.getElementById(`h2hst-btn-${name}`);
  const content = document.getElementById(`h2hst-${name}`);
  if (btn) btn.classList.add('active');
  if (content) content.classList.add('active');
  // Trigger chart resize when switching to charts tab
  if (name === 'charts') {
    setTimeout(() => {
      Object.values(h2hAdvancedCharts).forEach(ch => { if (ch) ch.resize(); });
    }, 50);
  }
}

async function loadAdvancedH2HData() {
  const loadingEl = document.getElementById('h2h-center-loading');
  const contentEl = document.getElementById('h2h-center-content');
  if (!loadingEl || !contentEl) return;

  loadingEl.style.display = 'flex';
  contentEl.style.display = 'none';

  try {
    const res = await fetch(`/api/history/advanced/${selectedTeamA}/${selectedTeamB}`);
    if (!res.ok) throw new Error('API error ' + res.status);
    const data = await res.json();

    const metaA = TEAM_METADATA[selectedTeamA] || { name: selectedTeamA, flag: '🏳️' };
    const metaB = TEAM_METADATA[selectedTeamB] || { name: selectedTeamB, flag: '🏳️' };

    // ── Header
    document.getElementById('h2h-center-flag-a').textContent = metaA.flag || '🏳️';
    document.getElementById('h2h-center-flag-b').textContent = metaB.flag || '🏳️';
    document.getElementById('h2h-center-name-a').textContent = metaA.name;
    document.getElementById('h2h-center-name-b').textContent = metaB.name;
    document.getElementById('h2h-center-last-badge').textContent = data.h2h.lastWinner || '—';

    const h2h = data.h2h;
    const scorers = data.scorers;
    const form = data.form;
    const insights = data.insights;
    const count = h2h.count;

    // ── Advanced Stats Grid
    const advGrid = document.getElementById('h2h-adv-stats-grid');
    if (advGrid) {
      advGrid.innerHTML = `
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${count}</span><span class="h2h-adv-stat-label">Total H2H</span></div>
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${h2h.winsA}</span><span class="h2h-adv-stat-label">${metaA.name.slice(0,10)} Victorias</span></div>
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${h2h.draws}</span><span class="h2h-adv-stat-label">Empates</span></div>
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${h2h.winsB}</span><span class="h2h-adv-stat-label">${metaB.name.slice(0,10)} Victorias</span></div>
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${h2h.avgGoals.toFixed(1)}</span><span class="h2h-adv-stat-label">Goles/Partido</span></div>
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${h2h.goalsA}</span><span class="h2h-adv-stat-label">Goles ${metaA.name.slice(0,8)}</span></div>
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${h2h.goalsB}</span><span class="h2h-adv-stat-label">Goles ${metaB.name.slice(0,8)}</span></div>
        <div class="h2h-adv-stat" title="${h2h.biggestWin}"><span class="h2h-adv-stat-num" style="font-size:0.75rem;">🏆</span><span class="h2h-adv-stat-label" style="font-size: 0.58rem; line-height: 1.3;">${h2h.biggestWin}</span></div>
      `;
    }

    // ── Win dominance bar
    if (count > 0) {
      const pA = Math.round(h2h.winsA / count * 100);
      const pD = Math.round(h2h.draws / count * 100);
      const pB = 100 - pA - pD;
      document.getElementById('h2h-bar-a').style.width = pA + '%';
      document.getElementById('h2h-bar-draw').style.width = pD + '%';
      document.getElementById('h2h-bar-b').style.width = Math.max(0, pB) + '%';
      document.getElementById('h2h-winbar-sample').textContent = `${count} partidos`;
      document.getElementById('h2h-bar-legend-a').textContent = `${metaA.name.slice(0,8)}: ${h2h.winsA}V (${pA}%)`;
      document.getElementById('h2h-bar-legend-d').textContent = `${h2h.draws}E (${pD}%)`;
      document.getElementById('h2h-bar-legend-b').textContent = `${metaB.name.slice(0,8)}: ${h2h.winsB}V (${Math.max(0,pB)}%)`;
    }

    // ── Patterns
    document.getElementById('h2h-btts-pct').textContent = h2h.patterns.btts + '%';
    document.getElementById('h2h-o25-pct').textContent = h2h.patterns.over25 + '%';
    document.getElementById('h2h-csa-pct').textContent = h2h.patterns.csA + '%';
    document.getElementById('h2h-csb-pct').textContent = h2h.patterns.csB + '%';
    document.getElementById('h2h-csa-lbl').textContent = `CS ${metaA.name.slice(0,8)}`;
    document.getElementById('h2h-csb-lbl').textContent = `CS ${metaB.name.slice(0,8)}`;

    // ── Conditions
    document.getElementById('h2h-cond-home').textContent = h2h.byCondition.homeA;
    document.getElementById('h2h-cond-away').textContent = h2h.byCondition.awayA;
    document.getElementById('h2h-cond-neutral').textContent = h2h.byCondition.neutral;
    document.getElementById('h2h-cond-home-lbl').textContent = `${metaA.name.slice(0,8)} de Local`;
    document.getElementById('h2h-cond-away-lbl').textContent = `${metaA.name.slice(0,8)} de Visit.`;

    // ── Most frequent scores
    const scoresTbody = document.getElementById('h2h-scores-tbody');
    if (scoresTbody) {
      if (h2h.mostFrequentScores.length === 0) {
        scoresTbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding: 20px; color: var(--color-text-muted);">Sin datos</td></tr>`;
      } else {
        const maxCount = h2h.mostFrequentScores[0].count;
        scoresTbody.innerHTML = h2h.mostFrequentScores.map(s => {
          const barW = Math.round(s.count / maxCount * 100);
          const freq = count > 0 ? Math.round(s.count / count * 100) : 0;
          return `<tr>
            <td><span class="h2h-score-badge">${s.score}</span></td>
            <td style="font-family: var(--font-family-mono); font-weight: 700;">${s.count}x</td>
            <td style="min-width: 80px;">
              <div style="display: flex; align-items: center; gap: 6px;">
                <div class="h2h-score-bar-mini" style="width: ${barW}px; max-width: 80px;"></div>
                <span style="font-size: 0.7rem; color: var(--color-text-muted);">${freq}%</span>
              </div>
            </td>
          </tr>`;
        }).join('');
      }
    }

    // ── Competition breakdown
    const compTbody = document.getElementById('h2h-comp-tbody');
    if (compTbody) {
      if (!h2h.byCompetition.length) {
        compTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px; color: var(--color-text-muted);">Sin datos</td></tr>`;
      } else {
        const sorted = [...h2h.byCompetition].sort((a, b) => b.pj - a.pj);
        compTbody.innerHTML = sorted.map(c => `<tr>
          <td style="max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.76rem;">${c.competition}</td>
          <td style="text-align: center; font-family: var(--font-family-mono); font-weight: 700;">${c.pj}</td>
          <td style="text-align: center; color: var(--color-team-a); font-weight: 700;">${c.winsA}</td>
          <td style="text-align: center; color: #6b7280; font-weight: 700;">${c.draws}</td>
          <td style="text-align: center; color: var(--color-team-b); font-weight: 700;">${c.winsB}</td>
        </tr>`).join('');
      }
    }

    // ── Timeline
    const timelineEl = document.getElementById('h2h-timeline-list');
    if (timelineEl) {
      const timeline = [...(h2h.timeline || [])].reverse(); // newest first
      if (!timeline.length) {
        timelineEl.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--color-text-muted); font-size: 0.82rem;">Sin partidos registrados</div>`;
      } else {
        timelineEl.innerHTML = timeline.map(m => {
          const isAHome = m.homeName === metaA.name || (m.homeName && m.homeName.toLowerCase().includes(selectedTeamA.split('-')[0]));
          const gsA = isAHome ? m.hg : m.ag;
          const gsB = isAHome ? m.ag : m.hg;
          const winClass = gsA > gsB ? 'win-a' : (gsA < gsB ? 'win-b' : 'draw');
          return `<div class="h2h-timeline-match ${winClass}">
            <span class="h2h-timeline-date">${m.date}</span>
            <span class="h2h-timeline-teams">${m.homeName} vs ${m.awayName}</span>
            <span class="h2h-timeline-score">${m.hg} – ${m.ag}</span>
            <span class="h2h-timeline-comp">${m.tournament || ''}</span>
          </div>`;
        }).join('');
      }
    }

    // ══ SCORERS TAB ══
    const scorersGrid = document.getElementById('h2h-scorers-grid');
    if (scorersGrid) {
      if (!scorers.topScorers.length) {
        scorersGrid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding: 20px; color: var(--color-text-muted); font-size:0.82rem;">No hay datos de goleadores para este H2H</div>`;
      } else {
        const rankLabels = ['top1', 'top2', 'top3', '', ''];
        scorersGrid.innerHTML = scorers.topScorers.map((s, i) => {
          const statusDot = s.active
            ? `<span class="h2h-scorer-status-active" title="Activo"></span>`
            : `<span class="h2h-scorer-status-retired" title="Retirado"></span>`;
          return `<div class="h2h-scorer-card">
            <span class="h2h-scorer-rank ${rankLabels[i] || ''}">#${i + 1}</span>
            <div class="h2h-scorer-info">
              <div class="h2h-scorer-name">${s.name} ${statusDot}</div>
              <div class="h2h-scorer-team">${s.team}</div>
            </div>
            <span class="h2h-scorer-goals">⚽ ${s.goals}</span>
          </div>`;
        }).join('');
      }
    }

    const scorerExtraGrid = document.getElementById('h2h-scorer-extra-grid');
    if (scorerExtraGrid) {
      scorerExtraGrid.innerHTML = `
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${scorers.avgGoalMinute || 0}'</span><span class="h2h-adv-stat-label">Min. Promedio de Gol</span></div>
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${scorers.penaltiesCount}</span><span class="h2h-adv-stat-label">Penaltis Marcados</span></div>
        <div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${scorers.ownGoalsCount}</span><span class="h2h-adv-stat-label">Autogoles</span></div>
      `;
    }

    // Period distribution
    const periodGrid = document.getElementById('h2h-period-grid');
    if (periodGrid) {
      const periods = ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90'];
      const pcts = scorers.periodDistribution || {};
      const maxPct = Math.max(...periods.map(p => pcts[p] || 0), 1);
      periodGrid.innerHTML = periods.map(p => {
        const pct = pcts[p] || 0;
        const barH = Math.round((pct / maxPct) * 32);
        return `<div class="h2h-period-cell">
          <div class="h2h-period-bar-wrap">
            <div class="h2h-period-bar" style="height: ${barH}px;"></div>
          </div>
          <span class="h2h-period-pct">${pct}%</span>
          <span class="h2h-period-label">${p}'</span>
        </div>`;
      }).join('');
    }

    // ══ FORMA TAB ══
    function renderFormCard(formData, teamName, teamFlag, suffix) {
      const nameEl = document.getElementById(`h2h-form-name-${suffix}`);
      const flagEl = document.getElementById(`h2h-form-flag-${suffix}`);
      const recordEl = document.getElementById(`h2h-form-record-${suffix}`);
      const statsEl = document.getElementById(`h2h-form-stats-${suffix}`);
      const streaksEl = document.getElementById(`h2h-streaks-${suffix}`);
      const rivalEl = document.getElementById(`h2h-rival-${suffix}`);

      if (nameEl) nameEl.textContent = teamName;
      if (flagEl) flagEl.textContent = teamFlag || '🏳️';
      if (recordEl) recordEl.textContent = formData.record;

      if (statsEl) {
        statsEl.innerHTML = `
          <div class="h2h-form-stat-row">
            <span class="h2h-form-stat-key">Goles marcados/partido</span>
            <span class="h2h-form-stat-val">${formData.avg_gf}</span>
          </div>
          <div class="h2h-form-stat-row">
            <span class="h2h-form-stat-key">Goles recibidos/partido</span>
            <span class="h2h-form-stat-val">${formData.avg_gc}</span>
          </div>
          <div class="h2h-form-stat-row">
            <span class="h2h-form-stat-key">Portería a cero</span>
            <span class="h2h-form-stat-val">${formData.clean_sheets}%</span>
          </div>
          <div class="h2h-form-stat-row">
            <span class="h2h-form-stat-key">BTTS</span>
            <span class="h2h-form-stat-val">${formData.btts}%</span>
          </div>
          <div class="h2h-form-stat-row">
            <span class="h2h-form-stat-key">Over 2.5</span>
            <span class="h2h-form-stat-val">${formData.over25}%</span>
          </div>
        `;
      }

      if (streaksEl) {
        const s = formData.streaks;
        streaksEl.innerHTML = `
          <div class="h2h-streak-badge"><span class="h2h-streak-num">${s.unbeaten}</span><span class="h2h-streak-lbl">Sin perder</span></div>
          <div class="h2h-streak-badge"><span class="h2h-streak-num">${s.losing}</span><span class="h2h-streak-lbl">Derrotas consec.</span></div>
          <div class="h2h-streak-badge"><span class="h2h-streak-num">${s.scoring}</span><span class="h2h-streak-lbl">Marcando</span></div>
          <div class="h2h-streak-badge"><span class="h2h-streak-num">${s.clean_sheet}</span><span class="h2h-streak-lbl">Portería a 0</span></div>
        `;
      }

      if (rivalEl) {
        const r = formData.by_rival;
        rivalEl.innerHTML = `
          <div class="h2h-rival-cell"><div class="h2h-rival-level">🔴 Top Nivel</div><div class="h2h-rival-rec">${r.top}</div></div>
          <div class="h2h-rival-cell"><div class="h2h-rival-level">🟡 Nivel Alto</div><div class="h2h-rival-rec">${r.high}</div></div>
          <div class="h2h-rival-cell"><div class="h2h-rival-level">🟢 Normal</div><div class="h2h-rival-rec">${r.medium}</div></div>
        `;
      }
    }

    renderFormCard(form.teamA, metaA.name, metaA.flag, 'a');
    renderFormCard(form.teamB, metaB.name, metaB.flag, 'b');

    // ══ INSIGHTS TAB ══
    const insightsList = document.getElementById('h2h-insights-list');
    if (insightsList) {
      if (!insights.detectedPatterns.length) {
        insightsList.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--color-text-muted); font-size: 0.82rem;">Sin insights disponibles</div>`;
      } else {
        insightsList.innerHTML = insights.detectedPatterns.map(p =>
          `<div class="h2h-insight-item">${p}</div>`
        ).join('');
      }
    }

    // Matrix headers
    const matrixHeadA = document.getElementById('h2h-matrix-head-a');
    const matrixHeadB = document.getElementById('h2h-matrix-head-b');
    if (matrixHeadA) matrixHeadA.textContent = metaA.name.slice(0, 10);
    if (matrixHeadB) matrixHeadB.textContent = metaB.name.slice(0, 10);

    const matrixTbody = document.getElementById('h2h-matrix-tbody');
    if (matrixTbody) {
      const m = insights.comparativeMatrix;
      matrixTbody.innerHTML = `
        <tr><td>Goles promedio</td><td>${m.avg_goals.h2h}</td><td>${m.avg_goals.team_a}</td><td>${m.avg_goals.team_b}</td></tr>
        <tr><td>BTTS %</td><td>${m.btts.h2h}</td><td>${m.btts.team_a}</td><td>${m.btts.team_b}</td></tr>
        <tr><td>Over 2.5 %</td><td>${m.over25.h2h}</td><td>${m.over25.team_a}</td><td>${m.over25.team_b}</td></tr>
        <tr><td>Portería a cero</td><td>${m.clean_sheets.h2h}</td><td>${m.clean_sheets.team_a}</td><td>${m.clean_sheets.team_b}</td></tr>
      `;
    }

    // Historical prediction
    const pred = insights.historicalPrediction;
    const predOutcomeEl = document.getElementById('h2h-pred-outcome');
    const predProbEl = document.getElementById('h2h-pred-prob');
    const predConfEl = document.getElementById('h2h-pred-conf');
    const predGoalsEl = document.getElementById('h2h-pred-goals');
    const predScoreEl = document.getElementById('h2h-pred-score');
    const predSampleEl = document.getElementById('h2h-pred-sample');
    if (predOutcomeEl) predOutcomeEl.textContent = pred.outcome;
    if (predProbEl) predProbEl.textContent = pred.probability + '%';
    if (predConfEl) predConfEl.textContent = pred.confidence + ' CONFIANZA';
    if (predGoalsEl) predGoalsEl.textContent = pred.exp_goals;
    if (predScoreEl) predScoreEl.textContent = pred.freq_score;
    if (predSampleEl) predSampleEl.textContent = pred.sample_size;

    // ══ CHARTS TAB ══
    const isDark = !document.body.classList.contains('light-theme');
    const textCol = isDark ? 'rgba(255,255,255,0.6)' : 'rgba(18,42,82,0.6)';
    const gridCol = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(18,42,82,0.06)';
    const primaryCol = '#f0b310';

    // Destroy old charts
    Object.values(h2hAdvancedCharts).forEach(ch => { if (ch) { ch.destroy(); } });
    h2hAdvancedCharts = { radar: null, doughnut: null, period: null };

    // Radar chart
    const radarCtx = document.getElementById('h2h-radar-chart');
    if (radarCtx) {
      const formA = form.teamA;
      const formB = form.teamB;
      h2hAdvancedCharts.radar = new Chart(radarCtx, {
        type: 'radar',
        data: {
          labels: ['Goles Marc.', 'Defensa', 'Portería a 0', 'BTTS', 'Over 2.5', 'Win Rate H2H'],
          datasets: [
            {
              label: metaA.name.slice(0, 10),
              data: [
                Math.min(formA.avg_gf * 20, 100),
                Math.max(0, 100 - formA.avg_gc * 20),
                formA.clean_sheets,
                formA.btts,
                formA.over25,
                count > 0 ? Math.round(h2h.winsA / count * 100) : 0
              ],
              backgroundColor: 'rgba(59,130,246,0.15)',
              borderColor: '#3b82f6',
              borderWidth: 2,
              pointBackgroundColor: '#3b82f6',
              pointRadius: 3,
            },
            {
              label: metaB.name.slice(0, 10),
              data: [
                Math.min(formB.avg_gf * 20, 100),
                Math.max(0, 100 - formB.avg_gc * 20),
                formB.clean_sheets,
                formB.btts,
                formB.over25,
                count > 0 ? Math.round(h2h.winsB / count * 100) : 0
              ],
              backgroundColor: 'rgba(16,185,129,0.15)',
              borderColor: '#10b981',
              borderWidth: 2,
              pointBackgroundColor: '#10b981',
              pointRadius: 3,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: textCol, font: { size: 10 } } } },
          scales: {
            r: {
              min: 0, max: 100,
              ticks: { color: textCol, font: { size: 9 }, stepSize: 25, backdropColor: 'transparent' },
              grid: { color: gridCol },
              pointLabels: { color: textCol, font: { size: 9 } },
              angleLines: { color: gridCol },
            }
          }
        }
      });
    }

    // Doughnut chart
    const doughnutCtx = document.getElementById('h2h-doughnut-chart');
    if (doughnutCtx) {
      h2hAdvancedCharts.doughnut = new Chart(doughnutCtx, {
        type: 'doughnut',
        data: {
          labels: [metaA.name.slice(0, 10) + ' gana', 'Empate', metaB.name.slice(0, 10) + ' gana'],
          datasets: [{
            data: [h2h.winsA, h2h.draws, h2h.winsB],
            backgroundColor: ['rgba(59,130,246,0.8)', 'rgba(107,114,128,0.8)', 'rgba(16,185,129,0.8)'],
            borderColor: [isDark ? '#1a2035' : '#fff', isDark ? '#1a2035' : '#fff', isDark ? '#1a2035' : '#fff'],
            borderWidth: 2,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '65%',
          plugins: {
            legend: { position: 'bottom', labels: { color: textCol, font: { size: 10 }, padding: 12 } },
          }
        }
      });
    }

    // Period bar chart
    const periodCtx = document.getElementById('h2h-period-chart');
    if (periodCtx) {
      const periods = ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90'];
      const pData = periods.map(p => scorers.periodDistribution[p] || 0);
      h2hAdvancedCharts.period = new Chart(periodCtx, {
        type: 'bar',
        data: {
          labels: periods.map(p => p + "'"),
          datasets: [{
            label: '% de goles',
            data: pData,
            backgroundColor: periods.map((_, i) => `rgba(240,179,16,${0.4 + i * 0.1})`),
            borderColor: primaryCol,
            borderWidth: 1,
            borderRadius: 4,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: textCol, font: { size: 10 } }, grid: { color: gridCol } },
            y: { ticks: { color: textCol, font: { size: 10 }, callback: v => v + '%' }, grid: { color: gridCol }, beginAtZero: true }
          }
        }
      });
    }

    // Show content
    loadingEl.style.display = 'none';
    contentEl.style.display = 'block';

  } catch (err) {
    console.error('Error loading advanced H2H data:', err);
    loadingEl.innerHTML = `<div style="text-align:center; padding: 40px; color: var(--color-text-muted);">
      <div style="font-size: 1.5rem; margin-bottom: 8px;">⚠️</div>
      Error al cargar datos H2H avanzados. Verifica que el servidor esté corriendo.
    </div>`;
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
    altitude: inputAltitude.value ? parseInt(inputAltitude.value) : 0,
    hostCountry: inputHostCountry.value || null
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

    // Render match summary (narrative description)
    renderMatchSummary(data, selectedTeamA, selectedTeamB);

    // Fetch AI tactical analysis if available
    fetchAITacticalAnalysis(selectedTeamA, selectedTeamB);

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
        // 1.5 Goals Line
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
          label: `${nameBVal} +1.5`,
          probYes: data.goalsMarkets.asianHandicap["-1.5"].teamB,
          probNo: data.goalsMarkets.asianHandicap["-1.5"].teamA,
          tStrYes: "m15-b",
          tStrNo: "m15-a",
          idYes: "in-ah-m15-b",
          idNo: "in-ah-m15-a"
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
          label: `${nameAVal} +1.5`,
          probYes: data.goalsMarkets.asianHandicap["+1.5"].teamA,
          probNo: data.goalsMarkets.asianHandicap["+1.5"].teamB,
          tStrYes: "p15-a",
          tStrNo: "p15-b",
          idYes: "in-ah-p15-a",
          idNo: "in-ah-p15-b"
        },
        // 0.5 Goals Line
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
          label: `${nameBVal} +0.5`,
          probYes: data.goalsMarkets.asianHandicap["-0.5"].teamB,
          probNo: data.goalsMarkets.asianHandicap["-0.5"].teamA,
          tStrYes: "m05-b",
          tStrNo: "m05-a",
          idYes: "in-ah-m05-b",
          idNo: "in-ah-m05-a"
        },
        {
          label: `${nameBVal} -0.5`,
          probYes: data.goalsMarkets.asianHandicap["+0.5"].teamB,
          probNo: data.goalsMarkets.asianHandicap["+0.5"].teamA,
          tStrYes: "p05-b",
          tStrNo: "p05-a",
          idYes: "in-ah-p05-b",
          idNo: "in-ah-p05-a"
        },
        {
          label: `${nameAVal} +0.5`,
          probYes: data.goalsMarkets.asianHandicap["+0.5"].teamA,
          probNo: data.goalsMarkets.asianHandicap["+0.5"].teamB,
          tStrYes: "p05-a",
          tStrNo: "p05-b",
          idYes: "in-ah-p05-a",
          idNo: "in-ah-p05-b"
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
    
    const evSpans = document.querySelectorAll(`[id="${targetId}"]`);
    
    evSpans.forEach(evSpan => {
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
    });
  }
});

/* ==========================================================================
   MATCH SUMMARY - Descripción narrativa del pronóstico
   ========================================================================== */
function renderMatchSummary(data, slugA, slugB) {
  const card = document.getElementById('match-summary-card');
  if (!card) return;

  const metaA = TEAM_METADATA[slugA] || { name: slugA, flag: '' };
  const metaB = TEAM_METADATA[slugB] || { name: slugB, flag: '' };
  const nameA = metaA.name;
  const nameB = metaB.name;
  const flagA = metaA.flag;
  const flagB = metaB.flag;

  const pA = data.probWinA;
  const pD = data.probDraw;
  const pB = data.probWinB;
  const xgA = data.xgA;
  const xgB = data.xgB;
  const cp = data.cornersPrediction;
  const gm = data.goalsMarkets;
  const topScore = data.topScores?.[0];

  // ---- Determinar favorito y nivel de confianza ----
  let favorito, pFav, pOther, nameFav, nameOther, flagFav, flagOther;
  if (pA >= pB && pA >= pD) {
    favorito = 'A'; pFav = pA; pOther = pB;
    nameFav = nameA; nameOther = nameB; flagFav = flagA; flagOther = flagB;
  } else if (pB >= pA && pB >= pD) {
    favorito = 'B'; pFav = pB; pOther = pA;
    nameFav = nameB; nameOther = nameA; flagFav = flagB; flagOther = flagA;
  } else {
    favorito = 'DRAW';
  }

  const gap = favorito !== 'DRAW' ? Math.abs(pFav - pOther) : 0;

  // Badge y color de confianza
  let confidenceLabel, badgeColor, badgeBg;
  if (favorito === 'DRAW') {
    confidenceLabel = '⚖️ Muy Equilibrado';
    badgeColor = '#9ca3af'; badgeBg = 'rgba(156,163,175,0.12)';
  } else if (gap >= 0.40) {
    confidenceLabel = '🔥 Alta Confianza';
    badgeColor = '#34d399'; badgeBg = 'rgba(52,211,153,0.12)';
  } else if (gap >= 0.20) {
    confidenceLabel = '✅ Favorable';
    badgeColor = '#f0b310'; badgeBg = 'rgba(240,179,16,0.12)';
  } else {
    confidenceLabel = '⚠️ Incierto';
    badgeColor = '#f87171'; badgeBg = 'rgba(248,113,113,0.12)';
  }

  const badge = document.getElementById('summary-confidence-badge');
  badge.textContent = confidenceLabel;
  badge.style.color = badgeColor;
  badge.style.background = badgeBg;
  badge.style.borderColor = badgeColor + '40';

  // ---- Veredicto narrativo ----
  const over25Prob = gm?.overUnder?.find(o => o.threshold === 2.5)?.over || 0;
  const btts = gm?.btts?.yes || 0;
  let verdict = '';

  if (favorito === 'DRAW') {
    verdict = `El modelo estadístico encuentra un <strong>equilibrio total</strong> entre ${flagA} <strong>${nameA}</strong> y ${flagB} <strong>${nameB}</strong>. ` +
      `Las probabilidades de victoria son casi idénticas (${(pA*100).toFixed(1)}% vs ${(pB*100).toFixed(1)}%), ` +
      `con un ${(pD*100).toFixed(1)}% de empate. El partido presenta un xG muy parejo de <strong>${xgA.toFixed(2)}</strong> vs <strong>${xgB.toFixed(2)}</strong>. ` +
      `Dado el equilibrio, los mercados de doble oportunidad y goles ofrecen mejor valor que el 1X2 directo.`;
  } else {
    const pFavPct = (pFav * 100).toFixed(1);
    const pOtherPct = (pOther * 100).toFixed(1);
    const xgFav = favorito === 'A' ? xgA : xgB;
    const xgOther = favorito === 'A' ? xgB : xgA;

    let openerPhrase;
    if (gap >= 0.40) {
      openerPhrase = `El modelo muestra una clara ventaja para ${flagFav} <strong>${nameFav}</strong>`;
    } else if (gap >= 0.20) {
      openerPhrase = `El modelo favorece levemente a ${flagFav} <strong>${nameFav}</strong>`;
    } else {
      openerPhrase = `El modelo apunta tímidamente hacia ${flagFav} <strong>${nameFav}</strong>`;
    }

    const goalsNote = over25Prob >= 0.55
      ? `El partido apunta a ser <strong>goleador</strong> (Over 2.5 al ${(over25Prob*100).toFixed(1)}%).`
      : over25Prob >= 0.40
        ? `Se espera un partido de <strong>goles moderados</strong> (Over 2.5 al ${(over25Prob*100).toFixed(1)}%).`
        : `Se espera un partido <strong>cerrado y con pocos goles</strong> (Over 2.5 solo al ${(over25Prob*100).toFixed(1)}%).`;

    const bttsNote = btts >= 0.55
      ? `Ambos equipos tienen alta probabilidad de marcar (BTTS ${(btts*100).toFixed(1)}%).`
      : btts >= 0.40
        ? `Existe una probabilidad moderada de que ambos anoten (BTTS ${(btts*100).toFixed(1)}%).`
        : `El modelo anticipa que al menos uno de los equipos se quedará sin marcar (BTTS solo ${(btts*100).toFixed(1)}%).`;

    verdict = `${openerPhrase}, con un ${pFavPct}% de probabilidad de victoria frente al ${pOtherPct}% de ${flagOther} <strong>${nameOther}</strong>. ` +
      `El xG esperado es de <strong>${xgFav.toFixed(2)}</strong> para ${nameFav} y <strong>${xgOther.toFixed(2)}</strong> para ${nameOther}. ` +
      `${goalsNote} ${bttsNote}`;
  }

  document.getElementById('summary-verdict').innerHTML = verdict;

  // ---- Key Data Chips ----
  document.getElementById('chip-xg-val').textContent = `${xgA.toFixed(2)} / ${xgB.toFixed(2)}`;
  document.getElementById('chip-corners-val').textContent =
    `${cp.expectedA.toFixed(1)} / ${cp.expectedB.toFixed(1)} (${cp.expectedTotal.toFixed(1)} tot.)`;
  document.getElementById('chip-top-score').textContent =
    topScore ? `${topScore.score} · ${(topScore.probability*100).toFixed(1)}%` : '--';
  document.getElementById('chip-btts').textContent = `${(btts*100).toFixed(1)}%`;
  document.getElementById('chip-over25').textContent = `${(over25Prob*100).toFixed(1)}%`;

  // Fuerza ofensiva relativa (shots-based)
  const shotA = data.comparisonStats?.teamA?.shots_per_90 || xgA * 7;
  const shotB = data.comparisonStats?.teamB?.shots_per_90 || xgB * 7;
  document.getElementById('chip-attack').textContent =
    `${shotA.toFixed(1)} / ${shotB.toFixed(1)} tiros`;

  // ---- Análisis de Mercados ----
  const marketsList = document.getElementById('summary-markets-list');
  marketsList.innerHTML = '';
  const markets = [];

  // 1X2
  const resultLabel = pA > pB && pA > pD ? `Victoria ${nameA}` :
                      pB > pA && pB > pD ? `Victoria ${nameB}` : 'Empate';
  const resultProb = Math.max(pA, pB, pD);
  markets.push({ label: `Resultado: ${resultLabel}`, value: `${(resultProb*100).toFixed(1)}%`, color: '#f0b310' });

  // BTTS
  const bttsBest = btts >= 0.5 ? { l: 'Ambos Anotan (Sí)', v: btts } : { l: 'Solo uno anota (No)', v: 1-btts };
  markets.push({ label: bttsBest.l, value: `${(bttsBest.v*100).toFixed(1)}%`, color: '#818cf8' });

  // O/U 2.5
  const over25Best = over25Prob >= 0.5 ? { l: 'Over 2.5 Goles', v: over25Prob } : { l: 'Under 2.5 Goles', v: 1-over25Prob };
  markets.push({ label: over25Best.l, value: `${(over25Best.v*100).toFixed(1)}%`, color: '#34d399' });

  // DNB
  const dnbFav = pA > pB ? { l: `DNB ${nameA}`, v: gm?.dnb?.['1'] } : { l: `DNB ${nameB}`, v: gm?.dnb?.['2'] };
  if (dnbFav.v) markets.push({ label: dnbFav.l, value: `${(dnbFav.v*100).toFixed(1)}%`, color: '#f87171' });

  // +EV market if odds available
  if (data.bettingAnalysis?.hasOdds) {
    const ba = data.bettingAnalysis;
    if (ba.valuableA) markets.push({ label: `⚡ Valor: ${nameA}`, value: `+EV ${(ba.edgeA*100).toFixed(1)}%`, color: '#10b981' });
    if (ba.valuableB) markets.push({ label: `⚡ Valor: ${nameB}`, value: `+EV ${(ba.edgeB*100).toFixed(1)}%`, color: '#10b981' });
    if (ba.valuableDraw) markets.push({ label: '⚡ Valor: Empate', value: `+EV ${(ba.edgeDraw*100).toFixed(1)}%`, color: '#10b981' });
  }

  markets.forEach(m => {
    const li = document.createElement('li');
    li.className = 'summary-market-item';
    li.innerHTML = `
      <span class="summary-market-dot" style="background: ${m.color};"></span>
      <span class="summary-market-label">${m.label}</span>
      <span class="summary-market-value" style="color: ${m.color};">${m.value}</span>
    `;
    marketsList.appendChild(li);
  });

  // ---- Análisis de Córneres ----
  const cornersList = document.getElementById('summary-corners-list');
  cornersList.innerHTML = '';
  const cornersItems = [];

  // Quién domina corners
  const cornersWinner = cp.probMostA > cp.probMostB
    ? { l: `${nameA} domina el saque`, v: cp.probMostA, c: '#f0b310' }
    : { l: `${nameB} domina el saque`, v: cp.probMostB, c: '#818cf8' };
  cornersItems.push({ label: cornersWinner.l, value: `${(cornersWinner.v*100).toFixed(1)}%`, color: cornersWinner.c });

  // Total corners más probable
  const totalC = cp.expectedTotal;
  cornersItems.push({ label: `Total esperado: ${totalC.toFixed(1)} córneres`, value: '', color: '#9ca3af' });

  // Over/under lines
  const ouLines = cp.overUnder || [];
  ouLines.forEach(ou => {
    const isOver = ou.over >= 0.5;
    const pct = (Math.max(ou.over, ou.under) * 100).toFixed(1);
    const dir = isOver ? 'Over' : 'Under';
    const color = isOver ? '#34d399' : '#f87171';
    cornersItems.push({ label: `${dir} ${ou.threshold} córneres`, value: `${pct}%`, color });
  });

  // Córneres A vs B
  cornersItems.push({ label: `${nameA}: ${cp.expectedA.toFixed(1)} | ${nameB}: ${cp.expectedB.toFixed(1)}`, value: '', color: '#6b7280' });

  cornersItems.forEach(ci => {
    const li = document.createElement('li');
    li.className = 'summary-market-item';
    li.innerHTML = `
      <span class="summary-market-dot" style="background: ${ci.color};"></span>
      <span class="summary-market-label">${ci.label}</span>
      ${ci.value ? `<span class="summary-market-value" style="color: ${ci.color};">${ci.value}</span>` : ''}
    `;
    cornersList.appendChild(li);
  });

  // ---- Fiabilidad de datos ----
  const srcA = data.xgSourceA;
  const srcB = data.xgSourceB;
  const srcALabel = srcA === 'fbref' ? 'datos reales FBref (Copa del Mundo)' :
                    srcA === 'real'  ? 'datos reales FBref' : 'estimación histórica';
  const srcBLabel = srcB === 'fbref' ? 'datos reales FBref (Copa del Mundo)' :
                    srcB === 'real'  ? 'datos reales FBref' : 'estimación histórica';
  const bothFbref = (srcA === 'fbref' || srcA === 'real') && (srcB === 'fbref' || srcB === 'real');
  const noneFbref = srcA === 'modelo' && srcB === 'modelo';

  let reliabilityText;
  if (bothFbref) {
    reliabilityText = `<strong>Alta fiabilidad.</strong> Ambos equipos usan ${srcALabel} — las estadísticas de xG y córneres están calibradas con rendimiento real en partidos oficiales internacionales recientes.`;
  } else if (noneFbref) {
    reliabilityText = `<strong>Fiabilidad moderada.</strong> Ningún equipo tiene estadísticas avanzadas recientes. El modelo usa historial de resultados ponderado por ELO + ranking FIFA. Las probabilidades son orientativas.`;
  } else {
    const withData = srcA !== 'modelo' ? nameA : nameB;
    const withEst  = srcA === 'modelo' ? nameA : nameB;
    reliabilityText = `<strong>Fiabilidad mixta.</strong> ${withData} usa ${srcA !== 'modelo' ? srcALabel : srcBLabel}, mientras que ${withEst} se estima por historial y ELO. Las probabilidades de ${withData} son más precisas.`;
  }

  document.getElementById('summary-reliability-text').innerHTML = reliabilityText;

  // Show the card
  card.style.display = 'block';
}

/* ==========================================================================
   PRESETS LOGIC (NUEVO)
   ========================================================================== */
function initPresets() {
  const presetBtns = document.querySelectorAll(".preset-btn");
  if (!presetBtns.length) return;

  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const preset = btn.dataset.preset;

      // Sync active states for all buttons with the selected preset across both groups
      presetBtns.forEach(b => {
        if (b.dataset.preset === preset) {
          b.classList.add("active", "btn-primary");
          b.classList.remove("btn-secondary");
        } else {
          b.classList.remove("active", "btn-primary");
          b.classList.add("btn-secondary");
        }
      });

      const wFifa = document.getElementById("input-weight-fifa");
      const wH2h = document.getElementById("input-weight-h2h");
      const decay = document.getElementById("input-decay");
      const ovrA = document.getElementById("input-override-a");
      const ovrB = document.getElementById("input-override-b");
      
      if (!wFifa || !wH2h || !decay || !ovrA || !ovrB) return;

      if (preset === "grupos") {
        wFifa.value = 30;
        wH2h.value = 10;
        decay.value = 12;
        ovrA.value = 1.0;
        ovrB.value = 1.0;
      } else if (preset === "eliminacion") {
        wFifa.value = 35;
        wH2h.value = 15;
        decay.value = 12;
        ovrA.value = 0.90;
        ovrB.value = 0.90;
      } else if (preset === "eliminatorias") {
        wFifa.value = 20;
        wH2h.value = 30;
        decay.value = 18;
        ovrA.value = 1.0;
        ovrB.value = 1.0;
      } else if (preset === "amistoso") {
        wFifa.value = 45;
        wH2h.value = 5;
        decay.value = 18;
        ovrA.value = 0.85;
        ovrB.value = 0.85;
      } else if (preset === "debutante") {
        wFifa.value = 40;
        wH2h.value = 0;
        decay.value = 24;
        ovrA.value = 0.95;
        ovrB.value = 0.95;
      } else if (preset === "clasico") {
        wFifa.value = 15;
        wH2h.value = 45;
        decay.value = 24;
        ovrA.value = 1.0;
        ovrB.value = 1.0;
      } else if (preset === "altitud") {
        wFifa.value = 20;
        wH2h.value = 10;
        decay.value = 12;
        ovrA.value = 1.20;
        ovrB.value = 0.75;
        const altitudeInput = document.getElementById("input-altitude");
        if (altitudeInput) altitudeInput.value = 2800;
      } else if (preset === "desigual") {
        wFifa.value = 50;
        wH2h.value = 0;
        decay.value = 12;
        ovrA.value = 1.10;
        ovrB.value = 0.80;
      }
      
      // Update UI representations
      updateMatchCard(true);
      updateWeightsPreview();

      // Instantly run the simulation if results panel is already visible
      const resultsTabHeader = document.getElementById("results-tab-header");
      if (resultsTabHeader && !resultsTabHeader.classList.contains("hidden")) {
        runPredictionFlow();
      }
    });
  });
}

let bbDonutChart = null;
function updateDonutChart(fifa, h2h, historic) {
  const ctx = document.getElementById('bb-donut-canvas');
  if (!ctx) return;
  
  const data = [fifa, h2h, historic];
  
  if (bbDonutChart) {
    bbDonutChart.data.datasets[0].data = data;
    bbDonutChart.update();
  } else {
    try {
      bbDonutChart = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
          labels: ['FIFA', 'H2H', 'Forma Histórica'],
          datasets: [{
            data: data,
            backgroundColor: ['#f59e0b', '#991b1b', '#64748b'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return ` ${context.label}: ${context.raw}%`;
                }
              }
            }
          },
          cutout: '65%'
        }
      });
    } catch (err) {
      console.error("Error creating donut chart:", err);
    }
  }
}

function updateWeightsPreview() {
  const wFifaInput = document.getElementById("input-weight-fifa");
  const wH2hInput = document.getElementById("input-weight-h2h");
  const previewDiv = document.getElementById("weights-formula-preview");
  if (!wFifaInput || !wH2hInput || !previewDiv) return;

  const fifaVal = parseFloat(wFifaInput.value) || 0;
  const h2hVal = parseFloat(wH2hInput.value) || 0;
  const total = fifaVal + h2hVal;

  let realFifa, realH2h, realForm;
  if (total > 100) {
    realFifa = Math.round((fifaVal / total) * 100);
    realH2h = Math.round((h2hVal / total) * 100);
    realForm = 0;
  } else {
    realFifa = Math.round(fifaVal);
    realH2h = Math.round(h2hVal);
    realForm = Math.max(0, 100 - realFifa - realH2h);
  }

  previewDiv.innerHTML = `Distribución Real: FIFA <strong>${realFifa}%</strong> | H2H <strong>${realH2h}%</strong> | Forma Histórica <strong>${realForm}%</strong>`;
  
  // Update donut chart
  updateDonutChart(realFifa, realH2h, realForm);
}

async function fetchAITacticalAnalysis(teamA, teamB) {
  const card = document.getElementById("ai-tactical-analysis-card");
  
  if (card) card.style.display = "none";
  
  try {
    const res = await fetch(`/api/ai-analyses/${teamA}/${teamB}`);
    const json = await res.json();
    
    if (res.ok && json.status === "success" && json.analysis) {
      const item = json.analysis;
      
      // Pre-fill all odds if they exist in the tactical analysis dictionary
      if (item.odds) {
        Object.keys(item.odds).forEach(originalId => {
          const inputEl = document.getElementById(originalId);
          if (inputEl) {
            inputEl.value = item.odds[originalId] !== null ? item.odds[originalId] : "";
            // Trigger input event to update EV calculations automatically
            inputEl.dispatchEvent(new Event("input", { bubbles: true }));
          }
        });
      } else {
        // Fallback for old items
        if (inputOddsA && item.odds_a !== undefined) {
          inputOddsA.value = item.odds_a !== null ? item.odds_a : "";
          inputOddsA.dispatchEvent(new Event("input", { bubbles: true }));
        }
        if (inputOddsDraw && item.odds_draw !== undefined) {
          inputOddsDraw.value = item.odds_draw !== null ? item.odds_draw : "";
          inputOddsDraw.dispatchEvent(new Event("input", { bubbles: true }));
        }
        if (inputOddsB && item.odds_b !== undefined) {
          inputOddsB.value = item.odds_b !== null ? item.odds_b : "";
          inputOddsB.dispatchEvent(new Event("input", { bubbles: true }));
        }
      }
      
      const badgeConf = document.getElementById("ai-confidence-badge");
      const verdictText = document.getElementById("ai-verdict-text");
      const tipsContainer = document.getElementById("ai-tips-container");
      
      if (badgeConf) badgeConf.textContent = `Confianza: ${item.confidence}%`;
      if (verdictText) verdictText.innerHTML = formatMarkdownSimple(item.analysis_text);
      
      if (tipsContainer) {
        tipsContainer.innerHTML = "";
        if (item.key_tips && item.key_tips.length > 0) {
          item.key_tips.forEach(tip => {
            const badge = document.createElement("span");
            badge.className = "ai-tip-badge";
            badge.textContent = tip;
            tipsContainer.appendChild(badge);
          });
        } else {
          tipsContainer.innerHTML = `<span style="font-size: 0.8rem; color: var(--color-text-secondary); font-style: italic;">Sin recomendaciones registradas</span>`;
        }
      }
      
      if (card) card.style.display = "block";

      // Auto-reveal the results tabs and activate the "Análisis" tab if an AI analysis exists
      const firstTimePlaceholder = document.getElementById("first-time-placeholder");
      const resultsTabHeader = document.getElementById("results-tab-header");
      const tabAnalysis = document.getElementById("tab-analysis");
      
      if (firstTimePlaceholder && !firstTimePlaceholder.classList.contains("hidden")) {
        firstTimePlaceholder.classList.add("hidden");
      }
      if (resultsTabHeader && resultsTabHeader.classList.contains("hidden")) {
        resultsTabHeader.classList.remove("hidden");
        // Ensure "Análisis" tab button is active if no tab is currently selected active
        const activeTabBtn = resultsTabHeader.querySelector(".tab-btn.active");
        if (!activeTabBtn) {
          const tabBtnAnalysis = document.getElementById("tab-btn-analysis");
          if (tabBtnAnalysis) tabBtnAnalysis.classList.add("active");
        }
      }
      if (tabAnalysis && tabAnalysis.classList.contains("hidden")) {
        const activeTabBtn = resultsTabHeader ? resultsTabHeader.querySelector(".tab-btn.active") : null;
        if (activeTabBtn && activeTabBtn.id === "tab-btn-analysis") {
          tabAnalysis.classList.remove("hidden");
        }
      }
    }
  } catch (error) {
    console.error("Error loading match AI analysis:", error);
  }
}

function formatMarkdownSimple(text) {
  if (!text) return "";
  
  let formatted = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
    
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  formatted = formatted.replace(/^\s*-\s+(.*?)$/gm, "<li>$1</li>");
  formatted = formatted.replace(/(<li>.*?<\/li>)/gs, "<ul>$1</ul>");
  formatted = formatted.replace(/<\/ul>\s*<ul>/g, "");
  
  return formatted;
}

/* ==========================================================================
   USER AUTH & SUPABASE INTEGRATION (NEW)
   ========================================================================== */
function initSupabaseAuth() {
  const client = getSupabase();
  if (!client) {
    console.warn("Supabase client is not loaded or configured. Auth disabled.");
    return;
  }

  // Elements
  const btnAuthLogout = document.getElementById("btn-auth-logout");
  
  const formLogin = document.getElementById("landing-form-login");
  const formRegister = document.getElementById("landing-form-register");
  const formForgot = document.getElementById("landing-form-forgot");
  const formReset = document.getElementById("landing-form-reset");
  
  const linkForgotPwd = document.getElementById("landing-link-forgot");
  const linkGoRegister = document.getElementById("landing-link-go-register");
  const linkGoLogin = document.getElementById("landing-link-go-login");
  const linkForgotBack = document.getElementById("landing-link-forgot-back");
  
  const errorMsg = document.getElementById("landing-auth-error-msg");
  const successMsg = document.getElementById("landing-auth-success-msg");

  // Show/Hide views inside the landing card
  function showAuthView(viewName) {
    if (errorMsg) errorMsg.classList.add("hidden");
    if (successMsg) successMsg.classList.add("hidden");

    const titleEl = document.getElementById("landing-auth-title");
    const subtitleEl = document.getElementById("landing-auth-subtitle");
    
    // Hide all forms
    if (formLogin) formLogin.classList.add("hidden");
    if (formRegister) formRegister.classList.add("hidden");
    if (formForgot) formForgot.classList.add("hidden");
    if (formReset) formReset.classList.add("hidden");

    if (viewName === "login") {
      if (formLogin) formLogin.classList.remove("hidden");
      if (titleEl) titleEl.textContent = "Iniciar Sesión";
      if (subtitleEl) subtitleEl.textContent = "Ingresa tus credenciales para acceder al simulador";
    } else if (viewName === "register") {
      if (formRegister) formRegister.classList.remove("hidden");
      if (titleEl) titleEl.textContent = "Crear Cuenta";
      if (subtitleEl) subtitleEl.textContent = "Regístrate gratis para acceder a todos los beneficios.";
    } else if (viewName === "forgot") {
      if (formForgot) formForgot.classList.remove("hidden");
      if (titleEl) titleEl.textContent = "Recuperar Contraseña";
      if (subtitleEl) subtitleEl.textContent = "Ingresa tu email para recibir un enlace de recuperación.";
    } else if (viewName === "reset") {
      if (formReset) formReset.classList.remove("hidden");
      if (titleEl) titleEl.textContent = "Restablecer Contraseña";
      if (subtitleEl) subtitleEl.textContent = "Escribe tu nueva contraseña a continuación.";
    }
  }

  // View switching links
  if (linkForgotPwd) {
    linkForgotPwd.addEventListener("click", (e) => {
      e.preventDefault();
      showAuthView("forgot");
    });
  }
  if (linkGoRegister) {
    linkGoRegister.addEventListener("click", (e) => {
      e.preventDefault();
      showAuthView("register");
    });
  }
  if (linkGoLogin) {
    linkGoLogin.addEventListener("click", (e) => {
      e.preventDefault();
      showAuthView("login");
    });
  }
  if (linkForgotBack) {
    linkForgotBack.addEventListener("click", (e) => {
      e.preventDefault();
      showAuthView("login");
    });
  }

  // Helper to show messages
  function showStatus(text, type = "error") {
    if (type === "error") {
      if (successMsg) successMsg.classList.add("hidden");
      if (errorMsg) {
        errorMsg.textContent = text;
        errorMsg.classList.remove("hidden");
      }
    } else {
      if (errorMsg) errorMsg.classList.add("hidden");
      if (successMsg) {
        successMsg.textContent = text;
        successMsg.classList.remove("hidden");
      }
    }
  }

  // 1. SIGN UP (REGISTER)
  if (formRegister) {
    formRegister.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("landing-register-username").value.trim();
      const email = document.getElementById("landing-register-email").value.trim();
      const password = document.getElementById("landing-register-password").value;
      const confirmPassword = document.getElementById("landing-register-password-confirm").value;

      if (!username) {
        showStatus("El nombre de usuario es obligatorio.", "error");
        return;
      }
      if (password.length < 6) {
        showStatus("La contraseña debe tener al menos 6 caracteres.", "error");
        return;
      }
      if (password !== confirmPassword) {
        showStatus("Las contraseñas no coinciden.", "error");
        return;
      }

      showStatus("Creando cuenta...", "success");
      try {
        const { data, error } = await client.auth.signUp({ 
          email, 
          password,
          options: {
            data: {
              username: username,
              display_name: username
            }
          }
        });
        if (error) throw error;
        
        if (data.session) {
          showStatus("¡Cuenta creada e inicio de sesión exitoso!", "success");
        } else {
          showStatus("¡Registro exitoso! Por favor revisa tu bandeja de entrada para verificar tu correo.", "success");
        }
      } catch (err) {
        console.error("SignUp error:", err);
        showStatus(err.message || "Error al registrar usuario.", "error");
      }
    });
  }

  // 2. SIGN IN (LOGIN)
  if (formLogin) {
    formLogin.addEventListener("submit", async (e) => {
      e.preventDefault();
      const loginInput = document.getElementById("landing-login-email").value.trim();
      const password = document.getElementById("landing-login-password").value;

      showStatus("Ingresando...", "success");
      try {
        let emailToUse = loginInput;
        
        // If it doesn't look like an email, assume it's a username and look it up
        if (!loginInput.includes("@")) {
          showStatus("Buscando usuario...", "success");
          try {
            const res = await fetch("/api/lookup-username", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ username: loginInput })
            });
            const data = await res.json();
            if (data.status === "success" && data.email) {
              emailToUse = data.email;
            } else {
              throw new Error("El nombre de usuario no existe.");
            }
          } catch (lookupErr) {
            throw new Error(lookupErr.message || "Error al buscar el usuario.");
          }
        }

        showStatus("Autenticando...", "success");
        const { error } = await client.auth.signInWithPassword({ email: emailToUse, password });
        if (error) throw error;
        
        showStatus("¡Inicio de sesión exitoso!", "success");
      } catch (err) {
        console.error("SignIn error:", err);
        showStatus(err.message || "Credenciales incorrectas o usuario no encontrado.", "error");
      }
    });
  }

  // 3. LOGOUT
  if (btnAuthLogout) {
    btnAuthLogout.addEventListener("click", async () => {
      try {
        const { error } = await client.auth.signOut();
        if (error) throw error;
      } catch (err) {
        console.error("Logout error:", err);
      }
    });
  }

  // 4. REQUEST PASSWORD RESET
  if (formForgot) {
    formForgot.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("landing-forgot-email").value.trim();

      showStatus("Enviando correo...", "success");
      try {
        const redirectUrl = window.location.origin + window.location.pathname;
        const { error } = await client.auth.resetPasswordForEmail(email, {
          redirectTo: redirectUrl
        });
        if (error) throw error;
        
        showStatus("Correo enviado. Revisa tu bandeja de entrada para restablecer tu contraseña.", "success");
      } catch (err) {
        console.error("Reset request error:", err);
        showStatus(err.message || "Error al solicitar restablecimiento.", "error");
      }
    });
  }

  // 5. UPDATE PASSWORD (NEW PASSWORD)
  if (formReset) {
    formReset.addEventListener("submit", async (e) => {
      e.preventDefault();
      const password = document.getElementById("landing-reset-password").value;
      const confirmPassword = document.getElementById("landing-reset-password-confirm").value;

      if (password.length < 6) {
        showStatus("La contraseña debe tener al menos 6 caracteres.", "error");
        return;
      }
      if (password !== confirmPassword) {
        showStatus("Las contraseñas no coinciden.", "error");
        return;
      }

      showStatus("Actualizando contraseña...", "success");
      try {
        const { error } = await client.auth.updateUser({ password });
        if (error) throw error;
        
        showStatus("¡Contraseña actualizada con éxito!", "success");
        window.history.replaceState(null, null, window.location.pathname);
        setTimeout(() => {
          showAuthView("login");
        }, 1500);
      } catch (err) {
        console.error("Password update error:", err);
        showStatus(err.message || "Error al actualizar contraseña.", "error");
      }
    });
  }

  // Dynamic transition helper
  function transitionToApp(showApp) {
    const landing = document.getElementById("landing-container");
    const app = document.querySelector(".app-container");
    
    if (showApp) {
      if (landing && !landing.classList.contains("hidden")) {
        landing.classList.add("fade-out-active");
        setTimeout(() => {
          landing.classList.add("hidden");
          landing.classList.remove("fade-out-active");
          
          if (app) {
            app.classList.remove("hidden");
            app.classList.add("fade-in-active");
            setTimeout(() => {
              app.classList.remove("fade-in-active");
            }, 400);
          }
        }, 400);
      } else {
        if (landing) landing.classList.add("hidden");
        if (app) app.classList.remove("hidden");
      }
    } else {
      if (app && !app.classList.contains("hidden")) {
        app.classList.add("fade-out-active");
        setTimeout(() => {
          app.classList.add("hidden");
          app.classList.remove("fade-out-active");
          
          if (landing) {
            landing.classList.remove("hidden");
            landing.classList.add("fade-in-active");
            setTimeout(() => {
              landing.classList.remove("fade-in-active");
            }, 400);
          }
        }, 400);
      } else {
        if (app) app.classList.add("hidden");
        if (landing) landing.classList.remove("hidden");
      }
    }
  }

  // 6. UPDATE UI STATUS
  function updateAuthUI(user) {
    const loggedOutDiv = document.getElementById("auth-logged-out");
    const loggedInDiv = document.getElementById("auth-logged-in");
    const nameSpan = document.getElementById("auth-user-name");
    
    if (user) {
      if (loggedOutDiv) loggedOutDiv.style.display = "none";
      if (loggedInDiv) loggedInDiv.style.display = "flex";
      if (nameSpan) {
        const username = user.user_metadata?.username || user.user_metadata?.display_name || user.email;
        nameSpan.textContent = username;
      }
      transitionToApp(true);
    } else {
      if (loggedInDiv) loggedInDiv.style.display = "none";
      if (loggedOutDiv) loggedOutDiv.style.display = "flex";
      if (nameSpan) nameSpan.textContent = "";
      transitionToApp(false);
    }
  }

  // 7. LISTEN TO SESSION AND URL REDIRECTS
  client.auth.getSession().then(({ data: { session } }) => {
    currentUser = session ? session.user : null;
    currentSessionToken = session ? session.access_token : null;
    updateAuthUI(currentUser);
    updateUserFeaturesUI();
  });

  client.auth.onAuthStateChange((event, session) => {
    currentUser = session ? session.user : null;
    currentSessionToken = session ? session.access_token : null;
    updateAuthUI(currentUser);
    updateUserFeaturesUI();
    
    if (event === "PASSWORD_RECOVERY") {
      showAuthView("reset");
    }
  });

  // Check URL hash for recovery state fallback
  const hash = window.location.hash;
  if (hash && hash.includes("type=recovery")) {
    showAuthView("reset");
  }
}

/* ==========================================================================
   USER ACC VALUE AND GAMIFICATION FEATURES
   ========================================================================== */

function updateUserFeaturesUI() {
  const isLoggedIn = !!currentUser;
  
  // Enable / disable buttons
  const btnSaveFav = document.getElementById("btn-save-favorite");
  const txtNotes = document.getElementById("textarea-private-notes");
  const btnVoteA = document.getElementById("btn-vote-a");
  const btnVoteDraw = document.getElementById("btn-vote-draw");
  const btnVoteB = document.getElementById("btn-vote-b");
  const btnSubmitPronostic = document.getElementById("btn-submit-pronostic");
  const btnSavePreset = document.getElementById("btn-save-preset");
  const userPresetsRow = document.getElementById("user-presets-row");
  const txtStatus = document.getElementById("user-actions-status");

  if (btnSaveFav) btnSaveFav.disabled = !isLoggedIn;
  if (txtNotes) txtNotes.disabled = !isLoggedIn;
  if (btnVoteA) btnVoteA.disabled = !isLoggedIn;
  if (btnVoteDraw) btnVoteDraw.disabled = !isLoggedIn;
  if (btnVoteB) btnVoteB.disabled = !isLoggedIn;
  if (btnSubmitPronostic) btnSubmitPronostic.disabled = !isLoggedIn;
  if (btnSavePreset) btnSavePreset.disabled = !isLoggedIn;
  
  if (userPresetsRow) {
    userPresetsRow.style.display = isLoggedIn ? "flex" : "none";
  }

  if (txtStatus) {
    if (isLoggedIn) {
      const username = currentUser.user_metadata?.username || currentUser.user_metadata?.display_name || currentUser.email;
      txtStatus.innerHTML = `Conectado como <strong>${username}</strong>`;
      // Load their features
      loadUserPresets();
      loadPollData();
      loadUserPronosticStatus();
    } else {
      txtStatus.textContent = "Iniciar sesión para guardar favoritos y pronósticos.";
      if (userPresetsRow) userPresetsRow.innerHTML = "";
      const resultsCont = document.getElementById("poll-results-container");
      if (resultsCont) resultsCont.classList.add("hidden");
    }
  }
}

// ----------------------------------------------------
// CUSTOM PRESETS JS
// ----------------------------------------------------
async function loadUserPresets() {
  if (!currentSessionToken) return;
  try {
    const res = await fetch("/api/user/presets", {
      headers: { "Authorization": `Bearer ${currentSessionToken}` }
    });
    const json = await res.json();
    if (json.status === "success") {
      renderUserPresetsRow(json.presets);
      renderUserPresetsList(json.presets);
    }
  } catch (err) {
    console.error("Error loading user presets:", err);
  }
}

function renderUserPresetsRow(presets) {
  const row = document.getElementById("user-presets-row");
  if (!row) return;
  row.innerHTML = "";
  
  if (!presets || presets.length === 0) {
    row.style.display = "none";
    return;
  }
  
  row.style.display = "flex";
  
  presets.forEach(p => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-secondary preset-btn";
    btn.style = "padding: 3px 8px; font-size: 0.7rem; height: auto; min-height: unset; line-height: 1.2; border-color: var(--color-primary); background: rgba(99,102,241,0.05); color: var(--color-primary); margin-right: 4px; margin-bottom: 4px;";
    btn.textContent = p.preset_name;
    btn.addEventListener("click", () => {
      const wFifa = document.getElementById("input-weight-fifa");
      const wH2h = document.getElementById("input-weight-h2h");
      const decay = document.getElementById("input-decay");
      const ovrA = document.getElementById("input-override-a");
      const ovrB = document.getElementById("input-override-b");
      const altitude = document.getElementById("input-altitude");
      
      if (wFifa) wFifa.value = p.fifa_weight;
      if (wH2h) wH2h.value = p.h2h_weight;
      if (decay) decay.value = p.decay;
      if (ovrA) ovrA.value = p.override_a;
      if (ovrB) ovrB.value = p.override_b;
      if (altitude) altitude.value = p.altitude;
      
      updateMatchCard(true);
      updateWeightsPreview();
      
      // Auto run simulation if results visible
      const resultsTabHeader = document.getElementById("results-tab-header");
      if (resultsTabHeader && !resultsTabHeader.classList.contains("hidden")) {
        runPredictionFlow();
      }
    });
    row.appendChild(btn);
  });
}

function renderUserPresetsList(presets) {
  const container = document.getElementById("user-presets-list-container");
  if (!container) return;
  container.innerHTML = "";
  
  if (!presets || presets.length === 0) {
    container.innerHTML = `
      <div class="no-matches-message" style="text-align: center; color: var(--color-text-secondary); padding: 24px;">
        No has guardado ningún preset personalizado de ponderación.
      </div>
    `;
    return;
  }
  
  presets.forEach(p => {
    const card = document.createElement("div");
    card.className = "glass-card";
    card.style = "padding: 12px; display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.01); border-color: var(--card-border-inner); margin-bottom: 8px;";
    card.innerHTML = `
      <div>
        <h4 style="margin: 0; color: var(--color-primary); font-size: 0.9rem;">${p.preset_name}</h4>
        <span style="font-size: 0.72rem; color: var(--color-text-secondary);">
          FIFA: ${p.fifa_weight}% | H2H: ${p.h2h_weight}% | Decay: ${p.decay}m | Override: ${p.override_a}x / ${p.override_b}x | Alt: ${p.altitude}m
        </span>
      </div>
      <button class="btn" style="padding: 4px 8px; font-size: 0.7rem; background: #dc2626; color: white; border: none; border-radius: 4px; height: auto; min-height: unset; cursor: pointer;">
        Eliminar
      </button>
    `;
    
    card.querySelector("button").addEventListener("click", async () => {
      if (confirm(`¿Estás seguro de que deseas eliminar el preset "${p.preset_name}"?`)) {
        try {
          const res = await fetch(`/api/user/presets/${p.id}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${currentSessionToken}` }
          });
          const json = await res.json();
          if (json.status === "success") {
            loadUserPresets();
          }
        } catch (err) {
          console.error("Error deleting preset:", err);
        }
      }
    });
    
    container.appendChild(card);
  });
}

// ----------------------------------------------------
// FAVORITES JS
// ----------------------------------------------------
async function loadUserFavorites() {
  if (!currentSessionToken) return;
  try {
    const res = await fetch("/api/user/favorites", {
      headers: { "Authorization": `Bearer ${currentSessionToken}` }
    });
    const json = await res.json();
    if (json.status === "success") {
      renderUserFavorites(json.favorites);
    }
  } catch (err) {
    console.error("Error loading favorites:", err);
  }
}

function renderUserFavorites(favorites) {
  const container = document.getElementById("favorites-list-container");
  if (!container) return;
  container.innerHTML = "";
  
  if (!favorites || favorites.length === 0) {
    container.innerHTML = `
      <div class="no-matches-message" style="text-align: center; color: var(--color-text-secondary); padding: 24px;">
        No has guardado ningún partido en favoritos todavía. Haz clic en "⭐ Guardar en Favoritos" al simular un partido.
      </div>
    `;
    return;
  }
  
  favorites.forEach(f => {
    const metaA = TEAM_METADATA[f.team_a] || { name: f.team_a.toUpperCase(), flag: "🏳️" };
    const metaB = TEAM_METADATA[f.team_b] || { name: f.team_b.toUpperCase(), flag: "🏳️" };
    
    const card = document.createElement("div");
    card.className = "glass-card";
    card.style = "padding: 14px; background: rgba(255,255,255,0.015); border-color: var(--card-border-inner); display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px;";
    
    const d = new Date(f.created_at);
    const dateStr = d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--color-text-secondary);">
        <span>Guardado el ${dateStr}</span>
        <button class="btn-delete-fav" style="background: none; border: none; color: #ef4444; font-size: 0.72rem; cursor: pointer; padding: 0;">🗑️ Quitar</button>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: 600; font-size: 0.92rem; color: white;">${metaA.flag} ${metaA.name} vs ${metaB.flag} ${metaB.name}</span>
        <span class="badge" style="font-size: 0.78rem;">${f.xg_a.toFixed(1)} - ${f.xg_b.toFixed(1)} xG</span>
      </div>
      <div style="font-size: 0.78rem; color: var(--color-text-secondary);">
        Probabilidades: ${metaA.name.slice(0,5)} ${(f.prob_a*100).toFixed(0)}% / Emp ${(f.prob_draw*100).toFixed(0)}% / ${metaB.name.slice(0,5)} ${(f.prob_b*100).toFixed(0)}%
      </div>
      ${f.notes ? `
        <div style="background: rgba(0,0,0,0.15); padding: 8px 10px; border-radius: 6px; border-left: 2px solid var(--color-primary); font-size: 0.8rem; color: var(--color-text-primary); margin-top: 4px; white-space: pre-wrap;">
          <strong>Notas:</strong> ${f.notes}
        </div>
      ` : ''}
    `;
    
    card.querySelector(".btn-delete-fav").addEventListener("click", async () => {
      try {
        const res = await fetch(`/api/user/favorites/${f.id}`, {
          method: "DELETE",
          headers: { "Authorization": `Bearer ${currentSessionToken}` }
        });
        const json = await res.json();
        if (json.status === "success") {
          loadUserFavorites();
        }
      } catch (err) {
        console.error("Error deleting favorite:", err);
      }
    });
    
    container.appendChild(card);
  });
}

// ----------------------------------------------------
// COMMUNITY POLL & GUESSES JS
// ----------------------------------------------------
async function loadPollData() {
  try {
    const authHeaders = currentSessionToken ? { "Authorization": `Bearer ${currentSessionToken}` } : {};
    const res = await fetch(`/api/match/vote/${selectedTeamA}/${selectedTeamB}`, {
      headers: authHeaders
    });
    const json = await res.json();
    if (json.status === "success") {
      renderPollResults(json.stats, json.user_vote);
    }
  } catch (err) {
    console.error("Error loading poll stats:", err);
  }
}

function renderPollResults(stats, userVote) {
  const pollResults = document.getElementById("poll-results-container");
  const btnA = document.getElementById("btn-vote-a");
  const btnDraw = document.getElementById("btn-vote-draw");
  const btnB = document.getElementById("btn-vote-b");
  
  if (!pollResults) return;
  pollResults.classList.remove("hidden");
  
  const lblA = document.getElementById("poll-lbl-a");
  const lblDraw = document.getElementById("poll-lbl-draw");
  const lblB = document.getElementById("poll-lbl-b");
  
  const barA = document.getElementById("poll-bar-a");
  const barDraw = document.getElementById("poll-bar-draw");
  const barB = document.getElementById("poll-bar-b");
  
  const pA = stats.percentages.A;
  const pDraw = stats.percentages.Draw;
  const pB = stats.percentages.B;
  const total = stats.total;
  
  const metaA = TEAM_METADATA[selectedTeamA] || { name: selectedTeamA.toUpperCase() };
  const metaB = TEAM_METADATA[selectedTeamB] || { name: selectedTeamB.toUpperCase() };
  
  if (lblA) lblA.textContent = `Gana ${metaA.name}: ${pA}% (${stats.votes.A} votos)`;
  if (lblDraw) lblDraw.textContent = `Empate: ${pDraw}% (${stats.votes.Draw} votos)`;
  if (lblB) lblB.textContent = `Gana ${metaB.name}: ${pB}% (${stats.votes.B} votos)`;
  
  if (barA) barA.style.width = `${pA}%`;
  if (barDraw) barDraw.style.width = `${pDraw}%`;
  if (barB) barB.style.width = `${pB}%`;
  
  // Highlight user vote
  [btnA, btnDraw, btnB].forEach(btn => {
    if (btn) {
      btn.classList.remove("active", "btn-primary");
      btn.classList.add("btn-secondary");
    }
  });
  
  if (userVote === "A" && btnA) {
    btnA.classList.add("active", "btn-primary");
    btnA.classList.remove("btn-secondary");
  } else if (userVote === "Draw" && btnDraw) {
    btnDraw.classList.add("active", "btn-primary");
    btnDraw.classList.remove("btn-secondary");
  } else if (userVote === "B" && btnB) {
    btnB.classList.add("active", "btn-primary");
    btnB.classList.remove("btn-secondary");
  }
}

async function loadUserPronosticStatus() {
  if (!currentSessionToken) return;
  const btn = document.getElementById("btn-submit-pronostic");
  if (!btn) return;
  
  try {
    const res = await fetch(`/api/match/pronostic/${selectedTeamA}/${selectedTeamB}`, {
      headers: { "Authorization": `Bearer ${currentSessionToken}` }
    });
    const json = await res.json();
    if (json.status === "success" && json.pronostic) {
      btn.disabled = true;
      let guessText = json.pronostic.guess === "A" ? "Local" : json.pronostic.guess === "B" ? "Visitante" : "Empate";
      btn.textContent = `🎯 Pronóstico Oficial: ${guessText}`;
      btn.style.background = "rgba(99,102,241,0.15)";
      btn.style.color = "var(--color-primary)";
      btn.style.border = "1px solid var(--color-primary)";
    } else {
      btn.disabled = false;
      btn.textContent = "🎯 Guardar Pronóstico Oficial (Leaderboard)";
      btn.style.background = "var(--color-primary)";
      btn.style.color = "white";
      btn.style.border = "none";
    }
  } catch (err) {
    console.error("Error loading user pronostic status:", err);
  }
}

// ----------------------------------------------------
// LEADERBOARD JS
// ----------------------------------------------------
async function loadLeaderboard() {
  try {
    const res = await fetch("/api/leaderboard");
    const json = await res.json();
    if (json.status === "success") {
      renderLeaderboard(json.leaderboard);
    }
  } catch (err) {
    console.error("Error loading leaderboard:", err);
  }
}

function renderLeaderboard(rankings) {
  const tbody = document.getElementById("leaderboard-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  
  if (!rankings || rankings.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="3" style="padding: 24px; text-align: center; color: var(--color-text-secondary);">
          Aún no hay puntuaciones registradas. ¡Sé el primero en guardar tu pronóstico oficial!
        </td>
      </tr>
    `;
    return;
  }
  
  rankings.forEach((r, idx) => {
    const pos = idx + 1;
    let posHtml = pos;
    if (pos === 1) posHtml = "🥇";
    else if (pos === 2) posHtml = "🥈";
    else if (pos === 3) posHtml = "🥉";
    
    const row = document.createElement("tr");
    row.style = "border-bottom: 1px solid rgba(255,255,255,0.03);";
    row.innerHTML = `
      <td style="padding: 10px; font-weight: 700; font-size: 1rem;">${posHtml}</td>
      <td style="padding: 10px; font-weight: 600; color: white;">${r.username}</td>
      <td style="padding: 10px; text-align: right; font-weight: 700; color: var(--color-primary); font-family: var(--font-family-mono);">${r.points} pts</td>
    `;
    tbody.appendChild(row);
  });
}

/* ==========================================================================
   BET BUILDER SYSTEM
   ========================================================================== */
let bbChart = null;
let bbRadarChart = null;
let bbTimingChart = null;
let bbFavorites = [];

window.initBetBuilder = function() {
  const checkboxes = document.querySelectorAll('input[name="bb-leg"]');
  checkboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      window.updateBBSelectedCount();
      runBetBuilderSimulation();
    });
  });

  const btnSave = document.getElementById('btn-save-bb-favorite');
  if (btnSave) {
    btnSave.addEventListener('click', saveBetBuilderFavorite);
  }

  loadBetBuilderFavorites();
  updateBetBuilderLabels();
  switchBBSegment('summary');
  window.updateBBSelectedCount();
};

window.toggleBBAccordion = function(headerBtn) {
  const item = headerBtn.closest('.bb-accordion-item');
  if (!item) return;
  const content = item.querySelector('.bb-accordion-content');
  const arrow = headerBtn.querySelector('.bb-accordion-arrow');
  
  const isExpanded = item.classList.contains('expanded');
  
  if (isExpanded) {
    item.classList.remove('expanded');
    content.style.display = 'none';
    if (arrow) {
      arrow.textContent = '▶';
      arrow.style.transform = 'none';
    }
  } else {
    item.classList.add('expanded');
    const cat = item.getAttribute('data-category');
    content.style.display = (cat === 'goals') ? 'grid' : 'flex';
    if (arrow) {
      arrow.textContent = '▼';
    }
  }
};

window.filterBBMarkets = function() {
  const query = document.getElementById('bb-market-search').value.toLowerCase().trim();
  const items = document.querySelectorAll('.bb-accordion-item');
  
  items.forEach(item => {
    const content = item.querySelector('.bb-accordion-content');
    const header = item.querySelector('.bb-accordion-header');
    const arrow = header.querySelector('.bb-accordion-arrow');
    const labels = content.querySelectorAll('.bb-checkbox-label');
    
    let matchedAny = false;
    labels.forEach(lbl => {
      const text = lbl.textContent.toLowerCase();
      if (text.includes(query)) {
        lbl.style.display = 'flex';
        matchedAny = true;
      } else {
        lbl.style.display = 'none';
      }
    });
    
    if (query === '') {
      item.style.display = 'block';
      labels.forEach(lbl => lbl.style.display = 'flex');
      
      const cat = item.getAttribute('data-category');
      if (cat === 'outcome') {
        item.classList.add('expanded');
        content.style.display = 'flex';
        if (arrow) arrow.textContent = '▼';
      } else {
        item.classList.remove('expanded');
        content.style.display = 'none';
        if (arrow) arrow.textContent = '▶';
      }
    } else {
      if (matchedAny) {
        item.style.display = 'block';
        item.classList.add('expanded');
        const cat = item.getAttribute('data-category');
        content.style.display = (cat === 'goals') ? 'grid' : 'flex';
        if (arrow) arrow.textContent = '▼';
      } else {
        item.style.display = 'none';
      }
    }
  });
};

window.clearAllBBLegs = function() {
  const checkboxes = document.querySelectorAll('input[name="bb-leg"]');
  checkboxes.forEach(cb => cb.checked = false);
  window.updateBBSelectedCount();
  runBetBuilderSimulation();
};

window.updateBBSelectedCount = function() {
  const checked = document.querySelectorAll('input[name="bb-leg"]:checked');
  const countSpan = document.getElementById('bb-selected-count');
  if (countSpan) {
    countSpan.textContent = `(${checked.length})`;
  }
};

window.switchBBSegment = function(segmentName) {
  const buttons = document.querySelectorAll('.bb-segment-btn');
  buttons.forEach(btn => {
    if (btn.getAttribute('data-segment') === segmentName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  const allSegments = ['summary', 'goals', 'markets', 'validation'];
  allSegments.forEach(seg => {
    const cards = document.querySelectorAll('.bb-seg-' + seg);
    cards.forEach(card => {
      if (seg === segmentName) {
        card.classList.remove('bb-seg-hidden');
      } else {
        card.classList.add('bb-seg-hidden');
      }
    });
  });
};

window.updateBetBuilderLabels = function() {
  const nameA = TEAM_METADATA[selectedTeamA]?.name || "Local";
  const nameB = TEAM_METADATA[selectedTeamB]?.name || "Visitante";
  
  document.querySelectorAll('.bb-lbl-a').forEach(el => el.textContent = `Victoria ${nameA}`);
  document.querySelectorAll('.bb-lbl-b').forEach(el => el.textContent = `Victoria ${nameB}`);
};

// Evaluador de logros de goles a nivel de marcador exacto para el Heatmap y Validaciones
function evaluateScoreLeg(leg, a, b) {
  if (leg === "win_a") return a > b;
  if (leg === "draw") return a === b;
  if (leg === "win_b") return b > a;
  if (leg === "btts_yes") return a > 0 && b > 0;
  if (leg === "btts_no") return a === 0 || b === 0;
  if (leg === "double_chance_1X") return a >= b;
  if (leg === "double_chance_12") return a !== b;
  if (leg === "double_chance_X2") return b >= a;
  if (leg.startsWith("over_")) {
    const val = parseFloat(leg.split("_")[1]);
    return (a + b) > val;
  }
  if (leg.startsWith("under_")) {
    const val = parseFloat(leg.split("_")[1]);
    return (a + b) < val;
  }
  if (leg === "handicap_minus_1_5_a") return (a - b) > 1.5;
  if (leg === "handicap_plus_1_5_a") return (a - b) > -1.5;
  if (leg === "handicap_minus_1_5_b") return (b - a) > 1.5;
  if (leg === "handicap_plus_1_5_b") return (b - a) > -1.5;
  
  // Para córners u otros logros, retornamos true en la matriz de goles
  return true;
}

// Variable global para almacenar el último resultado de la probabilidad combinada
let lastCombinedProb = 0.0;

window.updateBetBuilderEdge = function() {
  const inputOdds = parseFloat(document.getElementById('bb-market-odds').value);
  const edgeEl = document.getElementById('bb-edge-value');
  const kellyEl = document.getElementById('bb-kelly-stake');
  const badgeEl = document.getElementById('bb-value-badge');
  
  if (isNaN(inputOdds) || inputOdds <= 1.0 || lastCombinedProb <= 0) {
    if (edgeEl) edgeEl.textContent = '0.0%';
    if (kellyEl) kellyEl.textContent = '0.0%';
    if (badgeEl) badgeEl.style.display = 'none';
    return;
  }
  
  const edge = (lastCombinedProb * inputOdds) - 1.0;
  const edgePct = (edge * 100).toFixed(1);
  if (edgeEl) {
    edgeEl.textContent = `${edgePct}%`;
    edgeEl.style.color = edge > 0.05 ? '#10b981' : '#ffffff';
  }
  
  // Criterio de Kelly (Fórmula: f* = (p*o - 1) / (o - 1) = Edge / (Odds - 1))
  const kelly = edge > 0 ? (edge / (inputOdds - 1.0)) : 0;
  // Brindar un stake moderado (Kelly fraccionario de 0.25 para evitar sobre-exposición)
  const recommendedStake = (kelly * 0.25 * 100).toFixed(1);
  if (kellyEl) {
    kellyEl.textContent = `${recommendedStake}%`;
  }
  
  if (badgeEl) {
    badgeEl.style.display = edge > 0.05 ? 'block' : 'none';
  }
};

window.runBetBuilderSimulation = async function() {
  updateBetBuilderLabels();

  const checkboxes = document.querySelectorAll('input[name="bb-leg"]:checked');
  const legs = Array.from(checkboxes).map(cb => cb.value);

  const combinedProbEl = document.getElementById('bb-combined-prob-circle');
  const fairOddsEl = document.getElementById('bb-fair-odds');
  const correlationsTbody = document.getElementById('bb-correlations-tbody');
  const heatmapTable = document.getElementById('bb-heatmap-table');
  const h2hTbody = document.getElementById('bb-h2h-tbody');
  const similarTbody = document.getElementById('bb-similar-tbody');
  const riskLevelEl = document.getElementById('bb-risk-level');

  if (legs.length === 0) {
    lastCombinedProb = 0.0;
    if (combinedProbEl) combinedProbEl.textContent = '0.0%';
    if (fairOddsEl) fairOddsEl.textContent = '1.00';
    if (correlationsTbody) {
      correlationsTbody.innerHTML = `<tr><td colspan="3" style="text-align: center; padding: 24px; color: var(--color-text-muted);">Selecciona 1 o más logros para ver correlaciones.</td></tr>`;
    }
    if (heatmapTable) heatmapTable.innerHTML = '';
    if (h2hTbody) {
      h2hTbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 15px; color: var(--color-text-muted);">Sin enfrentamientos directos registrados.</td></tr>`;
    }
    if (similarTbody) {
      similarTbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 15px; color: var(--color-text-muted);">Sin partidos con perfil similar.</td></tr>`;
    }
    if (bbChart) {
      bbChart.destroy();
      bbChart = null;
    }
    updateBetBuilderEdge();
    return;
  }

  if (combinedProbEl) combinedProbEl.textContent = '...';

  const payload = {
    teamA: selectedTeamA,
    teamB: selectedTeamB,
    rankA: parseInt(rankSliderA.value),
    rankB: parseInt(rankSliderB.value),
    fifaWeight: parseFloat(weightFifaSlider.value),
    h2hWeight: parseFloat(weightH2hSlider.value),
    decayMonths: parseInt(decaySlider.value),
    numSims: 100000,
    strengthOverrideA: inputOverrideA.value ? parseFloat(inputOverrideA.value) : 1.0,
    strengthOverrideB: inputOverrideB.value ? parseFloat(inputOverrideB.value) : 1.0,
    altitude: inputAltitude.value ? parseInt(inputAltitude.value) : 0,
    hostCountry: inputHostCountry.value || null,
    legs: legs
  };

  try {
    const res = await fetch("/api/betbuilder/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("API simulation error");
    const data = await res.json();

    const sim = data.simulation;
    const hist = data.historicalMatches;

    lastCombinedProb = sim.combinedProb;
    const combPct = (sim.combinedProb * 100).toFixed(1);
    if (combinedProbEl) combinedProbEl.textContent = `${combPct}%`;
    if (fairOddsEl) {
      const oddVal = sim.combinedProb > 0 ? (1.0 / sim.combinedProb).toFixed(2) : "999.00";
      fairOddsEl.textContent = `${oddVal}`;
    }

    // Clasificar Nivel de Riesgo
    if (riskLevelEl) {
      if (sim.combinedProb > 0.6) {
        riskLevelEl.textContent = 'Bajo';
        riskLevelEl.style.color = '#10b981';
      } else if (sim.combinedProb >= 0.3) {
        riskLevelEl.textContent = 'Medio';
        riskLevelEl.style.color = '#f59e0b';
      } else {
        riskLevelEl.textContent = 'Alto';
        riskLevelEl.style.color = '#ef4444';
      }
    }

    updateBetBuilderEdge();

    const correlationSummary = document.getElementById('bb-correlation-summary');
    if (correlationSummary) {
      if (sim.correlations.length > 0) {
        let maxCorr = sim.correlations[0];
        for (let c of sim.correlations) {
          if (Math.abs(c.coefficient) > Math.abs(maxCorr.coefficient)) {
            maxCorr = c;
          }
        }
        const strength = Math.abs(maxCorr.coefficient) > 0.4 ? "Fuerte" : Math.abs(maxCorr.coefficient) > 0.15 ? "Moderada" : "Débil";
        const direction = maxCorr.coefficient > 0 ? "positiva" : "negativa";
        correlationSummary.innerHTML = `Correlación más destacada: <strong>${translateLeg(maxCorr.legA)}</strong> con <strong>${translateLeg(maxCorr.legB)}</strong> (${strength} ${direction}, r=${maxCorr.coefficient.toFixed(2)})`;
      } else {
        correlationSummary.textContent = "Las selecciones correlacionadas ajustan la probabilidad final automáticamente.";
      }
    }

    renderBetBuilderChart(legs, sim.individualProbs, sim.combinedProb);
    
    const nameA = TEAM_METADATA[selectedTeamA]?.name || "Local";
    const nameB = TEAM_METADATA[selectedTeamB]?.name || "Visitante";
    updateBetBuilderAdvancedMetrics(sim, nameA, nameB);

    if (correlationsTbody) {
      if (sim.correlations.length === 0) {
        correlationsTbody.innerHTML = `<tr><td colspan="3" style="text-align: center; padding: 24px; color: var(--color-text-muted);">Selecciona 2 o más logros para ver correlaciones.</td></tr>`;
      } else {
        correlationsTbody.innerHTML = sim.correlations.map(c => {
          let colorClass = 'color: var(--color-text-secondary);';
          let bgClass = '';
          if (c.coefficient > 0.7) {
            colorClass = 'color: #047857; font-weight: bold;';
            bgClass = 'background: rgba(4, 120, 87, 0.1);';
          } else if (c.coefficient >= 0.3) {
            colorClass = 'color: #34d399;';
            bgClass = 'background: rgba(52, 211, 153, 0.05);';
          } else if (c.coefficient < -0.3) {
            colorClass = 'color: #f87171;';
            bgClass = 'background: rgba(248, 113, 113, 0.05);';
          }
          return `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.03); ${bgClass}" title="El coeficiente de Pearson cuantifica la correlación lineal entre ambos logros.">
              <td style="padding: 10px 4px; color: #ffffff;">${translateLeg(c.legA)}</td>
              <td style="padding: 10px 4px; color: #ffffff;">${translateLeg(c.legB)}</td>
              <td style="padding: 10px 4px; text-align: right; ${colorClass}">${c.coefficient.toFixed(4)}</td>
            </tr>
          `;
        }).join('');
      }
    }

    if (heatmapTable) {
      const nameA = TEAM_METADATA[selectedTeamA]?.name || "Local";
      const nameB = TEAM_METADATA[selectedTeamB]?.name || "Visitante";
      
      // Encontrar los 3 marcadores más probables que CUMPLEN la combinación
      let validScores = [];
      for (let a = 0; a < 6; a++) {
        for (let b = 0; b < 6; b++) {
          const p = sim.scoreHeatmap[a][b];
          let meets = true;
          for (let leg of legs) {
            if (!evaluateScoreLeg(leg, a, b)) {
              meets = false;
              break;
            }
          }
          if (meets) {
            validScores.push({ a, b, p });
          }
        }
      }
      validScores.sort((x, y) => y.p - x.p);
      const top3Keys = validScores.slice(0, 3).map(x => `${x.a}-${x.b}`);

      let html = `<thead><tr style="color: var(--color-text-secondary); font-weight: 600;"><th style="padding: 4px;">${nameA} \\ ${nameB}</th>`;
      for (let b = 0; b < 6; b++) {
        html += `<th style="padding: 4px;">${b}</th>`;
      }
      html += `</tr></thead><tbody>`;

      for (let a = 0; a < 6; a++) {
        html += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.02);"><td style="font-weight: 600; color: var(--color-text-secondary); padding: 4px;">${a}</td>`;
        for (let b = 0; b < 6; b++) {
          const p = sim.scoreHeatmap[a][b];
          const pct = (p * 100).toFixed(2);
          
          // Evaluar cumplimiento y partialRatio de condiciones de goles
          let metCount = 0;
          for (let leg of legs) {
            if (evaluateScoreLeg(leg, a, b)) metCount++;
          }
          const partialRatio = legs.length > 0 ? (metCount / legs.length) : 1.0;
          const meets = metCount === legs.length;

          // Colores condicionales
          let bgColor = `rgba(239, 68, 68, ${0.05 + 0.3 * (1.0 - partialRatio)})`; // Rojo si no cumple
          if (meets) {
            const density = Math.min(1.0, p / 0.10);
            bgColor = `rgba(16, 185, 129, ${0.15 + 0.7 * density})`; // Verde si cumple
          }

          const isTop3 = top3Keys.includes(`${a}-${b}`);
          const cellBorder = isTop3 ? 'border: 2px solid #fbbf24; font-weight: bold;' : 'border: 1px solid rgba(255,255,255,0.03);';
          const textPrefix = isTop3 ? '👑 ' : '';

          html += `<td style="padding: 8px 6px; background: ${bgColor}; border-radius: 4px; ${cellBorder} transition: transform 0.15s; cursor: help;" title="Score: ${a}-${b} | Probabilidad: ${pct}% | Cumple: ${metCount}/${legs.length}">${textPrefix}${pct}%</td>`;
        }
        html += `</tr>`;
      }
      html += `</tbody>`;
      heatmapTable.innerHTML = html;
    }

    // Calcular tasa de éxito histórica combinada
    const calculateSuccessRate = (matchesList) => {
      if (matchesList.length === 0) return "0.0%";
      const met = matchesList.filter(m => m.fullyMet).length;
      return `${((met / matchesList.length) * 100).toFixed(1)}%`;
    };

    if (h2hTbody) {
      if (hist.directH2H.length === 0) {
        h2hTbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 15px; color: var(--color-text-muted);">Sin enfrentamientos directos registrados.</td></tr>`;
      } else {
        h2hTbody.innerHTML = hist.directH2H.map(m => {
          const metStyle = m.fullyMet ? 'background: rgba(16, 185, 129, 0.15); color: #10b981;' : 'background: rgba(239, 68, 68, 0.1); color: #ef4444;';
          const metText = m.fullyMet ? 'CUMPLIDO' : 'FALLADO';
          return `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
              <td style="padding: 8px 4px; color: var(--color-text-secondary);">${m.date}</td>
              <td style="padding: 8px 4px; color: #ffffff;">${m.homeName} vs ${m.awayName}</td>
              <td style="padding: 8px 4px; text-align: center; font-weight: 600; color: #ffffff;">${m.score}</td>
              <td style="padding: 8px 4px; text-align: center;"><span style="padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; ${metStyle}">${metText}</span></td>
            </tr>
          `;
        }).join('');
        // Append success rate row
        h2hTbody.innerHTML += `
          <tr style="background: rgba(255,255,255,0.01); font-weight: bold; border-top: 1px solid var(--panel-border);">
            <td colspan="3" style="padding: 10px 4px; color: var(--color-text-primary);">Tasa de Éxito H2H Histórica:</td>
            <td style="padding: 10px 4px; text-align: center; color: var(--color-primary);">${calculateSuccessRate(hist.directH2H)}</td>
          </tr>
        `;
      }
    }

    if (similarTbody) {
      if (hist.similarProfile.length === 0) {
        similarTbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 15px; color: var(--color-text-muted);">Sin partidos con perfil similar.</td></tr>`;
      } else {
        similarTbody.innerHTML = hist.similarProfile.map(m => {
          const metStyle = m.fullyMet ? 'background: rgba(16, 185, 129, 0.15); color: #10b981;' : 'background: rgba(239, 68, 68, 0.1); color: #ef4444;';
          const metText = m.fullyMet ? 'CUMPLIDO' : 'FALLADO';
          return `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
              <td style="padding: 8px 4px; color: var(--color-text-secondary);">${m.date}</td>
              <td style="padding: 8px 4px; color: #ffffff;">${m.homeName} vs ${m.awayName}</td>
              <td style="padding: 8px 4px; text-align: center; font-weight: 600; color: #ffffff;">${m.score}</td>
              <td style="padding: 8px 4px; text-align: center; color: var(--color-primary); font-weight: 600;">${m.similarity}%</td>
              <td style="padding: 8px 4px; text-align: center;"><span style="padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; ${metStyle}">${metText}</span></td>
            </tr>
          `;
        }).join('');
        // Append success rate row
        similarTbody.innerHTML += `
          <tr style="background: rgba(255,255,255,0.01); font-weight: bold; border-top: 1px solid var(--panel-border);">
            <td colspan="4" style="padding: 10px 4px; color: var(--color-text-primary);">Tasa de Éxito Perfil Similar:</td>
            <td style="padding: 10px 4px; text-align: center; color: var(--color-primary);">${calculateSuccessRate(hist.similarProfile)}</td>
          </tr>
        `;
      }
    }

  } catch (error) {
    console.error("Error running bet builder simulation:", error);
    if (combinedProbEl) combinedProbEl.textContent = 'ERROR';
  }
};

window.translateLeg = function(legKey) {
  if (legKey === "win_a") return "Victoria Local";
  if (legKey === "draw") return "Empate";
  if (legKey === "win_b") return "Victoria Visitante";
  if (legKey === "btts_yes") return "Ambos Anotan: Sí";
  if (legKey === "btts_no") return "Ambos Anotan: No";
  if (legKey === "double_chance_1X") return "Doble Oportunidad: 1X";
  if (legKey === "double_chance_12") return "Doble Oportunidad: 12";
  if (legKey === "double_chance_X2") return "Doble Oportunidad: X2";
  if (legKey.startsWith("over_") && legKey.endsWith("_goals")) {
    const val = legKey.split("_")[1];
    return `Goles: Over ${val}`;
  }
  if (legKey.startsWith("under_") && legKey.endsWith("_goals")) {
    const val = legKey.split("_")[1];
    return `Goles: Under ${val}`;
  }
  if (legKey === "corners_win_a") return "Más Córners Local";
  if (legKey === "corners_draw") return "Empate Córners";
  if (legKey === "corners_win_b") return "Más Córners Visitante";
  if (legKey.startsWith("corners_over_")) {
    const val = legKey.split("_")[2] + "." + legKey.split("_")[3];
    return `Córners: Over ${val}`;
  }
  if (legKey.startsWith("corners_under_")) {
    const val = legKey.split("_")[2] + "." + legKey.split("_")[3];
    return `Córners: Under ${val}`;
  }
  if (legKey.startsWith("handicap_minus_")) {
    const val = legKey.split("_")[2] + "." + legKey.split("_")[3];
    const team = legKey.endsWith("_a") ? "Local" : "Visitante";
    return `Handicap ${team} -${val}`;
  }
  if (legKey.startsWith("handicap_plus_")) {
    const val = legKey.split("_")[2] + "." + legKey.split("_")[3];
    const team = legKey.endsWith("_a") ? "Local" : "Visitante";
    return `Handicap ${team} +${val}`;
  }
  return legKey;
};

window.renderBetBuilderChart = function(legs, individualProbs, combinedProb) {
  const ctx = document.getElementById('bb-chart-canvas');
  if (!ctx) return;

  const textColor = document.body.classList.contains('light-theme') ? '#122a52' : '#ffffff';

  const labels = legs.map(l => translateLeg(l)).concat(["COMBINADA REAL"]);
  const dataValues = legs.map(l => (individualProbs[l] * 100).toFixed(1)).concat([(combinedProb * 100).toFixed(1)]);
  const bgColors = legs.map(() => 'rgba(255, 255, 255, 0.15)').concat(['rgba(240, 179, 16, 0.65)']);
  const borderColors = legs.map(() => 'rgba(255, 255, 255, 0.3)').concat(['rgba(240, 179, 16, 1)']);

  if (bbChart) {
    bbChart.data.labels = labels;
    bbChart.data.datasets[0].data = dataValues;
    bbChart.data.datasets[0].backgroundColor = bgColors;
    bbChart.data.datasets[0].borderColor = borderColors;
    bbChart.update();
  } else {
    bbChart = new Chart(ctx.getContext('2d'), {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Probabilidad (%)',
          data: dataValues,
          backgroundColor: bgColors,
          borderColor: borderColors,
          borderWidth: 1.5,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `Probabilidad: ${context.parsed.y}%`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: textColor }
          },
          x: {
            grid: { display: false },
            ticks: { color: textColor }
          }
        }
      }
    });
  }
};

window.updateBetBuilderAdvancedMetrics = function(sim, nameA, nameB) {
  const adv = sim.advanced;
  if (!adv) return;

  // 1. Expected Points (xPTS)
  const xptsA = adv.xptsA;
  const xptsB = adv.xptsB;
  const xptsElA = document.getElementById("bb-xpts-a");
  const xptsElB = document.getElementById("bb-xpts-b");
  const xptsBarA = document.getElementById("bb-xpts-bar-a");
  const xptsBarB = document.getElementById("bb-xpts-bar-b");
  
  if (xptsElA) xptsElA.textContent = xptsA.toFixed(2);
  if (xptsElB) xptsElB.textContent = xptsB.toFixed(2);
  if (xptsBarA && xptsBarB) {
    const total = xptsA + xptsB;
    const pctA = total > 0 ? (xptsA / total) * 100 : 50;
    xptsBarA.style.width = `${pctA}%`;
    xptsBarB.style.width = `${100 - pctA}%`;
  }

  // 2. Clean Sheet
  const csElA = document.getElementById("bb-cs-pct-a");
  const csElB = document.getElementById("bb-cs-pct-b");
  const csBarA = document.getElementById("bb-cs-bar-a");
  const csBarB = document.getElementById("bb-cs-bar-b");
  if (csElA) csElA.textContent = `${(adv.csA * 100).toFixed(1)}%`;
  if (csElB) csElB.textContent = `${(adv.csB * 100).toFixed(1)}%`;
  if (csBarA && csBarB) {
    csBarA.style.width = `${adv.csA * 100}%`;
    csBarB.style.width = `${adv.csB * 100}%`;
  }

  // 3. Win to Nil
  const w2nElA = document.getElementById("bb-w2n-pct-a");
  const w2nElB = document.getElementById("bb-w2n-pct-b");
  const w2nBarA = document.getElementById("bb-w2n-bar-a");
  const w2nBarB = document.getElementById("bb-w2n-bar-b");
  if (w2nElA) w2nElA.textContent = `${(adv.w2nA * 100).toFixed(1)}%`;
  if (w2nElB) w2nElB.textContent = `${(adv.w2nB * 100).toFixed(1)}%`;
  if (w2nBarA && w2nBarB) {
    w2nBarA.style.width = `${adv.w2nA * 100}%`;
    w2nBarB.style.width = `${adv.w2nB * 100}%`;
  }

  // 4. Asian Handicap
  const ahA1 = document.getElementById("bb-ah-a1");
  const ahA2 = document.getElementById("bb-ah-a2");
  const ahB1 = document.getElementById("bb-ah-b1");
  const ahB2 = document.getElementById("bb-ah-b2");
  if (ahA1) ahA1.textContent = `${(adv.ahMinus1_5A * 100).toFixed(1)}%`;
  if (ahA2) ahA2.textContent = `${(adv.ahMinus1_0A * 100).toFixed(1)}%`;
  if (ahB1) ahB1.textContent = `${(adv.ahPlus0_5B * 100).toFixed(1)}%`;
  if (ahB2) ahB2.textContent = `${(adv.ahPlus1_5B * 100).toFixed(1)}%`;

  // 5. HT/FT Matrix
  const htft = adv.htft;
  if (htft) {
    const elAA = document.getElementById("bb-htft-aa");
    const elDA = document.getElementById("bb-htft-da");
    const elBA = document.getElementById("bb-htft-ba");
    const elAD = document.getElementById("bb-htft-ad");
    const elDD = document.getElementById("bb-htft-dd");
    const elBD = document.getElementById("bb-htft-bd");
    const elAB = document.getElementById("bb-htft-ab");
    const elDB = document.getElementById("bb-htft-db");
    const elBB = document.getElementById("bb-htft-bb");

    if (elAA) elAA.textContent = `${(htft.AA * 100).toFixed(1)}%`;
    if (elDA) elDA.textContent = `${(htft.DA * 100).toFixed(1)}%`;
    if (elBA) elBA.textContent = `${(htft.BA * 100).toFixed(1)}%`;
    if (elAD) elAD.textContent = `${(htft.AD * 100).toFixed(1)}%`;
    if (elDD) elDD.textContent = `${(htft.DD * 100).toFixed(1)}%`;
    if (elBD) elBD.textContent = `${(htft.BD * 100).toFixed(1)}%`;
    if (elAB) elAB.textContent = `${(htft.AB * 100).toFixed(1)}%`;
    if (elDB) elDB.textContent = `${(htft.DB * 100).toFixed(1)}%`;
    if (elBB) elBB.textContent = `${(htft.BB * 100).toFixed(1)}%`;
  }

  // 6. Goal Bands
  const band01Pct = document.getElementById("bb-band-0-1-pct");
  const band23Pct = document.getElementById("bb-band-2-3-pct");
  const band45Pct = document.getElementById("bb-band-4-5-pct");
  const band6Pct = document.getElementById("bb-band-6-pct");
  
  const band01Bar = document.getElementById("bb-band-0-1-bar");
  const band23Bar = document.getElementById("bb-band-2-3-bar");
  const band45Bar = document.getElementById("bb-band-4-5-bar");
  const band6Bar = document.getElementById("bb-band-6-bar");

  if (band01Pct) band01Pct.textContent = `${(adv.band_0_1 * 100).toFixed(1)}%`;
  if (band23Pct) band23Pct.textContent = `${(adv.band_2_3 * 100).toFixed(1)}%`;
  if (band45Pct) band45Pct.textContent = `${(adv.band_4_5 * 100).toFixed(1)}%`;
  if (band6Pct) band6Pct.textContent = `${(adv.band_6_plus * 100).toFixed(1)}%`;

  if (band01Bar) band01Bar.style.width = `${adv.band_0_1 * 100}%`;
  if (band23Bar) band23Bar.style.width = `${adv.band_2_3 * 100}%`;
  if (band45Bar) band45Bar.style.width = `${adv.band_4_5 * 100}%`;
  if (band6Bar) band6Bar.style.width = `${adv.band_6_plus * 100}%`;

  // 7. Comparison Table
  const compHeaderA = document.getElementById("bb-comp-header-a");
  const compHeaderB = document.getElementById("bb-comp-header-b");
  if (compHeaderA) compHeaderA.textContent = nameA;
  if (compHeaderB) compHeaderB.textContent = nameB;

  const compXgA = document.getElementById("bb-comp-xg-a");
  const compXgB = document.getElementById("bb-comp-xg-b");
  if (compXgA) compXgA.textContent = sim.xgA.toFixed(2);
  if (compXgB) compXgB.textContent = sim.xgB.toFixed(2);

  const compShotsA = document.getElementById("bb-comp-shots-a");
  const compShotsB = document.getElementById("bb-comp-shots-b");
  if (compShotsA) compShotsA.textContent = adv.shotsA.toFixed(1);
  if (compShotsB) compShotsB.textContent = adv.shotsB.toFixed(1);

  const compCornersA = document.getElementById("bb-comp-corners-a");
  const compCornersB = document.getElementById("bb-comp-corners-b");
  if (compCornersA) compCornersA.textContent = adv.cornersA.toFixed(1);
  if (compCornersB) compCornersB.textContent = adv.cornersB.toFixed(1);

  const compPossA = document.getElementById("bb-comp-poss-a");
  const compPossB = document.getElementById("bb-comp-poss-b");
  if (compPossA) compPossA.textContent = `${adv.possessionA.toFixed(1)}%`;
  if (compPossB) compPossB.textContent = `${adv.possessionB.toFixed(1)}%`;

  const compCsA = document.getElementById("bb-comp-cs-a");
  const compCsB = document.getElementById("bb-comp-cs-b");
  if (compCsA) compCsA.textContent = `${(adv.csA * 100).toFixed(1)}%`;
  if (compCsB) compCsB.textContent = `${(adv.csB * 100).toFixed(1)}%`;

  // 8. Confidence Interval
  const confInterval = (sim.combinedProb > 0) ? (adv.confWinA * 100).toFixed(1) : "0.0";
  const probCircle = document.getElementById("bb-combined-prob-circle");
  if (probCircle) {
    const origText = (sim.combinedProb * 100).toFixed(1) + "%";
    probCircle.innerHTML = `${origText}<span style="display: block; font-size: 0.85rem; font-weight: normal; color: var(--color-text-muted); margin-top: 4px;">±${confInterval}% (Confianza 95%)</span>`;
  }

  // 9. Radar Chart
  renderBetBuilderRadar(adv, nameA, nameB);

  // 10. Timing Chart
  renderBetBuilderTiming(adv.timingDist);
};

window.renderBetBuilderRadar = function(adv, nameA, nameB) {
  const ctx = document.getElementById('bb-radar-canvas');
  if (!ctx) return;

  const textColor = document.body.classList.contains('light-theme') ? '#122a52' : '#ffffff';
  
  const attackA = Math.min(100, Math.max(0, (adv.xgA / 3.0) * 100));
  const attackB = Math.min(100, Math.max(0, (adv.xgB / 3.0) * 100));
  
  const defenseA = adv.csA * 100;
  const defenseB = adv.csB * 100;

  const formA = adv.formA * 10;
  const formB = adv.formB * 10;

  const cornersA = Math.min(100, Math.max(0, (adv.cornersA / 10.0) * 100));
  const cornersB = Math.min(100, Math.max(0, (adv.cornersB / 10.0) * 100));

  const shotsA = Math.min(100, Math.max(0, (adv.shotsA / 20.0) * 100));
  const shotsB = Math.min(100, Math.max(0, (adv.shotsB / 20.0) * 100));

  const possA = adv.possessionA;
  const possB = adv.possessionB;

  const dataA = [attackA, defenseA, formA, cornersA, shotsA, possA];
  const dataB = [attackB, defenseB, formB, cornersB, shotsB, possB];

  if (bbRadarChart) {
    bbRadarChart.data.datasets[0].label = nameA;
    bbRadarChart.data.datasets[0].data = dataA;
    bbRadarChart.data.datasets[0].rawValues = [adv.xgA, adv.csA * 100, adv.formA, adv.cornersA, adv.shotsA, adv.possessionA];
    
    bbRadarChart.data.datasets[1].label = nameB;
    bbRadarChart.data.datasets[1].data = dataB;
    bbRadarChart.data.datasets[1].rawValues = [adv.xgB, adv.csB * 100, adv.formB, adv.cornersB, adv.shotsB, adv.possessionB];
    
    bbRadarChart.options.scales.r.pointLabels.color = textColor;
    bbRadarChart.options.plugins.legend.labels.color = textColor;
    bbRadarChart.update();
  } else {
    bbRadarChart = new Chart(ctx.getContext('2d'), {
      type: 'radar',
      data: {
        labels: ['Ataque (xG)', 'Defensa (Clean Sheet)', 'Forma Reciente', 'Córners Proyectados', 'Tiros Esperados', 'Posesión Estimada'],
        datasets: [
          {
            label: nameA,
            data: dataA,
            rawValues: [adv.xgA, adv.csA * 100, adv.formA, adv.cornersA, adv.shotsA, adv.possessionA],
            backgroundColor: 'rgba(59, 130, 246, 0.15)',
            borderColor: 'rgba(59, 130, 246, 0.95)',
            pointBackgroundColor: '#3b82f6',
            pointBorderColor: '#0f172a',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2
          },
          {
            label: nameB,
            data: dataB,
            rawValues: [adv.xgB, adv.csB * 100, adv.formB, adv.cornersB, adv.shotsB, adv.possessionB],
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            borderColor: 'rgba(16, 185, 129, 0.95)',
            pointBackgroundColor: '#10b981',
            pointBorderColor: '#0f172a',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: textColor,
              boxWidth: 10,
              boxHeight: 10,
              usePointStyle: true,
              pointStyle: 'circle',
              font: {
                family: "'Inter', sans-serif",
                size: 11,
                weight: '600'
              }
            }
          },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1',
            borderColor: '#475569',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8,
            titleFont: {
              family: "'Inter', sans-serif",
              size: 12,
              weight: 'bold'
            },
            bodyFont: {
              family: "'Inter', sans-serif",
              size: 11
            },
            callbacks: {
              label: function(context) {
                const dataset = context.dataset;
                const index = context.dataIndex;
                const raw = dataset.rawValues[index];
                
                if (index === 0) return `${dataset.label} - Proyección xG: ${raw.toFixed(2)}`;
                if (index === 1) return `${dataset.label} - Arco en Cero (CS): ${raw.toFixed(1)}%`;
                if (index === 2) return `${dataset.label} - Forma: ${raw.toFixed(1)}/10`;
                if (index === 3) return `${dataset.label} - Córners Proyectados: ${raw.toFixed(1)}`;
                if (index === 4) return `${dataset.label} - Tiros Proyectados: ${raw.toFixed(1)}`;
                if (index === 5) return `${dataset.label} - Posesión: ${raw.toFixed(1)}%`;
                return `${dataset.label}: ${context.raw.toFixed(1)}`;
              }
            }
          }
        },
        scales: {
          r: {
            grid: {
              color: 'rgba(71, 85, 105, 0.35)',
              circular: true
            },
            angleLines: {
              color: 'rgba(71, 85, 105, 0.4)'
            },
            pointLabels: {
              color: textColor,
              font: {
                family: "'Inter', sans-serif",
                size: 10,
                weight: '500'
              }
            },
            ticks: {
              display: false,
              stepSize: 20
            },
            suggestedMin: 0,
            suggestedMax: 100
          }
        }
      }
    });
  }
};

window.renderBetBuilderTiming = function(timingDist) {
  const ctx = document.getElementById('bb-timing-canvas');
  if (!ctx) return;

  const textColor = document.body.classList.contains('light-theme') ? '#122a52' : '#ffffff';
  const labels = ['0-15 min', '16-30 min', '31-45 min', '46-60 min', '61-75 min', '76-90 min'];

  if (bbTimingChart) {
    bbTimingChart.data.datasets[0].data = timingDist;
    bbTimingChart.update();
  } else {
    bbTimingChart = new Chart(ctx.getContext('2d'), {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Distribución Temporal Goles (%)',
          data: timingDist,
          backgroundColor: 'rgba(245, 158, 11, 0.15)',
          borderColor: 'rgba(245, 158, 11, 1)',
          pointBackgroundColor: 'rgba(245, 158, 11, 1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: textColor, callback: v => `${v}%` }
          },
          x: {
            grid: { display: false },
            ticks: { color: textColor }
          }
        }
      }
    });
  }
};

window.saveBetBuilderFavorite = function() {
  const checkboxes = document.querySelectorAll('input[name="bb-leg"]:checked');
  const legs = Array.from(checkboxes).map(cb => cb.value);
  if (legs.length === 0) {
    alert("Selecciona al menos un logro para guardar.");
    return;
  }

  const dialog = document.getElementById('bb-save-dialog');
  const input = document.getElementById('bb-save-name-input');
  const confirmBtn = document.getElementById('bb-confirm-save-btn');
  
  if (!dialog || !input || !confirmBtn) return;
  
  // Limpiar valor del input
  input.value = `Combo ${TEAM_METADATA[selectedTeamA]?.name || selectedTeamA}`;
  dialog.showModal();
  
  confirmBtn.onclick = function() {
    const customName = input.value.trim() || `Combo JLY`;
    const nameA = TEAM_METADATA[selectedTeamA]?.name || selectedTeamA;
    const nameB = TEAM_METADATA[selectedTeamB]?.name || selectedTeamB;

    const newFav = {
      id: Date.now(),
      name: customName,
      teamA: selectedTeamA,
      teamB: selectedTeamB,
      teamAName: nameA,
      teamBName: nameB,
      legs: legs,
      createdAt: new Date().toISOString()
    };

    bbFavorites.push(newFav);
    localStorage.setItem('bb_favorites', JSON.stringify(bbFavorites));
    renderBetBuilderFavoritesList();
    dialog.close();
  };
};

window.loadBetBuilderFavorites = function() {
  try {
    const raw = localStorage.getItem('bb_favorites');
    bbFavorites = raw ? JSON.parse(raw) : [];
  } catch (e) {
    bbFavorites = [];
  }
  renderBetBuilderFavoritesList();
};

window.renderBetBuilderFavoritesList = function() {
  const container = document.getElementById('bb-favorites-container');
  if (!container) return;

  if (bbFavorites.length === 0) {
    container.innerHTML = `<div style="text-align: center; color: var(--color-text-muted); font-size: 0.8rem; padding: 10px;">No hay combinaciones guardadas.</div>`;
    return;
  }

  container.innerHTML = bbFavorites.map(fav => {
    const legBadges = fav.legs.map(l => `<span style="display: inline-block; font-size: 0.68rem; background: rgba(255,255,255,0.05); color: var(--color-text-secondary); padding: 2px 6px; border-radius: 4px;">${translateLeg(l)}</span>`).join(' ');
    return `
      <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border-inner); padding: 12px; border-radius: 8px; display: flex; justify-content: space-between; align-items: start; gap: 8px; transition: background 0.2s;">
        <div style="cursor: pointer; flex: 1;" onclick="applyBetBuilderFavorite(${fav.id})">
          <div style="font-size: 0.85rem; font-weight: bold; color: var(--color-primary); margin-bottom: 4px;">
            ${fav.name}
          </div>
          <div style="font-size: 0.75rem; color: #a1a1aa; margin-bottom: 6px;">
            ${TEAM_METADATA[fav.teamA]?.flag || ''} ${fav.teamAName} vs ${fav.teamBName} ${TEAM_METADATA[fav.teamB]?.flag || ''}
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 4px;">
            ${legBadges}
          </div>
        </div>
        <button style="background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.85rem; padding: 0 4px;" onclick="deleteBetBuilderFavorite(${fav.id}, event)" title="Eliminar combinación">
          ❌
        </button>
      </div>
    `;
  }).join('');
};

window.applyBetBuilderFavorite = function(favId) {
  const fav = bbFavorites.find(f => f.id === favId);
  if (!fav) return;

  selectedTeamA = fav.teamA;
  selectedTeamB = fav.teamB;
  
  const selectElA = document.getElementById("select-team-a");
  const selectElB = document.getElementById("select-team-b");
  if (selectElA) selectElA.value = fav.teamA;
  if (selectElB) selectElB.value = fav.teamB;
  
  try {
    if (selectElA && selectElA.tomselect) selectElA.tomselect.setValue(fav.teamA);
    if (selectElB && selectElB.tomselect) selectElB.tomselect.setValue(fav.teamB);
  } catch (e) {}

  if (TEAM_METADATA[selectedTeamA]) rankSliderA.value = TEAM_METADATA[selectedTeamA].rank;
  if (TEAM_METADATA[selectedTeamB]) rankSliderB.value = TEAM_METADATA[selectedTeamB].rank;
  
  const fifaDisplayA = document.getElementById("fifa-display-a");
  const fifaDisplayB = document.getElementById("fifa-display-b");
  if (fifaDisplayA) fifaDisplayA.textContent = `FIFA #${rankSliderA.value}`;
  if (fifaDisplayB) fifaDisplayB.textContent = `FIFA #${rankSliderB.value}`;

  updateMatchCard();

  document.querySelectorAll('input[name="bb-leg"]').forEach(cb => {
    cb.checked = fav.legs.includes(cb.value);
  });

  runBetBuilderSimulation();
};

window.deleteBetBuilderFavorite = function(favId, event) {
  event.stopPropagation();
  bbFavorites = bbFavorites.filter(f => f.id !== favId);
  localStorage.setItem('bb_favorites', JSON.stringify(bbFavorites));
  renderBetBuilderFavoritesList();
};

// ==========================================================================
// FASE 2: FUNCIONALIDADES PREMIUM PARA MONETIZACIÓN
// ==========================================================================

// TAREA 2.1: EXPORTAR ANÁLISIS A PDF
window.exportBetBuilderPDF = function() {
  const nameA = TEAM_METADATA[selectedTeamA]?.name || "Local";
  const nameB = TEAM_METADATA[selectedTeamB]?.name || "Visitante";
  const checkboxes = document.querySelectorAll('input[name="bb-leg"]:checked');
  const legs = Array.from(checkboxes).map(cb => translateLeg(cb.value));
  
  if (legs.length === 0) {
    alert("Por favor, selecciona logros para generar un reporte.");
    return;
  }
  
  const combPct = (lastCombinedProb * 100).toFixed(1);
  const fairOdds = lastCombinedProb > 0 ? (1.0 / lastCombinedProb).toFixed(2) : "999.00";
  const dateStr = new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  
  // Encontrar marcadores más probables que cumplen la combinada
  let validScores = [];
  const heatmapTable = document.getElementById('bb-heatmap-table');
  if (heatmapTable) {
    for (let a = 0; a < 6; a++) {
      for (let b = 0; b < 6; b++) {
        const cell = heatmapTable.querySelector(`tbody tr:nth-child(${a + 1}) td:nth-child(${b + 2})`);
        if (cell) {
          const title = cell.getAttribute('title') || '';
          const meets = cell.style.background.includes("rgba(16, 185, 129");
          if (meets && title.includes("Probabilidad: ")) {
            const pStr = title.split("Probabilidad: ")[1].split("%")[0];
            const p = parseFloat(pStr) / 100;
            validScores.push({ score: `${a}-${b}`, p });
          }
        }
      }
    }
  }
  validScores.sort((x, y) => y.p - x.p);
  const topScoresHtml = validScores.slice(0, 5).map((s, idx) => `
    <li style="font-size: 0.9rem; margin-bottom: 6px; color: #ffffff;">
      <strong>#${idx + 1} Marcador ${s.score}</strong> — Probabilidad: ${(s.p * 100).toFixed(2)}%
    </li>
  `).join('');

  const element = document.createElement('div');
  element.style.padding = '35px';
  element.style.background = '#0f172a';
  element.style.color = '#ffffff';
  element.style.fontFamily = "'Inter', sans-serif";
  element.style.borderRadius = '12px';
  element.style.outline = 'none';
  element.style.border = 'none';
  element.style.boxShadow = 'none';
  element.style.userSelect = 'none';
  element.style.webkitUserSelect = 'none';
  element.style.pointerEvents = 'none';
  // Necesario para que html2canvas pueda renderizar el elemento
  element.style.position = 'fixed';
  element.style.top = '-9999px';
  element.style.left = '-9999px';
  element.style.width = '794px'; // A4 ancho aprox a 96dpi
  element.style.zIndex = '-9999';
  document.body.appendChild(element);
  
  element.innerHTML = `
    <div style="border-bottom: 2px solid #f0b310; padding-bottom: 20px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h1 style="color: #f0b310; margin: 0; font-family: 'Outfit', sans-serif; font-size: 1.8rem;">JLYPREDICTION</h1>
        <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">Reporte de Análisis Estadístico Pro</span>
      </div>
      <div style="text-align: right; font-size: 0.75rem; color: #94a3b8;">
        Fecha: ${dateStr}
      </div>
    </div>
    
    <h2 style="font-size: 1.4rem; font-family: 'Outfit', sans-serif; margin-bottom: 10px; color: #ffffff;">
      Partido: ${nameA} vs ${nameB}
    </h2>
    <p style="font-size: 0.85rem; color: #94a3b8; margin-top: 0; margin-bottom: 20px;">
      Simulación Monte Carlo realizada sobre 100,000 iteraciones en base al modelo bivariado Dixon-Coles.
    </p>
    
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 18px; border-radius: 8px; margin-bottom: 25px;">
      <h3 style="margin-top: 0; font-size: 1rem; color: #f0b310; text-transform: uppercase;">Logros Combinados (Bet Builder)</h3>
      <ul style="padding-left: 20px; font-size: 0.9rem; line-height: 1.5; color: #cbd5e1;">
        ${legs.map(l => `<li>${l}</li>`).join('')}
      </ul>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
      <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15); padding: 15px; border-radius: 8px; text-align: center;">
        <span style="font-size: 0.8rem; color: #a7f3d0; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 5px;">Probabilidad Real</span>
        <div style="font-size: 2.2rem; font-weight: 800; color: #10b981;">${combPct}%</div>
      </div>
      <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center;">
        <span style="font-size: 0.8rem; color: #cbd5e1; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 5px;">Cuota Justa</span>
        <div style="font-size: 2.2rem; font-weight: 800; color: #ffffff;">${fairOdds}</div>
      </div>
    </div>
    
    <div style="margin-bottom: 30px;">
      <h3 style="border-left: 3px solid #f0b310; padding-left: 10px; font-size: 1.05rem; margin-bottom: 15px;">👑 Marcadores Más Probables que Cumplen</h3>
      <ul style="padding-left: 0; list-style: none;">
        ${topScoresHtml || '<li style="color: #94a3b8; font-size: 0.85rem;">Ningún marcador compatible entre las opciones simuladas.</li>'}
      </ul>
    </div>
    
    <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px; font-size: 0.75rem; color: #64748b; text-align: center; margin-top: 40px;">
      © JLYPrediction Engine. Todos los derechos reservados. Las apuestas deportivas conllevan riesgos de pérdida.
    </div>
  `;
  
  const options = {
    margin: 10,
    filename: `JLYPrediction_${nameA.replace(/\s+/g, '_')}_vs_${nameB.replace(/\s+/g, '_')}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: {
      scale: 2,
      backgroundColor: '#0f172a',
      useCORS: true,
      logging: false,
      windowWidth: 794
    },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };

  html2pdf().from(element).set(options).save().then(() => {
    document.body.removeChild(element);
  }).catch(() => {
    if (document.body.contains(element)) document.body.removeChild(element);
  });
};

// TAREA 2.2: COMPARADOR DE CUOTAS
window.updateOddsComparison = function() {
  const tbody = document.getElementById('odds-compare-tbody');
  if (!tbody || lastCombinedProb <= 0) return;

  const houses = [
    { name: "Bet365", inputId: "odds-bet365" },
    { name: "1xBet", inputId: "odds-1xbet" },
    { name: "Pinnacle", inputId: "odds-pinnacle" },
    { name: "Betfair", inputId: "odds-betfair" }
  ];

  let results = [];
  houses.forEach(h => {
    const el = document.getElementById(h.inputId);
    const odds = el ? parseFloat(el.value) : NaN;
    if (!isNaN(odds) && odds > 1.0) {
      const edge = (lastCombinedProb * odds) - 1.0;
      const payout = (100 * odds - 100);
      results.push({ name: h.name, odds, edge, payout });
    }
  });

  if (results.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 15px; color: var(--color-text-muted);">Ingresa una cuota arriba para comparar.</td></tr>`;
    return;
  }

  results.sort((x, y) => y.edge - x.edge);
  const bestName = results[0].name;

  tbody.innerHTML = results.map(r => {
    const isBest = r.name === bestName;
    const edgeColor = r.edge > 0.05 ? '#10b981' : r.edge < 0 ? '#ef4444' : 'var(--color-text-secondary)';
    const rowBorder = isBest ? 'border: 2px solid #fbbf24; background: rgba(251,191,36,0.03); font-weight: bold;' : 'border-bottom: 1px solid rgba(255,255,255,0.02);';
    const bestBadge = isBest ? ' <span style="color: #fbbf24; font-size: 0.7rem; font-weight: bold; border: 1px solid #fbbf24; padding: 1px 4px; border-radius: 4px; margin-left: 5px;">🔥 MEJOR</span>' : '';
    return `
      <tr style="${rowBorder}">
        <td style="padding: 10px 4px; color: #ffffff;">${r.name}${bestBadge}</td>
        <td style="padding: 10px 4px; text-align: center; color: #ffffff;">${r.odds.toFixed(2)}</td>
        <td style="padding: 10px 4px; text-align: center; color: ${edgeColor};">${(r.edge * 100).toFixed(1)}%</td>
        <td style="padding: 10px 4px; text-align: right; color: #ffffff;">$${r.payout.toFixed(2)}</td>
      </tr>
    `;
  }).join('');
};

// TAREA 2.3: MODO INVERSO (HEDGING)
let inverseModeActive = false;

window.toggleInverseMode = function() {
  inverseModeActive = !inverseModeActive;
  const btn = document.getElementById('btn-toggle-inverse');
  const panel = document.getElementById('inverse-metrics-panel');
  
  if (!btn || !panel) return;
  
  if (inverseModeActive) {
    btn.textContent = "Desactivar Inverso";
    btn.style.background = "rgba(239, 68, 68, 0.15)";
    btn.style.borderColor = "#ef4444";
    btn.style.color = "#ef4444";
    panel.style.display = "flex";
    
    const invProb = 1.0 - lastCombinedProb;
    const invOdds = invProb > 0 ? (1.0 / invProb) : 999.00;
    
    document.getElementById('bb-inverse-prob').textContent = `${(invProb * 100).toFixed(1)}%`;
    document.getElementById('bb-inverse-odds').textContent = `${invOdds.toFixed(2)}`;
  } else {
    btn.textContent = "Activar Inverso";
    btn.style.background = "rgba(240,179,16,0.15)";
    btn.style.borderColor = "var(--color-primary)";
    btn.style.color = "var(--color-primary)";
    panel.style.display = "none";
  }
};

// TAREA 2.4: ALERTAS DE VALUE BETS
window.toggleAlertsState = function() {
  const enabled = document.getElementById('alert-enable').checked;
  const config = document.getElementById('alerts-config-fields');
  if (config) config.style.display = enabled ? 'flex' : 'none';
};

async function dispatchValueBetEmail(toEmail, details) {
  const payload = {
    service_id: "service_default",
    template_id: "template_value_bet",
    user_id: "user_default_key",
    template_params: {
      to_email: toEmail,
      match_name: details.matchName,
      legs: details.legs.join(", "),
      prob: details.prob,
      odds: details.odds,
      edge: details.edge
    }
  };
  
  try {
    const res = await fetch("https://api.emailjs.com/api/v1.0/email/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      console.log("EmailJS: Alerta enviada con éxito.");
    }
  } catch (e) {
    console.error("Error al enviar alerta por email:", e);
  }
}

function checkAndTriggerValueBetAlert(prob, fairOdds) {
  const alertsEnabled = document.getElementById('alert-enable')?.checked;
  if (!alertsEnabled) return;
  
  const minEdge = parseFloat(document.getElementById('alert-min-edge').value);
  const email = document.getElementById('alert-email').value.trim();
  const inputOdds = parseFloat(document.getElementById('bb-market-odds').value);
  
  if (isNaN(inputOdds) || inputOdds <= 1.0) return;
  
  const edge = (prob * inputOdds) - 1.0;
  if (edge >= minEdge) {
    const nameA = TEAM_METADATA[selectedTeamA]?.name || selectedTeamA;
    const nameB = TEAM_METADATA[selectedTeamB]?.name || selectedTeamB;
    const checkboxes = document.querySelectorAll('input[name="bb-leg"]:checked');
    const legs = Array.from(checkboxes).map(cb => translateLeg(cb.value));

    const alertDetails = {
      matchName: `${nameA} vs ${nameB}`,
      legs: legs,
      prob: `${(prob * 100).toFixed(1)}%`,
      odds: inputOdds.toFixed(2),
      edge: `${(edge * 100).toFixed(1)}%`
    };

    const historyLog = document.getElementById('alert-history-log');
    if (historyLog) {
      historyLog.innerHTML = `⚡ <strong>Value Bet:</strong> ${alertDetails.matchName} a cuota <strong>${alertDetails.odds}</strong> (Edge: <span style="color: #10b981; font-weight: bold;">+${alertDetails.edge}</span>)`;
    }

    const savedLogs = JSON.parse(localStorage.getItem('bb_alerts_history') || '[]');
    savedLogs.push({ ...alertDetails, timestamp: new Date().toISOString() });
    localStorage.setItem('bb_alerts_history', JSON.stringify(savedLogs));

    if (email) {
      dispatchValueBetEmail(email, alertDetails);
    }
  }
}

const originalRunSim = window.runBetBuilderSimulation;
window.runBetBuilderSimulation = async function() {
  await originalRunSim();
  
  if (inverseModeActive) {
    const invProb = 1.0 - lastCombinedProb;
    const invOdds = invProb > 0 ? (1.0 / invProb) : 999.00;
    const invProbEl = document.getElementById('bb-inverse-prob');
    const invOddsEl = document.getElementById('bb-inverse-odds');
    if (invProbEl) invProbEl.textContent = `${(invProb * 100).toFixed(1)}%`;
    if (invOddsEl) invOddsEl.textContent = `${invOdds.toFixed(2)}`;
  }
  
  checkAndTriggerValueBetAlert(lastCombinedProb, lastCombinedProb > 0 ? 1 / lastCombinedProb : 999);
};

// Control de navegación de pestañas en móvil/tablet para el Bet Builder
window.switchBetBuilderTab = function(activeTabName) {
  const buttons = {
    'markets': document.getElementById('bb-nav-btn-markets'),
    'summary': document.getElementById('bb-nav-btn-summary')
  };
  
  for (let key in buttons) {
    if (buttons[key]) buttons[key].classList.remove('active');
  }
  if (buttons[activeTabName]) buttons[activeTabName].classList.add('active');

  const allTabGroups = [
    { cls: 'bb-card-markets', active: activeTabName === 'markets' },
    { cls: 'bb-card-summary',  active: activeTabName === 'summary' }
  ];

  allTabGroups.forEach(({ cls, active }) => {
    document.querySelectorAll('.' + cls).forEach(c => {
      if (active) {
        c.classList.remove('bb-tab-hidden');
      } else {
        c.classList.add('bb-tab-hidden');
      }
    });
  });
};

