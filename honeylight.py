#!/Users/queenbee/chromatic-roll/venv/bin/python3
"""
╔══════════════════════════════════════════════════════╗
║          HONEYLIGHT — The Solar Marble Quipu         ║
║   LED Colors → Marbles → Hammers → Steel Drum → 🎵  ║
║          Inspired by the Inca Quipu system           ║
╚══════════════════════════════════════════════════════╝
"""

import pygame
import numpy as np
import math, time, random, os, sys, wave, struct, threading, subprocess
from collections import deque

# ─── CONSTANTS ────────────────────────────────────────
W, H       = 1280, 820
FPS        = 60
SAMPLE_RATE= 44100

# ─── HONEYLIGHT NOTE→COLOR MAP (farm-themed palette) ──
NOTE_COLORS = {
    'C' : (210,  50,  50),   # Warm Red    "earth"
    'D' : (220, 130,  30),   # Amber       "honey"
    'E' : (210, 190,  30),   # Gold        "sun"
    'F' : ( 60, 170,  80),   # Leaf Green  "pasture"
    'G' : ( 50, 140, 220),   # Sky Blue    "open air"
    'A' : (140,  80, 200),   # Lavender    "dusk"
    'B' : (240, 240, 200),   # Warm White  "moonlight"
    'C2': (230,  80,  80),   # Bright Red  "dawn"
    'R' : ( 20,  20,  20),   # Rest / off
}

NOTES  = ['C','D','E','F','G','A','B','C2']
FREQS  = {
    'C' : 261.63, 'D': 293.66, 'E': 329.63,
    'F' : 349.23, 'G': 392.00, 'A': 440.00,
    'B' : 493.88, 'C2': 523.25, 'R': 0
}

# ─── ODE TO JOY (full arrangement, melody + harmony) ──
SONG = [   # (note, duration_beats)
    # Phrase 1
    ('E',1),('E',1),('F',1),('G',1),
    ('G',1),('F',1),('E',1),('D',1),
    ('C',1),('C',1),('D',1),('E',1),
    ('E',1.5),('D',0.5),('D',2),
    # Phrase 2
    ('E',1),('E',1),('F',1),('G',1),
    ('G',1),('F',1),('E',1),('D',1),
    ('C',1),('C',1),('D',1),('E',1),
    ('D',1.5),('C',0.5),('C',2),
    # Bridge
    ('D',1),('D',1),('E',1),('C',1),
    ('D',1),('E',0.5),('F',0.5),('E',1),('C',1),
    ('D',1),('E',0.5),('F',0.5),('E',1),('D',1),
    ('C',1),('D',1),('G',2),
    # Finale
    ('E',1),('E',1),('F',1),('G',1),
    ('G',1),('F',1),('E',1),('D',1),
    ('C',1),('C',1),('D',1),('E',1),
    ('D',1.5),('C',0.5),('C',3),
]

HARMONY = [
    ('C',2),('G',2),  ('G',2),('G',2),  ('C',2),('G',2),  ('G',2),('G',2),
    ('C',2),('G',2),  ('G',2),('G',2),  ('C',2),('G',2),  ('G',2),('G',2),
    ('G',4),('G',4),('G',4),('C',2),('G',2),
    ('C',2),('G',2),  ('G',2),('G',2),  ('C',2),('G',2),  ('G',2),('G',3),
]

BPM = 108

# ─── AUDIO SYNTHESIS ──────────────────────────────────
def marimba_tone(freq, dur, vel=0.82):
    if freq == 0:
        return np.zeros(int(SAMPLE_RATE * dur))
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    tone = (
        vel        * np.sin(2*np.pi*freq*1*t) * np.exp(-2.2*t) +
        vel * 0.25 * np.sin(2*np.pi*freq*2*t) * np.exp(-5.0*t) +
        vel * 0.09 * np.sin(2*np.pi*freq*3*t) * np.exp(-9.0*t) +
        vel * 0.03 * np.sin(2*np.pi*freq*4*t) * np.exp(-15*t)
    )
    atk = min(int(0.006*SAMPLE_RATE), len(tone))
    tone[:atk] *= np.linspace(0, 1, atk)
    # reverb
    dly = int(0.055*SAMPLE_RATE)
    if dly < len(tone):
        tone[dly:] += tone[:-dly]*0.28
    return tone

