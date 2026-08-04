
const steps = [];
let rafCb = null;
function stubCtx() {
  return new Proxy({}, {
    get(t, p) {
      if (p === 'measureText') return () => ({ width: 10 });
      if (p === 'createLinearGradient') return () => ({ addColorStop() {} });
      return typeof t[p] !== 'undefined' ? t[p] : () => {};
    },
    set(t, p, v) { t[p] = v; return true; }
  });
}
function stubEl() {
  return { style: {}, textContent: '', className: '',
    addEventListener() {}, onclick: null,
    getContext: () => stubCtx(),
    getBoundingClientRect: () => ({ left: 0, top: 0, width: 1440, height: 940 }) };
}
global.document = { getElementById: () => stubEl(), addEventListener() {}, createElement: () => stubEl() };
global.window = { devicePixelRatio: 1, addEventListener() {}, AudioContext: undefined, webkitAudioContext: undefined };
global.performance = { now: () => nowMs };
global.requestAnimationFrame = cb => { rafCb = cb; };
let nowMs = 0;

'use strict';
/* ══════════════════════════════════════════════════════════════════
   HONEYLIGHT MARBLE QUIPU — Snapshot System (v4)
   Mark's direction, 2026-08-04:
   · SOUNDSCAPE SNAPSHOT: bar heights are PROPORTIONAL to the sound-
     frequency distribution at each snapshot in time. A camera reads
     the bars, requests balls, and activates the hammers.
   · ALL 28 BALLS VISIBLE, ALWAYS. Conserved supply = 110% of max
     demand (25) — the 3 spare balls cover rapid-succession drops
     (>4 at once) while balls settle into the gate.
   · HOLDING BANK + FAST GATE ROUTER: balls rest at the top of the
     tank as pure potential energy; the gate carriage shuttles fast
     and routes each ball where the snapshot says it is needed.
   · MAPPING THE SYSTEM: the model carries every energy and informa-
     tion state — position + velocity of all 28 balls — and gears
     show the conversion chain: PE (top of tank) → MOTION → SOUND →
     MONEY → FLOWERS planted around the bees in Honeyton, WV.
     Balanced at every snapshot.
   Lift (v3) unchanged: 6 da Vinci wheels in series, each lifts 90%
   of ½D (Ø18" → 8.1"; 6 × 8.1" = 4.05 ft), RPM ∝ note frequency,
   LED color-coded. Overflow (v2) unchanged: RUBIN 1982 machine.
   ══════════════════════════════════════════════════════════════════ */

