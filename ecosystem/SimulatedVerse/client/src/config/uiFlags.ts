// client/src/config/uiFlags.ts
// Feature flags to gate legacy vs provisioned modes (no deletions)

export const UI_FLAGS = {
  MODE: (import.meta as any).env?.VITE_UI_MODE ?? 
        (typeof process !== 'undefined' ? process.env.UI_MODE : undefined) ?? 
        "legacy", // "legacy" | "provisioned" - legacy enables full agent interaction
  
  ENABLE_LEGACY_BUS: (import.meta as any).env?.VITE_ENABLE_LEGACY_BUS === "true",
  
  DEBUG_PROVISIONER: (import.meta as any).env?.VITE_DEBUG_PROVISIONER === "true",
  
  SIMULATION_ENABLED: (import.meta as any).env?.VITE_SIMULATION_ENABLED !== "false", // default true
};

// Guard for UI write operations
export function guardNoWrite(reason = "UI cannot mutate Real System") {
  if (UI_FLAGS.MODE === "provisioned") {
    throw new Error(`[GUARD] ${reason}`);
  }
}