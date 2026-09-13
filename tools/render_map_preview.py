#!/usr/bin/env python3
"""
Render a top-down preview image by composing tile PNGs and transition masks
Produces assets/preview_map.png
"""
import os, json, pygame
ROOT = os.path.dirname(__file__)
ASSETS = os.path.join(ROOT, '..', 'assets')
MAP_JSON = os.path.join(ROOT, '..', 'map_96x96_L4.json')
OUT = os.path.join(ASSETS, 'preview_map.png')
TILE = 32

pygame.init()
# Needed for convert_alpha on some platforms
pygame.display.set_mode((1,1))

def load_img(name):
    p = os.path.join(ASSETS, 'tiles', name + '.png')
    return pygame.image.load(p).convert_alpha()

def load_mask(a,b,dir):
    p = os.path.join(ASSETS, 'transitions', f'{a}_to_{b}_edge_{dir}.png')
    if os.path.exists(p):
        return pygame.image.load(p).convert_alpha()
    return None

plain=load_img('plain')
mount=load_img('mountain')
forest=load_img('forest')
dforest=load_img('deep_forest')
lake=load_img('lake')

with open(MAP_JSON,'r',encoding='utf-8') as f:
    data=json.load(f)

w=data['width']; h=data['height']
height_levels=data.get('height_levels')

surf=pygame.Surface((w*TILE, h*TILE), pygame.SRCALPHA)

for r in range(h):
    for c in range(w):
        t = data['tiles'][r][c]
        # select base
        if t == 2:
            base = lake
        else:
            lvl = height_levels[r][c] if height_levels else 0
            if lvl >= max(1, data.get('levels',1))-1:
                base = mount
            else:
                # simple deterministic forest placement
                hashv = (r*73856093) ^ (c*19349663)
                val = abs(hashv) % 100
                if val < 8: base= dforest
                elif val < 22: base= forest
                else: base = plain
        surf.blit(base, (c*TILE, r*TILE))

        # overlay transitions for 4 neighbors
        nbrs = {'n':(0,-1),'s':(0,1),'e':(1,0),'w':(-1,0)}
        for dir_key,(dx,dy) in nbrs.items():
            nx, ny = c+dx, r+dy
            if nx<0 or nx>=w or ny<0 or ny>=h: continue
            # neighbor base
            nt = data['tiles'][ny][nx]
            if nt==2:
                nb = lake
            else:
                nl = height_levels[ny][nx] if height_levels else 0
                if nl >= max(1,data.get('levels',1))-1: nb=mount
                else:
                    hashv = (ny*73856093) ^ (nx*19349663)
                    val = abs(hashv) % 100
                    if val < 8: nb=dforest
                    elif val <22: nb=forest
                    else: nb=plain
            if nb != base:
                mask = load_mask('mountain' if nb==mount else ('plain' if nb==plain else ('forest' if nb==forest else 'deep_forest')),
                                 'plain' if base==plain else ('mountain' if base==mount else ('forest' if base==forest else 'deep_forest')),
                                 dir_key)
                if mask:
                    # apply masked blit: create copy of nb then multiply alpha by mask
                    temp = nb.copy()
                    # scale masks to TILE if not matching
                    mask_s = pygame.transform.smoothscale(mask,(TILE,TILE))
                    # combine using alpha
                    temp.blit(mask_s, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                    surf.blit(temp, (c*TILE, r*TILE))

pygame.image.save(surf, OUT)
print('Wrote preview to', OUT)
pygame.quit()
