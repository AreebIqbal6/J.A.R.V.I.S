import puppeteer from 'puppeteer';
import fs from 'node:fs';

async function main() {
  console.log('[GEV-VERIFY] Starting God\'s Eye View comprehensive runtime audit...');

  const candidates = [
    process.env.PUPPETEER_EXECUTABLE_PATH,
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    await puppeteer.executablePath().catch(() => null),
  ];

  let executablePath = candidates.find(c => c && fs.existsSync(c));

  if (!executablePath) {
    console.error('[GEV-VERIFY] No Chromium/Edge browser found.');
    process.exit(1);
  }
  console.log('[GEV-VERIFY] Using browser executable at:', executablePath);

  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath,
    args: [
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-web-security',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const consoleLogs = [];
  const consoleErrors = [];
  const networkErrors = [];

  page.on('console', (msg) => {
    const text = msg.text();
    consoleLogs.push(`[${msg.type()}] ${text}`);
    if (msg.type() === 'error' && !text.includes('Failed to load resource')) {
      consoleErrors.push(text);
    }
  });

  page.on('pageerror', (err) => {
    consoleErrors.push(`[UNCAUGHT] ${err.message}`);
  });

  page.on('requestfailed', (req) => {
    // Only track internal or critical failures
    const url = req.url();
    if (url.includes('127.0.0.1') || url.includes('localhost')) {
      networkErrors.push(`${req.method()} ${url} -> ${req.failure()?.errorText}`);
    }
  });

  console.log('[GEV-VERIFY] Navigating to http://127.0.0.1:5173/?embed=1 ...');
  try {
    await page.goto('http://127.0.0.1:5173/?embed=1', { waitUntil: 'domcontentloaded', timeout: 30000 });
  } catch (err) {
    console.error('[GEV-VERIFY] Failed to load page:', err.message);
    await browser.close();
    process.exit(1);
  }

  console.log('[GEV-VERIFY] Waiting for window.__godsEyeView initialization...');
  try {
    await page.waitForFunction(() => !!window.__godsEyeView?.viewer, { timeout: 30000 });
    console.log('[GEV-VERIFY] PASS: window.__godsEyeView and Cesium Viewer initialized!');
  } catch (err) {
    console.error('[GEV-VERIFY] TIMEOUT waiting for __godsEyeView. Page console logs:');
    consoleErrors.forEach(e => console.error('  ERROR:', e));
    await browser.close();
    process.exit(1);
  }

  // 1. Inspect Core Subsystems
  const coreStatus = await page.evaluate(() => {
    const gev = window.__godsEyeView;
    return {
      hasViewer: !!gev.viewer,
      hasScene: !!gev.viewer?.scene,
      hasCamera: !!gev.viewer?.camera,
      hasDataManager: !!gev.dataManager,
      hasStyleManager: !!gev.styleManager,
      hasSceneDirector: !!gev.sceneDirector,
      hasMapStack: !!gev.mapStackController,
      hasAnnotations: !!gev.annotations,
      hasWeather: !!gev.weatherEffects,
      hasVoiceCommands: !!window.__gevVoiceCommands,
      scopeMaskHidden: window.getComputedStyle(document.getElementById('scope-mask') || document.body).display === 'none'
        || !document.getElementById('scope-mask')
        || window.getComputedStyle(document.getElementById('scope-mask')).visibility === 'hidden',
    };
  });

  console.log('\n--- CORE SUBSYSTEM VERIFICATION ---');
  for (const [key, val] of Object.entries(coreStatus)) {
    console.log(`  [${val ? 'PASS' : 'FAIL'}] ${key}: ${val}`);
  }

  // 2. Discover and Test All Data Layers
  const layerIds = await page.evaluate(() => {
    return Array.from(window.__godsEyeView.dataManager.layers.keys());
  });

  console.log(`\n--- DATA LAYERS AUDIT (${layerIds.length} Layers Found) ---`);
  const layerResults = [];

  for (const layerId of layerIds) {
    const res = await page.evaluate(async (id) => {
      const dm = window.__godsEyeView.dataManager;
      const entry = dm.layers.get(id);
      const name = entry?.module?.name || id;
      try {
        // Toggle ON
        const enablePromise = dm.setEnabled(id, true);
        // Wait up to 5s for activation or resolution
        await Promise.race([
          enablePromise,
          new Promise((r) => setTimeout(r, 4000))
        ]);

        const stats = typeof entry.module.getStats === 'function' ? entry.module.getStats() : {};
        const isEnabled = entry.enabled || entry.lifecycleState === 'enabled';

        // Toggle OFF
        await dm.setEnabled(id, false);

        return {
          id,
          name,
          success: true,
          enabledState: isEnabled,
          stats: JSON.stringify(stats),
        };
      } catch (err) {
        return {
          id,
          name,
          success: false,
          error: err.message,
        };
      }
    }, layerId);

    layerResults.push(res);
    console.log(`  [${res.success ? 'PASS' : 'FAIL'}] Layer: ${res.id} (${res.name}) ${res.success ? '-> Verified Toggle ON/OFF' : '-> ' + res.error}`);
  }

  // 3. Test Visual Styles / Presets
  console.log('\n--- VISUAL STYLE PRESETS AUDIT ---');
  const styleResults = await page.evaluate(async () => {
    const sm = window.__godsEyeView.styleManager;
    if (!sm) return { error: 'No styleManager' };
    const presets = sm.getPresets ? sm.getPresets() : ['default', 'flir', 'cyber', 'crt'];
    const tested = [];
    for (const p of presets.slice(0, 4)) {
      try {
        if (typeof sm.applyPreset === 'function') {
          sm.applyPreset(p);
          tested.push({ preset: p, success: true });
        }
      } catch (e) {
        tested.push({ preset: p, success: false, error: e.message });
      }
    }
    // Restore default
    if (typeof sm.applyPreset === 'function') sm.applyPreset('default');
    return { presets: tested };
  });
  if (styleResults.presets) {
    styleResults.presets.forEach(p => {
      console.log(`  [${p.success ? 'PASS' : 'FAIL'}] Style Preset: ${p.preset}`);
    });
  }

  // 4. Test Standalone Mode (http://127.0.0.1:5173/)
  console.log('\n--- TESTING STANDALONE MODE (POPOUT) ---');
  const page2 = await browser.newPage();
  try {
    await page2.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page2.waitForFunction(() => !!window.__godsEyeView?.viewer, { timeout: 20000 });
    console.log('  [PASS] Standalone mode loaded cleanly without errors');
  } catch (err) {
    console.log('  [FAIL] Standalone mode load failed:', err.message);
  } finally {
    await page2.close();
  }

  // Summary
  console.log('\n======================================================');
  console.log('GOD\'S EYE VIEW COMPLETE AUDIT SUMMARY');
  console.log('======================================================');
  const failedLayers = layerResults.filter(l => !l.success);
  console.log(`Total Layers: ${layerIds.length} | Passing: ${layerResults.length - failedLayers.length} | Failing: ${failedLayers.length}`);
  console.log(`Uncaught Page Errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    console.log('Logged Console Errors:');
    consoleErrors.slice(0, 10).forEach(e => console.log('  •', e));
  }
  console.log(`Local Network Failures: ${networkErrors.length}`);
  if (networkErrors.length > 0) {
    networkErrors.forEach(n => console.log('  •', n));
  }
  console.log('======================================================');

  await browser.close();
  process.exit(failedLayers.length > 0 || consoleErrors.length > 0 ? 1 : 0);
}

main().catch(err => {
  console.error('[GEV-VERIFY] Fatal error:', err);
  process.exit(1);
});
