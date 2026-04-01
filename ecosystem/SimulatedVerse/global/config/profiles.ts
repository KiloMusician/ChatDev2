// [Ω:root:config@profiles] Profile loading and management
import { readFile } from 'fs/promises';
import { join } from 'path';

export interface Profile {
  name: string;
  version: string;
  enabledModules: string[];
  requiredSecrets: string[];
  optionalSecrets: string[];
  features: Record<string, boolean>;
  limits: Record<string, number>;
  ui: Record<string, any>;
  automation: Record<string, any>;
}

export async function loadProfile(profileName: string): Promise<Profile> {
  try {
    const profilePath = join(process.cwd(), 'config', 'profiles', `${profileName}.json`);
    const content = await readFile(profilePath, 'utf-8');
    const profile = JSON.parse(content) as Profile;
    
    console.log(`[CONFIG] ✓ Loaded profile: ${profile.name} v${profile.version}`);
    return profile;
  } catch (error) {
    console.error(`[CONFIG] ❌ Failed to load profile: ${profileName}`);
    throw new Error(`Profile not found: ${profileName}. Available: dev, ci, prod`);
  }
}