/**
 * SocketClient — thin wrapper around Socket.IO for multiplayer.
 *
 * This is like a walkie-talkie: you press a button to talk,
 * and the relay server delivers your message to the other player.
 */

import { io } from 'socket.io-client';

/**
 * The relay server URL.
 * In development:  http://localhost:3000
 * In production:   set via VITE_RELAY_URL env var, or auto-detect.
 */
const RELAY_URL =
  import.meta.env.VITE_RELAY_URL ||
  (window.location.hostname === 'localhost'
    ? 'http://localhost:3000'
    : 'https://onev1fighter-relay.onrender.com');

export class SocketClient {
  constructor() {
    this.socket = null;
    this.role = null;    // 'host' | 'guest' | null
    this.roomCode = null;

    // Callbacks — set these from the outside
    this.onRoomCreated = null;   // (code) => {}
    this.onJoined = null;        // (code) => {}
    this.onJoinError = null;     // (message) => {}
    this.onGuestJoined = null;   // (profile) => {}  — host receives guest's profile
    this.onGameStart = null;     // (data) => {}  — guest receives initial game data
    this.onGameState = null;     // (data) => {}  — guest receives frame state
    this.onGuestInput = null;    // (data) => {}  — host receives guest inputs
    this.onPeerDisconnected = null; // () => {}
    this.onPeerProfile = null;   // (profile) => {}  — receive the other player's profile
    this.onPeerReady = null;     // () => {}  — the other player pressed Ready
  }

  /** Connect to the relay server. Returns a promise that resolves when connected. */
  connect() {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) { resolve(); return; }

      this.socket = io(RELAY_URL, {
        transports: ['websocket'],   // skip polling, go straight to WebSocket
        reconnection: true,
        reconnectionAttempts: 5,
        timeout: 10000,
      });

      this.socket.on('connect', () => {
        console.log('[SocketClient] connected:', this.socket.id);
        resolve();
      });

      this.socket.on('connect_error', (err) => {
        console.error('[SocketClient] connect error:', err.message);
        reject(err);
      });

      // Wire up all relay events
      this.socket.on('room_created', ({ code }) => {
        this.role = 'host';
        this.roomCode = code;
        this.onRoomCreated?.(code);
      });

      this.socket.on('joined', ({ code }) => {
        this.role = 'guest';
        this.roomCode = code;
        this.onJoined?.(code);
      });

      this.socket.on('join_error', ({ message }) => {
        this.onJoinError?.(message);
      });

      this.socket.on('guest_joined', (data) => {
        this.onGuestJoined?.(data?.profile);
      });

      this.socket.on('peer_profile', (data) => {
        this.onPeerProfile?.(data?.profile);
      });

      this.socket.on('peer_ready', () => {
        this.onPeerReady?.();
      });

      this.socket.on('game_start', (data) => {
        this.onGameStart?.(data);
      });

      this.socket.on('game_state', (data) => {
        this.onGameState?.(data);
      });

      this.socket.on('guest_input', (data) => {
        this.onGuestInput?.(data);
      });

      this.socket.on('peer_disconnected', () => {
        this.onPeerDisconnected?.();
      });
    });
  }

  // ── Actions ─────────────────────────────────────────────────

  createRoom(profile) {
    this.socket.emit('create_room', { profile });
  }

  joinRoom(code, profile) {
    this.socket.emit('join_room', { code: code.toUpperCase(), profile });
  }

  /** Tell the server you're ready to play */
  sendReady() {
    this.socket.emit('player_ready');
  }

  /** Host sends initial game data (walls, collectibles) to guest */
  sendGameStart(data) {
    this.socket.emit('game_start', data);
  }

  /** Host sends game state every frame */
  sendGameState(data) {
    this.socket.emit('game_state', data);
  }

  /** Guest sends their touch inputs every frame */
  sendInput(data) {
    this.socket.emit('guest_input', data);
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
    this.role = null;
    this.roomCode = null;
  }
}
