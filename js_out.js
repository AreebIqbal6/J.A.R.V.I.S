
  document.querySelectorAll('.shell-controls button[data-mode]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      document.querySelectorAll('.shell-controls button[data-mode]').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
      document.getElementById('screen-'+btn.dataset.mode).classList.add('active');
      document.getElementById('vrSubControls').style.display = (btn.dataset.mode==='vr') ? 'flex' : 'none';
      placeTicks();
    });
  });
  document.getElementById('fsBtn').addEventListener('click', ()=>{
    if(!document.fullscreenElement){ document.documentElement.requestFullscreen().catch(()=>{}); }
    else{ document.exitFullscreen(); }
  });

  function tick(){
    const now = new Date();
    const hh = String(now.getHours()).padStart(2,'0');
    const mm = String(now.getMinutes()).padStart(2,'0');
    document.getElementById('clockTime').textContent = hh+':'+mm;
    const days=['SUNDAY','MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY'];
    const months=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    document.getElementById('clockDate').textContent = days[now.getDay()]+' · '+now.getDate()+' '+months[now.getMonth()];
  }
  tick(); setInterval(tick, 15000);

  const panels = {
    chat:document.getElementById('panelChat'), camera:document.getElementById('panelCam'),
    music:document.getElementById('panelMusic'), brief:document.getElementById('panelBrief'),
    diag:document.getElementById('panelDiag'), home:document.getElementById('panelHome'),
    data:document.getElementById('panelData'), security:document.getElementById('panelSecurity'),
    comms:document.getElementById('panelComms'), coder:document.getElementById('panelCoder'),
    dynamic:document.getElementById('panelDynamic')
  };
  const idleStack = document.getElementById('idleStack');
  const dockBtns = document.querySelectorAll('.dock-btn');
  function setMode(mode){
    dockBtns.forEach(b=>b.classList.toggle('active', b.dataset.mode===mode));
    Object.entries(panels).forEach(([key,el])=>el.classList.toggle('show', key===mode));
    if(mode==='idle'){ idleStack.style.opacity=1; idleStack.style.transform='translate(-50%,-50%)'; }
    else{ idleStack.style.opacity=0; idleStack.style.transform='translate(-50%,-58%)'; }
  }
  dockBtns.forEach(btn=>btn.addEventListener('click', ()=>setMode(btn.dataset.mode)));

  document.querySelectorAll('#dockDots .dot').forEach(dot=>{
    dot.addEventListener('click', ()=>{
      const page = dot.dataset.page;
      document.querySelectorAll('#dockDots .dot').forEach(d=>d.classList.toggle('active', d===dot));
      document.querySelectorAll('#dockWidget .dock-page').forEach(p=>{ p.hidden = (p.dataset.page!==page); });
    });
  });
  // jump dock to the page containing whichever mode was just activated
  function revealDockPage(mode){
    const btn = document.querySelector(`.dock-btn[data-mode="${mode}"]`);
    if(!btn) return;
    const page = btn.closest('.dock-page');
    if(!page) return;
    document.querySelectorAll('#dockWidget .dock-page').forEach(p=>{ p.hidden = (p!==page); });
    document.querySelectorAll('#dockDots .dot').forEach(d=>d.classList.toggle('active', d.dataset.page===page.dataset.page));
  }

  const schematicWindow = document.getElementById('schematicWindow');
  const mapView = document.getElementById('mapView');
  const trackerWindow = document.getElementById('trackerWindow');
  document.querySelectorAll('#vrSubControls button').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      document.querySelectorAll('#vrSubControls button').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      const m = btn.dataset.vrmode;
      
      mapView.classList.remove('show');
      schematicWindow.style.opacity = 0; schematicWindow.style.pointerEvents = 'none';
      if(trackerWindow) { trackerWindow.style.opacity = 0; trackerWindow.style.pointerEvents = 'none'; }

      if(m==='map'){
        mapView.classList.add('show');
        if(!mapEntered){
          mapEntered = true;
          initKarachiMap();
          setTimeout(()=>flyToKarachi('quaid'), 900);
        } else {
          setTimeout(()=>karachiMap && karachiMap.invalidateSize(), 50);
        }
      }
      else if(m==='tracker'){
        if(trackerWindow) { trackerWindow.style.opacity = 1; trackerWindow.style.pointerEvents = 'auto'; }
        if(!trackerMapEntered){
          trackerMapEntered = true;
          initTrackerMap();
        } else {
          setTimeout(()=>trackerMap && trackerMap.invalidateSize(), 50);
        }
      }
      else { 
        schematicWindow.style.opacity=1; schematicWindow.style.pointerEvents='auto'; 
      }
    });
  });

  /* ---------------- Earth Tracker Map ---------------- */
  let trackerMapEntered = false;
  let trackerMap = null;
  let trackerMarkers = [];

  function initTrackerMap(){
    if(trackerMap || typeof L === 'undefined'){
      if(typeof L === 'undefined') {
        const errNote = document.getElementById('trackerOfflineNote');
        if(errNote) errNote.style.display = 'block';
      }
      return;
    }
    try{
      trackerMap = L.map('trackerMap', { zoomControl:false, attributionControl:false, worldCopyJump:true }).setView([20, 0], 2);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(trackerMap);
      setTimeout(()=>trackerMap.invalidateSize(), 60);
    }catch(e){
      const errNote = document.getElementById('trackerOfflineNote');
      if(errNote) errNote.style.display = 'block';
    }
  }

  /* ---------------- real map: Karachi, Pakistan (Leaflet + CARTO dark tiles) ---------------- */
  let mapEntered = false;
  let karachiMap = null;
  let currentMarker = null;

  const KARACHI_LOCATIONS = {
    world:     { lat:24.8607, lng:67.0011, zoom:11, label:null },
    quaid:     { lat:24.8534, lng:67.0295, zoom:16, label:'Mazar-e-Quaid' },
    clifton:   { lat:24.8138, lng:67.0293, zoom:15, label:'Clifton Beach' },
    dodarya:   { lat:24.8067, lng:67.0344, zoom:16, label:'Do Darya, Boat Basin' },
    saddar:    { lat:24.8570, lng:67.0180, zoom:16, label:'Empress Market, Saddar' },
    portgrand: { lat:24.8266, lng:66.9799, zoom:16, label:'Port Grand' },
  };

  function initKarachiMap(){
    if(karachiMap || typeof L === 'undefined'){
      if(typeof L === 'undefined') document.getElementById('mapOfflineNote').classList.add('show');
      return;
    }
    try{
      karachiMap = L.map('leafletMap', { zoomControl:true, attributionControl:true, worldCopyJump:true })
        .setView([KARACHI_LOCATIONS.world.lat, KARACHI_LOCATIONS.world.lng], KARACHI_LOCATIONS.world.zoom);
      const tiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd', maxZoom: 19
      });
      tiles.on('tileerror', ()=>document.getElementById('mapOfflineNote').classList.add('show'));
      tiles.addTo(karachiMap);
      setTimeout(()=>karachiMap.invalidateSize(), 60);
    }catch(e){ document.getElementById('mapOfflineNote').classList.add('show'); }
  }

  function flyToKarachi(key){
    const loc = KARACHI_LOCATIONS[key];
    if(!loc || !karachiMap) return;
    karachiMap.flyTo([loc.lat, loc.lng], loc.zoom, { duration: 2.1, easeLinearity: 0.25 });
    if(currentMarker){ karachiMap.removeLayer(currentMarker); currentMarker = null; }
    if(loc.label){
      const icon = L.divIcon({
        className:'', iconSize:[14,14], iconAnchor:[7,7],
        html:`<div class="map-tag-icon selected" style="transform:translate(10px,-6px)"><span class="flight-marker"></span><span class="label">${loc.label}</span></div>`
      });
      currentMarker = L.marker([loc.lat, loc.lng], { icon }).addTo(karachiMap);
    }
    document.querySelectorAll('.map-result').forEach(b=>b.classList.toggle('active', b.dataset.loc===key));
  }

  document.querySelectorAll('.map-result').forEach(btn=>{
    btn.addEventListener('click', ()=>flyToKarachi(btn.dataset.loc));
  });

  function placeTicks(){
    document.querySelectorAll('.orb-wrap').forEach(orb=>{
      orb.querySelectorAll('.tick').forEach(t=>t.remove());
      const w = orb.getBoundingClientRect().width;
      const r = w/2 + 14;
      for(let i=0;i<8;i++){
        const angle = i*45;
        const el = document.createElement('div');
        el.className = (i%2===0) ? 'tick' : 'tick dot';
        el.style.transform = `translate(-50%,-50%) rotate(${angle}deg) translateY(-${r}px)`;
        orb.appendChild(el);
      }
    });
  }
  placeTicks();
  window.addEventListener('resize', placeTicks);

  /* ============================================================
     JARVIS LIVE DATA ENGINE
     All data is fetched from the FastAPI backend via WebSockets
     ============================================================ */
  const API = 'http://localhost:8000/api';
  let ws;
  let reconnectTimer;

  function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8000/api/ws/hud');
    
    ws.onopen = () => {
      console.log('JARVIS WebSocket connected.');
      // Update UI offline states to online if needed
      document.querySelectorAll('.panel').forEach(p => p.style.filter = 'none');
      document.getElementById('clockDate').textContent = new Date().toDateString().toUpperCase();
    };

    ws.onclose = () => {
      console.warn('JARVIS WebSocket disconnected. Reconnecting in 3s...');
      document.querySelectorAll('.panel').forEach(p => p.style.filter = 'grayscale(0.6) brightness(0.6)');
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWebSocket, 3000);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleSocketMessage(payload.type, payload.data);
      } catch (e) {
        console.error('Error parsing WS message:', e);
      }
    };
  }

  function handleSocketMessage(type, d) {
    if (type === 'diagnostics') {
      setGauge(gauges.cpu, d.cpu, '%');
      setGauge(gauges.gpu, d.gpu, '%');
      setGauge(gauges.ram, d.ram, '%');
      const tempPct = Math.min(100, (d.core_temp / 100) * 100);
      setGauge(gauges.temp, tempPct, '°C');
      gauges.temp.querySelector('.gauge-value .num').textContent = Math.round(d.core_temp);
      
      netHistory.shift();
      netHistory.push(d.net_down_mbps);
      drawNet();
      document.getElementById('netVal').textContent = `${d.net_down_mbps.toFixed(0)} Mb/s ↓ · ${d.net_up_mbps.toFixed(0)} Mb/s ↑`;
    } 
    else if (type === 'media') {
      const titleEl = document.querySelector('.track-title');
      const artistEl = document.querySelector('.track-artist');
      const statusEl = document.querySelector('.music-status');
      const fillEl = document.querySelector('.track-progress .fill');
      const timesEl = document.querySelectorAll('.times span');
      const playBtn = document.querySelector('.transport .play');

      if(d.playing && titleEl){
        titleEl.textContent = d.title || 'Unknown';
        artistEl.textContent = d.artist || 'Unknown Artist';
        statusEl.textContent = d.status === 'Playing' ? 'PLAYING' : (d.status || 'PAUSED');
        if(d.duration_sec > 0){
          const pct = (d.position_sec / d.duration_sec) * 100;
          fillEl.style.width = pct + '%';
          const fmtTime = (s) => `${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
          if(timesEl.length >= 2){ timesEl[0].textContent = fmtTime(d.position_sec); timesEl[1].textContent = fmtTime(d.duration_sec); }
        }
        if(playBtn) playBtn.textContent = d.status === 'Playing' ? '⏸' : '▶';
      } else if (titleEl) {
        statusEl.textContent = 'NO MEDIA';
      }
    }
    else if (type === 'crypto') {
      if(d.price){
        const obHead = document.querySelector('.ob-head');
        if(obHead) obHead.textContent = `ORDER BOOK — ${d.symbol}`;
        const obContainer = document.querySelector('[data-view="quant"] .orderbook');
        if(obContainer && d.asks && d.bids){
          let obHtml = `<div class="ob-head">ORDER BOOK — ${d.symbol}</div>`;
          d.asks.slice(0,3).reverse().forEach(a => { obHtml += `<div class="ob-row ask"><span>${Math.round(a.price).toLocaleString()}</span><span>${a.qty.toFixed(3)}</span></div>`; });
          d.bids.slice(0,3).forEach(b => { obHtml += `<div class="ob-row bid"><span>${Math.round(b.price).toLocaleString()}</span><span>${b.qty.toFixed(3)}</span></div>`; });
          obContainer.innerHTML = obHtml;
        }
        const pnlRow = document.querySelector('.pnl-row');
        if(pnlRow){
          const dir = d.change_pct >= 0 ? 'up' : 'down';
          const sign = d.change_pct >= 0 ? '+' : '';
          pnlRow.innerHTML = `BTC/USDT · <b>$${Math.round(d.price).toLocaleString()}</b> · <span class="pnl-val ${dir}">${sign}${d.change_pct.toFixed(2)}% (24h)</span>`;
        }
      }
    }
    else if (type === 'f1_telemetry') {
      if(document.getElementById('panelData').classList.contains('show')){
        setRpm(d.rpm_pct);
        document.getElementById('gearNum').textContent = d.gear;
        document.getElementById('speedNum').textContent = d.speed;
      }
    }
    else if (type === 'security_log') {
      if(d.events && d.events.length > 0){
        const secLog = document.querySelector('.sec-log');
        if(secLog) secLog.innerHTML = d.events.map(ev => `<div class="sec-row${ev.warn ? ' warn' : ''}">${ev.time} — ${ev.warn ? '⚠ ' : ''}${ev.text}</div>`).join('');
      }
    }
    else if (type === 'markets') {
      if(d.tickers && d.tickers.length > 0){
        document.querySelector('.ticker-bar').innerHTML = d.tickers.map(t => {
          const dir = t.change_pct >= 0 ? 'up' : 'down';
          const sign = t.change_pct >= 0 ? '+' : '';
          return `<span>${t.name} <b>${t.value.toLocaleString()}</b> <span class="${dir}">${sign}${t.change_pct}%</span></span>`;
        }).join('');
      }
    }
    else if (type === 'briefing') {
      const weather = d.weather || {};
      const news = d.news || {};
      const briefText = document.querySelector('.brief-text');
      if(briefText){
        let html = `<b>Good to see you, Sir.</b> I am online and ready.<br/>`;
        if(weather.temp_c) html += `• Weather in ${weather.city}: ${weather.description}, ${weather.temp_c}°C (feels like ${weather.feels_like_c}°C).<br/>`;
        if(news.headlines && news.headlines.length > 0){
          html += `• <b>Top Headlines:</b><br/>`;
          news.headlines.slice(0,3).forEach(h => html += `&nbsp;&nbsp;→ ${h.title}<br/>`);
        }
        briefText.innerHTML = html;
      }
      if(news.headlines && news.headlines.length > 0){
        const breakingBar = document.querySelector('.breaking-bar');
        if(breakingBar) breakingBar.textContent = news.headlines[0].title.toUpperCase();
      }
    }
    else if (type === 'earth_tracker') {
      if(trackerMap && d.events) {
        trackerMarkers.forEach(m => trackerMap.removeLayer(m));
        trackerMarkers = [];
        d.events.forEach(ev => {
          const icon = L.divIcon({
            className:'', iconSize:[10,10], iconAnchor:[5,5],
            html:`<div class="map-tag-icon selected" style="transform:translate(8px,-4px)"><span class="flight-marker" style="background:#ff5d6c;box-shadow:0 0 10px #ff5d6c"></span><span class="label" style="font-size:9px;color:#ff5d6c;white-space:nowrap;">${ev.title}</span></div>`
          });
          const m = L.marker([ev.lat, ev.lng], { icon }).addTo(trackerMap);
          trackerMarkers.push(m);
        });
      }
    }
  }

  // Connect on load
  window.JARVIS_SOCKET = connectWebSocket;
  connectWebSocket();

  /* ============================================================
     1. Diagnostics Helpers
     ============================================================ */
  const GAUGE_R = 42, GAUGE_C = 2 * Math.PI * GAUGE_R;
  function setGauge(el, pct, suffix){
    if(!el) return;
    const fill = el.querySelector('.gauge-fill');
    fill.style.strokeDasharray = `${GAUGE_C} ${GAUGE_C}`;
    fill.style.strokeDashoffset = GAUGE_C * (1 - pct/100);
    el.classList.toggle('warn', pct>=70 && pct<88);
    el.classList.toggle('crit', pct>=88);
    el.querySelector('.gauge-value .num').textContent = Math.round(pct);
    if(suffix) el.querySelector('.gauge-value .pct').textContent = suffix;
  }
  const gauges = { cpu: document.getElementById('gaugeCpu'), gpu: document.getElementById('gaugeGpu'), ram: document.getElementById('gaugeRam'), temp: document.getElementById('gaugeTemp') };
  Object.values(gauges).forEach(g => { if(g) setGauge(g, parseFloat(g.dataset.pct)); });
  
  let netHistory = Array.from({length:30}, ()=>0);
  function drawNet(){
    const w=300,h=44, maxVal = Math.max(1, ...netHistory), step = w/(netHistory.length-1);
    const pts = netHistory.map((v,i)=>`${(i*step).toFixed(1)},${(h-(v/maxVal*h*0.9)).toFixed(1)}`);
    document.getElementById('netLine').setAttribute('points', pts.join(' '));
    document.getElementById('netFill').setAttribute('points', `0,${h} `+pts.join(' ')+` ${w},${h}`);
  }

  /* ============================================================
     2. Smart Home
     ============================================================ */
  document.querySelectorAll('.toggle').forEach(t=>{
    t.addEventListener('click', ()=>t.classList.toggle('on')); // Keep optimistic UI
  });
  const THERMO_R = 50, THERMO_C = 2*Math.PI*THERMO_R;
  let thermoTemp = 23;
  function drawThermo(){
    const pct = Math.max(0, Math.min(1, (thermoTemp-16)/(30-16)));
    const fill = document.getElementById('thermoFill');
    fill.style.strokeDasharray = `${THERMO_C} ${THERMO_C}`;
    fill.style.strokeDashoffset = THERMO_C*(1-pct);
    document.getElementById('thermoTemp').textContent = thermoTemp+'°';
  }
  drawThermo();
  document.querySelectorAll('.thermo-btns button').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      thermoTemp = Math.max(16, Math.min(30, thermoTemp + parseInt(btn.dataset.delta,10)));
      drawThermo();
    });
  });

  /* ============================================================
     3. F1 Helpers & Candlestick
     ============================================================ */
  document.querySelectorAll('.data-tab').forEach(tab=>{
    tab.addEventListener('click', ()=>{
      document.querySelectorAll('.data-tab').forEach(t=>t.classList.toggle('active', t===tab));
      document.querySelectorAll('.data-view').forEach(v=>v.hidden = (v.dataset.view!==tab.dataset.tab));
    });
  });

  const rpmBar = document.getElementById('rpmBar');
  const RPM_SEGS = 20;
  for(let i=0;i<RPM_SEGS;i++){ const s=document.createElement('div'); s.className='rpm-seg'; rpmBar.appendChild(s); }
  function setRpm(pct){
    const segs = rpmBar.children;
    const active = Math.floor((pct/100) * RPM_SEGS);
    for(let i=0; i<RPM_SEGS; i++){
      segs[i].className = 'rpm-seg';
      if(i < active){
        segs[i].classList.add('on');
        if(i > RPM_SEGS*0.85) segs[i].classList.add('max');
        else if(i > RPM_SEGS*0.65) segs[i].classList.add('hi');
      }
    }
  }

  function drawCandles(){
    const svg = document.getElementById('candleSvg');
    if(!svg || svg.childElementCount) return; // Only draw once
    let price = 40, html = '';
    for(let i=0;i<24;i++){
      const open = price, close = open + (Math.random()-0.5)*10;
      const high = Math.max(open,close) + Math.random()*4, low = Math.min(open,close) - Math.random()*4;
      const x = i*9 + 4, up = close >= open, color = up ? '#3fe08a' : '#ff5d6c';
      html += `<line x1="${x}" y1="${80-high}" x2="${x}" y2="${80-low}" stroke="${color}" stroke-width="1"/>`;
      html += `<rect x="${x-2.5}" y="${80-Math.max(open,close)}" width="5" height="${Math.max(1,Math.abs(open-close))}" fill="${color}"/>`;
      price = close;
    }
    svg.innerHTML = html;
  }
  drawCandles();

  /* ============================================================
     4. Camera — getUserMedia
     ============================================================ */
  (async function initCamera(){
    const camFeed = document.querySelector('.cam-feed');
    if(!camFeed) return;
    try{
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 180 } });
      const video = document.createElement('video');
      video.srcObject = stream;
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;
      video.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block;filter:brightness(0.85) contrast(1.1) saturate(0.8);';
      const camTag = camFeed.querySelector('.cam-tag');
      camFeed.insertBefore(video, camTag);
      if(camTag) camTag.textContent = 'LIVE FEED — WEBCAM ACTIVE';
    }catch(e){
      console.warn('Camera access denied or unavailable:', e);
    }
  })();

  /* ============================================================
     5. Dynamic fallback panel API & Chat logic
     ============================================================ */
  window.JARVIS = window.JARVIS || {};
  window.JARVIS.showDynamicResult = function(title, html){
    const tab = document.querySelector('#panelDynamic .panel-tab');
    if(tab) tab.innerHTML = '<span class="sq"></span>' + (title || '[DYNAMIC_QUERY_RESULT]');
    const body = document.getElementById('dynamicBody');
    if(body) body.innerHTML = html || ''; // Backend should sanitize this
    revealDockPage('dynamic');
    setMode('dynamic');
  };

  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  if(chatInput && chatSendBtn) {
    const sendMsg = async () => {
      const text = chatInput.value.trim();
      if(!text) return;
      chatInput.value = '';
      
      const chatLog = document.querySelector('.chat-log');
      if(chatLog){
        chatLog.innerHTML += `<div class="line user">${text}</div>`;
        chatLog.scrollTop = chatLog.scrollHeight;
      }
      
      try {
        const res = await fetch(`${API}/chat`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: text})
        });
        const data = await res.json();
        
        if(chatLog){
          chatLog.innerHTML += `<div class="line assistant">${data.text}</div>`;
          chatLog.scrollTop = chatLog.scrollHeight;
        }
        
        // Show dynamic result panel
        if(data.dynamic_result){
          window.JARVIS.showDynamicResult(data.dynamic_result.title, data.dynamic_result.html);
        }
      } catch (err) {
        console.error("Chat error:", err);
      }
    };
    
    chatSendBtn.addEventListener('click', sendMsg);
    chatInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') sendMsg(); });
  }
