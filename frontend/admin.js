let adminPassword = sessionStorage.getItem("adminPassword") || "";
let savedAnalyses = [];
let adminUsers = [];

function showToast(message, type = "info") {
  const container = document.getElementById("admin-toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `admin-toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

function handleUnauthorized() {
  adminPassword = "";
  sessionStorage.removeItem("adminPassword");
  showToast("Sesión expirada. Vuelve a iniciar sesión.", "error");
  checkAIAdminStatus();
}

function updateAdminStats() {
  console.log("DEBUG: updateAdminStats called. adminUsers count:", adminUsers.length, "savedAnalyses count:", savedAnalyses.length);
  const usersEl = document.getElementById("stat-users-count");
  const premiumEl = document.getElementById("stat-premium-count");
  const analysesEl = document.getElementById("stat-analyses-count");
  const badgeEl = document.getElementById("analyses-count-badge");

  console.log("DEBUG: DOM Elements found: usersEl:", !!usersEl, "premiumEl:", !!premiumEl, "analysesEl:", !!analysesEl);

  if (usersEl) {
    usersEl.textContent = adminUsers.length;
    console.log("DEBUG: Set users count to", adminUsers.length);
  }
  if (premiumEl) {
    const premiumCount = adminUsers.filter(u => u.plan === "PREMIUM").length;
    premiumEl.textContent = premiumCount;
    console.log("DEBUG: Set premium count to", premiumCount);
  }
  if (analysesEl) {
    analysesEl.textContent = savedAnalyses.length;
    console.log("DEBUG: Set analyses count to", savedAnalyses.length);
  }
  if (badgeEl) {
    badgeEl.textContent = savedAnalyses.length ? `(${savedAnalyses.length})` : "";
  }
}
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

document.addEventListener("DOMContentLoaded", () => {
  populateAdminSelects();

  // Init listeners and check status
  initAIAdminListeners();
  checkAIAdminStatus();
});

function populateAdminSelects() {
  const slugs = Object.keys(TEAM_METADATA).sort((a, b) => 
    TEAM_METADATA[a].name.localeCompare(TEAM_METADATA[b].name)
  );

  const aiTeamA = document.getElementById("ai-team-a");
  const aiTeamB = document.getElementById("ai-team-b");

  if (!aiTeamA || !aiTeamB) return;

  slugs.forEach(slug => {
    const optAiA = document.createElement("option");
    optAiA.value = slug;
    optAiA.textContent = `${TEAM_METADATA[slug].flag} ${TEAM_METADATA[slug].name}`;
    aiTeamA.appendChild(optAiA);

    const optAiB = document.createElement("option");
    optAiB.value = slug;
    optAiB.textContent = `${TEAM_METADATA[slug].flag} ${TEAM_METADATA[slug].name}`;
    aiTeamB.appendChild(optAiB);
  });
}

function checkAIAdminStatus() {
  const loginPanel = document.getElementById("ai-crud-login-panel");
  const adminPanel = document.getElementById("ai-crud-admin-panel");
  if (!loginPanel || !adminPanel) return;
  
  if (adminPassword) {
    loginPanel.style.display = "none";
    adminPanel.style.display = "block";
    loadAIAnalyses();
    loadAdminUsers();
  } else {
    loginPanel.style.display = "block";
    adminPanel.style.display = "none";
  }
}

async function loadAIAnalyses() {
  const aiAnalysesList = document.getElementById("ai-analyses-list");
  if (!aiAnalysesList) return;
  
  aiAnalysesList.innerHTML = `<div class="loading-placeholder" style="color: var(--color-text-secondary); font-size: 0.85rem;">Cargando análisis...</div>`;
  try {
    const res = await fetch("/api/ai-analyses");
    const json = await res.json();
    console.log("DEBUG: loadAIAnalyses success. Analyses received:", json.analyses ? json.analyses.length : 0);
    savedAnalyses = json.analyses || [];
    renderAIAnalysesList();
    updateAdminStats();
  } catch (error) {
    console.error("Error loading analyses:", error);
    aiAnalysesList.innerHTML = `<div class="loading-placeholder" style="color: #ef4444; font-size: 0.85rem;">Error al cargar la lista.</div>`;
  }
}

function renderAIAnalysesList() {
  const aiAnalysesList = document.getElementById("ai-analyses-list");
  const aiSearchInput = document.getElementById("ai-search-input");
  if (!aiAnalysesList) return;
  
  aiAnalysesList.innerHTML = "";
  const query = aiSearchInput ? aiSearchInput.value.toLowerCase().trim() : "";
  
  const filtered = savedAnalyses.filter(item => {
    const nameA = (TEAM_METADATA[item.teamA]?.name || item.teamA).toLowerCase();
    const nameB = (TEAM_METADATA[item.teamB]?.name || item.teamB).toLowerCase();
    return nameA.includes(query) || nameB.includes(query);
  });
  
  if (filtered.length === 0) {
    aiAnalysesList.innerHTML = `<div class="loading-placeholder" style="color: var(--color-text-secondary); font-size: 0.85rem;">No se encontraron análisis guardados.</div>`;
    return;
  }
  
  filtered.forEach(item => {
    const metaA = TEAM_METADATA[item.teamA] || { name: item.teamA.toUpperCase(), flag: "🏳️" };
    const metaB = TEAM_METADATA[item.teamB] || { name: item.teamB.toUpperCase(), flag: "🏳️" };
    
    const card = document.createElement("div");
    card.className = "glass-card";
    card.style.padding = "12px 16px";
    card.style.marginBottom = "8px";
    card.style.display = "flex";
    card.style.justifyContent = "space-between";
    card.style.alignItems = "center";
    card.style.flexWrap = "wrap";
    card.style.gap = "8px";
    
    card.innerHTML = `
      <div>
        <div style="font-size: 0.7rem; color: var(--color-text-secondary); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">${item.stage || "Fase de Grupos"} · Confianza: <strong style="color: var(--color-primary);">${item.confidence}%</strong>${item.predicted_score ? ` · ${item.predicted_score}` : ""}</div>
        <div style="font-weight: 600; font-size: 0.95rem;">${metaA.flag} ${metaA.name} vs ${metaB.flag} ${metaB.name}</div>
        ${item.model_name ? `<div style="font-size: 0.72rem; color: var(--color-text-secondary); margin-top: 4px;">${item.model_name}</div>` : ""}
      </div>
      <div style="display: flex; gap: 6px;">
        <button class="btn btn-secondary btn-edit-ai" data-id="${item.id}" style="padding: 4px 10px; font-size: 0.75rem; background: rgba(240,179,16,0.15); border-color: rgba(240,179,16,0.2); color: var(--color-primary); cursor: pointer; height: auto;">Editar</button>
        <button class="btn btn-secondary btn-delete-ai" data-id="${item.id}" style="padding: 4px 10px; font-size: 0.75rem; background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.2); color: #ef4444; cursor: pointer; height: auto;">Borrar</button>
      </div>
    `;
    aiAnalysesList.appendChild(card);
  });
}

function clearAIForm() {
  const aiIdField = document.getElementById("ai-id-field");
  const aiConfidence = document.getElementById("ai-confidence");
  const aiStage = document.getElementById("ai-stage");
  const aiKeyTips = document.getElementById("ai-key-tips");
  const aiText = document.getElementById("ai-text");
  const aiTeamA = document.getElementById("ai-team-a");
  const aiTeamB = document.getElementById("ai-team-b");
  const aiPredictedScore = document.getElementById("ai-predicted-score");
  const aiModelName = document.getElementById("ai-model-name");
  
  if (aiIdField) aiIdField.value = "";
  if (aiConfidence) aiConfidence.value = "80";
  if (aiStage) aiStage.value = "Fase de Grupos";
  if (aiKeyTips) aiKeyTips.value = "";
  if (aiText) aiText.value = "";
  if (aiPredictedScore) aiPredictedScore.value = "";
  if (aiModelName) aiModelName.value = "Manual";
  
  // Clear all odds fields starting with ai-odds-
  document.querySelectorAll('input[id^="ai-odds-"]').forEach(input => {
    input.value = "";
  });
  
  const formTitle = document.getElementById("crud-form-title");
  if (formTitle) formTitle.textContent = "Guardar Análisis de IA";
  
  if (aiTeamA) aiTeamA.value = "";
  if (aiTeamB) aiTeamB.value = "";
}

function initAIAdminListeners() {
  const aiLoginForm = document.getElementById("ai-login-form");
  const btnAiLogout = document.getElementById("btn-ai-logout");
  const aiAnalysisForm = document.getElementById("ai-analysis-form");
  const btnAiClear = document.getElementById("btn-ai-clear");
  const aiSearchInput = document.getElementById("ai-search-input");
  const aiAnalysesList = document.getElementById("ai-analyses-list");
  
  if (aiLoginForm) {
    aiLoginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const pwdInput = document.getElementById("ai-login-password");
      const errDiv = document.getElementById("ai-login-error");
      if (!pwdInput || !errDiv) return;
      
      errDiv.style.display = "none";
      const pwd = pwdInput.value;
      
      try {
        const res = await fetch("/api/ai-auth/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: pwd })
        });
        const json = await res.json();
        if (res.ok && json.status === "success") {
          adminPassword = pwd;
          sessionStorage.setItem("adminPassword", pwd);
          pwdInput.value = "";
          showToast("Acceso concedido.", "success");
          checkAIAdminStatus();
        } else {
          errDiv.textContent = json.detail || "Contraseña incorrecta";
          errDiv.style.display = "block";
        }
      } catch (err) {
        console.error("Auth error:", err);
        errDiv.textContent = "Error de red al verificar contraseña";
        errDiv.style.display = "block";
      }
    });
  }
  
  if (btnAiLogout) {
    btnAiLogout.addEventListener("click", () => {
      adminPassword = "";
      sessionStorage.removeItem("adminPassword");
      showToast("Sesión cerrada.", "info");
      checkAIAdminStatus();
    });
  }

  const btnRefreshUsers = document.getElementById("btn-refresh-users");
  if (btnRefreshUsers) {
    btnRefreshUsers.addEventListener("click", () => loadAdminUsers());
  }

  const btnRefreshAnalyses = document.getElementById("btn-refresh-analyses");
  if (btnRefreshAnalyses) {
    btnRefreshAnalyses.addEventListener("click", () => loadAIAnalyses());
  }

  const btnAdminExit = document.getElementById("btn-admin-exit");
  if (btnAdminExit) {
    btnAdminExit.addEventListener("click", (e) => {
      e.preventDefault();
      window.location.href = "/";
    });
  }
  
  if (btnAiClear) {
    btnAiClear.addEventListener("click", clearAIForm);
  }
  
  if (aiSearchInput) {
    aiSearchInput.addEventListener("input", renderAIAnalysesList);
  }
  
  if (aiAnalysisForm) {
    aiAnalysisForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      const aiIdField = document.getElementById("ai-id-field");
      const aiTeamA = document.getElementById("ai-team-a");
      const aiTeamB = document.getElementById("ai-team-b");
      const aiConfidence = document.getElementById("ai-confidence");
      const aiStage = document.getElementById("ai-stage");
      const aiKeyTips = document.getElementById("ai-key-tips");
      const aiText = document.getElementById("ai-text");
      const aiPredictedScore = document.getElementById("ai-predicted-score");
      const aiModelName = document.getElementById("ai-model-name");
      
      const tipsArr = aiKeyTips.value.split(",")
        .map(t => t.trim())
        .filter(t => t.length > 0);
        
      // Build the odds dictionary dynamically
      const oddsDict = {};
      document.querySelectorAll('input[id^="ai-odds-"]').forEach(input => {
        const originalId = input.id.replace("ai-odds-", "");
        oddsDict[originalId] = input.value ? parseFloat(input.value) : null;
      });
      
      const payload = {
        id: aiIdField.value ? parseInt(aiIdField.value) : null,
        teamA: aiTeamA.value,
        teamB: aiTeamB.value,
        analysisText: aiText.value,
        keyTips: tipsArr,
        confidence: parseInt(aiConfidence.value),
        predictedScore: aiPredictedScore?.value?.trim() || "—",
        modelName: aiModelName?.value?.trim() || "Manual",
        stage: aiStage.value,
        keyPlayers: "",
        oddsA: oddsDict["input-odds-a"] || null,
        oddsDraw: oddsDict["input-odds-draw"] || null,
        oddsB: oddsDict["input-odds-b"] || null,
        odds: oddsDict
      };
      
      try {
        const res = await fetch("/api/ai-analyses", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Admin-Password": adminPassword
          },
          body: JSON.stringify(payload)
        });
        
        if (res.status === 401) {
          handleUnauthorized();
          return;
        }
        
        const json = await res.json();
        if (res.ok && json.status === "success") {
          showToast(aiIdField.value ? "Análisis actualizado." : "Análisis guardado.", "success");
          clearAIForm();
          loadAIAnalyses();
        } else {
          showToast("Error al guardar: " + (json.detail || "Error desconocido"), "error");
        }
      } catch (err) {
        console.error("Save analysis error:", err);
        showToast("Error de red al guardar análisis.", "error");
      }
    });
  }
  
  if (aiAnalysesList) {
    aiAnalysesList.addEventListener("click", async (e) => {
      const editBtn = e.target.closest(".btn-edit-ai");
      const deleteBtn = e.target.closest(".btn-delete-ai");
      
      const aiIdField = document.getElementById("ai-id-field");
      const aiTeamA = document.getElementById("ai-team-a");
      const aiTeamB = document.getElementById("ai-team-b");
      const aiConfidence = document.getElementById("ai-confidence");
      const aiStage = document.getElementById("ai-stage");
      const aiKeyTips = document.getElementById("ai-key-tips");
      const aiText = document.getElementById("ai-text");
      const aiPredictedScore = document.getElementById("ai-predicted-score");
      const aiModelName = document.getElementById("ai-model-name");
      
      if (editBtn) {
        const id = parseInt(editBtn.dataset.id);
        const item = savedAnalyses.find(a => a.id === id);
        if (item) {
          aiIdField.value = item.id;
          if (aiTeamA) aiTeamA.value = item.teamA;
          if (aiTeamB) aiTeamB.value = item.teamB;
          if (aiConfidence) aiConfidence.value = item.confidence;
          if (aiStage) aiStage.value = item.stage || "Fase de Grupos";
          if (aiKeyTips) aiKeyTips.value = (item.key_tips || []).join(", ");
          if (aiText) aiText.value = item.analysis_text;
          if (aiPredictedScore) aiPredictedScore.value = item.predicted_score && item.predicted_score !== "null" ? item.predicted_score : "";
          if (aiModelName) aiModelName.value = item.model_name || "Manual";
          
          // Fill all odds fields dynamically if the dictionary exists
          if (item.odds) {
            Object.keys(item.odds).forEach(originalId => {
              const input = document.getElementById("ai-odds-" + originalId);
              if (input) {
                input.value = item.odds[originalId] !== null ? item.odds[originalId] : "";
              }
            });
          } else {
            // Fallback for old items
            const inputA = document.getElementById("ai-odds-input-odds-a");
            const inputDraw = document.getElementById("ai-odds-input-odds-draw");
            const inputB = document.getElementById("ai-odds-input-odds-b");
            if (inputA) inputA.value = item.odds_a !== undefined && item.odds_a !== null ? item.odds_a : "";
            if (inputDraw) inputDraw.value = item.odds_draw !== undefined && item.odds_draw !== null ? item.odds_draw : "";
            if (inputB) inputB.value = item.odds_b !== undefined && item.odds_b !== null ? item.odds_b : "";
          }
          
          const formTitle = document.getElementById("crud-form-title");
          if (formTitle) formTitle.textContent = "✏️ Editar Análisis de IA";
          
          const formCard = aiAnalysisForm ? aiAnalysisForm.closest(".glass-card") : null;
          if (formCard) formCard.scrollIntoView({ behavior: 'smooth' });
        }
      }
      
      if (deleteBtn) {
        if (!confirm("¿Estás seguro de que deseas eliminar este análisis?")) return;
        const id = parseInt(deleteBtn.dataset.id);
        
        try {
          const res = await fetch(`/api/ai-analyses/${id}`, {
            method: "DELETE",
            headers: {
              "X-Admin-Password": adminPassword
            }
          });
          
          if (res.status === 401) {
            handleUnauthorized();
            return;
          }
          
          const json = await res.json();
          if (res.ok && json.status === "success") {
            showToast("Análisis eliminado.", "success");
            loadAIAnalyses();
          } else {
            showToast("Error al borrar: " + (json.detail || "Error desconocido"), "error");
          }
        } catch (err) {
          console.error("Delete analysis error:", err);
          showToast("Error de red al borrar.", "error");
        }
      }
    });
  }

  // Event listener for user plan management (FREE / PREMIUM toggle)
  const usersTbody = document.getElementById("users-tbody");
  if (usersTbody) {
    usersTbody.addEventListener("click", async (e) => {
      const editPlanBtn = e.target.closest(".btn-edit-user-plan");
      if (editPlanBtn) {
        const userId = editPlanBtn.dataset.id;
        const newPlan = editPlanBtn.dataset.plan;
        
        editPlanBtn.disabled = true;
        editPlanBtn.textContent = "Guardando...";

        try {
          const res = await fetch(`/api/admin/users/${userId}/plan`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "X-Admin-Password": adminPassword
            },
            body: JSON.stringify({ plan: newPlan })
          });

          if (res.status === 401) {
            handleUnauthorized();
            return;
          }

          const json = await res.json();
          if (res.ok && json.status === "success") {
            showToast(`Plan actualizado a ${newPlan}.`, "success");
            loadAdminUsers();
          } else {
            showToast("Error al actualizar el plan: " + (json.detail || "Error desconocido"), "error");
            editPlanBtn.disabled = false;
            editPlanBtn.textContent = `Cambiar a ${newPlan}`;
          }
        } catch (err) {
          console.error("Update plan error:", err);
          showToast("Error de red al actualizar el plan.", "error");
          editPlanBtn.disabled = false;
          editPlanBtn.textContent = `Cambiar a ${newPlan}`;
        }
      }
    });
  }
}

