/**
 * On-screen SHOOT and SHIELD buttons on the LEFT side of the screen.
 * Left thumb presses shoot (tap) or holds shield.
 */
export class ActionButtons {
  /**
   * @param {Phaser.Scene} scene
   * @param {number} centreX   Horizontal centre of the button column (px)
   * @param {number} topY      Top of the upper button (px)
   * @param {number} btnW      Button width (px)
   * @param {number} btnH      Button height (px)
   * @param {number} gap       Vertical gap between buttons (px)
   */
  constructor(scene, centreX, topY, btnW, btnH, gap) {
    this.scene = scene;

    this.btnW = btnW;
    this.btnH = btnH;
    const x = centreX - btnW / 2;

    // Button rects (pixel coords)
    this.shootRect = { x, y: topY, w: btnW, h: btnH };
    this.shieldRect = { x, y: topY + btnH + gap, w: btnW, h: btnH };

    /** True for one frame when the shoot button is tapped */
    this.shootPressed = false;
    /** True while the shield button is held */
    this.shieldHeld = false;

    // Track which pointer is on which button
    this._shootPointerId = null;
    this._shieldPointerId = null;

    this.gfx = scene.add.graphics().setDepth(100);
    this.draw();

    scene.input.on('pointerdown', this.onDown, this);
    scene.input.on('pointerup', this.onUp, this);
  }

  // ── Pointer handlers ─────────────────────────────────────────

  onDown(pointer) {
    // Only capture touches on the LEFT half of the screen
    if (pointer.x > this.scene.scale.width * 0.55) return;

    if (this._hitTest(pointer, this.shootRect) && this._shootPointerId === null) {
      this._shootPointerId = pointer.id;
      this.shootPressed = true;
      this.draw();
    } else if (this._hitTest(pointer, this.shieldRect) && this._shieldPointerId === null) {
      this._shieldPointerId = pointer.id;
      this.shieldHeld = true;
      this.draw();
    }
  }

  onUp(pointer) {
    if (pointer.id === this._shootPointerId) {
      this._shootPointerId = null;
      this.draw();
    }
    if (pointer.id === this._shieldPointerId) {
      this._shieldPointerId = null;
      this.shieldHeld = false;
      this.draw();
    }
  }

  _hitTest(pointer, rect) {
    return (
      pointer.x >= rect.x && pointer.x <= rect.x + rect.w &&
      pointer.y >= rect.y && pointer.y <= rect.y + rect.h
    );
  }

  /** Call once per frame to reset single-frame flags. */
  consumeShoot() {
    const v = this.shootPressed;
    this.shootPressed = false;
    return v;
  }

  // ── Drawing ──────────────────────────────────────────────────

  draw() {
    this.gfx.clear();

    // Shoot button
    const shootAlpha = this._shootPointerId !== null ? 0.35 : 0.18;
    this.gfx.fillStyle(0xff0000, shootAlpha);
    this.gfx.fillRoundedRect(this.shootRect.x, this.shootRect.y, this.btnW, this.btnH, 12);
    this.gfx.lineStyle(2, 0xff0000, 0.4);
    this.gfx.strokeRoundedRect(this.shootRect.x, this.shootRect.y, this.btnW, this.btnH, 12);

    // Shield button
    const shieldAlpha = this.shieldHeld ? 0.35 : 0.18;
    this.gfx.fillStyle(0x0088ff, shieldAlpha);
    this.gfx.fillRoundedRect(this.shieldRect.x, this.shieldRect.y, this.btnW, this.btnH, 12);
    this.gfx.lineStyle(2, 0x0088ff, 0.4);
    this.gfx.strokeRoundedRect(this.shieldRect.x, this.shieldRect.y, this.btnW, this.btnH, 12);
  }

  /** Add text labels — call after creation so we can use Phaser text objects. */
  addLabels() {
    const style = { fontSize: '16px', fontFamily: 'Arial', color: '#000', fontStyle: 'bold' };
    this.scene.add.text(
      this.shootRect.x + this.btnW / 2,
      this.shootRect.y + this.btnH / 2,
      'SHOOT', { ...style, color: '#cc0000' },
    ).setOrigin(0.5).setDepth(101);

    this.scene.add.text(
      this.shieldRect.x + this.btnW / 2,
      this.shieldRect.y + this.btnH / 2,
      'SHIELD', { ...style, color: '#0066cc' },
    ).setOrigin(0.5).setDepth(101);
  }

  destroy() {
    this.scene.input.off('pointerdown', this.onDown, this);
    this.scene.input.off('pointerup', this.onUp, this);
    this.gfx.destroy();
  }
}
