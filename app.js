// Predictor Mundial 2026 - Frontend Client Logic
// Communicates with the FastAPI Python Backend for all computations, simulations, and betting odds analysis.

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
        new TomSelect("#select-team-a", {
          create: false,
          sortField: { field: "text", direction: "asc" }
        });
        
        new TomSelect("#select-team-b", {
          create: false,
          sortField: { field: "text", direction: "asc" }
        });

        new TomSelect("#ai-team-a", {
          create: false,
          sortField: { field: "text", direction: "asc" }
        });

        new TomSelect("#ai-team-b", {
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

    // 6. Init bet builder segments (hide non-summary)
    document.querySelectorAll('#bb-col-results [id^="bb-container-"]').forEach(el => {
      if (!el.classList.contains('bb-seg-summary')) el.style.display = 'none';
    });

    // 6.1. Initial segment button state
    document.querySelectorAll('.bb-segment-btn').forEach(b => b.classList.toggle('active', b.dataset.segment === 'summary'));

    // 7. Ready (Wait for manual simulation)

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

  const aiTeamA = document.getElementById("ai-team-a");
  const aiTeamB = document.getElementById("ai-team-b");

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
        if (targetId === "tab-analysis") {
          fetchAITacticalAnalysis(selectedTeamA, selectedTeamB);
        } else if (targetId === "tab-history") {
          loadAdvancedH2HData();
          loadH2HData();
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
    
    // Check and load AI analysis if it was already saved for this match
    fetchAITacticalAnalysis(selectedTeamA, selectedTeamB);
    
    // Load community poll and official predictions status
    loadPollData();
    loadUserPronosticStatus();
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

// ===== ADVANCED H2H CENTER =====
let h2hAdvancedCharts = { radar: null, doughnut: null, period: null };

window.switchH2HSubTab = function(name) {
  document.querySelectorAll('.h2h-subtab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.h2h-subtab-content').forEach(c => c.classList.remove('active'));
  const btn = document.getElementById(`h2hst-btn-${name}`);
  const content = document.getElementById(`h2hst-${name}`);
  if (btn) btn.classList.add('active');
  if (content) content.classList.add('active');

  if (name === 'charts') {
    setTimeout(() => {
      Object.values(h2hAdvancedCharts).forEach(ch => { if (ch) ch.resize(); });
    }, 50);
  }
};

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

    if (count > 0) {
      const pA = Math.round(h2h.winsA / count * 100);
      const pD = Math.round(h2h.draws / count * 100);
      const pB = 100 - pA - pD;
      const barA = document.getElementById('h2h-bar-a');
      const barDraw = document.getElementById('h2h-bar-draw');
      const barB = document.getElementById('h2h-bar-b');
      if (barA) barA.style.width = pA + '%';
      if (barDraw) barDraw.style.width = pD + '%';
      if (barB) barB.style.width = Math.max(0, pB) + '%';
      const winSample = document.getElementById('h2h-winbar-sample');
      if (winSample) winSample.textContent = `${count} partidos`;
      const legA = document.getElementById('h2h-bar-legend-a');
      const legD = document.getElementById('h2h-bar-legend-d');
      const legB = document.getElementById('h2h-bar-legend-b');
      if (legA) legA.textContent = `${metaA.name.slice(0,8)}: ${h2h.winsA}V (${pA}%)`;
      if (legD) legD.textContent = `${h2h.draws}E (${pD}%)`;
      if (legB) legB.textContent = `${metaB.name.slice(0,8)}: ${h2h.winsB}V (${Math.max(0,pB)}%)`;
    }

    [['h2h-btts-pct','btts'],['h2h-o25-pct','over25'],['h2h-csa-pct','csA'],['h2h-csb-pct','csB']].forEach(([id,k]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = h2h.patterns[k] + '%';
    });
    const csaLbl = document.getElementById('h2h-csa-lbl');
    const csbLbl = document.getElementById('h2h-csb-lbl');
    if (csaLbl) csaLbl.textContent = `CS ${metaA.name.slice(0,8)}`;
    if (csbLbl) csbLbl.textContent = `CS ${metaB.name.slice(0,8)}`;

    [['h2h-cond-home','homeA'],['h2h-cond-away','awayA'],['h2h-cond-neutral','neutral']].forEach(([id,k]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = h2h.byCondition[k];
    });
    const condHomeLbl = document.getElementById('h2h-cond-home-lbl');
    const condAwayLbl = document.getElementById('h2h-cond-away-lbl');
    if (condHomeLbl) condHomeLbl.textContent = `${metaA.name.slice(0,8)} de Local`;
    if (condAwayLbl) condAwayLbl.textContent = `${metaA.name.slice(0,8)} de Visit.`;

    const scoresTbody = document.getElementById('h2h-scores-tbody');
    if (scoresTbody) {
      if (h2h.mostFrequentScores.length === 0) {
        scoresTbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding: 20px; color: var(--color-text-muted);">Sin datos</td></tr>`;
      } else {
        const maxCount = h2h.mostFrequentScores[0].count;
        scoresTbody.innerHTML = h2h.mostFrequentScores.map(s => {
          const barW = Math.round(s.count / maxCount * 100);
          const freq = count > 0 ? Math.round(s.count / count * 100) : 0;
          return `<tr><td><span class="h2h-score-badge">${s.score}</span></td><td style="font-family: var(--font-family-mono); font-weight: 700;">${s.count}x</td><td style="min-width: 80px;"><div style="display: flex; align-items: center; gap: 6px;"><div class="h2h-score-bar-mini" style="width: ${barW}px; max-width: 80px;"></div><span style="font-size: 0.7rem; color: var(--color-text-muted);">${freq}%</span></div></td></tr>`;
        }).join('');
      }
    }

    const compTbody = document.getElementById('h2h-comp-tbody');
    if (compTbody) {
      if (!h2h.byCompetition.length) {
        compTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px; color: var(--color-text-muted);">Sin datos</td></tr>`;
      } else {
        const sorted = [...h2h.byCompetition].sort((a, b) => b.pj - a.pj);
        compTbody.innerHTML = sorted.map(c => `<tr><td style="max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.76rem;">${c.competition}</td><td style="text-align: center; font-family: var(--font-family-mono); font-weight: 700;">${c.pj}</td><td style="text-align: center; color: var(--color-team-a); font-weight: 700;">${c.winsA}</td><td style="text-align: center; color: #6b7280; font-weight: 700;">${c.draws}</td><td style="text-align: center; color: var(--color-team-b); font-weight: 700;">${c.winsB}</td></tr>`).join('');
      }
    }

    const timelineEl = document.getElementById('h2h-timeline-list');
    if (timelineEl) {
      const timeline = [...(h2h.timeline || [])].reverse();
      if (!timeline.length) {
        timelineEl.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--color-text-muted); font-size: 0.82rem;">Sin partidos registrados</div>`;
      } else {
        timelineEl.innerHTML = timeline.map(m => {
          const isAHome = m.homeName === metaA.name || (m.homeName && m.homeName.toLowerCase().includes(selectedTeamA.split('-')[0]));
          const gsA = isAHome ? m.hg : m.ag;
          const gsB = isAHome ? m.ag : m.hg;
          const winClass = gsA > gsB ? 'win-a' : (gsA < gsB ? 'win-b' : 'draw');
          return `<div class="h2h-timeline-match ${winClass}"><span class="h2h-timeline-date">${m.date}</span><span class="h2h-timeline-teams">${m.homeName} vs ${m.awayName}</span><span class="h2h-timeline-score">${m.hg} – ${m.ag}</span><span class="h2h-timeline-comp">${m.tournament || ''}</span></div>`;
        }).join('');
      }
    }

    const scorersGrid = document.getElementById('h2h-scorers-grid');
    if (scorersGrid) {
      if (!scorers.topScorers.length) {
        scorersGrid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding: 20px; color: var(--color-text-muted); font-size:0.82rem;">No hay datos de goleadores para este H2H</div>`;
      } else {
        const rankLabels = ['top1', 'top2', 'top3', '', ''];
        scorersGrid.innerHTML = scorers.topScorers.map((s, i) => {
          const statusDot = s.active ? `<span class="h2h-scorer-status-active" title="Activo"></span>` : `<span class="h2h-scorer-status-retired" title="Retirado"></span>`;
          return `<div class="h2h-scorer-card"><span class="h2h-scorer-rank ${rankLabels[i] || ''}">#${i + 1}</span><div class="h2h-scorer-info"><div class="h2h-scorer-name">${s.name} ${statusDot}</div><div class="h2h-scorer-team">${s.team}</div></div><span class="h2h-scorer-goals">⚽ ${s.goals}</span></div>`;
        }).join('');
      }
    }

    const scorerExtraGrid = document.getElementById('h2h-scorer-extra-grid');
    if (scorerExtraGrid) {
      scorerExtraGrid.innerHTML = `<div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${scorers.avgGoalMinute || 0}'</span><span class="h2h-adv-stat-label">Min. Promedio de Gol</span></div><div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${scorers.penaltiesCount}</span><span class="h2h-adv-stat-label">Penaltis Marcados</span></div><div class="h2h-adv-stat"><span class="h2h-adv-stat-num">${scorers.ownGoalsCount}</span><span class="h2h-adv-stat-label">Autogoles</span></div>`;
    }

    const periodGrid = document.getElementById('h2h-period-grid');
    if (periodGrid) {
      const periods = ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90'];
      const pcts = scorers.periodDistribution || {};
      const maxPct = Math.max(...periods.map(p => pcts[p] || 0), 1);
      periodGrid.innerHTML = periods.map(p => {
        const pct = pcts[p] || 0;
        const barH = Math.round((pct / maxPct) * 32);
        return `<div class="h2h-period-cell"><div class="h2h-period-bar-wrap"><div class="h2h-period-bar" style="height: ${barH}px;"></div></div><span class="h2h-period-pct">${pct}%</span><span class="h2h-period-label">${p}'</span></div>`;
      }).join('');
    }

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
        statsEl.innerHTML = `<div class="h2h-form-stat-row"><span class="h2h-form-stat-key">Goles marcados/partido</span><span class="h2h-form-stat-val">${formData.avg_gf}</span></div><div class="h2h-form-stat-row"><span class="h2h-form-stat-key">Goles recibidos/partido</span><span class="h2h-form-stat-val">${formData.avg_gc}</span></div><div class="h2h-form-stat-row"><span class="h2h-form-stat-key">Portería a cero</span><span class="h2h-form-stat-val">${formData.clean_sheets}%</span></div><div class="h2h-form-stat-row"><span class="h2h-form-stat-key">BTTS</span><span class="h2h-form-stat-val">${formData.btts}%</span></div><div class="h2h-form-stat-row"><span class="h2h-form-stat-key">Over 2.5</span><span class="h2h-form-stat-val">${formData.over25}%</span></div>`;
      }

      if (streaksEl) {
        const s = formData.streaks;
        streaksEl.innerHTML = `<div class="h2h-streak-badge"><span class="h2h-streak-num">${s.unbeaten}</span><span class="h2h-streak-lbl">Sin perder</span></div><div class="h2h-streak-badge"><span class="h2h-streak-num">${s.losing}</span><span class="h2h-streak-lbl">Derrotas consec.</span></div><div class="h2h-streak-badge"><span class="h2h-streak-num">${s.scoring}</span><span class="h2h-streak-lbl">Marcando</span></div><div class="h2h-streak-badge"><span class="h2h-streak-num">${s.clean_sheet}</span><span class="h2h-streak-lbl">Portería a 0</span></div>`;
      }

      if (rivalEl) {
        const r = formData.by_rival;
        rivalEl.innerHTML = `<div class="h2h-rival-cell"><div class="h2h-rival-level">🔴 Top Nivel</div><div class="h2h-rival-rec">${r.top}</div></div><div class="h2h-rival-cell"><div class="h2h-rival-level">🟡 Nivel Alto</div><div class="h2h-rival-rec">${r.high}</div></div><div class="h2h-rival-cell"><div class="h2h-rival-level">🟢 Nivel Medio</div><div class="h2h-rival-rec">${r.mid}</div></div><div class="h2h-rival-cell"><div class="h2h-rival-level">⚪ Nivel Bajo</div><div class="h2h-rival-rec">${r.low}</div></div>`;
      }
    }

    renderFormCard(form.teamA, metaA.name, metaA.flag, 'a');
    renderFormCard(form.teamB, metaB.name, metaB.flag, 'b');

    // ══ INSIGHTS TAB ══
    const insightsList = document.getElementById('h2h-insights-list');
    if (insightsList) {
      if (!insights.detectedPatterns || !insights.detectedPatterns.length) {
        insightsList.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--color-text-muted); font-size: 0.82rem;">Sin insights disponibles</div>`;
      } else {
        insightsList.innerHTML = insights.detectedPatterns.map(p =>
          `<div class="h2h-insight-item">${p}</div>`
        ).join('');
      }
    }

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
    const isLight = document.body.classList.contains('light-theme');
    const textCol = isLight ? 'rgba(15, 23, 42, 0.6)' : 'rgba(255,255,255,0.6)';
    const gridCol = isLight ? 'rgba(15, 23, 42, 0.06)' : 'rgba(255,255,255,0.06)';
    const primaryCol = '#f0b310';

    // Destroy old charts dynamically using Chart.getChart
    ['h2h-radar-chart', 'h2h-doughnut-chart', 'h2h-period-chart'].forEach(id => {
      const cv = document.getElementById(id);
      if (cv) {
        const ec = Chart.getChart(cv);
        if (ec) ec.destroy();
      }
    });

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
            borderColor: [isLight ? '#fff' : '#1a2035', isLight ? '#fff' : '#1a2035', isLight ? '#fff' : '#1a2035'],
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

    loadingEl.style.display = 'none';
    contentEl.style.display = 'block';
  } catch(e) {
    console.error('Error loading advanced H2H:', e);
    loadingEl.innerHTML = '<div style="text-align:center;padding:40px;color:#ef4444;">Error al cargar datos avanzados de H2H</div>';
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
    const wA = h2hWinsA ? parseInt(h2hWinsA.textContent) || 0 : 0;
    const wB = h2hWinsB ? parseInt(h2hWinsB.textContent) || 0 : 0;
    const dr = h2hDraws ? parseInt(h2hDraws.textContent) || 0 : 0;
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

// ── Update Bet Builder Analytics (radar, comparison table, HT/FT, goal bands, timings) ──
function updateBetBuilderAnalytics(data) {
  if (!data) return;

  const metaA = TEAM_METADATA[selectedTeamA] || { name: "Local", flag: "🏳️" };
  const metaB = TEAM_METADATA[selectedTeamB] || { name: "Visitante", flag: "🏳️" };

  // 1. Update Comparison Table Headers and Cells
  const headA = document.getElementById("bb-comp-header-a");
  const headB = document.getElementById("bb-comp-header-b");
  if (headA) headA.textContent = metaA.name.slice(0, 10);
  if (headB) headB.textContent = metaB.name.slice(0, 10);

  const statsA = data.comparisonStats.teamA;
  const statsB = data.comparisonStats.teamB;

  if (statsA && statsB) {
    // xG
    const xgAEl = document.getElementById("bb-comp-xg-a");
    const xgBEl = document.getElementById("bb-comp-xg-b");
    if (xgAEl) xgAEl.textContent = data.xgA.toFixed(2);
    if (xgBEl) xgBEl.textContent = data.xgB.toFixed(2);

    // Shots
    const shAEl = document.getElementById("bb-comp-shots-a");
    const shBEl = document.getElementById("bb-comp-shots-b");
    if (shAEl) shAEl.textContent = statsA.shots_per_90.toFixed(1);
    if (shBEl) shBEl.textContent = statsB.shots_per_90.toFixed(1);

    // Corners
    const crnAEl = document.getElementById("bb-comp-corners-a");
    const crnBEl = document.getElementById("bb-comp-corners-b");
    if (crnAEl) crnAEl.textContent = data.cornersPrediction.expectedA.toFixed(1);
    if (crnBEl) crnBEl.textContent = data.cornersPrediction.expectedB.toFixed(1);

    // Ball Possession (Elo projection)
    const eloDiff = statsA.elo - statsB.elo;
    const possA = Math.max(35, Math.min(65, 50 + eloDiff / 20));
    const possB = 100 - possA;
    const possAEl = document.getElementById("bb-comp-poss-a");
    const possBEl = document.getElementById("bb-comp-poss-b");
    if (possAEl) possAEl.textContent = possA.toFixed(1) + "%";
    if (possBEl) possBEl.textContent = possB.toFixed(1) + "%";

    // Clean Sheet
    const csA = Math.exp(-data.xgB) * 100;
    const csB = Math.exp(-data.xgA) * 100;
    const csAEl = document.getElementById("bb-comp-cs-a");
    const csBEl = document.getElementById("bb-comp-cs-b");
    if (csAEl) csAEl.textContent = csA.toFixed(1) + "%";
    if (csBEl) csBEl.textContent = csB.toFixed(1) + "%";
    
    // xPTS
    const xptsAEl = document.getElementById("bb-xpts-a");
    const xptsBEl = document.getElementById("bb-xpts-b");
    const xptsBarA = document.getElementById("bb-xpts-bar-a");
    const xptsBarB = document.getElementById("bb-xpts-bar-b");
    
    const xptsA = data.probWinA * 3 + data.probDraw * 1;
    const xptsB = data.probWinB * 3 + data.probDraw * 1;
    if (xptsAEl) xptsAEl.textContent = xptsA.toFixed(2);
    if (xptsBEl) xptsBEl.textContent = xptsB.toFixed(2);
    
    const xptsTotal = xptsA + xptsB || 1;
    if (xptsBarA) xptsBarA.style.width = (xptsA / xptsTotal * 100).toFixed(1) + "%";
    if (xptsBarB) xptsBarB.style.width = (xptsB / xptsTotal * 100).toFixed(1) + "%";
    
    // Clean Sheet Bars (for pro segment)
    const csAProEl = document.getElementById("bb-cs-a");
    const csBProEl = document.getElementById("bb-cs-b");
    const csBarA = document.getElementById("bb-cs-bar-a");
    const csBarB = document.getElementById("bb-cs-bar-b");
    if (csAProEl) csAProEl.textContent = csA.toFixed(1) + "%";
    if (csBProEl) csBProEl.textContent = csB.toFixed(1) + "%";
    const csTotal = csA + csB || 1;
    if (csBarA) csBarA.style.width = (csA / csTotal * 100).toFixed(1) + "%";
    if (csBarB) csBarB.style.width = (csB / csTotal * 100).toFixed(1) + "%";
  }

  // 2. Render Radar Chart
  const radarCanvas = document.getElementById("bb-radar-canvas");
  if (radarCanvas && statsA && statsB) {
    const existingRadar = Chart.getChart(radarCanvas);
    if (existingRadar) existingRadar.destroy();

    const isLight = document.body.classList.contains("light-theme");
    const textCol = isLight ? "rgba(15, 23, 42, 0.6)" : "rgba(255, 255, 255, 0.6)";
    const gridCol = isLight ? "rgba(15, 23, 42, 0.06)" : "rgba(255, 255, 255, 0.06)";

    const attackA = Math.min(100, Math.max(0, (statsA.xg_overall / 3.0) * 100));
    const attackB = Math.min(100, Math.max(0, (statsB.xg_overall / 3.0) * 100));
    const defenseA = Math.min(100, Math.max(0, ((3.0 - statsA.xga_overall) / 3.0) * 100));
    const defenseB = Math.min(100, Math.max(0, ((3.0 - statsB.xga_overall) / 3.0) * 100));
    const formDiffA = statsA.form_gs - statsA.form_gc;
    const formDiffB = statsB.form_gs - statsB.form_gc;
    const formA = Math.min(100, Math.max(0, (formDiffA + 2.0) * 25));
    const formB = Math.min(100, Math.max(0, (formDiffB + 2.0) * 25));
    const eloScoreA = Math.min(100, Math.max(0, ((statsA.elo - 1300) / 900) * 100));
    const eloScoreB = Math.min(100, Math.max(0, ((statsB.elo - 1300) / 900) * 100));
    const matchXgScoreA = Math.min(100, Math.max(0, (statsA.match_xg / 3.0) * 100));
    const matchXgScoreB = Math.min(100, Math.max(0, (statsB.match_xg / 3.0) * 100));

    new Chart(radarCanvas, {
      type: 'radar',
      data: {
        labels: ['Ataque', 'Defensa', 'Forma', 'Prestigio', 'xG Proyectado'],
        datasets: [
          {
            label: metaA.name.slice(0, 10),
            data: [attackA, defenseA, formA, eloScoreA, matchXgScoreA],
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            borderColor: '#3b82f6',
            borderWidth: 2,
            pointBackgroundColor: '#3b82f6',
            pointRadius: 2
          },
          {
            label: metaB.name.slice(0, 10),
            data: [attackB, defenseB, formB, eloScoreB, matchXgScoreB],
            backgroundColor: 'rgba(16, 185, 129, 0.2)',
            borderColor: '#10b981',
            borderWidth: 2,
            pointBackgroundColor: '#10b981',
            pointRadius: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: textCol, font: { size: 9 } } } },
        scales: {
          r: {
            min: 0, max: 100,
            ticks: { color: textCol, font: { size: 8 }, stepSize: 25, backdropColor: 'transparent' },
            grid: { color: gridCol },
            pointLabels: { color: textCol, font: { size: 8 } },
            angleLines: { color: gridCol }
          }
        }
      }
    });
  }

  // 3. Render score heatmap table
  const heatmapTable = document.getElementById("bb-heatmap-table");
  if (heatmapTable && data.scoreHeatmap) {
    const m = data.scoreHeatmap;
    let tableHtml = `
      <thead>
        <tr style="border-bottom: 1px solid var(--panel-border);">
          <th style="padding: 4px; color: var(--color-text-secondary); font-size: 0.7rem;">${metaA.name.slice(0,3)} \\ ${metaB.name.slice(0,3)}</th>
          <th style="padding: 4px; font-weight: bold; color: var(--color-team-b);">0</th>
          <th style="padding: 4px; font-weight: bold; color: var(--color-team-b);">1</th>
          <th style="padding: 4px; font-weight: bold; color: var(--color-team-b);">2</th>
          <th style="padding: 4px; font-weight: bold; color: var(--color-team-b);">3</th>
          <th style="padding: 4px; font-weight: bold; color: var(--color-team-b);">4</th>
        </tr>
      </thead>
      <tbody>
    `;
    for (let a = 0; a < 5; a++) {
      tableHtml += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.01);">
        <td style="padding: 4px; font-weight: bold; color: var(--color-team-a); border-right: 1px solid var(--panel-border);">${a}</td>
      `;
      for (let b = 0; b < 5; b++) {
        const prob = m[a][b];
        const probPct = (prob * 100).toFixed(1);
        const opacity = Math.min(0.85, prob * 5).toFixed(2);
        const bg = `rgba(245, 158, 11, ${opacity})`;
        const text = prob > 0.08 ? '#000000' : '#ffffff';
        tableHtml += `<td style="padding: 6px 4px; background: ${bg}; color: ${text}; font-weight: bold; font-family: monospace; border-radius: 2px;" title="${metaA.name} ${a} - ${b} ${metaB.name}: ${probPct}%">
          ${probPct}%
        </td>`;
      }
      tableHtml += `</tr>`;
    }
    tableHtml += `</tbody>`;
    heatmapTable.innerHTML = tableHtml;
  }

  // 4. Update Mitad/Final (HT/FT) Matrix
  const htftAA = document.getElementById("bb-htft-aa");
  const htftDA = document.getElementById("bb-htft-da");
  const htftBA = document.getElementById("bb-htft-ba");
  const htftAD = document.getElementById("bb-htft-ad");
  const htftDD = document.getElementById("bb-htft-dd");
  const htftBD = document.getElementById("bb-htft-bd");
  const htftAB = document.getElementById("bb-htft-ab");
  const htftDB = document.getElementById("bb-htft-db");
  const htftBB = document.getElementById("bb-htft-bb");

  if (htftAA) {
    const wA = data.probWinA;
    const wD = data.probDraw;
    const wB = data.probWinB;

    let aa = wA * (0.6 + 0.1 * wA);
    let da = wA * (0.3 - 0.05 * wA);
    let ba = wA * 0.04;
    let ad = wD * 0.2;
    let dd = wD * (0.6 + 0.1 * wD);
    let bd = wD * 0.2;
    let ab = wB * 0.04;
    let db = wB * (0.3 - 0.05 * wB);
    let bb = wB * (0.6 + 0.1 * wB);

    const sum = aa + da + ba + ad + dd + bd + ab + db + bb || 1;
    const toPct = val => ((val / sum) * 100).toFixed(1) + "%";

    htftAA.textContent = toPct(aa);
    htftDA.textContent = toPct(da);
    htftBA.textContent = toPct(ba);
    htftAD.textContent = toPct(ad);
    htftDD.textContent = toPct(dd);
    htftBD.textContent = toPct(bd);
    htftAB.textContent = toPct(ab);
    htftDB.textContent = toPct(db);
    htftBB.textContent = toPct(bb);
  }

  // 5. Update Goal Bands
  if (data.scoreHeatmap) {
    const m = data.scoreHeatmap;
    let p0_1 = 0, p2_3 = 0, p4_5 = 0;
    for (let a = 0; a < 5; a++) {
      for (let b = 0; b < 5; b++) {
        const sum = a + b;
        const p = m[a][b];
        if (sum <= 1) p0_1 += p;
        else if (sum <= 3) p2_3 += p;
        else if (sum <= 5) p4_5 += p;
      }
    }
    const p6plus = Math.max(0, 1.0 - p0_1 - p2_3 - p4_5);

    const pct0_1 = (p0_1 * 100).toFixed(1) + "%";
    const pct2_3 = (p2_3 * 100).toFixed(1) + "%";
    const pct4_5 = (p4_5 * 100).toFixed(1) + "%";
    const pct6plus = (p6plus * 100).toFixed(1) + "%";

    const el0_1_pct = document.getElementById("bb-band-0-1-pct");
    const el0_1_bar = document.getElementById("bb-band-0-1-bar");
    if (el0_1_pct) el0_1_pct.textContent = pct0_1;
    if (el0_1_bar) el0_1_bar.style.width = pct0_1;

    const el2_3_pct = document.getElementById("bb-band-2-3-pct");
    const el2_3_bar = document.getElementById("bb-band-2-3-bar");
    if (el2_3_pct) el2_3_pct.textContent = pct2_3;
    if (el2_3_bar) el2_3_bar.style.width = pct2_3;

    const el4_5_pct = document.getElementById("bb-band-4-5-pct");
    const el4_5_bar = document.getElementById("bb-band-4-5-bar");
    if (el4_5_pct) el4_5_pct.textContent = pct4_5;
    if (el4_5_bar) el4_5_bar.style.width = pct4_5;

    const el6_pct = document.getElementById("bb-band-6-pct");
    const el6_bar = document.getElementById("bb-band-6-bar");
    if (el6_pct) el6_pct.textContent = pct6plus;
    if (el6_bar) el6_bar.style.width = pct6plus;
  }

  // 6. Render Timing Canvas
  const timingCanvas = document.getElementById("bb-timing-canvas");
  if (timingCanvas) {
    const existingTiming = Chart.getChart(timingCanvas);
    if (existingTiming) existingTiming.destroy();

    const isLight = document.body.classList.contains("light-theme");
    const textCol = isLight ? "rgba(15, 23, 42, 0.6)" : "rgba(255, 255, 255, 0.6)";
    const gridCol = isLight ? "rgba(15, 23, 42, 0.06)" : "rgba(255, 255, 255, 0.06)";

    const periods = ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90'];
    const defaultDistribution = [12, 15, 18, 16, 18, 21];

    new Chart(timingCanvas, {
      type: 'bar',
      data: {
        labels: periods.map(p => p + "'"),
        datasets: [{
          label: '% de goles',
          data: defaultDistribution,
          backgroundColor: 'rgba(240, 179, 16, 0.65)',
          borderColor: '#f0b310',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: textCol, font: { size: 9 } }, grid: { color: gridCol } },
          y: { ticks: { color: textCol, font: { size: 9 }, callback: v => v + '%' }, grid: { color: gridCol }, beginAtZero: true }
        }
      }
    });
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

    if (typeof window.runBetBuilderSimulation === 'function') {
      window.runBetBuilderSimulation();
    }
    if (typeof window.updateBetBuilderLabels === 'function') {
      window.updateBetBuilderLabels();
    }
    if (typeof updateBetBuilderAnalytics === 'function') {
      updateBetBuilderAnalytics(data);
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

function updateWeightsPreview() {
  renderWeightDonut();
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

// ── View Team Details Modal ──
window.viewTeamDetails = async function(teamKey) {
  const teamSlug = teamKey === 'A' ? selectedTeamA : selectedTeamB;
  const meta = TEAM_METADATA[teamSlug];
  if (!meta) return;
  const teamName = meta.name || teamSlug;
  const flag = meta.flag || '🏳️';
  const rank = meta.rank || '—';
  const elo = Math.round(ratingsData[teamSlug] || 1500);

  const uid = 'td' + Date.now();
  const overlay = document.createElement('div');
  overlay.className = 'td-overlay';
  overlay.innerHTML = `
    <div class="td-modal">
      <div class="td-header">
        <div class="td-h-left">
          <span class="td-flag">${flag}</span>
          <div class="td-name-group">
            <div class="td-name">${teamName}</div>
            <div class="td-badges">
              <span class="td-badge fifa">FIFA #${rank}</span>
              <span class="td-badge elo">ELO ${elo}</span>
            </div>
          </div>
        </div>
        <button class="td-close" onclick="this.closest('.td-overlay').remove()">✕</button>
      </div>
      <div class="td-tabs" id="${uid}-tabs"></div>
      <div class="td-body" id="${uid}-body"><div class="td-empty">Cargando estadísticas...</div></div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });

  const tabsEl = document.getElementById(`${uid}-tabs`);
  const bodyEl = document.getElementById(`${uid}-body`);
  if (!tabsEl || !bodyEl) return;

  try {
    const [historyRes, scorersRes] = await Promise.all([
      fetch(`/api/history/${teamSlug}`),
      fetch(`/data/team_scorers_processed.json`)
    ]);
    const histData = historyRes.ok ? await historyRes.json() : { history: [] };
    const allScorers = scorersRes.ok ? await scorersRes.json() : {};
    const teamScorers = (allScorers[teamSlug] || []).slice(0, 10);
    const matches = histData.history || [];
    const recent = matches.slice(0, 10);

    const wins = recent.filter(m => m.goalsScored > m.goalsConceded).length;
    const draws = recent.filter(m => m.goalsScored === m.goalsConceded).length;
    const losses = recent.filter(m => m.goalsScored < m.goalsConceded).length;
    const totalGf = recent.reduce((s, m) => s + m.goalsScored, 0);
    const totalGc = recent.reduce((s, m) => s + m.goalsConceded, 0);
    const avgGf = recent.length ? (totalGf / recent.length).toFixed(1) : '0.0';
    const avgGc = recent.length ? (totalGc / recent.length).toFixed(1) : '0.0';
    const cs = recent.filter(m => m.goalsConceded === 0).length;
    const btts = recent.filter(m => m.goalsScored > 0 && m.goalsConceded > 0).length;
    const over25 = recent.filter(m => (m.goalsScored + m.goalsConceded) > 2.5).length;

    const tabs = [
      { id: 'stats',    label: '📊 Stats' },
      { id: 'matches',  label: '⚽ Partidos' },
      { id: 'scorers',  label: '🥅 Goleadores' },
      { id: 'trend',    label: '📈 Tendencia' },
    ];
    let activeTab = 'stats';

    function switchTD(tabId) {
      activeTab = tabId;
      tabsEl.querySelectorAll('.td-tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
      bodyEl.querySelectorAll('.td-tab-content').forEach(c => c.classList.toggle('active', c.id === `${uid}-tc-${tabId}`));
      if (tabId === 'trend') renderTrendChart();
    }

    tabsEl.innerHTML = tabs.map(t =>
      `<button class="td-tab${t.id === activeTab ? ' active' : ''}" data-tab="${t.id}">${t.label}</button>`
    ).join('');

    tabsEl.addEventListener('click', e => {
      const btn = e.target.closest('.td-tab');
      if (!btn) return;
      const tabId = btn.dataset.tab;
      switchTD(tabId);
    });

    function statCard(val, label, colorClass) {
      return `<div class="td-stat-card"><div class="td-stat-val ${colorClass}">${val}</div><div class="td-stat-label">${label}</div></div>`;
    }
    function streakBadge(num, label, color) {
      return `<div style="flex:1;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:10px;text-align:center;min-width:80px"><div style="font-size:1.2rem;font-weight:800;color:${color}">${num}</div><div style="font-size:0.62rem;color:#64748B;text-transform:uppercase;font-weight:600;margin-top:2px">${label}</div></div>`;
    }

    const formBars = recent.map(m => {
      const cls = m.goalsScored > m.goalsConceded ? 'win' : m.goalsScored === m.goalsConceded ? 'draw' : 'loss';
      const lbl = cls === 'win' ? 'W' : cls === 'draw' ? 'D' : 'L';
      return `<div class="td-form-bar ${cls}" title="${m.opponentName || ''}">${lbl}</div>`;
    }).join('');

    let statsHtml = `<div class="td-tab-content active" id="${uid}-tc-stats">`;
    statsHtml += `<div class="td-section-title">📊 Estadísticas generales (últimos 10 PJ)</div>`;
    statsHtml += `<div class="td-stats-grid">`;
    statsHtml += statCard(`${wins}V / ${draws}E / ${losses}D`, 'Record', '');
    statsHtml += statCard(avgGf, 'Goles a favor', 'green');
    statsHtml += statCard(avgGc, 'Goles en contra', 'red');
    statsHtml += statCard(cs, 'Clean sheets', 'green');
    statsHtml += statCard(btts, 'BTTS', 'amber');
    statsHtml += statCard(over25, 'Over 2.5', 'blue');
    statsHtml += statCard(`${totalGf} - ${totalGc}`, 'Dif. de goles', wins >= draws ? 'green' : 'red');
    statsHtml += statCard(elo.toString(), 'Rating Elo', 'purple');
    statsHtml += `</div>`;
    statsHtml += `<div style="margin-top:16px"><div class="td-section-title">📈 Forma reciente</div><div class="td-form-wrap">`;
    statsHtml += `<div class="td-form-label"><span>${wins}V ${draws}E ${losses}D</span><span>${recent.length} partidos</span></div>`;
    statsHtml += `<div class="td-form-row">${formBars}</div></div></div></div>`;

    let matchHtml = `<div class="td-tab-content" id="${uid}-tc-matches">`;
    matchHtml += `<div class="td-section-title">⚽ Últimos ${recent.length} partidos</div>`;
    matchHtml += `<div class="td-match-list">`;
    if (!recent.length) {
      matchHtml += `<div class="td-empty">No hay partidos registrados</div>`;
    } else {
      for (const m of recent) {
        const cls = m.goalsScored > m.goalsConceded ? 'win' : m.goalsScored === m.goalsConceded ? 'draw' : 'loss';
        const opp = m.opponentName || m.opponentSlug || '—';
        const tourn = m.opponentLevel ? `<span class="td-m-tourn">${m.opponentLevel}</span>` : '';
        matchHtml += `<div class="td-match-row"><span class="td-m-date">${m.date || '—'}</span><span class="td-m-opp">vs ${opp}</span>${tourn}<span class="td-m-score ${cls}">${m.goalsScored}-${m.goalsConceded}</span></div>`;
      }
    }
    matchHtml += `</div></div>`;

    let scorersHtml = `<div class="td-tab-content" id="${uid}-tc-scorers">`;
    scorersHtml += `<div class="td-section-title">🥅 Goleadores históricos</div>`;
    scorersHtml += `<div class="td-scorers-grid">`;
    if (!teamScorers.length) {
      scorersHtml += `<div class="td-empty" style="grid-column:1/-1">Sin datos de goleadores</div>`;
    } else {
      const maxGoals = Math.max(...teamScorers.map(s => s.goals), 1);
      const rankLabels = ['top1', 'top2', 'top3', '', '', '', '', '', '', ''];
      teamScorers.forEach((s, i) => {
        const dot = s.active ? `<span class="td-scorer-dot active" title="Activo"></span>` : `<span class="td-scorer-dot retired" title="Retirado"></span>`;
        const barW = Math.round(s.goals / maxGoals * 100);
        scorersHtml += `<div class="td-scorer"><span class="td-scorer-rank ${rankLabels[i] || ''}">#${i+1}</span><div class="td-scorer-info"><div class="td-scorer-name">${s.name} ${dot}</div><div class="td-scorer-bar-wrap"><div class="td-scorer-bar-fill" style="width:${barW}%"></div></div></div><span class="td-scorer-goals">${s.goals}</span></div>`;
      });
    }
    scorersHtml += `</div></div>`;

    let trendHtml = `<div class="td-tab-content" id="${uid}-tc-trend">`;
    trendHtml += `<div class="td-section-title">📈 Evolución de goles (últimos partidos)</div>`;
    trendHtml += `<div class="td-trend-canvas-wrap"><canvas id="${uid}-trend-canvas"></canvas></div>`;
    if (recent.length) {
      trendHtml += `<div style="margin-top:14px;display:flex;gap:12px;flex-wrap:wrap">`;
      trendHtml += streakBadge(wins + draws, 'Sin perder', wins + draws >= 3 ? '#10B981' : '#64748B');
      trendHtml += streakBadge(losses, 'Derrotas consec.', losses >= 2 ? '#EF4444' : '#64748B');
      trendHtml += streakBadge(recent.filter(m => m.goalsScored > 0).length, 'Anotando', '#F59E0B');
      trendHtml += streakBadge(cs, 'Portería a 0', '#60A5FA');
      trendHtml += `</div>`;
    }
    trendHtml += `</div>`;

    bodyEl.innerHTML = statsHtml + matchHtml + scorersHtml + trendHtml;

    let trendChartInstance = null;
    function renderTrendChart() {
      const canvas = document.getElementById(`${uid}-trend-canvas`);
      if (!canvas || !recent.length) return;
      if (trendChartInstance) { trendChartInstance.destroy(); trendChartInstance = null; }
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const labels = recent.map((_, i) => `#${recent.length - i}`).reverse();
      const gf = recent.map(m => m.goalsScored);
      const gc = recent.map(m => m.goalsConceded);
      const isDark = !document.body.classList.contains('light-theme');
      trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            { label: 'Goles a favor', data: gf, borderColor: '#10B981', backgroundColor: 'rgba(16,185,129,0.08)', borderWidth: 2, pointRadius: 3, pointBackgroundColor: '#10B981', fill: true, tension: 0.3 },
            { label: 'Goles en contra', data: gc, borderColor: '#EF4444', backgroundColor: 'rgba(239,68,68,0.08)', borderWidth: 2, pointRadius: 3, pointBackgroundColor: '#EF4444', fill: true, tension: 0.3 },
          ]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: isDark ? '#94A3B8' : '#475569', font: { size: 10 }, boxWidth: 12, padding: 8 } },
            tooltip: { backgroundColor: isDark ? '#1E293B' : '#F8FAFC', titleColor: isDark ? '#F8FAFC' : '#0F172A', bodyColor: isDark ? '#CBD5E1' : '#334155', borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', borderWidth: 1 }
          },
          scales: {
            x: { ticks: { color: isDark ? '#64748B' : '#64748B', font: { size: 9 } }, grid: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' } },
            y: { ticks: { color: isDark ? '#64748B' : '#64748B', font: { size: 9 }, stepSize: 1 }, grid: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }, beginAtZero: true }
          }
        }
      });
    }
  } catch(e) {
    bodyEl.innerHTML = '<div class="td-empty">Error al cargar estadísticas</div>';
  }
};