// ── canvas setup ─────────────────────────────────────────────────
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
const W = 1440, H = 940;
function fit() {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  cv.width = W * dpr; cv.height = H * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
fit(); window.addEventListener('resize', fit);

// ── ALIENPAN D Minor Kurd — 10 notes, 440 Hz ────────────────────
const NOTES = [
  { name: 'D3',  freq: 146.83, col: [195, 45, 45]  },  // Deep Ember
  { name: 'A3',  freq: 220.00, col: [210, 115, 20] },  // Burnt Honey
  { name: 'Bb3', freq: 233.08, col: [130, 175, 60] },  // Sage
  { name: 'C4',  freq: 261.63, col: [35, 165, 155] },  // Teal Spring
  { name: 'D4',  freq: 293.66, col: [40, 105, 210] },  // Twilight Blue
  { name: 'E4',  freq: 329.63, col: [130, 55, 195] },  // Violet Dusk
  { name: 'F4',  freq: 349.23, col: [190, 165, 60] },  // Evening Gold
  { name: 'G4',  freq: 392.00, col: [215, 90, 130] },  // Rose Dawn
  { name: 'A4',  freq: 440.00, col: [160, 170, 185] }, // Gunmetal Silver
  { name: 'C5',  freq: 523.25, col: [235, 225, 200] }, // Moonlit Cream
];

// ── layout constants ─────────────────────────────────────────────
const LEFT_W = 216, RIGHT_W = 150, FOOTER_H = 64, INSTR_H = 88;
const LANE_X = LEFT_W, LANE_W_AREA = W - LEFT_W - RIGHT_W;
const NUM_LANES = 10;
const LANE_W = LANE_W_AREA / NUM_LANES;
const BALL_R = 12;
const INSTR_Y = 700;                                  // instrument strip top
const LANE_Y = 216;                                   // lane frame top
const BALL_HIT_Y = INSTR_Y - BALL_R - 2;              // strike line
const FALL_TIME = 0.65;
const laneCx = l => LANE_X + l * LANE_W + LANE_W / 2;

// ── the 6 da Vinci lift wheels (left column) ────────────────────
const N_WHEELS = 6;
const LWR = 94;
const LIFT_CX = LEFT_W / 2;
const BALL_ORBIT_R = LWR - BALL_R * 0.4;              // ball path radius on a wheel
const LIFT_FLOOR = BALL_HIT_Y + BALL_R * 0.4;         // wheel-0 entry sits exactly at the strike line
const LIFT_ENTRY = Math.PI / 2;                       // canvas angle: bottom of wheel
const LIFT_PER_WHEEL = 0.9 * LWR;                     // 90% of ½D = 0.9R
// seamless handoff: release height of wheel i == entry height of wheel i+1
const LIFT_RELEASE = Math.asin((BALL_ORBIT_R - LIFT_PER_WHEEL) / BALL_ORBIT_R);
const REL_OFF = BALL_ORBIT_R * Math.sin(LIFT_RELEASE); // = r − 0.9R
const WHEEL_D_IN = 18;
const LIFT_PER_WHEEL_IN = 0.9 * WHEEL_D_IN / 2;       // 8.1"
const TOTAL_LIFT_IN = N_WHEELS * LIFT_PER_WHEEL_IN;   // 48.6"
const wheelCY = i => LIFT_FLOOR - LWR - i * LIFT_PER_WHEEL;
const WHEEL_NOTE = [0, 2, 4, 6, 8, 9];
const WHEEL_BASE_RPM = 15;
const wheelRPM = i => WHEEL_BASE_RPM * NOTES[WHEEL_NOTE[i]].freq / NOTES[WHEEL_NOTE[0]].freq;
const wheelOmega = i => wheelRPM(i) * 2 * Math.PI / 60;
const BRIDGE_TIME = 0.45;
const TOP_BRIDGE_Y = wheelCY(N_WHEELS - 1) + REL_OFF; // release height of the top wheel

// ── holding bank + gate router (top of the tank = PE) ───────────
const BANK_Y = TOP_BRIDGE_Y;                          // bank rail = lift top rail
const BALL_START_Y = BANK_Y;                          // bank seat = release height (exact PE)
const G_PX = 2 * (BALL_HIT_Y - BALL_START_Y) / (FALL_TIME * FALL_TIME);
const GATE_SPEED = 2400;                              // px/s — fast shuttle
const SLIDE_SPEED = 1300;                             // px/s — ball slides to gate
const GATE_LEAD = 150;                                // ms before fall lead

// ── physical units (for the energy ledger) ──────────────────────
const IN_PER_PX = TOTAL_LIFT_IN / (N_WHEELS * LIFT_PER_WHEEL);  // 48.6"/507.6px
const M_PER_PX = IN_PER_PX * 0.0254;
const BALL_MASS = 0.0459;                             // kg, regulation golf ball
const G_EARTH = 9.8;
const peOfY = y => BALL_MASS * G_EARTH * Math.max(0, (BALL_HIT_Y - y)) * M_PER_PX;
const SOUND_J = 0.02;                                 // acoustic energy radiated per strike
const NOTE_VALUE = 0.05;                              // $ per note (model value)
const FLOWER_COST = 0.25;                             // $ per flower planted
const PE_PER_DROP = peOfY(BALL_START_Y);              // PE released per ball drop (J)
const HARVEST_J = PE_PER_DROP - SOUND_J;              // surplus harvested as money per note

// ── the 1982 overflow machine (right column) ────────────────────
const WHEEL_CX = W - RIGHT_W / 2 - 4;
const WHEEL_CY = LANE_Y + (INSTR_Y - LANE_Y) * 0.40;
const WHEEL_R = 62;
const WHEEL_POCKETS = 6;
const ENTRY_ANG = -0.72;
const EXIT_ANG  = 2.35;
const MAG_A = 2.6, MAG_B = -0.15;

// ── ball supply: conserved, 110% of max demand ──────────────────
const MAX_DEMAND = 25;
const SUPPLY = Math.ceil(MAX_DEMAND * 1.10);          // = 28
const slotX = k => LANE_X + 16 + k * (LANE_W_AREA - 32) / (SUPPLY - 1);

// ── song: Ode to Joy, arranged for D Kurd ────────────────────────
const QN = 460;
const D3=0, A3=1, Bb3=2, C4=3, D4=4, E4=5, F4=6, G4=7, A4=8, C5=9;
function buildSong() {
  const ev = [];
  const mel = [E4,E4,F4,G4, G4,F4,E4,D4, C4,C4,D4,E4, E4,D4,D4];
  const dur = [1,1,1,1, 1,1,1,1, 1,1,1,1, 1.5,0.5,2];
  let t = 0;
  for (let i = 0; i < mel.length; i++) { ev.push([mel[i], t]); t += dur[i] * QN; }
  const bass = [[D3,0],[A3,2],[Bb3,4],[A3,6],[D3,8],[C4,10],[Bb3,12],[D3,14],[A3,14]];
  for (const [n, q] of bass) ev.push([n, q * QN]);
  ev.sort((a, b) => a[1] - b[1]);
  return { events: ev, totalMs: t + 1500 };
}
const SONG = buildSong();
const FALL_MS = FALL_TIME * 1000;

// ── state ────────────────────────────────────────────────────────
let gate = 'play';
let ovfRate = 1.0;
let paused = false;
let audioOn = false;
let songMs = -FALL_MS - 800;
let songIdx = 0;
let wheelAng1982 = 0;
let noteCount = 0;
let money = 0, flowers = 0;
let energyIn = 0, energyOut = 0;                      // J — the ledger
let accDispatch = 0, accStrike = 0;                   // decaying flow drivers
let flashBeam = 0;                                    // camera → gate flash
let camFlash = 0;
const liftAng = new Array(N_WHEELS).fill(0);
const liftGlow = new Array(N_WHEELS).fill(0);

let bankBalls = [];     // holding bank: {slot, x, state:'settle'|'slide', tx}
let gateState = { x: laneCx(4), pending: null };      // router carriage
let dispatchQueue = []; // {lane, due, manual}
let fieldBalls = [];    // falling: {lane, x, y, vy}
let rideBalls = [];     // on a lift wheel: {wheel, ang, lane, py}
let bridgeBalls = [];   // handoff bridge i (0..4) or top rail (5): {i, t, lane}
let liftFeed = [];      // tray → wheel-0 entry ramp: {t, lane}
let trayBalls = [];     // rolling on return tray: {x, tx, lane, t, dest}
let ovfFeed = [];       // tray → 1982 feed ramp: {t, lane}
let wheelBalls = [];    // in 1982 wheel pockets: {ang, lane}
let retBalls = [];      // 1982 eject → lift base chute: {t, lane}
let hammerSwing = new Array(NUM_LANES).fill(0);
let toneFlash = new Array(NUM_LANES).fill(0);
let laneGlow = new Array(NUM_LANES).fill(0);
let ripples = [];
const snapBars = new Array(NUM_LANES).fill(0);        // animated snapshot heights
let snapHistory = [];                                 // past snapshots (ribbon)
let snapTimer = 0;
const gearAng = [0, 0, 0, 0];
const flowerSpots = [];
for (let i = 0; i < 40; i++)
  flowerSpots.push({ fx: Math.random(), fy: Math.random(), c: (Math.random() * 10) | 0, ph: Math.random() * 7 });

// seed: all 28 balls settled in the holding bank — full PE at the top
function seedBank() {
  bankBalls = [];
  for (let k = 0; k < SUPPLY; k++) bankBalls.push({ slot: k, x: slotX(k), state: 'settle', tx: slotX(k), col: k % NUM_LANES });
  energyIn += SUPPLY * PE_PER_DROP;                   // initial charge: PE at the top of the tank
}
seedBank();

function totalBalls() {
  return bankBalls.length + fieldBalls.length + rideBalls.length + bridgeBalls.length +
         liftFeed.length + trayBalls.length + ovfFeed.length + wheelBalls.length + retBalls.length;
}

function resetSong() {
  songMs = -FALL_MS - 800; songIdx = 0; noteCount = 0;
  money = 0; flowers = 0; energyIn = 0; energyOut = 0;
  accDispatch = 0; accStrike = 0;
  fieldBalls = []; rideBalls = []; bridgeBalls = []; liftFeed = [];
  trayBalls = []; ovfFeed = []; wheelBalls = []; retBalls = [];
  dispatchQueue = []; gateState.pending = null;
  ripples = []; snapHistory = [];
  for (let i = 0; i < NUM_LANES; i++) { hammerSwing[i] = 0; toneFlash[i] = 0; laneGlow[i] = 0; }
  seedBank();
}

// ── audio: handpan synthesis (Web Audio) ─────────────────────────
let AC = null, master = null;
function initAudio() {
  if (!AC) {
    AC = new (window.AudioContext || window.webkitAudioContext)();
    master = AC.createGain(); master.gain.value = 0.55;
    const comp = AC.createDynamicsCompressor();
    comp.threshold.value = -18; comp.ratio.value = 6;
    master.connect(comp); comp.connect(AC.destination);
  }
  if (AC.state === 'suspended') AC.resume();
  audioOn = true;
  document.getElementById('audioHint').textContent = '🔊 sound on';
  const sg = document.getElementById('soundGate');
  if (sg) sg.style.display = 'none';
}
document.getElementById('soundGate').addEventListener('pointerdown', initAudio);
document.addEventListener('pointerdown', () => { if (!audioOn) initAudio(); });
document.addEventListener('keydown', () => { if (!audioOn) initAudio(); });

function playHandpan(freq) {
  if (!AC || AC.state !== 'running') return;
  const t0 = AC.currentTime;
  const partials = [[1.0, 1.0, 2.6], [2.0, 0.4, 2.1], [2.98, 0.18, 1.5]];
  for (const [ratio, amp, dec] of partials) {
    const o = AC.createOscillator();
    const g = AC.createGain();
    o.type = 'sine';
    o.frequency.value = freq * ratio * (1 + (Math.random() - 0.5) * 0.0015);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(amp * 0.32, t0 + 0.006);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dec);
    o.connect(g); g.connect(master);
    o.start(t0); o.stop(t0 + dec + 0.1);
  }
  const nb = AC.createBuffer(1, AC.sampleRate * 0.03, AC.sampleRate);
  const d = nb.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
  const ns = AC.createBufferSource(); ns.buffer = nb;
  const nf = AC.createBiquadFilter(); nf.type = 'bandpass';
  nf.frequency.value = freq * 2.5; nf.Q.value = 1.2;
  const ng = AC.createGain(); ng.gain.value = 0.12;
  ns.connect(nf); nf.connect(ng); ng.connect(master);
  ns.start(t0);
}

function strike(lane) {
  hammerSwing[lane] = 1; toneFlash[lane] = 1; laneGlow[lane] = 1;
  ripples.push({ lane, age: 0 });
  noteCount++;
  playHandpan(NOTES[lane].freq);
}

// ── the gate router: camera reads snapshot → bank → gate → lane ─
function requestDrop(lane, manual) {
  dispatchQueue.push({ lane, due: songMs + GATE_LEAD + FALL_MS, manual: !!manual });
}

function enterBank(lane, fromX) {
  const taken = new Set(bankBalls.map(b => b.slot));
  let best = -1, bd = 1e9;
  for (let k = 0; k < SUPPLY; k++) {
    if (taken.has(k)) continue;
    const d = Math.abs(slotX(k) - fromX);
    if (d < bd) { bd = d; best = k; }
  }
  if (best < 0) return false;                 // bank full — cannot happen with 28/28
  bankBalls.push({ slot: best, x: fromX, state: 'settle', tx: slotX(best), col: lane });
  return true;
}

