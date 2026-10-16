// ==============================================================================
// J.A.R.V.I.S. Command Surface — Live Neural Link & Generative UI Engine
// Single Source of Truth Backend Integration
// ==============================================================================

const API_BASE = window.location.origin || "http://127.0.0.1:8000";
const WS_URL = (window.location.protocol === "https:" ? "wss://" : "ws://") + 
               (window.location.host || "127.0.0.1:8000") + "/api/ws/hud";

// 1. DIGITAL CLOCK
function updateClock() {
  const clockEl = document.querySelector('#clock');
  if (clockEl) {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('en-GB', { hour12: false });
  }
}
updateClock();
setInterval(updateClock, 1000);

// 2. WEBSOCKET REAL-TIME EVENTBUS
let ws = null;
let wsReconnectTimer = null;

function connectWebSocket() {
  try {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log(">> [WS]: Neural EventBus Connected.");
      const dot = document.getElementById('neuralDot');
      if (dot) {
        dot.style.background = "var(--green)";
        dot.style.boxShadow = "0 0 18px var(--green)";
      }
      const st = document.getElementById('status');
      if (st) st.textContent = "Neural Link Active · All Real-Time Telemetry Streaming";
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleLiveEvent(msg);
      } catch (err) {
        console.error("WS Parse Error:", err);
      }
    };

    ws.onclose = () => {
      const dot = document.getElementById('neuralDot');
      if (dot) {
        dot.style.background = "#ff5d6c";
        dot.style.boxShadow = "0 0 18px #ff5d6c";
      }
      clearTimeout(wsReconnectTimer);
      wsReconnectTimer = setTimeout(connectWebSocket, 2000);
    };

    ws.onerror = (err) => {
      console.warn("WS Error:", err);
    };
  } catch (err) {
    clearTimeout(wsReconnectTimer);
    wsReconnectTimer = setTimeout(connectWebSocket, 2000);
  }
}

// 3. LIVE EVENT HANDLER (SINGLE SOURCE OF TRUTH)
function handleLiveEvent(msg) {
  const type = msg.type || msg.event;
  const data = msg.data || msg.payload || msg;
  if (!type) return;

  if (type === "diagnostics" || type === "system_telemetry" || type === "telemetry") {
    const cpu = Math.round(data.cpu ?? 0);
    const ram = Math.round(data.ram ?? data.mem ?? 0);
    const gpu = Math.round(data.gpu ?? 0);
    const temp = Math.round(data.core_temp ?? data.temp ?? 45);
    const net = data.net_down_mbps !== undefined ? `${data.net_down_mbps.toFixed(0)} Mb/s` : (data.net_speed ?? "0.0 Mb/s");

    const diagSum = document.getElementById('diagSummary');
    if (diagSum) diagSum.textContent = `CPU: ${cpu}% · RAM: ${ram}%`;
    const diagDet = document.getElementById('diagDetails');
    if (diagDet) diagDet.textContent = `GPU: ${gpu}% · Temp: ${temp}°C · Net: ${net}`;
    const diagM = document.getElementById('diagMeter');
    if (diagM) diagM.style.width = `${Math.min(100, Math.max(5, cpu))}%`;
  }
  else if (type === "weather") {
    const temp = data.temp_c ?? data.temp ?? 26;
    const desc = data.description ?? data.desc ?? "Nominal Weather Station";
    const wT = document.getElementById('weatherTemp');
    if (wT) wT.textContent = `${temp}°C / ${desc}`;
    const wD = document.getElementById('weatherDesc');
    if (wD) wD.textContent = `Humidity: ${data.humidity || 65}% · Wind: ${data.wind_kmph || data.wind || 14} km/h · Karachi`;
    const wM = document.getElementById('weatherMeter');
    if (wM) wM.style.width = `${Math.min(100, temp * 2.5)}%`;
  }
  else if (type === "crypto" || type === "quant") {
    const price = data.price ?? data.btc;
    const btcStr = price ? `$${Math.round(price).toLocaleString()}` : "$64,280";
    const chg = data.change_pct !== undefined ? `${data.change_pct >= 0 ? '+' : ''}${data.change_pct.toFixed(2)}%` : '+1.45%';
    const cEl = document.getElementById('cryptoBtc');
    if (cEl) cEl.textContent = `BTC: ${btcStr} (${chg})`;
  }
  else if (type === "music" || type === "media") {
    const title = data.title || data.track || "No Media Active";
    const artist = data.artist || "Audio Subsystem Standby";
    const mTitle = document.getElementById('musicTitle');
    if (mTitle) mTitle.textContent = title;
    const mArtist = document.getElementById('musicArtist');
    if (mArtist) mArtist.textContent = artist;

    if (data.duration_sec && data.position_sec) {
      const pct = (data.position_sec / data.duration_sec) * 100;
      const fill = document.getElementById('musicFill');
      if (fill) fill.style.width = `${pct}%`;
    }
  }
  else if (type === "home.devices" || type === "smart_home" || type === "plug") {
    let is_on = false;
    if (data.devices && Array.isArray(data.devices)) {
      const plug = data.devices.find(d => d.type === "plug");
      if (plug) is_on = plug.state === "on";
    } else if (data.is_on !== undefined) {
      is_on = data.is_on;
    }
    const pSt = document.getElementById('plugStatus');
    if (pSt) pSt.textContent = `Main Desk Appliance: ${is_on ? "ON" : "OFF"}`;
    const pInd = document.getElementById('plugIndicator');
    if (pInd) pInd.textContent = is_on ? "State: ACTIVE (Powered)" : "State: STANDBY";
  }
  else if (type === "f1") {
    const fRace = document.getElementById('f1Race');
    if (fRace && data.next_race) fRace.textContent = data.next_race;
    const fCd = document.getElementById('f1Countdown');
    if (fCd && data.lap) fCd.textContent = `Lap ${data.lap} · Leader: ${data.leader || 'VER'} (${data.gap || '+0.0s'})`;
  }
  else if (type === "transcript") {
    const term = document.getElementById('terminalOutput');
    if (term && data.text) {
      const p = document.createElement('p');
      p.innerHTML = `<span>[TRANSCRIPT]</span> ${escapeHtml(data.text)}`;
      term.appendChild(p);
      term.scrollTop = term.scrollHeight;
    }
  }
  else if (type === "dynamic_result") {
    mountDynamicUiElement(data.title, data.html);
  }
}

