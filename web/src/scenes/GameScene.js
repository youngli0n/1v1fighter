import Phaser from 'phaser';
import { GAME_CONFIG, COLORS } from '../config.js';
import { Player } from '../entities/Player.js';
import { Wall, generateWalls } from '../entities/Wall.js';
import { Collectible, generateCollectibles } from '../entities/Collectible.js';
import { GameState } from '../state/GameState.js';
import { AIPlayer } from '../ai/AIPlayer.js';
import { VirtualJoystick } from '../ui/VirtualJoystick.js';
import { ActionButtons } from '../ui/ActionButtons.js';
import { StatsPanel } from '../ui/StatsPanel.js';

/**
 * Main game scene — handles every state:
 *   instructions → countdown → playing → round_over / match_over
 *
 * Supports three modes:
 *   'ai'   — single-player vs AI (default, same as original)
 *   'host' — multiplayer: this device runs the simulation, remote guest sends inputs
 *   'guest'— multiplayer: this device sends inputs, renders state received from host
 */
export class GameScene extends Phaser.Scene {
  constructor() {
    super('GameScene');
  }

  /* ───────── lifecycle ───────── */

  init(data) {
    this.newMatch = data?.newMatch !== false;
    this.mode = data?.mode || 'ai';          // 'ai' | 'host' | 'guest'
    this.net = data?.net || null;             // SocketClient (host/guest)
    this.initialData = data?.initialData || null; // guest: walls + collectibles from host
  }

  create() {
    const W = GAME_CONFIG.tiles_width;
    const H = GAME_CONFIG.tiles_height;

    // ── Match setup ──────────────────────────────────────────
    if (this.mode === 'guest') {
      // Guest: build world from the data the host sent
      this._initFromHostData(this.initialData);
    } else if (this.newMatch) {
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
      this.player1.reset();
      this.player2.reset();
    }

    // AI only in AI mode
    if (this.mode === 'ai') {
      this.ai = new AIPlayer(this.player2, this.player1, this.walls);
    }

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

    const jRadius = Math.min(70, sw * 0.07);
    this.joystick = new VirtualJoystick(
      this,
      sw - jRadius - 30,
      boardH - jRadius - 20,
      jRadius,
    );

    const btnW = Math.min(90, sw * 0.09);
    const btnH = Math.min(60, boardH * 0.14);
    const gap = 12;
    const btnCentreX = 30 + btnW / 2;
    const btnTopY = boardH - btnH * 2 - gap - 20;
    this.actionButtons = new ActionButtons(this, btnCentreX, btnTopY, btnW, btnH, gap);
    this.actionButtons.addLabels();

    this.statsPanel = new StatsPanel(this);

    // ── Keyboard fallback ────────────────────────────────────
    this.keys = this.input.keyboard.addKeys({
      up: 'W', down: 'S', left: 'A', right: 'D',
      shoot: 'V', shield: 'B',
    });

    // ── Network setup ────────────────────────────────────────
    if (this.mode === 'host') {
      this.guestInput = { dx: 0, dy: 0, shoot: false, shield: false };
      this.net.onGuestInput = (data) => {
        this.guestInput.dx = data.dx;
        this.guestInput.dy = data.dy;
        if (data.shoot) this.guestInput.shoot = true; // accumulate until consumed
        this.guestInput.shield = data.shield;
      };
      this.net.onPeerDisconnected = () => this._onPeerDisconnected();
    }

    if (this.mode === 'guest') {
      this.latestState = null;
      this.net.onGameState = (data) => { this.latestState = data; };
      this.net.onPeerDisconnected = () => this._onPeerDisconnected();
    }

    // ── State machine ────────────────────────────────────────
    if (this.mode === 'ai') {
      this._setState('instructions');
    } else {
      // Multiplayer: skip instructions, go straight to countdown
      if (this.mode === 'host') {
        // Send initial game data to guest
        this._sendGameStart();
      }
      this.gameState.resetRound();
      this._setState('countdown');
    }

    // ── Tap-to-advance ───────────────────────────────────────
    this.input.on('pointerdown', () => {
      if (this.state === 'playing' || this.state === 'countdown') return;
      if (Date.now() - this.stateEnteredAt < 600) return;
      // Guest can't advance overlays — only the host/AI player can
      if (this.mode === 'guest') return;
      this._advanceOverlay();
    });
  }

  /* ───────── update loop ───────── */