def build_sound_cache():
    cache = {}
    for n, f in FREQS.items():
        buf = marimba_tone(f, 2.5)
        mx  = np.max(np.abs(buf)) or 1
        buf = (buf/mx * 0.75 * 32767).astype(np.int16)
        stereo = np.column_stack([buf, buf])
        snd = pygame.sndarray.make_sound(stereo)
        cache[n] = snd
    return cache

# ─── PARTICLES ────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -1)
        self.life = 1.0
        self.color = color
        self.r = random.randint(2, 5)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.25
        self.life -= 0.035
        return self.life > 0

    def draw(self, surf):
        alpha = max(0, int(self.life * 255))
        c = (*self.color, alpha)
        s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, c, (self.r, self.r), self.r)
        surf.blit(s, (int(self.x)-self.r, int(self.y)-self.r))

# ─── MARBLE ───────────────────────────────────────────
class Marble:
    def __init__(self, lane, color, x_start, y_start):
        self.lane    = lane
        self.color   = color
        self.x       = float(x_start)
        self.y       = float(y_start)
        self.vy      = 0.0
        self.active  = True
        self.hit     = False
        self.trail   = deque(maxlen=12)
        self.r       = 11

    def update(self, drum_y):
        self.trail.append((self.x, self.y))
        self.vy   += 0.55
        self.y    += self.vy
        if self.y >= drum_y - self.r:
            self.y  = drum_y - self.r
            self.vy = 0
            self.hit = True
            self.active = False

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            a = int(255 * (i / len(self.trail)) * 0.35)
            r = max(2, self.r - (len(self.trail)-i)//2)
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, a), (r, r), r)
            surf.blit(s, (int(tx)-r, int(ty)-r))
        # glow
        gs = pygame.Surface((self.r*4, self.r*4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.color, 60),
                           (self.r*2, self.r*2), self.r*2)
        surf.blit(gs, (int(self.x)-self.r*2, int(self.y)-self.r*2))
        # body
        pygame.draw.circle(surf, self.color,
                           (int(self.x), int(self.y)), self.r)
        # shine
        pygame.draw.circle(surf, (255,255,255),
                           (int(self.x)-3, int(self.y)-4), 3)

# ─── HAMMER ───────────────────────────────────────────
class Hammer:
    def __init__(self, x, y):
        self.x       = x
        self.base_y  = y
        self.y       = float(y)
        self.strike  = False
        self.angle   = 0.0          # for rotation animation
        self.timer   = 0

    def trigger(self):
        self.strike = True
        self.timer  = 18

    def update(self):
        if self.strike:
            self.angle = math.sin(self.timer * 0.35) * 38
            self.timer -= 1
            if self.timer <= 0:
                self.strike = False
                self.angle  = 0

    def draw(self, surf, color):
        # arm pivot at top
        pivot = (self.x, self.base_y - 55)
        arm_len = 52
        rad = math.radians(self.angle - 10)
        tip_x = pivot[0] + math.sin(rad) * arm_len
        tip_y = pivot[1] + math.cos(rad) * arm_len

        # arm
        pygame.draw.line(surf, (160, 140, 100), pivot,
                         (int(tip_x), int(tip_y)), 5)
        # head
        hc = color if self.strike else (100, 90, 80)
        pygame.draw.circle(surf, hc, (int(tip_x), int(tip_y)), 9)
        pygame.draw.circle(surf, (200, 180, 140),
                           (int(tip_x), int(tip_y)), 9, 2)
        # pivot pin
        pygame.draw.circle(surf, (180, 160, 120), pivot, 5)

