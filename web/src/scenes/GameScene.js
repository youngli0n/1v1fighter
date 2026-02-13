import Phaser from 'phaser';
import { GAME_CONFIG, COLORS } from '../config.js';
import { Player } from '../entities/Player.js';
import { generateWalls } from '../entities/Wall.js';
import { generateCollectibles } from '../entities/Collectible.js';
import { GameState } from '../state/GameState.js';
import { AIPlayer } from '../ai/AIPlayer.js';
import { VirtualJoystick } from '../ui/VirtualJoystick.js';
import { ActionButtons } from '../ui/ActionButtons.js';
import { StatsPanel } from '../ui/StatsPanel.js';

/**
 * Main game scene — handles every state:
 *   instructions → countdown → playing → round_over / match_over
 *
 * Everything is drawn here rather than switching Phaser scenes,
 * which keeps the port close to the original Python loop.
 */
export class GameScene extends Phaser.Scene {
  constructor() {
    super('GameScene');
  }

  /* ───────── lifecycle ───────── */

  init(data) {
    this.newMatch = data?.newMatch !== false;
  }

  create() {
    const W = GAME_CONFIG.tiles_width;
    const H = GAME_CONFIG.tiles_height;

    // ── Match setup ──────────────────────────────────────────
    if (this.newMatch) {
      this.gameState = new GameState();
      this.walls = generateWalls();
      this.player1 = new Player(0, Math.floor(H / 2) - 0.5, COLORS.player1);
      this.player2 = new Player(W - 1, Math.floor(H / 2) - 0.5, COLORS.player2);
      const p1 = { x: this.player1.startX, y: this.player1.startY };
      const p2 = { x: this.player2.startX, y: this.player2.startY };
      this.collectibles = generateCollectibles(
        this.walls, GAME_CONFIG.num_collectibles_per_match, p1, p2,
      );
    } else {
      // continuing match — players reset, walls/collectibles/gameState persist
      this.player1.reset();
      this.player2.reset();
    }

    this.ai = new AIPlayer(this.player2, this.player1, this.walls);
    this.gameOver = false;
    this.winner = null;

    // ── Graphics layers ──────────────────────────────────────
    this.gameGfx = this.add.graphics().setDepth(0);
    this.overlayGfx = this.add.graphics().setDepth(200);
    this.overlayTexts = [];

    // ── Touch controls ───────────────────────────────────────
    const ts = GAME_CONFIG.tile_size;
    const boardH = H * ts;
    const sw = this.scale.width;

    // Joystick — right side, vertically centered in the game board
    const jRadius = Math.min(70, sw * 0.07);
    this.joystick = new VirtualJoystick(
      this,
      sw - jRadius - 30,      // x: near right edge
      boardH - jRadius - 20,  // y: near bottom of board
      jRadius,
    );

    // Buttons — left side
    const btnW = Math.min(90, sw * 0.09);
    const btnH = Math.min(60, boardH * 0.14);
    const gap = 12;
    const btnCentreX = 30 + btnW / 2;
    const btnTopY = boardH - btnH * 2 - gap - 20;
    this.actionButtons = new ActionButtons(this, btnCentreX, btnTopY, btnW, btnH, gap);
    this.actionButtons.addLabels();

    // Stats panel
    this.statsPanel = new StatsPanel(this);

    // ── State machine ────────────────────────────────────────
    this._setState('instructions');

    // ── Keyboard fallback (for desktop testing) ──────────────
    this.keys = this.input.keyboard.addKeys({
      up: 'W', down: 'S', left: 'A', right: 'D',
      shoot: 'V', shield: 'B',
    });

    // ── Tap-to-advance for overlay states ────────────────────
    this.input.on('pointerdown', (pointer) => {
      if (this.state === 'playing' || this.state === 'countdown') return;
      // small debounce so you don't accidentally skip screens
      if (Date.now() - this.stateEnteredAt < 600) return;
      this._advanceOverlay();
    });
  }

  /* ───────── update loop ───────── */

  update(_time, delta) {
    const dt = delta / 1000;
    const t = Date.now() / 1000;

    // Countdown
    if (this.state === 'countdown') {
      if (this.gameState.updateCountdown(t)) {
        this._setState('playing');
      }
      this._drawCountdown();
    }

    // Gameplay
    if (this.state === 'playing') {
      this._updateGameplay(dt, t);
    }

    // Render game board every frame (underneath overlays)
    this._drawBoard(t);

    // Stats panel
    this.statsPanel.update(this.player1, this.player2, t);
  }

  /* ───────── state machine helpers ───────── */