// 4. GENERATIVE UI ENGINE (DYNAMIC ELEMENT SYNTHESIS)
function mountDynamicUiElement(title, htmlContent) {
  const grid = document.getElementById('dynamicGrid');
  if (!grid) return;

  const card = document.createElement('div');
  card.className = 'dynamic-card';

  const cleanTitle = escapeHtml(title || "INFO // GENERATED UI COMPONENT");
  const cleanHtml = sanitizeHtml(htmlContent);

  card.innerHTML = `
    <div class="dynamic-card-head">
      <span class="dynamic-card-title">${cleanTitle}</span>
      <button class="dynamic-card-close" title="Dismiss Element">✕</button>
    </div>
    <div class="dynamic-card-body">
      ${cleanHtml}
    </div>
  `;

  card.querySelector('.dynamic-card-close').addEventListener('click', () => {
    card.style.opacity = '0';
    card.style.transform = 'scale(0.95)';
    setTimeout(() => card.remove(), 250);
  });

  // Prepend so newest synthesized elements appear first
  grid.prepend(card);

  // Smooth scroll into view
  card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Generative Synthesis Bar Handler
const genPromptInput = document.getElementById('genUiPrompt');
const genSubmitBtn = document.getElementById('genUiSubmit');

async function triggerSynthesis() {
  if (!genPromptInput) return;
  const prompt = genPromptInput.value.trim();
  if (!prompt) return;
  genPromptInput.value = '';

  const st = document.getElementById('status');
  if (st) st.textContent = `Synthesizing dynamic frontend element for: "${prompt}"...`;

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: prompt })
    });
    const data = await res.json();

    if (data.dynamic_result) {
      mountDynamicUiElement(data.dynamic_result.title, data.dynamic_result.html);
    } else if (data.text) {
      mountDynamicUiElement("INFO // " + prompt.slice(0, 30).toUpperCase(), `<p>${escapeHtml(data.text)}</p>`);
    }

    if (st) st.textContent = "Element synthesized successfully and mounted to dashboard.";
  } catch (err) {
    console.error("Synthesis error:", err);
    if (st) st.textContent = `Synthesis error: ${err.message}`;
  }
}

if (genSubmitBtn) genSubmitBtn.addEventListener('click', triggerSynthesis);
if (genPromptInput) genPromptInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') triggerSynthesis(); });

const clearGenBtn = document.getElementById('clearDynamicElements');
if (clearGenBtn) {
  clearGenBtn.addEventListener('click', () => {
    const grid = document.getElementById('dynamicGrid');
    if (grid) {
      grid.querySelectorAll('.dynamic-card:not(#defaultGenCard)').forEach(c => c.remove());
    }
  });
}

// 5. REST TELEMETRY POLLING (INITIAL SYNC)
async function fetchInitialTelemetry() {
  try {
    const [statsRes, weatherRes, cryptoRes, mediaRes, homeRes] = await Promise.allSettled([
      fetch(`${API_BASE}/api/system-stats`).then(r => r.json()),
      fetch(`${API_BASE}/api/weather`).then(r => r.json()),
      fetch(`${API_BASE}/api/crypto`).then(r => r.json()),
      fetch(`${API_BASE}/api/media/now-playing`).then(r => r.json()),
      fetch(`${API_BASE}/api/home/devices`).then(r => r.json())
    ]);

    if (statsRes.status === "fulfilled" && statsRes.value) {
      handleLiveEvent({ type: "system_telemetry", data: statsRes.value });
    }
    if (weatherRes.status === "fulfilled" && weatherRes.value) {
      handleLiveEvent({ type: "weather", data: weatherRes.value });
    }
    if (cryptoRes.status === "fulfilled" && cryptoRes.value) {
      handleLiveEvent({ type: "crypto", data: cryptoRes.value });
    }
    if (mediaRes.status === "fulfilled" && mediaRes.value) {
      handleLiveEvent({ type: "music", data: mediaRes.value });
    }
    if (homeRes.status === "fulfilled" && homeRes.value && homeRes.value.devices) {
      const plug = homeRes.value.devices.find(d => d.type === "plug");
      if (plug) handleLiveEvent({ type: "smart_home", data: { is_on: plug.state === "on" } });
    }
  } catch (err) {
    console.warn("Telemetry Initial Fetch Notice:", err);
  }
}

