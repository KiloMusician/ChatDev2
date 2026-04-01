// [Ω:root:bootstrap@entry] System initialization gate
import { loadProfile } from '../config/profiles';
import { validateSecrets } from '../config/guards';
import { setupModules } from './registry/loader.ts';
import { printSplash } from '../ui/ascii/splash';

export interface BootContext {
  profile: string;
  startTime: number;
  modules: Record<string, any>;
  fingerprint: string;
}

/**
 * 🜁 Bootstrap Gate - Single entry point for all initialization
 * Usage: await boot(process.env.BOOT_PROFILE || 'dev')
 */
export async function boot(profileName: string = 'dev'): Promise<BootContext> {
  const startTime = Date.now();
  
  // Phase 1: ASCII splash and environment
  await printSplash();
  console.log(`[BOOT] Initializing CoreLink Foundation - Profile: ${profileName}`);
  
  // Phase 2: Load configuration and validate environment
  const profile = await loadProfile(profileName);
  const secrets = await validateSecrets(profile.requiredSecrets);
  
  // Phase 3: Module registration and dependency resolution
  const modules = await setupModules(profile.enabledModules);
  
  // Phase 4: Generate boot fingerprint for debugging
  const fingerprint = generateFingerprint(profile, Object.keys(modules));
  
  const bootTime = Date.now() - startTime;
  console.log(`[BOOT] ✓ System ready in ${bootTime}ms - Fingerprint: ${fingerprint}`);
  
  return {
    profile: profileName,
    startTime,
    modules,
    fingerprint
  };
}

function generateFingerprint(profile: any, moduleIds: string[]): string {
  const components = [
    profile.name,
    profile.version || '1.0.0',
    moduleIds.sort().join(','),
    process.env.NODE_ENV || 'development'
  ];
  
  // Simple hash for debugging (not crypto)
  return components.join(':').split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
    return a & a;
  }, 0).toString(16);
}