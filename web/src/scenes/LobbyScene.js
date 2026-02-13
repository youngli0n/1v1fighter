import Phaser from 'phaser';
import { GAME_CONFIG } from '../config.js';

/**
 * LobbyScene — the main menu.
 *
 * Three options:
 *   1. Play vs AI   → starts GameScene in 'ai' mode (same as before)
 *   2. Create Game  → connects to relay, creates a room, shows code/link
 *   3. Join Game    → shows input for room code, joins room
 *
 * If the URL contains ?room=XXXX, auto-joins that room.
 */
export class LobbyScene extends Phaser.Scene {
  constructor() {
    super('LobbyScene');
  }

  init(data) {
    /** @type {import('../net/SocketClient.js').SocketClient} */
    this.net = data.net;   // SocketClient instance passed from main.js
  }

  create() {
    const sw = this.scale.width;
    const sh = this.scale.height;
    const cx = sw / 2;

    // Background
    this.cameras.main.setBackgroundColor('#111111');

    // Title
    this.add.text(cx, sh * 0.08, '1v1 Fighter', {
      fontSize: `${Math.min(48, sw / 12)}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#ffffff',
      fontStyle: 'bold',
    }).setOrigin(0.5);

    this.add.text(cx, sh * 0.17, 'Multiplayer Arena', {
      fontSize: `${Math.min(20, sw / 30)}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#888888',
    }).setOrigin(0.5);

    // ── Buttons ──────────────────────────────────────────────
    const btnW = Math.min(300, sw * 0.5);
    const btnH = Math.min(56, sh * 0.11);
    const gap = Math.min(14, sh * 0.025);
    let y = sh * 0.28;

    this._makeButton(cx, y, btnW, btnH, 'Play vs AI', '#22aa22', () => this._startAI());
    y += btnH + gap;
    this._makeButton(cx, y, btnW, btnH, 'Create Game', '#0077cc', () => this._createGame());
    y += btnH + gap;
    this._makeButton(cx, y, btnW, btnH, 'Join Game', '#cc7700', () => this._showJoinUI());

    // ── Status area (below buttons) ──────────────────────────
    this.statusText = this.add.text(cx, sh * 0.62, '', {
      fontSize: `${Math.min(18, sw / 40)}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#cccccc',
      align: 'center',
      wordWrap: { width: sw * 0.8 },
    }).setOrigin(0.5, 0);

    this.codeText = this.add.text(cx, sh * 0.70, '', {
      fontSize: `${Math.min(48, sw / 14)}px`,
      fontFamily: 'monospace',
      color: '#ffffff',
      fontStyle: 'bold',
    }).setOrigin(0.5);

    // Room code input (hidden until "Join Game" is tapped)
    this.inputBg = null;
    this.inputText = null;
    this.inputCode = '';

    // ── Auto-join if URL has ?room=XXXX ──────────────────────
    const params = new URLSearchParams(window.location.search);
    const autoRoom = params.get('room');
    if (autoRoom) {
      this._joinRoom(autoRoom);
    }
  }

  // ── Button factory ─────────────────────────────────────────

  _makeButton(x, y, w, h, label, color, callback) {
    const hex = Phaser.Display.Color.HexStringToColor(color).color;
    const g = this.add.graphics();
    g.fillStyle(hex, 1);
    g.fillRoundedRect(x - w / 2, y, w, h, 12);

    const txt = this.add.text(x, y + h / 2, label, {
      fontSize: `${Math.min(22, h * 0.45)}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#ffffff',
      fontStyle: 'bold',
    }).setOrigin(0.5);

    // Hit zone
    const zone = this.add.zone(x, y + h / 2, w, h).setInteractive();
    zone.on('pointerdown', callback);

    return { g, txt, zone };
  }

  // ── Actions ────────────────────────────────────────────────

  _startAI() {
    this.scene.start('GameScene', { mode: 'ai', newMatch: true });
  }

