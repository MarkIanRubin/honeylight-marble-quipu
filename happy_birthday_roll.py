"""
Happy Birthday — Chromatic Optical Roll + Mechanical Interface Diagram
Mark Rubin / Honeylight

Full Happy Birthday melody scrolling as a chromatic color roll.
Bottom panel shows the live signal chain:
  LED Roll → Color Sensor → Raspberry Pi → Servo Gate → Golf Ball → Tone Bar
Each element pulses with the note's color when a note fires.

Color encoding:
  Hue        = Pitch (note identity)
  Brightness = Velocity (dynamics: dim=piano, bright=forte)
  Saturation = Articulation (washed=legato, vivid=staccato)
  Block length = Duration
  White flash  = Accent
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import colorsys

# ── Configuration ──────────────────────────────────────────────────────────────
NUM_LANES     = 8
FPS           = 30
BPM           = 90   # waltz tempo
EIGHTH_FRAMES = max(1, int(round(FPS * 60 / BPM / 2)))   # frames per 8th-note column
SENSOR_COL    = 20   # x position of the sensor/read bar
VISIBLE_COLS  = 72   # how many columns are visible at once

# ── Note / Color Definitions ───────────────────────────────────────────────────
LANE_NAMES   = ['C','D','E','F','G','A','B','─']
NOTE_TO_LANE = {'C':0,'D':1,'E':2,'F':3,'G':4,'A':5,'B':6,'_':7}

BASE_HUE = {          # HSV hue per note
    'C': 0.00,        # Red
    'D': 0.07,        # Orange
    'E': 0.14,        # Yellow
    'F': 0.28,        # Lime Green
    'G': 0.50,        # Cyan
    'A': 0.63,        # Blue
    'B': 0.77,        # Violet
}

def note_to_rgb(note, velocity=1.0, articulation='normal', accent=False):
    """Convert musical properties to an RGB colour."""
    if note in ('_', '─'):
        return np.array([0.02, 0.02, 0.06])
    h = BASE_HUE[note]
    v = 0.25 + 0.75 * velocity                           # brightness = dynamics
    s = {'legato': 0.30, 'staccato': 1.0}.get(articulation, 0.80)  # saturation = articulation
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    if accent:                                            # white flash on accent
        r, g, b = min(1,r+0.45), min(1,g+0.45), min(1,b+0.45)
    return np.array([r, g, b])

def arr_to_hex(arr):
    r,g,b = int(arr[0]*255), int(arr[1]*255), int(arr[2]*255)
    return f'#{r:02x}{g:02x}{b:02x}'

# ── Happy Birthday Score ───────────────────────────────────────────────────────
# (note, dur_8th_notes, velocity, articulation, accent, lyric_syllable)
# Notes used: C D E F G A B  — all 7 natural notes, exactly one octave
SONG = [
    # ——— LINE 1: "Happy Birthday to You" ———————————————————————
    ('G', 1, 0.65, 'staccato', False, 'Hap-'),
    ('G', 1, 0.65, 'staccato', False, 'py'),
    ('A', 2, 0.85, 'normal',   False, 'Birth-'),
    ('G', 2, 0.85, 'normal',   False, 'day'),
    ('C', 2, 0.80, 'normal',   False, 'to'),
    ('B', 4, 1.00, 'legato',   False, 'You'),
    ('_', 2, 0.00, 'normal',   False, ''),

    # ——— LINE 2: "Happy Birthday to You" ———————————————————————
    ('G', 1, 0.65, 'staccato', False, 'Hap-'),
    ('G', 1, 0.65, 'staccato', False, 'py'),
    ('A', 2, 0.85, 'normal',   False, 'Birth-'),
    ('G', 2, 0.85, 'normal',   False, 'day'),
    ('D', 2, 0.80, 'normal',   False, 'to'),
    ('C', 4, 1.00, 'legato',   False, 'You'),
    ('_', 2, 0.00, 'normal',   False, ''),

    # ——— LINE 3: "Happy Birthday Dear Mark" ————————————————————
    ('G', 1, 0.65, 'staccato', False, 'Hap-'),
    ('G', 1, 0.65, 'staccato', False, 'py'),
    ('G', 2, 1.00, 'normal',   True,  'Birth-'),   # high G — accented + white flash
    ('E', 2, 0.90, 'normal',   False, 'day'),
    ('C', 2, 0.85, 'normal',   False, 'dear'),
    ('B', 2, 0.85, 'normal',   False, 'Mar-'),
    ('A', 4, 1.00, 'legato',   False, 'k  ♩'),
    ('_', 2, 0.00, 'normal',   False, ''),

    # ——— LINE 4: "Happy Birthday to You" (final) ——————————————
    ('F', 1, 0.80, 'staccato', False, 'Hap-'),
    ('F', 1, 0.80, 'staccato', False, 'py'),
    ('E', 2, 0.90, 'normal',   False, 'Birth-'),
    ('C', 2, 0.90, 'normal',   False, 'day'),
    ('D', 2, 0.85, 'normal',   False, 'to'),
    ('C', 6, 1.00, 'legato',   False, 'You! 🎂'),
    ('_', 6, 0.00, 'normal',   False, ''),
]

# ── Build column list ──────────────────────────────────────────────────────────
# Each column dict: colours array (NUM_LANES,3), note label, lyric, lane index
def build_columns():
    cols = []
    silence = {'colors': np.full((NUM_LANES,3), 0.02),
               'note':'─','lyric':'','vel':0,'artic':'normal','lane':-1,'accent':False}
    for _ in range(14):
        cols.append({**silence, 'colors': np.full((NUM_LANES,3), 0.02)})

    for (note, dur, vel, artic, acc, lyric) in SONG:
        grid = np.full((NUM_LANES,3), 0.02)
        lane = -1
        if note not in ('_','─'):
            lane = NOTE_TO_LANE[note]
            grid[lane] = note_to_rgb(note, vel, artic, acc)
        for i in range(dur):
            cols.append({'colors': grid.copy(), 'note': note if note!='_' else '─',
                         'lyric': lyric if i==0 else '', 'vel': vel,
                         'artic': artic, 'lane': lane, 'accent': acc})

    for _ in range(SENSOR_COL + 10):
        cols.append({**silence, 'colors': np.full((NUM_LANES,3), 0.02)})
    return cols

COLUMNS      = build_columns()
TOTAL_COLS   = len(COLUMNS)
TOTAL_FRAMES = TOTAL_COLS * EIGHTH_FRAMES + FPS

# ── Figure Layout ──────────────────────────────────────────────────────────────
BG = '#03030b'
fig = plt.figure(figsize=(16, 9), facecolor=BG)

# ── Panel A: Color Roll ────────────────────────────────────────────────────────
ax_roll = fig.add_axes([0.05, 0.40, 0.90, 0.50])
ax_roll.set_facecolor(BG)
ax_roll.set_xlim(0, VISIBLE_COLS)
ax_roll.set_ylim(-0.5, NUM_LANES-0.5)
ax_roll.set_yticks(range(NUM_LANES))
ax_roll.set_yticklabels([f'  {n}' for n in LANE_NAMES],
                         color='#666688', fontsize=11, fontfamily='monospace')
ax_roll.set_xticks([])
ax_roll.spines[:].set_visible(False)
ax_roll.tick_params(left=False)
# Lane separator lines
for lane in range(NUM_LANES-1):
    ax_roll.axhline(lane+0.5, color='#0e0e22', lw=0.6, zorder=3)

# Titles
fig.text(0.5, 0.975, '◈  CHROMATIC OPTICAL ROLL  —  HAPPY BIRTHDAY  ◈',
         ha='center', color='#cccccc', fontsize=14, fontfamily='monospace', fontweight='bold')
fig.text(0.5, 0.945,
         'COLOUR = PITCH   ·   BRIGHTNESS = VELOCITY   ·   SATURATION = ARTICULATION   ·   LENGTH = DURATION',
         ha='center', color='#333355', fontsize=8, fontfamily='monospace')

# Roll image
roll_img = np.full((NUM_LANES, VISIBLE_COLS, 3), 0.02)
im = ax_roll.imshow(roll_img, aspect='auto', origin='lower',
                    extent=[0, VISIBLE_COLS, -0.5, NUM_LANES-0.5],
                    interpolation='nearest', vmin=0, vmax=1)

# Sensor bar
ax_roll.axvline(SENSOR_COL+0.5, color='white', lw=2.2, alpha=0.90, zorder=5)
ax_roll.text(SENSOR_COL+0.5, NUM_LANES-0.05, '▼ READ',
             ha='center', color='#ffffff', fontsize=8, fontfamily='monospace', zorder=6)

# Past overlay (dims already-played columns)
past_mask = patches.Rectangle((0, -0.5), SENSOR_COL+0.5, NUM_LANES,
                                facecolor=BG, alpha=0.54, zorder=4)
ax_roll.add_patch(past_mask)

# Colour legend strip at very top
ax_legend = fig.add_axes([0.05, 0.930, 0.90, 0.012])
ax_legend.axis('off')
ax_legend.set_xlim(0,1); ax_legend.set_ylim(0,1)
for i, note in enumerate(LANE_NAMES[:-1]):
    c = note_to_rgb(note, 1.0, 'staccato')
    x = i / 7
    w = 1 / 7
    ax_legend.add_patch(patches.Rectangle((x,0), w, 1, facecolor=tuple(c), edgecolor='none'))
    ax_legend.text(x+w/2, -0.8, note, ha='center', color='#555577',
                   fontsize=8, fontfamily='monospace', va='top')

# ── Panel B: Live Sensor Readout ───────────────────────────────────────────────
ax_sensor = fig.add_axes([0.05, 0.28, 0.90, 0.10])
ax_sensor.set_facecolor('#070714')
ax_sensor.set_xlim(0,1); ax_sensor.set_ylim(0,1); ax_sensor.axis('off')

ax_sensor.text(0.00, 1.05, 'SENSOR READING', color='#333355',
               fontsize=7, fontfamily='monospace', va='bottom')

# Colour swatch that matches firing note
swatch = patches.Rectangle((0.01,0.12), 0.055, 0.76,
                             facecolor='#111133', edgecolor='#222244',
                             linewidth=1, zorder=2)
ax_sensor.add_patch(swatch)

note_txt  = ax_sensor.text(0.09, 0.50, '─', va='center',
                            color='#444466', fontsize=26,
                            fontfamily='monospace', fontweight='bold')
lyric_txt = ax_sensor.text(0.22, 0.50, '', va='center',
                            color='#888899', fontsize=18,
                            fontfamily='monospace', fontstyle='italic')
vel_txt   = ax_sensor.text(0.72, 0.72, 'vel: ─', va='center',
                            color='#333355', fontsize=9, fontfamily='monospace')
art_txt   = ax_sensor.text(0.72, 0.28, 'artic: ─', va='center',
                            color='#333355', fontsize=9, fontfamily='monospace')
lane_txt  = ax_sensor.text(0.88, 0.50, 'LANE ─', va='center',
                            color='#333355', fontsize=9, fontfamily='monospace')

# ── Panel C: Mechanical Signal Chain ──────────────────────────────────────────
ax_mech = fig.add_axes([0.02, 0.01, 0.96, 0.25])
ax_mech.set_facecolor(BG)
ax_mech.set_xlim(0,1); ax_mech.set_ylim(0,1); ax_mech.axis('off')

fig.text(0.5, 0.275, '─── MECHANICAL SIGNAL CHAIN ───',
         ha='center', color='#222244', fontsize=8, fontfamily='monospace')

CHAIN = [
    (0.02,  'LED', 'LED\nMATRIX',    'Color roll\npainted by AI'),
    (0.19,  'RGB', 'COLOR\nSENSOR',  '8x TCS34725\nRGB readers'),
    (0.36,  'Pi',  'RASPBERRY\nPI',  'Decodes color\nto note+vel'),
    (0.53,  '[>]', 'SERVO\nGATE',    'Opens for\nball release'),
    (0.70,  '( )', 'GOLF\nBALL',     'Rolls down\nangled ramp'),
    (0.87,  '[|]', 'TONE\nBAR',      'Struck rings\nat pitch'),
]
BOX_W, BOX_H = 0.10, 0.68

mech_rects  = []
mech_emojis = []
mech_labels = []
mech_descs  = []

for (x, emoji, label, desc) in CHAIN:
    rect = patches.FancyBboxPatch(
        (x, 0.18), BOX_W, BOX_H,
        boxstyle='round,pad=0.015',
        facecolor='#0a0a1a', edgecolor='#1a1a3a', linewidth=1.5, zorder=2)
    ax_mech.add_patch(rect)
    mech_rects.append(rect)

    e = ax_mech.text(x+BOX_W/2, 0.72, emoji, ha='center', va='center',
                     fontsize=16, zorder=3)
    mech_emojis.append(e)

    l = ax_mech.text(x+BOX_W/2, 0.50, label, ha='center', va='center',
                     color='#444466', fontsize=8, fontfamily='monospace',
                     multialignment='center', fontweight='bold', zorder=3)
    mech_labels.append(l)

    d = ax_mech.text(x+BOX_W/2, 0.28, desc, ha='center', va='center',
                     color='#2a2a44', fontsize=6.5, fontfamily='monospace',
                     multialignment='center', zorder=3)
    mech_descs.append(d)

    # Arrow to next box
    if x != CHAIN[-1][0]:
        ax_mech.annotate('', xy=(x+BOX_W+0.06, 0.52), xytext=(x+BOX_W+0.0, 0.52),
                         arrowprops=dict(arrowstyle='->', color='#1a1a3a', lw=1.8),
                         zorder=1)

# ── Animation ─────────────────────────────────────────────────────────────────
sticky_lyric = ['']

def update(frame):
    col_idx = min(frame // EIGHTH_FRAMES, TOTAL_COLS - 1)

    # Build the visible roll buffer
    view = np.full((NUM_LANES, VISIBLE_COLS, 3), 0.02)
    for vc in range(VISIBLE_COLS):
        src = col_idx - SENSOR_COL + vc
        if 0 <= src < TOTAL_COLS:
            view[:, vc, :] = COLUMNS[src]['colors']

    # Gentle shimmer on future columns (right of sensor)
    shimmer = 1.0 + 0.045 * np.sin(frame * 0.38 + np.arange(VISIBLE_COLS) * 0.35)
    view = np.clip(view * shimmer[np.newaxis, :, np.newaxis], 0, 1)
    im.set_data(view)

    # What's at the sensor right now
    cur   = COLUMNS[col_idx]
    note  = cur['note']
    lyric = cur['lyric']
    if lyric:
        sticky_lyric[0] = lyric
    vel   = cur['vel']
    artic = cur['artic']
    lane  = cur['lane']

    if note != '─' and lane >= 0:
        c        = COLUMNS[col_idx]['colors'][lane]
        hex_col  = arr_to_hex(c)
        dim_col  = tuple(np.clip(c * 0.18, 0, 1))

        # Sensor panel
        swatch.set_facecolor(tuple(c))
        swatch.set_edgecolor(hex_col)
        note_txt.set_text(note)
        note_txt.set_color(hex_col)
        lyric_txt.set_text(sticky_lyric[0])
        lyric_txt.set_color('#cccccc')
        vel_txt.set_text(f'vel: {vel:.2f}')
        vel_txt.set_color('#8888aa')
        art_txt.set_text(f'artic: {artic}')
        art_txt.set_color('#8888aa')
        lane_txt.set_text(f'LANE {lane+1}')
        lane_txt.set_color(hex_col)

        # Mechanical chain — all 6 elements light up, last 3 brighter
        for i, (rect, lbl, desc) in enumerate(zip(mech_rects, mech_labels, mech_descs)):
            rect.set_edgecolor(hex_col)
            rect.set_linewidth(2.2)
            if i >= 3:                                # gate / ball / bar = vivid
                rect.set_facecolor(dim_col)
            else:                                     # led / sensor / pi = subtle
                rect.set_facecolor('#0e0e22')
            lbl.set_color('#ccccee')
            desc.set_color('#666688')
    else:
        # Rest — all dims
        swatch.set_facecolor('#0d0d22')
        swatch.set_edgecolor('#1a1a33')
        note_txt.set_text('─')
        note_txt.set_color('#333355')
        lyric_txt.set_text('')
        vel_txt.set_text('vel: ─')
        vel_txt.set_color('#333355')
        art_txt.set_text('artic: ─')
        art_txt.set_color('#333355')
        lane_txt.set_text('LANE ─')
        lane_txt.set_color('#333355')
        for rect, lbl, desc in zip(mech_rects, mech_labels, mech_descs):
            rect.set_facecolor('#0a0a1a')
            rect.set_edgecolor('#1a1a3a')
            rect.set_linewidth(1.5)
            lbl.set_color('#333355')
            desc.set_color('#1e1e33')

# (no blit — patches don't blit cleanly)
ani = animation.FuncAnimation(fig, update, frames=TOTAL_FRAMES,
                               interval=1000/FPS, blit=False)

out = '/Users/queenbee/chromatic-roll/happy_birthday_roll.mp4'
writer = animation.FFMpegWriter(fps=FPS, bitrate=5000,
                                 extra_args=['-vcodec','libx264','-pix_fmt','yuv420p'])
print(f"Rendering {TOTAL_FRAMES} frames ({TOTAL_FRAMES/FPS:.1f}s) at {FPS}fps  →  {out}")
ani.save(out, writer=writer, dpi=110, savefig_kwargs={'facecolor': BG})
print("Done!")
