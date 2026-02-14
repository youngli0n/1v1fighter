import Phaser from 'phaser';
import { GAME_CONFIG } from '../config.js';
import { PlayerProfile, AVATARS } from '../ui/PlayerProfile.js';

/**
 * LobbyScene — the main menu + lobby waiting room.
 *
 * Two UI states:
 *   1. "menu"  — title, buttons, profile badge (top-right)
 *   2. "lobby" — two player cards, ready buttons, start button
 */
export class LobbyScene extends Phaser.Scene {
  constructor() {
    super('LobbyScene');
  }

  init(data) {
    /** @type {import('../net/SocketClient.js').SocketClient} */
    this.net = data.net;
    this.profile = new PlayerProfile();

    // Lobby state
    this._state = 'menu';        // 'menu' | 'lobby'
    this._myRole = null;         // 'host' | 'guest'
    this._peerProfile = null;    // { name, avatar } of the other player
    this._myReady = false;
    this._peerReady = false;
    this._roomCode = null;

    // UI groups so we can show/hide easily
    this._menuObjects = [];
    this._lobbyObjects = [];
    this._editOverlayObjects = [];
  }

  create() {
    this.sw = this.scale.width;
    this.sh = this.scale.height;
    this.cx = this.sw / 2;

    // Background
    this.cameras.main.setBackgroundColor('#111111');

    this._buildMenu();

    // Auto-join if URL has ?room=XXXX
    const params = new URLSearchParams(window.location.search);
    const autoRoom = params.get('room');
    if (autoRoom) {
      this._joinRoom(autoRoom);
    }
  }

  // ═══════════════════════════════════════════════════════════
  //  MENU STATE — title, buttons, profile badge
  // ═══════════════════════════════════════════════════════════

