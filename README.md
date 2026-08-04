# Honeylight Workbench — chromatic-roll

Mark Rubin / Honeylight  
Queenbee Machine · `/Users/queenbee/chromatic-roll/`

---

## Python environment

```bash
/Users/queenbee/chromatic-roll/venv/bin/python3  honeylight_full.py
```

All scripts use the venv shebang — double-click or run directly.

---

## Files

| File | Description |
|---|---|
| `honeylight_full.py` | ⭐ **CURRENT** — Full system: Rubin Lifting Ramp + 16-lane instrument + Overflow ramp. Gate control. Tunable overflow rate. |
| `honeylight_proto.py` | 4ft × 8ft prototype sim — 16 lanes, 16 hammers, golf balls, Ode to Joy |
| `honeylight.py` | Original visual sim — LED quipu bar, marbles, hammers, waveform |
| `chromatic_roll.py` | Chromatic optical roll — AI Markov composer, 8 lanes, color roll |
| `happy_birthday_roll.py` | Happy Birthday on the optical roll |
| `happy_birthday_2oct.py` | 2-octave Happy Birthday render |
| `Honeylight_Quipu_Parts_List.md` | Complete prototype parts list — $2,431 total |

---

## System Architecture

```
  ┌─────────────────────────────────────────────────┐
  │           RUBIN LIFTING RAMP (left)             │
  │   Double helix A↑CW + B↑CCW · 0.25HP · 5ft     │
  └────────────────┬────────────────────────────────┘
                   │ delivers balls to lane tops
  ┌────────────────▼────────────────────────────────┐
  │          16-LANE INSTRUMENT  (centre)           │
  │  Golf balls · IR sensors · Solenoid hammers     │
  │  Handpan tongue drum · WS2812B LED Quipu bar   │
  │  Raspberry Pi Zero 2W · D natural minor         │
  └────────────────┬─────────────────┬──────────────┘
                   │ play mode       │ bypass mode (gate G)
              return tray       overflow right
                   │                 │
  ┌────────────────▼─────────────────▼──────────────┐
  │         OVERFLOW RAMP (right)                   │
  │   Double helix A↓CCW + B↓CW · 0.25HP · 5ft     │
  │   Tunable rate  (− / + keys or on-screen)       │
  └─────────────────────────────────────────────────┘
```

---

## Controls (honeylight_full.py)

| Key | Action |
|---|---|
| `G` | Toggle gate: Play instrument ↔ Bypass to overflow |
| `−` / `+` | Decrease / Increase overflow rate |
| `SPACE` | Pause / Resume |
| `R` | Restart song |
| `CLICK` lane | Drop ball manually |
| `1–9, 0` | Drop in lanes 1–10 |
| `Q W E T Y U` | Drop in lanes 11–16 |
| `ESC` | Quit |

---

## Roadmap

| Version | Description |
|---|---|
| **v0 (now)** | Prototype simulator — single drum, 16 lanes, solenoid arch |
| **v1 (2025)** | Physical build — 4×8 frame, golf balls, 0.25HP motor, Rubin ramps |
| **v2 (2026)** | Hybrid two-axis gimbal actuator — theatrical rotating arm |
| **v3 (2026+)** | Two instruments, two canons playing simultaneously |
| **v4** | 88 lanes — full chromatic range, all human music |

---

## Physics Reference

```
Golf ball:        1.68 in dia · 1.62 oz (45.9 g)
5 ft drop:        620–720 ms fall time
Min ball spacing: 247 ms (30° ramp)  →  8th notes @ 121 BPM
Motor:            0.25 HP = 186W · lifts 190 balls/sec max
Musical rate:     ~2 balls/sec  (1.5W, <1% motor load)
Noise threshold:  >12 simultaneous notes on single instrument
Sweet spot:       4–6 simultaneous lanes · 60–120 BPM
Upper limit:      16 lanes = string quartet = all coherent music
```

---

*"The runners run in parallel."*  
*Honeylight Marble Quipu · Potomac MD 20854*