// 6. HARDWARE & MEDIA CONTROLS
const togglePlugBtn = document.getElementById('togglePlugBtn');
if (togglePlugBtn) {
  togglePlugBtn.addEventListener('click', async () => {
    try {
      const res = await fetch(`${API_BASE}/api/smart-plug/toggle`, { method: "POST" });
      const data = await res.json();
      const pSt = document.getElementById('plugStatus');
      if (pSt) pSt.textContent = `Main Desk Appliance: ${data.is_on ? "ON" : "OFF"}`;
    } catch (err) {
      console.error("Plug toggle error:", err);
    }
  });
}

const mPlay = document.getElementById('mPlay');
if (mPlay) {
  mPlay.addEventListener('click', async () => {
    await fetch(`${API_BASE}/api/media/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "play_pause" })
    }).catch(() => {});
  });
}
const mPrev = document.getElementById('mPrev');
if (mPrev) {
  mPrev.addEventListener('click', async () => {
    await fetch(`${API_BASE}/api/media/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "prev" })
    }).catch(() => {});
  });
}
const mNext = document.getElementById('mNext');
if (mNext) {
  mNext.addEventListener('click', async () => {
    await fetch(`${API_BASE}/api/media/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "next" })
    }).catch(() => {});
  });
}
const mSearchBtn = document.getElementById('mSearchBtn');
const mSearchInput = document.getElementById('mSearch');
if (mSearchBtn && mSearchInput) {
  mSearchBtn.addEventListener('click', async () => {
    const q = mSearchInput.value.trim();
    if (!q) return;
    await fetch(`${API_BASE}/api/media/play-search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q })
    }).catch(() => {});
  });
}

// 7. PYTHON CODER SANDBOX
const runCoderBtn = document.getElementById('runCoderBtn');
const coderText = document.getElementById('coderText');
const coderOutput = document.getElementById('coderOutput');
const coderStatus = document.getElementById('coderStatus');

