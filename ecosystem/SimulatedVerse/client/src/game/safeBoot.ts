/**
 * OWNERS: @team/game  TAGS: boot, safety, validation  STABILITY: prod
 * DEPENDS: server/routes.ts
 * INTEGRATION: {hud, save, agents}
 * HEALTH: {boot_smoke:true, unit:true}
 * NOTES: SOP-01 Rosetta Stone header. BD-01 Boot Smoke validation.
 */

// **BATTLE DRILL BD-01**: Boot Smoke validation with error banners
export async function safeBoot(): Promise<{ok: boolean, reason?: string, data?: any}> {
  try {
    console.log('[BOOT] Starting safeBoot validation...');
    
    const response = await fetch("/api/game/boot-smoke");
    if (!response.ok) {
      const error = `HTTP ${response.status}: ${response.statusText}`;
      console.error('[BOOT] Boot smoke failed:', error);
      return { ok: false, reason: error };
    }
    
    const bootData = await response.json();
    console.log('[BOOT] Boot smoke response:', bootData);
    
    // **VALIDATION**: Never blank screen - always show reason
    if (!bootData.ok) {
      return { ok: false, reason: bootData.reason || 'Boot validation failed' };
    }
    
    if (bootData.summary?.resources === 0) {
      return { ok: false, reason: 'No game resources available - seed default content pack' };
    }
    
    if (bootData.summary?.routes === 0) {
      return { ok: false, reason: 'No API routes available - check server health' };
    }
    
    console.log('[BOOT] ✅ Safe boot validation passed');
    return { ok: true, data: bootData };
    
  } catch (error) {
    const reason = error instanceof Error ? error.message : 'Unknown boot error';
    console.error('[BOOT] Safe boot exception:', reason);
    return { ok: false, reason };
  }
}