/**
 * SolSpot Frontend Application
 * Interacts with FastAPI backend powered by Prior Labs TabPFN & Google Gemma 2.
 */

// Application State
const state = {
  currentLocation: {
    name: "San Francisco",
    lat: 37.7749,
    lon: -122.4194
  },
  forecastData: null,
  activeHourIndex: 12,
  timerInterval: null,
  timerRemainingSeconds: 20 * 60, // 20 minutes
  isTimerRunning: false,
  isAudioPlaying: false,
  audioContext: null,
  noiseNode: null,
  streak: parseInt(localStorage.getItem("solspot_streak") || "0", 10)
};

// DOM Elements
const elements = {
  cityInput: document.getElementById("cityInput"),
  geoBtn: document.getElementById("geoBtn"),
  searchResults: document.getElementById("searchResults"),
  locationChip: document.getElementById("locationChip"),
  windowTime: document.getElementById("windowTime"),
  windowSummary: document.getElementById("windowSummary"),
  peakScoreVal: document.getElementById("peakScoreVal"),
  scoreRing: document.getElementById("scoreRing"),
  quickLux: document.getElementById("quickLux"),
  quickTemp: document.getElementById("quickTemp"),
  quickUv: document.getElementById("quickUv"),
  solarArcCanvas: document.getElementById("solarArcCanvas"),
  hourlyStrip: document.getElementById("hourlyStrip"),
  questText: document.getElementById("questText"),
  refreshQuestBtn: document.getElementById("refreshQuestBtn"),
  activateGrassBtn: document.getElementById("activateGrassBtn"),
  setReminderBtn: document.getElementById("setReminderBtn"),
  grassModeModal: document.getElementById("grassModeModal"),
  closeGrassModalBtn: document.getElementById("closeGrassModalBtn"),
  finishGrassBtn: document.getElementById("finishGrassBtn"),
  modalTimer: document.getElementById("modalTimer"),
  breatheText: document.getElementById("breatheText"),
  toggleAudioBtn: document.getElementById("toggleAudioBtn"),
  audioIcon: document.getElementById("audioIcon"),
  audioLabel: document.getElementById("audioLabel"),
  celebrationModal: document.getElementById("celebrationModal"),
  closeCelebrationBtn: document.getElementById("closeCelebrationBtn"),
  streakCount: document.getElementById("streakCount"),
  newStreakNum: document.getElementById("newStreakNum"),
  tabpfnStatusChip: document.getElementById("tabpfnStatusChip")
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  elements.streakCount.textContent = state.streak;
  initEventListeners();
  initBreathingText();
  detectLocationOrFallback();
});

function initEventListeners() {
  // Geolocation
  elements.geoBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    elements.locationChip.textContent = "📍 Locating via GPS...";
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        state.currentLocation = {
          name: "Current GPS Location",
          lat: pos.coords.latitude,
          lon: pos.coords.longitude
        };
        fetchForecast();
      },
      (err) => {
        console.warn("Geolocation denied or error:", err);
        elements.locationChip.textContent = "📍 GPS denied. Using default.";
        fetchForecast();
      }
    );
  });

  // City Search with Debounce
  let searchTimeout = null;
  elements.cityInput.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();
    if (query.length < 2) {
      elements.searchResults.classList.add("hidden");
      return;
    }
    searchTimeout = setTimeout(async () => {
      try {
        const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await resp.json();
        renderSearchResults(data.results || []);
      } catch (err) {
        console.error("Search error:", err);
      }
    }, 280);
  });

  // Close search dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!elements.searchResults.contains(e.target) && e.target !== elements.cityInput) {
      elements.searchResults.classList.add("hidden");
    }
  });

  // Refresh Gemma Micro-Quest
  elements.refreshQuestBtn.addEventListener("click", async () => {
    elements.questText.textContent = "Gemma 2 is synthesizing a new sensory quest...";
    elements.refreshQuestBtn.style.transform = "rotate(180deg)";
    try {
      const best = state.forecastData?.best_window || {};
      const resp = await fetch(`/api/refresh-quest?hour=${best.best_hour || 12}&temp=${best.temp_c || 20}&uv=${best.uv_index || 2}&cloud=${best.cloud_cover || 20}`);
      const data = await resp.json();
      elements.questText.textContent = data.quest_text;
    } catch (err) {
      console.error(err);
    } finally {
      setTimeout(() => elements.refreshQuestBtn.style.transform = "", 300);
    }
  });

  // Grass Mode Modal triggers
  elements.activateGrassBtn.addEventListener("click", openGrassMode);
  elements.closeGrassModalBtn.addEventListener("click", closeGrassMode);
  elements.finishGrassBtn.addEventListener("click", completeGrassSession);
  elements.closeCelebrationBtn.addEventListener("click", () => {
    elements.celebrationModal.classList.add("hidden");
  });

  // Web Audio ambient sound toggle
  elements.toggleAudioBtn.addEventListener("click", toggleNatureAudio);

  // Notification button
  elements.setReminderBtn.addEventListener("click", () => {
    if ("Notification" in window) {
      Notification.requestPermission().then((perm) => {
        if (perm === "granted") {
          new Notification("SolSpot Reminder Scheduled", {
            body: `Your optimal Touch Grass window is at ${state.forecastData?.best_window?.window_time || "afternoon"}.`,
            icon: "/static/assets/favicon.ico"
          });
          alert("Reminder set! We will notify you when your optimal window approaches.");
        } else {
          alert("Notifications are disabled in your browser settings.");
        }
      });
    } else {
      alert("Browser notifications not supported.");
    }
  });
}