if (runCoderBtn && coderText) {
  runCoderBtn.addEventListener('click', async () => {
    const code = coderText.value;
    if (!code) return;
    if (coderStatus) coderStatus.textContent = "Executing...";
    try {
      const res = await fetch(`${API_BASE}/api/coder/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: code })
      });
      const data = await res.json();
      if (coderOutput) {
        coderOutput.textContent = data.output || data.error || "[No Output]";
      }
      if (coderStatus) coderStatus.textContent = data.success ? "Success (0)" : "Error";
    } catch (err) {
      if (coderOutput) coderOutput.textContent = "Execution failed: " + err.message;
      if (coderStatus) coderStatus.textContent = "Failed";
    }
  });
}

// 8. NEURAL CHAT TERMINAL SENDER
const chatInputText = document.getElementById('chatInputText');
const chatSendBtn = document.getElementById('chatSendBtn');
const terminalOutput = document.getElementById('terminalOutput');

async function sendChatMessage() {
  if (!chatInputText) return;
  const text = chatInputText.value.trim();
  if (!text) return;
  chatInputText.value = '';

  if (terminalOutput) {
    const userP = document.createElement('p');
    userP.innerHTML = `<span>$ user:</span> ${escapeHtml(text)}`;
    terminalOutput.appendChild(userP);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
  }

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    });
    const data = await res.json();

    if (terminalOutput && data.text) {
      const jarvisP = document.createElement('p');
      jarvisP.innerHTML = `<span style="color:var(--cyan);">$ jarvis:</span> ${escapeHtml(data.text)}`;
      terminalOutput.appendChild(jarvisP);
      terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    if (data.dynamic_result) {
      mountDynamicUiElement(data.dynamic_result.title, data.dynamic_result.html);
    }
  } catch (err) {
    console.error("Chat error:", err);
  }
}

if (chatSendBtn) chatSendBtn.addEventListener('click', sendChatMessage);
if (chatInputText) chatInputText.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendChatMessage(); });

// 9. INTERACTIVE ARC REACTOR PUSH-TO-TALK
const reactorOrb = document.getElementById('mic-btn');
if (reactorOrb) {
  reactorOrb.addEventListener('click', async () => {
    const st = document.getElementById('status');
    if (st) st.textContent = "Listening... (Speak command now)";
    try {
      await fetch(`${API_BASE}/api/think`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "Hello JARVIS" })
      });
    } catch (err) {
      console.warn("Reactor PTT Ping:", err);
    }
  });
}

// 10. SECURITY SANITIZATION HELPERS
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function sanitizeHtml(raw) {
  if (!raw) return '';
  return String(raw)
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .replace(/<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi, '')
    .replace(/\s+on\w+="[^"]*"/gi, '')
    .replace(/\s+on\w+='[^']*'/gi, '')
    .replace(/href\s*=\s*["']javascript:[^"']*["']/gi, 'href="#"');
}

// ==============================================================================
// 11. BALL KNOWLEDGE TACTICAL SUITE (IPTV, VISION, GEOSLEUTH, SCOUT, OCR, PHONELINK)
// ==============================================================================

// A. IPTV LIVE STREAM PLAYER (iptv-org & Hls.js)
let hlsInstance = null;
let iptvChannels = [];

async function initIptvPlayer() {
  const video = document.getElementById('iptvPlayer');
  if (!video) return;

  try {
    const res = await fetch(`${API_BASE}/api/iptv/channels`);
    const data = await res.json();
    if (data.channels && data.channels.length > 0) {
      iptvChannels = data.channels;
    }
  } catch (err) {
    console.warn("IPTV channels fetch:", err);
  }

  // Load default channel (NASA TV)
  playChannel("nasa");

  // Wire channel switcher buttons
  document.querySelectorAll('.iptv-ch-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.iptv-ch-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const chId = btn.getAttribute('data-ch');
      playChannel(chId);
    });
  });
}

function playChannel(channelId) {
  const video = document.getElementById('iptvPlayer');
  if (!video) return;

  const ch = iptvChannels.find(c => c.id === channelId) || {
    name: "NASA TV — Orbital Stream",
    badge: "ORBITAL // 408 KM",
    url: "https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8"
  };

  const titleEl = document.getElementById('iptvTitle');
  const badgeEl = document.getElementById('iptvBadge');
  if (titleEl) titleEl.textContent = ch.name;
  if (badgeEl) badgeEl.textContent = ch.badge || "LIVE BROADCAST";

  if (window.Hls && Hls.isSupported()) {
    if (hlsInstance) hlsInstance.destroy();
    hlsInstance = new Hls({ enableWorker: true, lowLatencyMode: true });
    hlsInstance.loadSource(ch.url);
    hlsInstance.attachMedia(video);
    hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
      video.play().catch(() => {});
    });
    hlsInstance.on(Hls.Events.ERROR, (event, data) => {
      if (data.fatal) {
        console.warn("HLS fatal error:", data.type);
        hlsInstance.destroy();
      }
    });
  } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = ch.url;
    video.play().catch(() => {});
  }
}

// B. ROBOFLOW SUPERVISION OPTICAL RECON
const visionScanBtn = document.getElementById('visionScanBtn');
if (visionScanBtn) {
  visionScanBtn.addEventListener('click', async () => {
    visionScanBtn.textContent = "[SCANNING SECTOR...]";
    try {
      const res = await fetch(`${API_BASE}/api/vision/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_b64: "" })
      });
      const data = await res.json();
      if (data.annotated_b64) {
        const img = document.getElementById('visionImg');
        const ph = document.getElementById('visionPlaceholder');
        if (img) {
          img.src = data.annotated_b64;
          img.style.display = "block";
        }
        if (ph) ph.style.display = "none";
      }
      const detEl = document.getElementById('visionDetections');
      if (detEl) detEl.textContent = `${data.detections_count || 0} Targets Detected`;
      const resEl = document.getElementById('visionRes');
      if (resEl) resEl.textContent = data.resolution || "640x480";
      const stEl = document.getElementById('visionStatus');
      if (stEl) stEl.textContent = data.sensor_health || "ONLINE";
    } catch (err) {
      console.error("Vision scan error:", err);
    } finally {
      visionScanBtn.textContent = "[SCAN OPTICAL SECTOR]";
    }
  });
}

// C. GEO-SLEUTH OSINT GEOLOCATION
const geoSearchBtn = document.getElementById('geoSearchBtn');
const geoQueryInput = document.getElementById('geoQueryInput');

async function runGeoSleuth() {
  if (!geoQueryInput) return;
  const q = geoQueryInput.value.trim();
  if (!q) return;

  const targetTitle = document.getElementById('geoTargetTitle');
  if (targetTitle) targetTitle.textContent = "Acquiring Coordinates...";

  try {
    const res = await fetch(`${API_BASE}/api/osint/geosleuth`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, query_type: "auto" })
    });
    const data = await res.json();

    if (data.error) {
      if (targetTitle) targetTitle.textContent = "Target Not Found";
      const gName = document.getElementById('geoName');
      if (gName) gName.textContent = data.error;
      return;
    }

    if (targetTitle) targetTitle.textContent = `Target Locked: ${q}`;
    const gCoords = document.getElementById('geoCoords');
    if (gCoords && data.lat !== undefined) gCoords.textContent = `${data.lat.toFixed(5)}, ${data.lon.toFixed(5)}`;
    const gName = document.getElementById('geoName');
    if (gName) gName.textContent = data.display_name || data.resolved_address || q;
    const gLink = document.getElementById('geoOsmLink');
    if (gLink && data.osm_url) {
      gLink.href = data.osm_url;
      gLink.style.display = "inline-block";
    }
  } catch (err) {
    console.error("GeoSleuth error:", err);
    if (targetTitle) targetTitle.textContent = "Error Querying Coordinates";
  }
}

