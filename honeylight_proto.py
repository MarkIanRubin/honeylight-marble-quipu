#!/Users/queenbee/chromatic-roll/venv/bin/python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   HONEYLIGHT MARBLE QUIPU — Physical Prototype Simulator            ║
║   4 ft tall  ×  8 ft wide  ·  16 lanes  ·  1 hammer per lane       ║
║   Golf ball drop physics  ·  Tongue drum synthesis                  ║
║   Auto-plays: Ode to Joy (melody + bass, 2 simultaneous voices)     ║
╠══════════════════════════════════════════════════════════════════════╣
║  CONTROLS                                                           ║
║   SPACE        Pause / Resume                                       ║
║   R            Restart song                                         ║
║   CLICK lane   Drop ball manually                                   ║
║   1-9,0        Drop in lanes  1–10                                  ║
║   Q W E T Y U  Drop in lanes 11–16  (skips R = restart)            ║
║   ESC          Quit                                                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import pygame
import numpy as np
import math
import sys
from typing import List, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# INIT
# ═══════════════════════════════════════════════════════════════════════════
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

SW, SH = 1400, 800
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Honeylight Marble Quipu  —  4 ft × 8 ft Prototype")
clock = pygame.time.Clock()
FPS   = 60

FONT_T  = pygame.font.SysFont('monospace', 17, bold=True)
FONT_S  = pygame.font.SysFont('monospace', 11)
FONT_XS = pygame.font.SysFont('monospace', 10)
FONT_N  = pygame.font.SysFont('monospace', 10, bold=True)

# ═══════════════════════════════════════════════════════════════════════════
# LAYOUT  —  maps to physical 4 ft × 8 ft frame
# ═══════════════════════════════════════════════════════════════════════════
NUM_LANES    = 16
MARGIN       = 40
HEADER_H     = 75
FOOTER_H     = 110