function stepGateAndBank(dt) {
  // drop stale song requests (manual requests never expire)
  dispatchQueue = dispatchQueue.filter(q => q.manual || songMs < q.due + 260);

  // carriage: commit to the head of the queue
  if (!gateState.pending && dispatchQueue.length) {
    gateState.pending = dispatchQueue[0];
  }

  if (gateState.pending) {
    const tx = laneCx(gateState.pending.lane);
    // reserve the nearest settled ball (re-try until one is available —
    // the gate waits for balls to settle rather than dropping unready ones)
    if (!bankBalls.some(b => b.state === 'slide')) {
      let best = null, bd = 1e9;
      for (const b of bankBalls) {
        if (b.state !== 'settle') continue;
        const d = Math.abs(b.x - tx);
        if (d < bd) { bd = d; best = b; }
      }
      if (best) { best.state = 'slide'; best.tx = tx; }
    }
    // fast carriage shuttle
    const dx = tx - gateState.x;
    const step = GATE_SPEED * dt;
    gateState.x += Math.abs(dx) <= step ? dx : Math.sign(dx) * step;
  }

  // balls sliding along the bank rail toward the gate
  for (const b of bankBalls) {
    const dx = b.tx - b.x;
    const step = (b.state === 'slide' ? SLIDE_SPEED : 700) * dt;
    if (Math.abs(dx) <= step) b.x = b.tx; else b.x += Math.sign(dx) * step;
  }

  // release: carriage in position AND reserved ball arrived at the gate
  if (gateState.pending) {
    const q = gateState.pending;
    const tx = laneCx(q.lane);
    const arrived = Math.abs(gateState.x - tx) < 4;
    const ball = bankBalls.find(b => b.state === 'slide' && Math.abs(b.x - tx) < 7);
    if (arrived && ball) {
      bankBalls = bankBalls.filter(b => b !== ball);
      fieldBalls.push({ lane: q.lane, x: gateState.x, y: BALL_START_Y, vy: 0 });
      accDispatch += peOfY(BALL_START_Y);   // flow driver only — lift work is the ledger's IN
      flashBeam = 1; camFlash = 1;
      dispatchQueue.shift();
      gateState.pending = null;
    }
  }
}

// ── snapshot: proportional frequency distribution of the soundscape
function snapshotTargets() {
  const counts = new Array(NUM_LANES).fill(0);
  const t0 = songMs, t1 = songMs + 1600;
  for (const [lane, st] of SONG.events) if (st >= t0 && st < t1) counts[lane]++;
  const mx = Math.max(1, ...counts);
  return counts.map(c => c / mx);
}

function step(dt) {
  songMs += dt * 1000;
  wheelAng1982 += ovfRate * 45 * 2 * Math.PI / 60 * dt;
  for (let i = 0; i < N_WHEELS; i++) {
    liftAng[i] -= wheelOmega(i) * dt;
    liftGlow[i] = Math.max(0, liftGlow[i] - dt * 2.4);
  }
  accDispatch = Math.max(0, accDispatch - dt * accDispatch / 1.5 - 0.001 * dt);
  accStrike = Math.max(0, accStrike - dt * accStrike / 1.5 - 0.001 * dt);
  flashBeam = Math.max(0, flashBeam - dt * 3);
  camFlash = Math.max(0, camFlash - dt * 3);

  // schedule song notes through the gate router
  while (songIdx < SONG.events.length) {
    const [lane, st] = SONG.events[songIdx];
    if (songMs >= st - FALL_MS - GATE_LEAD) { requestDrop(lane, false); songIdx++; }
    else break;
  }

  stepGateAndBank(dt);

  // snapshot bars — animate toward the current distribution
  const tgt = snapshotTargets();
  for (let i = 0; i < NUM_LANES; i++)
    snapBars[i] += (tgt[i] - snapBars[i]) * Math.min(1, dt * 7);
  snapTimer += dt;
  if (snapTimer >= 0.25) {
    snapTimer = 0;
    snapHistory.push(tgt.slice());
    if (snapHistory.length > 26) snapHistory.shift();
  }

  // falling balls → strike line (position + velocity tracked)
  // ledger: the ball's KE at the strike line equals the PE it released
  // (conservation). Most recirculates through the lift; SOUND_J radiates;
  // the surplus HARVEST_J leaves the system as money → flowers.
  const survivors = [];
  for (const b of fieldBalls) {
    b.vy += G_PX * dt; b.y += b.vy * dt;
    if (b.y >= BALL_HIT_Y) {
      if (gate === 'play') {
        strike(b.lane);
        energyOut += SOUND_J;
        money += NOTE_VALUE;
        const nf = Math.floor(money / FLOWER_COST);
        if (nf > flowers) { flowers = nf; accStrike += 0.6; }
        trayBalls.push({ x: b.x, tx: LANE_X + 30, lane: b.lane, t: 0, dest: 'lift' });
      } else {
        laneGlow[b.lane] = Math.max(laneGlow[b.lane], 0.25);
        trayBalls.push({ x: b.x, tx: FEED1982_P0[0], lane: b.lane, t: 0, dest: 'wheel' });
      }
      accStrike += 0.3;
    } else survivors.push(b);
  }
  fieldBalls = survivors;

  // tray: roll to destination, then hand off
  const trayLeft = [];
  for (const b of trayBalls) {
    b.t += dt / 0.55;
    b.x += (b.tx - b.x) * Math.min(1, dt * 6);
    if (b.t >= 1) {
      if (b.dest === 'lift') liftFeed.push({ t: 0, lane: b.lane });
      else ovfFeed.push({ t: 0, lane: b.lane });
    } else trayLeft.push(b);
  }
  trayBalls = trayLeft;

  // tray → wheel-0 entry ramp
  const lfLeft = [];
  for (const b of liftFeed) {
    b.t += dt / 0.5;
    if (b.t >= 1) { rideBalls.push({ wheel: 0, ang: LIFT_ENTRY, lane: b.lane, py: 0 }); liftGlow[0] = 1; }
    else lfLeft.push(b);
  }
  liftFeed = lfLeft;

  // da Vinci lift wheels: carry CCW from entry (bottom) to release (right)
  // ledger: signed mgh per step, capped at the exact release height — the
  // frame-boundary overshoot past LIFT_RELEASE is a teleport back onto the
  // bridge, not real climb, so it is not credited. Each full wheel passage
  // credits exactly 0.9R of lift; each 6-wheel loop credits PE_PER_DROP.
  const rideLeft = [];
  for (const b of rideBalls) {
    const cy = wheelCY(b.wheel), r = LWR - BALL_R * 0.4;
    const prevY = cy + r * Math.sin(b.ang);
    b.ang -= wheelOmega(b.wheel) * dt;
    if (b.ang <= LIFT_RELEASE) {
      const relY = cy + r - LIFT_PER_WHEEL;           // exact release height
      energyIn += BALL_MASS * G_EARTH * (prevY - relY) * M_PER_PX;
      liftGlow[b.wheel] = 1;
      bridgeBalls.push({ i: b.wheel, t: 0, lane: b.lane });
    } else {
      const newY = cy + r * Math.sin(b.ang);
      energyIn += BALL_MASS * G_EARTH * (prevY - newY) * M_PER_PX;
      rideLeft.push(b);
    }
  }
  rideBalls = rideLeft;

  // bridges 0..4: wheel i release → wheel i+1 entry; bridge 5: top rail → bank
  const brLeft = [];
  for (const b of bridgeBalls) {
    b.t += dt / BRIDGE_TIME;
    if (b.t >= 1) {
      if (b.i < N_WHEELS - 1) {
        rideBalls.push({ wheel: b.i + 1, ang: LIFT_ENTRY, lane: b.lane, py: 0 });
        liftGlow[b.i + 1] = Math.max(liftGlow[b.i + 1], 0.7);
      } else {
        const x0 = LIFT_CX + LWR + 8;
        if (!enterBank(b.lane, x0 + 60)) ovfFeed.push({ t: 0, lane: b.lane });
      }
    } else brLeft.push(b);
  }
  bridgeBalls = brLeft;

  // tray → 1982 feed ramp
  const ofLeft = [];
  for (const b of ovfFeed) {
    b.t += dt / 0.5;
    if (b.t >= 1) wheelBalls.push({ ang: ENTRY_ANG, lane: b.lane });
    else ofLeft.push(b);
  }
  ovfFeed = ofLeft;

  // 1982 wheel: carry from entry to eject
  const wSpeed = ovfRate * 45 * 2 * Math.PI / 60;
  const wheelLeft = [];
  for (const b of wheelBalls) {
    b.ang += wSpeed * dt;
    if (b.ang >= EXIT_ANG) retBalls.push({ t: 0, lane: b.lane });
    else wheelLeft.push(b);
  }
  wheelBalls = wheelLeft;

  // 1982 eject → lift base chute → wheel 0
  const retLeft = [];
  for (const b of retBalls) {
    b.t += dt / 0.8;
    if (b.t >= 1) { rideBalls.push({ wheel: 0, ang: LIFT_ENTRY, lane: b.lane, py: 0 }); liftGlow[0] = 1; }
    else retLeft.push(b);
  }
  retBalls = retLeft;

  // gears: PE → MOTION → SOUND → MONEY
  // in-flight KE via conservation: PE released since the gate, minus none yet
  const keNow = fieldBalls.reduce((s, b) => s + Math.max(0, peOfY(BALL_START_Y) - peOfY(b.y)), 0);
  gearAng[0] += (0.35 + 3.0 * accDispatch) * dt;
  gearAng[1] += (0.35 + 2.6 * keNow) * dt;
  gearAng[2] += (0.35 + 3.0 * accStrike) * dt;
  gearAng[3] += (0.35 + 2.4 * accStrike) * dt;

  // decay visuals
  for (let i = 0; i < NUM_LANES; i++) {
    laneGlow[i] = Math.max(0, laneGlow[i] - dt * 1.8);
    toneFlash[i] = Math.max(0, toneFlash[i] - dt * 2.6);
    hammerSwing[i] = Math.max(0, hammerSwing[i] - dt * 7);
  }
  ripples = ripples.filter(r => (r.age += dt) < 0.7);
}