if (geoSearchBtn) geoSearchBtn.addEventListener('click', runGeoSleuth);
if (geoQueryInput) geoQueryInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') runGeoSleuth(); });

// D. SCOUT WEB INTELLIGENCE & LEAD ENGINE
const scoutSearchBtn = document.getElementById('scoutSearchBtn');
const scoutQueryInput = document.getElementById('scoutQueryInput');

async function runScoutRecon() {
  if (!scoutQueryInput) return;
  const target = scoutQueryInput.value.trim();
  if (!target) return;

  const title = document.getElementById('scoutTargetTitle');
  if (title) title.textContent = `Reconnaissance: ${target}...`;

  try {
    const res = await fetch(`${API_BASE}/api/intel/scout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target: target })
    });
    const data = await res.json();

    if (data.error) {
      if (title) title.textContent = "Recon Failed";
      const sSum = document.getElementById('scoutSummary');
      if (sSum) sSum.textContent = data.error;
      return;
    }

    if (title) title.textContent = `Scout Recon: ${data.target}`;
    const sScore = document.getElementById('scoutScore');
    if (sScore) sScore.textContent = data.lead_score || "N/A";
    const sEmails = document.getElementById('scoutEmailsCount');
    if (sEmails) sEmails.textContent = (data.emails ? data.emails.length : 0);

    const sTags = document.getElementById('scoutTechTags');
    if (sTags) {
      sTags.innerHTML = '';
      const techs = (data.technologies && data.technologies.length > 0) ? data.technologies : ["Proprietary Stack"];
      techs.forEach(t => {
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.style.fontSize = '9px';
        badge.textContent = t;
        sTags.appendChild(badge);
      });
    }

    const sSum = document.getElementById('scoutSummary');
    if (sSum) sSum.textContent = data.summary || data.description || "Reconnaissance complete.";
  } catch (err) {
    console.error("Scout error:", err);
    if (title) title.textContent = "Recon Error";
  }
}

if (scoutSearchBtn) scoutSearchBtn.addEventListener('click', runScoutRecon);
if (scoutQueryInput) scoutQueryInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') runScoutRecon(); });

// E. PHONELINK DEVICE CONTROLLER
async function syncPhoneStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/phone/status`);
    const data = await res.json();
    if (data.device_name) {
      const pName = document.getElementById('phoneName');
      if (pName) pName.textContent = data.device_name;
      const pDesc = document.getElementById('phoneStatusDesc');
      if (pDesc) pDesc.textContent = `● ${data.status} (${data.carrier || "5G"})`;
      const pBat = document.getElementById('phoneBatteryMeter');
      if (pBat) pBat.style.width = `${data.battery || 85}%`;
    }
  } catch (err) {
    console.warn("PhoneLink sync:", err);
  }
}

const phonePingBtn = document.getElementById('phonePingBtn');
if (phonePingBtn) {
  phonePingBtn.addEventListener('click', async () => {
    const res = await fetch(`${API_BASE}/api/phone/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "ping" })
    });
    const data = await res.json();
    const out = document.getElementById('phoneActionResult');
    if (out) out.textContent = data.message || "Ping alert sent.";
  });
}

const phoneClipBtn = document.getElementById('phoneClipBtn');
if (phoneClipBtn) {
  phoneClipBtn.addEventListener('click', async () => {
    const res = await fetch(`${API_BASE}/api/phone/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "sync_clipboard" })
    });
    const data = await res.json();
    const out = document.getElementById('phoneActionResult');
    if (out) out.textContent = data.message || "Clipboard beamed to mobile.";
  });
}

const phoneQrBtn = document.getElementById('phoneQrBtn');
if (phoneQrBtn) {
  phoneQrBtn.addEventListener('click', async () => {
    const res = await fetch(`${API_BASE}/api/phone/qr`, { method: "POST" });
    const data = await res.json();
    const out = document.getElementById('phoneActionResult');
    if (out) out.textContent = data.message || "QR Code generated.";
  });
}

// F. UNLIMITED-OCR EXTRACTION
const ocrFileInput = document.getElementById('ocrFileInput');
const ocrUploadBtn = document.getElementById('ocrUploadBtn');
const ocrDemoBtn = document.getElementById('ocrDemoBtn');
const ocrResultBox = document.getElementById('ocrResultBox');

