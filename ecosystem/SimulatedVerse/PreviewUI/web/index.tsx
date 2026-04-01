/**
 * Entry point for UI Metamorphosis system
 */

export { GameShell } from "./core/GameShell";
export { useGame } from "./core/store";
export { CrashConsole } from "./panels/CrashConsole";
export { NanoFoundry } from "./panels/NanoFoundry";
export { parseCommand, executeCommand } from "./core/TerminalBus";
export type { PlayerState, PlayerActions } from "./core/store";
export type { Command, CommandResult } from "./core/TerminalBus";