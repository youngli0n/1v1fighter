import { GAME_CONFIG } from '../config.js';

/**
 * Simple heuristic AI that controls Player 2.
 * Ported from ai_player.py.
 */
export class AIPlayer {
  constructor(player2, player1, walls) {
    this.player2 = player2;
    this.player1 = player1;
    this.walls = walls;
    this.lastShotTime = 0;
    this.shotCooldown = 1.0 / GAME_CONFIG.fire_rate;
  }

  update(dt, currentTime) {
    const p1 = this.player1;
    const p2 = this.player2;

    const dx = p1.x - p2.x;
    const dy = p1.y - p2.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // ── Movement ─────────────────────────────────────────────
    if (!p2.shieldActive) {
      const targetX = GAME_CONFIG.tiles_width / 2;
      const targetY = p1.y; // mirror player 1 vertically

      let moveX = 0;
      let moveY = 0;
      if (p2.x > targetX) moveX = -1;
      else if (p2.x < targetX) moveX = 1;
      if (p2.y > targetY) moveY = -1;
      else if (p2.y < targetY) moveY = 1;

      p2.move(
        moveX * GAME_CONFIG.player_speed,
        moveY * GAME_CONFIG.player_speed,
        dt, currentTime, p1, this.walls,
      );
    }

    // ── Shooting ─────────────────────────────────────────────
    if (!p2.shieldActive &&
        distance < GAME_CONFIG.tiles_width / 2 &&
        currentTime - this.lastShotTime > this.shotCooldown) {
      p2.shoot(currentTime);
      this.lastShotTime = currentTime;
    }

    // ── Shield ───────────────────────────────────────────────
    p2.shieldActive = (
      p1.projectiles.length > 0 &&
      distance < GAME_CONFIG.tiles_width / 3
    );
  }
}
