#!/usr/bin/env python3
"""
Generate 32x32 pixel-art terrain tiles and transition masks.
Writes to assets/tiles and assets/transitions (overwrites existing files with same names).
"""
import os, random, pygame
TILE = 32
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')
TILES_DIR = os.path.join(OUT_DIR, 'tiles')
TRANS_DIR = os.path.join(OUT_DIR, 'transitions')
os.makedirs(TILES_DIR, exist_ok=True)
os.makedirs(TRANS_DIR, exist_ok=True)

pygame.init()

def new():
    return pygame.Surface((TILE, TILE), pygame.SRCALPHA)

def save(s, path):
    pygame.image.save(s, path)

# pixel helper
def rect(s,x,y,w,h,color):
    pygame.draw.rect(s, color, (x,y,w,h))

# Plain: simple checker + speckles
def plain():
    s=new()
    c1=(80,140,40)
    c2=(72,132,36)
    for y in range(0,TILE,2):
        for x in range(0,TILE,2):
            rect(s,x,y,2,2, c1 if (x+y)//2%2==0 else c2)
    # speckles
    for _ in range(60):
        x=random.randrange(0,TILE)
        y=random.randrange(0,TILE)
        s.set_at((x,y),(min(255,c1[0]+random.randint(-8,8)),min(255,c1[1]+random.randint(-8,8)),min(255,c1[2]+random.randint(-8,8))))
    return s

# Mountain: blocky peaks
def mountain():
    s=new()
    # base grass
    rect(s,0,0,TILE,TILE,(90,120,70))
    # peaks: stack small triangles approximated by rectangles
    peak=(110,100,90)
    dark=(70,60,55)
    for i in range(4):
        w = TILE//2 - i*4
        x = TILE//4 + i*2
        y = 4 + i*6
        rect(s,x,y,w,4, peak)
        rect(s,x,y+4,w,4,dark)
    # add some rocky speckles
    for _ in range(30):
        x=random.randrange(0,TILE)
        y=random.randrange(0,TILE//2)
        s.set_at((x,y), dark)
    return s

# Forest: pixel trees
def forest(deep=False):
    s=new()
    bg=(70,130,50) if not deep else (46,95,42)
    rect(s,0,0,TILE,TILE,bg)
    trunk=(60,40,20)
    leaf=(34,90,30) if deep else (46,120,40)
    count=14 if not deep else 26
    for _ in range(count):
        x=random.randrange(2,TILE-4)
        y=random.randrange(4,TILE-6)
        # canopy
        for oy in (-1,0,1):
            for ox in (-1,0,1):
                px=x+ox; py=y+oy
                if 0<=px<TILE and 0<=py<TILE:
                    s.set_at((px,py), leaf)
        # trunk
        if y+2<TILE:
            s.set_at((x,y+2), trunk)
            if x+1<TILE: s.set_at((x+1,y+2), trunk)
    return s

# Lake: blocky water with shore
def lake():
    s=new()
    shore=(200,180,140)
    water=(40,80,160)
    light=(70,130,200)
    rect(s,0,0,TILE,TILE,(34,100,60))
    # water blob
    for y in range(6,TILE-6):
        for x in range(6,TILE-6):
            if (x-16)**2 + (y-14)**2 < (10+random.randint(-2,2))**2:
                s.set_at((x,y), water)
    # highlights
    for i in range(6):
        x=random.randrange(8,TILE-8); y=random.randrange(8,TILE-8)
        if s.get_at((x,y))==water:
            s.set_at((x,y), light)
    # shoreline
    for x in range(TILE):
        for y in range(TILE):
            if s.get_at((x,y))==water:
                for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx,ny=x+dx,y+dy
                    if 0<=nx<TILE and 0<=ny<TILE and s.get_at((nx,ny))!=(water):
                        s.set_at((nx,ny), shore)
    return s

# transition masks simple alpha gradients from edge/corner
DIRS=['n','s','e','w','ne','nw','se','sw']

def mask(dir_key):
    s=new()
    for y in range(TILE):
        for x in range(TILE):
            alpha=0
            if dir_key=='n':
                alpha = max(0, 255 - int((y/(TILE-1))*255*1.5))
            elif dir_key=='s':
                alpha = max(0, 255 - int(((TILE-1-y)/(TILE-1))*255*1.5))
            elif dir_key=='e':
                alpha = max(0, 255 - int(((TILE-1-x)/(TILE-1))*255*1.5))
            elif dir_key=='w':
                alpha = max(0, 255 - int((x/(TILE-1))*255*1.5))
            elif dir_key in ('ne','nw','se','sw'):
                cx = 0 if dir_key[1]=='w' else TILE-1
                cy = 0 if dir_key[0]=='n' else TILE-1
                dist = ((x-cx)**2 + (y-cy)**2)**0.5
                maxd = (TILE*0.9)
                alpha = max(0, 255 - int((dist/maxd)*255*1.2))
            # soften
            if random.random()<0.02:
                alpha = int(alpha*random.uniform(0.6,1.0))
            s.set_at((x,y),(255,255,255,alpha))
    return s

# generate
tiles={'plain':plain(),'mountain':mountain(),'forest':forest(False),'deep_forest':forest(True),'lake':lake()}
for name,s in tiles.items():
    p=os.path.join(TILES_DIR,f'{name}.png')
    save(s,p)
    print('Wrote',p)

pairs=[('mountain','plain'),('plain','forest'),('plain','lake'),('forest','lake'),('mountain','forest')]
for a,b in pairs:
    for d in DIRS:
        m=mask(d)
        p=os.path.join(TRANS_DIR,f'{a}_to_{b}_edge_{d}.png')
        save(m,p)
        print('Wrote',p)

print('Pixel tiles generated in', OUT_DIR)
pygame.quit()
