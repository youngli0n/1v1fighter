import Phaser from 'phaser';
import { initConfig } from '../config.js';
import { SocketClient } from '../net/SocketClient.js';

/**
 * Tiny boot scene: calculate tile size from screen dimensions,
 * then hand off to LobbyScene (the main menu).
 */
export class BootScene extends Phaser.Scene {
  constructor() {
    super('BootScene');
  }

  create() {
    const vv = window.visualViewport;
    const w = vv ? Math.round(vv.width) : this.scale.width;
    const h = vv ? Math.round(vv.height) : this.scale.height;
    initConfig(w, h);

    // Create a shared SocketClient and pass it to LobbyScene
    const net = new SocketClient();
    this.scene.start('LobbyScene', { net });
  }
}