  _setState(s) {
    // clean up overlay texts from previous state
    for (const txt of this.overlayTexts) txt.destroy();
    this.overlayTexts = [];
    this.overlayGfx.clear();

    this.state = s;
    this.stateEnteredAt = Date.now();

    if (s === 'instructions') this._buildInstructionsOverlay();
    if (s === 'round_over') this._buildRoundOverlay();
    if (s === 'match_over') this._buildMatchOverlay();
  }

  _advanceOverlay() {
    if (this.state === 'instructions') {
      this.gameState.resetRound();
      this._setState('countdown');
    } else if (this.state === 'round_over') {
      this.player1.reset();
      this.player2.reset();
      // Regenerate walls and collectibles for the new round
      this.walls = generateWalls();
      const p1 = { x: this.player1.startX, y: this.player1.startY };
      const p2 = { x: this.player2.startX, y: this.player2.startY };
      this.collectibles = generateCollectibles(
        this.walls, GAME_CONFIG.num_collectibles_per_match, p1, p2,
      );
      this.ai = new AIPlayer(this.player2, this.player1, this.walls);
      this.gameOver = false;
      this.winner = null;
      this.gameState.resetRound();
      this._setState('countdown');
    } else if (this.state === 'match_over') {
      this.scene.restart({ newMatch: true });
    }
  }

  /* ───────── gameplay ───────── */

  _updateGameplay(dt, t) {
    const p1 = this.player1;
    const p2 = this.player2;

    // ── Player 1 input (touch + keyboard fallback) ──────────
    let dx = this.joystick.dx * GAME_CONFIG.player_speed;
    let dy = this.joystick.dy * GAME_CONFIG.player_speed;

    // Keyboard override when joystick idle
    if (dx === 0 && dy === 0) {
      dx = ((this.keys.right.isDown ? 1 : 0) - (this.keys.left.isDown ? 1 : 0)) * GAME_CONFIG.player_speed;
      dy = ((this.keys.down.isDown ? 1 : 0) - (this.keys.up.isDown ? 1 : 0)) * GAME_CONFIG.player_speed;
    }

    p1.move(dx, dy, dt, t, p2, this.walls);

    // Shield (touch or keyboard)
    p1.shieldActive = this.actionButtons.shieldHeld || this.keys.shield.isDown;

    // Shoot (touch or keyboard)
    if (this.actionButtons.consumeShoot() || Phaser.Input.Keyboard.JustDown(this.keys.shoot)) {
      p1.shoot(t);
    }

    // ── AI (Player 2) ───────────────────────────────────────
    this.ai.update(dt, t);

    // ── Projectiles ─────────────────────────────────────────
    p1.updateProjectiles(dt, p2, t, this.walls);
    p2.updateProjectiles(dt, p1, t, this.walls);

    // ── Collectibles ────────────────────────────────────────
    for (let i = this.collectibles.length - 1; i >= 0; i--) {
      const c = this.collectibles[i];
      const ts = GAME_CONFIG.tile_size;

      // simple AABB between collectible and each player (pixel space)
      const cr = c.getRect();
      for (const [player, other] of [[p1, p2], [p2, p1]]) {
        const pr = {
          x: Math.floor(player.x * ts), y: Math.floor(player.y * ts), w: ts, h: ts,
        };
        if (cr.x < pr.x + pr.w && cr.x + cr.w > pr.x &&
            cr.y < pr.y + pr.h && cr.y + cr.h > pr.y) {
          c.applyEffect(player, t, other);
          this.collectibles.splice(i, 1);
          break;
        }
      }
    }

    // ── Win check ───────────────────────────────────────────
    if (p1.getProgress() >= 100) {
      this.gameOver = true;
      this.winner = p1;
      this.gameState.recordRoundWin(1);
    } else if (p2.getProgress() >= 100) {
      this.gameOver = true;
      this.winner = p2;
      this.gameState.recordRoundWin(2);
    }

    if (this.gameOver) {
      this._setState(this.gameState.matchOver ? 'match_over' : 'round_over');
    }
  }

  /* ───────── rendering ───────── */