async function loadAdminUsers() {
  const tbody = document.getElementById("users-tbody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/admin/users", {
      headers: {
        "X-Admin-Password": adminPassword
      }
    });

    if (res.status === 401) {
      handleUnauthorized();
      return;
    }

    const data = await res.json();
    console.log("DEBUG: loadAdminUsers success. Users received:", data.users ? data.users.length : 0);
    if (res.ok && data.status === "success" && data.users) {
      adminUsers = data.users;
      tbody.innerHTML = "";
      updateAdminStats();
      if (data.users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--color-text-secondary);">No hay usuarios registrados.</td></tr>`;
        return;
      }

      data.users.forEach(user => {
        const tr = document.createElement("tr");
        tr.style.borderBottom = "1px solid rgba(255,255,255,0.05)";

        const shortenedId = user.id ? `${user.id.substring(0, 8)}...` : "N/A";
        const cleanEmail = user.email || "N/A";
        const username = user.username || cleanEmail.split("@")[0];

        // Format created_at date nicely
        let dateStr = "N/A";
        if (user.created_at) {
          const d = new Date(user.created_at);
          dateStr = d.toLocaleDateString("es-ES", {
            day: "numeric",
            month: "short",
            year: "numeric"
          });
        }

        const isPremium = user.plan === "PREMIUM";
        const badgeStyle = isPremium 
          ? "background: rgba(240, 179, 16, 0.15); color: var(--color-primary); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;"
          : "background: rgba(52, 211, 153, 0.15); color: #34d399; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;";

        const newPlanToggle = isPremium ? "FREE" : "PREMIUM";

        tr.innerHTML = `
          <td style="padding: 12px 8px; font-family: monospace; color: var(--color-text-secondary);" title="${user.id}">${shortenedId}</td>
          <td style="padding: 12px 8px; font-weight: 600;">
            ${username} <span style="font-weight: 400; font-size: 0.75rem; color: var(--color-text-secondary);">(${cleanEmail})</span>
          </td>
          <td style="padding: 12px 8px; color: var(--color-text-secondary);">${dateStr}</td>
          <td style="padding: 12px 8px;"><span style="${badgeStyle}">${user.plan}</span></td>
          <td style="padding: 12px 8px;">
            <button class="btn btn-secondary btn-edit-user-plan" data-id="${user.id}" data-plan="${newPlanToggle}" style="padding: 4px 10px; height: auto; font-size: 0.7rem; cursor: pointer;">
              Cambiar a ${newPlanToggle}
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } else {
      tbody.innerHTML = `<tr><td colspan="5" style="padding: 20px; text-align: center; color: #ef4444;">Error al cargar usuarios: ${data.detail || "Error desconocido"}</td></tr>`;
    }
  } catch (err) {
    console.error("Error loading admin users:", err);
    tbody.innerHTML = `<tr><td colspan="5" style="padding: 20px; text-align: center; color: #ef4444;">Error de red al cargar usuarios.</td></tr>`;
  }
}
