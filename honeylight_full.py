#!/Users/queenbee/chromatic-roll/venv/bin/python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║   HONEYLIGHT MARBLE QUIPU — Full System                                 ║
║   Rubin Lifting Ramp  +  16-lane instrument  +  Overflow Ramp           ║
║                                                                          ║
║   The Rubin Lifting Ramp:                                                ║
║     Two nested counter-rotating helical screws (double-helix)           ║
║     Helix A: clockwise  · Helix B: counter-clockwise                    ║
║     Golf balls ride the nip between them — both surfaces push UP        ║
║     Archimedean screw principle + twin-screw grip + Da Vinci helix      ║
║     Motor: 0.25 HP   Lift: 5 feet   Rate: 10% above musical fall rate   ║
║                                                                          ║
║   Overflow Ramp (right side):                                            ║
║     Identical twin-screw ramp, reversed — descends balls                ║
║     Bypass gate routes all balls here (skips instrument)                ║
║     Overflow rate is tunable  (− / + keys or on-screen buttons)         ║
║                                                                          ║
║   CONTROLS                                                               ║
║     SPACE     Pause / Resume                                             ║
║     R         Restart song                                               ║
║     G         Toggle gate (Play ↔ Bypass to overflow)                   ║
║     − / +     Decrease / Increase overflow rate                          ║
║     CLICK     Drop ball in lane                                          ║
║     1–9,0     Lanes 1–10    Q W E T Y U  Lanes 11–16                    ║
║     ESC       Quit                                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import pygame
import numpy as np
import math
import sys
from collections import deque
from typing import List, Tuple

# ══════════════════════════════════════════════════════════════════════════
# INIT
# ══════════════════════════════════════════════════════════════════════════
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

SW, SH   = 1500, 900
screen   = pygame.display.set_mode((SW, SH))
pygame.display.set_caption(
    "Honeylight Marble Quipu  —  Rubin Lifting Ramp  ·  Full System")
clock    = pygame.time.Clock()
FPS      = 60

FONT_T   = pygame.font.SysFont('monospace', 14, bold=True)
FONT_S   = pygame.font.SysFont('monospace', 11)
FONT_XS  = pygame.font.SysFont('monospace', 10)
FONT_N   = pygame.font.SysFont('monospace', 10, bold=True)
FONT_LG  = pygame.font.SysFont('monospace', 18, bold=True)

# ══════════════════════════════════════════════════════════════════════════
# LAYOUT   maps to physical 5 ft tall × 8 ft wide frame
# ══════════════════════════════════════════════════════════════════════════
RAMP_W       = 160
HEADER_H     = 70
FOOTER_H     = 120

