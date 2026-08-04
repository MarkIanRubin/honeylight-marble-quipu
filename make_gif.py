#!/Users/queenbee/chromatic-roll/venv/bin/python3
"""Render honeylight_demo.gif for GitHub README."""
import os, math
import numpy as np
import pygame
pygame.display.init()
pygame.font.init()

SW, SH = 1200, 680
surf = pygame.Surface((SW, SH))

RAMP_W=130; HEADER_H=58; FOOTER_H=90
LANE_AREA_X=RAMP_W; LANE_AREA_Y=HEADER_H
LANE_AREA_W=SW-2*RAMP_W; LANE_AREA_H=SH-HEADER_H-FOOTER_H
NUM_LANES=16; LANE_W=LANE_AREA_W//NUM_LANES; BALL_R=max(8,LANE_W//3-2)
HAMMER_Y=LANE_AREA_Y+LANE_AREA_H-14
RAMP_Y_TOP=LANE_AREA_Y+8; RAMP_Y_BOT=HAMMER_Y; RAMP_HEIGHT=RAMP_Y_BOT-RAMP_Y_TOP
HELIX_AMP=44; HELIX_TURNS=7; HELIX_SEGS=120
LIFT_CX=RAMP_W//2; OVFL_CX=SW-RAMP_W//2
BALL_START_Y=LANE_AREA_Y+BALL_R+3; BALL_HIT_Y=HAMMER_Y-BALL_R
FALL_DIST_PX=BALL_HIT_Y-BALL_START_Y; FALL_TIME_S=0.65
G_PX=2.0*FALL_DIST_PX/(FALL_TIME_S**2)
FALL_MS=int(FALL_TIME_S*1000)

NOTE_DATA=[
    ('D3',(195,45,45)),('E3',(210,90,20)),('F3',(220,140,20)),('G3',(130,175,60)),
    ('A3',(55,160,80)),('Bb3',(35,165,155)),('C4',(35,130,210)),('D4',(40,105,210)),
    ('E4',(80,70,205)),('F4',(120,55,195)),('G4',(150,55,180)),('A4',(170,55,150)),
    ('Bb4',(160,175,190)),('C5',(195,200,215)),('D5',(215,90,130)),('E5',(240,135,135)),
]
NAMES=[n[0] for n in NOTE_DATA]; COLORS=[n[1] for n in NOTE_DATA]
def lane_cx(l): return LANE_AREA_X+l*LANE_W+LANE_W//2

