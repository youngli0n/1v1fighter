/**
 * On-screen virtual joystick for the RIGHT side of the screen.
 * The player drags their right thumb to move.
 */
export class VirtualJoystick {
  /**
   * @param {Phaser.Scene} scene
   * @param {number} x  Centre X of the joystick base (pixels)
   * @param {number} y  Centre Y of the joystick base (pixels)
   * @param {number} radius  Outer radius of the joystick base (pixels)
   */
  constructor(scene, x, y, radius) {
    this.scene = scene;
    this.baseX = x;
    this.baseY = y;
    this.radius = radius;
    this.knobRadius = radius * 0.4;

    /** Normalised direction: -1 … 1 on each axis */
    this.dx = 0;
    this.dy = 0;

    this.active = false;
    this.pointerId = null;

    // Graphics layer (drawn above game, below HUD text)
    this.gfx = scene.add.graphics().setDepth(100);
    this.draw();

    // Input listeners
    scene.input.on('pointerdown', this.onDown, this);
    scene.input.on('pointermove', this.onMove, this);
    scene.input.on('pointerup', this.onUp, this);
  }

  // ── Pointer handlers ─────────────────────────────────────────

  onDown(pointer) {
    // Only capture touches on the RIGHT half of the screen
    if (pointer.x < this.scene.scale.width * 0.45) return;
    if (this.active) return; // already tracking a finger

    this.active = true;
    this.pointerId = pointer.id;
    this.updateKnob(pointer.x, pointer.y);
  }

  onMove(pointer) {
    if (!this.active || pointer.id !== this.pointerId) return;
    this.updateKnob(pointer.x, pointer.y);
  }

  onUp(pointer) {
    if (pointer.id !== this.pointerId) return;
    this.active = false;
    this.pointerId = null;
    this.dx = 0;
    this.dy = 0;
    this.draw();
  }

  // ── Internal ─────────────────────────────────────────────────

  updateKnob(px, py) {
    let offX = px - this.baseX;
    let offY = py - this.baseY;
    const dist = Math.sqrt(offX * offX + offY * offY);

    if (dist > this.radius) {
      offX = (offX / dist) * this.radius;
      offY = (offY / dist) * this.radius;
    }

    this.dx = offX / this.radius;
    this.dy = offY / this.radius;
    this.draw(this.baseX + offX, this.baseY + offY);
  }

  draw(knobX, knobY) {
    this.gfx.clear();

    // Base
    this.gfx.fillStyle(0x000000, 0.12);
    this.gfx.fillCircle(this.baseX, this.baseY, this.radius);
    this.gfx.lineStyle(2, 0x000000, 0.2);
    this.gfx.strokeCircle(this.baseX, this.baseY, this.radius);

    // Knob
    const kx = knobX ?? this.baseX;
    const ky = knobY ?? this.baseY;
    this.gfx.fillStyle(0x000000, 0.25);
    this.gfx.fillCircle(kx, ky, this.knobRadius);
  }

  /** Update position when screen resizes */
  reposition(x, y, radius) {
    this.baseX = x;
    this.baseY = y;
    this.radius = radius;
    this.knobRadius = radius * 0.4;
    this.draw();
  }

  destroy() {
    this.scene.input.off('pointerdown', this.onDown, this);
    this.scene.input.off('pointermove', this.onMove, this);
    this.scene.input.off('pointerup', this.onUp, this);
    this.gfx.destroy();
  }
}