LANE_AREA_X  = RAMP_W               # 160
LANE_AREA_Y  = HEADER_H             # 70
LANE_AREA_W  = SW - 2 * RAMP_W     # 1180
LANE_AREA_H  = SH - HEADER_H - FOOTER_H  # 710
NUM_LANES    = 16
LANE_W       = LANE_AREA_W // NUM_LANES   # 73
BALL_R       = max(9, LANE_W // 3 - 2)   # 22

HAMMER_Y     = LANE_AREA_Y + LANE_AREA_H - 16   # 764

# Ramp geometry
RAMP_Y_TOP   = LANE_AREA_Y + 10    # 80  — top of 5-ft column
RAMP_Y_BOT   = HAMMER_Y            # 764 — bottom (ball exits here into lane top)
RAMP_HEIGHT  = RAMP_Y_BOT - RAMP_Y_TOP   # 684 px  = 5 ft

HELIX_AMP    = 56    # ± pixels from ramp centre (helix radius)
HELIX_TURNS  = 8     # full revolutions in 5 ft
HELIX_SEGS   = 160   # render resolution

LIFT_CX      = RAMP_W // 2          # 80   — centre x, lift ramp
OVFL_CX      = SW - RAMP_W // 2    # 1420 — centre x, overflow ramp

# ══════════════════════════════════════════════════════════════════════════
# BALL PHYSICS  (5-ft free fall through near-vertical tube)
# ══════════════════════════════════════════════════════════════════════════
BALL_START_Y  = LANE_AREA_Y + BALL_R + 4    # 96   — release point at top
BALL_HIT_Y    = HAMMER_Y    - BALL_R        # 742  — solenoid strike point
FALL_DIST_PX  = BALL_HIT_Y - BALL_START_Y   # 646 px
FALL_TIME_S   = 0.72                         # 5 ft drop ≈ 720 ms
G_PX          = 2.0 * FALL_DIST_PX / (FALL_TIME_S ** 2)   # 2492 px/s²
FALL_TIME_MS  = int(FALL_TIME_S * 1000)      # 720 ms

MIN_GAP_MS    = 300   # minimum ms between consecutive balls in same lane

PX_PER_FOOT   = RAMP_HEIGHT / 5.0   # 136.8 px per foot

# ══════════════════════════════════════════════════════════════════════════
# MOTOR  —  0.25 HP
# ══════════════════════════════════════════════════════════════════════════
MOTOR_HP      = 0.25
MOTOR_W       = MOTOR_HP * 745.7   # 186 W
# Lift rate physics: max balls/sec = (W × efficiency) / (m × g × h)
LIFT_EFF      = 0.70
BALL_KG       = 0.04593
LIFT_H_M      = 1.524              # 5 ft in metres
W_PER_BS      = BALL_KG * 9.81 * LIFT_H_M   # watts needed per ball/sec
MAX_LIFT_BS   = (MOTOR_W * LIFT_EFF) / W_PER_BS   # ≈ 190 balls/sec

MUSICAL_RATE  = 2.0   # typical balls/sec during play
SURPLUS       = 1.10  # 10% above fall rate
# 1 ball/rev model → RPM = balls/sec × 60
BASE_LIFT_RPM = MUSICAL_RATE * SURPLUS * 60   # ≈ 132 RPM
BASE_OVFL_RPM = 45.0   # overflow default (tunable)

# ══════════════════════════════════════════════════════════════════════════
# NOTE DATA  —  D natural minor, 2 octaves (D3 – E5), 16 lanes
#               Twilight Goat Pasture colour palette
# ══════════════════════════════════════════════════════════════════════════
NOTE_DATA: List[Tuple] = [
    ('D3',  146.83, (195,  45,  45)),
    ('E3',  164.81, (210,  90,  20)),
    ('F3',  174.61, (220, 140,  20)),
    ('G3',  196.00, (130, 175,  60)),
    ('A3',  220.00, ( 55, 160,  80)),
    ('Bb3', 233.08, ( 35, 165, 155)),
    ('C4',  261.63, ( 35, 130, 210)),
    ('D4',  293.66, ( 40, 105, 210)),
    ('E4',  329.63, ( 80,  70, 205)),
    ('F4',  349.23, (120,  55, 195)),
    ('G4',  392.00, (150,  55, 180)),
    ('A4',  440.00, (170,  55, 150)),
    ('Bb4', 466.16, (160, 175, 190)),
    ('C5',  523.25, (195, 200, 215)),
    ('D5',  587.33, (215,  90, 130)),
    ('E5',  659.25, (240, 135, 135)),
]
NAMES  = [n[0] for n in NOTE_DATA]
FREQS  = [n[1] for n in NOTE_DATA]
COLORS = [n[2] for n in NOTE_DATA]

def lane_cx(lane: int) -> int:
    return LANE_AREA_X + lane * LANE_W + LANE_W // 2

# ══════════════════════════════════════════════════════════════════════════
# SOUND SYNTHESIS  —  steel tongue drum
# ══════════════════════════════════════════════════════════════════════════
SR = 44100

def synth_tongue_drum(freq: float, dur=3.5, vol=0.70):
    n   = int(SR * dur)
    t   = np.linspace(0, dur, n, endpoint=False)
    atk = int(0.004 * SR);  dcy = int(0.180 * SR)
    env = np.empty(n, dtype=np.float32)
    env[:atk]       = np.linspace(0.0, 1.0, atk,  dtype=np.float32)
    ed              = atk + dcy
    env[atk:ed]     = np.linspace(1.0, 0.28, dcy, dtype=np.float32)
    env[ed:]        = (0.28 * np.exp(np.linspace(0.0, -5.0, n - ed),
                                     dtype=np.float32)).astype(np.float32)
    wave  = np.sin(2*np.pi*freq*t, dtype=np.float32) * env
    nyq   = SR * 0.45
    for fmul, amp, dec in [(2.76, 0.18, 4.0), (5.40, 0.06, 9.0)]:
        f2 = freq * fmul
        if f2 < nyq:
            wave += (amp * np.sin(2*np.pi*f2*t, dtype=np.float32) *
                     env * np.exp(-t*dec).astype(np.float32))
    rng   = np.random.default_rng(int(freq*100) & 0xFFFF)
    wave += (rng.uniform(-1.0, 1.0, n).astype(np.float32) *
             np.exp(-t*130.0).astype(np.float32) * 0.07)
    pk = np.max(np.abs(wave))
    if pk > 1e-9:
        wave = (wave / pk) * vol
    buf = np.ascontiguousarray(
        np.column_stack([wave, wave]) * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(buf)

print("🎵  Building sound cache (16 notes)…")
SOUNDS = []
for _i, (_nm, _fr, _) in enumerate(NOTE_DATA):
    SOUNDS.append(synth_tongue_drum(_fr))
    print(f"   [{_nm:5s}] {_fr:7.2f} Hz  {'█'*(_i+1)}{'░'*(15-_i)}", end='\r')
print("\n✅  Sound cache ready.\n")

# ══════════════════════════════════════════════════════════════════════════
# SONG  —  Ode to Joy, D natural minor, 120 BPM
# ══════════════════════════════════════════════════════════════════════════
QN, HN = 500, 1000
C4,D4,E4,F4,G4 = 6,7,8,9,10
D3,G3,A3       = 0,3,4

def build_song():
    mel = [
        (E4,0*QN),(E4,1*QN),(F4,2*QN),(G4,3*QN),
        (G4,4*QN),(F4,5*QN),(E4,6*QN),(D4,7*QN),
        (C4,8*QN),(C4,9*QN),(D4,10*QN),(E4,11*QN),
        (E4,12*QN),(D4,13*QN+QN//2),(D4,15*QN),
        (E4,16*QN),(E4,17*QN),(F4,18*QN),(G4,19*QN),
        (G4,20*QN),(F4,21*QN),(E4,22*QN),(D4,23*QN),
        (C4,24*QN),(C4,25*QN),(D4,26*QN),(E4,27*QN),
        (D4,28*QN),(C4,29*QN+QN//2),(C4,31*QN),
    ]
    bas = [
        (D3,0*HN),(A3,1*HN),(G3,2*HN),(A3,3*HN),
        (D3,4*HN),(G3,5*HN),(A3,6*HN),(D3,7*HN),
        (D3,8*HN),(A3,9*HN),(G3,10*HN),(A3,11*HN),
        (D3,12*HN),(G3,13*HN),(D3,14*HN),(D3,15*HN),
    ]
    return sorted(mel + bas, key=lambda e: e[1])

SONG          = build_song()
SONG_TOTAL_MS = max(t for _,t in SONG) + 2500

# ══════════════════════════════════════════════════════════════════════════
# FIELD BALL  (falling through the 16-lane instrument zone)
# ══════════════════════════════════════════════════════════════════════════
class FieldBall:
    __slots__ = ['lane','x','y','vy']
    def __init__(self, lane):
        self.lane = lane
        self.x    = float(lane_cx(lane))
        self.y    = float(BALL_START_Y)
        self.vy   = 0.0
    def update(self, dt):
        self.vy += G_PX * dt
        self.y  += self.vy * dt
    def draw(self, surf):
        ix,iy = int(self.x), int(self.y)
        r,g,b = COLORS[self.lane]
        pygame.draw.circle(surf,(0,0,0),(ix+2,iy+2),BALL_R)
        pygame.draw.circle(surf,(r,g,b),(ix,iy),BALL_R)
        pygame.draw.circle(surf,(255,255,255),(ix-BALL_R//3,iy-BALL_R//3),BALL_R//4)
        pygame.draw.circle(surf,(12,12,15),(ix,iy),BALL_R,1)

# ══════════════════════════════════════════════════════════════════════════
# RAMP BALL  (riding the double-helix)
# ══════════════════════════════════════════════════════════════════════════
class RampBall:
    __slots__ = ['progress','speed','lane','hx']
    def __init__(self, progress, speed, lane, hx=0):
        self.progress = float(progress)
        self.speed    = float(speed)
        self.lane     = lane
        self.hx       = hx   # 0 or 1 — which helix

# ══════════════════════════════════════════════════════════════════════════
# HELIX RAMP  —  The Rubin Lifting / Overflow Ramp
# ══════════════════════════════════════════════════════════════════════════
class HelixRamp:
    """
    Nested counter-rotating double-helix ball transport.
    going_up=True  → lift (Rubin Lifting Ramp, left side)
    going_up=False → overflow descent (right side, inverse)

    Helix A: clockwise rotation when going up   (colour: blue)
    Helix B: counter-clockwise when going up    (colour: amber)
    Their counter-rotation creates a rising nip between them —
    golf balls sit in this nip and are carried upward by both surfaces.
    On the overflow ramp, motor reverses → both surfaces carry downward.
    """

    # Helix colours
    COL_A      = (70,  150, 255)   # Helix A  (CW when lifting)
    COL_B      = (255, 165,  50)   # Helix B  (CCW when lifting)
    COL_A_DIM  = (18,  38,  65)
    COL_B_DIM  = (65,  42,  13)

    def __init__(self, cx, y_top, y_bot, going_up=True,
                 label="LIFT", rpm=BASE_LIFT_RPM):
        self.cx       = cx
        self.y_top    = y_top
        self.y_bot    = y_bot
        self.height   = y_bot - y_top
        self.going_up = going_up
        self.label    = label
        self.rpm      = rpm          # motor speed
        self.phase    = 0.0          # animation phase (radians)
        self.balls: List[RampBall] = []
        self.rate_mult = 1.0         # overflow rate multiplier
        self.balls_delivered = 0

        # Seed with some balls already in transit for visual richness
        for i in range(6):
            prog = (i + 1) / 7.0
            spd  = self._ball_speed()
            self.balls.append(RampBall(prog, spd, i * 2 % NUM_LANES, i % 2))

    def _ball_speed(self):
        """progress/sec  —  positive=up, negative=down."""
        # 1 ball/rev model: throughput = rpm/60 balls/sec
        # Ball traverses 0→1 in HELIX_TURNS revolutions
        # speed = rpm/60 / HELIX_TURNS  progress/sec
        spd = (self.rpm / 60.0) / HELIX_TURNS * self.rate_mult
        return spd if self.going_up else -spd

    def add_ball(self, lane):
        start = 0.0 if self.going_up else 1.0
        hx    = len(self.balls) % 2
        self.balls.append(RampBall(start, self._ball_speed(), lane, hx))

    def update(self, dt) -> List[int]:
        """Advance phase + balls. Returns list of lane indices that exited (delivered)."""
        # Phase: A rotates one way, B the other
        rad_s = self.rpm * 2 * math.pi / 60.0
        if self.going_up:
            self.phase += rad_s * dt
        else:
            self.phase -= rad_s * dt

        delivered = []
        survivors = []
        for b in self.balls:
            b.speed = self._ball_speed()   # update if rate changed
            b.progress += b.speed * dt
            if self.going_up and b.progress >= 1.0:
                delivered.append(b.lane)
                self.balls_delivered += 1
            elif not self.going_up and b.progress <= 0.0:
                delivered.append(b.lane)
                self.balls_delivered += 1
            else:
                survivors.append(b)
        self.balls = survivors
        return delivered

    def _pos(self, progress, hx_id):
        """Screen (x, y) and depth z for a point on helix hx_id."""
        # Helix A: phase offset 0; Helix B: phase offset π (counter-rotation)
        angle = progress * HELIX_TURNS * 2 * math.pi + self.phase
        if hx_id == 1:
            angle = -(progress * HELIX_TURNS * 2 * math.pi + self.phase) + math.pi
        x = self.cx + HELIX_AMP * math.sin(angle)
        y = self.y_bot - progress * self.height
        z = math.cos(angle)   # > 0 = in front
        return x, y, z

    def draw(self, surf: pygame.Surface):
        # ── Draw both helixes ──────────────────────────────────────────
        for hx_id in range(2):
            col_f = self.COL_A      if hx_id == 0 else self.COL_B
            col_b = self.COL_A_DIM  if hx_id == 0 else self.COL_B_DIM

            progs = [i / HELIX_SEGS for i in range(HELIX_SEGS + 1)]
            pts   = [self._pos(p, hx_id) for p in progs]

            # Draw back portions (dim) first, front (full) on top
            for front_pass in (False, True):
                col = col_f if front_pass else col_b
                w   = 3     if front_pass else 1
                px0, py0, pz0 = pts[0]
                for i in range(1, len(pts)):
                    px1, py1, pz1 = pts[i]
                    midz = (pz0 + pz1) / 2
                    if (midz > 0) == front_pass:
                        pygame.draw.line(surf, col,
                                         (int(px0), int(py0)),
                                         (int(px1), int(py1)), w)
                    px0,py0,pz0 = px1,py1,pz1

        # ── Draw balls on ramp ─────────────────────────────────────────
        for b in self.balls:
            x, y, z = self._pos(b.progress, b.hx)
            if z < -0.4:       # skip balls deep inside the helix
                continue
            r  = max(7, int(BALL_R * 0.70 + z * 5))
            rc, gc, bc = COLORS[b.lane]
            pygame.draw.circle(surf, (0,0,0), (int(x)+1, int(y)+1), r)
            pygame.draw.circle(surf, (rc,gc,bc), (int(x), int(y)), r)
            pygame.draw.circle(surf, (255,255,255),
                               (int(x)-r//3, int(y)-r//3), max(2,r//3))

        # ── Motor indicator ────────────────────────────────────────────
        self._draw_motor(surf)

        # ── Helix legend ───────────────────────────────────────────────
        if self.going_up:
            lx = self.cx - 70
            ta = FONT_XS.render("A ● CW  ↑", True, self.COL_A)
            tb = FONT_XS.render("B ● CCW ↑", True, self.COL_B)
        else:
            lx = self.cx - 70
            ta = FONT_XS.render("A ● CCW ↓", True, self.COL_A)
            tb = FONT_XS.render("B ● CW  ↓", True, self.COL_B)
        surf.blit(ta, (self.cx - ta.get_width()//2, self.y_top - 30))
        surf.blit(tb, (self.cx - tb.get_width()//2, self.y_top - 18))

    def _draw_motor(self, surf):
        my = self.y_bot + 36
        mx = self.cx
        # Body
        pygame.draw.circle(surf, (32, 42, 56), (mx, my), 22)
        pygame.draw.circle(surf, (52, 66, 84), (mx, my), 22, 2)
        # Rotating arm (visual RPM)
        vis_rpm = min(self.rpm, 180)   # cap visual for clarity
        vis_phase = self.phase * (vis_rpm / max(1, self.rpm))
        dx = int(16 * math.cos(vis_phase))
        dy = int(16 * math.sin(vis_phase))
        pygame.draw.line(surf, (90, 170, 255), (mx, my), (mx+dx, my+dy), 3)
        pygame.draw.circle(surf, (70, 140, 220), (mx, my), 4)
        # Labels
        lbl  = FONT_N.render(self.label, True, (100, 130, 170))
        rpm_ = FONT_XS.render(f"{self.rpm:.0f} RPM", True, (65, 85, 110))
        hp_  = FONT_XS.render("0.25 HP", True, (50, 65, 85))
        surf.blit(lbl,  (mx - lbl.get_width()//2,  my + 26))
        surf.blit(rpm_, (mx - rpm_.get_width()//2, my + 39))
        surf.blit(hp_,  (mx - hp_.get_width()//2,  my + 52))

# ══════════════════════════════════════════════════════════════════════════
# HAMMER  (solenoid actuator)
# ══════════════════════════════════════════════════════════════════════════
class Hammer:
    __slots__ = ['lane','x','glow','plunge','strikes']
    def __init__(self, lane):
        self.lane    = lane
        self.x       = lane_cx(lane)
        self.glow    = 0.0
        self.plunge  = 0.0
        self.strikes = 0
    def strike(self):
        self.glow = 1.0;  self.plunge = 1.0;  self.strikes += 1
    def update(self, dt):
        self.glow   = max(0.0, self.glow   - dt * 2.2)
        self.plunge = max(0.0, self.plunge - dt * 9.0)
    def draw(self, surf):
        cx,cy = self.x, HAMMER_Y
        col   = COLORS[self.lane]
        bw,bh = LANE_W - 8, 16
        if self.glow > 0.02:
            gc  = tuple(min(255, int(c * self.glow + 15)) for c in col)
            pad = int(10 * self.glow)
            pygame.draw.rect(surf, gc,
                             (cx-bw//2-pad, cy-bh//2-pad,
                              bw+2*pad, bh+2*pad), border_radius=6)
        pygame.draw.rect(surf,(42,48,58),(cx-bw//2,cy-bh//2,bw,bh),border_radius=3)
        pygame.draw.rect(surf,(62,68,80),(cx-bw//2,cy-bh//2,bw,bh),1,border_radius=3)
        pe = int(self.plunge * 14)
        pt = cy - bh//2 - 9
        pc = col if self.glow > 0.08 else (88,98,112)
        pygame.draw.rect(surf, pc, (cx-3, pt+pe, 6, 11), border_radius=2)
        tc = (tuple(min(255,c+80) for c in col) if self.glow > 0.05 else (115,128,144))
        pygame.draw.circle(surf, tc, (cx, pt+pe+11), 4)
        if self.strikes:
            cs = FONT_XS.render(str(self.strikes), True, (45,55,70))
            surf.blit(cs, (cx - cs.get_width()//2, cy + bh//2 + 2))

# ══════════════════════════════════════════════════════════════════════════
# WAVEFORM
# ══════════════════════════════════════════════════════════════════════════
WAVE_W   = LANE_AREA_W
WAVE_Y   = SH - FOOTER_H + 6
WAVE_H   = 28
wave_buf = np.zeros(WAVE_W, dtype=np.float32)

def wave_strike(lane):
    cycles = FREQS[lane] / 55.0
    ph     = np.linspace(0.0, 2*math.pi*cycles, WAVE_W, dtype=np.float32)
    burst  = np.sin(ph) * 0.88
    env    = np.exp(-np.linspace(0.0, 3.0, WAVE_W, dtype=np.float32))
    wave_buf[:] = np.where(np.abs(burst*env) > np.abs(wave_buf),
                           burst, wave_buf*0.5)

def draw_wave(surf, lane_glow):
    global wave_buf
    wave_buf *= 0.978
    pts = [(LANE_AREA_X + i,
            int(WAVE_Y + WAVE_H//2 + wave_buf[i] * (WAVE_H//2 - 2)))
           for i in range(WAVE_W)]
    if len(pts) > 1:
        pygame.draw.lines(surf, (45,180,148), False, pts, 1)
    for i, g in enumerate(lane_glow):
        if g > 0.08:
            cx  = lane_cx(i)
            col = tuple(int(c * min(1.0, g * 0.8)) for c in COLORS[i])
            pygame.draw.line(surf, col, (cx, WAVE_Y), (cx, WAVE_Y+WAVE_H), 2)

# ══════════════════════════════════════════════════════════════════════════
# CONTROL PANEL RECTS
# ══════════════════════════════════════════════════════════════════════════
GATE_BTN     = pygame.Rect(SW//2 - 125, SH - FOOTER_H + 46, 250, 30)
MINUS_BTN    = pygame.Rect(SW//2 + 148, SH - FOOTER_H + 46,  30, 30)
PLUS_BTN     = pygame.Rect(SW//2 + 186, SH - FOOTER_H + 46,  30, 30)

def draw_controls(surf, bypass, ovfl_rate, notes, ovfl_rpm, lift_rpm, total_balls):
    # Gate button
    gc  = (115, 32, 32) if bypass else (32, 95, 52)
    pygame.draw.rect(surf, gc, GATE_BTN, border_radius=6)
    pygame.draw.rect(surf, (70, 85, 110), GATE_BTN, 1, border_radius=6)
    gt  = ("G ⬛ BYPASS → OVERFLOW" if bypass else "G ▶ PLAY INSTRUMENT")
    gtx = FONT_S.render(gt, True, (230, 230, 230))
    surf.blit(gtx, (GATE_BTN.centerx - gtx.get_width()//2, GATE_BTN.y + 7))

    # Overflow rate
    rl  = FONT_XS.render("OVERFLOW:", True, (55, 70, 95))
    rv  = FONT_N.render(f"{ovfl_rate:.1f}×  {ovfl_rpm:.0f} RPM", True, (130, 170, 215))
    surf.blit(rl, (MINUS_BTN.x - 95, GATE_BTN.y + 3))
    surf.blit(rv, (MINUS_BTN.x - 95, GATE_BTN.y + 16))
    pygame.draw.rect(surf, (38, 48, 62), MINUS_BTN, border_radius=4)
    pygame.draw.rect(surf, (38, 48, 62), PLUS_BTN,  border_radius=4)
    surf.blit(FONT_T.render("−", True, (170,195,225)),
              (MINUS_BTN.x + 7, MINUS_BTN.y + 5))
    surf.blit(FONT_T.render("+", True, (170,195,225)),
              (PLUS_BTN.x  + 7, PLUS_BTN.y  + 5))

    # Stats row
    stats = [
        ("LIFT RPM",    f"{lift_rpm:.0f}"),
        ("OVFL RPM",    f"{ovfl_rpm:.0f}"),
        ("MOTOR",       "0.25 HP"),
        ("MAX LIFT",    "190 b/s"),
        ("SURPLUS",     "+10%"),
        ("LANES",       "16"),
        ("NOTES",       str(notes)),
        ("BALLS",       str(total_balls)),
        ("HEIGHT",      "5 ft"),
        ("BPM",         "120"),
        ("VOICE",       "2"),
    ]
    sx = LANE_AREA_X
    sy = SH - 30
    for lbl_s, val_s in stats:
        ls = FONT_XS.render(lbl_s, True, (38, 50, 66))
        vs = FONT_N.render(val_s,  True, (105, 135, 175))
        surf.blit(ls, (sx, sy - 14))
        surf.blit(vs, (sx, sy))
        sx += max(ls.get_width(), vs.get_width()) + 16

# ══════════════════════════════════════════════════════════════════════════
# RETURN TRAY  (horizontal conveyor at bottom)
# ══════════════════════════════════════════════════════════════════════════
class ReturnTray:
    """Catches struck balls, queues them for routing to lift or overflow."""
    TRAY_Y  = HAMMER_Y + 28
    DELAY   = 28   # frames until ball reaches tray end

    def __init__(self):
        self._queue: deque = deque()

    def receive(self, lane):
        self._queue.append([lane, self.DELAY])

    def update(self) -> List[int]:
        """Returns list of lane indices ready to route."""
        nq, ready = deque(), []
        for entry in self._queue:
            entry[1] -= 1
            if entry[1] <= 0:
                ready.append(entry[0])
            else:
                nq.append(entry)
        self._queue = nq
        return ready

    def draw(self, surf, bypass):
        ty = self.TRAY_Y
        # Tray body
        pygame.draw.rect(surf, (20, 28, 40),
                         (LANE_AREA_X-8, ty, LANE_AREA_W+16, 10), border_radius=3)
        pygame.draw.rect(surf, (35, 45, 58),
                         (LANE_AREA_X-8, ty, LANE_AREA_W+16, 10), 1, border_radius=3)
        # Flow arrows
        arrow_col = (90, 25, 25) if bypass else (35, 90, 55)
        lbl = ("→  BYPASS  → OVERFLOW" if bypass else "←  RETURN  → LIFT")
        lt  = FONT_XS.render(lbl, True, arrow_col)
        surf.blit(lt, (LANE_AREA_X + LANE_AREA_W//2 - lt.get_width()//2, ty + 12))
        # Connection lines
        # Left: tray → lift ramp
        pygame.draw.line(surf, (30, 48, 70),
                         (LANE_AREA_X, ty + 5), (LIFT_CX + HELIX_AMP, ty + 5), 2)
        # Right: tray → overflow ramp (red when bypass active)
        rc = (100, 35, 35) if bypass else (25, 35, 50)
        pygame.draw.line(surf, rc,
                         (LANE_AREA_X + LANE_AREA_W, ty + 5),
                         (OVFL_CX - HELIX_AMP, ty + 5), 2)

# ══════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════
def run():
    field_balls: List[FieldBall] = []
    hammers      = [Hammer(i) for i in range(NUM_LANES)]
    lane_glow    = [0.0] * NUM_LANES
    last_drop    = [-99999.0] * NUM_LANES

    lift_ramp = HelixRamp(LIFT_CX, RAMP_Y_TOP, RAMP_Y_BOT,
                          going_up=True,  label="LIFT",     rpm=BASE_LIFT_RPM)
    ovfl_ramp = HelixRamp(OVFL_CX, RAMP_Y_TOP, RAMP_Y_BOT,
                          going_up=False, label="OVERFLOW", rpm=BASE_OVFL_RPM)

    tray         = ReturnTray()
    gate_bypass  = False
    ovfl_rate    = 1.0

    song_ms   = float(-FALL_TIME_MS)
    song_idx  = 0
    paused    = False
    notes     = 0
    total_balls_in_system = 96

    KEY_MAP = {
        pygame.K_1:0, pygame.K_2:1, pygame.K_3:2, pygame.K_4:3,
        pygame.K_5:4, pygame.K_6:5, pygame.K_7:6, pygame.K_8:7,
        pygame.K_9:8, pygame.K_0:9,
        pygame.K_q:10, pygame.K_w:11, pygame.K_e:12,
        pygame.K_t:13, pygame.K_y:14, pygame.K_u:15,
    }

    def drop_ball(lane):
        if song_ms - last_drop[lane] >= MIN_GAP_MS:
            field_balls.append(FieldBall(lane))
            last_drop[lane] = song_ms

    def restart():
        nonlocal song_ms, song_idx, notes
        field_balls.clear()
        wave_buf[:] = 0.0
        song_ms   = float(-FALL_TIME_MS)
        song_idx  = 0
        notes     = 0
        for h in hammers: h.strikes = 0

    running = True
    while running:
        dt    = clock.tick(FPS) / 1000.0
        dt_ms = dt * 1000.0

        # ── Events ─────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                k = ev.key
                if   k == pygame.K_ESCAPE: running = False
                elif k == pygame.K_SPACE:  paused = not paused
                elif k == pygame.K_r:      restart()
                elif k == pygame.K_g:      gate_bypass = not gate_bypass
                elif k in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                    ovfl_rate = max(0.1, round(ovfl_rate - 0.1, 1))
                elif k in (pygame.K_EQUALS, pygame.K_PLUS):
                    ovfl_rate = min(8.0, round(ovfl_rate + 0.1, 1))
                elif k in KEY_MAP:
                    drop_ball(KEY_MAP[k])
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx,my = ev.pos
                if GATE_BTN.collidepoint(mx, my):
                    gate_bypass = not gate_bypass
                elif MINUS_BTN.collidepoint(mx, my):
                    ovfl_rate = max(0.1, round(ovfl_rate - 0.1, 1))
                elif PLUS_BTN.collidepoint(mx, my):
                    ovfl_rate = min(8.0, round(ovfl_rate + 0.1, 1))
                elif LANE_AREA_Y <= my <= LANE_AREA_Y + LANE_AREA_H:
                    lane = (mx - LANE_AREA_X) // LANE_W
                    if 0 <= lane < NUM_LANES:
                        drop_ball(lane)

        if paused:
            pass
        else:
            song_ms += dt_ms

            # ── Song scheduler ────────────────────────────────────────
            while song_idx < len(SONG):
                lane, st = SONG[song_idx]
                if song_ms >= st - FALL_TIME_MS:
                    drop_ball(lane)
                    song_idx += 1
                else:
                    break

            # ── Ball physics + hammer ─────────────────────────────────
            survivors = []
            for b in field_balls:
                b.update(dt)
                if b.y >= BALL_HIT_Y:
                    if not gate_bypass:
                        SOUNDS[b.lane].play()
                        hammers[b.lane].strike()
                        lane_glow[b.lane] = 1.0
                        wave_strike(b.lane)
                        notes += 1
                    tray.receive(b.lane)
                else:
                    survivors.append(b)
            field_balls[:] = survivors

            # ── Tray routing ──────────────────────────────────────────
            ready = tray.update()
            for lane in ready:
                if gate_bypass:
                    ovfl_ramp.add_ball(lane)
                else:
                    lift_ramp.add_ball(lane)

            # ── Ramp updates ──────────────────────────────────────────
            lift_ramp.rpm       = BASE_LIFT_RPM
            ovfl_ramp.rpm       = BASE_OVFL_RPM * ovfl_rate
            ovfl_ramp.rate_mult = ovfl_rate

            delivered_lift = lift_ramp.update(dt)
            delivered_ovfl = ovfl_ramp.update(dt)
            # Balls delivered by lift ramp re-enter field (dropped into lane tops)
            for lane in delivered_lift:
                drop_ball(lane)

            # ── Hammers + glow decay ──────────────────────────────────
            for h in hammers: h.update(dt)
            for i in range(NUM_LANES):
                lane_glow[i] = max(0.0, lane_glow[i] - dt * 1.8)

            # ── Loop song ─────────────────────────────────────────────
            if song_idx >= len(SONG) and not field_balls:
                restart()

        # ═══ DRAW ═══════════════════════════════════════════════════════

        screen.fill((5, 7, 11))

        # ── Header ────────────────────────────────────────────────────
        ht = FONT_T.render(
            "  HONEYLIGHT MARBLE QUIPU  ·  Rubin Lifting Ramp  ·  "
            "5 ft  ·  16 lanes  ·  0.25 HP motor  ·  Golf balls",
            True, (145, 162, 195))
        screen.blit(ht, (4, 7))

        pct   = min(1.0, max(0.0, song_ms) / SONG_TOTAL_MS)
        status = ("⏸ PAUSED — SPACE to resume" if paused else
                  f"♩ Ode to Joy · {int(pct*100)}%  |  "
                  f"SPACE=pause  R=restart  G=gate  −/+=overflow  CLICK=drop  ESC=quit")
        st_ = FONT_XS.render(status, True, (60, 75, 100))
        screen.blit(st_, (4, 28))

        # Progress bar
        pygame.draw.rect(screen,(16,22,32),(LANE_AREA_X,50,LANE_AREA_W,4),border_radius=2)
        pygame.draw.rect(screen,(50,125,195),(LANE_AREA_X,50,int(LANE_AREA_W*pct),4),border_radius=2)

        # ── Lift ramp (LEFT) ──────────────────────────────────────────
        lift_ramp.draw(screen)

        # ── Overflow ramp (RIGHT) ─────────────────────────────────────
        ovfl_ramp.draw(screen)

        # ── Lane area border ──────────────────────────────────────────
        pygame.draw.rect(screen, (28,36,48),
                         (LANE_AREA_X, LANE_AREA_Y, LANE_AREA_W, LANE_AREA_H),
                         2, border_radius=2)

        # ── Height ruler ─────────────────────────────────────────────
        for ft in range(6):
            ry = LANE_AREA_Y + int(ft * PX_PER_FOOT)
            if ry <= LANE_AREA_Y + LANE_AREA_H:
                pygame.draw.line(screen,(26,34,46),
                                 (LANE_AREA_X-8,ry),(LANE_AREA_X-2,ry))
                rl = FONT_XS.render(f"{ft}'", True, (36,48,62))
                screen.blit(rl,(LANE_AREA_X-22, ry-5))

        # ── LED Quipu bar ─────────────────────────────────────────────
        for i in range(NUM_LANES):
            cx  = lane_cx(i)
            cy  = LANE_AREA_Y - 24
            dim = tuple(max(10, int(c*0.08)) for c in COLORS[i])
            pygame.draw.circle(screen, dim, (cx,cy), 8)
            if lane_glow[i] > 0.02:
                gc = tuple(min(255, int(c*lane_glow[i])) for c in COLORS[i])
                pygame.draw.circle(screen, gc, (cx,cy), 8)
                if lane_glow[i] > 0.3:
                    pygame.draw.circle(screen,
                                       tuple(c//4 for c in gc), (cx,cy), 13, 2)
            pygame.draw.circle(screen, (16,20,28), (cx,cy), 8, 1)
            nl = FONT_XS.render(NAMES[i], True, (50,62,82))
            screen.blit(nl, (cx - nl.get_width()//2, cy-5))

        # ── Lane dividers + glow fills ────────────────────────────────
        for i in range(NUM_LANES):
            lx = LANE_AREA_X + i * LANE_W
            if i > 0:
                pygame.draw.line(screen,(16,21,30),(lx,LANE_AREA_Y),(lx,HAMMER_Y-18))
            if lane_glow[i] > 0.04:
                r,g,b = COLORS[i]
                s = pygame.Surface((LANE_W-1, LANE_AREA_H-20), pygame.SRCALPHA)
                s.fill((r,g,b,int(lane_glow[i]*13)))
                screen.blit(s,(lx+1,LANE_AREA_Y))

        # ── Field balls ───────────────────────────────────────────────
        for b in field_balls:
            b.draw(screen)

        # ── Hammers ───────────────────────────────────────────────────
        for h in hammers:
            h.draw(screen)

        # ── Return tray ───────────────────────────────────────────────
        tray.draw(screen, gate_bypass)

        # ── Dimension labels ──────────────────────────────────────────
        d8 = FONT_XS.render("← 8 ft →", True, (32,42,56))
        screen.blit(d8,(LANE_AREA_X+LANE_AREA_W//2-d8.get_width()//2,
                        LANE_AREA_Y+LANE_AREA_H+3))
        d5 = FONT_XS.render("5ft", True, (32,42,56))
        screen.blit(d5,(LANE_AREA_X-22, LANE_AREA_Y+LANE_AREA_H//2-5))

        # ── Footer waveform + controls ────────────────────────────────
        draw_wave(screen, lane_glow)
        draw_controls(screen, gate_bypass, ovfl_rate, notes,
                      ovfl_ramp.rpm, lift_ramp.rpm, total_balls_in_system)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    run()
