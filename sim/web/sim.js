// Browser front-end for the ELS simulator. All lathe logic runs in els.wasm, compiled
// from firmware/lib/els_core — this file only draws and forwards inputs.
(async function () {
  'use strict';

  const BTN = { NUT: 0, MODE: 1, UNITS: 2, DIR: 3, STOP_L: 4, STOP_R: 5, JOG_L: 6, JOG_R: 7, RETURN: 8, KNOB: 9 };
  const NUT = { OPEN: 0, ARMED: 1, ENGAGED: 2 };
  const PASS_COLORS = ['#5aaaff', '#2fd068', '#f5c53a', '#ff7a59', '#c78bff', '#4fe0d0'];

  // ---- wasm ----
  const tftCanvas = document.getElementById('tft');
  const tft = tftCanvas.getContext('2d');
  let memory = null;

  const css565 = (c) =>
    `rgb(${(((c >> 11) & 31) * 255) / 31 | 0},${(((c >> 5) & 63) * 255) / 63 | 0},${((c & 31) * 255) / 31 | 0})`;
  const cString = (ptr) => {
    const u8 = new Uint8Array(memory.buffer);
    let s = '';
    while (u8[ptr]) s += String.fromCharCode(u8[ptr++]);
    return s;
  };

  const env = {
    js_fill_rect(x, y, w, h, c) {
      tft.fillStyle = css565(c);
      tft.fillRect(x, y, w, h);
    },
    // Mimics the 6x8-cell ILI9341_t3 font grid so the layout matches the real screen.
    js_text(x, y, ptr, size, fg, bg) {
      const s = cString(ptr);
      tft.fillStyle = css565(bg);
      tft.fillRect(x, y, s.length * 6 * size, 8 * size);
      tft.fillStyle = css565(fg);
      tft.font = `bold ${Math.round(8.4 * size)}px Menlo, ui-monospace, monospace`;
      tft.textBaseline = 'top';
      for (let i = 0; i < s.length; i++) tft.fillText(s[i], x + i * 6 * size + 0.4 * size, y + 0.2 * size);
    },
  };

  const bytes = Uint8Array.from(atob(window.ELS_WASM_B64), (c) => c.charCodeAt(0));
  const { instance } = await WebAssembly.instantiate(bytes, { env });
  const w = instance.exports;
  memory = w.memory;

  w.sim_init(40, 600, 3000); // Roher TBL-20/520: 3 mm leadscrew

  const status = () => {
    const f = new Float32Array(memory.buffer, w.sim_status(), 16);
    return {
      pos: f[0], rpm: f[1], nut: f[2], fault: f[3],
      hasL: f[4] > 0, lo: f[5], hasR: f[6] > 0, hi: f[7],
      mode: f[8], angle: f[9], lead: f[10], synced: f[11] > 0, vel: f[12],
      simRpm: f[13], maxRpm: f[14], enabled: f[15] > 0,
    };
  };

  // ---- inputs ----
  const held = {};
  const longTimers = {};
  const btnEls = {};
  document.querySelectorAll('[data-btn]').forEach((el) => {
    const b = +el.dataset.btn;
    btnEls[b] = el;
    el.addEventListener('pointerdown', (e) => { e.preventDefault(); el.setPointerCapture(e.pointerId); down(b); });
    el.addEventListener('pointerup', () => up(b));
    el.addEventListener('pointercancel', () => up(b));
  });

  function down(b) {
    if (held[b]) return;
    held[b] = true;
    btnEls[b] && btnEls[b].classList.add('down');
    w.sim_press(b);
    longTimers[b] = setTimeout(() => held[b] && w.sim_long(b), 1000);
  }
  function up(b) {
    if (!held[b]) return;
    held[b] = false;
    btnEls[b] && btnEls[b].classList.remove('down');
    clearTimeout(longTimers[b]);
    w.sim_release(b);
  }

  // Knob: wheel, or click left / right half; centre = push.
  const knob = document.getElementById('knob');
  const knobMark = knob.querySelector('.mark');
  let knobAngle = 0;
  function turn(d) {
    w.sim_knob(d);
    knobAngle += d * 15;
    knobMark.style.transform = `rotate(${knobAngle}deg)`;
  }
  knob.addEventListener('wheel', (e) => { e.preventDefault(); turn(e.deltaY > 0 ? -1 : 1); }, { passive: false });
  knob.addEventListener('pointerdown', (e) => {
    const r = knob.getBoundingClientRect();
    const dx = e.clientX - (r.left + r.width / 2);
    const dy = e.clientY - (r.top + r.height / 2);
    if (Math.hypot(dx, dy) < 18) { w.sim_press(BTN.KNOB); w.sim_release(BTN.KNOB); }
    else turn(dx < 0 ? -1 : 1);
  });

  // Spindle.
  const rpmSlider = document.getElementById('rpm');
  const rpmOut = document.getElementById('rpmOut');
  let spindleOn = false;
  let spindleDir = 1;
  const applySpindle = () => {
    const v = Math.abs(+rpmSlider.value) * spindleDir;
    w.sim_set_spindle(spindleOn ? v : 0, 600);
  };
  rpmSlider.addEventListener('input', () => {
    spindleDir = +rpmSlider.value < 0 ? -1 : 1;
    applySpindle();
  });
  document.getElementById('spinFwd').onclick = () => { spindleOn = true; spindleDir = 1; rpmSlider.value = Math.abs(+rpmSlider.value); applySpindle(); };
  document.getElementById('spinRev').onclick = () => { spindleOn = true; spindleDir = -1; rpmSlider.value = -Math.abs(+rpmSlider.value); applySpindle(); };
  document.getElementById('spinStop').onclick = () => { spindleOn = false; applySpindle(); };

  // Faults.
  const estopEl = document.getElementById('estop');
  const faultLed = document.getElementById('faultLed');
  const alarmEl = document.getElementById('alarm');
  let estop = false;
  const applyInputs = () => {
    estopEl.classList.toggle('tripped', estop);
    estopEl.textContent = estop ? 'TWIST TO RELEASE' : 'E-STOP';
    w.sim_set_inputs(estop ? 1 : 0, alarmEl.checked ? 1 : 0);
  };
  estopEl.onclick = () => { estop = !estop; applyInputs(); };
  alarmEl.onchange = applyInputs;

  const slowmo = document.getElementById('slowmo');

  const KEYMAP = { n: BTN.NUT, m: BTN.MODE, u: BTN.UNITS, d: BTN.DIR, '[': BTN.STOP_L, ']': BTN.STOP_R,
    ArrowLeft: BTN.JOG_L, ArrowRight: BTN.JOG_R, r: BTN.RETURN, k: BTN.KNOB };
  window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' && e.target.type !== 'range' && e.target.type !== 'checkbox') return;
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    if (k in KEYMAP) { e.preventDefault(); if (!e.repeat) down(KEYMAP[k]); return; }
    if (k === '-' || k === '_') turn(-1);
    else if (k === '=' || k === '+') turn(1);
    else if (k === ' ') { e.preventDefault(); spindleOn = !spindleOn; applySpindle(); }
    else if (k === 'x') { estop = !estop; applyInputs(); }
  });
  window.addEventListener('keyup', (e) => {
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    if (k in KEYMAP) up(KEYMAP[k]);
  });

  // ---- passes (for the phase plot) ----
  let passes = [];
  let current = null;
  let lastNut = NUT.OPEN;
  let threadKey = '';
  let passCounter = 0;

  function readSamples(n) {
    const view = new DataView(memory.buffer, w.sim_samples(), n * 16);
    for (let i = 0; i < n; i++) {
      const revs = view.getFloat64(i * 16, true);
      const pos = view.getFloat32(i * 16 + 8, true);
      const nut = view.getInt32(i * 16 + 12, true);
      if (nut === NUT.ENGAGED && lastNut !== NUT.ENGAGED) {
        current = { pts: [], color: PASS_COLORS[passCounter++ % PASS_COLORS.length] };
        passes.push(current);
        if (passes.length > 8) passes.shift();
      }
      if (nut === NUT.ENGAGED && current && current.pts.length < 60000) current.pts.push([pos, revs]);
      if (nut !== NUT.ENGAGED) current = null;
      lastNut = nut;
    }
  }

  const wrap = (v, p) => ((v % p) + p) % p;
  // Mean groove phase of a pass (mm, 0..|lead|), skipping the ramp at each end.
  function passPhase(pass, lead) {
    const P = Math.abs(lead);
    const pts = pass.pts.slice(80, -40);
    if (pts.length < 20) return null;
    let c = 0, s = 0;
    for (const [pos, revs] of pts) {
      const a = (2 * Math.PI * wrap(pos - lead * revs, P)) / P;
      c += Math.cos(a);
      s += Math.sin(a);
    }
    return wrap((Math.atan2(s, c) / (2 * Math.PI)) * P, P);
  }

  // ---- drawing ----
  const lathe = document.getElementById('lathe').getContext('2d');
  const phase = document.getElementById('phase').getContext('2d');
  const passesEl = document.getElementById('passes');
  const PX_PER_MM = 5;
  const X0 = 800; // screen x of carriage position 0
  const X = (mm) => X0 + mm * PX_PER_MM;
  const CHUCK_FACE_MM = -140;
  const STOCK_END_MM = 18;

  function drawLathe(st) {
    const g = lathe;
    const W = 960, H = 250;
    g.clearRect(0, 0, W, H);
    const cy = 100, r = 32;

    // Bed.
    g.fillStyle = '#1c2029';
    g.fillRect(0, 196, W, 30);
    // Leadscrew with marks that move with the carriage.
    g.strokeStyle = '#59606e';
    g.lineWidth = 6;
    g.beginPath(); g.moveTo(0, 212); g.lineTo(W, 212); g.stroke();
    g.strokeStyle = '#2b3039';
    g.lineWidth = 2;
    const screwPhase = wrap(st.pos * PX_PER_MM * 2.2, 10);
    for (let x = -10 + screwPhase; x < W; x += 10) { g.beginPath(); g.moveTo(x, 207); g.lineTo(x + 4, 217); g.stroke(); }

    // Headstock + chuck.
    g.fillStyle = '#2c3240';
    g.fillRect(0, 20, X(CHUCK_FACE_MM) - 40, 170);
    const chx = X(CHUCK_FACE_MM) - 40;
    g.fillStyle = '#4a5160';
    g.fillRect(chx, cy - 70, 40, 140);
    g.strokeStyle = '#7d8596';
    g.lineWidth = 3;
    for (let k = 0; k < 3; k++) {
      const a = 2 * Math.PI * (st.angle + k / 3);
      const y = cy - Math.cos(a) * 60;
      g.globalAlpha = Math.sin(a) > 0 ? 1 : 0.35;
      g.beginPath(); g.moveTo(chx + 4, y); g.lineTo(chx + 36, y); g.stroke();
    }
    g.globalAlpha = 1;

    // Stock.
    const x0 = X(CHUCK_FACE_MM), x1 = X(STOCK_END_MM);
    const grad = g.createLinearGradient(0, cy - r, 0, cy + r);
    grad.addColorStop(0, '#9aa3b2'); grad.addColorStop(0.5, '#d9dee6'); grad.addColorStop(1, '#6b7382');
    g.fillStyle = grad;
    g.fillRect(x0, cy - r, x1 - x0, 2 * r);

    // Threaded section from all passes of the current thread.
    if (passes.length && st.mode === 1 && Math.abs(st.lead) > 0) {
      let lo = Infinity, hi = -Infinity;
      for (const p of passes) for (const [pos] of p.pts) { lo = Math.min(lo, pos); hi = Math.max(hi, pos); }
      lo = Math.max(lo, CHUCK_FACE_MM); hi = Math.min(hi, STOCK_END_MM);
      if (hi > lo) {
        const pitchPx = Math.abs(st.lead) * PX_PER_MM;
        const ref = passPhase(passes[0], st.lead) ?? 0;
        g.save();
        g.beginPath(); g.rect(X(lo), cy - r, (hi - lo) * PX_PER_MM, 2 * r); g.clip();
        g.fillStyle = '#7d8696';
        g.fillRect(X(lo), cy - r, (hi - lo) * PX_PER_MM, 2 * r);
        g.strokeStyle = '#3b414d';
        g.lineWidth = Math.max(1.5, pitchPx * 0.35);
        // Crests turn with the spindle: phase of the helix at the current angle.
        const turnShift = wrap(ref + st.lead * st.angle, Math.abs(st.lead)) * PX_PER_MM;
        for (let x = X(lo) - pitchPx * 3 + wrap(turnShift - X(lo), pitchPx); x < X(hi) + pitchPx * 3; x += pitchPx) {
          g.beginPath(); g.moveTo(x, cy - r); g.lineTo(x + pitchPx * 0.5, cy + r); g.stroke();
        }
        g.restore();
      }
    }

    // Stops.
    g.setLineDash([6, 5]);
    g.lineWidth = 2;
    g.font = '12px Menlo, monospace';
    for (const [has, mm, label] of [[st.hasL, st.lo, 'L'], [st.hasR, st.hi, 'R']]) {
      if (!has) continue;
      g.strokeStyle = '#f5c53a';
      g.beginPath(); g.moveTo(X(mm), 10); g.lineTo(X(mm), 196); g.stroke();
      g.fillStyle = '#f5c53a';
      g.fillText(`${label} ${mm.toFixed(2)}`, X(mm) + 4, 22);
    }
    g.setLineDash([]);

    // Carriage + tool (tool tip at the carriage position).
    const tx = X(st.pos);
    const nutColor = st.nut === NUT.ENGAGED ? '#2fd068' : st.nut === NUT.ARMED ? '#f5c53a' : '#59606e';
    g.fillStyle = '#3a4150';
    g.fillRect(tx - 60, 150, 120, 46);
    g.fillStyle = nutColor;
    g.fillRect(tx - 60, 190, 120, 6);
    g.fillStyle = '#c9a227';
    g.beginPath(); g.moveTo(tx, cy + r + 2); g.lineTo(tx - 7, 150); g.lineTo(tx + 7, 150); g.closePath(); g.fill();

    // Readout.
    g.fillStyle = '#e5e7ee';
    g.font = '13px Menlo, monospace';
    const nutTxt = ['OPEN', 'ARMED', 'ENGAGED'][st.nut] || '';
    g.fillText(`X ${st.pos.toFixed(3)} mm   v ${st.vel.toFixed(1)} mm/s   spindle ${st.simRpm.toFixed(0)} rpm   nut ${nutTxt}${st.enabled ? '' : '   DRIVER DISABLED'}`, 12, 244);
  }

  function drawPhase(st) {
    const g = phase;
    const W = 960, H = 230;
    g.clearRect(0, 0, W, H);
    g.strokeStyle = '#232733';
    g.lineWidth = 1;
    g.fillStyle = '#5c6372';
    g.font = '11px Menlo, monospace';
    for (let a = 0; a <= 360; a += 90) {
      const y = H - 10 - (a / 360) * (H - 20);
      g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke();
      g.fillText(`${a}°`, 4, y - 2);
    }
    for (let mm = -140; mm <= 20; mm += 10) {
      g.beginPath(); g.moveTo(X(mm), 0); g.lineTo(X(mm), H); g.stroke();
      g.fillText(`${mm}`, X(mm) + 2, H - 1);
    }
    for (const p of passes) {
      g.fillStyle = p.color;
      for (let i = 0; i < p.pts.length; i += 2) {
        const [pos, revs] = p.pts[i];
        const y = H - 10 - wrap(revs, 1) * (H - 20);
        g.fillRect(X(pos) - 1, y - 1, 2, 2);
      }
    }

    // Per-pass groove offset relative to pass 1.
    if (st.mode === 1 && passes.length) {
      const ref = passPhase(passes[0], st.lead);
      passesEl.innerHTML = passes
        .map((p, i) => {
          const ph = passPhase(p, st.lead);
          let txt = '…';
          if (ph != null && ref != null) {
            const P = Math.abs(st.lead);
            let d = wrap(ph - ref + P / 2, P) - P / 2;
            txt = `${(d * 1000).toFixed(1)} µm`;
          }
          return `<div style="border-color:${p.color}">pass ${i + 1}: ${txt}</div>`;
        })
        .join('');
    } else {
      passesEl.textContent = st.mode === 1 ? 'Press NUT with the spindle running to cut pass 1.' : 'Feed mode: no thread phase.';
    }
  }

  // ---- main loop ----
  const nutEl = document.getElementById('nut');
  let last = performance.now();
  let simMs = 0;
  w.sim_render(0, 1);

  function frame(now) {
    let dt = Math.min(now - last, 50);
    last = now;
    if (slowmo.checked) dt *= 0.2;
    simMs += dt;
    const n = w.sim_run(dt);
    readSamples(n);
    const st = status();

    const key = `${st.lead.toFixed(6)}|${st.synced}|${st.mode}`;
    if (key !== threadKey) {
      // A different thread (pitch/mode/direction changed, sync set or dropped):
      // only the pass being cut right now belongs to it.
      passes = passes.filter((p) => p === current);
      threadKey = key;
    }

    w.sim_render(simMs, 0);
    rpmOut.textContent = st.simRpm.toFixed(0);
    nutEl.classList.toggle('engaged', st.nut === NUT.ENGAGED);
    nutEl.classList.toggle('armed', st.nut === NUT.ARMED);
    faultLed.classList.toggle('on', st.fault !== 0);
    drawLathe(st);
    drawPhase(st);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