  _drawBoard(t) {
    const g = this.gameGfx;
    g.clear();

    const ts = GAME_CONFIG.tile_size;
    const W = GAME_CONFIG.tiles_width;
    const H = GAME_CONFIG.tiles_height;

    // Background
    g.fillStyle(COLORS.background, 1);
    g.fillRect(0, 0, W * ts, H * ts);

    // Center line
    const cx = (W / 2) * ts;
    g.lineStyle(1, COLORS.center_line, 1);
    g.lineBetween(cx, 0, cx, H * ts);

    // Walls
    for (const wall of this.walls) {
      const r = wall.getRect();
      g.fillStyle(COLORS.wall, 1);
      g.fillRect(r.x, r.y, r.w, r.h);
    }

    // Collectibles
    for (const c of this.collectibles) {
      const r = c.getRect();
      g.fillStyle(c.color, 1);
      g.fillRect(r.x, r.y, r.w, r.h);
    }

    // Players (+ shield outline)
    for (const p of [this.player1, this.player2]) {
      const px = Math.floor(p.x * ts);
      const py = Math.floor(p.y * ts);
      if (p.shieldActive) {
        g.lineStyle(2, p.color, 1);
        g.strokeRect(px - 2, py - 2, ts + 4, ts + 4);
      }
      g.fillStyle(p.color, 1);
      g.fillRect(px, py, ts, ts);
    }

    // Projectiles
    for (const p of [...this.player1.projectiles, ...this.player2.projectiles]) {
      const r = p.getRect();
      g.fillStyle(COLORS.projectile, 1);
      g.fillRect(r.x, r.y, r.w, r.h);
    }
  }

  /* ─── overlay builders ─── */

  _buildInstructionsOverlay() {
    const g = this.overlayGfx;
    const sw = this.scale.width;
    const sh = this.scale.height;

    g.fillStyle(0xffffff, 0.92);
    g.fillRect(0, 0, sw, sh);

    const cx = sw / 2;
    const baseSize = Math.min(24, sh / 20);
    let y = sh * 0.08;

    const title = this._overlayText(cx, y, 'How to Play', baseSize * 1.6, '#000', true);
    y += baseSize * 2.5;

    const lines = [
      { t: '1. Race to the centre line first!', style: 'heading' },
      { t: 'Reach 100% progress to win the round.', style: 'body' },
      { t: '2. Use walls for cover', style: 'heading' },
      { t: 'Gray walls block bullets — hide behind them.', style: 'body' },
      { t: '3. Touch controls', style: 'heading' },
      { t: 'Right thumb: drag joystick to MOVE', style: 'body' },
      { t: 'Left thumb: SHOOT or hold SHIELD', style: 'body' },
      { t: '4. Getting hit slows you down', style: 'heading' },
      { t: `Speed drops to ${GAME_CONFIG.slow_factor * 100}% for ${GAME_CONFIG.slow_duration}s. Attacker speeds up!`, style: 'body' },
      { t: '5. Blocking gives a speed boost', style: 'heading' },
      { t: `Each block: +${GAME_CONFIG.shield_boost_amount * 100}% for ${GAME_CONFIG.shield_boost_duration}s`, style: 'body' },
      { t: `6. Win ${GAME_CONFIG.rounds_to_win} rounds to win the match`, style: 'heading' },
    ];

    for (const { t: text, style } of lines) {
      if (style === 'heading') y += baseSize * 0.6;
      const size = style === 'heading' ? baseSize * 1.1 : baseSize * 0.9;
      this._overlayText(sw * 0.08, y, text, size, '#000');
      y += size * 1.4;
    }

    y = sh * 0.88;
    this._overlayText(cx, y, 'Tap anywhere to start', baseSize * 1.2, '#444', true);
  }

  _buildRoundOverlay() {
    const g = this.overlayGfx;
    const sw = this.scale.width;
    const sh = this.scale.height;

    g.fillStyle(0xffffff, 0.95);
    g.fillRect(0, 0, sw, sh);

    const cx = sw / 2;
    const baseSize = Math.min(28, sh / 16);
    const winnerNum = this.winner === this.player1 ? 1 : 2;
    const winnerHex = this.winner === this.player1 ? '#cc0000' : '#0000cc';
    let y = sh * 0.15;

    this._overlayText(cx, y, `Player ${winnerNum} Wins Round ${this.gameState.currentRound - 1}!`, baseSize * 1.6, winnerHex, true);
    y += baseSize * 3;
    this._overlayText(cx, y, `Match Score: ${this.gameState.getMatchScore()}`, baseSize, '#000', true);

    y += baseSize * 2;
    for (const [p, num] of [[this.player1, 1], [this.player2, 2]]) {
      const t = Date.now() / 1000;
      this._overlayText(cx, y, `Player ${num}:`, baseSize * 0.9, '#000', true);
      y += baseSize * 1.2;
      this._overlayText(cx, y, `Speed ${Math.round(p.getTotalSpeedMultiplier(t) * 100)}%  |  Progress ${Math.min(100, Math.round(p.getProgress()))}%`, baseSize * 0.8, '#555', true);
      y += baseSize * 1.6;
    }

    this._overlayText(cx, sh * 0.88, 'Tap to start next round', baseSize, '#444', true);
  }

