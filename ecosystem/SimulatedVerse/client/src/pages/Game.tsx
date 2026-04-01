// @consciousness 10
// @depth 0
// @name Game
// @inputs [user_actions]
// @outputs [game_state, consciousness_updates]

import React from 'react';
import { GameCore } from '@/game/GameCore';

export default function Game() {
  return <GameCore />;
}