if (ocrUploadBtn && ocrFileInput) {
  ocrUploadBtn.addEventListener('click', () => ocrFileInput.click());
  ocrFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (ocrResultBox) ocrResultBox.textContent = `Processing '${file.name}' with Unlimited-OCR engine...`;

    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/vision/ocr`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_b64: reader.result, filename: file.name })
        });
        const data = await res.json();
        if (ocrResultBox) ocrResultBox.textContent = data.text || JSON.stringify(data, null, 2);
      } catch (err) {
        if (ocrResultBox) ocrResultBox.textContent = "OCR error: " + err.message;
      }
    };
    reader.readAsDataURL(file);
  });
}

if (ocrDemoBtn) {
  ocrDemoBtn.addEventListener('click', async () => {
    if (ocrResultBox) ocrResultBox.textContent = "Running Unlimited-OCR synthetic document parse...";
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 400;
      canvas.height = 160;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#0a0d11';
      ctx.fillRect(0, 0, 400, 160);
      ctx.fillStyle = '#4dd8ff';
      ctx.font = '16px monospace';
      ctx.fillText("JARVIS SYSTEM LOG // LEVEL 1", 20, 40);
      ctx.fillText("All telemetry lines nominal.", 20, 80);
      ctx.fillText("Optical link: STABLE // 2026", 20, 120);

      const b64 = canvas.toDataURL('image/png');
      const res = await fetch(`${API_BASE}/api/vision/ocr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_b64: b64, filename: "demo_log.png" })
      });
      const data = await res.json();
      if (ocrResultBox) ocrResultBox.textContent = data.text || JSON.stringify(data, null, 2);
    } catch (err) {
      if (ocrResultBox) ocrResultBox.textContent = "OCR Demo error: " + err.message;
    }
  });
}

// INITIALIZE
fetchInitialTelemetry();
syncPhoneStatus();
initIptvPlayer();
connectWebSocket();
setInterval(fetchInitialTelemetry, 10000);
setInterval(syncPhoneStatus, 15000);

// ==============================================================================
// INDUSTRIAL SRE OPERATOR SUITE: COMMAND PALETTE & HEALTH MONITORING
// ==============================================================================
const cmdPaletteModal = document.getElementById('cmdPaletteModal');
const cmdPaletteInput = document.getElementById('cmdPaletteInput');
const cmdPaletteList = document.getElementById('cmdPaletteList');
const diagModal = document.getElementById('diagModal');

const PALETTE_COMMANDS = [
  { title: "Arc Reactor // Central Neural Hub", cat: "Jump", target: "#mic-btn", desc: "Digital clock, Arc Reactor, and generative synthesis." },
  { title: "Dynamic UI Section // Generative Elements", cat: "Jump", target: "#dynamicSection", desc: "Autonomous on-demand synthesized widgets." },
  { title: "Hardware Matrix // SRE Telemetry", cat: "Jump", target: "#hwGrid", desc: "Live CPU, RAM, GPU, thermals and bandwidth." },
  { title: "Smart Home Matrix // Local IoT", cat: "Jump", target: "#homeSection", desc: "TP-Link Kasa smart plug & studio illumination." },
  { title: "Markets & F1 // Real-Time Intelligence", cat: "Jump", target: "#marketSection", desc: "Binance BTC spot ticker & Formula 1 telemetry." },
  { title: "IPTV Live Feeds // Global Television", cat: "Jump", target: "#iptvSection", desc: "International streaming broadcast channels." },
  { title: "Optical Recon // Computer Vision", cat: "Jump", target: "#visionSection", desc: "Webcam live analysis & optical OCR." },
  { title: "OSINT Intelligence // Target Recon", cat: "Jump", target: "#osintSection", desc: "Domain scout & Geo-Sleuth geolocation." },
  { title: "Coder Sandbox // Isolated Python", cat: "Jump", target: "#coderSection", desc: "Run Python scripts inside secure sandbox." },
  { title: "PhoneLink // Mobile Synchronization", cat: "Jump", target: "#phoneSection", desc: "Inspect connected mobile status and push notes." },
  { title: "⚡ Synthesize Dynamic UI Element", cat: "Action", action: "synth_prompt", desc: "Generate a custom frontend component on demand." },
  { title: "🔍 Inspect SRE Deep Health Matrix", cat: "SRE", action: "open_health", desc: "View SQLite WAL latency, port checks, and hardware thresholds." },
  { title: "📊 Open Prometheus Metrics (/metrics)", cat: "SRE", action: "open_metrics", desc: "View Prometheus exposition telemetry format." },
  { title: "🛑 Trigger Immediate Emergency Halt", cat: "Safety", action: "emergency_halt", desc: "Suspend all background execution threads." }
];

let selectedPaletteIndex = 0;
let filteredCommands = [...PALETTE_COMMANDS];

function openCommandPalette() {
  if (!cmdPaletteModal) return;
  cmdPaletteModal.style.display = 'flex';
  cmdPaletteInput.value = '';
  filterPalette('');
  setTimeout(() => cmdPaletteInput.focus(), 50);
}

function closeCommandPalette() {
  if (!cmdPaletteModal) return;
  cmdPaletteModal.style.display = 'none';
}

function renderPaletteList() {
  if (!cmdPaletteList) return;
  cmdPaletteList.innerHTML = '';
  filteredCommands.forEach((cmd, idx) => {
    const item = document.createElement('div');
    item.style.padding = '8px 14px';
    item.style.display = 'flex';
    item.style.alignItems = 'center';
    item.style.justifyContent = 'space-between';
    item.style.cursor = 'pointer';
    item.style.borderLeft = idx === selectedPaletteIndex ? '3px solid #4dd8ff' : '3px solid transparent';
    item.style.background = idx === selectedPaletteIndex ? 'rgba(77,216,255,0.12)' : 'transparent';
    item.innerHTML = `
      <div>
        <div style="color:${idx === selectedPaletteIndex ? '#4dd8ff' : '#e2e8f0'}; font-weight:600; font-size:12px;">${cmd.title}</div>
        <div style="color:var(--muted); font-size:10px; margin-top:2px;">${cmd.desc}</div>
      </div>
      <span style="font-size:9px; color:var(--cyan); border:1px solid rgba(77,216,255,0.3); padding:2px 6px; border-radius:3px;">${cmd.cat}</span>
    `;
    item.addEventListener('mouseenter', () => {
      selectedPaletteIndex = idx;
      renderPaletteList();
    });
    item.addEventListener('click', () => executePaletteCommand(cmd));
    cmdPaletteList.appendChild(item);
  });
}

