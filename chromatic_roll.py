"""
Chromatic Optical Roll — AI Music Visualizer
Mark Rubin / Honeylight

Simulates the scrolling color roll display.
- 8 lanes, each a musical note (C D E F G A B + rest)
- Color encodes pitch, brightness encodes velocity, saturation encodes articulation
- A simple Markov-chain AI composes in real-time, painting the roll
- The "sensor bar" reads the roll and prints what note fires
- Renders to chromatic_roll.mp4
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import random
import colorsys

# ─── Constants ────────────────────────────────────────────────────────────────

NUM_LANES     = 8
ROLL_COLS     = 120       # visible columns on screen
FPS           = 30
TEMPO_BPM     = 72
BEAT_FRAMES   = int(FPS * 60 / TEMPO_BPM / 2)  # frames per 8th note
SENSOR_COL    = 20        # x position of sensor bar (read head)
TOTAL_FRAMES  = FPS * 18  # 18 second clip

# ─── Note / Color Definitions ─────────────────────────────────────────────────

NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B', '─']

# Base hues for each lane (HSV hue 0-1)
BASE_COLORS = {
    'C': (0.00, 1.0, 1.0),   # Red
    'D': (0.07, 1.0, 1.0),   # Orange
    'E': (0.14, 1.0, 1.0),   # Yellow
    'F': (0.28, 1.0, 1.0),   # Lime Green
    'G': (0.50, 1.0, 1.0),   # Cyan
    'A': (0.63, 1.0, 1.0),   # Blue
    'B': (0.77, 1.0, 1.0),   # Violet
    '─': (0.00, 0.0, 0.05),  # Near-black / rest
}

def note_to_rgb(note, velocity=1.0, articulation='normal'):
    """Convert note + dynamics to RGB color."""
    h, s, v = BASE_COLORS[note]
    if note == '─':
        return (0.03, 0.03, 0.05)
    # Velocity → brightness (0.3 piano .. 1.0 forte)
    v = 0.3 + 0.7 * velocity
    # Articulation → saturation (legato = pastel, staccato = full sat)
    if articulation == 'legato':
        s = 0.35
    elif articulation == 'staccato':
        s = 1.0
    else:
        s = 0.75
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b)

def accent_flash(color, strength=0.6):
    """Add a white flash tint for accented notes."""
    r, g, b = color
    r = min(1.0, r + strength)
    g = min(1.0, g + strength)
    b = min(1.0, b + strength)
    return (r, g, b)

# ─── Markov Chain AI Composer ─────────────────────────────────────────────────

# Transition probabilities — each note tends toward harmonically near neighbors
TRANSITIONS = {
    'C': ['C','E','G','G','E','C','─','D'],
    'D': ['D','F','A','G','E','D','C','─'],
    'E': ['E','G','B','A','F','E','C','D'],
    'F': ['F','A','C','G','E','F','D','─'],
    'G': ['G','B','D','E','A','G','C','─'],
    'A': ['A','C','E','G','B','A','F','─'],
    'B': ['B','D','G','A','F','B','G','─'],
    '─': ['C','G','E','A','─','─','C','G'],
}

ARTICULATIONS = ['staccato','staccato','normal','normal','normal','legato']

class AIComposer:
    def __init__(self):
        self.lane_states = [random.choice(NOTES) for _ in range(NUM_LANES)]
        self.beat_counter = 0
        self.mood = 0.7  # 0=calm, 1=energetic

    def next_beat(self):
        """Returns one column of note events for all 8 lanes."""
        self.beat_counter += 1
        # Drift mood slowly
        self.mood = max(0.2, min(1.0, self.mood + random.uniform(-0.05, 0.05)))

        events = []
        for lane in range(NUM_LANES):
            note = self.lane_states[lane]
            # Decide if this lane fires this beat
            rest_prob = 0.35 - 0.15 * self.mood
            if random.random() < rest_prob:
                new_note = '─'
            else:
                candidates = TRANSITIONS[note]
                new_note = random.choice(candidates)
            self.lane_states[lane] = new_note

            velocity = random.uniform(0.4, 1.0) * self.mood + 0.1
            velocity = min(1.0, velocity)
            articulation = random.choice(ARTICULATIONS)
            accent = (random.random() < 0.08)  # 8% chance of accent

            events.append({
                'note': new_note,
                'velocity': velocity,
                'articulation': articulation,
                'accent': accent,
            })
        return events

# ─── Roll Buffer ──────────────────────────────────────────────────────────────

class RollBuffer:
    """Stores the color of every cell in the scrolling roll."""
    def __init__(self, cols):
        self.cols = cols
        # shape: (NUM_LANES, cols, 3)  — RGB
        self.buffer = np.zeros((NUM_LANES, cols, 3))
        self.col_notes = ['─'] * cols  # note name per column for sensor readout

    def paint_column(self, col, events):
        """Paint one column from AI events."""
        col = col % self.cols
        for lane, ev in enumerate(events):
            color = note_to_rgb(ev['note'], ev['velocity'], ev['articulation'])
            if ev['accent'] and ev['note'] != '─':
                color = accent_flash(color, 0.4)
            self.buffer[lane, col] = color
        # store dominant note for readout (first non-rest)
        fired = [e['note'] for e in events if e['note'] != '─']
        self.col_notes[col] = ','.join(fired[:3]) if fired else '─'

    def scroll_view(self, head_col):
        """Return buffer rotated so head_col is at SENSOR_COL."""
        shift = SENSOR_COL - head_col
        return np.roll(self.buffer, shift, axis=1)

# ─── Build the Animation ──────────────────────────────────────────────────────

composer = AIComposer()
roll     = RollBuffer(ROLL_COLS)

# Pre-fill right side of buffer with upcoming notes
for c in range(ROLL_COLS):
    events = composer.next_beat()
    roll.paint_column(c, events)

# Setup figure
fig = plt.figure(figsize=(14, 6), facecolor='#05050a')
ax  = fig.add_axes([0.04, 0.18, 0.92, 0.72])
ax.set_facecolor('#05050a')
ax.set_xlim(0, ROLL_COLS)
ax.set_ylim(-0.5, NUM_LANES - 0.5)
ax.set_yticks(range(NUM_LANES))
ax.set_yticklabels([f'  {n}' for n in NOTES], color='#888888', fontsize=11, fontfamily='monospace')
ax.set_xticks([])
ax.spines[:].set_visible(False)
ax.tick_params(left=False)

# Title
fig.text(0.5, 0.94, '◈  CHROMATIC OPTICAL ROLL  ◈', ha='center', va='top',
         color='#cccccc', fontsize=15, fontfamily='monospace', fontweight='bold')
fig.text(0.5, 0.88, 'AI COMPOSER  ·  COLOR = PITCH  ·  BRIGHTNESS = VELOCITY  ·  SATURATION = ARTICULATION',
         ha='center', va='top', color='#555555', fontsize=8, fontfamily='monospace')

# Sensor bar label
sensor_label = ax.text(SENSOR_COL, NUM_LANES - 0.1, '▼ READ', ha='center',
                        color='#ffffff', fontsize=8, fontfamily='monospace', va='bottom')

# Status bar at bottom
status_ax = fig.add_axes([0.04, 0.04, 0.92, 0.10])
status_ax.set_facecolor('#0a0a12')
status_ax.set_xlim(0, 1)
status_ax.set_ylim(0, 1)
status_ax.axis('off')
status_text = status_ax.text(0.5, 0.5, '♩  ─  ─  ─  ─  ─  ─  ─', ha='center', va='center',
                               color='#00ffcc', fontsize=12, fontfamily='monospace')
mood_text   = status_ax.text(0.02, 0.5, 'MOOD ▓▓▓▓▓░░░', ha='left', va='center',
                               color='#444466', fontsize=9, fontfamily='monospace')
beat_text   = status_ax.text(0.98, 0.5, 'BEAT 0001', ha='right', va='center',
                               color='#444466', fontsize=9, fontfamily='monospace')

# Color legend
legend_ax = fig.add_axes([0.04, 0.0, 0.92, 0.03])
legend_ax.set_facecolor('#05050a')
legend_ax.axis('off')
for i, note in enumerate(NOTES[:-1]):
    xpos = 0.06 + i * 0.13
    color = note_to_rgb(note, 1.0, 'staccato')
    legend_ax.add_patch(patches.Rectangle((xpos - 0.02, 0.1), 0.04, 0.8,
                                           facecolor=color, edgecolor='none'))
    legend_ax.text(xpos, -0.3, note, ha='center', va='top',
                   color='#888888', fontsize=8, fontfamily='monospace')

# ─── Image grid for the roll ──────────────────────────────────────────────────

# We draw each cell as a colored rectangle — use imshow for speed
img_data = np.zeros((NUM_LANES, ROLL_COLS, 3))
im = ax.imshow(img_data, aspect='auto', origin='lower',
               extent=[0, ROLL_COLS, -0.5, NUM_LANES - 0.5],
               interpolation='nearest', vmin=0, vmax=1)

# Sensor bar line
sensor_line = ax.axvline(x=SENSOR_COL + 0.5, color='white', linewidth=2.5, alpha=0.9, zorder=5)

# Glow effect columns (dim overlay left of sensor = "past")
past_overlay = patches.Rectangle((0, -0.5), SENSOR_COL + 0.5, NUM_LANES,
                                   facecolor='#05050a', alpha=0.55, zorder=4)
ax.add_patch(past_overlay)

# ─── Animation State ──────────────────────────────────────────────────────────

state = {
    'head_col': SENSOR_COL,  # which column is currently under sensor
    'frame': 0,
    'beat': 0,
    'last_beat_frame': 0,
    'fired_notes': '─',
}

def update(frame):
    state['frame'] = frame

    # Advance roll one column every BEAT_FRAMES
    if frame - state['last_beat_frame'] >= BEAT_FRAMES:
        state['last_beat_frame'] = frame
        state['beat'] += 1
        state['head_col'] = (state['head_col'] + 1) % ROLL_COLS

        # Paint a new column ahead of the sensor
        lookahead_col = (state['head_col'] + (ROLL_COLS - SENSOR_COL - 1)) % ROLL_COLS
        events = composer.next_beat()
        roll.paint_column(lookahead_col, events)

        # What's firing right now
        fired_col = state['head_col'] % ROLL_COLS
        state['fired_notes'] = roll.col_notes[fired_col]

    # Build the view
    view = roll.scroll_view(state['head_col'])  # (NUM_LANES, ROLL_COLS, 3)

    # Subtle pixel shimmer on active (right of sensor) cells
    shimmer = 1.0 + 0.04 * np.sin(frame * 0.4 + np.arange(ROLL_COLS) * 0.3)
    view_shim = np.clip(view * shimmer[np.newaxis, :, np.newaxis], 0, 1)

    im.set_data(view_shim)

    # Status bar
    notes_str = '  '.join(f'{n:>2}' for n in state['fired_notes'].split(',')) \
                if state['fired_notes'] != '─' else '─  ─  ─  ─  ─  ─  ─  ─'
    status_text.set_text(f'♩  {notes_str}')

    mood_bars = int(composer.mood * 8)
    mood_text.set_text(f"MOOD {'▓'*mood_bars}{'░'*(8-mood_bars)}")
    beat_text.set_text(f"BEAT {state['beat']:04d}")

    return [im, status_text, mood_text, beat_text]

ani = animation.FuncAnimation(fig, update, frames=TOTAL_FRAMES,
                               interval=1000/FPS, blit=True)

# ─── Save ─────────────────────────────────────────────────────────────────────

out_path = '/Users/queenbee/chromatic-roll/chromatic_roll.mp4'
writer = animation.FFMpegWriter(fps=FPS, bitrate=4000,
                                 extra_args=['-vcodec','libx264','-pix_fmt','yuv420p'])
print(f"Rendering {TOTAL_FRAMES} frames at {FPS}fps → {out_path}")
ani.save(out_path, writer=writer, dpi=120,
         savefig_kwargs={'facecolor': '#05050a'})
print("Done!")