  _buildMenu() {
    const { sw, sh, cx } = this;

    // Title
    this._menuObjects.push(
      this.add.text(cx, sh * 0.08, '1v1 Fighter', {
        fontSize: `${Math.min(48, sw / 12)}px`,
        fontFamily: 'Arial, sans-serif',
        color: '#ffffff',
        fontStyle: 'bold',
      }).setOrigin(0.5)
    );

    this._menuObjects.push(
      this.add.text(cx, sh * 0.17, 'Multiplayer Arena', {
        fontSize: `${Math.min(20, sw / 30)}px`,
        fontFamily: 'Arial, sans-serif',
        color: '#888888',
      }).setOrigin(0.5)
    );

    // Buttons
    const btnW = Math.min(300, sw * 0.5);
    const btnH = Math.min(56, sh * 0.11);
    const gap = Math.min(14, sh * 0.025);
    let y = sh * 0.28;

    this._menuObjects.push(...this._makeButton(cx, y, btnW, btnH, 'Play vs AI', '#22aa22', () => this._startAI()));
    y += btnH + gap;
    this._menuObjects.push(...this._makeButton(cx, y, btnW, btnH, 'Create Game', '#0077cc', () => this._createGame()));
    y += btnH + gap;
    this._menuObjects.push(...this._makeButton(cx, y, btnW, btnH, 'Join Game', '#cc7700', () => this._showJoinUI()));

    // Status area
    this.statusText = this.add.text(cx, sh * 0.62, '', {
      fontSize: `${Math.min(18, sw / 40)}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#cccccc',
      align: 'center',
      wordWrap: { width: sw * 0.8 },
    }).setOrigin(0.5, 0);
    this._menuObjects.push(this.statusText);

    this.codeText = this.add.text(cx, sh * 0.70, '', {
      fontSize: `${Math.min(48, sw / 14)}px`,
      fontFamily: 'monospace',
      color: '#ffffff',
      fontStyle: 'bold',
    }).setOrigin(0.5);
    this._menuObjects.push(this.codeText);

    // Room code input (hidden until "Join Game" is tapped)
    this.inputBg = null;
    this.inputText = null;
    this.inputCode = '';

    // Profile badge (top-right corner)
    this._buildProfileBadge();
  }

  // ── Profile badge (top-right) ─────────────────────────────

  _buildProfileBadge() {
    const { sw, sh } = this;

    // Position at the same height as the title (sh * 0.08) so it's
    // guaranteed to be in visible space — if the title shows, this will too.
    const radius = Math.min(32, Math.max(22, sw * 0.03));
    const badgeX = sw - radius - 20;
    const badgeY = sh * 0.08;

    // Circle background — bright border so it pops
    const bg = this.add.graphics();
    bg.fillStyle(0x444444, 1);
    bg.fillCircle(badgeX, badgeY, radius);
    bg.lineStyle(3, 0xffffff, 0.7);
    bg.strokeCircle(badgeX, badgeY, radius);
    this._menuObjects.push(bg);

    // Avatar emoji (scaled to the circle)
    this._badgeAvatar = this.add.text(badgeX, badgeY, this.profile.avatar, {
      fontSize: `${Math.max(22, radius)}px`,
    }).setOrigin(0.5);
    this._menuObjects.push(this._badgeAvatar);

    // Name below
    this._badgeName = this.add.text(badgeX, badgeY + radius + 6, this.profile.name, {
      fontSize: `${Math.max(13, Math.min(16, sw * 0.018))}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#cccccc',
      align: 'center',
    }).setOrigin(0.5, 0);
    this._menuObjects.push(this._badgeName);

    // Make it clickable — generous hit area
    const hitW = radius * 3;
    const hitH = radius * 3;
    const zone = this.add.zone(badgeX, badgeY + 10, hitW, hitH).setInteractive();
    zone.on('pointerdown', () => this._showEditOverlay());
    this._menuObjects.push(zone);

    // "tap to edit" hint
    const editHint = this.add.text(badgeX, badgeY + radius + 22, 'tap to edit', {
      fontSize: `${Math.max(10, Math.min(13, sw * 0.014))}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#888888',
    }).setOrigin(0.5, 0);
    this._menuObjects.push(editHint);
  }

  // ── Edit overlay ──────────────────────────────────────────

  _showEditOverlay() {
    if (this._editOverlayObjects.length > 0) return; // already open

    const { sw, sh, cx } = this;

    // Dark backdrop
    const backdrop = this.add.graphics();
    backdrop.fillStyle(0x000000, 0.8);
    backdrop.fillRect(0, 0, sw, sh);
    this._editOverlayObjects.push(backdrop);

    // Make backdrop block clicks to things behind it
    const backdropZone = this.add.zone(cx, sh / 2, sw, sh).setInteractive();
    this._editOverlayObjects.push(backdropZone);

    // Panel
    const panelW = Math.min(360, sw * 0.85);
    const panelH = Math.min(420, sh * 0.75);
    const panelX = cx - panelW / 2;
    const panelY = sh / 2 - panelH / 2;

    const panel = this.add.graphics();
    panel.fillStyle(0x222222, 1);
    panel.fillRoundedRect(panelX, panelY, panelW, panelH, 16);
    panel.lineStyle(2, 0x555555, 1);
    panel.strokeRoundedRect(panelX, panelY, panelW, panelH, 16);
    this._editOverlayObjects.push(panel);

    // Title
    this._editOverlayObjects.push(
      this.add.text(cx, panelY + 24, 'Edit Profile', {
        fontSize: '22px',
        fontFamily: 'Arial, sans-serif',
        color: '#ffffff',
        fontStyle: 'bold',
      }).setOrigin(0.5, 0)
    );

    // ── Name input ─────────────────────────────────
    this._editOverlayObjects.push(
      this.add.text(panelX + 20, panelY + 64, 'Name:', {
        fontSize: '16px',
        fontFamily: 'Arial, sans-serif',
        color: '#cccccc',
      })
    );

    // Name box (clickable to edit)
    const nameBoxY = panelY + 88;
    const nameBoxW = panelW - 40;
    const nameBoxH = 40;
    const nameBg = this.add.graphics();
    nameBg.fillStyle(0x333333, 1);
    nameBg.fillRoundedRect(panelX + 20, nameBoxY, nameBoxW, nameBoxH, 8);
    this._editOverlayObjects.push(nameBg);

    this._editNameText = this.add.text(panelX + 30, nameBoxY + nameBoxH / 2, this.profile.name, {
      fontSize: '18px',
      fontFamily: 'Arial, sans-serif',
      color: '#ffffff',
    }).setOrigin(0, 0.5);
    this._editOverlayObjects.push(this._editNameText);

    const nameZone = this.add.zone(panelX + 20 + nameBoxW / 2, nameBoxY + nameBoxH / 2, nameBoxW, nameBoxH).setInteractive();
    nameZone.on('pointerdown', () => {
      const newName = window.prompt('Enter your name:', this.profile.name);
      if (newName && newName.trim()) {
        this.profile.name = newName.trim().substring(0, 16);
        this._editNameText.setText(this.profile.name);
      }
    });
    this._editOverlayObjects.push(nameZone);

    // ── Avatar grid ────────────────────────────────
    this._editOverlayObjects.push(
      this.add.text(panelX + 20, panelY + 148, 'Avatar:', {
        fontSize: '16px',
        fontFamily: 'Arial, sans-serif',
        color: '#cccccc',
      })
    );

    const gridStartX = panelX + 30;
    const gridStartY = panelY + 176;
    const cellSize = 44;
    const cols = Math.min(6, Math.floor((panelW - 60) / cellSize));

    AVATARS.forEach((emoji, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const ax = gridStartX + col * cellSize + cellSize / 2;
      const ay = gridStartY + row * cellSize + cellSize / 2;

      // Highlight if selected
      const highlight = this.add.graphics();
      if (this.profile.avatar === emoji) {
        highlight.fillStyle(0x0077cc, 0.5);
        highlight.fillRoundedRect(ax - cellSize / 2 + 2, ay - cellSize / 2 + 2, cellSize - 4, cellSize - 4, 8);
      }
      this._editOverlayObjects.push(highlight);

      const txt = this.add.text(ax, ay, emoji, {
        fontSize: '28px',
      }).setOrigin(0.5);
      this._editOverlayObjects.push(txt);

      const z = this.add.zone(ax, ay, cellSize, cellSize).setInteractive();
      z.on('pointerdown', () => {
        this.profile.avatar = emoji;
        // Rebuild overlay to update highlight
        this._closeEditOverlay();
        this._showEditOverlay();
      });
      this._editOverlayObjects.push(z);
    });

    // ── Upload photo button ────────────────────────
    const rows = Math.ceil(AVATARS.length / cols);
    const uploadY = gridStartY + rows * cellSize + 16;

    const uploadObjs = this._makeButton(cx, uploadY, Math.min(200, panelW - 60), 38, 'Upload Photo', '#555555', () => {
      this._handlePhotoUpload();
    });
    this._editOverlayObjects.push(...uploadObjs);

    // ── Save button ────────────────────────────────
    const saveY = uploadY + 56;
    const saveObjs = this._makeButton(cx, saveY, Math.min(200, panelW - 60), 44, 'Save', '#22aa22', () => {
      this.profile.save();
      this._closeEditOverlay();
      this._refreshBadge();
    });
    this._editOverlayObjects.push(...saveObjs);
  }

  _closeEditOverlay() {
    this._editOverlayObjects.forEach(obj => obj.destroy());
    this._editOverlayObjects = [];
  }

  _handlePhotoUpload() {
    // Create a hidden file input and click it
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        // Resize to a small image (64x64) to keep localStorage small
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = 64;
          canvas.height = 64;
          const ctx = canvas.getContext('2d');
          // Draw centered/cropped square
          const size = Math.min(img.width, img.height);
          const sx = (img.width - size) / 2;
          const sy = (img.height - size) / 2;
          ctx.drawImage(img, sx, sy, size, size, 0, 0, 64, 64);
          this.profile.avatar = canvas.toDataURL('image/jpeg', 0.7);
          // Refresh the overlay
          this._closeEditOverlay();
          this._showEditOverlay();
        };
        img.src = event.target.result;
      };
      reader.readAsDataURL(file);
    };
    input.click();
  }

  _refreshBadge() {
    if (this._badgeAvatar) {
      if (this.profile.isCustomAvatar()) {
        this._badgeAvatar.setText('📷');
      } else {
        this._badgeAvatar.setText(this.profile.avatar);
      }
    }
    if (this._badgeName) {
      this._badgeName.setText(this.profile.name);
    }
  }

  // ═══════════════════════════════════════════════════════════
  //  BUTTON FACTORY
  // ═══════════════════════════════════════════════════════════

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

    const zone = this.add.zone(x, y + h / 2, w, h).setInteractive();
    zone.on('pointerdown', callback);

    return [g, txt, zone];
  }

  // ═══════════════════════════════════════════════════════════
  //  MENU ACTIONS
  // ═══════════════════════════════════════════════════════════

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
      this._roomCode = code;
      this._myRole = 'host';
      this._switchToLobby();
    };

    this.net.onGuestJoined = (guestProfile) => {
      this._peerProfile = guestProfile;
      this._refreshLobbyCards();
    };

    this.net.onPeerReady = () => {
      this._peerReady = true;
      this._refreshLobbyCards();
    };

    this.net.createRoom(this.profile.toData());
  }

  _showJoinUI() {
    if (this.inputBg) return;

    const { sw, sh, cx } = this;

    this.statusText.setText('Enter the 4-letter room code:');
    this.codeText.setText('');

    const boxW = Math.min(220, sw * 0.35);
    const boxH = Math.min(56, sh * 0.09);
    const boxY = sh * 0.70;

    this.inputBg = this.add.graphics();
    this.inputBg.fillStyle(0x333333, 1);
    this.inputBg.fillRoundedRect(cx - boxW / 2, boxY, boxW, boxH, 10);
    this.inputBg.lineStyle(2, 0xffffff, 0.5);
    this.inputBg.strokeRoundedRect(cx - boxW / 2, boxY, boxW, boxH, 10);
    this._menuObjects.push(this.inputBg);

    this.inputText = this.add.text(cx, boxY + boxH / 2, '____', {
      fontSize: `${Math.min(36, sw / 18)}px`,
      fontFamily: 'monospace',
      color: '#ffffff',
      fontStyle: 'bold',
      letterSpacing: 8,
    }).setOrigin(0.5);
    this._menuObjects.push(this.inputText);

    const goObjs = this._makeButton(cx, boxY + boxH + 14, Math.min(160, sw * 0.25), Math.min(44, sh * 0.07), 'Join!', '#cc7700', () => {
      if (this.inputCode.length === 4) {
        this._joinRoom(this.inputCode);
      }
    });
    this._menuObjects.push(...goObjs);

    this.input.keyboard.on('keydown', this._onKey, this);

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
      this._roomCode = code;
      this._myRole = 'guest';
      this._switchToLobby();
    };

    this.net.onJoinError = (message) => {
      this.statusText.setText(`Could not join: ${message}`);
    };

    this.net.onPeerProfile = (hostProfile) => {
      this._peerProfile = hostProfile;
      this._refreshLobbyCards();
    };

    this.net.onPeerReady = () => {
      this._peerReady = true;
      this._refreshLobbyCards();
    };

    this.net.onGameStart = (data) => {
      this.scene.start('GameScene', {
        mode: 'guest',
        newMatch: true,
        net: this.net,
        initialData: data,
      });
    };

    this.net.joinRoom(code, this.profile.toData());
  }

  // ═══════════════════════════════════════════════════════════
  //  LOBBY STATE — player cards, ready, start
  // ═══════════════════════════════════════════════════════════

  _switchToLobby() {
    this._state = 'lobby';

    // Hide all menu stuff
    this._menuObjects.forEach(obj => obj.setVisible(false));
    this._closeEditOverlay();

    // Build the lobby UI
    this._buildLobbyUI();
  }

  _buildLobbyUI() {
    const { sw, sh, cx } = this;

    // Room code at top
    const codeLabel = this.add.text(cx, sh * 0.06, `Room: ${this._roomCode}`, {
      fontSize: `${Math.min(28, sw / 16)}px`,
      fontFamily: 'monospace',
      color: '#ffffff',
      fontStyle: 'bold',
    }).setOrigin(0.5);
    this._lobbyObjects.push(codeLabel);

    // Copy link hint
    const base = window.location.origin + window.location.pathname;
    const link = `${base}?room=${this._roomCode}`;
    navigator.clipboard?.writeText(link).catch(() => {});

    const linkHint = this.add.text(cx, sh * 0.12, 'Link copied! Share it with a friend.', {
      fontSize: `${Math.min(14, sw / 40)}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#888888',
    }).setOrigin(0.5);
    this._lobbyObjects.push(linkHint);

    // "VS" in the middle
    const vsText = this.add.text(cx, sh * 0.4, 'VS', {
      fontSize: `${Math.min(40, sw / 14)}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#555555',
      fontStyle: 'bold',
    }).setOrigin(0.5);
    this._lobbyObjects.push(vsText);

    // Player cards — these get rebuilt by _refreshLobbyCards
    this._playerCardObjects = [];
    this._refreshLobbyCards();
  }

  _refreshLobbyCards() {
    // Destroy old card objects
    this._playerCardObjects.forEach(obj => obj.destroy());
    this._playerCardObjects = [];

    const { sw, sh } = this;
    const cardW = Math.min(160, sw * 0.35);
    const cardY = sh * 0.22;

    // Left card = host (or me if I'm host, peer if I'm guest)
    const leftProfile = this._myRole === 'host' ? this.profile.toData() : this._peerProfile;
    const rightProfile = this._myRole === 'host' ? this._peerProfile : this.profile.toData();
    const leftReady = this._myRole === 'host' ? this._myReady : this._peerReady;
    const rightReady = this._myRole === 'host' ? this._peerReady : this._myReady;

    const leftX = sw * 0.25;
    const rightX = sw * 0.75;

    this._drawPlayerCard(leftX, cardY, cardW, leftProfile, leftReady);
    this._drawPlayerCard(rightX, cardY, cardW, rightProfile, rightReady);

    // Ready button (only if I haven't readied up yet)
    if (!this._myReady) {
      const readyY = sh * 0.62;
      const readyObjs = this._makeButton(this.cx, readyY, Math.min(200, sw * 0.4), 50, 'READY!', '#cc7700', () => {
        this._myReady = true;
        this.net.sendReady();
        this._refreshLobbyCards();
      });
      this._playerCardObjects.push(...readyObjs);
    } else {
      // Show a "you're ready" message
      const readyMsg = this.add.text(this.cx, sh * 0.63, '✓ You are ready!', {
        fontSize: `${Math.min(20, sw / 28)}px`,
        fontFamily: 'Arial, sans-serif',
        color: '#44cc44',
        fontStyle: 'bold',
      }).setOrigin(0.5);
      this._playerCardObjects.push(readyMsg);
    }

    // START button — only host sees this, and only when BOTH are ready
    if (this._myRole === 'host' && this._myReady && this._peerReady) {
      const startY = sh * 0.73;
      const startObjs = this._makeButton(this.cx, startY, Math.min(240, sw * 0.45), 54, '▶  START', '#22aa22', () => {
        this.scene.start('GameScene', {
          mode: 'host',
          newMatch: true,
          net: this.net,
        });
      });
      this._playerCardObjects.push(...startObjs);
    } else if (this._myRole === 'host' && this._myReady && !this._peerReady && this._peerProfile) {
      // Host is ready, waiting for guest
      const waitMsg = this.add.text(this.cx, sh * 0.73, 'Waiting for opponent to ready up...', {
        fontSize: `${Math.min(14, sw / 40)}px`,
        fontFamily: 'Arial, sans-serif',
        color: '#888888',
      }).setOrigin(0.5);
      this._playerCardObjects.push(waitMsg);
    } else if (this._myRole === 'guest' && this._myReady) {
      // Guest is ready, waiting for host to start
      const waitMsg = this.add.text(this.cx, sh * 0.73, 'Waiting for host to start...', {
        fontSize: `${Math.min(14, sw / 40)}px`,
        fontFamily: 'Arial, sans-serif',
        color: '#888888',
      }).setOrigin(0.5);
      this._playerCardObjects.push(waitMsg);
    }
  }

  /**
   * Draw a player card — avatar circle + name + ready badge.
   * If profile is null, shows a "?" waiting placeholder.
   */
  _drawPlayerCard(x, y, w, profile, isReady) {
    const radius = Math.min(40, w * 0.25);

    if (!profile) {
      // Empty slot — waiting for player
      const bg = this.add.graphics();
      bg.lineStyle(3, 0x555555, 1);
      bg.strokeCircle(x, y + radius, radius);
      this._playerCardObjects.push(bg);

      const q = this.add.text(x, y + radius, '?', {
        fontSize: `${radius * 1.2}px`,
        fontFamily: 'Arial, sans-serif',
        color: '#555555',
        fontStyle: 'bold',
      }).setOrigin(0.5);
      this._playerCardObjects.push(q);

      const waiting = this.add.text(x, y + radius * 2 + 14, 'Waiting...', {
        fontSize: '14px',
        fontFamily: 'Arial, sans-serif',
        color: '#666666',
      }).setOrigin(0.5, 0);
      this._playerCardObjects.push(waiting);
      return;
    }

    // Avatar circle background
    const bg = this.add.graphics();
    bg.fillStyle(0x333333, 1);
    bg.fillCircle(x, y + radius, radius);
    if (isReady) {
      bg.lineStyle(3, 0x44cc44, 1); // green border when ready
    } else {
      bg.lineStyle(2, 0x888888, 1);
    }
    bg.strokeCircle(x, y + radius, radius);
    this._playerCardObjects.push(bg);

    // Avatar — emoji or custom photo
    if (profile.avatar && profile.avatar.startsWith('data:')) {
      // Custom uploaded photo — load as texture and display
      const texKey = `avatar_${x}_${y}_${Date.now()}`;
      const img = new Image();
      img.onload = () => {
        if (this.textures.exists(texKey)) this.textures.remove(texKey);
        this.textures.addImage(texKey, img);
        const sprite = this.add.image(x, y + radius, texKey)
          .setDisplaySize(radius * 1.6, radius * 1.6);
        this._playerCardObjects.push(sprite);

        // Circular mask
        const mask = this.add.graphics();
        mask.fillCircle(x, y + radius, radius - 2);
        sprite.setMask(mask.createGeometryMask());
        this._playerCardObjects.push(mask);
      };
      img.src = profile.avatar;
    } else {
      // Emoji avatar
      const emojiText = this.add.text(x, y + radius, profile.avatar || '⚔️', {
        fontSize: `${radius * 1.1}px`,
      }).setOrigin(0.5);
      this._playerCardObjects.push(emojiText);
    }

    // Name
    const nameText = this.add.text(x, y + radius * 2 + 14, profile.name || 'Player', {
      fontSize: `${Math.min(18, w * 0.12)}px`,
      fontFamily: 'Arial, sans-serif',
      color: '#ffffff',
      fontStyle: 'bold',
      align: 'center',
    }).setOrigin(0.5, 0);
    this._playerCardObjects.push(nameText);

    // Ready badge
    if (isReady) {
      const badge = this.add.text(x, y + radius * 2 + 38, 'READY', {
        fontSize: '14px',
        fontFamily: 'Arial, sans-serif',
        color: '#44cc44',
        fontStyle: 'bold',
      }).setOrigin(0.5, 0);
      this._playerCardObjects.push(badge);
    }
  }

  // ═══════════════════════════════════════════════════════════
  //  CLEANUP
  // ═══════════════════════════════════════════════════════════

  shutdown() {
    this.input.keyboard.off('keydown', this._onKey, this);
    this._closeEditOverlay();
  }
}