// ── path geometry ────────────────────────────────────────────────
const TRAY_Y = INSTR_Y + INSTR_H - 20;
const FEED1982_P0 = [LANE_X + LANE_W_AREA - 8, TRAY_Y];
const FEED1982_P1 = [WHEEL_CX + WHEEL_R * Math.cos(ENTRY_ANG), WHEEL_CY + WHEEL_R * Math.sin(ENTRY_ANG)];
const EJECT_PT = [WHEEL_CX + WHEEL_R * Math.cos(EXIT_ANG), WHEEL_CY + WHEEL_R * Math.sin(EXIT_ANG)];
const RET_P0 = EJECT_PT;
const RET_P1 = [WHEEL_CX - WHEEL_R - 30, WHEEL_CY + WHEEL_R + 40];
const RET_P2 = [LIFT_CX + LWR + 26, wheelCY(0) + REL_OFF];
const LFEED_P0 = [LANE_X + 10, TRAY_Y];
const LFEED_P1 = [LIFT_CX + LWR * 0.55, wheelCY(0) + LWR - 4];

// ── drawing helpers ──────────────────────────────────────────────
function rgb(c, a) { return a === undefined ? `rgb(${c[0]},${c[1]},${c[2]})` : `rgba(${c[0]},${c[1]},${c[2]},${a})`; }

function drawBall(x, y, col, r) {
  r = r || BALL_R;
  ctx.beginPath(); ctx.arc(x + 2, y + 2, r, 0, 7); ctx.fillStyle = 'rgba(0,0,0,.5)'; ctx.fill();
  ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fillStyle = rgb(col); ctx.fill();
  ctx.beginPath(); ctx.arc(x - r / 3, y - r / 3, r / 3, 0, 7); ctx.fillStyle = 'rgba(255,255,255,.75)'; ctx.fill();
  ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.strokeStyle = '#0c0c0f'; ctx.lineWidth = 1; ctx.stroke();
}

function ballOnLiftWheel(b) {
  const cx = LIFT_CX, cy = wheelCY(b.wheel);
  const r = LWR - BALL_R * 0.4;
  return [cx + r * Math.cos(b.ang), cy + r * Math.sin(b.ang)];
}

function drawLiftWheel(i) {
  const cx = LIFT_CX, cy = wheelCY(i), R = LWR;
  const note = NOTES[WHEEL_NOTE[i]];
  const c = note.col;
  const glow = liftGlow[i];
  ctx.strokeStyle = '#1c2430'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx, cy + R + 6); ctx.stroke();
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7);
  ctx.fillStyle = 'rgba(16,21,31,.88)'; ctx.fill();
  ctx.lineWidth = 3.5;
  ctx.strokeStyle = rgb(c.map(v => Math.max(18, v * 0.16)));
  ctx.stroke();
  if (glow > 0.02) {
    ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7);
    ctx.strokeStyle = rgb(c, Math.min(1, glow)); ctx.lineWidth = 3.5; ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, R + 6, 0, 7);
    ctx.strokeStyle = rgb(c, glow * 0.35); ctx.lineWidth = 5; ctx.stroke();
  }
  for (let k = 0; k < 6; k++) {
    const a0 = liftAng[i] + k * Math.PI / 3;
    ctx.beginPath();
    for (let s = 0; s <= 18; s++) {
      const t = s / 18;
      const a = a0 + t * 0.85;
      const r = R * 0.22 + t * R * 0.72;
      const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
      if (s === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = glow > 0.05 ? rgb(c, 0.35 + glow * 0.4) : '#3c4a66';
    ctx.lineWidth = 2; ctx.stroke();
  }
  for (let k = 0; k < 6; k++) {
    const a = liftAng[i] + k * Math.PI / 3;
    ctx.beginPath(); ctx.moveTo(cx + R * 0.18 * Math.cos(a), cy + R * 0.18 * Math.sin(a));
    ctx.lineTo(cx + R * 0.97 * Math.cos(a), cy + R * 0.97 * Math.sin(a));
    ctx.strokeStyle = '#2c3a52'; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.beginPath(); ctx.arc(cx + (R - 7) * Math.cos(a), cy + (R - 7) * Math.sin(a), 8, 0, 7);
    ctx.strokeStyle = '#2c3a52'; ctx.lineWidth = 1.5; ctx.stroke();
  }
  ctx.beginPath(); ctx.arc(cx, cy, 10, 0, 7); ctx.fillStyle = '#202a38'; ctx.fill();
  ctx.strokeStyle = rgb(c, 0.5 + glow * 0.5); ctx.lineWidth = 2; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx, cy);
  ctx.lineTo(cx + 9 * Math.cos(liftAng[i]), cy + 9 * Math.sin(liftAng[i]));
  ctx.strokeStyle = rgb(c); ctx.lineWidth = 2.5; ctx.stroke();
  ctx.font = 'bold 10px monospace'; ctx.textAlign = 'center';
  ctx.fillStyle = rgb(c, 0.55 + glow * 0.45);
  ctx.fillText(note.name, cx, cy + 3.5);
  ctx.font = '9px monospace'; ctx.fillStyle = '#5c6c88';
  ctx.fillText(`${wheelRPM(i).toFixed(0)} RPM`, cx, cy + R + 16);
}

