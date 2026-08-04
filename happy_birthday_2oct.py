"""
Happy Birthday — 2-Octave Chromatic Optical Roll + Synthesized Audio
Mark Rubin / Honeylight

16 lanes:  C4-B4 (lower octave, mid brightness)
           C5-B5 (upper octave, full brightness)
           C6    (top)
           ─     (rest / black)

Audio: marimba-style tones synthesized in numpy, muxed into the final MP4.
The tones fire exactly when the note crosses the sensor bar — the visual and
audio are sample-accurate.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import colorsys, wave, subprocess, os

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════
SR        = 44100          # audio sample rate
NUM_LANES = 16
FPS       = 30
BPM       = 90
E8TH      = 60.0/BPM/2    # 0.3333s per 8th-note column
E8TH_F    = max(1,int(round(FPS*E8TH)))   # 10 frames per column
SENSOR    = 18             # sensor bar x position (columns from left)
VIS       = 68             # visible columns on screen
LEAD      = 8              # silence columns before song reaches sensor
BG        = '#03030b'
DIR       = '/Users/queenbee/chromatic-roll'

# ══════════════════════════════════════════════════════════════════════════════
#  NOTES — 16 LANES
# ══════════════════════════════════════════════════════════════════════════════
LNAMES = ['C4','D4','E4','F4','G4','A4','B4',
          'C5','D5','E5','F5','G5','A5','B5',
          'C6','─']

FREQS = {
    'C4':261.63,'D4':293.66,'E4':329.63,'F4':349.23,
    'G4':392.00,'A4':440.00,'B4':493.88,
    'C5':523.25,'D5':587.33,'E5':659.25,'F5':698.46,
    'G5':783.99,'A5':880.00,'B5':987.77,
    'C6':1046.50,
}

N2L = {
    'C4':0,'D4':1,'E4':2,'F4':3,'G4':4,'A4':5,'B4':6,
    'C5':7,'D5':8,'E5':9,'F5':10,'G5':11,'A5':12,'B5':13,
    'C6':14,'_':15,'─':15,
}

HUE = {'C':0.00,'D':0.07,'E':0.14,'F':0.28,'G':0.50,'A':0.63,'B':0.77}

def n2rgb(note, vel=1.0, artic='normal', acc=False):
    """note name → RGB  (hue=pitch, brightness=vel, saturation=articulation)"""
    if note in ('_','─'):
        return np.array([0.02,0.02,0.06])
    nm  = note[0]
    oct = int(note[1])
    h   = HUE[nm]
    # lower octave dimmer base, upper octave brighter
    base_v = {4:0.42, 5:0.78, 6:0.92}.get(oct, 0.78)
    v  = base_v + (1.0-base_v)*vel
    s  = {'legato':0.30,'staccato':1.0}.get(artic, 0.82)
    if oct >= 5: s = min(1.0, s+0.10)
    r,g,b = colorsys.hsv_to_rgb(h,s,v)
    if acc: r,g,b = min(1,r+0.42),min(1,g+0.42),min(1,b+0.42)
    return np.array([r,g,b])

def hex_c(a):
    return '#{:02x}{:02x}{:02x}'.format(int(a[0]*255),int(a[1]*255),int(a[2]*255))

# ══════════════════════════════════════════════════════════════════════════════
#  SCORE — HAPPY BIRTHDAY (2-octave range)
# ══════════════════════════════════════════════════════════════════════════════
# (note, dur_8ths, velocity, articulation, accent, lyric)
SONG = [
    # ── Line 1 : "Happy Birthday to You"
    ('G4',1,0.65,'staccato',False,'Hap-'),
    ('G4',1,0.65,'staccato',False,'py'),
    ('A4',2,0.85,'normal',  False,'Birth-'),
    ('G4',2,0.85,'normal',  False,'day'),
    ('C5',2,0.80,'normal',  False,'to'),
    ('B4',4,1.00,'legato',  False,'You'),
    ('_', 2,0.00,'normal',  False,''),
    # ── Line 2 : "Happy Birthday to You"
    ('G4',1,0.65,'staccato',False,'Hap-'),
    ('G4',1,0.65,'staccato',False,'py'),
    ('A4',2,0.85,'normal',  False,'Birth-'),
    ('G4',2,0.85,'normal',  False,'day'),
    ('D5',2,0.80,'normal',  False,'to'),
    ('C5',4,1.00,'legato',  False,'You'),
    ('_', 2,0.00,'normal',  False,''),
    # ── Line 3 : "Happy Birthday Dear Mark"  — G5 climax accent
    ('G4',1,0.65,'staccato',False,'Hap-'),
    ('G4',1,0.65,'staccato',False,'py'),
    ('G5',2,1.00,'normal',  True, 'Birth-'),   # ← white-flash accent, G5!
    ('E5',2,0.90,'normal',  False,'day'),
    ('C5',2,0.85,'normal',  False,'dear'),
    ('B4',2,0.85,'normal',  False,'Mar-'),
    ('A4',4,1.00,'legato',  False,'k'),
    ('_', 2,0.00,'normal',  False,''),
    # ── Line 4 : "Happy Birthday to You"  (final)
    ('F5',1,0.80,'staccato',False,'Hap-'),
    ('F5',1,0.80,'staccato',False,'py'),
    ('E5',2,0.90,'normal',  False,'Birth-'),
    ('C5',2,0.90,'normal',  False,'day'),
    ('D5',2,0.85,'normal',  False,'to'),
    ('C5',6,1.00,'legato',  False,'You!'),
    ('_', 6,0.00,'normal',  False,''),
]

# ══════════════════════════════════════════════════════════════════════════════
#  AUDIO — marimba-style synthesis
# ══════════════════════════════════════════════════════════════════════════════
def make_tone(freq, dur_s, vel, decay=5.2):
    """Fundamental + inharmonic 4th overtone + octave, exponential decay."""
    n   = int(SR*dur_s)
    t   = np.linspace(0, dur_s, n, endpoint=False)
    env = np.exp(-t*decay)
    atk = min(int(0.003*SR), n)
    env[:atk] *= np.linspace(0,1,atk)        # 3 ms attack ramp
    return (np.sin(2*np.pi*freq*t)       * 0.60 +
            np.sin(2*np.pi*freq*3.97*t)  * 0.27 +   # inharmonic overtone
            np.sin(2*np.pi*freq*2.0*t)   * 0.13
           ) * env * vel * 0.78

def build_audio(total_frames):
    total_s   = total_frames/FPS + 3.0
    total_smp = int(total_s * SR)
    buf  = np.zeros(total_smp)
    pos  = LEAD                              # column position in score
    for note,dur,vel,artic,_acc,_ in SONG:
        if note != '_':
            t0   = int(pos * E8TH * SR)    # sample when note hits sensor
            tdur = dur * E8TH * 0.90
            if artic == 'staccato': tdur *= 0.38
            tone = make_tone(FREQS[note], min(tdur,2.0), vel)
            end  = min(t0+len(tone), total_smp)
            buf[t0:end] += tone[:end-t0]
        pos += dur
    mx = np.max(np.abs(buf))
    if mx > 0: buf = buf/mx * 0.82
    return buf

def save_wav(path, buf):
    i16 = np.clip(buf*32767,-32768,32767).astype(np.int16)
    with wave.open(path,'w') as f:
        f.setnchannels(1); f.setsampwidth(2)
        f.setframerate(SR); f.writeframes(i16.tobytes())

# ══════════════════════════════════════════════════════════════════════════════
#  COLUMNS — one per 8th note
# ══════════════════════════════════════════════════════════════════════════════
def sil():
    return {'colors':np.full((NUM_LANES,3),0.02),
            'note':'─','lyric':'','vel':0,'artic':'normal','lane':-1,'accent':False}

def build_cols():
    cols = [sil() for _ in range(LEAD)]
    for note,dur,vel,artic,acc,lyr in SONG:
        g  = np.full((NUM_LANES,3),0.02)
        ln = -1
        if note != '_':
            ln = N2L[note]
            g[ln] = n2rgb(note, vel, artic, acc)
        for i in range(dur):
            cols.append({'colors':g.copy(),
                         'note':note if note!='_' else '─',
                         'lyric':lyr if i==0 else '',
                         'vel':vel,'artic':artic,'lane':ln,'accent':acc})
    for _ in range(SENSOR+14): cols.append(sil())
    return cols

COLS   = build_cols()
NCOLS  = len(COLS)
NFRAMS = int(NCOLS*E8TH_F + FPS*2)

# ══════════════════════════════════════════════════════════════════════════════
#  FIGURE
# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16,9), facecolor=BG)

# ── Roll panel ────────────────────────────────────────────────────────────────
ax_r = fig.add_axes([0.07,0.36,0.89,0.55])
ax_r.set_facecolor(BG)
ax_r.set_xlim(0,VIS); ax_r.set_ylim(-0.5,NUM_LANES-0.5)
ax_r.set_yticks(range(NUM_LANES))
ax_r.set_yticklabels([f' {n}' for n in LNAMES],
                      color='#555577', fontsize=8.5, fontfamily='monospace')
ax_r.set_xticks([]); ax_r.spines[:].set_visible(False); ax_r.tick_params(left=False)

# Lane grid lines — thick bright divider between OCT4 and OCT5
for i in range(NUM_LANES-1):
    lw  = 1.8 if i==6  else (1.0 if i==13 else 0.4)
    col = '#303068' if i==6 else ('#202044' if i==13 else '#0b0b1c')
    ax_r.axhline(i+0.5, color=col, lw=lw, zorder=3)

# Octave bracket labels (right side of roll)
ax_r.text(VIS+0.8,  3.0, 'OCT 4', va='center', color='#2a2a55',
           fontsize=8, fontfamily='monospace', fontweight='bold')
ax_r.text(VIS+0.8, 10.0, 'OCT 5', va='center', color='#3a3a88',
           fontsize=8, fontfamily='monospace', fontweight='bold')

# Titles
fig.text(0.5,0.975,'CHROMATIC OPTICAL ROLL  -  HAPPY BIRTHDAY  -  16 LANES / 2 OCTAVES',
         ha='center',color='#cccccc',fontsize=13,fontfamily='monospace',fontweight='bold')
fig.text(0.5,0.950,
         'COLOR = PITCH   |   BRIGHTNESS = VELOCITY   |   SATURATION = ARTICULATION   |   LENGTH = DURATION   |   AUDIO LIVE',
         ha='center',color='#2a2a44',fontsize=8,fontfamily='monospace')

# ── Color legend (2 rows: OCT4 bottom, OCT5 top) ─────────────────────────────
ax_lg = fig.add_axes([0.07,0.918,0.89,0.028])
ax_lg.axis('off'); ax_lg.set_xlim(0,1); ax_lg.set_ylim(0,2)
note14 = ['C4','D4','E4','F4','G4','A4','B4','C5','D5','E5','F5','G5','A5','B5']
for i,n in enumerate(note14):
    c   = n2rgb(n, 0.92, 'staccato')
    row = 0 if i<7 else 1          # OCT4=bottom, OCT5=top
    xi  = (i%7)/7
    ax_lg.add_patch(patches.Rectangle((xi,row),1/7,0.96,facecolor=tuple(c),edgecolor='none'))
    fcol = '#444466' if i<7 else '#6666aa'
    ax_lg.text(xi+1/14, row-0.35, n, ha='center', color=fcol,
               fontsize=6.5, fontfamily='monospace')
ax_lg.text(1.005, 0.48, 'OCT4', ha='left', va='center',
           color='#333355', fontsize=6, fontfamily='monospace')
ax_lg.text(1.005, 1.48, 'OCT5', ha='left', va='center',
           color='#444488', fontsize=6, fontfamily='monospace')

# ── Roll image ────────────────────────────────────────────────────────────────
im = ax_r.imshow(np.full((NUM_LANES,VIS,3),0.02),
                  aspect='auto',origin='lower',
                  extent=[0,VIS,-0.5,NUM_LANES-0.5],
                  interpolation='nearest',vmin=0,vmax=1)

# Sensor bar (the "read head")
ax_r.axvline(SENSOR+0.5, color='white', lw=2.6, alpha=0.90, zorder=5)
ax_r.text(SENSOR+0.5, NUM_LANES-0.05, 'READ',
           ha='center', color='#ffffff', fontsize=7, fontfamily='monospace', zorder=6)

# Past overlay — dims already-played columns
ax_r.add_patch(patches.Rectangle((0,-0.5),SENSOR+0.5,NUM_LANES,
                                   facecolor=BG,alpha=0.52,zorder=4))

# ── Sensor readout strip ──────────────────────────────────────────────────────
ax_s = fig.add_axes([0.07,0.245,0.89,0.105])
ax_s.set_facecolor('#070714')
ax_s.set_xlim(0,1); ax_s.set_ylim(0,1); ax_s.axis('off')
ax_s.text(0.0,1.07,'SENSOR READING',color='#222244',
           fontsize=7,fontfamily='monospace',va='bottom')

sw    = patches.Rectangle((0.008,0.10),0.055,0.78,
                            facecolor='#111133',edgecolor='#222244',lw=1.2,zorder=2)
ax_s.add_patch(sw)
ntxt  = ax_s.text(0.085,0.50,'─',va='center',ha='left',
                   color='#333355',fontsize=26,fontfamily='monospace',fontweight='bold')
ltxt  = ax_s.text(0.22, 0.50,'',va='center',ha='left',
                   color='#888899',fontsize=20,fontfamily='monospace',fontstyle='italic')
vtxt  = ax_s.text(0.72, 0.72,'vel: ─',va='center',
                   color='#333355',fontsize=8,fontfamily='monospace')
atxt  = ax_s.text(0.72, 0.28,'artic: ─',va='center',
                   color='#333355',fontsize=8,fontfamily='monospace')
lantx = ax_s.text(0.90, 0.50,'LANE ─',va='center',
                   color='#333355',fontsize=8,fontfamily='monospace')

# Beat flash bar (thin strip below sensor readout)
ax_bf = fig.add_axes([0.07,0.237,0.89,0.006])
ax_bf.set_facecolor(BG); ax_bf.axis('off')
ax_bf.set_xlim(0,1); ax_bf.set_ylim(0,1)
beat_bar = patches.Rectangle((0,0),1,1,facecolor='#111133',edgecolor='none')
ax_bf.add_patch(beat_bar)

# ── Mechanical signal chain ───────────────────────────────────────────────────
ax_c = fig.add_axes([0.02,0.01,0.96,0.215])
ax_c.set_facecolor(BG); ax_c.set_xlim(0,1); ax_c.set_ylim(0,1); ax_c.axis('off')
fig.text(0.5,0.235,'--- MECHANICAL SIGNAL CHAIN ---',
         ha='center',color='#1a1a33',fontsize=8,fontfamily='monospace')

CHAIN = [
    (0.02, 'LED', 'LED\nMATRIX',    'AI paints\ncolor roll'),
    (0.19, 'RGB', 'COLOR\nSENSOR',  '16x TCS34725\nRGB readers'),
    (0.36, 'Pi',  'RASPBERRY\nPI',  'Decodes color\nto note+vel'),
    (0.53, '[>]', 'SERVO\nGATE',    'Opens for\nball release'),
    (0.70, '(o)', 'GOLF\nBALL',     'Rolls down\nangled ramp'),
    (0.87, '[|]', 'TONE\nBAR',      'Struck rings\nat pitch'),
]
BW=0.105; BH=0.68
mrects=[]; mlbls=[]; mdescs=[]; msyms=[]

for i,(x,sym,lbl,desc) in enumerate(CHAIN):
    r = patches.FancyBboxPatch((x,0.15),BW,BH,
                                boxstyle='round,pad=0.02',
                                facecolor='#080818',edgecolor='#181830',
                                lw=1.5,zorder=2)
    ax_c.add_patch(r); mrects.append(r)
    s = ax_c.text(x+BW/2, 0.72, sym, ha='center', va='center',
                   color='#333355', fontsize=12, fontfamily='monospace',
                   fontweight='bold', zorder=3)
    msyms.append(s)
    l = ax_c.text(x+BW/2, 0.50, lbl, ha='center', va='center',
                   color='#333355', fontsize=8, fontfamily='monospace',
                   fontweight='bold', multialignment='center', zorder=3)
    mlbls.append(l)
    d = ax_c.text(x+BW/2, 0.26, desc, ha='center', va='center',
                   color='#202038', fontsize=6.5, fontfamily='monospace',
                   multialignment='center', zorder=3)
    mdescs.append(d)
    if i < len(CHAIN)-1:
        ax_c.annotate('',xy=(x+BW+0.05,0.52),xytext=(x+BW+0.005,0.52),
                       arrowprops=dict(arrowstyle='->',color='#181830',lw=1.8),zorder=1)

# ══════════════════════════════════════════════════════════════════════════════
#  ANIMATION
# ══════════════════════════════════════════════════════════════════════════════
sticky = ['']
prev_lane = [-1]

def update(frame):
    ci   = min(frame//E8TH_F, NCOLS-1)
    beat = frame % E8TH_F                 # position within current beat

    # ── Build visible roll buffer ──────────────────────────────────────────
    view = np.full((NUM_LANES,VIS,3),0.02)
    for vc in range(VIS):
        src = ci - SENSOR + vc
        if 0 <= src < NCOLS:
            view[:,vc,:] = COLS[src]['colors']

    # Subtle shimmer on future columns
    sh   = 1.0 + 0.04*np.sin(frame*0.38 + np.arange(VIS)*0.32)
    view = np.clip(view * sh[np.newaxis,:,np.newaxis], 0, 1)
    im.set_data(view)

    # ── Beat-flash bar (flashes white at start of each note, fades) ────────
    bf_alpha = max(0.0, 1.0 - beat / (E8TH_F * 0.5))

    cur   = COLS[ci]
    note  = cur['note']
    lyr   = cur['lyric']
    if lyr: sticky[0] = lyr
    vel   = cur['vel']
    artic = cur['artic']
    lane  = cur['lane']

    if note != '─' and lane >= 0:
        c   = COLS[ci]['colors'][lane]
        hx  = hex_c(c)
        dc  = tuple(np.clip(c*0.16, 0, 1))

        # Beat flash in note's color
        fc = tuple(np.clip(c*bf_alpha*0.8, 0, 1))
        beat_bar.set_facecolor(fc)

        # Sensor readout
        sw.set_facecolor(tuple(c)); sw.set_edgecolor(hx)
        ntxt.set_text(note);           ntxt.set_color(hx)
        ltxt.set_text(sticky[0]);      ltxt.set_color('#ddddee')
        vtxt.set_text(f'vel: {vel:.2f}'); vtxt.set_color('#7777aa')
        atxt.set_text(f'artic: {artic}');  atxt.set_color('#7777aa')
        lantx.set_text(f'LANE {lane+1}'); lantx.set_color(hx)

        # Chain — all 6 light up; gate/ball/bar glow brightest
        for j,(r,l,d,s) in enumerate(zip(mrects,mlbls,mdescs,msyms)):
            r.set_edgecolor(hx); r.set_linewidth(2.4)
            r.set_facecolor(dc if j >= 3 else '#0e0e26')
            l.set_color('#ccccee'); d.set_color('#5566bb'); s.set_color(hx)
    else:
        beat_bar.set_facecolor('#030308')
        sw.set_facecolor('#0d0d22'); sw.set_edgecolor('#1a1a33')
        ntxt.set_text('─');         ntxt.set_color('#333355')
        ltxt.set_text('')
        vtxt.set_text('vel: ─');    vtxt.set_color('#333355')
        atxt.set_text('artic: ─');  atxt.set_color('#333355')
        lantx.set_text('LANE ─');   lantx.set_color('#333355')
        for r,l,d,s in zip(mrects,mlbls,mdescs,msyms):
            r.set_facecolor('#080818'); r.set_edgecolor('#181830'); r.set_linewidth(1.5)
            l.set_color('#333355'); d.set_color('#202038'); s.set_color('#333355')

ani = animation.FuncAnimation(fig, update, frames=NFRAMS,
                               interval=1000/FPS, blit=False)

# ══════════════════════════════════════════════════════════════════════════════
#  RENDER — audio first, then video, then mux
# ══════════════════════════════════════════════════════════════════════════════
vid = os.path.join(DIR, 'hb2_noaudio.mp4')
wav_path = os.path.join(DIR, 'hb2_audio.wav')
out = os.path.join(DIR, 'happy_birthday_2oct.mp4')

print(f"Synthesizing audio ({NFRAMS/FPS:.1f}s at {SR}Hz)...")
audio = build_audio(NFRAMS)
save_wav(wav_path, audio)
print(f"  WAV: {wav_path}")

writer = animation.FFMpegWriter(fps=FPS, bitrate=6000,
                                 extra_args=['-vcodec','libx264','-pix_fmt','yuv420p'])
print(f"Rendering {NFRAMS} frames ({NFRAMS/FPS:.1f}s) at {FPS}fps → {vid}")
ani.save(vid, writer=writer, dpi=110, savefig_kwargs={'facecolor':BG})
print(f"  Video: {vid}")

print("Muxing audio + video...")
res = subprocess.run(
    ['ffmpeg','-y','-i',vid,'-i',wav_path,
     '-c:v','copy','-c:a','aac','-b:a','192k','-shortest', out],
    capture_output=True, text=True)
if res.returncode == 0:
    print(f"  Final: {out}")
else:
    print("FFmpeg error:", res.stderr[-400:])
