import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene.js';
import { LobbyScene } from './scenes/LobbyScene.js';
import { GameScene } from './scenes/GameScene.js';
import { initConfig } from './config.js';
import { SocketClient } from './net/SocketClient.js';

/**
 * Return the actual visible viewport size.
 * On iOS Safari, window.innerHeight includes the area behind the
 * toolbar — visualViewport gives the real usable area instead.
 */
function getViewportSize() {
  if (window.visualViewport) {
    return { w: Math.round(window.visualViewport.width), h: Math.round(window.visualViewport.height) };
  }
  return { w: window.innerWidth, h: window.innerHeight };
}

/**
 * Entry point — creates the Phaser game instance.
 * We use a tiny delay to ensure the viewport has settled,
 * which avoids the "tiny canvas in top-left" bug on PWA launch.
 */
function boot() {
  const { w, h } = getViewportSize();

  const config = {
    type: Phaser.AUTO,
    width: w,
    height: h,
    backgroundColor: '#ffffff',
    parent: document.body,
    scale: {
      mode: Phaser.Scale.RESIZE,
      autoCenter: Phaser.Scale.NO_CENTER,   // canvas starts at (0,0)
    },
    input: {
      activePointers: 3,
    },
    scene: [BootScene, LobbyScene, GameScene],
  };

  const game = new Phaser.Game(config);

  /** Central resize handler — fires for Safari toolbar, orientation, PWA launch, etc. */
  function onResize() {
    const { w: nw, h: nh } = getViewportSize();
    game.scale.resize(nw, nh);
    initConfig(nw, nh);

    const gs = game.scene.getScene('GameScene');
    if (gs && gs.scene.isActive()) {
      gs.handleResize();
    }
  }

  // visualViewport fires its own resize event when Safari's toolbar shows/hides
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', onResize);
  }
  window.addEventListener('resize', onResize);

  // Extra safety: recheck after a short delay (covers PWA launch edge case)
  setTimeout(onResize, 300);
}

// Wait for viewport to be ready before booting Phaser
if (document.readyState === 'complete') {
  requestAnimationFrame(boot);
} else {
  window.addEventListener('load', () => requestAnimationFrame(boot));
}
