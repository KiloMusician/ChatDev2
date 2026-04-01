/**
 * Terminal Command Bus - Interactive command system for Culture-Ship
 */

import { PlayerState, useGame } from "./store";
import { UPGRADES } from "../../../GameDev/gameplay/progression/Upgrades";
import { calculateCostForLevel, canAffordCost } from "../services/CostCurves";

export type Command =
  | { kind: "STATUS" }
  | { kind: "INV" }
  | { kind: "BUY"; upgrade: string; amount?: number }
  | { kind: "SET_THEME"; theme: "classic" | "holo" }
  | { kind: "HELP" }
  | { kind: "CLEAR" }
  | { kind: "FLAGS" }
  | { kind: "RESET" }
  | { kind: "SCAN"; scope?: string };

export interface CommandResult {
  ok: boolean;
  messages: string[];
}

export function parseCommand(input: string): Command | null {
  const parts = input.trim().toLowerCase().split(/\s+/);
  const cmd = parts[0];
  
  switch (cmd) {
    case "status":
      return { kind: "STATUS" };
      
    case "inv":
    case "inventory":
      return { kind: "INV" };
      
    case "buy":
      if (parts.length < 2) return null;
      const upgrade = parts[1]?.toUpperCase() || "";
      const amount = parts[2] ? parseInt(parts[2]) : 1;
      return { kind: "BUY", upgrade, amount };
      
    case "theme":
      if (parts.length < 2) return null;
      const theme = parts[1] as "classic" | "holo";
      return { kind: "SET_THEME", theme };
      
    case "help":
      return { kind: "HELP" };
      
    case "clear":
      return { kind: "CLEAR" };
      
    case "flags":
      return { kind: "FLAGS" };
      
    case "reset":
      return { kind: "RESET" };
      
    case "scan":
      return { kind: "SCAN", scope: parts[1] };
      
    default:
      return null;
  }
}

export function executeCommand(cmd: Command): CommandResult {
  const game = useGame.getState();
  
  switch (cmd.kind) {
    case "STATUS":
      return {
        ok: true,
        messages: [
          `> SHIP STATUS:`,
          `> Tick: ${game.tick}`,
          `> Phase: ${game.uiPhase}`,
          `> Mode: ${game.mode}`,
          `> Upgrades: ${Object.keys(game.upgrades).length}`,
          `> Total Energy Generated: ${game.totalEnergyGenerated}`,
          `> Total Scrap Collected: ${game.totalScrapCollected}`
        ]
      };
      
    case "INV":
      const resources = Object.entries(game.inv).filter(([,v]) => v > 0);
      return {
        ok: true,
        messages: [
          `> INVENTORY:`,
          ...resources.map(([k,v]) => `> ${k}: ${v}`)
        ]
      };
      
    case "BUY":
      const upgrade = UPGRADES.find(u => u.id === cmd.upgrade);
      if (!upgrade) {
        return {
          ok: false,
          messages: [`> Error: Unknown upgrade '${cmd.upgrade}'`]
        };
      }
      
      const level = game.getUpgradeLevel(cmd.upgrade);
      const cost = calculateCostForLevel(upgrade.pricer, level + 1);
      
      if (!canAffordCost(game, cost)) {
        return {
          ok: false,
          messages: [`> Error: Insufficient resources for ${upgrade.title}`]
        };
      }
      
      if (game.spendResources(cost)) {
        game.buyUpgrade(cmd.upgrade, cmd.amount || 1);
        
        // Apply upgrade effects
        if (upgrade.grants) {
          Object.entries(upgrade.grants).forEach(([resource, amount]) => {
            game.addResource(resource as any, amount);
          });
        }
        
        if (upgrade.flags) {
          upgrade.flags.forEach(flag => game.setFlag(flag, true));
        }
        
        return {
          ok: true,
          messages: [`> ${upgrade.title} upgraded to level ${level + 1}`]
        };
      }
      
      return {
        ok: false,
        messages: [`> Error: Purchase failed`]
      };
      
    case "SET_THEME":
      if (cmd.theme === "holo" && !game.hasFlag("UI_THEME_HOLOGRAPHIC")) {
        return {
          ok: false,
          messages: [`> Error: Holographic theme not unlocked`]
        };
      }
      
      return {
        ok: true,
        messages: [`> Theme set to ${cmd.theme}`]
      };
      
    case "FLAGS":
      const activeFlags = Object.entries(game.flags).filter(([,v]) => v).map(([k]) => k);
      return {
        ok: true,
        messages: [
          `> ACTIVE FLAGS:`,
          ...activeFlags.map(flag => `> ${flag}`)
        ]
      };
      
    case "RESET":
      game.reset();
      return {
        ok: true,
        messages: [`> System reset complete`]
      };
      
    case "SCAN":
      return {
        ok: true,
        messages: [
          `> SCAN RESULTS:`,
          `> Available upgrades: ${UPGRADES.length}`,
          `> Unlocked features: ${Object.values(game.flags).filter(Boolean).length}`,
          `> Current consciousness level: ${((game.totalEnergyGenerated + game.totalScrapCollected) / 100).toFixed(1)}%`
        ]
      };
      
    case "HELP":
      return {
        ok: true,
        messages: [
          `> AVAILABLE COMMANDS:`,
          `> status - Show ship status`,
          `> inv - Show inventory`,
          `> buy <upgrade> [amount] - Purchase upgrade`,
          `> theme <classic|holo> - Change theme`,
          `> flags - Show active flags`,
          `> scan - Scan ship systems`,
          `> reset - Reset all progress`,
          `> clear - Clear terminal`,
          `> help - Show this help`
        ]
      };
      
    case "CLEAR":
      return { ok: true, messages: [] };
      
    default:
      return {
        ok: false,
        messages: [`> Unknown command`]
      };
  }
}