LANE_AREA_X  = MARGIN
LANE_AREA_Y  = HEADER_H
LANE_AREA_W  = SW - 2 * MARGIN           # 1320 px  =  8 ft
LANE_AREA_H  = SH - HEADER_H - FOOTER_H  #  615 px  =  4 ft
LANE_W       = LANE_AREA_W // NUM_LANES  #   82 px per lane (~6 in)
BALL_R       = max(10, LANE_W // 3 - 2) #   25 px  (golf ball)

HAMMER_Y     = LANE_AREA_Y + LANE_AREA_H - 16   # solenoid strike line

# ═══════════════════════════════════════════════════════════════════════════
# PHYSICS  —  free-fall drop, golf ball in vertical tube
#  Real: 4 ft drop ≈ 500 ms  (free fall sqrt(2h/g))
#  We use 620 ms for visual clarity — balls are clearly readable
# ═══════════════════════════════════════════════════════════════════════════
BALL_START_Y  = LANE_AREA_Y + BALL_R + 4    # top of drop zone
BALL_HIT_Y    = HAMMER_Y    - BALL_R        # where ball triggers hammer
FALL_DIST_PX  = BALL_HIT_Y  - BALL_START_Y  # 545 px

FALL_TIME_S   = 0.62                         # seconds for 4 ft drop
G_PX          = 2.0 * FALL_DIST_PX / (FALL_TIME_S ** 2)   # 2836 px/s²
FALL_TIME_MS  = int(FALL_TIME_S * 1000)      # 620 ms

PX_PER_FOOT   = LANE_AREA_H / 4.0           # for ruler

MIN_GAP_MS    = 300   # minimum ms between consecutive drops in same lane

def lane_cx(lane: int) -> int:
    """Pixel x-centre of a lane."""
    return LANE_AREA_X + lane * LANE_W + LANE_W // 2

# ═══════════════════════════════════════════════════════════════════════════
# NOTES  —  D natural minor, 2 octaves (D3 – E5), 16 lanes
#            Twilight Goat Pasture colour palette
# ═══════════════════════════════════════════════════════════════════════════
NOTE_DATA: List[Tuple[str, float, Tuple[int,int,int]]] = [
    # (name,    freq Hz,   RGB colour)
    ('D3',  146.83, (195,  45,  45)),   #  0  Deep Ember
    ('E3',  164.81, (210,  90,  20)),   #  1  Burnt Honey
    ('F3',  174.61, (220, 140,  20)),   #  2  Amber
    ('G3',  196.00, (130, 175,  60)),   #  3  Sage
    ('A3',  220.00, ( 55, 160,  80)),   #  4  Pasture
    ('Bb3', 233.08, ( 35, 165, 155)),   #  5  Teal
    ('C4',  261.63, ( 35, 130, 210)),   #  6  Sky
    ('D4',  293.66, ( 40, 105, 210)),   #  7  Twilight Blue
    ('E4',  329.63, ( 80,  70, 205)),   #  8  Deep Indigo
    ('F4',  349.23, (120,  55, 195)),   #  9  Violet
    ('G4',  392.00, (150,  55, 180)),   # 10  Purple
    ('A4',  440.00, (170,  55, 150)),   # 11  Mauve
    ('Bb4', 466.16, (160, 175, 190)),   # 12  Gunmetal Silver
    ('C5',  523.25, (195, 200, 215)),   # 13  Light Silver
    ('D5',  587.33, (215,  90, 130)),   # 14  Rose Dawn
    ('E5',  659.25, (240, 135, 135)),   # 15  Bright Rose
]
NAMES:  List[str]              = [n[0] for n in NOTE_DATA]
FREQS:  List[float]            = [n[1] for n in NOTE_DATA]
COLORS: List[Tuple[int,int,int]] = [n[2] for n in NOTE_DATA]

# ═══════════════════════════════════════════════════════════════════════════
# SOUND SYNTHESIS  —  steel tongue drum timbre
# ═══════════════════════════════════════════════════════════════════════════
SR = 44100   # sample rate

def synth_tongue_drum(freq: float,
                      dur:  float = 3.5,
                      vol:  float = 0.70) -> pygame.mixer.Sound:
    """
    Synthesise one tongue-drum note.
    Characteristics:
      • Sharp transient attack (4 ms)
      • Fast decay to 28 % amplitude (180 ms)
      • Long exponential tail (natural sustain)
      • Inharmonic partials  (tongue drum is NOT a tuning fork)
      • Small body-resonance click on attack
    """
    n   = int(SR * dur)
    t   = np.linspace(0, dur, n, endpoint=False)

    # Amplitude envelope
    atk       = int(0.004 * SR)
    dcy       = int(0.180 * SR)
    env       = np.empty(n, dtype=np.float32)
    env[:atk] = np.linspace(0.0, 1.0, atk, dtype=np.float32)
    end_dcy   = atk + dcy
    env[atk:end_dcy] = np.linspace(1.0, 0.28, dcy, dtype=np.float32)
    tail_len  = n - end_dcy
    env[end_dcy:] = (0.28 * np.exp(
        np.linspace(0.0, -5.0, tail_len), dtype=np.float32
    )).astype(np.float32)

    # Partials  (tongue drum inharmonicity: ×2.76, ×5.40)
    wave  = np.sin(2 * np.pi * freq          * t, dtype=np.float32) * env
    f2    = freq * 2.76
    f3    = freq * 5.40
    nyq   = SR * 0.45
    if f2 < nyq:
        wave += (0.18 * np.sin(2 * np.pi * f2 * t, dtype=np.float32)
                      * env * np.exp(-t * 4.0).astype(np.float32))
    if f3 < nyq:
        wave += (0.06 * np.sin(2 * np.pi * f3 * t, dtype=np.float32)
                      * env * np.exp(-t * 9.0).astype(np.float32))

    # Attack click — randomised with deterministic seed (reproducible)
    rng   = np.random.default_rng(int(freq * 100) & 0xFFFF)
    noise = rng.uniform(-1.0, 1.0, n).astype(np.float32)
    wave += noise * np.exp(-t * 130.0).astype(np.float32) * 0.07

    # Normalise → volume
    peak = np.max(np.abs(wave))
    if peak > 1e-9:
        wave = (wave / peak) * vol

    # Stereo int16
    buf = np.ascontiguousarray(
        np.column_stack([wave, wave]) * 32767
    ).astype(np.int16)
    return pygame.sndarray.make_sound(buf)


print("🎵  Building tongue-drum sound cache  (16 notes) ...")
SOUNDS: List[pygame.mixer.Sound] = []
for _i, (_name, _freq, _) in enumerate(NOTE_DATA):
    SOUNDS.append(synth_tongue_drum(_freq))
    bar = '█' * (_i + 1) + '░' * (15 - _i)
    print(f"   [{bar}]  {_name:5s}  {_freq:7.2f} Hz", end='\r')
print("\n✅  Sound cache ready.\n")

# ═══════════════════════════════════════════════════════════════════════════
# SONG  —  Ode to Joy, D natural minor, 2 voices, 120 BPM
#
#  Voice 1 (melody): lanes 6–10  (C4 D4 E4 F4 G4)
#  Voice 2 (bass):   lanes 0,3,4 (D3 G3 A3)
#
#  Format: (lane_index, sound_time_ms)
#  Ball is released at (sound_time_ms − FALL_TIME_MS) so it arrives
#  at the hammer exactly on the beat.
# ═══════════════════════════════════════════════════════════════════════════
QN = 500   # quarter note  =  500 ms  (120 BPM)
HN = 1000  # half note

def build_song() -> List[Tuple[int, int]]:
    C4, D4, E4, F4, G4 = 6, 7, 8, 9, 10
    D3, G3, A3          = 0, 3, 4

    melody = [
        # ── Phrase 1 ──────────────────────────────────────────────────
        (E4,  0*QN), (E4,  1*QN), (F4,  2*QN), (G4,  3*QN),   # E E F G
        (G4,  4*QN), (F4,  5*QN), (E4,  6*QN), (D4,  7*QN),   # G F E D
        (C4,  8*QN), (C4,  9*QN), (D4, 10*QN), (E4, 11*QN),   # C C D E
        (E4, 12*QN), (D4, 13*QN + QN//2), (D4, 15*QN),        # E. D D
        # ── Phrase 2 ──────────────────────────────────────────────────
        (E4, 16*QN), (E4, 17*QN), (F4, 18*QN), (G4, 19*QN),   # E E F G
        (G4, 20*QN), (F4, 21*QN), (E4, 22*QN), (D4, 23*QN),   # G F E D
        (C4, 24*QN), (C4, 25*QN), (D4, 26*QN), (E4, 27*QN),   # C C D E
        (D4, 28*QN), (C4, 29*QN + QN//2), (C4, 31*QN),        # D. C C
    ]

    bass = [
        # Half-note root motion  (two notes per measure)
        (D3,  0*HN), (A3,  1*HN),
        (G3,  2*HN), (A3,  3*HN),
        (D3,  4*HN), (G3,  5*HN),
        (A3,  6*HN), (D3,  7*HN),
        # Phrase 2 bass
        (D3,  8*HN), (A3,  9*HN),
        (G3, 10*HN), (A3, 11*HN),
        (D3, 12*HN), (G3, 13*HN),
        (D3, 14*HN), (D3, 15*HN),
    ]

    events = sorted(melody + bass, key=lambda e: e[1])
    return events


SONG          = build_song()
SONG_TOTAL_MS = max(t for _, t in SONG) + 2500   # include fade tail

# ═══════════════════════════════════════════════════════════════════════════
# BALL
# ═══════════════════════════════════════════════════════════════════════════
class Ball:
    __slots__ = ['lane', 'x', 'y', 'vy', 'color', 'bright']

    def __init__(self, lane: int) -> None:
        self.lane   = lane
        self.x      = float(lane_cx(lane))
        self.y      = float(BALL_START_Y)
        self.vy     = 0.0
        self.color  = COLORS[lane]
        self.bright = 1.0   # dims slightly on old balls (unused now — kept for future)

    def update(self, dt: float) -> None:
        self.vy += G_PX * dt
        self.y  += self.vy * dt

    def draw(self, surf: pygame.Surface) -> None:
        ix, iy = int(self.x), int(self.y)
        r, g, b = self.color
        # Shadow
        pygame.draw.circle(surf, (0, 0, 0), (ix + 2, iy + 2), BALL_R)
        # Body
        pygame.draw.circle(surf, (r, g, b), (ix, iy), BALL_R)
        # Equator line (shows rotation illusion)
        eq_y = iy
        pygame.draw.arc(surf, (max(0,r-60), max(0,g-60), max(0,b-60)),
                        (ix - BALL_R, eq_y - 3, BALL_R*2, 6),
                        0, math.pi, 2)
        # Shine highlight (top-left)
        hx = ix - BALL_R // 3
        hy = iy - BALL_R // 3
        pygame.draw.circle(surf, (255, 255, 255), (hx, hy), BALL_R // 4)
        # Edge
        pygame.draw.circle(surf, (12, 12, 15), (ix, iy), BALL_R, 1)

# ═══════════════════════════════════════════════════════════════════════════
# HAMMER  (solenoid + plunger visualisation)
# ═══════════════════════════════════════════════════════════════════════════
class Hammer:
    __slots__ = ['lane', 'x', 'glow', 'plunge', 'strikes']

    def __init__(self, lane: int) -> None:
        self.lane    = lane
        self.x       = lane_cx(lane)
        self.glow    = 0.0
        self.plunge  = 0.0
        self.strikes = 0

    def strike(self) -> None:
        self.glow   = 1.0
        self.plunge = 1.0
        self.strikes += 1

    def update(self, dt: float) -> None:
        self.glow   = max(0.0, self.glow   - dt * 2.0)
        self.plunge = max(0.0, self.plunge - dt * 9.0)

    def draw(self, surf: pygame.Surface) -> None:
        cx        = self.x
        cy        = HAMMER_Y
        col       = COLORS[self.lane]
        bw        = LANE_W - 8    # body width
        bh        = 18            # body height

        # Glow halo
        if self.glow > 0.02:
            gc  = tuple(min(255, int(c * self.glow + 15)) for c in col)
            pad = int(12 * self.glow)
            gr  = pygame.Rect(cx - bw//2 - pad, cy - bh//2 - pad,
                              bw + 2*pad, bh + 2*pad)
            pygame.draw.rect(surf, gc, gr, border_radius=8)

        # Solenoid body
        br = pygame.Rect(cx - bw//2, cy - bh//2, bw, bh)
        pygame.draw.rect(surf, (42, 48, 58), br, border_radius=3)
        pygame.draw.rect(surf, (62, 68, 80), br, 1, border_radius=3)

        # Winding detail lines
        for yy in range(-6, 7, 3):
            pygame.draw.line(surf, (30, 35, 43),
                             (cx - bw//2 + 3, cy + yy),
                             (cx + bw//2 - 3, cy + yy))

        # Plunger rod
        p_ext   = int(self.plunge * 18)           # extends downward on strike
        p_top_y = cy - bh//2 - 12                 # resting tip
        p_rect  = pygame.Rect(cx - 3, p_top_y + p_ext, 6, 14)
        p_col   = col if self.glow > 0.08 else (88, 98, 112)
        pygame.draw.rect(surf, p_col, p_rect, border_radius=2)

        # Rubber mallet tip
        tip_y = p_top_y + p_ext + 14
        tip_c = (tuple(min(255, c + 90) for c in col)
                 if self.glow > 0.05 else (120, 132, 148))
        pygame.draw.circle(surf, tip_c, (cx, tip_y), 5)
        pygame.draw.circle(surf, (20, 22, 28), (cx, tip_y), 5, 1)

        # Strike count (tiny)
        if self.strikes > 0:
            cnt = FONT_XS.render(str(self.strikes), True, (50, 60, 75))
            surf.blit(cnt, (cx - cnt.get_width()//2, cy + bh//2 + 2))

# ═══════════════════════════════════════════════════════════════════════════
# WAVEFORM  —  oscilloscope strip in footer
# ═══════════════════════════════════════════════════════════════════════════
WAVE_W   = LANE_AREA_W
WAVE_Y   = SH - FOOTER_H + 6
WAVE_H   = 34
wave_buf = np.zeros(WAVE_W, dtype=np.float32)

def wave_strike(lane: int) -> None:
    """Add a decaying sine burst for the struck note."""
    freq   = FREQS[lane]
    cycles = freq / 55.0          # visual frequency (not acoustic — scaled)
    phase  = np.linspace(0.0, 2.0 * math.pi * cycles, WAVE_W, dtype=np.float32)
    burst  = np.sin(phase) * 0.90
    # Take the envelope-weighted max so old notes fade under new strikes
    env    = np.exp(-np.linspace(0.0, 3.0, WAVE_W, dtype=np.float32))
    wave_buf[:] = np.where(np.abs(burst * env) > np.abs(wave_buf),
                           burst, wave_buf * 0.5)

def draw_wave(surf: pygame.Surface, lane_glow: List[float]) -> None:
    global wave_buf
    wave_buf *= 0.975   # exponential decay each frame

    pts = [(MARGIN + i,
            int(WAVE_Y + WAVE_H//2 + wave_buf[i] * (WAVE_H//2 - 2)))
           for i in range(WAVE_W)]
    if len(pts) > 1:
        pygame.draw.lines(surf, (50, 185, 155), False, pts, 1)

    # Per-lane vertical marker ticks
    for i, g in enumerate(lane_glow):
        if g > 0.08:
            cx  = lane_cx(i)
            col = tuple(int(c * min(1.0, g)) for c in COLORS[i])
            pygame.draw.line(surf, col, (cx, WAVE_Y), (cx, WAVE_Y + WAVE_H), 2)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════
def run() -> None:
    balls:      List[Ball]   = []
    hammers:    List[Hammer] = [Hammer(i) for i in range(NUM_LANES)]
    lane_glow:  List[float]  = [0.0] * NUM_LANES
    last_drop:  List[float]  = [-99999.0] * NUM_LANES   # ms of last drop per lane

    # Song sequencer state
    song_ms   = float(-FALL_TIME_MS)   # start early so first ball is released
    song_idx  = 0
    paused    = False
    notes_ttl = 0    # total notes played this session

    # Keyboard → lane mapping (R is reserved for restart)
    KEY_MAP = {
        pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
        pygame.K_5: 4, pygame.K_6: 5, pygame.K_7: 6, pygame.K_8: 7,
        pygame.K_9: 8, pygame.K_0: 9,
        pygame.K_q:10, pygame.K_w:11, pygame.K_e:12,
        # K_r = restart (not a lane)
        pygame.K_t:13, pygame.K_y:14, pygame.K_u:15,
    }

    def drop_ball(lane: int) -> None:
        """Release a ball if minimum lane spacing allows."""
        if song_ms - last_drop[lane] >= MIN_GAP_MS:
            balls.append(Ball(lane))
            last_drop[lane] = song_ms

    def restart() -> None:
        nonlocal song_ms, song_idx, notes_ttl
        balls.clear()
        song_ms   = float(-FALL_TIME_MS)
        song_idx  = 0
        wave_buf[:] = 0.0
        notes_ttl = 0
        for h in hammers:
            h.strikes = 0

    running = True
    while running:
        dt    = clock.tick(FPS) / 1000.0
        dt_ms = dt * 1000.0

        # ── Events ───────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_SPACE:
                    paused = not paused
                elif ev.key == pygame.K_r:
                    restart()
                elif ev.key in KEY_MAP:
                    drop_ball(KEY_MAP[ev.key])
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if LANE_AREA_Y <= my <= LANE_AREA_Y + LANE_AREA_H:
                    lane = (mx - LANE_AREA_X) // LANE_W
                    if 0 <= lane < NUM_LANES:
                        drop_ball(lane)

        if paused:
            # Still need to render — just skip physics
            pass
        else:
            song_ms += dt_ms

            # ── Schedule song balls ───────────────────────────────────
            while song_idx < len(SONG):
                lane, sound_t = SONG[song_idx]
                if song_ms >= sound_t - FALL_TIME_MS:
                    drop_ball(lane)
                    song_idx += 1
                else:
                    break

            # ── Physics update + collision ────────────────────────────
            survivors: List[Ball] = []
            for b in balls:
                b.update(dt)
                if b.y >= BALL_HIT_Y:
                    # STRIKE
                    SOUNDS[b.lane].play()
                    hammers[b.lane].strike()
                    lane_glow[b.lane] = 1.0
                    wave_strike(b.lane)
                    notes_ttl += 1
                else:
                    survivors.append(b)
            balls = survivors

            # ── Decay hammers + lane glow ─────────────────────────────
            for h in hammers:
                h.update(dt)
            for i in range(NUM_LANES):
                lane_glow[i] = max(0.0, lane_glow[i] - dt * 1.6)

            # ── Loop song ─────────────────────────────────────────────
            if song_idx >= len(SONG) and not balls:
                restart()

        # ═══ DRAW ════════════════════════════════════════════════════

        screen.fill((6, 8, 12))

        # ── Header ───────────────────────────────────────────────────
        t1 = FONT_T.render(
            "  HONEYLIGHT MARBLE QUIPU    ·    4 ft × 8 ft    ·    "
            "16 lanes    ·    16 hammers    ·    2 voices",
            True, (180, 192, 215))
        screen.blit(t1, (MARGIN, 8))

        pct    = min(1.0, max(0.0, song_ms) / SONG_TOTAL_MS)
        status = ("⏸  PAUSED  —  SPACE to resume"
                  if paused else
                  f"♩  Ode to Joy (D minor)  —  {int(pct*100):3d}%  "
                  f"—  {notes_ttl} notes  —  "
                  "SPACE=pause  R=restart  CLICK=drop")
        t2 = FONT_S.render(status, True, (80, 95, 120))
        screen.blit(t2, (MARGIN, 32))

        # Progress bar
        pb_rect = pygame.Rect(LANE_AREA_X, 52, LANE_AREA_W, 5)
        pygame.draw.rect(screen, (20, 26, 36), pb_rect, border_radius=2)
        pygame.draw.rect(screen, (55, 130, 200),
                         pygame.Rect(LANE_AREA_X, 52, int(LANE_AREA_W * pct), 5),
                         border_radius=2)

        # ── LED Quipu Bar  (one dot per lane, above frame) ───────────
        for i in range(NUM_LANES):
            cx  = lane_cx(i)
            cy  = LANE_AREA_Y - 20
            dim = tuple(max(10, int(c * 0.09)) for c in COLORS[i])
            pygame.draw.circle(screen, dim, (cx, cy), 8)
            if lane_glow[i] > 0.02:
                gc = tuple(min(255, int(c * lane_glow[i])) for c in COLORS[i])
                pygame.draw.circle(screen, gc, (cx, cy), 8)
                if lane_glow[i] > 0.35:
                    ring = tuple(c // 4 for c in gc)
                    pygame.draw.circle(screen, ring, (cx, cy), 13, 2)
            pygame.draw.circle(screen, (18, 22, 30), (cx, cy), 8, 1)
            lbl = FONT_XS.render(NAMES[i], True, (55, 68, 88))
            screen.blit(lbl, (cx - lbl.get_width()//2, cy - 5))

        # ── Frame border ──────────────────────────────────────────────
        pygame.draw.rect(screen, (30, 38, 50),
                         pygame.Rect(LANE_AREA_X, LANE_AREA_Y,
                                     LANE_AREA_W, LANE_AREA_H), 2, border_radius=3)

        # ── Height ruler (left edge) ──────────────────────────────────
        for ft in range(5):
            ry  = LANE_AREA_Y + int(ft * PX_PER_FOOT)
            col = (28, 36, 48) if ft > 0 else (45, 55, 70)
            pygame.draw.line(screen, col,
                             (LANE_AREA_X - 10, ry), (LANE_AREA_X - 2, ry))
            rl = FONT_XS.render(f"{ft}'", True, (40, 52, 68))
            screen.blit(rl, (LANE_AREA_X - 24, ry - 5))

        # ── Lane dividers + active background tint ────────────────────
        for i in range(NUM_LANES):
            lx = LANE_AREA_X + i * LANE_W
            # Divider
            if i > 0:
                pygame.draw.line(screen, (18, 23, 32),
                                 (lx, LANE_AREA_Y), (lx, HAMMER_Y - 20))
            # Lane background glow when recently struck
            if lane_glow[i] > 0.04:
                r, g, b = COLORS[i]
                s = pygame.Surface((LANE_W - 1, LANE_AREA_H - 22), pygame.SRCALPHA)
                s.fill((r, g, b, int(lane_glow[i] * 16)))
                screen.blit(s, (lx + 1, LANE_AREA_Y))

        # ── Golf balls ────────────────────────────────────────────────
        for b in balls:
            b.draw(screen)

        # ── Hammers ───────────────────────────────────────────────────
        for h in hammers:
            h.draw(screen)

        # ── Dimension labels ──────────────────────────────────────────
        lbl8 = FONT_XS.render("← 8 feet →", True, (38, 48, 62))
        screen.blit(lbl8, (LANE_AREA_X + LANE_AREA_W//2 - lbl8.get_width()//2,
                            LANE_AREA_Y + LANE_AREA_H + 4))
        lbl4 = FONT_XS.render("4ft", True, (38, 48, 62))
        screen.blit(lbl4, (LANE_AREA_X - 28,
                            LANE_AREA_Y + LANE_AREA_H//2 - 5))

        # ── Footer waveform ───────────────────────────────────────────
        draw_wave(screen, lane_glow)

        # ── Footer spec strip ─────────────────────────────────────────
        specs = [
            ("LANES",   "16"),
            ("FRAME",   "4ft × 8ft"),
            ("BALL",    "Golf ball"),
            ("DROP",    "4 ft"),
            ("FALL",    f"{FALL_TIME_MS}ms"),
            ("PITCH",   "D natural minor"),
            ("RANGE",   "D3 – E5"),
            ("VOICES",  "2  (mel+bass)"),
            ("BPM",     "120"),
            ("MAX SIM", "6 notes"),
            ("SOLENOIDS","16"),
            ("STATUS",  "READY" if not paused else "PAUSED"),
        ]
        sx = MARGIN
        sy = WAVE_Y + WAVE_H + 7
        for lbl_s, val_s in specs:
            ls = FONT_XS.render(lbl_s, True, (45, 58, 75))
            vs = FONT_N.render(val_s,  True, (125, 155, 192))
            screen.blit(ls, (sx, sy))
            screen.blit(vs, (sx, sy + 13))
            sx += max(ls.get_width(), vs.get_width()) + 18

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    run()
