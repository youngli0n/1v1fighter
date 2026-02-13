// Game configuration — ported from game_config.py
// All game settings live here for easy tweaking.

export const GAME_CONFIG = {
  // Tile / board dimensions (tiles)
  tile_size: 20,            // recalculated at boot based on screen size
  tiles_width: 40,
  tiles_height: 20,
  stats_panel_height: 100,  // recalculated at boot

  player_speed: 5,          // tiles per second
  fps: 60,

  // Shooting
  fire_rate: 5,             // shots per second
  projectile_speed: 100,    // tiles per second
  projectile_size: 1,       // tiles
  slow_factor: 0.5,
  slow_duration: 2.0,       // seconds
  speedup_factor: 1.5,
  speedup_duration: 1.0,

  // Shield
  shield_boost_duration: 4.0,
  shield_boost_amount: 0.05,
  shield_boost_max: 0.5,

  // Walls
  walls_enabled: true,
  num_walls_per_side: 5,
  wall_width: 0.5,
  wall_height: 3,
  wall_min_distance: 5,

  // Rounds
  rounds_to_win: 3,
  countdown_ticks: 3,
  countdown_duration: 2,    // total countdown sequence seconds

  // Collectibles
  collectibles_enabled: true,
  num_collectibles_per_match: 10,
  collectible_size: 0.8,
  speed_boost_duration: 5.0,
  speed_boost_multiplier: 1.3,
  speed_debuff_duration: 3.0,
  speed_debuff_multiplier: 0.7,

  // Collectible placement guardrails
  min_distance_from_border: 0.5,
  min_distance_from_player: 2.0,
  min_distance_between_collectibles: 1.0,
  min_distance_from_center_line: 1.0,
  collectible_generation_max_attempts: 100,

  // Computed at boot — filled in by initConfig()
  game_width: 0,
  game_height: 0,
};

// Colors as hex numbers (Phaser uses 0xRRGGBB)
export const COLORS = {
  background:        0xffffff,
  center_line:       0x000000,
  player1:           0xff0000,
  player2:           0x0000ff,
  stats_panel:       0xf0f0f0,
  progress_bar_bg:   0xc8c8c8,
  progress_bar_fill: 0x009600,
  text:              0x000000,
  speed_boost:       0x00ff00,
  speed_debuff:      0xff8c00,
  wall:              0x808080,
  projectile:        0x000000,
};

/**
 * Minimum tile size in pixels. If the default 40×20 grid would make
 * tiles smaller than this, we shrink the grid (fewer but bigger tiles)
 * so the game stays playable on small phone screens.
 */
const MIN_TILE_PX = 18;

/** Once the grid has been set on first boot, don't change it on resize. */
let _gridLocked = false;

/**
 * Call once at boot (and again on resize) to calculate tile_size,
 * panel height, etc. based on the actual visible dimensions.
 *
 * On the very first call, if the screen is too small for the default
 * 40×20 grid, we reduce tiles_width / tiles_height so each tile is
 * at least MIN_TILE_PX pixels. The 2 : 1 width-to-height ratio is kept
 * so the game board still looks right.
 */
export function initConfig(screenW, screenH) {
  const minStatsHeight = 60;

  // ── First boot: adapt grid for small screens ──────────────
  if (!_gridLocked) {
    _gridLocked = true;

    const testW = Math.floor(screenW / GAME_CONFIG.tiles_width);
    const testH = Math.floor((screenH - minStatsHeight) / GAME_CONFIG.tiles_height);

    if (Math.min(testW, testH) < MIN_TILE_PX) {
      // How many tiles fit at the minimum size?
      let tilesW = Math.floor(screenW / MIN_TILE_PX);
      let tilesH = Math.floor((screenH - minStatsHeight) / MIN_TILE_PX);

      // Keep the board's 2 : 1 aspect ratio
      if (tilesW > tilesH * 2) {
        tilesW = tilesH * 2;
      } else {
        tilesH = Math.floor(tilesW / 2);
      }

      // Even numbers keep the centre line clean
      tilesW -= tilesW % 2;
      tilesH -= tilesH % 2;

      // Safety minimums
      tilesW = Math.max(16, tilesW);
      tilesH = Math.max(8, tilesH);

      GAME_CONFIG.tiles_width = tilesW;
      GAME_CONFIG.tiles_height = tilesH;

      // Scale gameplay settings so the smaller board doesn't feel cramped
      const areaRatio = (tilesW * tilesH) / (40 * 20);
      GAME_CONFIG.num_walls_per_side = Math.max(2, Math.round(5 * areaRatio));
      GAME_CONFIG.wall_min_distance = Math.max(2, Math.round(5 * Math.sqrt(areaRatio)));
      GAME_CONFIG.num_collectibles_per_match = Math.max(4, Math.round(10 * areaRatio));
    }
  }

  // ── Always recalculate pixel sizes ────────────────────────
  const tileByWidth  = Math.floor(screenW / GAME_CONFIG.tiles_width);
  const tileByHeight = Math.floor((screenH - minStatsHeight) / GAME_CONFIG.tiles_height);
  const tileSize = Math.max(1, Math.min(tileByWidth, tileByHeight));

  const boardH = GAME_CONFIG.tiles_height * tileSize;

  GAME_CONFIG.tile_size = tileSize;
  GAME_CONFIG.stats_panel_height = Math.max(minStatsHeight, screenH - boardH);
  GAME_CONFIG.game_width = screenW;
  GAME_CONFIG.game_height = screenH;
}
