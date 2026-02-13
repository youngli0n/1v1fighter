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
    initConfig(this.scale.width, this.scale.height);
    this.scene.start('GameScene', { newMatch: true });
  }
}
