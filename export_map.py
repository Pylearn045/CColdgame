#!/usr/bin/env python3
"""
Export a map JSON file using the game's procedural generator.
Usage: python export_map.py --width 96 --height 96
Produces: map_<W>x<H>.json in the repository root.
"""
import argparse
import json
import game

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def main():
    p = argparse.ArgumentParser(description='Export map JSON from game.GameMap')
    p.add_argument('--width', type=int, default=96)
    p.add_argument('--height', type=int, default=96)
    p.add_argument('--levels', type=int, default=3, help='Number of discrete height levels (1-5)')
    args = p.parse_args()

    W = clamp(args.width, 16, 128)
    H = clamp(args.height, 16, 128)
    LEVELS = clamp(args.levels, 1, 5)

    # Override module-level map size constants so GameMap generates desired size
    game.MAP_COLS = W
    game.MAP_ROWS = H
    game.MAP_PX_W = W * game.TILE
    game.MAP_PX_H = H * game.TILE

    gm = game.GameMap()

    # Generate a smooth heightmap (values 0.0..1.0) using value noise + smoothing
    import random as _random
    _random.seed()
    height = [[_random.random() for _ in range(W)] for __ in range(H)]

    # Smooth several passes to form hills/valleys
    def smooth(hm, passes=5):
        for _ in range(passes):
            new = [[0.0 for _ in range(W)] for __ in range(H)]
            for y in range(H):
                for x in range(W):
                    s = 0.0
                    c = 0
                    for oy in (-1,0,1):
                        for ox in (-1,0,1):
                            nx, ny = x+ox, y+oy
                            if 0 <= nx < W and 0 <= ny < H:
                                s += hm[ny][nx]
                                c += 1
                    new[y][x] = s / c
            hm = new
        return hm

    height = smooth(height, passes=6)

    # Bias height to avoid deep oceans: reduce heights where original tile is WATER
    for y in range(H):
        for x in range(W):
            if gm.tiles[y][x] == game.WATER:
                height[y][x] = min(height[y][x], 0.25)

    # Normalize to 0..1
    minv = min(min(row) for row in height)
    maxv = max(max(row) for row in height)
    if maxv - minv > 1e-6:
        for y in range(H):
            for x in range(W):
                height[y][x] = (height[y][x] - minv) / (maxv - minv)
    else:
        for y in range(H):
            for x in range(W):
                height[y][x] = 0.0

    # Quantize to discrete levels 0..LEVELS-1
    height_levels = [[min(LEVELS-1, int(h * LEVELS)) for h in row] for row in height]

    # Build binary layer maps: layers[layer_index][row][col] == 1 if that cell==level
    layers = []
    for lev in range(LEVELS):
        layer = [[1 if height_levels[r][c] == lev else 0 for c in range(W)] for r in range(H)]
        layers.append(layer)

    # Prepare export structure. "tiles" is a list of rows (H) each with W ints.
    export = {
        'width': W,
        'height': H,
        'tiles': gm.tiles,
        'levels': LEVELS,
        'height_levels': height_levels,
        'layers': layers,
        'tile_enum': {
            'GRASS': game.GRASS,
            'DIRT': game.DIRT,
            'WATER': game.WATER,
            'TIBERIUM_T': game.TIBERIUM_T
        }
    }

    out_name = f'map_{W}x{H}_L{LEVELS}.json'
    with open(out_name, 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2, ensure_ascii=False)

    print(f'Exported {out_name}')

if __name__ == '__main__':
    main()
