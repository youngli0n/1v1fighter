import { GAME_CONFIG } from '../config.js';

/**
 * A bullet shot by a player.
 * Travels horizontally and can be deflected by shields.
 */
export class Projectile {
  constructor(x, y, direction, isDeflected = false) {
    this.x = x;
    this.y = y;
    this.direction = direction;   // 1 = right (P1), -1 = left (P2)
    this.isDeflected = isDeflected;
  }

  get speedMultiplier() {
    return this.isDeflected ? 2.0 : 1.0;
  }

  /** Return the pixel-space rect {x,y,w,h} for rendering / collision. */
  getRect() {
    const ts = GAME_CONFIG.tile_size;
    return {
      x: Math.floor(this.x * ts),
      y: Math.floor(this.y * ts),
      w: GAME_CONFIG.projectile_size * ts,
      h: GAME_CONFIG.projectile_size * ts,
    };
  }

  /**
   * Build a list of sub-step positions along this frame's movement path.
   * Prevents fast projectiles from tunnelling through thin walls / players.
   */
  getMovementWithSubsteps(dt, maxStepSize = 0.5) {
    const distance = Math.abs(
      this.direction * GAME_CONFIG.projectile_speed * this.speedMultiplier * dt
    );

    if (distance <= maxStepSize) {
      return [
        { x: this.x, y: this.y },
        { x: this.x + this.direction * distance, y: this.y },
      ];
    }

    const numSteps = Math.ceil(distance / maxStepSize);
    const stepSize = distance / numSteps;
    const positions = [];
    for (let i = 0; i <= numSteps; i++) {
      positions.push({
        x: this.x + this.direction * stepSize * i,
        y: this.y,
      });
    }
    return positions;
  }
}