  update(_time, delta) {
    // Guest has its own update path
    if (this.mode === 'guest') {
      this._guestUpdate();
      return;
    }

    const dt = delta / 1000;
    const t = Date.now() / 1000;

    if (this.state === 'countdown') {
      if (this.gameState.updateCountdown(t)) {
        this._setState('playing');
      }
      this._drawCountdown();
    }

    if (this.state === 'playing') {
      this._updateGameplay(dt, t);
    }

    this._drawBoard(t);
    this.statsPanel.update(this.player1, this.player2, t);

    // Host: send state to guest every frame (in all states)
    if (this.mode === 'host') {
      this._sendState();
    }
  }

  /* ───────── state machine helpers ───────── */

  _setState(s) {
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
      this.walls = generateWalls();
      const p1 = { x: this.player1.startX, y: this.player1.startY };
      const p2 = { x: this.player2.startX, y: this.player2.startY };
      this.collectibles = generateCollectibles(
        this.walls, GAME_CONFIG.num_collectibles_per_match, p1, p2,
      );
      if (this.mode === 'ai') {
        this.ai = new AIPlayer(this.player2, this.player1, this.walls);
      }
      if (this.mode === 'host') {
        this._sendGameStart(); // send new walls/collectibles to guest
      }
      this.gameOver = false;
      this.winner = null;
      this.gameState.resetRound();
      this._setState('countdown');
    } else if (this.state === 'match_over') {
      if (this.mode === 'host') {
        // Restart match — guest will get new game_start data
        this.scene.restart({ mode: 'host', newMatch: true, net: this.net });
      } else {
        this.scene.restart({ mode: 'ai', newMatch: true });
      }
    }
  }

  /* ───────── gameplay ───────── */

  _updateGameplay(dt, t) {
    const p1 = this.player1;
    const p2 = this.player2;

    // ── Player 1 input (local touch + keyboard) ──────────────
    let dx = this.joystick.dx * GAME_CONFIG.player_speed;
    let dy = this.joystick.dy * GAME_CONFIG.player_speed;
    if (dx === 0 && dy === 0) {
      dx = ((this.keys.right.isDown ? 1 : 0) - (this.keys.left.isDown ? 1 : 0)) * GAME_CONFIG.player_speed;
      dy = ((this.keys.down.isDown ? 1 : 0) - (this.keys.up.isDown ? 1 : 0)) * GAME_CONFIG.player_speed;
    }
    p1.move(dx, dy, dt, t, p2, this.walls);
    p1.shieldActive = this.actionButtons.shieldHeld || this.keys.shield.isDown;
    if (this.actionButtons.consumeShoot() || Phaser.Input.Keyboard.JustDown(this.keys.shoot)) {
      p1.shoot(t);
    }

    // ── Player 2 input (AI or remote guest) ──────────────────
    if (this.mode === 'host') {
      const gi = this.guestInput;
      p2.move(gi.dx, gi.dy, dt, t, p1, this.walls);
      p2.shieldActive = gi.shield;
      if (gi.shoot) {
        p2.shoot(t);
        gi.shoot = false; // consume
      }
    } else {
      this.ai.update(dt, t);
    }

    // ── Projectiles ─────────────────────────────────────────
    p1.updateProjectiles(dt, p2, t, this.walls);
    p2.updateProjectiles(dt, p1, t, this.walls);

    // ── Collectibles ────────────────────────────────────────
    for (let i = this.collectibles.length - 1; i >= 0; i--) {
      const c = this.collectibles[i];
      const ts = GAME_CONFIG.tile_size;
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

  /* ───────── MULTIPLAYER: Host serialization ───────── */

  /** Send initial game data (walls, collectibles) to guest */
  _sendGameStart() {
    this.net.sendGameStart({
      walls: this.walls.map((w) => ({ x: w.x, y: w.y })),
      collectibles: this.collectibles.map((c) => ({
        x: c.x, y: c.y, color: c.color,
      })),
    });
  }

  /** Serialize full game state and send to guest (called every frame) */
  _sendState() {
    const t = Date.now() / 1000;
    const serializePlayer = (p) => ({
      x: p.x,
      y: p.y,
      sa: p.shieldActive,
      pr: Math.min(100, Math.round(p.getProgress())),
      spd: Math.round(p.getTotalSpeedMultiplier(t) * 100),
      sl: p.isSlowed(t),
      su: p.isSpeedup(t),
      sb: p.shieldBoosts.filter((b) => t < b.endTime).length,
    });

    this.net.sendGameState({
      p1: serializePlayer(this.player1),
      p2: serializePlayer(this.player2),
      b1: this.player1.projectiles.map((p) => {
        const r = p.getRect();
        return { x: r.x, y: r.y, w: r.w, h: r.h };
      }),
      b2: this.player2.projectiles.map((p) => {
        const r = p.getRect();
        return { x: r.x, y: r.y, w: r.w, h: r.h };
      }),
      cl: this.collectibles.map((c) => ({ x: c.x, y: c.y, c: c.color })),
      st: this.state,
      cd: this.gameState.countdownTicks,
      cda: this.gameState.countdownActive,
      rw: [...this.gameState.roundWins],
      cr: this.gameState.currentRound,
      mo: this.gameState.matchOver,
      go: this.gameOver,
      win: this.winner === this.player1 ? 1 : this.winner === this.player2 ? 2 : 0,
      rh: [...this.gameState.roundHistory],
    });
  }

  /* ───────── MULTIPLAYER: Guest logic ───────── */

  /** Called once in create() to build the world from host data */
  _initFromHostData(data) {
    const H = GAME_CONFIG.tiles_height;
    const W = GAME_CONFIG.tiles_width;

    this.gameState = new GameState();

    // Recreate walls from positions
    this.walls = (data?.walls || []).map((w) => new Wall(w.x, w.y));

    // Recreate collectibles as simple renderable objects
    this.collectibles = (data?.collectibles || []).map((c) =>
      new Collectible(c.x, c.y, c.color),
    );

    // Create player shells — their positions/state will be set from packets
    this.player1 = new Player(0, Math.floor(H / 2) - 0.5, COLORS.player1);
    this.player2 = new Player(W - 1, Math.floor(H / 2) - 0.5, COLORS.player2);

    // Override methods so they return values from the state packet
    this.player1._gp = 0;
    this.player1._gs = 100;
    this.player2._gp = 0;
    this.player2._gs = 100;

    for (const p of [this.player1, this.player2]) {
      p.getProgress = () => p._gp;
      p.getTotalSpeedMultiplier = () => p._gs / 100;
      p.isSlowed = () => p._sl || false;
      p.isSpeedup = () => p._su || false;
    }
  }

  /** Guest update loop — receive state, render, send input */
  _guestUpdate() {
    const t = Date.now() / 1000;

    // Send our inputs to the host
    this.net.sendInput({
      dx: this.joystick.dx * GAME_CONFIG.player_speed,
      dy: this.joystick.dy * GAME_CONFIG.player_speed,
      shoot: this.actionButtons.consumeShoot() || Phaser.Input.Keyboard.JustDown(this.keys.shoot),
      shield: this.actionButtons.shieldHeld || this.keys.shield.isDown,
    });

    // Apply latest state from host
    if (this.latestState) {
      this._applyGuestState(this.latestState);
    }

    // Render
    this._drawBoard(t);
    this.statsPanel.update(this.player1, this.player2, t);

    // Overlays
    if (this.state === 'countdown') {
      this._drawCountdown();
    }
  }

  /** Apply a state packet from the host to local objects */
  _applyGuestState(s) {
    // Players
    const applyPlayer = (p, d) => {
      p.x = d.x;
      p.y = d.y;
      p.shieldActive = d.sa;
      p._gp = d.pr;
      p._gs = d.spd;
      p._sl = d.sl;
      p._su = d.su;
      // Fake shieldBoosts array so StatsPanel can count them
      p.shieldBoosts = Array.from({ length: d.sb }, () => ({ endTime: Infinity }));
    };
    applyPlayer(this.player1, s.p1);
    applyPlayer(this.player2, s.p2);

    // Projectiles — create simple objects with getRect()
    this.player1.projectiles = (s.b1 || []).map((b) => ({
      getRect: () => b,
    }));
    this.player2.projectiles = (s.b2 || []).map((b) => ({
      getRect: () => b,
    }));

    // Collectibles — rebuild from state
    this.collectibles = (s.cl || []).map((c) =>
      new Collectible(c.x, c.y, c.c),
    );

    // Game state
    this.gameState.countdownTicks = s.cd;
    this.gameState.countdownActive = s.cda;
    this.gameState.roundWins = s.rw;
    this.gameState.currentRound = s.cr;
    this.gameState.matchOver = s.mo;
    this.gameState.roundHistory = s.rh || [];
    this.gameOver = s.go;

    if (s.win === 1) this.winner = this.player1;
    else if (s.win === 2) this.winner = this.player2;
    else this.winner = null;

    // State transitions (only when state actually changes)
    if (s.st !== this.state) {
      this._setState(s.st);
    }

    // If host restarted a round, we'll get new game_start data
    // via the onGameStart callback in LobbyScene or here
    if (!this._gameStartListenerSet) {
      this._gameStartListenerSet = true;
      this.net.onGameStart = (data) => {
        this.walls = (data.walls || []).map((w) => new Wall(w.x, w.y));
        this.collectibles = (data.collectibles || []).map((c) =>
          new Collectible(c.x, c.y, c.color),
        );
      };
    }
  }

  /** Handle opponent disconnecting */
  _onPeerDisconnected() {
    // Go back to lobby
    this.net.disconnect();
    this.scene.start('LobbyScene', { net: new (this.net.constructor)() });
  }

  /* ───────── rendering ───────── */

  _drawBoard(t) {
    const g = this.gameGfx;
    g.clear();

    const ts = GAME_CONFIG.tile_size;
    const W = GAME_CONFIG.tiles_width;
    const H = GAME_CONFIG.tiles_height;

    g.fillStyle(COLORS.background, 1);
    g.fillRect(0, 0, W * ts, H * ts);

    const cx = (W / 2) * ts;
    g.lineStyle(1, COLORS.center_line, 1);
    g.lineBetween(cx, 0, cx, H * ts);

    for (const wall of this.walls) {
      const r = wall.getRect();
      g.fillStyle(COLORS.wall, 1);
      g.fillRect(r.x, r.y, r.w, r.h);
    }

    for (const c of this.collectibles) {
      const r = c.getRect();
      g.fillStyle(c.color, 1);
      g.fillRect(r.x, r.y, r.w, r.h);
    }

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

    this._overlayText(cx, y, 'How to Play', baseSize * 1.6, '#000', true);
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

    const tapMsg = this.mode === 'guest'
      ? 'Waiting for host to start next round...'
      : 'Tap to start next round';
    this._overlayText(cx, sh * 0.88, tapMsg, baseSize, '#444', true);
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

    const tapMsg = this.mode === 'guest'
      ? 'Waiting for host to start new match...'
      : 'Tap to start new match';
    this._overlayText(cx, sh * 0.88, tapMsg, baseSize, '#444', true);
  }

  _drawCountdown() {
    for (const t of this.overlayTexts) t.destroy();
    this.overlayTexts = [];
    this.overlayGfx.clear();

    const gs = this.gameState;
    if (!gs.countdownActive) return;

    const sw = this.scale.width;
    const cx = sw / 2;
    const ts = GAME_CONFIG.tile_size;
    const boardH = GAME_CONFIG.tiles_height * ts;
    const cy = boardH / 2;

    this._overlayText(cx, cy - boardH * 0.22, `ROUND ${gs.currentRound}`, Math.min(40, boardH / 6), '#000', true);

    if (gs.roundWins[0] === GAME_CONFIG.rounds_to_win - 1 ||
        gs.roundWins[1] === GAME_CONFIG.rounds_to_win - 1) {
      const g = this.overlayGfx;
      const mpY = cy - boardH * 0.35;
      g.fillStyle(0xff0000, 1);
      g.fillRoundedRect(cx - 90, mpY - 16, 180, 32, 8);
      this._overlayText(cx, mpY, 'MATCH POINT', 18, '#fff', true);
    }

    const boxW = sw * 0.25;
    const boxH = boardH * 0.3;
    this.overlayGfx.fillStyle(0x000000, 1);
    this.overlayGfx.fillRect(cx - boxW / 2, cy - boxH / 2, boxW, boxH);

    const cdText = gs.countdownTicks > 0 ? String(gs.countdownTicks) : 'GO!';
    this._overlayText(cx, cy, cdText, Math.min(72, boardH / 3), '#ffffff', true);
  }

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

  handleResize() {
    const ts = GAME_CONFIG.tile_size;
    const boardH = GAME_CONFIG.tiles_height * ts;
    const sw = this.scale.width;

    const jRadius = Math.min(70, sw * 0.07);
    this.joystick.reposition(sw - jRadius - 30, boardH - jRadius - 20, jRadius);

    const btnW = Math.min(90, sw * 0.09);
    const btnH = Math.min(60, boardH * 0.14);
    const btnCentreX = 30 + btnW / 2;
    const btnTopY = boardH - btnH * 2 - 12 - 20;
    this.actionButtons.reposition(btnCentreX, btnTopY, btnW, btnH);

    if (this.state !== 'playing' && this.state !== 'countdown') {
      this._setState(this.state);
    }
  }
}
