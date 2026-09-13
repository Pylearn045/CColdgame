import pygame, math, random, heapq, sys, wave, struct, os, tempfile

# ============================================================
# CONSTANTS
# ============================================================
SCREEN_W, SCREEN_H = 1024, 768
SIDEBAR_W = 192
GAME_W = SCREEN_W - SIDEBAR_W
TILE = 32
MAP_COLS, MAP_ROWS = 48, 48
MAP_PX_W = MAP_COLS * TILE
MAP_PX_H = MAP_ROWS * TILE
GRASS, DIRT, WATER, TIBERIUM_T = 0, 1, 2, 3
GDI, NOD = 0, 1
B_CYARD, B_POWER, B_BARRACKS, B_REFINERY, B_WARFACTORY, B_TURRET = range(6)
U_MINIGUN, U_ROCKET, U_TANK, U_HARV = range(4)
GS_PLAYING = 0
GS_GAME_OVER = 1
FPS = 60

BUILD_DATA = {
    B_CYARD: ("Construction Yard", 1000, 3, 3, 0, 800),
    B_POWER: ("Power Plant", 200, 2, 2, 100, 300),
    B_BARRACKS: ("Barracks", 300, 3, 2, -20, 400),
    B_REFINERY: ("Refinery", 500, 3, 2, -30, 500),
    B_WARFACTORY: ("War Factory", 600, 3, 2, -30, 500),
    B_TURRET:     ("Gun Turret",     0, 2, 2, 0, 600),
}
UNIT_DATA = {
    U_MINIGUN: ("Minigunner", 200, 2.5, 100, 15, 96, "infantry"),
    U_ROCKET: ("Rocket Soldier", 300, 2.2, 120, 35, 160, "infantry"),
    U_TANK: ("Light Tank", 600, 2.0, 300, 40, 128, "vehicle"),
    U_HARV: ("Harvester", 700, 1.6, 400, 0, 0, "vehicle"),
}
TIB_VALUE = 25
HARV_CAP = 15

C = {
    "grass": (80,140,40), "grass_a": (72,132,36), "grass_d": (60,120,30),
    "dirt": (140,110,70), "dirt_d": (120,95,60),
    "water": (40,80,160), "water_l": (50,100,200),
    "tiberium": (60,220,60), "tiberium_g": (80,255,80), "tiberium_d": (40,160,40),
    "gdi": (60,130,200), "gdi_l": (100,180,240), "gdi_d": (30,80,140),
    "nod": (200,40,40), "nod_l": (240,80,80), "nod_d": (140,20,20),
    "sb_bg": (25,25,30), "sb_btn": (50,50,60), "sb_btn_h": (70,70,85),
    "sb_btn_d": (35,35,40), "sb_txt": (200,200,200), "sb_acc": (180,140,40),
    "hgreen": (40,200,40), "hred": (200,40,40),
    "white": (255,255,255), "black": (0,0,0), "gray": (128,128,128),
    "cy_hl": (255,255,100), "select": (0,255,0),
}