function drawLiftColumn() {
  for (let i = 0; i < N_WHEELS - 1; i++) {
    const y = wheelCY(i) + REL_OFF;
    ctx.strokeStyle = '#54432a'; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.moveTo(LIFT_CX + LWR + 8, y); ctx.lineTo(LIFT_CX + 4, y); ctx.stroke();
    ctx.strokeStyle = '#2e2418'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(LIFT_CX + LWR + 8, y - 3.5); ctx.lineTo(LIFT_CX + 4, y - 3.5); ctx.stroke();
  }
  ctx.strokeStyle = '#54432a'; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.moveTo(LIFT_CX + LWR + 8, TOP_BRIDGE_Y);
  ctx.lineTo(LANE_X + LANE_W_AREA, TOP_BRIDGE_Y); ctx.stroke();
  ctx.strokeStyle = '#2e2418'; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(LIFT_CX + LWR + 8, TOP_BRIDGE_Y - 3.5);
  ctx.lineTo(LANE_X + LANE_W_AREA, TOP_BRIDGE_Y - 3.5); ctx.stroke();
  ctx.strokeStyle = '#54432a'; ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(LFEED_P0[0], LFEED_P0[1]); ctx.lineTo(LFEED_P1[0], LFEED_P1[1]); ctx.stroke();
  for (const b of liftFeed) {
    const x = LFEED_P0[0] + (LFEED_P1[0] - LFEED_P0[0]) * b.t;
    const y = LFEED_P0[1] + (LFEED_P1[1] - LFEED_P0[1]) * b.t - 7;
    drawBall(x, y, NOTES[b.lane].col, 9);
  }
  for (let i = 0; i < N_WHEELS; i++) drawLiftWheel(i);
  for (const b of rideBalls) {
    const [x, y] = ballOnLiftWheel(b);
    drawBall(x, y, NOTES[b.lane].col, 9.5);
  }
  for (const b of bridgeBalls) {
    if (b.i < N_WHEELS - 1) {
      const y = wheelCY(b.i) + REL_OFF;
      const x = LIFT_CX + LWR + 8 - b.t * (LWR + 4);
      drawBall(x, y - 7, NOTES[b.lane].col, 9);
    } else {
      const x0 = LIFT_CX + LWR + 8;
      const x = x0 + b.t * 60;
      drawBall(x, TOP_BRIDGE_Y - 7, NOTES[b.lane].col, 9);
    }
  }
  ctx.font = '9px monospace'; ctx.fillStyle = '#8a7340'; ctx.textAlign = 'center';
  ctx.fillText('DA VINCI LIFT — 6 WHEELS', LIFT_CX, INSTR_Y + 14);
  ctx.fillText(`each lifts 90% of ½D · ${LIFT_PER_WHEEL_IN}" × ${N_WHEELS} = ${TOTAL_LIFT_IN}" (4.05 ft)`, LIFT_CX, INSTR_Y + 26);
}