  async _createGame() {
    this.statusText.setText('Connecting to server...');

    try {
      await this.net.connect();
    } catch (e) {
      this.statusText.setText('Could not connect to server.\nPlease try again.');
      return;
    }

    this.net.onRoomCreated = (code) => {
      this.statusText.setText('Waiting for a friend to join...\nShare this code:');
      this.codeText.setText(code);

      // Build a shareable link
      const base = window.location.origin + window.location.pathname;
      const link = `${base}?room=${code}`;
      console.log('[Lobby] Share link:', link);

      // Try to copy to clipboard
      navigator.clipboard?.writeText(link).then(() => {
        this.statusText.setText(
          'Waiting for a friend to join...\nShare this code (link copied!):',
        );
      }).catch(() => { /* ignore clipboard errors */ });
    };

    this.net.onGuestJoined = () => {
      this.statusText.setText('Friend joined! Starting...');
      this.codeText.setText('');

      // Short delay so the player sees the message
      this.time.delayedCall(600, () => {
        this.scene.start('GameScene', {
          mode: 'host',
          newMatch: true,
          net: this.net,
        });
      });
    };

    this.net.createRoom();
  }

  _showJoinUI() {
    if (this.inputBg) return; // already showing

    const sw = this.scale.width;
    const sh = this.scale.height;
    const cx = sw / 2;

    this.statusText.setText('Enter the 4-letter room code:');
    this.codeText.setText('');

    // Input box background
    const boxW = Math.min(220, sw * 0.35);
    const boxH = Math.min(56, sh * 0.09);
    const boxY = sh * 0.70;

    this.inputBg = this.add.graphics();
    this.inputBg.fillStyle(0x333333, 1);
    this.inputBg.fillRoundedRect(cx - boxW / 2, boxY, boxW, boxH, 10);
    this.inputBg.lineStyle(2, 0xffffff, 0.5);
    this.inputBg.strokeRoundedRect(cx - boxW / 2, boxY, boxW, boxH, 10);

    this.inputText = this.add.text(cx, boxY + boxH / 2, '____', {
      fontSize: `${Math.min(36, sw / 18)}px`,
      fontFamily: 'monospace',
      color: '#ffffff',
      fontStyle: 'bold',
      letterSpacing: 8,
    }).setOrigin(0.5);

    // "Go" button
    const goY = boxY + boxH + 14;
    this._makeButton(cx, goY, Math.min(160, sw * 0.25), Math.min(44, sh * 0.07), 'Join!', '#cc7700', () => {
      if (this.inputCode.length === 4) {
        this._joinRoom(this.inputCode);
      }
    });

    // Listen for keyboard input (desktop) and also show on-screen keyboard hint
    this.input.keyboard.on('keydown', this._onKey, this);

    // Also accept touch input — show a native prompt as a fallback
    // (on iPad, there's no easy way to type without a hardware keyboard)
    this.input.on('pointerdown', (pointer) => {
      if (pointer.y >= boxY && pointer.y <= boxY + boxH &&
          pointer.x >= cx - boxW / 2 && pointer.x <= cx + boxW / 2) {
        this._promptForCode();
      }
    });
  }

  _onKey(event) {
    if (this.inputCode.length < 4 && /^[a-zA-Z0-9]$/.test(event.key)) {
      this.inputCode += event.key.toUpperCase();
      this._updateInputDisplay();
    } else if (event.key === 'Backspace' && this.inputCode.length > 0) {
      this.inputCode = this.inputCode.slice(0, -1);
      this._updateInputDisplay();
    } else if (event.key === 'Enter' && this.inputCode.length === 4) {
      this._joinRoom(this.inputCode);
    }
  }

  _promptForCode() {
    const code = window.prompt('Enter 4-letter room code:');
    if (code && code.trim().length === 4) {
      this.inputCode = code.trim().toUpperCase();
      this._updateInputDisplay();
      this._joinRoom(this.inputCode);
    }
  }

  _updateInputDisplay() {
    if (!this.inputText) return;
    const display = this.inputCode.padEnd(4, '_');
    this.inputText.setText(display);
  }

  async _joinRoom(code) {
    code = code.toUpperCase().trim();
    this.statusText.setText(`Joining room ${code}...`);

    try {
      await this.net.connect();
    } catch (e) {
      this.statusText.setText('Could not connect to server.\nPlease try again.');
      return;
    }

    this.net.onJoined = () => {
      this.statusText.setText('Joined! Waiting for host to start...');
    };

    this.net.onJoinError = (message) => {
      this.statusText.setText(`Could not join: ${message}`);
    };

    this.net.onGameStart = (data) => {
      this.statusText.setText('Game starting!');
      this.time.delayedCall(300, () => {
        this.scene.start('GameScene', {
          mode: 'guest',
          newMatch: true,
          net: this.net,
          initialData: data,
        });
      });
    };

    this.net.joinRoom(code);
  }

  // Clean up keyboard listener when leaving
  shutdown() {
    this.input.keyboard.off('keydown', this._onKey, this);
  }
}