QN=500; HN=1000
C4,D4,E4,F4,G4=6,7,8,9,10; D3,G3,A3=0,3,4
EVENTS=sorted([
    (E4,0),(E4,QN),(F4,2*QN),(G4,3*QN),(G4,4*QN),(F4,5*QN),(E4,6*QN),(D4,7*QN),
    (C4,8*QN),(C4,9*QN),(D4,10*QN),(E4,11*QN),(E4,12*QN),(D4,13*QN+QN//2),
    (D3,0),(A3,HN),(G3,2*HN),(A3,3*HN),(D3,4*HN),(G3,5*HN),(A3,6*HN),(D3,7*HN),
],key=lambda e:e[1])

FONT_T=pygame.font.SysFont('monospace',13,bold=True)
FONT_S=pygame.font.SysFont('monospace',10)
FONT_XS=pygame.font.SysFont('monospace',9)

FPS=18; DURATION_S=5.0; NFRAMES=int(FPS*DURATION_S); dt=1.0/FPS
frames=[]
song_ms=float(-FALL_MS); song_idx=0
last_drop=[-99999.0]*NUM_LANES; MIN_GAP=300
balls=[]
lift_balls=[[i/6.0,i%2,i*2%NUM_LANES] for i in range(6)]
ovfl_balls=[[1-i/6.0,i%2,(i*3+1)%NUM_LANES] for i in range(4)]
phase=0.0
lane_glow=[0.0]*NUM_LANES
hammer_glow=[0.0]*NUM_LANES
hammer_plunge=[0.0]*NUM_LANES

def draw_helix(cx, going_up, blst):
    CA=(70,150,255); CB=(255,165,50); CAD=(18,38,65); CBD=(65,42,13)
    for hx_id in range(2):
        cf=CA if hx_id==0 else CB; cb2=CAD if hx_id==0 else CBD
        pts=[]
        for si in range(HELIX_SEGS+1):
            p=si/HELIX_SEGS
            ang=p*HELIX_TURNS*2*math.pi+(phase if going_up else -phase)
            if hx_id==1:
                ang=-(p*HELIX_TURNS*2*math.pi+(phase if going_up else -phase))+math.pi
            x=cx+HELIX_AMP*math.sin(ang); y=RAMP_Y_BOT-p*RAMP_HEIGHT; z=math.cos(ang)
            pts.append((x,y,z))
        for fp in (False,True):
            col=cf if fp else cb2; ww=3 if fp else 1
            px0,py0,pz0=pts[0]
            for si in range(1,len(pts)):
                px1,py1,pz1=pts[si]
                if ((pz0+pz1)/2>0)==fp:
                    pygame.draw.line(surf,col,(int(px0),int(py0)),(int(px1),int(py1)),ww)
                px0,py0,pz0=px1,py1,pz1
    for prog,hx,ln in blst:
        ang=prog*HELIX_TURNS*2*math.pi+(phase if going_up else -phase)
        if hx==1:
            ang=-(prog*HELIX_TURNS*2*math.pi+(phase if going_up else -phase))+math.pi
        bx=cx+HELIX_AMP*math.sin(ang); by_=RAMP_Y_BOT-prog*RAMP_HEIGHT; z_=math.cos(ang)
        if z_<-0.4: continue
        br=max(6,int(BALL_R*0.65+z_*4)); rc,gc_,bc=COLORS[ln]
        pygame.draw.circle(surf,(0,0,0),(int(bx)+1,int(by_)+1),br)
        pygame.draw.circle(surf,(rc,gc_,bc),(int(bx),int(by_)),br)
        pygame.draw.circle(surf,(255,255,255),(int(bx)-br//3,int(by_)-br//3),max(2,br//3))
    my=RAMP_Y_BOT+28
    pygame.draw.circle(surf,(32,42,56),(cx,my),18)
    pygame.draw.circle(surf,(52,66,84),(cx,my),18,2)
    dx2=int(14*math.cos(phase)); dy2=int(14*math.sin(phase))
    pygame.draw.line(surf,(90,170,255),(cx,my),(cx+dx2,my+dy2),3)
    pygame.draw.circle(surf,(70,140,220),(cx,my),4)
    lbl=FONT_XS.render("LIFT" if going_up else "OVERFLOW",True,(80,110,150))
    surf.blit(lbl,(cx-lbl.get_width()//2,my+24))

for frame_i in range(NFRAMES):
    song_ms+=dt*1000; phase+=45*2*math.pi/60*dt
    while song_idx<len(EVENTS):
        lane,st=EVENTS[song_idx]
        if song_ms>=st-FALL_MS and song_ms-last_drop[lane]>=MIN_GAP:
            balls.append([lane,float(lane_cx(lane)),float(BALL_START_Y),0.0])
            last_drop[lane]=song_ms; song_idx+=1
        else: break
    survivors=[]
    for b in balls:
        b[3]+=G_PX*dt; b[2]+=b[3]*dt
        if b[2]>=BALL_HIT_Y:
            lane_glow[b[0]]=1.0; hammer_glow[b[0]]=1.0; hammer_plunge[b[0]]=1.0
            lift_balls.append([0.0,frame_i%2,b[0]])
        else: survivors.append(b)
    balls=survivors
    for i in range(NUM_LANES):
        lane_glow[i]=max(0,lane_glow[i]-dt*1.8)
        hammer_glow[i]=max(0,hammer_glow[i]-dt*2.2)
        hammer_plunge[i]=max(0,hammer_plunge[i]-dt*9)
    speed=45/60/HELIX_TURNS*dt
    lift_balls=[[p+speed,hx,ln] for p,hx,ln in lift_balls if p+speed<1.01]
    ovfl_balls=[[p-speed,hx,ln] for p,hx,ln in ovfl_balls if p-speed>-0.01]
    if frame_i%20==0: ovfl_balls.append([1.0,frame_i%2,frame_i%NUM_LANES])

    surf.fill((5,7,11))
    ht=FONT_T.render(
        "  HONEYLIGHT MARBLE QUIPU  ·  Rubin Lifting Ramp  ·  16 lanes  ·  0.25 HP  ·  D natural minor",
        True,(140,158,190))
    surf.blit(ht,(4,6))
    pct=min(1,max(0,song_ms)/(7*HN+500))
    pygame.draw.rect(surf,(16,22,32),(LANE_AREA_X,44,LANE_AREA_W,3),border_radius=2)
    pygame.draw.rect(surf,(50,125,195),(LANE_AREA_X,44,int(LANE_AREA_W*pct),3),border_radius=2)

    for i in range(NUM_LANES):
        cx=lane_cx(i); cy=LANE_AREA_Y-20
        dim=tuple(max(10,int(c*0.09)) for c in COLORS[i])
        pygame.draw.circle(surf,dim,(cx,cy),7)
        if lane_glow[i]>0.02:
            gc=tuple(min(255,int(c*lane_glow[i])) for c in COLORS[i])
            pygame.draw.circle(surf,gc,(cx,cy),7)
            if lane_glow[i]>0.35:
                pygame.draw.circle(surf,tuple(c//4 for c in gc),(cx,cy),12,2)
        pygame.draw.circle(surf,(16,20,28),(cx,cy),7,1)
        nl=FONT_XS.render(NAMES[i],True,(50,62,82))
        surf.blit(nl,(cx-nl.get_width()//2,cy-4))

    pygame.draw.rect(surf,(28,36,48),(LANE_AREA_X,LANE_AREA_Y,LANE_AREA_W,LANE_AREA_H),2,border_radius=2)
    for i in range(NUM_LANES):
        lx=LANE_AREA_X+i*LANE_W
        if i>0: pygame.draw.line(surf,(16,21,30),(lx,LANE_AREA_Y),(lx,HAMMER_Y-16))
        if lane_glow[i]>0.04:
            r,g,b=COLORS[i]; s=pygame.Surface((LANE_W-1,LANE_AREA_H-20),pygame.SRCALPHA)
            s.fill((r,g,b,int(lane_glow[i]*14))); surf.blit(s,(lx+1,LANE_AREA_Y))

    draw_helix(LIFT_CX,True,lift_balls)
    draw_helix(OVFL_CX,False,ovfl_balls)

    ty=HAMMER_Y+22
    pygame.draw.rect(surf,(20,28,40),(LANE_AREA_X-6,ty,LANE_AREA_W+12,8),border_radius=3)
    pygame.draw.line(surf,(30,48,70),(LANE_AREA_X,ty+4),(LIFT_CX+HELIX_AMP,ty+4),2)
    pygame.draw.line(surf,(25,35,50),(LANE_AREA_X+LANE_AREA_W,ty+4),(OVFL_CX-HELIX_AMP,ty+4),2)

    for b in balls:
        lane=b[0]; ix=int(b[1]); iy=int(b[2]); r,g,bb_=COLORS[lane]
        pygame.draw.circle(surf,(0,0,0),(ix+2,iy+2),BALL_R)
        pygame.draw.circle(surf,(r,g,bb_),(ix,iy),BALL_R)
        pygame.draw.circle(surf,(255,255,255),(ix-BALL_R//3,iy-BALL_R//3),BALL_R//4)
        pygame.draw.circle(surf,(12,12,15),(ix,iy),BALL_R,1)

    for i in range(NUM_LANES):
        cx=lane_cx(i); cy=HAMMER_Y; col=COLORS[i]; bw,bh=LANE_W-6,14
        if hammer_glow[i]>0.02:
            gc=tuple(min(255,int(c*hammer_glow[i]+15)) for c in col)
            pad=int(8*hammer_glow[i])
            pygame.draw.rect(surf,gc,(cx-bw//2-pad,cy-bh//2-pad,bw+2*pad,bh+2*pad),border_radius=5)
        pygame.draw.rect(surf,(42,48,58),(cx-bw//2,cy-bh//2,bw,bh),border_radius=3)
        pe=int(hammer_plunge[i]*10)
        pc=col if hammer_glow[i]>0.08 else (88,98,112)
        pygame.draw.rect(surf,pc,(cx-3,cy-bh//2-7+pe,5,9),border_radius=2)

    raw=pygame.surfarray.array3d(surf)
    frames.append(raw.transpose(1,0,2).copy())
    print(f"  frame {frame_i+1}/{NFRAMES}", end='\r', flush=True)

pygame.quit()
print(f"\nRendered {NFRAMES} frames. Encoding GIF...")

from PIL import Image as PILImage
pil_frames=[PILImage.fromarray(f).quantize(colors=128) for f in frames]
out='/Users/queenbee/chromatic-roll/honeylight_demo.gif'
pil_frames[0].save(out,save_all=True,append_images=pil_frames[1:],
    optimize=True,duration=int(1000/FPS),loop=0)
sz=os.path.getsize(out)/1024/1024
print(f"DONE  →  {out}  ({sz:.1f} MB,  {NFRAMES} frames @ {FPS}fps)")
