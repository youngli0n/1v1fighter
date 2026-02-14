/**
 * 1v1 Fighter — Relay Server
 *
 * This server has ZERO game logic. It just:
 *   1. Lets a host create a room (gets a 4-character code)
 *   2. Lets a guest join that room
 *   3. Relays messages between them
 *
 * Think of it like a telephone switchboard — it connects two
 * people but doesn't listen to their conversation.
 */

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);

const io = new Server(server, {
  cors: {
    origin: '*',                 // allow any origin (the PWA on GitHub Pages)
    methods: ['GET', 'POST'],
  },
});

// ── Room storage ─────────────────────────────────────────────
// Map of roomCode → { hostId, guestId }
const rooms = new Map();

/** Generate a random 4-character room code like "XK72" */
function makeCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // no I/O/0/1 to avoid confusion
  let code;
  do {
    code = '';
    for (let i = 0; i < 4; i++) code += chars[Math.floor(Math.random() * chars.length)];
  } while (rooms.has(code)); // ensure uniqueness
  return code;
}

// ── Health check endpoint (Render pings this) ────────────────
app.get('/', (_req, res) => {
  res.send(`1v1 Fighter relay — ${rooms.size} active room(s)`);
});

// ── Socket.IO events ─────────────────────────────────────────
io.on('connection', (socket) => {
  console.log(`+ connect  ${socket.id}`);

  // ── Host creates a room ──────────────────────────────────
  socket.on('create_room', ({ profile } = {}) => {
    const code = makeCode();
    rooms.set(code, {
      hostId: socket.id,
      guestId: null,
      hostProfile: profile || null,
      guestProfile: null,
      hostReady: false,
      guestReady: false,
    });
    socket.join(code);
    socket.data.room = code;
    socket.data.role = 'host';
    socket.emit('room_created', { code });
    console.log(`  room ${code} created by ${socket.id}`);
  });

  // ── Guest joins a room ───────────────────────────────────
  socket.on('join_room', ({ code, profile } = {}) => {
    const room = rooms.get(code);
    if (!room) {
      socket.emit('join_error', { message: 'Room not found' });
      return;
    }
    if (room.guestId) {
      socket.emit('join_error', { message: 'Room is full' });
      return;
    }

    room.guestId = socket.id;
    room.guestProfile = profile || null;
    socket.join(code);
    socket.data.room = code;
    socket.data.role = 'guest';

    // Send guest's profile to host, and host's profile to guest
    io.to(room.hostId).emit('guest_joined', { profile: room.guestProfile });
    socket.emit('joined', { code });
    socket.emit('peer_profile', { profile: room.hostProfile });
    console.log(`  room ${code} guest joined: ${socket.id}`);
  });

  // ── Player signals they are ready ──────────────────────
  socket.on('player_ready', () => {
    const code = socket.data.room;
    const room = code ? rooms.get(code) : null;
    if (!room) return;

    if (socket.data.role === 'host') {
      room.hostReady = true;
      if (room.guestId) io.to(room.guestId).emit('peer_ready');
    } else if (socket.data.role === 'guest') {
      room.guestReady = true;
      io.to(room.hostId).emit('peer_ready');
    }
    console.log(`  room ${code} — ${socket.data.role} is ready`);
  });

  // ── Host sends initial game data (walls, collectibles) ──
  socket.on('game_start', (data) => {
    const room = rooms.get(socket.data.room);
    if (!room || socket.data.role !== 'host') return;
    io.to(room.guestId).emit('game_start', data);
  });

  // ── Host sends game state every frame ────────────────────
  socket.on('game_state', (data) => {
    const room = rooms.get(socket.data.room);
    if (!room || socket.data.role !== 'host') return;
    io.to(room.guestId).emit('game_state', data);
  });

  // ── Guest sends their inputs every frame ─────────────────
  socket.on('guest_input', (data) => {
    const room = rooms.get(socket.data.room);
    if (!room || socket.data.role !== 'guest') return;
    io.to(room.hostId).emit('guest_input', data);
  });

  // ── Disconnect cleanup ───────────────────────────────────
  socket.on('disconnect', () => {
    const code = socket.data.room;
    if (code && rooms.has(code)) {
      const room = rooms.get(code);
      // Notify the other player
      if (socket.data.role === 'host') {
        if (room.guestId) io.to(room.guestId).emit('peer_disconnected');
        rooms.delete(code);
      } else if (socket.data.role === 'guest') {
        room.guestId = null;
        room.guestProfile = null;
        room.guestReady = false;
        room.hostReady = false;  // reset host ready too since guest left
        io.to(room.hostId).emit('peer_disconnected');
      }
      console.log(`  room ${code} — ${socket.data.role} disconnected`);
    }
    console.log(`- disconnect ${socket.id}`);
  });
});

// ── Start ────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Relay server listening on port ${PORT}`);
});
