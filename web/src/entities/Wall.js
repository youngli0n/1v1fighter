import { GAME_CONFIG } from '../config.js';

/**
 * A wall that blocks players and projectiles.
 * Position is given as (x = left edge, y = bottom edge) in tiles.
 */
export class Wall {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.width = GAME_CONFIG.wall_width;
    this.height = GAME_CONFIG.wall_height;
  }

  /** Pixel-space rect for rendering / collision. */
  getRect() {
    const ts = GAME_CONFIG.tile_size;
    return {
      x: Math.floor(this.x * ts),
      y: Math.floor((this.y - this.height) * ts),
      w: Math.floor(this.width * ts),
      h: Math.floor(this.height * ts),
    };
  }

  /** Tile-space bounds (minX, minY, maxX, maxY). */
  getTileBounds() {
    return {
      minX: this.x,
      minY: this.y - this.height,
      maxX: this.x + this.width,
      maxY: this.y,
    };
  }

  overlaps(other) {
    const a = this.getTileBounds();
    const b = other.getTileBounds();
    return !(a.maxX <= b.minX || a.minX >= b.maxX ||
             a.maxY <= b.minY || a.minY >= b.maxY);
  }
}

// ── Wall generation ────────────────────────────────────────────

export function generateWalls() {
  const walls = [];
  if (!GAME_CONFIG.walls_enabled) return walls;

  const centerX = GAME_CONFIG.tiles_width / 2;
  const p1StartX = 0;
  const p1StartY = GAME_CONFIG.tiles_height / 2 - 0.5;

  for (let wi = 0; wi < GAME_CONFIG.num_walls_per_side; wi++) {
    let placed = false;
    for (let attempts = 0; attempts < 100 && !placed; attempts++) {
      const x = Math.random() * (centerX - GAME_CONFIG.wall_width - 1 - 2) + 2;
      const y = Math.random() * (GAME_CONFIG.tiles_height - 0.5 - GAME_CONFIG.wall_height) + GAME_CONFIG.wall_height;

      const temp = new Wall(x, y);

      // Min distance check
      let tooClose = false;
      for (const w of walls) {
        const dx = (x + GAME_CONFIG.wall_width / 2) - (w.x + w.width / 2);
        const dy = (y - GAME_CONFIG.wall_height / 2) - (w.y - w.height / 2);
        if (Math.sqrt(dx * dx + dy * dy) < GAME_CONFIG.wall_min_distance) {
          tooClose = true;
          break;
        }
      }
      if (tooClose) continue;

      // Overlap check
      if (walls.some((w) => temp.overlaps(w))) continue;

      // Player start zone check
      if (Math.abs(x - p1StartX) < 1.5 && Math.abs(y - p1StartY) < 1.5) continue;

      // Place wall + mirrored copy
      walls.push(new Wall(x, y));
      const mirroredX = GAME_CONFIG.tiles_width - x - GAME_CONFIG.wall_width;
      walls.push(new Wall(mirroredX, y));
      placed = true;
    }
  }
  return walls;
}
