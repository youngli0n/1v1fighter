import { GAME_CONFIG, COLORS } from '../config.js';
import { Projectile } from './Projectile.js';

/**
 * Represents one player in the game.
 * Ported from player.py — every speed/effect formula matches the Python original.
 */
export class Player {
  /**
   * @param {number} x  Starting tile X
   * @param {number} y  Starting tile Y
   * @param {number} color  Hex colour (e.g. 0xff0000)
   */
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.color = color;

    this.startX = x;
    this.startY = y;

    // Effects
    this.slowEndTime = 0;
    this.speedupEndTime = 0;

    // Shooting
    this.lastShotTime = 0;
    this.projectiles = [];

    // Shield
    this.shieldActive = false;
    this.shieldBoosts = []; // { endTime, amount }
  }

  // ── Helpers ──────────────────────────────────────────────────

  reset() {
    this.x = this.startX;
    this.y = this.startY;
    this.slowEndTime = 0;
    this.speedupEndTime = 0;
    this.lastShotTime = 0;
    this.projectiles = [];
    this.shieldActive = false;
    this.shieldBoosts = [];
  }

  isSlowed(t) { return t < this.slowEndTime; }
  isSpeedup(t) { return t < this.speedupEndTime; }

  /**
   * Exact port of get_total_speed_multiplier from player.py.
   * Handles slow regen, speedup decay, and shield boost stacking.
   */
  getTotalSpeedMultiplier(t) {
    // Prune expired shield boosts and sum active ones
    this.shieldBoosts = this.shieldBoosts.filter((b) => t < b.endTime);
    let shieldBoost = this.shieldBoosts.reduce((sum, b) => sum + b.amount, 0);
    shieldBoost = Math.min(shieldBoost, GAME_CONFIG.shield_boost_max);

    // Temporary effect (slow or speedup)
    let tempEffect;
    if (this.isSlowed(t)) {
      const remaining = this.slowEndTime - t;
      const sf = GAME_CONFIG.slow_factor;
      tempEffect = sf + (1.0 - sf) * (1.0 - remaining / GAME_CONFIG.slow_duration);
    } else if (this.isSpeedup(t)) {
      const remaining = this.speedupEndTime - t;
      const spf = GAME_CONFIG.speedup_factor;
      tempEffect = 1.0 + (spf - 1.0) * (remaining / GAME_CONFIG.speedup_duration);
    } else {
      tempEffect = 1.0;
    }

    let totalSpeed = 1.0 + shieldBoost;
    if (tempEffect < 1.0) {
      totalSpeed *= tempEffect;          // slow is multiplicative
    } else {
      totalSpeed = Math.min(totalSpeed + (tempEffect - 1.0), 1.5);
    }
    return totalSpeed;
  }

  canShoot(t) {
    if (this.shieldActive) return false;
    const mult = this.getTotalSpeedMultiplier(t);
    return t - this.lastShotTime >= 1.0 / (GAME_CONFIG.fire_rate * mult);
  }

  applyEffect(type, duration, t) {
    if (type === 'slow') {
      if (!this.isSlowed(t)) this.slowEndTime = t + duration;
    } else if (type === 'speedup') {
      if (!this.isSpeedup(t)) this.speedupEndTime = t + duration;
    } else if (type === 'block') {
      this.shieldBoosts.push({
        endTime: t + GAME_CONFIG.shield_boost_duration,
        amount: GAME_CONFIG.shield_boost_amount,
      });
    }
  }

  // ── Shooting ─────────────────────────────────────────────────

  shoot(t) {
    if (!this.canShoot(t)) return;
    const dir = this.color === COLORS.player1 ? 1 : -1;
    const px = this.x + dir;
    this.projectiles.push(new Projectile(px, this.y, dir));
    this.lastShotTime = t;
  }

  // ── Movement ─────────────────────────────────────────────────

  move(dx, dy, dt, t, otherPlayer, walls) {
    if (this.shieldActive) dx = 0;
    if (dx === 0 && dy === 0) return;

    const mult = this.getTotalSpeedMultiplier(t);
    const newX = this.x + dx * dt * mult;
    const newY = this.y + dy * dt * mult;

    // Bounds check
    if (newX < 0 || newX > GAME_CONFIG.tiles_width - 1) return;
    if (newY < 0 || newY > GAME_CONFIG.tiles_height - 1) return;

    // Other-player collision (1.1 tile buffer)
    if (Math.abs(newX - otherPlayer.x) < 1.1 &&
        Math.abs(newY - otherPlayer.y) < 1.1) return;

    // Wall collision (pixel-space AABB, matching Python int() truncation)
    const ts = GAME_CONFIG.tile_size;
    const pr = { x: Math.floor(newX * ts), y: Math.floor(newY * ts), w: ts, h: ts };
    if (walls) {
      for (const wall of walls) {
        const wr = wall.getRect();
        if (pr.x < wr.x + wr.w && pr.x + pr.w > wr.x &&
            pr.y < wr.y + wr.h && pr.y + pr.h > wr.y) {
          return; // blocked
        }
      }
    }

    this.x = newX;
    this.y = newY;
  }

  // ── Projectile updates ───────────────────────────────────────

  updateProjectiles(dt, otherPlayer, t, walls) {
    const toRemove = [];

    for (const proj of this.projectiles) {
      const path = proj.getMovementWithSubsteps(dt, 0.5);
      let collided = false;

      for (let i = 1; i < path.length; i++) {
        proj.x = path[i].x;

        // Out-of-bounds
        if (proj.x < 0 || proj.x > GAME_CONFIG.tiles_width ||
            proj.y < 0 || proj.y > GAME_CONFIG.tiles_height) {
          collided = true;
          break;
        }

        const ts = GAME_CONFIG.tile_size;
        const prRect = proj.getRect();

        // Wall hit
        if (walls) {
          let hitWall = false;
          for (const wall of walls) {
            const wr = wall.getRect();
            if (prRect.x < wr.x + wr.w && prRect.x + prRect.w > wr.x &&
                prRect.y < wr.y + wr.h && prRect.y + prRect.h > wr.y) {
              hitWall = true;
              break;
            }
          }
          if (hitWall) { collided = true; break; }
        }

        // Player hit
        const opRect = {
          x: Math.floor(otherPlayer.x * ts),
          y: Math.floor(otherPlayer.y * ts),
          w: ts,
          h: ts,
        };
        if (prRect.x < opRect.x + opRect.w && prRect.x + prRect.w > opRect.x &&
            prRect.y < opRect.y + opRect.h && prRect.y + prRect.h > opRect.y) {
          collided = true;

          if (otherPlayer.shieldActive) {
            // Deflect
            otherPlayer.applyEffect('block', GAME_CONFIG.shield_boost_duration, t);
            const deflectDir = -proj.direction;
            const deflected = new Projectile(
              otherPlayer.x + (deflectDir === 1 ? 1 : -1),
              otherPlayer.y,
              deflectDir,
              true,
            );
            otherPlayer.projectiles.push(deflected);
          } else {
            // Hit effects
            otherPlayer.applyEffect('slow', GAME_CONFIG.slow_duration, t);
            this.applyEffect('speedup', GAME_CONFIG.speedup_duration, t);
          }
          break;
        }
      }

      if (collided) {
        toRemove.push(proj);
      } else {
        // Move to final position
        proj.x = path[path.length - 1].x;
      }
    }

    for (const p of toRemove) {
      const idx = this.projectiles.indexOf(p);
      if (idx !== -1) this.projectiles.splice(idx, 1);
    }
  }

  // ── Progress ─────────────────────────────────────────────────

  getProgress() {
    const center = GAME_CONFIG.tiles_width / 2;
    if (this.x < center) {
      // Player 1 — moving right toward center
      const dist = center - (this.x + 1);
      return ((center - dist) / center) * 100;
    } else {
      // Player 2 — moving left toward center
      const dist = this.x - center;
      return ((center - dist) / center) * 100;
    }
  }
}