  _buildMatchOverlay() {
    const g = this.overlayGfx;
    const sw = this.scale.width;
    const sh = this.scale.height;

    g.fillStyle(0xffffff, 0.95);
    g.fillRect(0, 0, sw, sh);

    const cx = sw / 2;
    const baseSize = Math.min(28, sh / 16);
    const winnerNum = this.winner === this.player1 ? 1 : 2;
    const winnerHex = this.winner === this.player1 ? '#cc0000' : '#0000cc';
    let y = sh * 0.12;

    this._overlayText(cx, y, `Player ${winnerNum} Wins The Match!`, baseSize * 1.8, winnerHex, true);
    y += baseSize * 3;
    this._overlayText(cx, y, `(${this.gameState.roundWins[0]} - ${this.gameState.roundWins[1]})`, baseSize * 1.2, '#000', true);

    y += baseSize * 2.5;
    this._overlayText(cx, y, 'Match Summary:', baseSize, '#000', true);
    y += baseSize * 1.5;
    for (let i = 0; i < this.gameState.roundHistory.length; i++) {
      this._overlayText(cx, y, `Round ${i + 1}: P${this.gameState.roundHistory[i]} Win`, baseSize * 0.85, '#555', true);
      y += baseSize * 1.2;
    }

    this._overlayText(cx, sh * 0.88, 'Tap to start new match', baseSize, '#444', true);
  }

  _drawCountdown() {
    // Clean previous frame's countdown content
    for (const t of this.overlayTexts) t.destroy();
    this.overlayTexts = [];
    this.overlayGfx.clear();

    const gs = this.gameState;
    if (!gs.countdownActive) return;

    const sw = this.scale.width;
    const sh = this.scale.height;
    const cx = sw / 2;
    const ts = GAME_CONFIG.tile_size;
    const boardH = GAME_CONFIG.tiles_height * ts;
    const cy = boardH / 2;

    // Round label above the box
    this._overlayText(cx, cy - boardH * 0.22, `ROUND ${gs.currentRound}`, Math.min(40, boardH / 6), '#000', true);

    // Match point
    if (gs.roundWins[0] === GAME_CONFIG.rounds_to_win - 1 ||
        gs.roundWins[1] === GAME_CONFIG.rounds_to_win - 1) {
      const g = this.overlayGfx;
      const mpY = cy - boardH * 0.35;
      g.fillStyle(0xff0000, 1);
      g.fillRoundedRect(cx - 90, mpY - 16, 180, 32, 8);
      this._overlayText(cx, mpY, 'MATCH POINT', 18, '#fff', true);
    }

    // Black box + number
    const boxW = sw * 0.25;
    const boxH = boardH * 0.3;
    this.overlayGfx.fillStyle(0x000000, 1);
    this.overlayGfx.fillRect(cx - boxW / 2, cy - boxH / 2, boxW, boxH);

    const cdText = gs.countdownTicks > 0 ? String(gs.countdownTicks) : 'GO!';
    this._overlayText(cx, cy, cdText, Math.min(72, boardH / 3), '#ffffff', true);
  }

  /** Helper: create a text object, track it for later cleanup. */
  _overlayText(x, y, str, size, color, centre = false) {
    const t = this.add.text(x, y, str, {
      fontSize: `${Math.round(size)}px`,
      fontFamily: 'Arial, sans-serif',
      color,
      fontStyle: 'bold',
    }).setDepth(201);
    if (centre) t.setOrigin(0.5);
    this.overlayTexts.push(t);
    return t;
  }

  /* ───────── resize handler ───────── */

  /**
   * Called when the window resizes (e.g., when installed as PWA, orientation change).
   * Repositions all UI elements to fit the new screen size.
   */
  handleResize() {
    const ts = GAME_CONFIG.tile_size;
    const boardH = GAME_CONFIG.tiles_height * ts;
    const sw = this.scale.width;

    // Reposition joystick
    const jRadius = Math.min(70, sw * 0.07);
    this.joystick.reposition(
      sw - jRadius - 30,
      boardH - jRadius - 20,
      jRadius,
    );

    // Reposition action buttons
    const btnW = Math.min(90, sw * 0.09);
    const btnH = Math.min(60, boardH * 0.14);
    const btnCentreX = 30 + btnW / 2;
    const btnTopY = boardH - btnH * 2 - 12 - 20;
    this.actionButtons.reposition(btnCentreX, btnTopY, btnW, btnH);

    // Stats panel will auto-adjust since it reads from GAME_CONFIG each frame
    // Redraw any overlay that's currently showing
    if (this.state !== 'playing' && this.state !== 'countdown') {
      this._setState(this.state);
    }
  }
}