function drawWheel1982() {
  const cx = WHEEL_CX, cy = WHEEL_CY, R = WHEEL_R;
  ctx.strokeStyle = '#232c3d'; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx, INSTR_Y - 4); ctx.stroke();
  ctx.fillStyle = '#1a2233'; ctx.fillRect(cx - 26, INSTR_Y - 8, 52, 8);
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7);
  ctx.fillStyle = 'rgba(16,21,31,.85)'; ctx.fill();
  ctx.lineWidth = 3; ctx.strokeStyle = '#3a4a64'; ctx.stroke();
  for (let k = 0; k < WHEEL_POCKETS; k++) {
    const a0 = wheelAng1982 + k * Math.PI * 2 / WHEEL_POCKETS;
    ctx.beginPath();
    for (let s = 0; s <= 20; s++) {
      const t = s / 20;
      const a = a0 + t * 0.85;
      const r = R * 0.28 + t * R * 0.66;
      const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
      if (s === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = '#4a5a7d'; ctx.lineWidth = 2; ctx.stroke();
  }
  for (let k = 0; k < WHEEL_POCKETS; k++) {
    const a = wheelAng1982 + k * Math.PI * 2 / WHEEL_POCKETS;
    ctx.beginPath(); ctx.moveTo(cx + R * 0.2 * Math.cos(a), cy + R * 0.2 * Math.sin(a));
    ctx.lineTo(cx + R * 0.97 * Math.cos(a), cy + R * 0.97 * Math.sin(a));
    ctx.strokeStyle = '#2c3a52'; ctx.lineWidth = 1.5; ctx.stroke();
  }
  ctx.beginPath(); ctx.arc(cx, cy, 10, 0, 7); ctx.fillStyle = '#202a38'; ctx.fill();
  ctx.strokeStyle = '#4a5a7d'; ctx.lineWidth = 2; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx, cy);
  ctx.lineTo(cx + 9 * Math.cos(wheelAng1982), cy + 9 * Math.sin(wheelAng1982));
  ctx.strokeStyle = '#ffa050'; ctx.lineWidth = 2.5; ctx.stroke();
  ctx.beginPath(); ctx.arc(cx, cy, R + 14, -0.4, -1.6, true);
  ctx.strokeStyle = 'rgba(232,197,106,.5)'; ctx.lineWidth = 2; ctx.stroke();
  const ah = -1.6;
  ctx.beginPath();
  ctx.moveTo(cx + (R + 14) * Math.cos(ah), cy + (R + 14) * Math.sin(ah));
  ctx.lineTo(cx + (R + 20) * Math.cos(ah - 0.18), cy + (R + 20) * Math.sin(ah - 0.18));
  ctx.lineTo(cx + (R + 8) * Math.cos(ah - 0.22), cy + (R + 8) * Math.sin(ah - 0.22));
  ctx.closePath(); ctx.fillStyle = 'rgba(232,197,106,.6)'; ctx.fill();
  for (const ma of [MAG_A, MAG_B]) {
    const mx = cx + (R + 26) * Math.cos(ma), myy = cy + (R + 26) * Math.sin(ma);
    ctx.save(); ctx.translate(mx, myy); ctx.rotate(ma + Math.PI / 2);
    ctx.fillStyle = '#5a3030'; ctx.fillRect(-12, -7, 24, 14);
    ctx.fillStyle = '#c05050'; ctx.fillRect(-12, -7, 12, 14);
    ctx.strokeStyle = '#7d4040'; ctx.lineWidth = 1; ctx.strokeRect(-12, -7, 24, 14);
    ctx.restore();
    ctx.strokeStyle = '#e05050'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(mx, myy);
    ctx.lineTo(cx + (R + 6) * Math.cos(ma), cy + (R + 6) * Math.sin(ma)); ctx.stroke();
  }
  for (const b of wheelBalls) {
    const r = R * 0.28 + ((b.ang - ENTRY_ANG) / (EXIT_ANG - ENTRY_ANG)) * R * 0.6;
    drawBall(cx + r * Math.cos(b.ang), cy + r * Math.sin(b.ang), NOTES[b.lane].col, 9);
  }
  ctx.strokeStyle = '#54432a'; ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(FEED1982_P0[0], FEED1982_P0[1]); ctx.lineTo(FEED1982_P1[0], FEED1982_P1[1]); ctx.stroke();
  ctx.strokeStyle = '#2e2418'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(FEED1982_P0[0], FEED1982_P0[1] - 4); ctx.lineTo(FEED1982_P1[0], FEED1982_P1[1] - 4); ctx.stroke();
  for (const b of ovfFeed) {
    const x = FEED1982_P0[0] + (FEED1982_P1[0] - FEED1982_P0[0]) * b.t;
    const y = FEED1982_P0[1] + (FEED1982_P1[1] - FEED1982_P0[1]) * b.t - 7;
    drawBall(x, y, NOTES[b.lane].col, 9);
  }
  ctx.strokeStyle = '#54432a'; ctx.lineWidth = 5;
  ctx.beginPath();
  for (let s = 0; s <= 24; s++) {
    const p = bez3(RET_P0, RET_P1, RET_P2, s / 24);
    if (s === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
  }
  ctx.stroke();
  for (const b of retBalls) {
    const p = bez3(RET_P0, RET_P1, RET_P2, b.t);
    drawBall(p[0], p[1] - 6, NOTES[b.lane].col, 9);
  }
  ctx.font = '9px monospace'; ctx.fillStyle = '#8a7340'; ctx.textAlign = 'center';
  ctx.fillText('RUBIN 1982', cx, INSTR_Y + 14);
  ctx.fillText('OVERFLOW MACHINE', cx, INSTR_Y + 26);
  ctx.fillStyle = '#5c6c88';
  ctx.fillText(`${(ovfRate * 45).toFixed(0)} RPM`, cx, cy + 4);
}

function bez3(a, b, c, t) {
  const u = 1 - t;
  return [u * u * a[0] + 2 * u * t * b[0] + t * t * c[0],
          u * u * a[1] + 2 * u * t * b[1] + t * t * c[1]];
}

// ── snapshot strip: proportional bars + camera + history ribbon ──
const SNAP_BASE = 112, SNAP_MAXH = 44, CAM_Y = 56;
function drawSnapshotStrip() {
  ctx.font = '9px monospace'; ctx.textAlign = 'left';
  ctx.fillStyle = '#5c6c88';
  ctx.fillText('SOUNDSCAPE SNAPSHOT — bar height ∝ frequency distribution · camera reads → gate routes → hammers strike', LANE_X, 50);

  // history ribbon (snapshots in time, newest right) — top right of header
  const rx0 = W - 430, ry0 = 8, rw = 3.2, rh = 3.6;
  for (let j = 0; j < snapHistory.length; j++) {
    const snap = snapHistory[j];
    const x = rx0 + (26 - snapHistory.length + j) * (rw + 1.2);
    for (let i = 0; i < NUM_LANES; i++) {
      if (snap[i] <= 0.01) continue;
      ctx.fillStyle = rgb(NOTES[i].col, 0.16 + 0.5 * snap[i] * (j + 1) / 26);
      ctx.fillRect(x, ry0 + i * rh, rw, rh - 0.6);
    }
  }
  ctx.font = '8px monospace'; ctx.fillStyle = '#3a4a64';
  ctx.fillText('SNAPSHOTS IN TIME →', rx0, ry0 + NUM_LANES * rh + 9);

  // proportional bars
  for (let i = 0; i < NUM_LANES; i++) {
    const cx = laneCx(i), c = NOTES[i].col;
    const h = 4 + snapBars[i] * SNAP_MAXH;
    const bw = LANE_W * 0.52;
    ctx.fillStyle = rgb(c.map(v => Math.max(12, v * 0.14)));
    ctx.fillRect(cx - bw / 2, SNAP_BASE - 4, bw, 4);
    if (snapBars[i] > 0.02) {
      const g = ctx.createLinearGradient(0, SNAP_BASE - h, 0, SNAP_BASE);
      g.addColorStop(0, rgb(c, 0.95));
      g.addColorStop(1, rgb(c, 0.30));
      ctx.fillStyle = g;
      ctx.fillRect(cx - bw / 2, SNAP_BASE - h, bw, h);
      ctx.strokeStyle = rgb(c, 0.8); ctx.lineWidth = 1;
      ctx.strokeRect(cx - bw / 2, SNAP_BASE - h, bw, h);
    }
    ctx.font = '8px monospace'; ctx.fillStyle = '#32405a'; ctx.textAlign = 'center';
    ctx.fillText(NOTES[i].name, cx, SNAP_BASE + 10);
  }
  ctx.strokeStyle = '#1c2430'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(LANE_X, SNAP_BASE); ctx.lineTo(LANE_X + LANE_W_AREA, SNAP_BASE); ctx.stroke();

  // the camera — sweeps the snapshot, flashes on read
  const camX = LANE_X + (((songMs / 2200) % 1) + 1) % 1 * LANE_W_AREA;
  if (flashBeam > 0.02 && gateState.pending) {
    ctx.strokeStyle = `rgba(232,197,106,${flashBeam * 0.7})`; ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(camX, CAM_Y + 8);
    ctx.lineTo(gateState.x, BANK_Y + 24); ctx.stroke();
    ctx.setLineDash([]);
  }
  ctx.fillStyle = camFlash > 0.05 ? '#e8c56a' : '#2a3548';
  ctx.beginPath(); ctx.roundRect(camX - 13, CAM_Y - 7, 26, 15, 4); ctx.fill();
  ctx.strokeStyle = '#4a5a7d'; ctx.lineWidth = 1; ctx.stroke();
  ctx.beginPath(); ctx.arc(camX, CAM_Y + 1, 4.5, 0, 7);
  ctx.fillStyle = camFlash > 0.05 ? '#fff' : '#8fa3c4'; ctx.fill();
  ctx.font = '8px monospace'; ctx.fillStyle = '#5c6c88'; ctx.textAlign = 'center';
  ctx.fillText('CAMERA', camX, CAM_Y - 12);
}

// ── holding bank + gate router ───────────────────────────────────
function drawBankAndGate() {
  // rail + tank label (PE at the top of the tank)
  ctx.strokeStyle = '#6b5636'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(LANE_X, BANK_Y); ctx.lineTo(LANE_X + LANE_W_AREA, BANK_Y); ctx.stroke();
  for (let k = 0; k < SUPPLY; k++) {
    ctx.beginPath(); ctx.arc(slotX(k), BANK_Y, 2, 0, 7);
    ctx.fillStyle = '#2a3040'; ctx.fill();
  }
  ctx.font = '9px monospace'; ctx.textAlign = 'left'; ctx.fillStyle = '#8a7340';
  ctx.fillText(`HOLDING BANK — POTENTIAL ENERGY · ${bankBalls.length} settled · gate routes where needed`, LANE_X + 4, BANK_Y - 28);

  // settled + sliding balls (all visible, seated on the rail at release height)
  for (const b of bankBalls) {
    drawBall(b.x, BANK_Y - 9, NOTES[b.col].col, 8.5);
  }

  // gate carriage
  const gx = gateState.x;
  ctx.fillStyle = gateState.pending ? '#243049' : '#1a2233';
  ctx.beginPath(); ctx.roundRect(gx - 17, BANK_Y + 4, 34, 16, 3); ctx.fill();
  ctx.strokeStyle = gateState.pending ? '#e8c56a' : '#2e3a52'; ctx.lineWidth = 1.5;
  ctx.strokeRect(gx - 17, BANK_Y + 4, 34, 16);
  ctx.fillStyle = '#0a0d14'; ctx.fillRect(gx - 6, BANK_Y + 4, 12, 5);  // gate opening
  ctx.font = '8px monospace'; ctx.fillStyle = gateState.pending ? '#e8c56a' : '#5c6c88';
  ctx.textAlign = 'center';
  ctx.fillText('GATE', gx, BANK_Y + 30);
}

// ── ledger band: balance, gears, flower field ────────────────────
function drawGear(x, y, r, teeth, ang, col, label, sub) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
  ctx.beginPath();
  for (let k = 0; k < teeth; k++) {
    const a0 = k * 2 * Math.PI / teeth;
    const a1 = a0 + Math.PI / teeth * 0.55;
    const a2 = a0 + Math.PI / teeth;
    const a3 = a0 + Math.PI / teeth * 1.55;
    ctx.lineTo((r + 5) * Math.cos(a0), (r + 5) * Math.sin(a0));
    ctx.lineTo((r + 5) * Math.cos(a1), (r + 5) * Math.sin(a1));
    ctx.lineTo(r * Math.cos(a2), r * Math.sin(a2));
    ctx.lineTo(r * Math.cos(a3), r * Math.sin(a3));
  }
  ctx.closePath();
  ctx.fillStyle = rgb(col, 0.16); ctx.fill();
  ctx.strokeStyle = rgb(col, 0.8); ctx.lineWidth = 1.5; ctx.stroke();
  ctx.beginPath(); ctx.arc(0, 0, r * 0.35, 0, 7);
  ctx.strokeStyle = rgb(col, 0.5); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(r * 0.8, 0);
  ctx.strokeStyle = rgb(col, 0.9); ctx.lineWidth = 2; ctx.stroke();
  ctx.restore();
  ctx.font = 'bold 9px monospace'; ctx.fillStyle = rgb(col); ctx.textAlign = 'center';
  ctx.fillText(label, x, y - r - 12);
  ctx.font = '9px monospace'; ctx.fillStyle = '#8fa3c4';
  ctx.fillText(sub, x, y + r + 16);
}

function currentTotals() {
  let pe = 0, ke = 0;
  // in-flight: PE(y) + KE, with KE from conservation (exact — no cinematic scaling)
  for (const b of fieldBalls) { pe += peOfY(b.y); ke += Math.max(0, PE_PER_DROP - peOfY(b.y)); }
  for (const b of bankBalls) pe += peOfY(BANK_Y);     // seated at release height
  for (const b of rideBalls) { const [x, y] = ballOnLiftWheel(b); pe += peOfY(y); }
  for (const b of bridgeBalls) {
    const y = b.i < N_WHEELS - 1 ? wheelCY(b.i) + REL_OFF : TOP_BRIDGE_Y;
    pe += peOfY(y);                                   // flat bridges — no height change
  }
  // tray, lift-feed, and the whole 1982 bypass circuit are passive
  // recirculators below the strike line: PE-neutral by construction
  // (trayBalls, liftFeed, ovfFeed, wheelBalls, retBalls all count 0).
  return { pe, ke };
}