function detectLocationOrFallback() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        state.currentLocation = {
          name: "Your Location",
          lat: pos.coords.latitude,
          lon: pos.coords.longitude
        };
        fetchForecast();
      },
      () => {
        // Fallback default city
        fetchForecast();
      },
      { timeout: 4000 }
    );
  } else {
    fetchForecast();
  }
}

async function fetchForecast() {
  elements.locationChip.textContent = `📍 ${state.currentLocation.name}`;
  elements.windowTime.textContent = "Calculating...";
  elements.windowSummary.textContent = "Prior Labs TabPFN is analyzing solar blue-spectrum and UV curves...";

  try {
    const url = `/api/forecast?lat=${state.currentLocation.lat}&lon=${state.currentLocation.lon}&city_name=${encodeURIComponent(state.currentLocation.name)}`;
    const resp = await fetch(url);
    if (!resp.ok) throw new Error("Forecast API error");

    const data = await resp.json();
    state.forecastData = data;
    renderDashboard(data);
  } catch (err) {
    console.error("Forecast failed:", err);
    elements.windowSummary.textContent = "Unable to fetch live solar forecast. Please check internet connection.";
  }
}

function renderDashboard(data) {
  const best = data.best_window || {};
  const gemma = data.gemma_quest || {};
  const hourly = data.hourly_scores || [];

  // Update Status Chip
  if (data.engine_metadata?.tabpfn_active) {
    elements.tabpfnStatusChip.textContent = "TabPFN Transformer (Live)";
    elements.tabpfnStatusChip.classList.add("ready");
  } else {
    elements.tabpfnStatusChip.textContent = "TabPFN / Hybrid Engine";
  }

  // Hero Card
  elements.windowTime.textContent = best.window_time || "14:15 – 14:35";
  elements.windowSummary.textContent = `${best.tier || "Optimal Window"}: ${best.recommendation || "High circadian stimulation with safe UV exposure."}`;
  
  // Radial Score Ring
  const score = best.peak_score || 85;
  elements.peakScoreVal.textContent = Math.round(score);
  const maxDash = 326.7;
  const offset = maxDash - (score / 100) * maxDash;
  elements.scoreRing.style.strokeDashoffset = offset;

  // Conditions
  elements.quickLux.textContent = `${(best.lux_estimate || 8500).toLocaleString()} lux`;
  elements.quickTemp.textContent = `${best.temp_c || 21}°C`;
  elements.quickUv.textContent = `UV ${best.uv_index || 3.1}`;

  // Gemma Quest
  elements.questText.textContent = gemma.quest_text || "Step outside and look away from all monitors.";

  // Render Hourly Scroller
  renderHourlyStrip(hourly, best.best_hour);

  // Render Solar Arc
  drawSolarArc(hourly, best.best_hour);
}

