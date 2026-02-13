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
 * Call once at boot to calculate tile_size, panel height, etc.
 * based on the actual screen dimensions.
 */
export function initConfig(screenW, screenH) {
  let tileSize = Math.floor(screenW / GAME_CONFIG.tiles_width);
  const minStatsHeight = 80;

  if (GAME_CONFIG.tiles_height * tileSize + minStatsHeight > screenH) {
    tileSize = Math.floor((screenH - minStatsHeight) / GAME_CONFIG.tiles_height);
  }

  GAME_CONFIG.tile_size = tileSize;
  GAME_CONFIG.stats_panel_height = screenH - GAME_CONFIG.tiles_height * tileSize;
  GAME_CONFIG.game_width = screenW;
  GAME_CONFIG.game_height = screenH;
}