# ============================================================
# Sprite manager (simple pixel-art placeholder generator + loader)
# ============================================================
class SpriteManager:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.sprites_dir = os.path.join(script_dir, "assets", "sprites")
        if not os.path.isdir(self.sprites_dir):
            os.makedirs(self.sprites_dir, exist_ok=True)
        self.sprites = {}
        self.colors = {"GDI": C["gdi"], "NOD": C["nod"]}
        try:
            self._ensure_and_load()
        except Exception:
            pass

    def _save_surface(self, surf, path):
        try:
            pygame.image.save(surf, path)
        except Exception:
            pass

    def _gen_sprite_surface(self, w, h, color, kind):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0,0,0,0))
        base_col = color
        dark = (max(0, base_col[0]-40), max(0, base_col[1]-40), max(0, base_col[2]-40))
        # Body
        body_rect = (0, h//4, w, h*3//4)
        pygame.draw.rect(surf, base_col, body_rect)
        # Simple details per kind
        if kind == "tank":
            pygame.draw.rect(surf, dark, (w*2//5, h//8, w//5, h//3))
            pygame.draw.rect(surf, (0,0,0), (0, h-3, w, 3))
        elif kind == "infantry":
            pygame.draw.circle(surf, (255,255,255), (w//2, h//4), max(2, w//6))
            pygame.draw.rect(surf, dark, (w//4, h//2, w//2, h//3))
        elif kind in ("harv", "ref", "cyard", "turret"):
            pygame.draw.rect(surf, dark, (w//10, h//3, w*8//10, h*4//10))
            if kind == "turret":
                pygame.draw.circle(surf, (max(0,base_col[0]-80),max(0,base_col[1]-80),max(0,base_col[2]-80)), (w//2, h//3), max(3, w//6))
        return surf

    def _ensure_and_load(self):
        pairs = [
            ("gdi_tank.png","GDI","tank",24,24),
            ("nod_tank.png","NOD","tank",24,24),
            ("gdi_infantry.png","GDI","infantry",12,12),
            ("nod_infantry.png","NOD","infantry",12,12),
            ("gdi_harv.png","GDI","harv",28,20),
            ("nod_harv.png","NOD","harv",28,20),
            ("gdi_cyard.png","GDI","cyard",48,48),
            ("nod_cyard.png","NOD","cyard",48,48),
            ("gdi_refinery.png","GDI","ref",32,24),
            ("nod_refinery.png","NOD","ref",32,24),
            ("gdi_turret.png","GDI","turret",24,24),
            ("nod_turret.png","NOD","turret",24,24),
        ]
        for fname, faction, kind, w, h in pairs:
            path = os.path.join(self.sprites_dir, fname)
            color = self.colors.get(faction, (200,200,200))
            if not os.path.isfile(path):
                surf = self._gen_sprite_surface(w, h, color, kind)
                try:
                    pygame.image.save(surf, path)
                except Exception:
                    pass
            try:
                img = pygame.image.load(path).convert_alpha()
            except Exception:
                img = self._gen_sprite_surface(w, h, color, kind)

            # create a second frame with a small highlight/offset for simple two-frame animation
            img2 = pygame.Surface((w, h), pygame.SRCALPHA)
            img2.blit(img, (0,0))
            try:
                if kind == 'tank':
                    pygame.draw.rect(img2, (255,255,180,160), (w-6, 6, 3, 2))
                elif kind == 'infantry':
                    pygame.draw.circle(img2, (255,255,255,160), (w//2, 2), 1)
                elif kind == 'harv':
                    pygame.draw.rect(img2, (255,255,255,140), (w-4, h//2-2, 3, 3))
                elif kind == 'turret':
                    pygame.draw.rect(img2, (255,255,255,180), (w-5, h//2-1, 4, 2))
                else:
                    pygame.draw.rect(img2, (255,255,255,80), (w-3, 2, 2, 2))
            except Exception:
                pass

            # store as two-frame list
            self.sprites[fname] = [img, img2]

        # Load tile images from assets/tiles and scale to TILE
        self.tiles = {}
        tiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'tiles')
        try:
            for entry in os.listdir(tiles_dir):
                if entry.lower().endswith('.png'):
                    p = os.path.join(tiles_dir, entry)
                    try:
                        timg = pygame.image.load(p).convert_alpha()
                        # scale to TILE
                        timg = pygame.transform.scale(timg, (TILE, TILE))
                        self.tiles[entry] = timg
                    except Exception:
                        pass
        except Exception:
            # no tiles directory or pygame not ready
            pass

    def get(self, key):
        return self.sprites.get(key)


# ============================================================
# GAME MAP
# ============================================================
class GameMap:
    def __init__(self):
        self.tiles = [[GRASS] * MAP_COLS for _ in range(MAP_ROWS)]
        self.generate()

    def generate(self):
        # Seed random
        random.seed()

        # 1. Place water bodies
        for _ in range(6):
            wx = random.randint(2, MAP_COLS - 4)
            wy = random.randint(2, MAP_ROWS - 4)
            for r in range(random.randint(4, 8)):
                for c in range(random.randint(4, 8)):
                    cx, cy = wx + c, wy + r
                    if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
                        if random.random() < 0.75:
                            self.tiles[cy][cx] = WATER

        # 2. Tiberium fields (clusters in center areas)
        for _ in range(5):
            tx = random.randint(10, MAP_COLS - 15)
            ty = random.randint(10, MAP_ROWS - 15)
            for r in range(random.randint(3, 5)):
                for c in range(random.randint(3, 5)):
                    cx, cy = tx + c, ty + r
                    if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
                        if self.tiles[cy][cx] != WATER and random.random() < 0.6:
                            self.tiles[cy][cx] = TIBERIUM_T
        # 2b. Extra tiberium biased toward GDI base (30% tilt)
        for _ in range(2):
            tx = random.randint(5, 25)
            ty = random.randint(28, 44)
            for r in range(random.randint(3, 5)):
                for c in range(random.randint(3, 5)):
                    cx, cy = tx + c, ty + r
                    if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
                        if self.tiles[cy][cx] == GRASS and random.random() < 0.5:
                            self.tiles[cy][cx] = TIBERIUM_T

        # 3. Scatter dirt patches
        for _ in range(40):
            dx = random.randint(1, MAP_COLS - 2)
            dy = random.randint(1, MAP_ROWS - 2)
            if self.tiles[dy][dx] != WATER:
                for r in range(-1, 2):
                    for c in range(-1, 2):
                        cx, cy = dx + c, dy + r
                        if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
                            if self.tiles[cy][cx] == GRASS and random.random() < 0.3:
                                self.tiles[cy][cx] = DIRT

        # 4. Clear starting areas
        self.clear_area(2, MAP_ROWS - 8, 6, 6)    # GDI start (bottom-left)
        self.clear_area(MAP_COLS - 9, 2, 8, 6)    # Nod start (top-right)

        # 5. Ensure paths between the bases
        self.ensure_path(6, MAP_ROWS - 5, MAP_COLS - 5, 5)

    def clear_area(self, gx, gy, w, h):
        for r in range(gy, min(gy + h, MAP_ROWS)):
            for c in range(gx, min(gx + w, MAP_COLS)):
                self.tiles[r][c] = GRASS

    def ensure_path(self, sx, sy, ex, ey):
        """Dig a rough path between two points"""
        x, y = sx, sy
        steps = 0
        while (abs(x - ex) > 3 or abs(y - ey) > 3) and steps < 100:
            self.tiles[y][x] = GRASS
            for r in range(-1, 2):
                for c in range(-1, 2):
                    cx, cy = x + c, y + r
                    if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
                        if self.tiles[cy][cx] == WATER and random.random() < 0.3:
                            self.tiles[cy][cx] = GRASS
            if random.random() < 0.5:
                x += 1 if x < ex else (-1 if x > ex else 0)
            else:
                y += 1 if y < ey else (-1 if y > ey else 0)
            steps += 1

    def is_walkable(self, col, row, ignore_buildings=None):
        if col < 0 or col >= MAP_COLS or row < 0 or row >= MAP_ROWS:
            return False
        if self.tiles[row][col] == WATER:
            return False
        return True

    def find_path(self, sx, sy, ex, ey, ignore_buildings=None):
        if not self.is_walkable(ex, ey):
            return None
        if sx == ex and sy == ey:
            return [(sx, sy)]

        open_set = []
        heapq.heappush(open_set, (0, 0, sx, sy))
        came_from = {}
        g_score = { (sx, sy): 0 }
        f_score = { (sx, sy): self.heuristic(sx, sy, ex, ey) }
        closed_set = set()

        while open_set:
            _, _, cx, cy = heapq.heappop(open_set)
            if (cx, cy) in closed_set:
                continue
            closed_set.add((cx, cy))

            if cx == ex and cy == ey:
                path = []
                cur = (ex, ey)
                while cur in came_from:
                    path.append(cur)
                    cur = came_from[cur]
                path.append((sx, sy))
                path.reverse()
                return path

            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,1), (1,-1), (-1,-1)]:
                nx, ny = cx + dx, cy + dy
                if not self.is_walkable(nx, ny):
                    continue
                if (nx, ny) in closed_set:
                    continue
                move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
                tent_g = g_score[(cx, cy)] + move_cost
                if tent_g < g_score.get((nx, ny), float("inf")):
                    came_from[(nx, ny)] = (cx, cy)
                    g_score[(nx, ny)] = tent_g
                    f = tent_g + self.heuristic(nx, ny, ex, ey)
                    heapq.heappush(open_set, (f, random.random(), nx, ny))

        return None

    def heuristic(self, ax, ay, bx, by):
        return math.hypot(ax - bx, ay - by)

    def draw(self, surf, cam_x, cam_y):
        start_col = max(0, cam_x // TILE)
        start_row = max(0, cam_y // TILE)
        end_col = min(MAP_COLS, (cam_x + GAME_W) // TILE + 2)
        end_row = min(MAP_ROWS, (cam_y + SCREEN_H) // TILE + 2)

        use_tiles = ('SPRITE_MANAGER' in globals() and SPRITE_MANAGER and hasattr(SPRITE_MANAGER, 'tiles'))

        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                t = self.tiles[r][c]
                px = c * TILE - cam_x
                py = r * TILE - cam_y

                drew = False
                if use_tiles:
                    # pick tile name based on type with some variation
                    key = None
                    if t == GRASS:
                        # vary between plain and light forest for visual variety
                        if (r + c) % 11 == 0:
                            key = 'deep_forest.png'
                        elif (r + c) % 3 == 0:
                            key = 'forest.png'
                        else:
                            key = 'plain.png'
                    elif t == DIRT:
                        key = 'forest.png'
                    elif t == WATER:
                        key = 'lake.png'
                    elif t == TIBERIUM_T:
                        # use plain as base and crystals draw on top
                        key = 'plain.png'

                    if key and key in SPRITE_MANAGER.tiles:
                        try:
                            surf.blit(SPRITE_MANAGER.tiles[key], (px, py))
                            drew = True
                        except Exception:
                            drew = False

                if not drew:
                    # fallback to geometric drawing
                    if t == GRASS:
                        col = C["grass"] if (r + c) % 2 == 0 else C["grass_a"]
                        pygame.draw.rect(surf, col, (px, py, TILE, TILE))
                        # Random grass tuft
                        if (r * 7 + c * 13) % 11 == 0:
                            tuft_c = C["grass_d"]
                            pygame.draw.line(surf, tuft_c, (px+8, py+TILE), (px+10, py+TILE-4), 2)
                            pygame.draw.line(surf, tuft_c, (px+12, py+TILE), (px+15, py+TILE-3), 2)
                    elif t == DIRT:
                        pygame.draw.rect(surf, C["dirt"], (px, py, TILE, TILE))
                        # Dirt texture
                        if (r + c) % 3 == 0:
                            pygame.draw.circle(surf, C["dirt_d"], (px+8, py+8), 3)
                    elif t == WATER:
                        pygame.draw.rect(surf, C["water"], (px, py, TILE, TILE))
                        # Wave highlight
                        wave_x = (px + (r * 7) % TILE) % TILE
                        pygame.draw.line(surf, C["water_l"],
                            (px + wave_x, py + 4), (px + wave_x + 8, py + 2), 2)
                    elif t == TIBERIUM_T:
                        pygame.draw.rect(surf, C["grass_a"], (px, py, TILE, TILE))
                        # Crystal will be drawn by TiberiumCrystal.draw

                # If tiberium present, crystals are drawn later by TiberiumCrystal.draw

# ============================================================
# BUILDING CLASS
# ============================================================
class Building:
    def __init__(self, gx, gy, btype, faction, hp):
        self.gx, self.gy = gx, gy
        self.btype = btype
        self.faction = faction
        data = BUILD_DATA[btype]
        self.name = data[0]
        self.cost = data[1]
        self.gw = data[2]
        self.gh = data[3]
        self.power_val = data[4]
        self.max_hp = data[5]
        self.hp = hp
        self.anim = 0

    @property
    def px(self): return self.gx * TILE
    @property
    def py(self): return self.gy * TILE
    @property
    def pw(self): return self.gw * TILE
    @property
    def ph(self): return self.gh * TILE
    @property
    def center(self):
        return (self.px + self.pw // 2, self.py + self.ph // 2)

    def update(self, game):
        self.anim = (self.anim + 1) % 60
        if self.btype == B_TURRET and self.anim % 30 == 0:
            nearest = None
            nd = 999999
            cx = self.px + self.pw // 2
            cy = self.py + self.ph // 2
            for u in game.units:
                if u.faction != self.faction and u.hp > 0:
                    d = ((u.x - cx) ** 2 + (u.y - cy) ** 2) ** 0.5
                    if d < nd:
                        nd = d
                        nearest = u
            if nearest and nd < 160:
                game.projectiles.append(Projectile(cx, cy, nearest.x, nearest.y))
                nearest.hp -= 40
                if hasattr(game, 'sound_mgr') and game.sound_mgr:
                    game.sound_mgr.play('cannon', 0.25)

    def draw(self, surf, cam_x, cam_y, selected=False):
        sx, sy = self.px - cam_x, self.py - cam_y
        if self.faction == GDI:
            main_c, light_c, dark_c = C["gdi"], C["gdi_l"], C["gdi_d"]
            pref = "gdi"
        else:
            main_c, light_c, dark_c = C["nod"], C["nod_l"], C["nod_d"]
            pref = "nod"

        # Skip if off screen
        if sx + self.pw < -50 or sx > GAME_W + 50:
            return
        if sy + self.ph < -50 or sy > SCREEN_H + 50:
            return

        # Try to draw sprite if available
        sprite_name = None
        if self.btype == B_CYARD:
            sprite_name = f"{pref}_cyard.png"
        elif self.btype == B_POWER:
            sprite_name = f"{pref}_refinery.png"
        elif self.btype == B_BARRACKS:
            sprite_name = f"{pref}_cyard.png"
        elif self.btype == B_REFINERY:
            sprite_name = f"{pref}_refinery.png"
        elif self.btype == B_WARFACTORY:
            sprite_name = f"{pref}_cyard.png"
        elif self.btype == B_TURRET:
            sprite_name = f"{pref}_turret.png"

        sprite = None
        if 'SPRITE_MANAGER' in globals() and SPRITE_MANAGER:
            sprite = SPRITE_MANAGER.get(sprite_name) if sprite_name else None

        if sprite:
            try:
                if isinstance(sprite, (list, tuple)):
                    idx = (pygame.time.get_ticks() // 300) % len(sprite)
                    img_src = sprite[idx]
                else:
                    img_src = sprite
                img = pygame.transform.scale(img_src, (self.pw, self.ph))
                surf.blit(img, (sx, sy))
            except Exception:
                sprite = None

        if not sprite:
            # Fallback to original geometric drawing
            pygame.draw.rect(surf, dark_c, (sx, sy, self.pw, self.ph))
            pygame.draw.rect(surf, main_c, (sx + 2, sy + 2, self.pw - 4, self.ph - 4))
            inner = pygame.Rect(sx + 4, sy + 4, self.pw - 8, self.ph - 8)
            pygame.draw.rect(surf, (max(0,main_c[0]-25), max(0,main_c[1]-25), max(0,main_c[2]-25)), inner)

            # Building-specific details
            if self.btype == B_CYARD:
                midx = sx + self.pw // 2
                pygame.draw.rect(surf, C["gray"], (midx - 4, sy - 6, 8, 8))
                pygame.draw.rect(surf, C["sb_acc"], (midx - 2, sy - 10, 4, 4))
                pygame.draw.rect(surf, light_c, (sx + 4, sy + self.ph - 12, 10, 12))
            elif self.btype == B_POWER:
                pygame.draw.circle(surf, light_c, (sx + self.pw//2, sy + self.ph//2), 10)
                pygame.draw.circle(surf, C["sb_acc"], (sx + self.pw//2, sy + self.ph//2), 5)
                if self.anim % 20 < 10:
                    pygame.draw.circle(surf, C["white"], (sx + self.pw//2, sy + self.ph//2), 2)
            elif self.btype == B_BARRACKS:
                roof = [(sx, sy), (sx+self.pw, sy), (sx+self.pw-4, sy-8), (sx+4, sy-8)]
                pygame.draw.polygon(surf, light_c, roof)
                pygame.draw.rect(surf, dark_c, (sx + self.pw//2 - 5, sy + self.ph - 10, 10, 10))
            elif self.btype == B_REFINERY:
                pygame.draw.rect(surf, C["gray"], (sx + self.pw - 12, sy + 2, 10, self.ph - 4))
                pygame.draw.rect(surf, C["tiberium"], (sx + self.pw - 10, sy + 4, 6, self.ph - 8))
                pygame.draw.rect(surf, dark_c, (sx + 4, sy + self.ph - 12, 12, 12))
            elif self.btype == B_WARFACTORY:
                pygame.draw.rect(surf, dark_c, (sx + self.pw//2 - 8, sy + self.ph - 14, 16, 14))
                pygame.draw.rect(surf, C["gray"], (sx + self.pw//2 - 4, sy + self.ph - 10, 8, 6))

            # Turret-specific: circular base + rotating barrel
            if self.btype == B_TURRET:
                cx, cy = sx + self.pw // 2, sy + self.ph // 2
                pygame.draw.circle(surf, dark_c, (cx, cy), self.pw // 2)
                pygame.draw.circle(surf, main_c, (cx, cy), self.pw // 2 - 3)
                angle = (self.anim / 60.0) * 6.28318
                bx = cx + int(10 * math.cos(angle))
                by = cy + int(10 * math.sin(angle))
                pygame.draw.line(surf, dark_c, (cx, cy), (bx, by), 4)
                pygame.draw.circle(surf, light_c, (cx, cy), 4)

        # Selection
        if selected:
            pygame.draw.rect(surf, C["select"], (sx, sy, self.pw, self.ph), 2)

        # Health bar
        if self.hp < self.max_hp or self.btype == B_TURRET:
            bar_w = self.pw
            bar_h = 4
            ratio = self.hp / max(1, self.max_hp)
            hp_c = C["hgreen"] if ratio > 0.5 else (C["hred"] if ratio < 0.25 else C["sb_acc"])
            pygame.draw.rect(surf, C["black"], (sx, sy - 8, bar_w, bar_h))
            pygame.draw.rect(surf, hp_c, (sx, sy - 8, int(bar_w * ratio), bar_h))

        # Name
        font = pygame.font.Font(None, 10)
        label = font.render(self.name[:10], True, C["white"])
        surf.blit(label, (sx + 2, sy + 2))


# ============================================================
# UNIT CLASS
# ============================================================
class Unit:
    def __init__(self, ux, uy, utype, faction, hp, speed, dmg, range_px, armor):
        self.x, self.y = float(ux), float(uy)
        self.utype = utype
        self.faction = faction
        data = UNIT_DATA[utype]
        self.name = data[0]
        self.cost = data[1]
        self.base_speed = data[2]
        self.max_hp = data[3]
        self.damage = dmg
        self.attack_range = range_px
        self.armor = armor
        self.hp = hp
        self.speed = speed
        self.path = []
        self.target = None
        self.target_pos = None
        self.cooldown = 0
        self.anim_frame = 0
        self.facing = 0
        self.harvesting = False
        self.harvest_cargo = 0
        self.harvest_target = None
        self.returning = False

    def distance_to(self, ox, oy):
        return math.hypot(self.x - ox, self.y - oy)

    def is_under_cursor(self, mx, my, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        r = 18 if self.armor == "infantry" else 26
        return (mx - sx) ** 2 + (my - sy) ** 2 <= r ** 2

    def set_path_to(self, tx, ty, game_map, ingame):
        sx = max(0, min(MAP_COLS - 1, int(self.x // TILE)))
        sy = max(0, min(MAP_ROWS - 1, int(self.y // TILE)))
        ex = max(0, min(MAP_COLS - 1, int(tx // TILE)))
        ey = max(0, min(MAP_ROWS - 1, int(ty // TILE)))

        # For harvesters, don't walk on tiberium if possible
        path = game_map.find_path(sx, sy, ex, ey)
        if path and len(path) > 1:
            self.path = path[1:]
            self.target_pos = None
            return True
        return False

    def set_target(self, enemy):
        self.target = enemy
        self.path = []
        self.target_pos = None

    def update(self, game):
        self.anim_frame += 1
        if self.cooldown > 0:
            self.cooldown -= 1

        if self.utype == U_HARV:
            self.update_harvester(game)
            return

        # Combat AI: find and attack nearest enemy
        if self.damage > 0:
            nearest = None
            nd = float("inf")
            # Only engage if not following a player-given order
            if not self.path and not self.target_pos and self.target is None:
                for u in game.units:
                    if u.faction != self.faction and u.hp > 0:
                        d = self.distance_to(u.x, u.y)
                        if d < nd:
                            nd = d
                            nearest = u

                if nearest:
                    if nd <= self.attack_range and self.cooldown <= 0:
                        nearest.hp -= self.damage
                        self.cooldown = 30
                        game.projectiles.append(Projectile(self.x, self.y, nearest.x, nearest.y))
                        if hasattr(game, 'sound_mgr') and game.sound_mgr:
                            game.sound_mgr.play('gunfire' if self.armor=='infantry' else 'cannon', 0.3)
                        return
                    elif nd < self.attack_range * 4 and nd > self.attack_range * 0.9:
                        self.move_toward(nearest.x, nearest.y)
                        return

            # Attack nearby enemy buildings
            if not nearest or nd > self.attack_range * 4:
                near_build = None
                nb_dist = 999999
                bx2, by2 = 0, 0
                for b in game.buildings:
                    if b.faction != self.faction and b.hp > 0:
                        cxb, cyb = b.px + b.pw // 2, b.py + b.ph // 2
                        db = ((self.x - cxb)**2 + (self.y - cyb)**2)**0.5
                        if db < nb_dist:
                            nb_dist = db
                            near_build = b
                            bx2, by2 = cxb, cyb
                if near_build and nb_dist < self.attack_range * 3:
                    if nb_dist <= self.attack_range and self.cooldown <= 0:
                        near_build.hp -= self.damage
                        self.cooldown = 30
                        game.projectiles.append(Projectile(self.x, self.y, bx2, by2))
                        if hasattr(game, 'sound_mgr') and game.sound_mgr:
                            game.sound_mgr.play('cannon', 0.3)
                        return
                    elif nb_dist > self.attack_range * 0.9:
                        self.move_toward(bx2, by2)
                        return
            elif self.path:
                # Has move order - only shoot if enemy is in range, don't chase
                nearest2 = None
                nd2 = float("inf")
                for u in game.units:
                    if u.faction != self.faction and u.hp > 0:
                        d = self.distance_to(u.x, u.y)
                        if d < nd2 and d < self.attack_range * 1.5:
                            nd2 = d
                            nearest2 = u
                if nearest2 and nd2 <= self.attack_range and self.cooldown <= 0:
                    nearest2.hp -= self.damage
                    self.cooldown = 30
                    game.projectiles.append(Projectile(self.x, self.y, nearest2.x, nearest2.y))

        # Clear attack target, follow movement command
        self.target = None
        if self.path:
            self.follow_path()
        elif self.target_pos:
            self.move_toward_target()

        # Prevent unit overlap
        self.separate_from_others(game)

    def move_toward(self, tx, ty):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        self.update_facing(dx, dy)

    def move_toward_target(self):
        tx, ty = self.target_pos
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < self.speed:
            self.x, self.y = tx, ty
            self.target_pos = None
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        self.update_facing(dx, dy)

    def follow_path(self):
        if not self.path:
            return
        tx = self.path[0][0] * TILE + TILE // 2
        ty = self.path[0][1] * TILE + TILE // 2
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < self.speed:
            self.x, self.y = float(tx), float(ty)
            self.path.pop(0)
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        self.update_facing(dx, dy)
        self.clamp_map()

    def update_harvester(self, game):
        # Validate existing target is still alive
        if self.harvest_target and self.harvest_target not in game.tiberium_crystals:
            self.harvesting = False
            self.harvest_target = None
        # Recover stuck state
        if self.harvesting and not self.harvest_target:
            self.harvesting = False

        # Find tiberium to harvest
        if not self.harvesting and not self.returning and self.harvest_cargo < HARV_CAP:
            nearest = None
            nd = float("inf")
            for tc in game.tiberium_crystals:
                d = self.distance_to(tc.px + TILE//2, tc.py + TILE//2)
                if d < nd:
                    nd = d
                    nearest = tc
            if nearest and nd < TILE * 30:
                self.harvest_target = nearest
                self.harvesting = True
                self.set_path_to(nearest.px + TILE//2, nearest.py + TILE//2, game.game_map, game)
            elif not self.path:
                wx = max(TILE, min(MAP_PX_W - TILE, self.x + random.randint(-TILE*5, TILE*5)))
                wy = max(TILE, min(MAP_PX_H - TILE, self.y + random.randint(-TILE*5, TILE*5)))
                self.set_path_to(wx, wy, game.game_map, game)

        # Harvesting
        if self.harvesting and self.harvest_target:
            d = self.distance_to(self.harvest_target.px + TILE//2, self.harvest_target.py + TILE//2)
            if d < TILE * 2:
                if self.harvest_target.hp > 0 and self.cooldown <= 0:
                    self.harvest_target.hp -= 1
                    self.harvest_cargo += 1
                    self.cooldown = 10
                if self.harvest_target.hp <= 0 or self.harvest_cargo >= HARV_CAP:
                    if self.harvest_target in game.tiberium_crystals and self.harvest_target.hp <= 0:
                        game.tiberium_crystals.remove(self.harvest_target)
                    if self.harvest_cargo >= HARV_CAP:
                        self.harvesting = False
                        self.returning = True
                        self.find_nearest_refinery(game)
                    else:
                        self.harvesting = False
                        self.harvest_target = None
            else:
                if self.path:
                    self.follow_path()
                elif self.anim_frame % 30 == 0:
                    self.set_path_to(self.harvest_target.px + TILE//2, self.harvest_target.py + TILE//2,
                                    game.game_map, game)
                else:
                    self.move_toward(self.harvest_target.px + TILE // 2,
                                     self.harvest_target.py + TILE // 2)

        # Separation from other units
        self.separate_from_others(game)

        # Returning
        if self.returning:
            if not self.path:
                if self.harvest_cargo > 0:
                    nearest_b = None
                    nd = 999999
                    for b in game.buildings:
                        if b.faction == self.faction:
                            d = self.distance_to(b.px + b.pw//2, b.py + b.ph//2)
                            if d < nd:
                                nd = d
                                nearest_b = b
                    if nearest_b:
                        self.set_path_to(nearest_b.px + nearest_b.pw//2, nearest_b.py + nearest_b.ph//2,
                                        game.game_map, game)
                        if self.path:
                            return
                game.credits += self.harvest_cargo * TIB_VALUE
                self.harvest_cargo = 0
                self.returning = False
                self.harvest_target = None
            else:
                self.follow_path()

    def find_nearest_refinery(self, game):
        nearest = None
        nd = float("inf")
        for b in game.buildings:
            if b.btype == B_REFINERY and b.faction == self.faction:
                d = self.distance_to(b.px + b.pw//2, b.py + b.ph//2)
                if d < nd:
                    nd = d
                    nearest = b
        if nearest:
            self.set_path_to(nearest.px + nearest.pw//2, nearest.py + nearest.ph//2,
                            game.game_map, game)

    def separate_from_others(self, game):
        min_dist = 10 if self.armor == 'infantry' else 22
        for other in game.units:
            if other is self:
                continue
            if other.faction != self.faction:
                continue
            # Use average minimum distance for mixed types
            sep = min_dist if other.armor == self.armor else 14
            dx = self.x - other.x
            dy = self.y - other.y
            dist = math.hypot(dx, dy)
            if 0 < dist < sep:
                push = (sep - dist) * 0.3
                self.x += (dx / dist) * push
                self.y += (dy / dist) * push
                self.clamp_map()

    def update_facing(self, dx, dy):
        if abs(dx) > abs(dy):
            self.facing = 0 if dx > 0 else 2
        else:
            self.facing = 1 if dy > 0 else 3

    def clamp_map(self):
        margin = TILE // 2
        self.x = max(margin, min(MAP_PX_W - margin, self.x))
        self.y = max(margin, min(MAP_PX_H - margin, self.y))

    def draw(self, surf, cam_x, cam_y, selected=False):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        if sx < -30 or sx > GAME_W + 30 or sy < -30 or sy > SCREEN_H + 30:
            return

        main_c, light_c, dark_c = (C["gdi"], C["gdi_l"], C["gdi_d"]) if self.faction == GDI \
            else (C["nod"], C["nod_l"], C["nod_d"])

        # Determine sprite key
        pref = "gdi" if self.faction == GDI else "nod"
        if self.utype == U_MINIGUN or self.armor == "infantry":
            sprite_key = f"{pref}_infantry.png"
            desired_size = (12,12)
        elif self.utype == U_ROCKET:
            sprite_key = f"{pref}_infantry.png"
            desired_size = (14,14)
        elif self.utype == U_TANK:
            sprite_key = f"{pref}_tank.png"
            desired_size = (24,24)
        elif self.utype == U_HARV:
            sprite_key = f"{pref}_harv.png"
            desired_size = (28,20)
        else:
            sprite_key = None
            desired_size = (16,16)

        sprite = None
        if 'SPRITE_MANAGER' in globals() and SPRITE_MANAGER and sprite_key:
            sprite = SPRITE_MANAGER.get(sprite_key)

        if sprite:
            try:
                if isinstance(sprite, (list, tuple)):
                    idx = (pygame.time.get_ticks() // 200) % len(sprite)
                    img_src = sprite[idx]
                else:
                    img_src = sprite
                img = pygame.transform.scale(img_src, desired_size)
                # center
                iw, ih = desired_size
                surf.blit(img, (sx - iw//2, sy - ih//2))
            except Exception:
                sprite = None

        if not sprite:
            # Fallback to original geometric drawing
            if self.armor == "infantry":
                body_r = 7 if self.utype == U_ROCKET else 5
                # Body
                pygame.draw.circle(surf, dark_c, (sx, sy), body_r + 1)
                pygame.draw.circle(surf, main_c, (sx, sy), body_r)
                # Head
                pygame.draw.circle(surf, C["white"], (sx, sy - body_r - 2), 3)
                # Gun
                if self.facing == 0:
                    pygame.draw.line(surf, dark_c, (sx+body_r, sy), (sx+body_r+8, sy), 2)
                elif self.facing == 1:
                    pygame.draw.line(surf, dark_c, (sx, sy+body_r), (sx, sy+body_r+8), 2)
                elif self.facing == 2:
                    pygame.draw.line(surf, dark_c, (sx-body_r, sy), (sx-body_r-8, sy), 2)
                else:
                    pygame.draw.line(surf, dark_c, (sx, sy-body_r), (sx, sy-body_r-8), 2)
                # Rocket soldier backpack
                if self.utype == U_ROCKET:
                    pygame.draw.circle(surf, C["gray"], (sx, sy - body_r // 2), 3)
            else:
                half_w = 12 if self.utype == U_TANK else 14
                half_h = 10 if self.utype == U_TANK else 12
                # Shadow
                pygame.draw.ellipse(surf, (0,0,0,80), (sx-half_w+1, sy-half_h+1, half_w*2, half_h*2))
                # Body
                pygame.draw.rect(surf, dark_c, (sx-half_w, sy-half_h, half_w*2, half_h*2))
                pygame.draw.rect(surf, main_c, (sx-half_w+1, sy-half_h+1, half_w*2-2, half_h*2-2))
                # Turret / detail
                if self.utype == U_TANK:
                    pygame.draw.circle(surf, light_c, (sx, sy), 6)
                    if self.facing == 0:
                        pygame.draw.rect(surf, dark_c, (sx+3, sy-2, 12, 4))
                    elif self.facing == 1:
                        pygame.draw.rect(surf, dark_c, (sx-2, sy+3, 4, 12))
                    elif self.facing == 2:
                        pygame.draw.rect(surf, dark_c, (sx-15, sy-2, 12, 4))
                    else:
                        pygame.draw.rect(surf, dark_c, (sx-2, sy-15, 4, 12))
                    # Treads
                    pygame.draw.rect(surf, (0,0,0), (sx-half_w, sy-half_h-2, half_w*2, 2))
                    pygame.draw.rect(surf, (0,0,0), (sx-half_w, sy+half_h, half_w*2, 2))
                else:
                    # Harvester
                    pygame.draw.rect(surf, C["gray"], (sx-half_w+1, sy+half_h-5, half_w*2-2, 4))
                    if self.harvest_cargo > 0:
                        pct = self.harvest_cargo / HARV_CAP
                        pygame.draw.rect(surf, C["tiberium"], (sx-half_w+1, sy-half_h+1, int((half_w*2-2)*pct), 3))

        # Selection circle
        if selected:
            r = 14 if self.armor == "infantry" else 20
            pygame.draw.circle(surf, C["select"], (sx, sy), r, 2)

        # Health bar
        if self.hp < self.max_hp:
            bw = 16
            bh = 3
            ratio = self.hp / max(1, self.max_hp)
            hp_c = C["hgreen"] if ratio > 0.5 else (C["hred"] if ratio < 0.25 else C["sb_acc"])
            pygame.draw.rect(surf, C["black"], (sx - bw//2, sy - 18, bw, bh))
            pygame.draw.rect(surf, hp_c, (sx - bw//2, sy - 18, int(bw * ratio), bh))


# ============================================================
# PROJECTILE CLASS
# ============================================================
class Projectile:
    def __init__(self, sx, sy, tx, ty):
        self.x, self.y = float(sx), float(sy)
        dx = tx - sx
        dy = ty - sy
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * 8
            self.vy = (dy / dist) * 8
        else:
            self.vx = self.vy = 0
        self.life = 50
        self.dead = False

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0 or self.x < 0 or self.x > MAP_PX_W or self.y < 0 or self.y > MAP_PX_H:
            self.dead = True

    def draw(self, surf, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        pygame.draw.circle(surf, C["white"], (sx, sy), 2)
        pygame.draw.circle(surf, C["sb_acc"], (sx, sy), 1)


# ============================================================
# TIBERIUM CRYSTAL (harvestable resource)
# ============================================================
class TiberiumCrystal:
    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.hp = 8

    @property
    def px(self): return self.col * TILE
    @property
    def py(self): return self.row * TILE

    def draw(self, surf, cam_x, cam_y):
        px = self.px - cam_x
        py = self.py - cam_y
        if px < -TILE or px > GAME_W + TILE or py < -TILE or py > SCREEN_H + TILE:
            return
        if self.hp <= 0:
            return
        # Crystal patches
        main = C["tiberium_g"]
        dark = C["tiberium"]
        glow = C["tiberium"]
        # Multiple crystal spikes
        if self.hp > 6:
            pts = [(px+4, py+TILE), (px+12, py+TILE), (px+8, py+2)]
            pygame.draw.polygon(surf, main, pts)
            pts2 = [(px+10, py+TILE), (px+18, py+TILE), (px+14, py+8)]
            pygame.draw.polygon(surf, dark, pts2)
        elif self.hp > 3:
            pts = [(px+6, py+TILE), (px+14, py+TILE), (px+10, py+6)]
            pygame.draw.polygon(surf, main, pts)
        else:
            pts = [(px+8, py+TILE), (px+16, py+TILE), (px+12, py+10)]
            pygame.draw.polygon(surf, dark, pts)
        # Small glow
        glow_s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*C["tiberium_g"], 40), (TILE//2, TILE//2), 10)
        surf.blit(glow_s, (px, py))


# ============================================================
# SIDEBAR UI
# ============================================================
class Sidebar:
    def __init__(self):
        self.rect = pygame.Rect(GAME_W, 0, SIDEBAR_W, SCREEN_H)
        self.font_s = pygame.font.Font(None, 14)
        self.font_m = pygame.font.Font(None, 18)
        self.font_l = pygame.font.Font(None, 24)
        self.hover_btn = -1
        self.active_tab = 0  # 0=builder tab when CY selected, 1=barracks, 2=war factory
        self.btn_rects = []
        self.scroll_y = 0

    def get_buttons_for(self, game):
        btns = []
        if game.selected_building and game.selected_building.btype == B_CYARD:
            btns = [
                ("POW", "Power Plant", "build", B_POWER, 200),
                ("BAR", "Barracks", "build", B_BARRACKS, 300),
                ("REF", "Refinery", "build", B_REFINERY, 500),
                ("WAR", "War Factory", "build", B_WARFACTORY, 600),
            ]
        elif game.selected_building and game.selected_building.btype == B_BARRACKS:
            btns = [
                ("MINI", "Minigunner (200)", "unit", U_MINIGUN, 200),
                ("ROCK", "Rocket(300)", "unit", U_ROCKET, 300),
            ]
        elif game.selected_building and game.selected_building.btype == B_WARFACTORY:
            btns = [
                ("TANK", "Light Tank (600)", "unit", U_TANK, 600),
                ("HARV", "Harvester (700)", "unit", U_HARV, 700),
            ]
        return btns

    def draw(self, surf, game):
        # Background
        pygame.draw.rect(surf, C["sb_bg"], self.rect)
        # Border
        pygame.draw.line(surf, C["sb_acc"], (GAME_W, 0), (GAME_W, SCREEN_H), 2)

        # Credits display
        cred_text = self.font_l.render(f"${game.credits}", True, C["sb_acc"])
        surf.blit(cred_text, (GAME_W + 10, 10))

        # Power indicator
        pw_text = self.font_s.render(f"PWR: {game.power_available}/{game.power_used}", True, C["sb_txt"])
        surf.blit(pw_text, (GAME_W + 10, 38))

        # Faction emblem
        emblem = "GDI"
        fac_text = self.font_l.render(emblem, True, C["gdi_l"] if emblem == "GDI" else C["nod_l"])
        surf.blit(fac_text, (GAME_W + 10, 60))

        # Separator
        pygame.draw.line(surf, C["gray"], (GAME_W, 90), (SCREEN_W, 90))

        # Selection info
        if game.selected_building:
            b = game.selected_building
            info_y = 100
            name_text = self.font_m.render(b.name, True, C["white"])
            surf.blit(name_text, (GAME_W + 10, info_y))
            hp_text = self.font_s.render(f"HP: {max(0,b.hp)}/{b.max_hp}", True, C["hgreen"])
            surf.blit(hp_text, (GAME_W + 10, info_y + 22))
        elif game.selected_units:
            info_y = 100
            u = game.selected_units[0]
            name_text = self.font_m.render(f"{u.name} x{len(game.selected_units)}", True, C["white"])
            surf.blit(name_text, (GAME_W + 10, info_y))
            hp_text = self.font_s.render(f"HP: {max(0,u.hp)}/{u.max_hp}", True, C["hgreen"])
            surf.blit(hp_text, (GAME_W + 10, info_y + 22))

        # Build buttons
        btns = self.get_buttons_for(game)
        self.btn_rects = []
        btn_y = 160
        btn_h = 60
        y_offset = 0
        self.hover_btn = -1

        for i, (label, tooltip, action_type, obj_type, cost) in enumerate(btns):
            by = btn_y + y_offset
            pygame.draw.rect(surf, C["sb_btn"], (GAME_W + 8, by, SIDEBAR_W - 16, btn_h), 0, 3)
            # Button label
            btn_label = self.font_m.render(label, True, C["sb_acc"])
            surf.blit(btn_label, (GAME_W + 16, by + 6))
            # Cost
            cost_text = self.font_s.render(f"${cost}", True, C["sb_txt"])
            surf.blit(cost_text, (GAME_W + 16, by + 28))
            # Check if affordable
            affordable = game.credits >= cost
            power_ok = True
            if action_type == "build":
                data = BUILD_DATA[obj_type]
                if data[4] < 0:  # consumes power
                    power_ok = (game.power_available + game.power_used >= abs(data[4]))
            if not affordable or not power_ok:
                # Dim overlay
                dim = pygame.Surface((SIDEBAR_W - 16, btn_h), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 120))
                surf.blit(dim, (GAME_W + 8, by))
            # Hover
            mx, my = pygame.mouse.get_pos()
            btn_rect = pygame.Rect(GAME_W + 8, by, SIDEBAR_W - 16, btn_h)
            self.btn_rects.append(btn_rect)
            if btn_rect.collidepoint(mx, my):
                self.hover_btn = i
                pygame.draw.rect(surf, C["sb_btn_h"], btn_rect, 2, 3)
                # Tooltip
                if tooltip:
                    tt = self.font_s.render(tooltip, True, C["white"])
                    surf.blit(tt, (GAME_W + 16, by + 44))
            y_offset += btn_h + 6

        # Tooltip for hover
        if game.state == GS_GAME_OVER and game.winner is not None:
            # Game over overlay
            go_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            go_surf.fill((0, 0, 0, 180))
            surf.blit(go_surf, (0, 0))
            win_text = "VICTORY! GDI WINS!" if game.winner == GDI else "DEFEATED. NOD WINS!"
            win_c = C["gdi_l"] if game.winner == GDI else C["nod_l"]
            big_font = pygame.font.Font(None, 72)
            wt = big_font.render(win_text, True, win_c)
            surf.blit(wt, (SCREEN_W // 2 - wt.get_width() // 2, SCREEN_H // 2 - 40))
            sub_font = pygame.font.Font(None, 28)
            st = sub_font.render("Press R to restart or ESC to quit", True, C["white"])
            surf.blit(st, (SCREEN_W // 2 - st.get_width() // 2, SCREEN_H // 2 + 20))

        # Minimap (in the sidebar)
        self.draw_minimap(surf, game)

    def draw_minimap(self, surf, game):
        mm_x = GAME_W + 16
        mm_y = SCREEN_H - 175
        mm_w = MINIMAP_W = 160
        mm_h = MINIMAP_H = 160

        # Border
        pygame.draw.rect(surf, C["gray"], (mm_x - 2, mm_y - 2, mm_w + 4, mm_h + 4), 1)

        # Scale factors
        sx = mm_w / MAP_COLS
        sy = mm_h / MAP_ROWS

        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                t = game.game_map.tiles[r][c]
                if t == WATER:
                    col = C["water"]
                elif t == TIBERIUM_T:
                    col = C["tiberium_g"]
                elif t == DIRT:
                    col = C["dirt"]
                else:
                    col = C["grass_d"] if (r + c) % 2 == 0 else C["grass"]
                px = mm_x + int(c * sx)
                py = mm_y + int(r * sy)
                size = max(1, int(sx + 0.5))
                surf.fill(col, (px, py, size, size))

        # Draw buildings on minimap
        for b in game.buildings:
            bx = mm_x + int(b.gx * sx)
            by = mm_y + int(b.gy * sy)
            bw = max(1, int(b.gw * sx))
            bh = max(1, int(b.gh * sy))
            col = C["gdi_l"] if b.faction == GDI else C["nod_l"]
            surf.fill(col, (bx, by, bw, bh))

        # Draw units on minimap
        for u in game.units:
            ux = mm_x + int((u.x / TILE) * sx)
            uy = mm_y + int((u.y / TILE) * sy)
            col = C["gdi"] if u.faction == GDI else C["nod"]
            surf.set_at((int(ux), int(uy)), col)

        # Camera viewport on minimap
        cam_x = mm_x + int((game.cam_x / TILE) * sx)
        cam_y = mm_y + int((game.cam_y / TILE) * sy)
        cam_w = max(2, int((GAME_W / TILE) * sx))
        cam_h = max(2, int((SCREEN_H / TILE) * sy))
        pygame.draw.rect(surf, C["white"], (cam_x, cam_y, cam_w, cam_h), 1)

    def handle_click(self, game, pos):
        if game.state == GS_GAME_OVER:
            return False

        # Check button clicks
        mx, my = pos
        btns = self.get_buttons_for(game)
        for i, btn_rect in enumerate(self.btn_rects):
            if btn_rect.collidepoint(mx, my) and i < len(btns):
                label, tooltip, action_type, obj_type, cost = btns[i]
                if game.credits >= cost:
                    return ("build" if action_type == "build" else "train", obj_type, cost)
        return None


# ============================================================
# AI CONTROLLER
# ============================================================
class AIController:
    def __init__(self, faction, difficulty=1.0):
        self.faction = faction
        self.difficulty = difficulty  # multiplier for AI speed/reaction
        self.last_build_time = 0
        self.build_cycle = 0
        self.attack_timer = 0
        self.unit_cycle = 0
        self.aggression = 0.7

    def update(self, game):
        if game.state != GS_PLAYING:
            return
        if game.game_time < 180:  # Wait 1 second before acting
            return

        # AI build logic
        self.build_cycle += 1
        if self.build_cycle >= max(30, int(90 / self.difficulty)):
            self.build_cycle = 0
            self.ai_build(game)

        # AI train units
        self.unit_cycle += 1
        if self.unit_cycle >= max(20, int(60 / self.difficulty)):
            self.unit_cycle = 0
            self.ai_train(game)

        # AI attack
        if game.game_time > 900:  # Start attacking after 5 seconds
            self.attack_timer += 1
            if self.attack_timer >= max(120, int(300 / self.difficulty)):
                self.attack_timer = 0
                self.ai_attack(game)

        # Have harvesters harvest
        for u in game.units:
            if u.faction == self.faction and u.utype == U_HARV and not u.harvesting and not u.returning:
                pass  # harvester handles itself

    def ai_build(self, game):
        # Count buildings
        cys = [b for b in game.buildings if b.faction == self.faction and b.btype == B_CYARD]
        if not cys:
            return
        cy = cys[0]

        powers = [b for b in game.buildings if b.faction == self.faction and b.btype == B_POWER]
        refineries = [b for b in game.buildings if b.faction == self.faction and b.btype == B_REFINERY]
        barracks = [b for b in game.buildings if b.faction == self.faction and b.btype == B_BARRACKS]
        war_factories = [b for b in game.buildings if b.faction == self.faction and b.btype == B_WARFACTORY]

        # Determine what to build
        if len(powers) < 2:
            btype = B_POWER
        elif len(refineries) == 0:
            btype = B_REFINERY
        elif len(barracks) == 0:
            btype = B_BARRACKS
        elif len(war_factories) == 0:
            btype = B_WARFACTORY
        elif len(powers) < 3:
            btype = B_POWER
        elif len(refineries) < 2:
            btype = B_REFINERY
        elif len(war_factories) < 2:
            btype = B_WARFACTORY
        else:
            btype = B_POWER

        # Check cost
        data = BUILD_DATA[btype]
        name, cost, gw, gh, power, hp = data
        if game.credits >= cost:
            # Find placement near construction yard
            for attempt in range(20):
                ox = cy.gx + random.randint(-4, 4)
                oy = cy.gy + random.randint(-5, 5)
                ox = max(0, min(MAP_COLS - gw, ox))
                oy = max(0, min(MAP_ROWS - gh, oy))
                if game.can_place_building(ox, oy, btype, self.faction):
                    game.add_building(ox, oy, btype, self.faction)
                    break

    def ai_train(self, game):
        barracks_list = [b for b in game.buildings if b.faction == self.faction and b.btype == B_BARRACKS]
        war_factories = [b for b in game.buildings if b.faction == self.faction and b.btype == B_WARFACTORY]

        if barracks_list and game.credits >= 300:
            b = barracks_list[0]
            utype = U_ROCKET if random.random() < 0.3 else U_MINIGUN
            spawn_x = b.px + b.pw // 2 + random.randint(-10, 10)
            spawn_y = b.py + b.ph + TILE // 2
            game.add_unit(spawn_x, spawn_y, utype, self.faction)

        if war_factories and game.credits >= 600:
            w = war_factories[0]
            utype = U_HARV if len([u for u in game.units if u.faction == self.faction and u.utype == U_HARV]) < 2 else U_TANK
            spawn_x = w.px + w.pw // 2 + random.randint(-10, 10)
            spawn_y = w.py + w.ph + TILE // 2
            if game.credits >= UNIT_DATA[utype][1]:
                game.add_unit(spawn_x, spawn_y, utype, self.faction)

    def ai_attack(self, game):
        # Find combat units
        attackers = [u for u in game.units if u.faction == self.faction and u.damage > 0]
        if len(attackers) < 3:
            return

        # Find enemy construction yard
        target = None
        for b in game.buildings:
            if b.faction != self.faction and b.btype == B_CYARD:
                target = (b.px + b.pw // 2, b.py + b.ph // 2)
                break
        if not target:
            # Attack any enemy building
            for b in game.buildings:
                if b.faction != self.faction:
                    target = (b.px + b.pw // 2, b.py + b.ph // 2)
                    break

        if target:
            for u in attackers[:5]:
                u.set_path_to(target[0], target[1], game.game_map, game)

            # Add some randomness so they spread out
            for u in attackers[5:]:
                tx = target[0] + random.randint(-TILE*2, TILE*2)
                ty = target[1] + random.randint(-TILE*2, TILE*2)
                u.set_path_to(tx, ty, game.game_map, game)


# ============================================================
# MAIN GAME CLASS
# ============================================================
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Command & Conquer: Tiberian Dawn (Clone)")
        self.clock = pygame.time.Clock()
        self.running = True
        self.sound_mgr = SoundManager()
        self.sound_mgr.start_music()
        # Initialize sprite manager (creates/loads placeholder sprites under assets/sprites)
        try:
            self.sprite_manager = SpriteManager()
            global SPRITE_MANAGER
            SPRITE_MANAGER = self.sprite_manager
        except Exception:
            self.sprite_manager = None
            SPRITE_MANAGER = None
        self.reset_game()

    def reset_game(self):
        self.game_map = GameMap()
        self.units = []
        self.buildings = []
        self.projectiles = []
        self.tiberium_crystals = []
        self.selected_units = []
        self.selected_building = None
        self.move_markers = []
        self.turret_timers = []
        self.credits = 2500
        self.power_available = 0
        self.power_used = 0
        self.state = GS_PLAYING
        self.winner = None
        self.frame = 0
        self.game_time = 0
        self.dragging = False
        self.drag_start = None
        self.drag_rect = None
        self.right_click_target = None
        self.placing_building = None
        self.place_type = None
        self.place_cost = 0
        self.ai = AIController(NOD, difficulty=0.35)
        self.sidebar = Sidebar()
        self.show_help = False
        # GDI base camera position (for Home key)
        self.home_cam_x = max(0, min(MAP_PX_W - GAME_W, 112 - GAME_W // 2))
        self.home_cam_y = max(0, min(MAP_PX_H - SCREEN_H, 1392 - SCREEN_H // 2))
        self.cam_x = self.home_cam_x
        self.cam_y = 0
        # GDI base camera position (for Home key)
        self.home_cam_x = max(0, min(MAP_PX_W - GAME_W, 112 - GAME_W // 2))
        self.home_cam_y = max(0, min(MAP_PX_H - SCREEN_H, 1392 - SCREEN_H // 2))

        # Spawn tiberium crystals
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                if self.game_map.tiles[r][c] == TIBERIUM_T:
                    tiberium = TiberiumCrystal(c, r)
                    self.tiberium_crystals.append(tiberium)

        # Place initial GDI buildings
        # Construction yard at bottom-left
        cy = self.add_building(2, MAP_ROWS - 6, B_CYARD, GDI)
        self.add_unit(cy.px + cy.pw // 2 + 40, cy.py + cy.ph + 10, U_TANK, GDI)
        self.add_unit(cy.px + cy.pw // 2 + 20, cy.py + cy.ph + 10, U_MINIGUN, GDI)
        self.add_unit(cy.px + cy.pw // 2, cy.py + cy.ph + 10, U_MINIGUN, GDI)
        self.add_unit(cy.px + cy.pw // 2 - 20, cy.py + cy.ph + 10, U_MINIGUN, GDI)
        self.add_unit(cy.px + cy.pw // 2 - 40, cy.py + cy.ph + 10, U_MINIGUN, GDI)
        self.add_unit(cy.px + cy.pw // 2 + 30, cy.py + cy.ph + 60, U_HARV, GDI)
        self.add_unit(cy.px + cy.pw // 2 - 30, cy.py + cy.ph + 60, U_MINIGUN, GDI)

        # Place turrets forward toward NOD base
        self.add_building(4, 38, B_TURRET, GDI)
        self.add_building(8, 39, B_TURRET, GDI)

        # Place initial NOD buildings
        cy2 = self.add_building(MAP_COLS - 8, 2, B_CYARD, NOD)
        self.add_unit(cy2.px + cy2.pw // 2 + 30, cy2.py + cy2.gh * TILE + 10, U_MINIGUN, NOD)
        self.add_unit(cy2.px + cy2.pw // 2 - 30, cy2.py + cy2.gh * TILE + 10, U_MINIGUN, NOD)
        self.add_unit(cy2.px + cy2.pw // 2, cy2.py + cy2.gh * TILE + 40, U_TANK, NOD)

        # Place NOD turrets forward toward GDI base
        self.add_building(41, 8, B_TURRET, NOD)
        self.add_building(37, 6, B_TURRET, NOD)

        # Camera to player base
        self.cam_x = self.home_cam_x
        self.cam_y = self.home_cam_y

    def can_place_building(self, gx, gy, btype, faction):
        data = BUILD_DATA[btype]
        gw, gh = data[2], data[3]
        for col in range(gx, gx + gw):
            for row in range(gy, gy + gh):
                if col < 0 or col >= MAP_COLS or row < 0 or row >= MAP_ROWS:
                    return False
                t = self.game_map.tiles[row][col]
                if t == WATER:
                    return False
                for b in self.buildings:
                    if col >= b.gx and col < b.gx + b.gw and row >= b.gy and row < b.gy + b.gh:
                        return False
        return True

    def find_build_spot(self, cy_building, btype):
        data = BUILD_DATA[btype]
        gw, gh = data[2], data[3]
        # Try around the construction yard
        best_positions = []
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                gx = cy_building.gx + cy_building.gw // 2 + dx
                gy = cy_building.gy + cy_building.gh + dy
                if self.can_place_building(gx, gy, btype, GDI):
                    best_positions.append((gx, gy))
        if best_positions:
            return best_positions[0]
        return None

    def add_building(self, gx, gy, btype, faction):
        data = BUILD_DATA[btype]
        name, cost, gw, gh, power, hp = data
        b = Building(gx, gy, btype, faction, hp)
        self.buildings.append(b)
        if power >= 0:
            self.power_available += power
        else:
            self.power_used += abs(power)
        return b

    def add_unit(self, ux, uy, utype, faction):
        ux = max(TILE//2, min(MAP_PX_W - TILE//2, ux))
        uy = max(TILE//2, min(MAP_PX_H - TILE//2, uy))
        data = UNIT_DATA[utype]
        name, cost, speed, max_hp, dmg, range_px, armor = data
        u = Unit(ux, uy, utype, faction, max_hp, speed, dmg, range_px, armor)
        if faction == GDI:
            u.max_hp *= 2
            u.hp = u.max_hp
        self.units.append(u)
        return u

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mousedown(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_mouseup(event)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mousemotion(event)

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_r and self.state == GS_GAME_OVER:
            self.reset_game()
        elif event.key == pygame.K_F1 or event.key == pygame.K_h:
            self.show_help = not getattr(self, "show_help", False)
        # Camera controls
        elif event.key == pygame.K_HOME:
            self.cam_x = self.home_cam_x
            self.cam_y = self.home_cam_y
        elif event.key == pygame.K_HOME:
            self.cam_x = self.home_cam_x
            self.cam_y = self.home_cam_y
        elif event.key == pygame.K_UP or event.key == pygame.K_w:
            self.cam_y = max(0, self.cam_y - 50)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.cam_y = min(MAP_PX_H - SCREEN_H, self.cam_y + 50)
        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self.cam_x = max(0, self.cam_x - 50)
        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            self.cam_x = min(MAP_PX_W - GAME_W, self.cam_x + 50)

    def handle_mousedown(self, event):
        mx, my = event.pos
        if event.button == 1:  # Left click
            # Check minimap click
            mm_x = GAME_W + 16
            mm_y = SCREEN_H - 175
            mm_w = 160
            mm_h = 160
            if mm_x <= mx <= mm_x + mm_w and mm_y <= my <= mm_y + mm_h:
                sx = mm_w / MAP_COLS
                sy = mm_h / MAP_ROWS
                tc = (mx - mm_x) / sx
                tr = (my - mm_y) / sy
                self.cam_x = max(0, min(MAP_PX_W - GAME_W, int(tc * TILE) - GAME_W // 2))
                self.cam_y = max(0, min(MAP_PX_H - SCREEN_H, int(tr * TILE) - SCREEN_H // 2))
                return
            # Check sidebar first
            if mx >= GAME_W:
                result = self.sidebar.handle_click(self, (mx, my))
                if result and result[0] == "build" and self.state == GS_PLAYING:
                    btype = result[1]
                    cost = result[2]
                    # Find building spot
                    cys = [b for b in self.buildings if b.faction == GDI and b.btype == B_CYARD]
                    if cys:
                        spot = self.find_build_spot(cys[0], btype)
                        if spot:
                            self.credits -= cost
                            self.add_building(spot[0], spot[1], btype, GDI)
                elif result and result[0] == "train" and self.state == GS_PLAYING:
                    utype = result[1]
                    cost = result[2]
                    # Spawn near the producing building
                    if self.selected_building:
                        bx = self.selected_building.px + self.selected_building.pw // 2
                        by = self.selected_building.py + self.selected_building.ph + TILE // 2
                        self.credits -= cost
                        self.add_unit(bx, by, utype, GDI)
                return

            # Left click on game area
            self.dragging = True
            self.drag_start = (mx, my)
            self.drag_rect = pygame.Rect(mx, my, 0, 0)

            # Check if clicking on a unit
            clicked_unit = None
            for u in reversed(self.units):
                if u.faction == GDI and u.is_under_cursor(mx, my, self.cam_x, self.cam_y):
                    clicked_unit = u
                    break

            if clicked_unit:
                self.selected_building = None
                self.selected_units = [clicked_unit]
                # Play selection sound
                if self.sound_mgr:
                    if clicked_unit.utype == U_HARV:
                        self.sound_mgr.play('harv_ack', 0.5)
                    elif clicked_unit.armor == 'vehicle':
                        self.sound_mgr.play('tank_ack', 0.5)
                    else:
                        self.sound_mgr.play('soldier_ack', 0.5)
            else:
                # Check buildings
                clicked_building = None
                for b in reversed(self.buildings):
                    if b.faction == GDI:
                        sx = b.px - self.cam_x
                        sy = b.py - self.cam_y
                        if sx <= mx <= sx + b.pw and sy <= my <= sy + b.ph:
                            clicked_building = b
                            break
                if clicked_building:
                    self.selected_units = []
                    self.selected_building = clicked_building
                else:
                    self.selected_units = []
                    self.selected_building = None

        elif event.button == 3:  # Right click
            # Move/attack command
            if self.selected_units and self.state == GS_PLAYING:
                tx = mx + self.cam_x
                ty = my + self.cam_y

                # Check if right-clicked on enemy
                enemy_clicked = None
                for u in self.units:
                    if u.faction != GDI and u.is_under_cursor(mx, my, self.cam_x, self.cam_y):
                        enemy_clicked = u
                        break

                if enemy_clicked:
                    for u in self.selected_units:
                        if u.damage > 0:
                            u.set_target(enemy_clicked)
                        else:
                            u.set_path_to(enemy_clicked.x, enemy_clicked.y, self.game_map, self)
                else:
                    for u in self.selected_units:
                        u.target = None
                        u.set_path_to(tx, ty, self.game_map, self)
                    self.move_markers.append([tx, ty, 30])

    def handle_mouseup(self, event):
        if event.button == 1 and self.dragging:
            self.dragging = False
            # Box select
            if self.drag_rect and self.drag_rect.width > 3:
                selected = []
                for u in self.units:
                    if u.faction == GDI:
                        sx = u.x - self.cam_x
                        sy = u.y - self.cam_y
                        r = 12 if u.armor == "infantry" else 18
                        if self.drag_rect.collidepoint(sx, sy):
                            selected.append(u)
                if selected:
                    self.selected_units = selected
                    self.selected_building = None
            self.drag_rect = None

    def handle_mousemotion(self, event):
        mx, my = event.pos
        # Scroll with mouse at screen edge (only in game area)
        if self.state == GS_PLAYING and mx < GAME_W:
            scroll = 8
            edge = 20
            if mx < edge:
                self.cam_x = max(0, self.cam_x - scroll)
            elif mx > GAME_W - edge:
                self.cam_x = min(MAP_PX_W - GAME_W, self.cam_x + scroll)
            if my < edge:
                self.cam_y = max(0, self.cam_y - scroll)
            elif my > SCREEN_H - edge:
                self.cam_y = min(MAP_PX_H - SCREEN_H, self.cam_y + scroll)

        if self.dragging:
            self.drag_rect = pygame.Rect(
                min(self.drag_start[0], mx),
                min(self.drag_start[1], my),
                abs(mx - self.drag_start[0]),
                abs(my - self.drag_start[1])
            )

    def update(self):
        self.frame += 1
        self.game_time += 1
        if self.state != GS_PLAYING:
            return

        # Update buildings
        for b in self.buildings[:]:
            b.update(self)
            if b.hp <= 0:
                if b is self.selected_building:
                    self.selected_building = None
                if b.btype == B_TURRET:
                    self.turret_timers.append([b.gx, b.gy, b.faction, 7200])
                self.buildings.remove(b)
                if b.power_val >= 0:
                    self.power_available = max(0, self.power_available - b.power_val)
                else:
                    self.power_used = max(0, self.power_used - abs(b.power_val))

        # Update units
        for u in self.units[:]:
            u.update(self)
            if u.hp <= 0:
                if u in self.selected_units:
                    self.selected_units.remove(u)
                self.units.remove(u)

        # Update projectiles
        for p in self.projectiles[:]:
            p.update()
            if p.dead:
                self.projectiles.remove(p)

        # Update move markers
        for m in self.move_markers[:]:
            m[2] -= 1
            if m[2] <= 0:
                self.move_markers.remove(m)

        # AI
        self.ai.update(self)

        # Turret respawn (2 minutes = 7200 frames)
        for t in self.turret_timers[:]:
            t[3] -= 1
            if t[3] <= 0:
                self.add_building(t[0], t[1], B_TURRET, t[2])
                self.turret_timers.remove(t)

        # Check game over
        gdi_cys = [b for b in self.buildings if b.btype == B_CYARD and b.faction == GDI]
        nod_cys = [b for b in self.buildings if b.btype == B_CYARD and b.faction == NOD]
        if len(gdi_cys) == 0:
            self.state = GS_GAME_OVER
            self.winner = NOD
        elif len(nod_cys) == 0:
            self.state = GS_GAME_OVER
            self.winner = GDI

    def draw(self):
        # Clear
        self.screen.fill(C["black"])

        # Draw map
        self.game_map.draw(self.screen, self.cam_x, self.cam_y)

        # Draw tiberium
        for tc in self.tiberium_crystals[:]:
            tc.draw(self.screen, self.cam_x, self.cam_y)

        # Draw buildings
        for b in self.buildings:
            b.draw(self.screen, self.cam_x, self.cam_y, b is self.selected_building)

        # Draw units
        for u in self.units:
            u.draw(self.screen, self.cam_x, self.cam_y, u in self.selected_units)

        # Draw move markers
        for m in self.move_markers:
            mx = int(m[0] - self.cam_x)
            my = int(m[1] - self.cam_y)
            if 0 <= mx <= GAME_W and 0 <= my <= SCREEN_H:
                color = (0, 255, 0)
                pygame.draw.circle(self.screen, color, (mx, my), 4, 2)
                pygame.draw.line(self.screen, color, (mx-6, my-6), (mx-2, my-2), 2)
                pygame.draw.line(self.screen, color, (mx+6, my-6), (mx+2, my-2), 2)
                pygame.draw.line(self.screen, color, (mx-6, my+6), (mx-2, my+2), 2)
                pygame.draw.line(self.screen, color, (mx+6, my+6), (mx+2, my+2), 2)

        # Draw projectiles
        for p in self.projectiles:
            p.draw(self.screen, self.cam_x, self.cam_y)

        # Draw drag selection
        if self.dragging and self.drag_rect:
            drag_surf = pygame.Surface((self.drag_rect.width, self.drag_rect.height), pygame.SRCALPHA)
            drag_surf.fill((0, 255, 0, 40))
            self.screen.blit(drag_surf, (self.drag_rect.x, self.drag_rect.y))
            pygame.draw.rect(self.screen, C["select"], self.drag_rect, 1)

        # Draw help overlay
        if self.show_help:
            help_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            help_surf.fill((0, 0, 0, 200))
            self.screen.blit(help_surf, (0, 0))
            font_l = pygame.font.Font(None, 28)
            font_m = pygame.font.Font(None, 20)
            help_lines = [
                ("--- CONTROLS ---", font_l, C["sb_acc"]),
                ("", None, None),
                ("Left Click   - Select unit/building", font_m, C["white"]),
                ("Drag Left    - Select multiple units", font_m, C["white"]),
                ("Right Click  - Move / Attack enemy", font_m, C["white"]),
                ("", None, None),
                ("WASD / Arrows - Scroll map", font_m, C["gray"]),
                ("Edge Scroll  - Mouse at screen edge", font_m, C["gray"]),
                ("F1/H         - Toggle this help", font_m, C["gray"]),
                ("", None, None),
                ("--- SIDEBAR ---", font_m, C["sb_acc"]),
                ("Select CYard -> Build buttons", font_m, C["white"]),
                ("Select Barracks/WarFactory -> Train", font_m, C["white"]),
                ("", None, None),
                ("--- ECONOMY ---", font_m, C["tiberium_g"]),
                ("Harvester auto-collects Tiberium", font_m, C["white"]),
                ("Returns to Refinery for credits", font_m, C["white"]),
                ("", None, None),
                ("R: Restart    ESC: Quit", font_m, C["gray"]),
            ]
            y = 100
            for text, font, color in help_lines:
                if font is None:
                    y += 10
                    continue
                label = font.render(text, True, color)
                self.screen.blit(label, (SCREEN_W // 2 - label.get_width() // 2, y))
                y += 28

        # Draw sidebar (last = on top)
        self.sidebar.draw(self.screen, self)

        # FPS
        fps_text = pygame.font.Font(None, 14).render(f"FPS: {int(self.clock.get_fps())}", True, C["gray"])
        self.screen.blit(fps_text, (5, 5))


# ============================================================
# SOUND MANAGER
# ============================================================
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self._bg_sound = None
        self.sound_dir = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.sound_dir = os.path.join(script_dir, "sounds")
            if not os.path.isdir(self.sound_dir):
                os.mkdir(self.sound_dir)
            self._gen_sounds()
            print("SoundManager loaded:", len(self.sounds), "sounds from", self.sound_dir)
        except Exception as _e:
            print("SoundManager init error:", _e)

    def _mk(self, name, dur, func):
        path = os.path.join(self.sound_dir, name + ".wav")
        if os.path.isfile(path):
            try:
                snd = pygame.mixer.Sound(path)
                self.sounds[name] = snd
                return snd
            except:
                pass
        try:
            with wave.open(path, "w") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(22050)
                n = int(22050 * dur)
                for i in range(n):
                    t = i / 22050.0
                    s = max(-1.0, min(1.0, func(t)))
                    w.writeframes(struct.pack("<h", int(s * 32767)))
            snd = pygame.mixer.Sound(path)
            self.sounds[name] = snd
            return snd
        except Exception as e:
            print("Sound gen error for", name, ":", e)
            return None

    def _gen_sounds(self):
        self._mk("soldier_ack", 0.2, lambda t: math.sin(2*math.pi*700*t)*max(0,1-t*5)*0.4)
        self._mk("tank_ack", 0.35, lambda t: (1.0 if math.sin(2*math.pi*120*t)>0 else -1.0)*max(0,1-t*3)*0.35)
        self._mk("harv_ack", 0.25, lambda t: (2*(300*t-math.floor(300*t+0.5)))*max(0,1-t*4)*0.3)
        self._mk("gunfire", 0.08, lambda t: math.sin(t*123456)*max(0,1-t*12)*0.2)
        self._mk("cannon", 0.4, lambda t: math.sin(2*math.pi*80*t)*max(0,1-t*2.5)*0.5)
        self._mk("impact", 0.1, lambda t: math.sin(t*98765)*max(0,1-t*10)*0.25)
        self._bg_sound = self._mk("bg_music", 4.0, self._bg_func)

    def _bg_func(self, t):
        bass = math.sin(2*math.pi*55*t)*0.25
        pulse = (math.sin(2*math.pi*2*t)*0.5+0.5)*math.sin(2*math.pi*110*t)*0.15
        beat = int(t/2)&3
        perc = 0.0
        if (beat==0 or beat==2) and (t%2)<0.05:
            perc = math.sin(2*math.pi*800*(t%2)*20)*max(0,1-(t%2)*20)*0.2
        return bass+pulse+perc+math.sin(t*54321)*0.03

    def play(self, name, vol=1.0):
        if name in self.sounds:
            try:
                s = self.sounds[name]
                s.set_volume(vol)
                s.play()
            except:
                pass

    def start_music(self):
        if self._bg_sound:
            self._bg_sound.set_volume(0.3)
            self._bg_sound.play(-1)

    def stop_music(self):
        if self._bg_sound:
            self._bg_sound.stop()

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    pygame.init()
    print("Command & Conquer: Tiberian Dawn Clone")
    print("Controls:")
    print("  Left click: Select units/buildings")
    print("  Drag select: Select multiple units")
    print("  Right click: Move/Attack")
    print("  Arrow/WASD: Scroll map")
    print("  Sidebar: Build structures/train units")
    print("  R: Restart after game over")
    print("  ESC: Quit")
    game = Game()
    game.run()