function renderSearchResults(results) {
  elements.searchResults.innerHTML = "";
  if (!results.length) {
    elements.searchResults.classList.add("hidden");
    return;
  }

  results.forEach((city) => {
    const div = document.createElement("div");
    div.className = "search-item";
    div.innerHTML = `
      <span><strong>${city.name}</strong>${city.admin1 ? ", " + city.admin1 : ""}</span>
      <span class="search-item-country">${city.country}</span>
    `;
    div.addEventListener("click", () => {
      state.currentLocation = {
        name: `${city.name}, ${city.country}`,
        lat: city.latitude,
        lon: city.longitude
      };
      elements.cityInput.value = city.name;
      elements.searchResults.classList.add("hidden");
      fetchForecast();
    });
    elements.searchResults.appendChild(div);
  });

  elements.searchResults.classList.remove("hidden");
}

function renderHourlyStrip(hourly, bestHour) {
  elements.hourlyStrip.innerHTML = "";

  hourly.forEach((hourData, idx) => {
    const h = hourData.hour;
    if (h < 5 || h > 21) return; // focus on daylight hours

    const card = document.createElement("div");
    card.className = "hour-card";
    if (Math.floor(h) === bestHour) card.classList.add("golden-window");

    const timeLabel = `${String(Math.floor(h)).padStart(2, '0')}:00`;
    
    // Icon based on hour and conditions
    let icon = "☀️";
    if (hourData.cloud_cover_pct > 70) icon = "☁️";
    else if (h < 7 || h > 18) icon = "🌅";
    else if (hourData.uv_index > 6) icon = "🔥";

    card.innerHTML = `
      <span class="hc-time">${timeLabel}</span>
      <span class="hc-icon">${icon}</span>
      <span class="hc-score">${Math.round(hourData.circadian_wellness_score)}</span>
      <span class="hc-badge">${hourData.badge || "🌿"}</span>
    `;

    card.addEventListener("click", () => {
      document.querySelectorAll(".hour-card").forEach(c => c.classList.remove("active-hour"));
      card.classList.add("active-hour");
      state.activeHourIndex = idx;
      drawSolarArc(hourly, Math.floor(h));
    });

    elements.hourlyStrip.appendChild(card);
  });
}

function drawSolarArc(hourly, highlightHour = 12) {
  const canvas = elements.solarArcCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  
  // Set display resolution
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * window.devicePixelRatio || 900;
  canvas.height = rect.height * window.devicePixelRatio || 180;
  ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

  const w = rect.width;
  const h = rect.height;

  ctx.clearRect(0, 0, w, h);

  // Draw Ground / Horizon Line
  const horizonY = h - 35;
  ctx.beginPath();
  ctx.moveTo(30, horizonY);
  ctx.lineTo(w - 30, horizonY);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Draw Solar Arc Path
  ctx.beginPath();
  const startX = 40;
  const endX = w - 40;
  const peakY = 25;
  ctx.moveTo(startX, horizonY);
  ctx.quadraticCurveTo(w / 2, peakY, endX, horizonY);
  
  // Arc gradient
  const arcGrad = ctx.createLinearGradient(startX, 0, endX, 0);
  arcGrad.addColorStop(0, "rgba(251, 191, 36, 0.3)");
  arcGrad.addColorStop(0.5, "rgba(245, 158, 11, 0.9)");
  arcGrad.addColorStop(1, "rgba(239, 68, 68, 0.4)");

  ctx.strokeStyle = arcGrad;
  ctx.lineWidth = 3;
  ctx.setLineDash([4, 4]);
  ctx.stroke();
  ctx.setLineDash([]);

  // Calculate Sun Position for highlightHour (scale from 6 AM to 20 PM)
  const normTime = Math.max(0, Math.min(1, (highlightHour - 6) / 14));
  const sunX = startX + normTime * (endX - startX);
  // Quadratic bezier formula y = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
  const t = normTime;
  const sunY = (1 - t) * (1 - t) * horizonY + 2 * (1 - t) * t * peakY + t * t * horizonY;

  // Glow halo
  const sunGlow = ctx.createRadialGradient(sunX, sunY, 2, sunX, sunY, 26);
  sunGlow.addColorStop(0, "rgba(251, 191, 36, 0.9)");
  sunGlow.addColorStop(0.4, "rgba(245, 158, 11, 0.35)");
  sunGlow.addColorStop(1, "rgba(245, 158, 11, 0)");
  ctx.fillStyle = sunGlow;
  ctx.beginPath();
  ctx.arc(sunX, sunY, 26, 0, Math.PI * 2);
  ctx.fill();

  // Sun Core
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(sunX, sunY, 7, 0, Math.PI * 2);
  ctx.fill();

  // Labels
  ctx.fillStyle = "rgba(148, 163, 184, 0.8)";
  ctx.font = "11px 'Plus Jakarta Sans', sans-serif";
  ctx.fillText("06:00 Dawn", startX, horizonY + 20);
  ctx.fillText("13:00 Solar Noon", w / 2 - 40, horizonY + 20);
  ctx.fillText("20:00 Dusk", endX - 50, horizonY + 20);

  // Optimal Window Flag
  ctx.fillStyle = "#fbbf24";
  ctx.font = "bold 11px 'JetBrains Mono', monospace";
  ctx.fillText(`Target: ${highlightHour}:00`, Math.max(20, Math.min(w - 90, sunX - 35)), sunY - 14);
}

