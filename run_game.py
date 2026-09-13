#!/usr/bin/env python3
"""
Run game.py with custom map size by setting module-level constants before creating Game.
Usage: python run_game.py --width 96 --height 96
"""
import argparse
import game

p = argparse.ArgumentParser()
p.add_argument('--width', type=int, default=96)
p.add_argument('--height', type=int, default=96)
args = p.parse_args()

W = max(16, min(128, args.width))
H = max(16, min(128, args.height))

# Override constants
game.MAP_COLS = W
game.MAP_ROWS = H
game.MAP_PX_W = W * game.TILE
game.MAP_PX_H = H * game.TILE

# Initialize pygame and run
import pygame
pygame.init()
print(f"Starting game with map {W}x{H}")
g = game.Game()
g.run()