function filterPalette(query) {
  const q = query.toLowerCase().trim();
  if (!q) {
    filteredCommands = [...PALETTE_COMMANDS];
  } else {
    filteredCommands = PALETTE_COMMANDS.filter(c => 
      c.title.toLowerCase().includes(q) || 
      c.desc.toLowerCase().includes(q) ||
      c.cat.toLowerCase().includes(q)
    );
  }
  selectedPaletteIndex = 0;
  renderPaletteList();
}

function executePaletteCommand(cmd) {
  closeCommandPalette();
  if (cmd.target) {
    const el = document.querySelector(cmd.target);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  } else if (cmd.action === "synth_prompt") {
    const prompt = window.prompt("Enter requested UI component to synthesize (e.g., 'Workout tracker', 'Mortgage calculator'):");
    if (prompt) {
      const inp = document.getElementById('genUiPrompt');
      if (inp) {
        inp.value = prompt;
        const btn = document.getElementById('genUiSubmit');
        if (btn) btn.click();
      }
    }
  } else if (cmd.action === "open_health") {
    openHealthModal();
  } else if (cmd.action === "open_metrics") {
    window.open('/metrics', '_blank');
  } else if (cmd.action === "emergency_halt") {
    triggerEmergencyHalt();
  }
}

if (cmdPaletteInput) {
  cmdPaletteInput.addEventListener('input', (e) => filterPalette(e.target.value));
  cmdPaletteInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (filteredCommands.length > 0) {
        selectedPaletteIndex = (selectedPaletteIndex + 1) % filteredCommands.length;
        renderPaletteList();
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (filteredCommands.length > 0) {
        selectedPaletteIndex = (selectedPaletteIndex - 1 + filteredCommands.length) % filteredCommands.length;
        renderPaletteList();
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredCommands[selectedPaletteIndex]) {
        executePaletteCommand(filteredCommands[selectedPaletteIndex]);
      }
    } else if (e.key === 'Escape') {
      closeCommandPalette();
    }
  });
}

window.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    if (cmdPaletteModal && cmdPaletteModal.style.display === 'flex') {
      closeCommandPalette();
    } else {
      openCommandPalette();
    }
  } else if (e.key === 'Escape') {
    closeCommandPalette();
    closeHealthModal();
  }
});

const cmdTriggerBtn = document.getElementById('cmdPaletteTriggerBtn');
if (cmdTriggerBtn) cmdTriggerBtn.addEventListener('click', openCommandPalette);

let lastHealthData = null;
function openHealthModal() {
  if (!diagModal) return;
  diagModal.style.display = 'flex';
  updateHealthModalUI(lastHealthData);
  fetchHealthData();
}

function closeHealthModal() {
  if (!diagModal) return;
  diagModal.style.display = 'none';
}

