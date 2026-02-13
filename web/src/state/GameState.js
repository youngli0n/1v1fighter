import { GAME_CONFIG } from '../config.js';

/**
 * Tracks rounds, match score, countdown, and win conditions.
 * Ported from game_state.py.
 */
export class GameState {
  constructor() {
    this.resetMatch();
  }

  resetMatch() {
    this.roundWins = [0, 0];       // [p1, p2]
    this.currentRound = 1;
    this.roundHistory = [];        // array of winner numbers (1 or 2)
    this.matchOver = false;
    this.roundOver = false;
    this.countdownActive = true;
    this.countdownTicks = GAME_CONFIG.countdown_ticks;
    this.lastCountdownUpdate = Date.now() / 1000;
  }

  resetRound() {
    this.roundOver = false;
    this.countdownActive = true;
    this.countdownTicks = GAME_CONFIG.countdown_ticks;
    this.lastCountdownUpdate = Date.now() / 1000;
  }

  /**
   * Tick the countdown timer.
   * @returns {boolean} true when countdown finishes.
   */
  updateCountdown(currentTime) {
    if (!this.countdownActive) return false;

    const interval = GAME_CONFIG.countdown_duration / 4; // 4 steps: 3,2,1,GO
    if (currentTime - this.lastCountdownUpdate >= interval) {
      this.countdownTicks -= 1;
      this.lastCountdownUpdate = currentTime;
      if (this.countdownTicks < 0) {
        this.countdownActive = false;
        return true;
      }
    }
    return false;
  }

  recordRoundWin(winnerNum) {
    this.roundWins[winnerNum - 1] += 1;
    this.roundHistory.push(winnerNum);
    this.roundOver = true;

    if (this.roundWins[winnerNum - 1] >= GAME_CONFIG.rounds_to_win) {
      this.matchOver = true;
    }

    this.currentRound += 1;
  }

  getMatchScore() {
    return `P1: ${this.roundWins[0]}  P2: ${this.roundWins[1]}`;
  }
}