// ── Comparar Equipos Modal ──
window.compareTeams = async function() {
  if (!selectedTeamA || !selectedTeamB) return;
  const metaA = TEAM_METADATA[selectedTeamA] || { name: selectedTeamA, flag: '🏳️', rank: '—' };
  const metaB = TEAM_METADATA[selectedTeamB] || { name: selectedTeamB, flag: '🏳️', rank: '—' };
  const eloA = Math.round(ratingsData[selectedTeamA] || 1500);
  const eloB = Math.round(ratingsData[selectedTeamB] || 1500);

  const uid = 'cmp' + Date.now();
  const overlay = document.createElement('div');
  overlay.className = 'cmp-overlay';
  overlay.innerHTML = `
    <div class="cmp-modal">
      <div class="cmp-header">
        <div class="cmp-h-left">
          <span class="cmp-flag">${metaA.flag}</span>
          <span class="cmp-vs">vs</span>
          <span class="cmp-flag">${metaB.flag}</span>
          <div class="cmp-name-group">
            <div class="cmp-name">${metaA.name}</div>
            <div class="cmp-name-sep">—</div>
            <div class="cmp-name">${metaB.name}</div>
          </div>
        </div>
        <button class="cmp-close" onclick="this.closest('.cmp-overlay').remove()">✕</button>
      </div>
      <div class="cmp-body" id="${uid}-body"><div class="cmp-loading">Cargando comparación...</div></div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  const bodyEl = document.getElementById(`${uid}-body`);

  try {
    const [advRes, histARes, histBRes] = await Promise.all([
      fetch(`/api/history/advanced/${selectedTeamA}/${selectedTeamB}`),
      fetch(`/api/history/${selectedTeamA}`),
      fetch(`/api/history/${selectedTeamB}`)
    ]);
    const adv = advRes.ok ? await advRes.json() : null;
    const histA = histARes.ok ? await histARes.json() : { history: [] };
    const histB = histBRes.ok ? await histBRes.json() : { history: [] };

    const matchesA = (histA.history || []).slice(0, 10);
    const matchesB = (histB.history || []).slice(0, 10);

    function calcStats(matches) {
      const n = matches.length;
      const wins = matches.filter(m => m.goalsScored > m.goalsConceded).length;
      const draws = matches.filter(m => m.goalsScored === m.goalsConceded).length;
      const losses = matches.filter(m => m.goalsScored < m.goalsConceded).length;
      const gf = matches.reduce((s, m) => s + m.goalsScored, 0);
      const gc = matches.reduce((s, m) => s + m.goalsConceded, 0);
      return { n, wins, draws, losses, gf, gc,
        avgGf: n ? (gf / n).toFixed(1) : '0.0',
        avgGc: n ? (gc / n).toFixed(1) : '0.0',
        cs: n ? matches.filter(m => m.goalsConceded === 0).length : 0,
        csPct: n ? Math.round(matches.filter(m => m.goalsConceded === 0).length / n * 100) : 0,
        btts: n ? matches.filter(m => m.goalsScored > 0 && m.goalsConceded > 0).length : 0,
        bttsPct: n ? Math.round(matches.filter(m => m.goalsScored > 0 && m.goalsConceded > 0).length / n * 100) : 0,
        over25: n ? matches.filter(m => (m.goalsScored + m.goalsConceded) > 2.5).length : 0,
        over25Pct: n ? Math.round(matches.filter(m => (m.goalsScored + m.goalsConceded) > 2.5).length / n * 100) : 0,
      };
    }
    const sA = calcStats(matchesA);
    const sB = calcStats(matchesB);

    const h2h = adv?.h2h || { winsA: 0, winsB: 0, draws: 0, count: 0, avgGoals: 0, goalsA: 0, goalsB: 0 };
    const formA = adv?.form?.teamA || { avg_gf: '—', avg_gc: '—', clean_sheets: '—', btts: '—', over25: '—', record: '—', streaks: {}, by_rival: {} };
    const formB = adv?.form?.teamB || { avg_gf: '—', avg_gc: '—', clean_sheets: '—', btts: '—', over25: '—', record: '—', streaks: {}, by_rival: {} };

    const advantages = [];
    if (parseFloat(sA.avgGc) < parseFloat(sB.avgGc)) advantages.push(`${metaA.name}: Mejor defensa (${sA.avgGc} goles/partido)`);
    else if (parseFloat(sB.avgGc) < parseFloat(sA.avgGc)) advantages.push(`${metaB.name}: Mejor defensa (${sB.avgGc} goles/partido)`);
    if (parseFloat(sA.avgGf) > parseFloat(sB.avgGf)) advantages.push(`${metaA.name}: Mejor ataque (${sA.avgGf} goles/partido)`);
    else if (parseFloat(sB.avgGf) > parseFloat(sA.avgGf)) advantages.push(`${metaB.name}: Mejor ataque (${sB.avgGf} goles/partido)`);
    if (sA.wins > sB.wins) advantages.push(`${metaA.name}: Más victorias recientes (${sA.wins}/${sA.n})`);
    else if (sB.wins > sA.wins) advantages.push(`${metaB.name}: Más victorias recientes (${sB.wins}/${sB.n})`);
    if (sA.csPct > sB.csPct) advantages.push(`${metaA.name}: Mejor % portería a cero (${sA.csPct}%)`);
    else if (sB.csPct > sA.csPct) advantages.push(`${metaB.name}: Mejor % portería a cero (${sB.csPct}%)`);
    if (eloA > eloB) advantages.push(`${metaA.name}: Mejor rating Elo (${eloA})`);
    else if (eloB > eloA) advantages.push(`${metaB.name}: Mejor rating Elo (${eloB})`);
    if (h2h.count > 0) {
      if (h2h.winsA > h2h.winsB) advantages.push(`${metaA.name}: Domina el H2H (${h2h.winsA}V ${h2h.draws}E ${h2h.winsB}D)`);
      else if (h2h.winsB > h2h.winsA) advantages.push(`${metaB.name}: Domina el H2H (${h2h.winsB}V ${h2h.draws}E ${h2h.winsA}D)`);
    }

    function better(a, b, higher) {
      if (a === b) return ['', ''];
      if (higher) return a > b ? ['cmp-cell-better', 'cmp-cell-worse'] : ['cmp-cell-worse', 'cmp-cell-better'];
      return a < b ? ['cmp-cell-better', 'cmp-cell-worse'] : ['cmp-cell-worse', 'cmp-cell-better'];
    }
    const aCls = (vA, vB, higher) => better(vA, vB, higher)[0];
    const bCls = (vA, vB, higher) => better(vA, vB, higher)[1];

    function insightLine(teamName, formData) {
      const parts = [];
      if (formData.clean_sheets !== '—') parts.push(`Portería a cero: ${formData.clean_sheets}%`);
      if (formData.btts !== '—') parts.push(`BTTS: ${formData.btts}%`);
      if (formData.over25 !== '—') parts.push(`Over 2.5: ${formData.over25}%`);
      if (formData.avg_gf !== '—') parts.push(`G/P: ${formData.avg_gf}`);
      const streak = formData.streaks || {};
      if (streak.unbeaten > 1) parts.push(`Racha sin perder: ${streak.unbeaten}`);
      return parts.join(' | ');
    }

    bodyEl.innerHTML = `
      <div class="cmp-grid">
        <div class="cmp-section">
          <div class="cmp-section-title">🏆 Ranking y Elo</div>
          <div class="cmp-compact-table">
            <div class="cmp-row">
              <span class="cmp-label">Ranking FIFA</span>
              <span class="cmp-val ${aCls(metaA.rank, metaB.rank, false)}">#${metaA.rank}</span>
              <span class="cmp-val ${bCls(metaA.rank, metaB.rank, false)}">#${metaB.rank}</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">Rating Elo</span>
              <span class="cmp-val ${aCls(eloA, eloB, true)}">${eloA}</span>
              <span class="cmp-val ${bCls(eloA, eloB, true)}">${eloB}</span>
            </div>
          </div>
        </div>

        <div class="cmp-section">
          <div class="cmp-section-title">⚡ Forma reciente (últimos ${sA.n} PJ)</div>
          <div class="cmp-compact-table">
            <div class="cmp-row">
              <span class="cmp-label">Record</span>
              <span class="cmp-val">${sA.wins}V / ${sA.draws}E / ${sA.losses}D</span>
              <span class="cmp-val">${sB.wins}V / ${sB.draws}E / ${sB.losses}D</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">Goles a favor (prom.)</span>
              <span class="cmp-val ${aCls(sA.avgGf, sB.avgGf, true)}">${sA.avgGf}</span>
              <span class="cmp-val ${bCls(sA.avgGf, sB.avgGf, true)}">${sB.avgGf}</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">Goles en contra (prom.)</span>
              <span class="cmp-val ${aCls(sA.avgGc, sB.avgGc, false)}">${sA.avgGc}</span>
              <span class="cmp-val ${bCls(sA.avgGc, sB.avgGc, false)}">${sB.avgGc}</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">Clean sheets</span>
              <span class="cmp-val ${aCls(sA.csPct, sB.csPct, true)}">${sA.csPct}%</span>
              <span class="cmp-val ${bCls(sA.csPct, sB.csPct, true)}">${sB.csPct}%</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">BTTS</span>
              <span class="cmp-val ${aCls(sA.bttsPct, sB.bttsPct, true)}">${sA.bttsPct}%</span>
              <span class="cmp-val ${bCls(sA.bttsPct, sB.bttsPct, true)}">${sB.bttsPct}%</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">Over 2.5</span>
              <span class="cmp-val ${aCls(sA.over25Pct, sB.over25Pct, true)}">${sA.over25Pct}%</span>
              <span class="cmp-val ${bCls(sA.over25Pct, sB.over25Pct, true)}">${sB.over25Pct}%</span>
            </div>
          </div>
        </div>

        <div class="cmp-section">
          <div class="cmp-section-title">🤝 Historial (H2H)</div>
          ${h2h.count > 0 ? `
          <div class="cmp-h2h-bar-wrap">
            <div class="cmp-h2h-bar">
              <div class="cmp-h2h-bar-a" style="width:${Math.round(h2h.winsA/h2h.count*100)}%"></div>
              <div class="cmp-h2h-bar-draw" style="width:${Math.round(h2h.draws/h2h.count*100)}%"></div>
              <div class="cmp-h2h-bar-b" style="width:${Math.round(h2h.winsB/h2h.count*100)}%"></div>
            </div>
          </div>
          <div class="cmp-compact-table" style="margin-top:8px">
            <div class="cmp-row"><span class="cmp-label">Partidos</span><span class="cmp-val" style="grid-column:span 2">${h2h.count}</span></div>
            <div class="cmp-row">
              <span class="cmp-label">Victorias</span>
              <span class="cmp-val cmp-cell-better">${metaA.name.slice(0,10)}: ${h2h.winsA}</span>
              <span class="cmp-val ${h2h.winsB > h2h.winsA ? 'cmp-cell-better' : ''}">${metaB.name.slice(0,10)}: ${h2h.winsB}</span>
            </div>
            <div class="cmp-row"><span class="cmp-label">Empates</span><span class="cmp-val" style="grid-column:span 2">${h2h.draws}</span></div>
            <div class="cmp-row"><span class="cmp-label">Goles/Partido</span><span class="cmp-val" style="grid-column:span 2">${h2h.avgGoals.toFixed(1)}</span></div>
          </div>
          ` : `<div class="cmp-empty">Sin enfrentamientos directos registrados</div>`}
        </div>

        <div class="cmp-full-width">
          <div class="cmp-section-title">🔑 Ventajas clave</div>
          <div class="cmp-adv-grid">
            ${advantages.length ? advantages.map(a => `<div class="cmp-adv-chip">${a}</div>`).join('') : '<div class="cmp-empty">Datos insuficientes para determinar ventajas</div>'}
          </div>
        </div>

        <div class="cmp-full-width">
          <div class="cmp-section-title">📊 Rendimiento por nivel de rival</div>
          <div class="cmp-compact-table">
            <div class="cmp-row cmp-row-header">
              <span class="cmp-label">Nivel</span>
              <span class="cmp-val">${metaA.name.slice(0,10)}</span>
              <span class="cmp-val">${metaB.name.slice(0,10)}</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">🔴 Top</span>
              <span class="cmp-val">${formA.by_rival?.top || '—'}</span>
              <span class="cmp-val">${formB.by_rival?.top || '—'}</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">🟡 Alto</span>
              <span class="cmp-val">${formA.by_rival?.high || '—'}</span>
              <span class="cmp-val">${formB.by_rival?.high || '—'}</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">🟢 Medio</span>
              <span class="cmp-val">${formA.by_rival?.mid || '—'}</span>
              <span class="cmp-val">${formB.by_rival?.mid || '—'}</span>
            </div>
            <div class="cmp-row">
              <span class="cmp-label">⚪ Bajo</span>
              <span class="cmp-val">${formA.by_rival?.low || '—'}</span>
              <span class="cmp-val">${formB.by_rival?.low || '—'}</span>
            </div>
          </div>
        </div>

        <div class="cmp-full-width">
          <div class="cmp-section-title">💡 Insights</div>
          <div class="cmp-insights-grid">
            <div class="cmp-insight-card">
              <div class="cmp-insight-flag">${metaA.flag}</div>
              <div class="cmp-insight-name">${metaA.name}</div>
              <div class="cmp-insight-text">${insightLine(metaA.name, formA)}</div>
            </div>
            <div class="cmp-insight-card">
              <div class="cmp-insight-flag">${metaB.flag}</div>
              <div class="cmp-insight-name">${metaB.name}</div>
              <div class="cmp-insight-text">${insightLine(metaB.name, formB)}</div>
            </div>
          </div>
        </div>
      </div>
    `;
  } catch(e) {
    bodyEl.innerHTML = '<div class="cmp-empty">Error al cargar datos de comparación</div>';
  }
};

// ═══ BET BUILDER FUNCTIONS ═══

// ── Donut chart de ponderación ──
function renderWeightDonut() {
  const canvas = document.getElementById('bb-donut-canvas');
  if (!canvas) return;

  // Destroy existing chart on this canvas to prevent overlap/flicker
  const existingChart = Chart.getChart(canvas);
  if (existingChart) {
    existingChart.destroy();
  }

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const wFifa = parseFloat(document.getElementById('input-weight-fifa')?.value) || 0;
  const wH2h = parseFloat(document.getElementById('input-weight-h2h')?.value) || 0;
  const total = wFifa + wH2h;
  let fifaW, h2hW, formW;
  if (total > 100) {
    fifaW = Math.round((wFifa / total) * 100);
    h2hW = Math.round((wH2h / total) * 100);
    formW = 0;
  } else {
    fifaW = wFifa;
    h2hW = wH2h;
    formW = 100 - fifaW - h2hW;
  }

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['FIFA', 'H2H', 'Forma'],
      datasets: [{
        data: [fifaW, h2hW, formW],
        backgroundColor: ['#F59E0B', '#EF4444', '#10B981'],
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '70%',
      layout: {
        padding: 5
      },
      legend: {
        display: false
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(15, 22, 42, 0.9)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 4,
          caretSize: 4,
          bodyFont: { size: 9 },
          titleFont: { size: 9 },
          callbacks: {
            label: function(context) {
              return ` ${context.label}: ${context.raw}%`;
            }
          }
        }
      }
    }
  });
}

// ── Toggle accordion ──
window.toggleBBAccordion = function(btn) {
  const item = btn.closest('.bb-accordion-item');
  if (!item) return;
  const content = item.querySelector('.bb-accordion-content');
  const arrow = btn.querySelector('.bb-accordion-arrow');
  if (!content || !arrow) return;
  const isExpanded = item.classList.toggle('expanded');
  if (isExpanded) {
    content.style.display = 'flex';
    const cat = item.dataset.category;
    if (cat === 'goals') content.style.display = 'grid';
  } else {
    content.style.display = 'none';
  }
  arrow.textContent = isExpanded ? '▼' : '▶';
};

// ── Clear all bet builder legs ──
window.clearAllBBLegs = function() {
  document.querySelectorAll('input[name="bb-leg"]').forEach(cb => cb.checked = false);
  updateBBLegsCount();
  window.runBetBuilderSimulation();
};

// ── Toggle alerts config fields ──
window.toggleAlertsState = function() {
  const cb = document.getElementById('alert-enable');
  const fields = document.getElementById('alerts-config-fields');
  if (fields) fields.style.display = cb?.checked ? 'flex' : 'none';
};

// ── Update legs counter ──
function updateBBLegsCount() {
  const count = document.querySelectorAll('input[name="bb-leg"]:checked').length;
  const el = document.getElementById('bb-selected-count');
  if (el) el.textContent = `(${count})`;
}

// ── Filter markets by search ──
window.filterBBMarkets = function() {
  const q = (document.getElementById('bb-market-search')?.value || '').toLowerCase().trim();
  document.querySelectorAll('.bb-accordion-item').forEach(item => {
    const text = item.textContent.toLowerCase();
    item.style.display = (!q || text.includes(q)) ? '' : 'none';
  });
};

// ── Switch bet builder segment (summary/goals/markets/validation) ──
window.switchBBSegment = function(name) {
  document.querySelectorAll('.bb-segment-btn').forEach(b => b.classList.toggle('active', b.dataset.segment === name));
  document.querySelectorAll('#bb-col-results [id^="bb-container-"]').forEach(el => {
    el.style.display = el.classList.contains(`bb-seg-${name}`) ? '' : 'none';
  });

  setTimeout(() => {
    const radarCv = document.getElementById("bb-radar-canvas");
    const timingCv = document.getElementById("bb-timing-canvas");
    if (radarCv) {
      const radar = Chart.getChart(radarCv);
      if (radar) radar.resize();
    }
    if (timingCv) {
      const timing = Chart.getChart(timingCv);
      if (timing) timing.resize();
    }
  }, 50);
};

// ── Switch mobile nav tab ──
window.switchBetBuilderTab = function(name) {
  document.querySelectorAll('.bb-mobile-nav-btn').forEach(b => b.classList.toggle('active', b.id === `bb-nav-btn-${name}`));
  const colMarkets = document.getElementById('bb-col-markets');
  const colResults = document.getElementById('bb-col-results');
  if (colMarkets) colMarkets.classList.toggle('bb-tab-hidden', name !== 'markets');
  if (colResults) colResults.classList.toggle('bb-tab-hidden', name !== 'summary');
  if (name === 'summary' && !window._bbSegInit) { window._bbSegInit = true; switchBBSegment('summary'); }

  setTimeout(() => {
    const radarCv = document.getElementById("bb-radar-canvas");
    const timingCv = document.getElementById("bb-timing-canvas");
    if (radarCv) {
      const radar = Chart.getChart(radarCv);
      if (radar) radar.resize();
    }
    if (timingCv) {
      const timing = Chart.getChart(timingCv);
      if (timing) timing.resize();
    }
  }, 50);
};

// ── Update edge calculation ──
window.updateBetBuilderEdge = function() {
  const combinedProbText = document.getElementById('bb-combined-prob-circle')?.textContent || '0.0%';
  const marketOdds = parseFloat(document.getElementById('bb-market-odds')?.value) || 0;
  const combinedProb = parseFloat(combinedProbText) / 100;
  if (!marketOdds || !combinedProb) {
    ['bb-edge-value', 'bb-kelly-stake', 'bb-risk-level'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = id === 'bb-risk-level' ? 'Bajo' : '0.0%';
    });
    const badge = document.getElementById('bb-value-badge');
    if (badge) badge.style.display = 'none';
    return;
  }
  const fairOdds = 1 / combinedProb;
  const edge = (marketOdds - fairOdds) / fairOdds * 100;
  const kelly = ((combinedProb * marketOdds - 1) / (marketOdds - 1)) * 100;
  const edgeEl = document.getElementById('bb-edge-value');
  const kellyEl = document.getElementById('bb-kelly-stake');
  const riskEl = document.getElementById('bb-risk-level');
  const badge = document.getElementById('bb-value-badge');
  if (edgeEl) edgeEl.textContent = edge.toFixed(1) + '%';
  if (kellyEl) kellyEl.textContent = Math.max(0, kelly).toFixed(1) + '%';
  if (riskEl) {
    const risk = Math.abs(kelly);
    riskEl.textContent = risk < 5 ? 'Bajo' : risk < 15 ? 'Medio' : 'Alto';
    riskEl.style.color = risk < 5 ? '#10B981' : risk < 15 ? '#F59E0B' : '#EF4444';
  }
  if (badge) {
    badge.style.display = edge > 0 ? 'block' : 'none';
    badge.textContent = edge > 0 ? '⚡ Value Bet Detectada' : '';
  }
};

// ── Update odds comparison table ──
window.updateOddsComparison = function() {
  const probText = document.getElementById('bb-combined-prob-circle')?.textContent || '0.0%';
  const prob = parseFloat(probText) / 100;
  const tbody = document.getElementById('odds-compare-tbody');
  if (!tbody) return;
  const entries = [];
  ['bet365', '1xbet', 'pinnacle', 'betfair'].forEach(id => {
    const input = document.getElementById('odds-' + id);
    if (!input) return;
    const odds = parseFloat(input.value);
    if (!odds || odds <= 0) return;
    const label = input.closest('label')?.childNodes[0]?.textContent || id;
    const fairOdds = prob > 0 ? 1 / prob : 0;
    const edge = fairOdds > 0 ? (odds - fairOdds) / fairOdds * 100 : 0;
    const ret = 100 * (odds - 1) * prob - 100 * (1 - prob);
    entries.push({ label, odds, edge, ret });
  });
  entries.sort((a, b) => b.edge - a.edge);
  if (entries.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:15px;color:var(--color-text-muted);">Ingresa una cuota arriba para comparar.</td></tr>';
    return;
  }
  tbody.innerHTML = entries.map(e => `<tr style="border-bottom:1px solid var(--panel-border);">
    <td style="padding:6px 2px;font-weight:600;">${e.label}</td>
    <td style="padding:6px 2px;text-align:center;font-family:monospace;">${e.odds.toFixed(2)}</td>
    <td style="padding:6px 2px;text-align:center;color:${e.edge > 0 ? '#10B981' : '#EF4444'};font-weight:600;">${e.edge > 0 ? '+' : ''}${e.edge.toFixed(1)}%</td>
    <td style="padding:6px 2px;text-align:right;font-family:monospace;color:${e.ret > 0 ? '#10B981' : '#EF4444'};">${e.ret > 0 ? '+' : ''}$${e.ret.toFixed(2)}</td>
  </tr>`).join('');
};

// ── Export bet builder as PDF ──
window.exportBetBuilderPDF = function() {
  window.print();
};

// ── Toggle inverse mode ──
window.toggleInverseMode = function() {
  const panel = document.getElementById('inverse-metrics-panel');
  if (!panel) return;
  const isVisible = panel.style.display !== 'none';
  panel.style.display = isVisible ? 'none' : 'flex';
};

// ── Populate Validation Tables ──
function populateValidationTables(matches, legs) {
  const h2hTbody = document.getElementById('bb-h2h-tbody');
  const similarTbody = document.getElementById('bb-similar-tbody');
  
  if (h2hTbody) {
    if (!matches || !matches.directH2H || matches.directH2H.length === 0) {
      h2hTbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 15px; color: var(--color-text-muted);">Sin partidos seleccionados o no hay historial.</td></tr>';
    } else {
      h2hTbody.innerHTML = matches.directH2H.map(m => {
        const combText = m.fullyMet ? '<span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10B981; padding: 2px 6px; border-radius: 4px; font-weight: bold;">Sí</span>' : '<span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #EF4444; padding: 2px 6px; border-radius: 4px; font-weight: bold;">No</span>';
        return `<tr style="border-bottom: 1px solid var(--panel-border);">
          <td style="padding: 8px 4px; color: var(--color-text-muted); font-family: monospace;">${m.date}</td>
          <td style="padding: 8px 4px; font-weight: 500;">${m.homeName} vs ${m.awayName}</td>
          <td style="padding: 8px 4px; text-align: center; font-family: monospace; font-weight: 700;">${m.score}</td>
          <td style="padding: 8px 4px; text-align: center;">${combText}</td>
        </tr>`;
      }).join('');
    }
  }

  if (similarTbody) {
    if (!matches || !matches.similarProfile || matches.similarProfile.length === 0) {
      similarTbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 15px; color: var(--color-text-muted);">Sin partidos seleccionados o no hay historial.</td></tr>';
    } else {
      similarTbody.innerHTML = matches.similarProfile.map(m => {
        const combText = m.fullyMet ? '<span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10B981; padding: 2px 6px; border-radius: 4px; font-weight: bold;">Sí</span>' : '<span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #EF4444; padding: 2px 6px; border-radius: 4px; font-weight: bold;">No</span>';
        return `<tr style="border-bottom: 1px solid var(--panel-border);">
          <td style="padding: 8px 4px; color: var(--color-text-muted); font-family: monospace;">${m.date}</td>
          <td style="padding: 8px 4px; font-weight: 500;">${m.homeName} vs ${m.awayName}</td>
          <td style="padding: 8px 4px; text-align: center; font-family: monospace; font-weight: 700;">${m.score}</td>
          <td style="padding: 8px 4px; text-align: center; font-family: monospace; font-weight: 600; color: var(--color-primary);">${m.similarity}%</td>
          <td style="padding: 8px 4px; text-align: center;">${combText}</td>
        </tr>`;
      }).join('');
    }
  }
}

// ── Run Bet Builder Simulation ──
window.runBetBuilderSimulation = async function() {
  const checkedLegs = Array.from(document.querySelectorAll('input[name="bb-leg"]:checked')).map(cb => cb.value);
  const probCircle = document.getElementById('bb-combined-prob-circle');
  const fairOddsEl = document.getElementById('bb-fair-odds');
  
  if (checkedLegs.length === 0) {
    if (probCircle) probCircle.textContent = '0.0%';
    if (fairOddsEl) fairOddsEl.textContent = '1.00';
    window.updateBetBuilderEdge();
    window.updateOddsComparison();
    populateValidationTables({ directH2H: [], similarProfile: [] }, []);
    return;
  }
  
  if (probCircle) probCircle.textContent = 'Simulando...';
  
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
    legs: checkedLegs
  };

  try {
    const res = await fetch("/api/betbuilder/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Simulation failed");
    const data = await res.json();
    
    const prob = (data.simulation.combinedProb * 100).toFixed(1);
    if (probCircle) probCircle.textContent = `${prob}%`;
    
    const fairOdds = 1 / data.simulation.combinedProb;
    if (fairOddsEl) fairOddsEl.textContent = isFinite(fairOdds) ? fairOdds.toFixed(2) : '99.00';
    
    window.updateBetBuilderEdge();
    window.updateOddsComparison();
    populateValidationTables(data.historicalMatches, checkedLegs);
  } catch (e) {
    console.error("Bet Builder simulation error:", e);
    if (probCircle) probCircle.textContent = 'Error';
  }
};

// ── Update Bet Builder Labels ──
window.updateBetBuilderLabels = function() {
  const metaA = TEAM_METADATA[selectedTeamA] || { name: "Local" };
  const metaB = TEAM_METADATA[selectedTeamB] || { name: "Visitante" };
  
  document.querySelectorAll('.bb-lbl-a').forEach(el => el.textContent = `Victoria ${metaA.name}`);
  document.querySelectorAll('.bb-lbl-b').forEach(el => el.textContent = `Victoria ${metaB.name}`);
  
  const cbCornersA = document.querySelector('input[value="corners_win_a"]');
  if (cbCornersA && cbCornersA.nextSibling) {
    cbCornersA.nextSibling.textContent = ` Más Córners ${metaA.name}`;
  }
  const cbCornersB = document.querySelector('input[value="corners_win_b"]');
  if (cbCornersB && cbCornersB.nextSibling) {
    cbCornersB.nextSibling.textContent = ` Más Córners ${metaB.name}`;
  }
  
  const cbHcA1 = document.querySelector('input[value="handicap_minus_1_5_a"]');
  if (cbHcA1 && cbHcA1.nextSibling) cbHcA1.nextSibling.textContent = ` ${metaA.name} Handicap -1.5`;
  const cbHcA2 = document.querySelector('input[value="handicap_plus_1_5_a"]');
  if (cbHcA2 && cbHcA2.nextSibling) cbHcA2.nextSibling.textContent = ` ${metaA.name} Handicap +1.5`;
  const cbHcB1 = document.querySelector('input[value="handicap_minus_1_5_b"]');
  if (cbHcB1 && cbHcB1.nextSibling) cbHcB1.nextSibling.textContent = ` ${metaB.name} Handicap -1.5`;
  const cbHcB2 = document.querySelector('input[value="handicap_plus_1_5_b"]');
  if (cbHcB2 && cbHcB2.nextSibling) cbHcB2.nextSibling.textContent = ` ${metaB.name} Handicap +1.5`;
};

// Init donut + sync range sliders with number inputs
(function initWeightsUI() {
  renderWeightDonut();
  [['fifa','input-weight-fifa','slider-weight-fifa'],['h2h','input-weight-h2h','slider-weight-h2h'],['decay','input-decay','slider-decay']].forEach(([,inputId,sliderId]) => {
    const input = document.getElementById(inputId);
    const slider = document.getElementById(sliderId);
    if (input && slider) {
      input.addEventListener('input', () => { slider.value = input.value; renderWeightDonut(); });
      slider.addEventListener('input', () => { input.value = slider.value; renderWeightDonut(); });
    }
  });
})();

// Wire up BB checkbox listener for leg count and trigger simulation
document.addEventListener('change', function bbCheckChange(e) {
  if (e.target && e.target.matches('input[name="bb-leg"]')) {
    updateBBLegsCount();
    window.runBetBuilderSimulation();
  }
});