function updateHealthModalUI(data) {
  const body = document.getElementById('diagModalBody');
  if (!body) return;
  if (!data) {
    body.innerHTML = '<div style="padding:20px; color:var(--muted); text-align:center;">Querying neural diagnostic probes...</div>';
    return;
  }
  const chk = data.checks || {};
  const db = chk.database || {};
  const gev = chk.gods_eye_view || {};
  const hw = chk.hardware || {};
  const ws = chk.websockets || {};

  const statusColor = data.status === 'NOMINAL' ? '#3cff8c' : (data.status === 'DEGRADED' ? '#ffb84d' : '#ff5d6c');

  body.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid rgba(77,216,255,0.2); padding-bottom:10px;">
      <div>
        <span style="font-size:11px; color:var(--muted);">SYSTEM HEALTH STATUS:</span>
        <span style="font-size:14px; font-weight:bold; color:${statusColor}; margin-left:8px;">● ${data.status}</span>
      </div>
      <div style="font-size:11px; color:var(--muted);">Uptime: <b style="color:#fff;">${data.uptime_hours || 0} hrs</b></div>
    </div>

    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:11px;">
      <div style="background:rgba(77,216,255,0.06); padding:10px; border-radius:5px; border:1px solid rgba(77,216,255,0.15);">
        <div style="color:var(--cyan); font-weight:bold; margin-bottom:6px;">◈ SQLite Persistence (WAL)</div>
        <div>Status: <b style="color:#3cff8c;">${db.status || 'OK'}</b></div>
        <div>Journal Mode: <b style="color:#fff;">${db.journal_mode || 'wal'}</b></div>
        <div>Query Latency: <b style="color:#fff;">${db.latency_ms || 0} ms</b></div>
      </div>

      <div style="background:rgba(77,216,255,0.06); padding:10px; border-radius:5px; border:1px solid rgba(77,216,255,0.15);">
        <div style="color:var(--cyan); font-weight:bold; margin-bottom:6px;">◈ God's Eye View (Vite 5173)</div>
        <div>Status: <b style="color:${gev.status === 'ONLINE' ? '#3cff8c' : '#ffb84d'};">${gev.status || 'ONLINE'}</b></div>
        <div>Port: <b style="color:#fff;">${gev.port || 5173}</b></div>
        <div>Probe Latency: <b style="color:#fff;">${gev.latency_ms || 0} ms</b></div>
      </div>

      <div style="background:rgba(77,216,255,0.06); padding:10px; border-radius:5px; border:1px solid rgba(77,216,255,0.15);">
        <div style="color:var(--cyan); font-weight:bold; margin-bottom:6px;">◈ Host Hardware Thresholds</div>
        <div>CPU Load: <b style="color:#fff;">${hw.cpu_pct || 0}%</b></div>
        <div>RAM Used: <b style="color:#fff;">${hw.ram_pct || 0}%</b></div>
        <div>Disk Root: <b style="color:#fff;">${hw.disk_pct || 0}%</b></div>
      </div>

      <div style="background:rgba(77,216,255,0.06); padding:10px; border-radius:5px; border:1px solid rgba(77,216,255,0.15);">
        <div style="color:var(--cyan); font-weight:bold; margin-bottom:6px;">◈ Real-Time EventBus WebSockets</div>
        <div>Status: <b style="color:#3cff8c;">${ws.status || 'HEALTHY'}</b></div>
        <div>Connected Clients: <b style="color:#fff;">${ws.active_clients || 1}</b></div>
        <div>Heartbeat Ping: <b style="color:#fff;">&lt; 5 ms</b></div>
      </div>
    </div>

    <div style="margin-top:14px; display:flex; justify-content:space-between; align-items:center;">
      <a href="/metrics" target="_blank" style="color:var(--cyan); font-size:11px; text-decoration:none;">[View Full Prometheus Telemetry (/metrics) ↗]</a>
      <button onclick="triggerEmergencyHalt()" style="background:rgba(255,93,108,0.2); border:1px solid #ff5d6c; color:#ff5d6c; padding:5px 12px; border-radius:4px; font-size:10px; font-weight:bold; cursor:pointer;">[EMERGENCY HALT]</button>
    </div>
  `;
}

const healthBadge = document.getElementById('systemHealthBadge');
if (healthBadge) healthBadge.addEventListener('click', openHealthModal);

async function fetchHealthData() {
  try {
    const res = await fetch('/api/health');
    if (res.ok) {
      const data = await res.json();
      lastHealthData = data;
      const textEl = document.getElementById('systemHealthText');
      const dotEl = document.getElementById('systemHealthDot');
      if (textEl && dotEl && healthBadge) {
        textEl.textContent = data.status;
        if (data.status === 'NOMINAL') {
          healthBadge.style.color = '#3cff8c';
          healthBadge.style.borderColor = '#3cff8c';
          healthBadge.style.background = 'rgba(60,255,140,0.12)';
          dotEl.style.background = '#3cff8c';
          dotEl.style.boxShadow = '0 0 6px #3cff8c';
        } else if (data.status === 'DEGRADED') {
          healthBadge.style.color = '#ffb84d';
          healthBadge.style.borderColor = '#ffb84d';
          healthBadge.style.background = 'rgba(255,184,77,0.12)';
          dotEl.style.background = '#ffb84d';
          dotEl.style.boxShadow = '0 0 6px #ffb84d';
        } else {
          healthBadge.style.color = '#ff5d6c';
          healthBadge.style.borderColor = '#ff5d6c';
          healthBadge.style.background = 'rgba(255,93,108,0.12)';
          dotEl.style.background = '#ff5d6c';
          dotEl.style.boxShadow = '0 0 6px #ff5d6c';
        }
      }
      if (diagModal && diagModal.style.display === 'flex') {
        updateHealthModalUI(data);
      }
    }
  } catch (e) {
    console.warn("Health poll error:", e);
  }
}

fetchHealthData();
setInterval(fetchHealthData, 10000);

window.triggerEmergencyHalt = async function() {
  if (!confirm("CONFIRM EMERGENCY SYSTEM HALT: This will suspend background worker execution and log an immediate critical audit event.")) return;
  try {
    const res = await fetch('/api/system/emergency-halt', { method: 'POST' });
    if (res.ok) {
      alert("CRITICAL HALT EXECUTED: All background subsystems suspended. Event logged to Data/audit.jsonl with SHA-256 integrity seal.");
      const textEl = document.getElementById('systemHealthText');
      if (textEl) textEl.textContent = 'HALTED';
    }
  } catch (e) {
    alert("Halt dispatch error: " + e.message);
  }
};

const haltBtn = document.getElementById('emergencyHaltBtn');
if (haltBtn) haltBtn.addEventListener('click', window.triggerEmergencyHalt);
