import { GAME_CONFIG, COLORS } from '../config.js';

/**
 * Base class for all collectible power-ups.
 */
export class Collectible {
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.color = color;
    this.size = GAME_CONFIG.collectible_size;
  }

  getRect() {
    const ts = GAME_CONFIG.tile_size;
    return {
      x: Math.floor(this.x * ts),
      y: Math.floor(this.y * ts),
      w: Math.floor(this.size * ts),
      h: Math.floor(this.size * ts),
    };
  }

  /** Override in subclasses. */
  applyEffect(_player, _currentTime, _otherPlayer) {}
}

// ── Speed Boost (green) — speeds up the collector ──────────────

export class SpeedBoostCollectible extends Collectible {
  constructor(x, y) {
    super(x, y, COLORS.speed_boost);
  }

  applyEffect(player, currentTime) {
    if (currentTime < player.speedupEndTime) {
      const remaining = player.speedupEndTime - currentTime;
      player.speedupEndTime = currentTime + remaining + GAME_CONFIG.speed_boost_duration;
    } else {
      player.speedupEndTime = currentTime + GAME_CONFIG.speed_boost_duration;
    }
  }
}

// ── Speed Debuff (orange) — slows the opponent ─────────────────

export class SpeedDebuffCollectible extends Collectible {
  constructor(x, y) {
    super(x, y, COLORS.speed_debuff);
  }

  applyEffect(_player, currentTime, otherPlayer) {
    if (!otherPlayer) return;
    if (currentTime < otherPlayer.slowEndTime) {
      const remaining = otherPlayer.slowEndTime - currentTime;
      otherPlayer.slowEndTime = currentTime + remaining + GAME_CONFIG.speed_debuff_duration;
    } else {
      otherPlayer.slowEndTime = currentTime + GAME_CONFIG.speed_debuff_duration;
    }
  }
}

// ── Collectible generation ─────────────────────────────────────

function findValidPositions(walls, existing, p1Pos, p2Pos, side) {
  const valid = [];
  const cfg = GAME_CONFIG;
  const centerX = cfg.tiles_width / 2;

  const minX = side === 'left'
    ? cfg.min_distance_from_border
    : centerX + cfg.min_distance_from_center_line;
  const maxX = side === 'left'
    ? centerX - cfg.min_distance_from_center_line
    : cfg.tiles_width - cfg.collectible_size - cfg.min_distance_from_border;

  const step = cfg.collectible_size;

  for (let xi = Math.floor(minX / step); xi < Math.floor(maxX / step); xi++) {
    const xPos = xi * step;
    for (let yi = Math.floor(cfg.min_distance_from_border / step);
         yi < Math.floor((cfg.tiles_height - cfg.collectible_size - cfg.min_distance_from_border) / step);
         yi++) {
      const yPos = yi * step;

      // Check wall overlap (simple AABB in tile space)
      const cs = cfg.collectible_size;
      let bad = false;
      for (const w of walls) {
        const wb = w.getTileBounds();
        if (xPos < wb.maxX && xPos + cs > wb.minX && yPos < wb.maxY && yPos + cs > wb.minY) {
          bad = true;
          break;
        }
      }
      if (bad) continue;

      // Distance from player starts
      for (const pos of [p1Pos, p2Pos]) {
        if (pos) {
          const dx = xPos - pos.x;
          const dy = yPos - pos.y;
          if (Math.sqrt(dx * dx + dy * dy) < cfg.min_distance_from_player) { bad = true; break; }
        }
      }
      if (bad) continue;

      // Distance from existing collectibles
      for (const c of existing) {
        const dx = xPos - c.x;
        const dy = yPos - c.y;
        if (Math.sqrt(dx * dx + dy * dy) < cfg.min_distance_between_collectibles) { bad = true; break; }
      }
      if (bad) continue;

      valid.push({ x: xPos, y: yPos });
    }
  }
  return valid;
}

function randomCollectible(positions) {
  if (positions.length === 0) return null;
  const { x, y } = positions[Math.floor(Math.random() * positions.length)];
  return Math.random() < 0.5
    ? new SpeedBoostCollectible(x, y)
    : new SpeedDebuffCollectible(x, y);
}

export function generateCollectibles(walls, count, p1Pos, p2Pos) {
  if (!GAME_CONFIG.collectibles_enabled) return [];

  const collectibles = [];
  const centerX = GAME_CONFIG.tiles_width / 2;
  const perSide = Math.floor(count / 2);

  // Left side
  for (let i = 0; i < perSide; i++) {
    const positions = findValidPositions(walls, collectibles, p1Pos, p2Pos, 'left');
    const c = randomCollectible(positions);
    if (c && c.x < centerX) collectibles.push(c);
  }

  // Right side
  for (let i = 0; i < perSide; i++) {
    const positions = findValidPositions(walls, collectibles, p1Pos, p2Pos, 'right');
    const c = randomCollectible(positions);
    if (c && c.x >= centerX) collectibles.push(c);
  }

  return collectibles;
}