function drawLedger() {
  const y0 = INSTR_Y + INSTR_H + 4;
  ctx.strokeStyle = '#141b26'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(LANE_X, y0); ctx.lineTo(W - RIGHT_W, y0); ctx.stroke();

  // ── flower field (regenerative output) ──
  const fx0 = LANE_X + 8, fx1 = LANE_X + 470;
  ctx.font = '9px monospace'; ctx.fillStyle = '#4caf7d'; ctx.textAlign = 'left';
  ctx.fillText(`HONEYTON, WV — FLOWER FIELD · ${flowers} planted · adds more than it takes`, fx0, y0 + 14);
  for (let k = 0; k < Math.min(flowers, 30); k++) {
    const sp = flowerSpots[k % flowerSpots.length];
    const x = fx0 + 10 + sp.fx * (fx1 - fx0 - 20);
    const y = y0 + 58 - sp.fy * 30;
    const c = NOTES[sp.c].col;
    ctx.strokeStyle = '#3d6b3d'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(x, y + 12); ctx.lineTo(x, y); ctx.stroke();
    for (let p = 0; p < 5; p++) {
      const a = sp.ph + p * 2 * Math.PI / 5;
      ctx.beginPath(); ctx.arc(x + 3.4 * Math.cos(a), y + 3.4 * Math.sin(a), 2.6, 0, 7);
      ctx.fillStyle = rgb(c, 0.9); ctx.fill();
    }
    ctx.beginPath(); ctx.arc(x, y, 2, 0, 7); ctx.fillStyle = '#e8c56a'; ctx.fill();
  }
  ctx.font = '8px monospace'; ctx.fillStyle = '#3a5a44';
  ctx.fillText('flowers → nectar → bees → honey → the system recharges', fx0, y0 + 70);

  // ── balance: balanced at every snapshot ──
  // identity: IN = OUT(radiated sound) + STORED(PE+KE) + HARVESTED(money channel)
  const bx = LANE_X + 620;
  const { pe, ke } = currentTotals();
  const stored = pe + ke;                             // every ball's PE + KE, tracked
  const harvested = noteCount * HARVEST_J;            // surplus → money → flowers
  const lhs = energyIn, rhs = energyOut + stored + harvested;
  const diff = lhs - rhs;
  const tilt = Math.max(-0.05, Math.min(0.05, diff * 0.5));
  ctx.strokeStyle = '#4a5a7d'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(bx, y0 + 52); ctx.lineTo(bx, y0 + 26); ctx.stroke();
  ctx.save(); ctx.translate(bx, y0 + 26); ctx.rotate(tilt);
  ctx.strokeStyle = '#8fa3c4'; ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.moveTo(-58, 0); ctx.lineTo(58, 0); ctx.stroke();
  for (const s of [-58, 58]) {
    ctx.beginPath(); ctx.moveTo(s, 0); ctx.lineTo(s - 8, 14); ctx.lineTo(s + 8, 14); ctx.closePath();
    ctx.strokeStyle = '#4a5a7d'; ctx.lineWidth = 1; ctx.stroke();
  }
  ctx.restore();
  ctx.font = '9px monospace'; ctx.textAlign = 'center';
  ctx.fillStyle = '#e8c56a';
  ctx.fillText(`IN ${lhs.toFixed(1)} J`, bx - 58, y0 + 20);
  ctx.fillText(`OUT+STORED+HARVEST ${rhs.toFixed(1)} J`, bx + 58, y0 + 20);
  ctx.fillStyle = Math.abs(diff) <= 0.05 + 0.03 * lhs ? '#4caf7d' : '#e07070';
  ctx.font = 'bold 9px monospace';
  ctx.fillText('BALANCED AT EVERY SNAPSHOT', bx, y0 + 68);

  // ── gears: PE → MOTION → SOUND → MONEY ──
  const gx0 = LANE_X + 800, gy = y0 + 40;
  drawGear(gx0,        gy, 24, 10,  gearAng[0], [232, 197, 106], 'PE',    `${(pe).toFixed(2)} J stored`);
  drawGear(gx0 + 56,   gy, 24, 10, -gearAng[1], [64, 140, 220],  'MOTION',`${(ke).toFixed(2)} J falling`);
  drawGear(gx0 + 112,  gy, 24, 10,  gearAng[2], [130, 175, 60],  'SOUND', `${noteCount} notes`);
  drawGear(gx0 + 168,  gy, 24, 10, -gearAng[3], [210, 175, 60],  'MONEY', `$${money.toFixed(2)}`);
  ctx.font = '8px monospace'; ctx.fillStyle = '#5c6c88'; ctx.textAlign = 'center';
  ctx.fillText('potential energy at the top of the tank → motion → sound → money → flowers', gx0 + 84, y0 + 78);
}

