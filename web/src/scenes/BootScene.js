import Phaser from 'phaser';
import { initConfig } from '../config.js';

/**
 * Tiny boot scene: calculate tile size from screen dimensions,
 * then hand off to GameScene.
 */
export class BootScene extends Phaser.Scene {
  constructor() {
    super('BootScene');
  }

  create() {
    // Use visualViewport for accurate dimensions on iOS Safari
    const vv = window.visualViewport;
    const w = vv ? Math.round(vv.width) : this.scale.width;
    const h = vv ? Math.round(vv.height) : this.scale.height;
    initConfig(w, h);
    this.scene.start('GameScene', { newMatch: true });
  }
}
