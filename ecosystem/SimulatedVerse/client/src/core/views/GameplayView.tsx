/**
 * 🎮 Gameplay View - Core Incremental Mechanics
 * Main gameplay interface with progression systems
 * Integrated GameShell for ASCII gameplay loop + Interactive Actions Panel
 */

import React, { useState } from 'react';
import GameShell from '../../components/GameShell';
import GameplayActionsPanel from '../../components/GameplayActionsPanel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function GameplayView() {
  return (
    <div className="gameplay-view h-full bg-black" data-testid="gameplay-view">
      <Tabs defaultValue="actions" className="h-full">
        <TabsList className="w-full grid grid-cols-2 bg-gray-900">
          <TabsTrigger value="actions" data-testid="tab-actions">🎮 Actions</TabsTrigger>
          <TabsTrigger value="ascii" data-testid="tab-ascii">📟 ASCII View</TabsTrigger>
        </TabsList>
        
        <TabsContent value="actions" className="h-full mt-0">
          <GameplayActionsPanel />
        </TabsContent>
        
        <TabsContent value="ascii" className="h-full mt-0">
          <GameShell />
        </TabsContent>
      </Tabs>
    </div>
  );
}