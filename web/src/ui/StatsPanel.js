import { GAME_CONFIG, COLORS } from '../config.js';

/**
 * HUD panel at the bottom of the screen showing
 * speed, shield, effects, and a progress bar for each player.
 */
export class StatsPanel {
  constructor(scene) {
    this.scene = scene;
    this.gfx = scene.add.graphics().setDepth(50);
    this.texts = [];
  }

  /** Redraw every frame. */
  update(player1, player2, currentTime) {
    // Clean up previous text objects
    for (const t of this.texts) t.destroy();
    this.texts = [];

    this.gfx.clear();

    const ts = GAME_CONFIG.tile_size;
    const panelY = GAME_CONFIG.tiles_height * ts;
    const panelH = GAME_CONFIG.stats_panel_height;
    const panelW = GAME_CONFIG.game_width;

    // Background
    this.gfx.fillStyle(COLORS.stats_panel, 1);
    this.gfx.fillRect(0, panelY, panelW, panelH);

    // Divider
    this.gfx.lineStyle(1, COLORS.text, 0.3);
    this.gfx.lineBetween(panelW / 2, panelY + 8, panelW / 2, panelY + panelH - 8);

    const sectionW = panelW / 2;
    const pad = Math.max(10, panelW / 80);

    this._drawPlayerStats(player1, 0, sectionW, pad, panelY, panelH, currentTime, true);
    this._drawPlayerStats(player2, sectionW, sectionW, pad, panelY, panelH, currentTime, false);
  }

  _drawPlayerStats(player, sectionX, sectionW, pad, panelY, panelH, t, isP1) {
    const lines = [];
    const speed = player.getTotalSpeedMultiplier(t);
    lines.push({ text: `P${isP1 ? 1 : 2} Speed: ${Math.round(speed * 100)}%`, color: '#000' });

    const shieldColor = isP1 ? '#cc0000' : '#0000cc';
    lines.push({
      text: `Shield: ${player.shieldActive ? 'ACTIVE' : 'inactive'}`,
      color: player.shieldActive ? shieldColor : '#000',
    });

    if (player.isSpeedup(t)) {
      const rem = Math.max(0, player.speedupEndTime - t);
      lines.push({ text: `SPEED BOOST: ${rem.toFixed(1)}s`, color: '#00aa00' });
    }
    if (player.isSlowed(t)) {
      const rem = Math.max(0, player.slowEndTime - t);
      lines.push({ text: `SLOWED: ${rem.toFixed(1)}s`, color: '#ff8c00' });
    }

    const activeBoosts = player.shieldBoosts.filter((b) => t < b.endTime);
    if (activeBoosts.length > 0) {
      const longest = Math.max(...activeBoosts.map((b) => b.endTime));
      const rem = Math.max(0, longest - t);
      lines.push({ text: `Block Boosts: ${activeBoosts.length} (${rem.toFixed(1)}s)`, color: '#000' });
    }

    // Layout
    const fontSize = Math.min(16, panelH / 6);
    const lineH = fontSize + 3;
    const barH = Math.min(12, panelH / 7);
    const barW = Math.min(sectionW - pad * 2, sectionW / 2);
    const totalH = lines.length * lineH + barH + 5;
    let y = panelY + (panelH - totalH) / 2;
    const x = sectionX + pad;

    for (const { text, color } of lines) {
      const t2 = this.scene.add.text(x, y, text, {
        fontSize: `${fontSize}px`, fontFamily: 'Arial', color,
      }).setDepth(51);
      this.texts.push(t2);
      y += lineH;
    }

    // Progress bar
    const progress = Math.min(100, player.getProgress());
    y += 3;

    this.gfx.fillStyle(COLORS.progress_bar_bg, 1);
    this.gfx.fillRect(x, y, barW, barH);

    this.gfx.fillStyle(COLORS.progress_bar_fill, 1);
    this.gfx.fillRect(x, y, barW * (progress / 100), barH);

    const pText = this.scene.add.text(x + barW + pad, y + barH / 2, `${Math.round(progress)}%`, {
      fontSize: `${fontSize}px`, fontFamily: 'Arial', color: '#000',
    }).setOrigin(0, 0.5).setDepth(51);
    this.texts.push(pText);
  }

  destroy() {
    for (const t of this.texts) t.destroy();
    this.gfx.destroy();
  }
}
