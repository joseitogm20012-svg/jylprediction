#!/usr/bin/env node
// Walk-forward, OUT-OF-SAMPLE backtest of the model on real internationals.
// Includes ROI / Financial Backtesting with a Simulated Bookmaker.
//   node backtest.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { matchProb, expectedScore } from "./elo.mjs";

const D = (f) => new URL(`./data/${f}`, import.meta.url);
const SEED = {
  argentina:2085,france:2065,spain:2055,brazil:2045,england:2000,portugal:1980,netherlands:1965,germany:1945,belgium:1925,italy:1915,colombia:1890,uruguay:1875,croatia:1870,morocco:1840,switzerland:1825,usa:1830,mexico:1825,japan:1810,senegal:1795,denmark:1790,ecuador:1760,australia:1735,"south-korea":1730,iran:1720,poland:1715,canada:1700,serbia:1695,wales:1665,ghana:1665,tunisia:1655,"ivory-coast":1655,nigeria:1645,"saudi-arabia":1640,qatar:1630,egypt:1620,algeria:1615,scotland:1610,cameroon:1600,paraguay:1595,venezuela:1590,chile:1580,peru:1575,"czech-republic":1570,"bosnia-and-herzegovina":1545,"south-africa":1520,"new-zealand":1495,panama:1480,jamaica:1460,honduras:1440,jordan:1420,haiti:1380,"el-salvador":1370,"trinidad-and-tobago":1360,guatemala:1345
};
const HOME_ADV = 75, BURN_IN = 150;
const baseK = (n = "") => { n = n.toLowerCase();
  if (/world cup(?!.*qual)/.test(n)) return 55;
  if (/world cup.*qual|qualification/.test(n)) return 40;
  if (/copa america|euro championship\b|asian cup|africa cup|gold cup/.test(n)) return 50;
  if (/nations league|nations cup/.test(n)) return 32;
  if (/friendl/.test(n)) return 18;
  return 28; };
const gMult = (gd) => { const d = Math.abs(gd); return d <= 1 ? 1 : d === 2 ? 1.5 : (11 + d) / 8; };

