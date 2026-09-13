#!/usr/bin/env python3
"""
Generate procedural terrain tiles and transition masks using pygame (no extra deps).
Creates assets/tiles and assets/transitions with 64x64 PNGs.
"""
import os
import math
import random
import pygame

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')
TILE = 64
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'tiles'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'transitions'), exist_ok=True)

pygame.init()

def save(surf, path):
    pygame.image.save(surf, path)

# Helpers
def new_surf():
    return pygame.Surface((TILE, TILE), pygame.SRCALPHA)

def draw_plain():
    s = new_surf()
    grass = (80,140,40)
    grass_a = (72,132,36)
    s.fill(grass)
    for y in range(0, TILE, 4):
        color = grass if (y//4)%2==0 else grass_a
        pygame.draw.line(s, color, (0,y), (TILE,y), 1)
    # subtle noise
    for _ in range(300):
        x = random.randint(0,TILE-1)
        y = random.randint(0,TILE-1)
        col = (random.randint(-8,8)+grass[0], random.randint(-8,8)+grass[1], random.randint(-8,8)+grass[2])
        col = tuple(max(0,min(255,c)) for c in col)
        s.set_at((x,y), col)
    return s

def draw_mountain():
    s = new_surf()
    base = (120,110,100)
    rock = (90,80,70)
    dark = (60,55,50)
    s.fill((0,0,0,0))
    # background grassy base
    pygame.draw.rect(s, (90,120,70), (0,0,TILE,TILE))
    # draw layered triangles for rocky peaks
    for i in range(4):
        points = [
            (random.randint(-10,10), TILE - i*8),
            (TILE//2 + random.randint(-12,12), 6 + i*6),
            (TILE + random.randint(-10,10), TILE - i*8)
        ]
        color = tuple(max(0,min(255, c - i*10)) for c in rock)
        pygame.draw.polygon(s, color, points)
    # add shading and ridges
    for i in range(6):
        x1 = random.randint(0,TILE-1)
        pygame.draw.line(s, dark, (x1, TILE//4), (x1+random.randint(-8,8), TILE-1), 1)
    return s

def draw_forest(deep=False):
    s = new_surf()
    base = (46, 95, 42) if deep else (70,130,50)
    s.fill(base)
    # draw many tree canopies
    for i in range(30 if deep else 18):
        x = random.randint(4, TILE-4)
        y = random.randint(6, TILE-6)
        r = random.randint(6, 12) if deep else random.randint(5,10)
        col = (max(0, base[0]-random.randint(0,20)), min(255, base[1]+random.randint(0,40)), max(0, base[2]-random.randint(0,20)))
        pygame.draw.circle(s, col, (x,y), r)
        # trunk
        pygame.draw.line(s, (60,40,20), (x, y+r), (x, y+r+6), 2)
    # darken bottom a bit
    overlay = pygame.Surface((TILE,TILE), pygame.SRCALPHA)
    overlay.fill((0,0,0,30))
    s.blit(overlay, (0,0))
    return s

def draw_lake():
    s = new_surf()
    water = (40,80,160)
    water_l = (60,110,200)
    s.fill((34,100,60))
    # fill center with water ellipse
    pygame.draw.ellipse(s, water, (6,6,TILE-12,TILE-20))
    # highlights
    for i in range(6):
        pygame.draw.arc(s, water_l, (6,6,TILE-12,TILE-20), random.random()*0.5, random.random()*2.5, 2)
    # shoreline texture
    for x in range(0, TILE, 3):
        y = int((math.sin(x/5.0)*2.0) + (TILE*0.7))
        pygame.draw.circle(s, (200,180,140), (x, y), 1)
    return s

# transition masks: simple alpha gradients that can be used to blend
DIRS = {'n':(0,-1),'s':(0,1),'e':(1,0),'w':(-1,0),'ne':(1,-1),'nw':(-1,-1),'se':(1,1),'sw':(-1,1)}

def make_edge_mask(dir_key):
    s = new_surf()
    s.fill((0,0,0,0))
    dx, dy = DIRS[dir_key]
    for y in range(TILE):
        for x in range(TILE):
            # distance from edge in direction
            if dx != 0 and dy == 0:
                dist = (0.5 - x/TILE) * (-dx)
            elif dy != 0 and dx == 0:
                dist = (0.5 - y/TILE) * (-dy)
            else:
                cx = 0 if dx<0 else 1
                cy = 0 if dy<0 else 1
                dist = math.hypot((x/TILE - cx), (y/TILE - cy))
            alpha = int(max(0, min(255, 255 * (1.0 - dist*2.0))))
            if random.random() < 0.02:
                alpha = int(alpha * random.uniform(0.6,1.0))
            s.set_at((x,y), (255,255,255,alpha))
    return s

# Generate base tiles
tiles = {
    'plain': draw_plain(),
    'mountain': draw_mountain(),
    'forest': draw_forest(deep=False),
    'deep_forest': draw_forest(deep=True),
    'lake': draw_lake(),
}

for name,surf in tiles.items():
    p = os.path.join(OUT_DIR,'tiles', f'{name}.png')
    save(surf, p)
    print('Wrote', p)

# Generate transition masks for pairs
pairs = [
    ('mountain','plain'), ('plain','forest'), ('plain','lake'), ('forest','lake'), ('mountain','forest')
]

for a,b in pairs:
    for d in DIRS.keys():
        mask = make_edge_mask(d)
        path = os.path.join(OUT_DIR,'transitions', f'{a}_to_{b}_edge_{d}.png')
        save(mask, path)
        print('Wrote', path)

print('Tile generation complete. Files in', OUT_DIR)
pygame.quit()