# ─── MAIN APP ─────────────────────────────────────────
class HoneylightApp:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16,
                          channels=2, buffer=512)
        self.screen  = pygame.display.set_mode((W, H))
        pygame.display.set_caption(
            "✦ HONEYLIGHT — The Solar Marble Quipu ✦")
        self.clock   = pygame.time.Clock()

        # fonts
        self.font_lg = pygame.font.SysFont('Georgia', 26, bold=True)
        self.font_md = pygame.font.SysFont('Georgia', 18)
        self.font_sm = pygame.font.SysFont('Courier',  14)

        # geometry
        n = len(NOTES)
        self.LANE_X   = [160 + i * 130 for i in range(n)]
        self.LED_Y    = 90
        self.TRACK_Y1 = 130
        self.TRACK_Y2 = 480
        self.DRUM_Y   = 560
        self.HAM_Y    = 510
        self.EXPORT_BTN = pygame.Rect(W-200, H-60, 175, 42)

        # sound
        print("Building sound cache…", end=' ', flush=True)
        self.sounds  = build_sound_cache()
        print("done")

        # state
        self.marbles    = []
        self.particles  = []
        self.hammers    = {n: Hammer(self.LANE_X[i], self.HAM_Y)
                           for i, n in enumerate(NOTES)}
        self.led_colors = {n: NOTE_COLORS['R'] for n in NOTES}
        self.led_bright = {n: 0.0 for n in NOTES}
        self.active_note= None
        self.note_label = ""
        self.waveform   = deque([0.0]*220, maxlen=220)
        self.score_pos  = 0
        self.beat_timer = 0.0
        self.beat_sec   = 60.0 / BPM
        self.playing    = True
        self.exporting  = False
        self.export_msg = ""
        self.frames_cap = []        # for mp4 export
        self.recording  = False

        # precompute song schedule
        self.schedule   = []        # list of (beat_offset, note)
        offset = 0
        for note, dur in SONG:
            self.schedule.append((offset, note, dur))
            offset += dur
        self.total_beats = offset
        self.elapsed_beats = 0.0

    # ─── UPDATE ───────────────────────────────────────
    def update(self, dt):
        if not self.playing:
            return

        self.elapsed_beats += dt / self.beat_sec

        # check for new notes
        while (self.score_pos < len(self.schedule) and
               self.schedule[self.score_pos][0] <= self.elapsed_beats):
            _, note, dur = self.schedule[self.score_pos]
            self.fire_note(note, dur)
            self.score_pos += 1

        # loop
        if self.score_pos >= len(self.schedule):
            self.elapsed_beats = 0.0
            self.score_pos = 0

        # update marbles
        alive = []
        for m in self.marbles:
            m.update(self.DRUM_Y)
            if m.hit and not m.active:
                # trigger hammer + particles
                self.hammers[m.lane].trigger()
                col = NOTE_COLORS.get(m.lane, (200,200,200))
                for _ in range(28):
                    self.particles.append(
                        Particle(m.x, self.DRUM_Y - 12, col))
                m.hit = False
            elif m.active:
                alive.append(m)
            # keep dead marbles one more frame for hit flash
        self.marbles = alive

        # update hammers
        for h in self.hammers.values():
            h.update()

        # update particles
        self.particles = [p for p in self.particles if p.update()]

        # fade LEDs
        for n in NOTES:
            if self.led_bright[n] > 0:
                self.led_bright[n] = max(0, self.led_bright[n] - dt*1.8)

        # fake waveform from active notes
        wave_v = sum(self.led_bright[n] for n in NOTES) / len(NOTES)
        noise  = random.gauss(0, wave_v * 0.4)
        self.waveform.append(noise)

    def fire_note(self, note, dur):
        if note == 'R':
            return
        idx   = NOTES.index(note)
        lx    = self.LANE_X[idx]
        col   = NOTE_COLORS[note]
        # spawn marble
        self.marbles.append(Marble(note, col, lx, self.TRACK_Y1))
        # light LED
        self.led_colors[note] = col
        self.led_bright[note] = 1.0
        # play sound
        self.sounds[note].play()
        self.active_note = note
        self.note_label  = note if note != 'C2' else "C'"

    # ─── DRAW ─────────────────────────────────────────
    def draw(self):
        surf = self.screen

        # ── background ──
        for y in range(H):
            t   = y / H
            col = (int(8+t*10), int(8+t*14), int(16+t*22))
            pygame.draw.line(surf, col, (0, y), (W, y))

        self._draw_stars(surf)
        self._draw_title(surf)
        self._draw_quipu_header(surf)
        self._draw_led_bar(surf)
        self._draw_tracks(surf)
        self._draw_drum(surf)
        self._draw_hammers(surf)
        self._draw_marbles(surf)
        self._draw_particles(surf)
        self._draw_waveform(surf)
        self._draw_note_display(surf)
        self._draw_legend(surf)
        self._draw_export_button(surf)
        self._draw_progress(surf)

        pygame.display.flip()

    def _draw_stars(self, surf):
        if not hasattr(self, '_stars'):
            self._stars = [(random.randint(0, W), random.randint(0, H//3),
                            random.randint(1,2)) for _ in range(80)]
        t = time.time()
        for sx, sy, sr in self._stars:
            br = int(100 + 60 * math.sin(t*0.7 + sx*0.1))
            pygame.draw.circle(surf, (br,br,br), (sx,sy), sr)

    def _draw_title(self, surf):
        t1 = self.font_lg.render(
            "✦  H O N E Y L I G H T  ✦", True, (220, 190, 100))
        t2 = self.font_sm.render(
            "The Solar Marble Quipu  —  LED Colors → Marbles → Hammers → Music",
            True, (150, 140, 110))
        surf.blit(t1, (W//2 - t1.get_width()//2, 12))
        surf.blit(t2, (W//2 - t2.get_width()//2, 46))

    def _draw_quipu_header(self, surf):
        lbl = self.font_sm.render(
            "☀  SUN  →  CAMERA  →  LED BAR (quipu)  →  MARBLES  →  HAMMERS  →  DRUM  →  🎵",
            True, (120, 160, 120))
        surf.blit(lbl, (W//2 - lbl.get_width()//2, 66))

    def _draw_led_bar(self, surf):
        bar_y  = self.LED_Y
        bar_h  = 28
        for i, note in enumerate(NOTES):
            lx  = self.LANE_X[i]
            br  = self.led_bright[note]
            col = NOTE_COLORS[note]
            # glow
            if br > 0:
                gs = int(br * 60)
                gl = pygame.Surface((90, 60), pygame.SRCALPHA)
                pygame.draw.ellipse(gl, (*col, gs), (0, 0, 90, 60))
                surf.blit(gl, (lx-45, bar_y-18))
            # LED body
            bc  = tuple(int(c * (0.15 + 0.85*br)) for c in col)
            rect= pygame.Rect(lx-26, bar_y, 52, bar_h)
            pygame.draw.rect(surf, bc, rect, border_radius=8)
            pygame.draw.rect(surf, (200,200,180), rect, 2,
                             border_radius=8)
            # label
            lbl = 'C\'' if note=='C2' else note
            txt = self.font_sm.render(lbl, True,
                  (240,240,240) if br > 0.3 else (100,100,100))
            surf.blit(txt, (lx - txt.get_width()//2,
                            bar_y + bar_h + 4))

        # LED bar bracket
        x0 = self.LANE_X[0] - 36
        x1 = self.LANE_X[-1]+ 36
        pygame.draw.rect(surf, (80,70,60),
                         (x0, bar_y-4, x1-x0, bar_h+8),
                         2, border_radius=10)
        lbl = self.font_sm.render("◈ LED QUIPU BAR", True, (140,130,100))
        surf.blit(lbl, (x0, bar_y - 22))

    def _draw_tracks(self, surf):
        for i, note in enumerate(NOTES):
            lx  = self.LANE_X[i]
            col = NOTE_COLORS[note]
            # channel walls
            pygame.draw.line(surf, (50,48,44),
                             (lx-14, self.TRACK_Y1+30),
                             (lx-14, self.TRACK_Y2), 2)
            pygame.draw.line(surf, (50,48,44),
                             (lx+14, self.TRACK_Y1+30),
                             (lx+14, self.TRACK_Y2), 2)
            # subtle color wash
            for yy in range(self.TRACK_Y1+30, self.TRACK_Y2, 4):
                pygame.draw.line(surf,
                    tuple(int(c*0.06) for c in col),
                    (lx-13, yy), (lx+13, yy))
            # gate
            gt_y = self.TRACK_Y1 + 24
            pygame.draw.line(surf, (100,90,70),
                             (lx-14, gt_y), (lx+14, gt_y), 3)

    def _draw_drum(self, surf):
        # wooden resonator box
        box_x  = self.LANE_X[0]  - 50
        box_w  = self.LANE_X[-1] - self.LANE_X[0] + 100
        box_y  = self.DRUM_Y - 10
        box_h  = 120

        for dy in range(box_h):
            t   = dy / box_h
            col = (int(80+t*30), int(50+t*20), int(20+t*10))
            pygame.draw.line(surf, col,
                             (box_x, box_y+dy), (box_x+box_w, box_y+dy))
        pygame.draw.rect(surf, (120, 80, 40),
                         (box_x, box_y, box_w, box_h), 3,
                         border_radius=6)

        # drum surface / strike zones per note
        for i, note in enumerate(NOTES):
            lx  = self.LANE_X[i]
            br  = self.led_bright[note]
            col = NOTE_COLORS[note]
            base= (60, 55, 45)
            zc  = tuple(int(base[j] + (col[j]-base[j])*br*0.7)
                        for j in range(3))
            pygame.draw.ellipse(surf, zc,
                                (lx-22, self.DRUM_Y-14, 44, 20))
            pygame.draw.ellipse(surf, (100,90,70),
                                (lx-22, self.DRUM_Y-14, 44, 20), 2)

        lbl = self.font_sm.render(
            "◈  STEEL TONGUE DRUM  —  RESONATOR CAVITY",
            True, (160, 130, 80))
        surf.blit(lbl, (W//2 - lbl.get_width()//2, box_y + box_h + 4))

        # note frequency labels
        for i, note in enumerate(NOTES):
            lx = self.LANE_X[i]
            hz = FREQS[note]
            f  = self.font_sm.render(f"{hz:.0f}Hz", True, (100,90,70))
            surf.blit(f, (lx - f.get_width()//2, box_y + box_h + 22))

    def _draw_hammers(self, surf):
        lbl = self.font_sm.render("◈  SOLENOID HAMMERS",
                                  True, (140,130,100))
        surf.blit(lbl, (self.LANE_X[0]-36, self.HAM_Y - 72))
        for i, note in enumerate(NOTES):
            col = NOTE_COLORS[note]
            br  = self.led_bright[note]
            hcol= tuple(min(255, int(c*(0.4+0.6*br))) for c in col)
            self.hammers[note].draw(surf, hcol)

    def _draw_marbles(self, surf):
        for m in self.marbles:
            m.draw(surf)

    def _draw_particles(self, surf):
        for p in self.particles:
            p.draw(surf)

    def _draw_waveform(self, surf):
        ww, wh = 340, 70
        wx, wy = W//2 - ww//2, H - 130
        # background
        wb = pygame.Surface((ww, wh), pygame.SRCALPHA)
        wb.fill((0, 0, 0, 100))
        surf.blit(wb, (wx, wy))
        pygame.draw.rect(surf, (80,80,60), (wx, wy, ww, wh), 1,
                         border_radius=4)

        pts = list(self.waveform)
        mid = wy + wh//2
        step= ww / len(pts)
        prev= None
        for j, v in enumerate(pts):
            px = int(wx + j*step)
            py = int(mid + v * wh * 0.45)
            py = max(wy+2, min(wy+wh-2, py))
            if prev:
                br  = self.led_bright.get(self.active_note or 'C', 0)
                col = NOTE_COLORS.get(self.active_note or 'C',
                                      (100,200,100))
                wc  = tuple(int(60 + c*0.6*br) for c in col)
                pygame.draw.line(surf, wc, prev, (px, py), 2)
            prev = (px, py)

        lbl = self.font_sm.render("◈ ACOUSTIC OUTPUT",
                                  True, (120,140,100))
        surf.blit(lbl, (wx, wy - 18))

    def _draw_note_display(self, surf):
        if not self.active_note:
            return
        note = self.active_note
        br   = self.led_bright.get(note, 0)
        col  = NOTE_COLORS.get(note, (200,200,200))
        lbl  = 'C\'' if note=='C2' else note
        glow = pygame.Surface((140,140), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, int(br*80)), (70,70), 70)
        surf.blit(glow, (W - 175, H - 190))
        nt = self.font_lg.render(lbl, True,
             tuple(min(255,int(c*br+60)) for c in col))
        surf.blit(nt, (W - 140, H - 165))
        f2 = self.font_sm.render(f"{FREQS[note]:.1f} Hz",
                                 True, (150,150,130))
        surf.blit(f2, (W - 148, H - 135))
        cn = self.font_sm.render("current note", True, (100,100,80))
        surf.blit(cn, (W - 155, H - 112))

    def _draw_legend(self, surf):
        lx, ly = 18, 220
        ttl = self.font_sm.render("NOTE → COLOR", True, (160,150,120))
        surf.blit(ttl, (lx, ly))
        for j, note in enumerate(NOTES):
            col = NOTE_COLORS[note]
            pygame.draw.rect(surf, col,
                             (lx, ly+20+j*26, 18, 18),
                             border_radius=4)
            lbl = 'C\'' if note=='C2' else note
            nm  = self.font_sm.render(
                f"{lbl}  {FREQS[note]:.0f}Hz", True, (180,170,140))
            surf.blit(nm, (lx+24, ly+21+j*26))

        # farm theme labels
        themes = ['earth','honey','sun','pasture',
                  'open air','dusk','moonlight','dawn']
        for j, th in enumerate(themes):
            tm = self.font_sm.render(th, True, (100,100,80))
            surf.blit(tm, (lx+105, ly+21+j*26))

    def _draw_export_button(self, surf):
        col = (60,140,80) if not self.exporting else (100,80,40)
        pygame.draw.rect(surf, col, self.EXPORT_BTN,
                         border_radius=8)
        pygame.draw.rect(surf, (180,200,160), self.EXPORT_BTN,
                         2, border_radius=8)
        txt = "⬛ EXPORT MP4" if not self.exporting else "Exporting…"
        t   = self.font_md.render(txt, True, (220,240,210))
        surf.blit(t, (self.EXPORT_BTN.x + self.EXPORT_BTN.w//2
                      - t.get_width()//2,
                      self.EXPORT_BTN.y + 10))
        if self.export_msg:
            em = self.font_sm.render(self.export_msg,
                                     True, (140,200,140))
            surf.blit(em, (self.EXPORT_BTN.x,
                           self.EXPORT_BTN.y + self.EXPORT_BTN.h + 6))

    def _draw_progress(self, surf):
        if not self.schedule:
            return
        pct  = min(1.0, self.elapsed_beats / self.total_beats)
        bw   = W - 40
        by   = H - 28
        pygame.draw.rect(surf, (40,40,35), (20, by, bw, 10),
                         border_radius=5)
        pygame.draw.rect(surf, (150,180,100),
                         (20, by, int(bw*pct), 10),
                         border_radius=5)
        lbl  = self.font_sm.render(
            "♩ Ode to Joy — Beethoven  (Honeylight marimba arrangement)",
            True, (120,120,100))
        surf.blit(lbl, (20, by - 18))

    # ─── MP4 EXPORT ───────────────────────────────────
    def start_export(self):
        if self.exporting:
            return
        self.exporting  = True
        self.recording  = True
        self.frames_cap = []
        self.export_msg = "Recording 15s…"
        threading.Thread(target=self._export_worker,
                         daemon=True).start()

    def capture_frame(self):
        if self.recording:
            raw = pygame.surfarray.array3d(self.screen)
            # pygame is (W,H,3), ffmpeg wants (H,W,3)
            self.frames_cap.append(np.transpose(raw, (1,0,2)).copy())
            if len(self.frames_cap) >= FPS * 15:
                self.recording = False

    def _export_worker(self):
        # wait until recording done
        while self.recording:
            time.sleep(0.1)
        out = os.path.expanduser('~/Downloads/honeylight.mp4')
        cmd = [
            'ffmpeg','-y',
            '-f','rawvideo','-vcodec','rawvideo',
            '-s', f'{W}x{H}',
            '-pix_fmt','rgb24',
            '-r', str(FPS),
            '-i','pipe:0',
            '-vcodec','libx264',
            '-pix_fmt','yuv420p',
            '-preset','fast',
            '-crf','22',
            out
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)
        for frame in self.frames_cap:
            proc.stdin.write(frame.astype(np.uint8).tobytes())
        proc.stdin.close()
        proc.wait()
        self.exporting  = False
        self.export_msg = f"✓ Saved: ~/Downloads/honeylight.mp4"
        self.frames_cap = []

    # ─── MAIN LOOP ────────────────────────────────────
    def run(self):
        last = time.time()
        while True:
            now = time.time()
            dt  = now - last
            last= now

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_SPACE:
                        self.playing = not self.playing
                    if event.key == pygame.K_e:
                        self.start_export()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.EXPORT_BTN.collidepoint(event.pos):
                        self.start_export()

            self.update(dt)
            self.draw()
            if self.recording:
                self.capture_frame()
            self.clock.tick(FPS)


# ─── ENTRY POINT ──────────────────────────────────────
if __name__ == '__main__':
    print("╔══════════════════════════════════════════╗")
    print("║   HONEYLIGHT — The Solar Marble Quipu   ║")
    print("╠══════════════════════════════════════════╣")
    print("║  SPACE = pause/play                      ║")
    print("║  E     = export 15s MP4                  ║")
    print("║  ESC   = quit                            ║")
    print("╚══════════════════════════════════════════╝")
    HoneylightApp().run()
