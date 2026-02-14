/**
 * PlayerProfile — saves and loads the player's name + avatar.
 *
 * Think of this like a save file for your player card.
 * It stores your name and avatar in localStorage so the
 * browser remembers you next time you play.
 */

// Built-in emoji avatars players can pick from
export const AVATARS = [
  '⚔️', '🥷', '🤖', '👽', '💀', '🔥',
  '⚡', '🦊', '🐉', '🎯', '🛡️', '👾',
];

const STORAGE_KEY = '1v1fighter_profile';

export class PlayerProfile {
  constructor() {
    this._load();
  }

  /** Load profile from localStorage, or create a default one */
  _load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const data = JSON.parse(saved);
        this.name = data.name || this._randomName();
        this.avatar = data.avatar || AVATARS[0];
      } else {
        this.name = this._randomName();
        this.avatar = AVATARS[0];
      }
    } catch {
      this.name = this._randomName();
      this.avatar = AVATARS[0];
    }
  }

  /** Save current profile to localStorage */
  save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        name: this.name,
        avatar: this.avatar,
      }));
    } catch {
      // localStorage might be full or blocked — that's okay
    }
  }

  /** Generate a random name like "Player_7382" */
  _randomName() {
    const num = Math.floor(1000 + Math.random() * 9000);
    return `Player_${num}`;
  }

  /** Returns a simple object to send over the network */
  toData() {
    return { name: this.name, avatar: this.avatar };
  }

  /** Check if the avatar is a custom upload (data URL) vs built-in emoji */
  isCustomAvatar() {
    return this.avatar.startsWith('data:');
  }
}
