import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene.js';
import { GameScene } from './scenes/GameScene.js';

/**
 * Entry point — creates the Phaser game instance.
 *
 * Screen size is read once; BootScene will call initConfig()
 * to calculate tile_size and panel height before anything renders.
 */
const config = {
  type: Phaser.AUTO,
  width: window.innerWidth,
  height: window.innerHeight,
  backgroundColor: '#ffffff',
  parent: document.body,
  scale: {
    mode: Phaser.Scale.NONE,       // we size to window ourselves
    autoCenter: Phaser.Scale.NO_CENTER,
  },
  input: {
    activePointers: 3,             // support multi-touch
  },
  scene: [BootScene, GameScene],
};

new Phaser.Game(config);