function draw() {
  ctx.fillStyle = '#05070b'; ctx.fillRect(0, 0, W, H);

  // header
  const tot = totalBalls();
  ctx.font = 'bold 14px monospace'; ctx.fillStyle = '#8c9ebe'; ctx.textAlign = 'left';
  ctx.fillText('HONEYLIGHT MARBLE QUIPU  ·  SNAPSHOT SYSTEM  ·  mapping the system', 12, 22);
  ctx.font = '11px monospace';
  ctx.fillStyle = tot === SUPPLY ? '#4caf7d' : '#e05050';
  ctx.fillText(`SUPPLY ${tot}/${SUPPLY} CONSERVED (110% of max ${MAX_DEMAND}) · position + velocity of every ball · balanced at every snapshot`, 12, 38);
  const pct = Math.min(1, Math.max(0, songMs / SONG.totalMs));
  ctx.fillStyle = '#101620'; ctx.fillRect(LANE_X, 44, LANE_W_AREA - 440, 3);
  ctx.fillStyle = '#327dc3'; ctx.fillRect(LANE_X, 44, (LANE_W_AREA - 440) * pct, 3);

  drawSnapshotStrip();
  drawBankAndGate();

  // lane frame + dividers + glow wash
  ctx.strokeStyle = '#1c2430'; ctx.lineWidth = 2;
  ctx.strokeRect(LANE_X, LANE_Y, LANE_W_AREA, INSTR_Y - LANE_Y);
  for (let i = 0; i < NUM_LANES; i++) {
    const lx = LANE_X + i * LANE_W;
    if (i > 0) { ctx.strokeStyle = '#10151e'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(lx, LANE_Y); ctx.lineTo(lx, INSTR_Y - 6); ctx.stroke(); }
    if (laneGlow[i] > 0.04) {
      ctx.fillStyle = rgb(NOTES[i].col, laneGlow[i] * 0.07);
      ctx.fillRect(lx + 1, LANE_Y, LANE_W - 2, INSTR_Y - LANE_Y - 4);
    }
  }

  drawLiftColumn();
  drawWheel1982();

  // ── instrument strip: the ALIENPAN ─────────────────────────────
  ctx.fillStyle = '#161210';
  ctx.beginPath(); ctx.roundRect(LANE_X - 6, INSTR_Y, LANE_W_AREA + 12, INSTR_H, 8); ctx.fill();
  const grad = ctx.createLinearGradient(0, INSTR_Y, 0, INSTR_Y + INSTR_H);
  grad.addColorStop(0, 'rgba(120,84,40,.28)');
  grad.addColorStop(0.5, 'rgba(70,50,26,.12)');
  grad.addColorStop(1, 'rgba(30,22,12,.3)');
  ctx.fillStyle = grad;
  ctx.beginPath(); ctx.roundRect(LANE_X - 6, INSTR_Y, LANE_W_AREA + 12, INSTR_H, 8); ctx.fill();
  ctx.strokeStyle = '#3d3020'; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.roundRect(LANE_X - 6, INSTR_Y, LANE_W_AREA + 12, INSTR_H, 8); ctx.stroke();
  ctx.font = '9px monospace'; ctx.fillStyle = '#6b5636'; ctx.textAlign = 'left';
  ctx.fillText('ALIENPAN · D KURD · 440 Hz · AISI 430', LANE_X + 4, INSTR_Y + INSTR_H - 8);

  const FIELD_Y = INSTR_Y + 54;
  for (let i = 0; i < NUM_LANES; i++) {
    const cx = laneCx(i), c = NOTES[i].col;
    ctx.beginPath(); ctx.ellipse(cx, FIELD_Y, LANE_W * 0.34, 13, 0, 0, 7);
    ctx.fillStyle = toneFlash[i] > 0.02 ? rgb(c, 0.25 + toneFlash[i] * 0.75) : '#241c12';
    ctx.fill();
    ctx.strokeStyle = toneFlash[i] > 0.02 ? rgb(c) : '#4a3a24'; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.beginPath(); ctx.ellipse(cx, FIELD_Y, 4, 2.4, 0, 0, 7);
    ctx.fillStyle = toneFlash[i] > 0.02 ? '#fff' : '#120d08'; ctx.fill();
    for (const r of ripples) if (r.lane === i) {
      const rr = 8 + r.age * 46;
      ctx.beginPath(); ctx.ellipse(cx, FIELD_Y, rr, rr * 0.42, 0, 0, 7);
      ctx.strokeStyle = rgb(c, Math.max(0, 0.8 - r.age * 1.3)); ctx.lineWidth = 2; ctx.stroke();
    }
    const swing = hammerSwing[i];
    const plunge = Math.pow(swing, 0.6) * 16;
    const hy = INSTR_Y + 8;
    ctx.fillStyle = '#2a303a';
    ctx.beginPath(); ctx.roundRect(cx - 9, hy, 18, 14, 3); ctx.fill();
    ctx.strokeStyle = swing > 0.05 ? rgb(c) : '#3a4352'; ctx.lineWidth = 1;
    ctx.strokeRect(cx - 9, hy, 18, 14);
    ctx.strokeStyle = '#8a95a5'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(cx, hy + 14); ctx.lineTo(cx, hy + 18 + plunge); ctx.stroke();
    const mY = hy + 22 + plunge;
    ctx.beginPath(); ctx.arc(cx, mY, 6, 0, 7);
    ctx.fillStyle = swing > 0.05 ? rgb(c) : '#586270'; ctx.fill();
    ctx.strokeStyle = '#14181f'; ctx.lineWidth = 1; ctx.stroke();
    if (swing > 0.55) {
      ctx.beginPath(); ctx.arc(cx, FIELD_Y - 6, 10, 0, 7);
      ctx.fillStyle = rgb(c, (swing - 0.55) * 1.4); ctx.fill();
    }
  }

  // return tray
  ctx.fillStyle = '#141c28';
  ctx.beginPath(); ctx.roundRect(LANE_X - 6, TRAY_Y, LANE_W_AREA + 12, 8, 3); ctx.fill();
  ctx.strokeStyle = gate === 'play' ? '#1e4030' : '#402020'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(LANE_X, TRAY_Y + 4); ctx.lineTo(LANE_X + LANE_W_AREA, TRAY_Y + 4); ctx.stroke();
  ctx.font = '10px monospace'; ctx.textAlign = 'center';
  ctx.fillStyle = gate === 'play' ? '#4caf7d' : '#e07070';
  ctx.fillText(gate === 'play'
    ? '◀ PLAY: strike → tray → da Vinci lift → holding bank (closed loop)'
    : 'BYPASS: pass-through → tray → 1982 wheel → lift ▶',
    LANE_X + LANE_W_AREA / 2, TRAY_Y + 20);
  for (const b of trayBalls) drawBall(b.x, TRAY_Y - 6, NOTES[b.lane].col, 9);

  // field balls (falling — every one visible)
  for (const b of fieldBalls) drawBall(b.x, b.y, NOTES[b.lane].col);

  drawLedger();

  // footer readouts
  const stats = [
    ['GATE', gate === 'play' ? '▶ PLAY' : '⏭ BYPASS'],
    ['NOTES', String(noteCount)],
    ['MONEY', `$${money.toFixed(2)}`],
    ['FLOWERS', `${flowers} planted`],
    ['BANK', `${bankBalls.length}`],
    ['QUEUE', `${dispatchQueue.length}`],
    ['IN FLIGHT', String(fieldBalls.length)],
    ['ENERGY IN', `${energyIn.toFixed(1)} J`],
    ['SUPPLY', `${tot}/${SUPPLY}`],
  ];
  let sx = LANE_X, sy = H - 14;
  ctx.textAlign = 'left';
  for (const [k, v] of stats) {
    ctx.font = '9px monospace'; ctx.fillStyle = '#3a4a64'; ctx.fillText(k, sx, sy - 14);
    ctx.font = '12px monospace';
    ctx.fillStyle = (k === 'GATE') ? (gate === 'play' ? '#4caf7d' : '#e07070')
      : (k === 'SUPPLY' && tot !== SUPPLY) ? '#e05050' : '#9fb2d0';
    ctx.fillText(v, sx, sy);
    sx += Math.max(ctx.measureText(k).width, ctx.measureText(v).width) + 26;
  }
}

// ── main loop ────────────────────────────────────────────────────
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  if (!paused) step(dt);
  draw();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// ── controls ─────────────────────────────────────────────────────
const gateBtn = document.getElementById('gateBtn');
function setGate(g) {
  gate = g;
  gateBtn.textContent = g === 'play' ? '▶ GATE: PLAY' : '⏭ GATE: BYPASS';
  gateBtn.className = 'btn ' + (g === 'play' ? 'play active' : 'bypass active');
}
gateBtn.onclick = () => setGate(gate === 'play' ? 'bypass' : 'play');

document.getElementById('ovfMinus').onclick = () => { ovfRate = Math.max(0.1, Math.round((ovfRate - 0.1) * 10) / 10); upd(); };
document.getElementById('ovfPlus').onclick = () => { ovfRate = Math.min(8.0, Math.round((ovfRate + 0.1) * 10) / 10); upd(); };
function upd() { document.getElementById('ovfReadout').textContent = ovfRate.toFixed(1) + '×'; }

document.getElementById('testBtn').onclick = () => {
  initAudio();
  NOTES.forEach((n, i) => setTimeout(() => strike(i), i * 130));
};
const pauseBtn = document.getElementById('pauseBtn');
pauseBtn.onclick = () => { paused = !paused; pauseBtn.textContent = paused ? '▶ RESUME' : '⏸ PAUSE'; };
document.getElementById('restartBtn').onclick = resetSong;

cv.addEventListener('pointerdown', e => {
  const rect = cv.getBoundingClientRect();
  const x = (e.clientX - rect.left) * (W / rect.width);
  const y = (e.clientY - rect.top) * (H / rect.height);
  if (x > LANE_X && x < LANE_X + LANE_W_AREA && y > LANE_Y && y < INSTR_Y) {
    const lane = Math.min(NUM_LANES - 1, Math.floor((x - LANE_X) / LANE_W));
    requestDrop(lane, true);
  }
});

window.addEventListener('keydown', e => {
  if (e.key === 'g' || e.key === 'G') setGate(gate === 'play' ? 'bypass' : 'play');
  else if (e.key === '-' || e.key === '_') { ovfRate = Math.max(0.1, ovfRate - 0.1); upd(); }
  else if (e.key === '+' || e.key === '=') { ovfRate = Math.min(8.0, ovfRate + 0.1); upd(); }
  else if (e.key === ' ') { e.preventDefault(); pauseBtn.click(); }
  else if (e.key === 'r' || e.key === 'R') resetSong();
  else if (/^[0-9]$/.test(e.key)) {
    const lane = e.key === '0' ? 9 : parseInt(e.key) - 1;
    if (lane < NUM_LANES) requestDrop(lane, true);
  }
});

function drive(seconds) {
  const dtMs = 1000 / 60;
  let until = nowMs + seconds * 1000;
  while (nowMs < until) { nowMs += dtMs; if (rafCb) { const cb = rafCb; rafCb = null; cb(nowMs); } }
}
const probe = tag => {
  const { pe, ke } = currentTotals();
  const diff = energyIn - energyOut - pe - ke - noteCount * HARVEST_J;
  console.log(`${tag} t=${(songMs/1000).toFixed(1)}s total=${totalBalls()} bank=${bankBalls.length} notes=${noteCount} diff=${diff.toFixed(6)}`);
};
drive(14); probe('A');
drive(14); probe('B');
drive(14); probe('C');
[1,3,5,7,8,9].forEach(l => requestDrop(l, true));
drive(10); probe('D-burst6');
drive(16); probe('E');
// bypass cycle test
setGate && setGate('bypass');
drive(8); probe('F-bypass');
setGate && setGate('play');
drive(14); probe('G-play');