// Parse CSV instead of JSON
let matches = [];
try {
  const csvText = readFileSync(D("results.csv"), "utf8");
  const lines = csvText.trim().split(/\r?\n/);
  for (let i = 1; i < lines.length; i++) {
    const p = lines[i].split(',');
    if (p.length < 6) continue;
    const date = p[0], homeName = p[1], awayName = p[2], hgStr = p[3], agStr = p[4], leagueName = p[5];
    if (!homeName || !awayName) continue;
    const hg = (hgStr === 'NA' || isNaN(parseInt(hgStr))) ? null : parseInt(hgStr);
    const ag = (agStr === 'NA' || isNaN(parseInt(agStr))) ? null : parseInt(agStr);
    const homeSlug = homeName.toLowerCase().replace(/ /g, '-').replace(/'/g, '').replace(/\./g, '');
    const awaySlug = awayName.toLowerCase().replace(/ /g, '-').replace(/'/g, '').replace(/\./g, '');
    matches.push({ date, homeName, awayName, hg, ag, leagueName, homeSlug, awaySlug });
  }
} catch (e) {
  console.error("No se pudo leer data/results.csv. Asegúrate de ejecutar update_results.bat primero.");
  process.exit(1);
}

// Trackers
const R = {};
const naiveR = {}; // Bookmaker's Elo (basic)

const getR = (dict, s, nm) => { const k = s ?? `ghost:${nm}`; if (dict[k] == null) dict[k] = s && SEED[s] != null ? SEED[s] : 1500; return dict[k]; };
const setR = (dict, s, nm, v) => { dict[s ?? `ghost:${nm}`] = v; };

let n = 0, hit = 0, brier = 0, logloss = 0, favN = 0, favHit = 0, baseHome = 0, baseElo = 0, i = 0;
let eH = 0, eD = 0, eA = 0;

// Financial metrics
let bankroll = 0; // units
let betsPlaced = 0;
let betsWon = 0;
const VIG_MARGIN = 1.05; // 5% bookmaker margin
const MIN_EDGE = 0.05; // Bet only if we have at least 5% expected value
const BET_SIZE = 1; // 1 unit per bet

let rps = 0, rpsU = 0;
const rps3 = (p, y) => 0.5 * ((p[0] - y[0]) ** 2 + (p[0] + p[1] - y[0] - y[1]) ** 2);
const BINS = 10;
const calib = Array.from({ length: BINS }, () => ({ sumP: 0, sumY: 0, n: 0 }));

for (const m of matches) {
  if (m.hg == null || m.ag == null) continue;
  
  // Advanced Model Ratings
  const ra = getR(R, m.homeSlug, m.homeName);
  const rb = getR(R, m.awaySlug, m.awayName);
  
  // Naive Bookmaker Ratings
  const naiveRa = getR(naiveR, m.homeSlug, m.homeName);
  const naiveRb = getR(naiveR, m.awaySlug, m.awayName);
  
  if (i >= BURN_IN) {
    const p = matchProb(ra, rb, HOME_ADV);
    const probs = [p.winA, p.draw, p.winB];
    const actual = m.hg > m.ag ? 0 : m.hg < m.ag ? 2 : 1;
    const y = [actual === 0 ? 1 : 0, actual === 1 ? 1 : 0, actual === 2 ? 1 : 0];
    const pred = probs.indexOf(Math.max(...probs));
    
    if (pred === actual) hit++;
    brier += (probs[0]-y[0])**2 + (probs[1]-y[1])**2 + (probs[2]-y[2])**2;
    logloss += -Math.log(Math.max(1e-12, probs[actual]));
    rps += rps3(probs, y); rpsU += rps3([1/3, 1/3, 1/3], y);
    
    for (let k = 0; k < 3; k++) {
      const b = Math.min(BINS - 1, Math.floor(probs[k] * BINS));
      calib[b].sumP += probs[k]; calib[b].sumY += y[k]; calib[b].n++;
    }
    
    if (Math.max(...probs) >= 0.5) { favN++; if (pred === actual) favHit++; }
    if (actual === 0) baseHome++;
    if ((expectedScore(ra, rb, HOME_ADV) >= 0.5 ? 0 : 2) === actual) baseElo++;
    if (actual === 0) eH++; else if (actual === 1) eD++; else eA++;
    
    // --- FINANCIAL SIMULATION ---
    // Generate Bookmaker odds using Naive Elo + 5% Vig
    const naiveP = matchProb(naiveRa, naiveRb, 50); // Simpler home adv
    const naiveProbs = [naiveP.winA, naiveP.draw, naiveP.winB];
    
    // Convert to decimal odds (e.g. fair prob 0.5 -> fair odds 2.0 -> vig odds 1.9)
    const bookieOdds = naiveProbs.map(prob => 1 / (prob * VIG_MARGIN));
    
    // Look for value bets (Edge = ModelProb * BookieOdds - 1)
    let betPlacedThisMatch = false;
    for (let k = 0; k < 3; k++) {
      // Evitamos apostar a probabilidades irracionales (menores al 5%)
      if (probs[k] < 0.05) continue;
      
      const edge = (probs[k] * bookieOdds[k]) - 1;
      
      // If we find significant value, we bet 1 unit
      if (edge > MIN_EDGE) {
        betsPlaced += BET_SIZE;
        if (actual === k) {
          bankroll += (BET_SIZE * bookieOdds[k]) - BET_SIZE; // Profit
          betsWon++;
        } else {
          bankroll -= BET_SIZE; // Loss
        }
        betPlacedThisMatch = true;
        // Solo apostamos a un mercado por partido (el de mayor valor) para evitar sobreexposición
        break; 
      }
    }
    
    n++;
  }
  
  // Update Advanced Model (Dynamic K, Goal Difference multiplier)
  const exp = expectedScore(ra, rb, HOME_ADV);
  const score = m.hg > m.ag ? 1 : m.hg < m.ag ? 0 : 0.5;
  const delta = baseK(m.leagueName) * gMult(m.hg - m.ag) * (score - exp);
  setR(R, m.homeSlug, m.homeName, ra + delta);
  setR(R, m.awaySlug, m.awayName, rb - delta);
  
  // Update Naive Model (Flat K=20, no multipliers)
  const naiveExp = expectedScore(naiveRa, naiveRb, 50);
  const naiveDelta = 20 * (score - naiveExp);
  setR(naiveR, m.homeSlug, m.homeName, naiveRa + naiveDelta);
  setR(naiveR, m.awaySlug, m.awayName, naiveRb - naiveDelta);
  
  i++;
}

const pct = (x) => (x * 100).toFixed(1) + "%";
console.log(`\n=== Walk-forward backtest — ${n} of ${matches.length} matches (burn-in ${BURN_IN}) ===`);
console.log(`Eval outcome split: home ${pct(eH/n)}  draw ${pct(eD/n)}  away ${pct(eA/n)}\n`);
console.log(`MODEL METRICS`);
console.log(`  Accuracy (top pick):   ${pct(hit/n)}`);
console.log(`  Favourite acc (p≥50%): ${pct(favHit/favN)}  (${favN} matches)`);
console.log(`  Brier (3-way, ↓):      ${(brier/n).toFixed(3)}`);
console.log(`  Log-loss (↓):          ${(logloss/n).toFixed(3)}`);
console.log(`  RPS (↓):               ${(rps/n).toFixed(4)}`);
const ece = calib.reduce((s, b) => s + (b.n ? Math.abs(b.sumP / b.n - b.sumY / b.n) * b.n : 0), 0) / (3 * n);
console.log(`  ECE (calibration, ↓):  ${(ece * 100).toFixed(1)}%\n`);

console.log(`FINANCIAL BACKTESTING (Simulated Bookmaker)`);
console.log(`  Bookmaker Margin (Vig): ${((VIG_MARGIN - 1)*100).toFixed(1)}%`);
console.log(`  Minimum Edge to Bet:   ${(MIN_EDGE*100).toFixed(1)}%`);
console.log(`  Total Bets Placed:     ${betsPlaced}  (${(betsPlaced/n * 100).toFixed(1)}% of matches)`);
if (betsPlaced > 0) {
  console.log(`  Bets Won:              ${betsWon} (${pct(betsWon/betsPlaced)} Hit Rate)`);
  const roi = (bankroll / betsPlaced) * 100;
  console.log(`  Profit/Loss (P&L):     ${bankroll >= 0 ? '+' : ''}${bankroll.toFixed(2)} Units`);
  console.log(`  Yield (ROI):           ${roi >= 0 ? '+' : ''}${roi.toFixed(2)}%`);
}
console.log(`\nBASELINES`);
console.log(`  Always pick home:      ${pct(baseHome/n)}`);
console.log(`  Pick higher-Elo team:  ${pct(baseElo/n)}`);

// Persist the metrics
writeFileSync(D("model-backtest.json"), JSON.stringify({
  generatedAt: new Date().toISOString(),
  method: "Walk-forward out-of-sample with Simulated Financial ROI.",
  totalMatches: matches.length, evaluated: n, burnIn: BURN_IN,
  outcomeSplit: { home: +(eH/n).toFixed(4), draw: +(eD/n).toFixed(4), away: +(eA/n).toFixed(4) },
  model: { accuracy: +(hit/n).toFixed(4), brier: +(brier/n).toFixed(4), logloss: +(logloss/n).toFixed(4),
           rps: +(rps/n).toFixed(4), ece: +ece.toFixed(4) },
  financials: {
    margin: VIG_MARGIN,
    minEdge: MIN_EDGE,
    betsPlaced: betsPlaced,
    betsWon: betsWon,
    profitUnits: +bankroll.toFixed(2),
    roiPercent: betsPlaced > 0 ? +((bankroll / betsPlaced) * 100).toFixed(2) : 0
  }
}, null, 2) + "\n");
console.log("\n→ wrote data/model-backtest.json");