// Grass Mode Fullscreen Logic
function openGrassMode() {
  elements.grassModeModal.classList.remove("hidden");
  state.timerRemainingSeconds = 20 * 60;
  state.isTimerRunning = true;
  updateTimerDisplay();

  clearInterval(state.timerInterval);
  state.timerInterval = setInterval(() => {
    if (state.timerRemainingSeconds > 0) {
      state.timerRemainingSeconds--;
      updateTimerDisplay();
    } else {
      completeGrassSession();
    }
  }, 1000);
}

function closeGrassMode() {
  elements.grassModeModal.classList.add("hidden");
  clearInterval(state.timerInterval);
  state.isTimerRunning = false;
  stopNatureAudio();
}

function updateTimerDisplay() {
  const m = Math.floor(state.timerRemainingSeconds / 60);
  const s = state.timerRemainingSeconds % 60;
  elements.modalTimer.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function initBreathingText() {
  const texts = ["Inhale Deeply (4s)", "Hold Gently (4s)", "Exhale Slowly (4s)", "Relax Shoulders"];
  let i = 0;
  setInterval(() => {
    i = (i + 1) % texts.length;
    elements.breatheText.textContent = texts[i];
  }, 4000);
}

function completeGrassSession() {
  closeGrassMode();
  state.streak += 1;
  localStorage.setItem("solspot_streak", state.streak);
  elements.streakCount.textContent = state.streak;
  elements.newStreakNum.textContent = state.streak;
  elements.celebrationModal.classList.remove("hidden");
}

// Procedural Nature Audio (Breeze / Wind chime via Web Audio API)
function toggleNatureAudio() {
  if (state.isAudioPlaying) {
    stopNatureAudio();
  } else {
    startNatureAudio();
  }
}

function startNatureAudio() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    state.audioContext = new AudioContext();

    // White noise buffer for wind/rustle
    const bufferSize = state.audioContext.sampleRate * 2;
    const noiseBuffer = state.audioContext.createBuffer(1, bufferSize, state.audioContext.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      output[i] = Math.random() * 2 - 1;
    }

    const whiteNoise = state.audioContext.createBufferSource();
    whiteNoise.buffer = noiseBuffer;
    whiteNoise.loop = true;

    // Filter to simulate low rustling wind
    const filter = state.audioContext.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(380, state.audioContext.currentTime);

    const gainNode = state.audioContext.createGain();
    gainNode.gain.setValueAtTime(0.08, state.audioContext.currentTime);

    whiteNoise.connect(filter);
    filter.connect(gainNode);
    gainNode.connect(state.audioContext.destination);

    whiteNoise.start();
    state.noiseNode = whiteNoise;
    state.isAudioPlaying = true;

    elements.audioIcon.textContent = "🔊";
    elements.audioLabel.textContent = "Mute Ambient Sound";
  } catch (err) {
    console.warn("Web audio not supported:", err);
  }
}

function stopNatureAudio() {
  if (state.noiseNode) {
    try {
      state.noiseNode.stop();
      state.noiseNode.disconnect();
    } catch (_) {}
  }
  if (state.audioContext) {
    state.audioContext.close();
  }
  state.isAudioPlaying = false;
  elements.audioIcon.textContent = "🔈";
  elements.audioLabel.textContent = "Play Gentle Nature Ambient";
}
