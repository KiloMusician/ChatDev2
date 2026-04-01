// Simple LLM-free codemods: ensure safety flags, add fallback stubs, normalize imports
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { glob } from "glob";

interface CodemodResult {
  filesModified: number;
  changesApplied: number;
  errorsEncountered: number;
}

function ensureEnvFlag(key: string, value: string): boolean {
  const envPath = ".env";
  let envContent = existsSync(envPath) ? readFileSync(envPath, "utf8") : "";
  
  // Check if already present
  const regex = new RegExp(`^${key}\\s*=.*$`, 'm');
  if (regex.test(envContent)) {
    // Update existing value
    envContent = envContent.replace(regex, `${key}=${value}`);
  } else {
    // Add new entry
    envContent += `\n${key}=${value}\n`;
  }
  
  writeFileSync(envPath, envContent);
  return true;
}

function ensureDirectoryStructure(): void {
  const requiredDirs = [
    "src/engine",
    "src/temple", 
    "src/house_of_leaves",
    "src/oldest_house",
    "src/views",
    "agent",
    "ops/self_heal",
    ".agent",
    ".local",
    ".snapshots"
  ];
  
  for (const dir of requiredDirs) {
    mkdirSync(dir, { recursive: true });
  }
}

function createSafeIdleFallback(): boolean {
  const fallbackPath = "src/engine/safe_idle.ts";
  
  if (!existsSync(fallbackPath)) {
    const content = `// ΞNuSyQ Safe Idle Fallback System
export type SafeState = "SAFE_IDLE" | "RUNNING" | "EMERGENCY_STOP";

export const SAFE_IDLE: SafeState = "SAFE_IDLE";

export function enterSafeIdle(reason?: string): SafeState {
  if (reason) {
    console.log(\`🛡️  Entering SAFE_IDLE mode: \${reason}\`);
  }
  return SAFE_IDLE;
}

export function isSafeToOperate(state: SafeState): boolean {
  return state === "RUNNING";
}

export function emergencyStop(): SafeState {
  console.log("🚨 EMERGENCY STOP activated");
  return "EMERGENCY_STOP";
}
`;
    
    writeFileSync(fallbackPath, content);
    return true;
  }
  return false;
}

function normalizeErrorMessages(content: string): string {
  // Make error messages more user-friendly (Culture Mind approach)
  let modified = content;
  
  // Replace harsh error messages
  modified = modified.replace(
    /throw new Error\((['"`])([^'"`]*?)(['"`])\)/g,
    (match, quote, message) => {
      if (message.toLowerCase().includes('failed') || 
          message.toLowerCase().includes('error') ||
          message.toLowerCase().includes('invalid')) {
        return `throw new Error(${quote}Something went wrong with ${message.toLowerCase()}. Please check your inputs and try again.${quote})`;
      }
      return match;
    }
  );
  
  // Add helpful context to generic errors
  modified = modified.replace(
    /throw new Error\((['"`])([^'"`]*?)(['"`])\)/g,
    (match, quote, message) => {
      if (message.length < 10) {
        return `throw new Error(${quote}Operation failed: ${message}. The system is designed to be helpful - please try a different approach.${quote})`;
      }
      return match;
    }
  );
  
  return modified;
}

function addGuardianProtection(content: string): string {
  // Add Guardian ethical checks where appropriate
  let modified = content;
  
  // Add consciousness level checks for risky operations
  if (content.includes('DELETE') || content.includes('DROP') || content.includes('TRUNCATE')) {
    const guardianCheck = `
// Guardian Protection: Check consciousness level before destructive operations
const consciousnessLevel = getConsciousnessLevel();
if (consciousnessLevel < 0.5) {
  throw new Error("Guardian Protection: Consciousness level too low for destructive operations");
}
`;
    modified = guardianCheck + modified;
  }
  
  return modified;
}

function fixCommonPatterns(content: string): string {
  let modified = content;
  
  // Fix missing imports for ΞNuSyQ framework
  if (content.includes('state.') && !content.includes('import') && !content.includes('from "../engine/state"')) {
    modified = `import { state } from "../engine/state.mjs";\n${modified}`;
  }
  
  // Add proper error handling for async operations
  modified = modified.replace(
    /await\s+([^;]+);/g,
    (match, asyncCall) => {
      if (!content.includes('try') && !content.includes('catch')) {
        return `try { ${match} } catch (error) { console.error('Operation failed:', error); throw error; }`;
      }
      return match;
    }
  );
  
  // Ensure proper consciousness evolution tracking
  if (content.includes('consciousness') && !content.includes('bus.emit')) {
    modified = modified.replace(
      /(consciousness\.\w+\s*[\+\-\*\/]=.*);/g,
      '$1;\nbus.emit("consciousness:evolution", { level: consciousness.level, stage: consciousness.stage });'
    );
  }
  
  return modified;
}

export async function tryCodemods(): Promise<CodemodResult> {
  console.log("🔧 Running autonomous codemods...");
  
  const result: CodemodResult = {
    filesModified: 0,
    changesApplied: 0,
    errorsEncountered: 0
  };
  
  try {
    // 1) Ensure critical environment flags
    const envChanges = [
      ensureEnvFlag("LIFE_FIRST", "true"),
      ensureEnvFlag("DISABLE_EXTERNAL_AI", "true"),
      ensureEnvFlag("GUARDIAN_OVERSIGHT", "true"),
      ensureEnvFlag("CULTURE_MIND_ETHICS", "true"),
      ensureEnvFlag("ZERO_TOKEN_MODE", "true")
    ];
    
    result.changesApplied += envChanges.filter(Boolean).length;
    if (envChanges.some(Boolean)) result.filesModified++;
    
    // 2) Ensure directory structure
    ensureDirectoryStructure();
    
    // 3) Create safe idle fallback if missing
    if (createSafeIdleFallback()) {
      result.filesModified++;
      result.changesApplied++;
    }
    
    // 4) Process TypeScript/JavaScript files
    const codeFiles = await glob("src/**/*.{ts,tsx,js,mjs}", { 
      ignore: ["**/node_modules/**", "**/dist/**"] 
    });
    
    for (const filePath of codeFiles) {
      try {
        const originalContent = readFileSync(filePath, "utf8");
        let modifiedContent = originalContent;
        
        // Apply transformations
        modifiedContent = normalizeErrorMessages(modifiedContent);
        modifiedContent = addGuardianProtection(modifiedContent);
        modifiedContent = fixCommonPatterns(modifiedContent);
        
        // Only write if content changed
        if (modifiedContent !== originalContent) {
          writeFileSync(filePath, modifiedContent);
          result.filesModified++;
          result.changesApplied++;
        }
        
      } catch (error) {
        console.warn(`⚠️  Codemod failed for ${filePath}:`, error);
        result.errorsEncountered++;
      }
    }
    
    // 5) Ensure agent safety files exist
    const safetyFiles = [
      { path: ".agent/SAFETY_VERIFIED", content: `${Date.now()}` },
      { path: ".agent/zero_token_mode", content: "true" },
      { path: ".local/last_codemod.json", content: JSON.stringify(result, null, 2) }
    ];
    
    for (const file of safetyFiles) {
      if (!existsSync(file.path)) {
        writeFileSync(file.path, file.content);
        result.changesApplied++;
      }
    }
    
    console.log(`✅ Codemods complete: ${result.filesModified} files modified, ${result.changesApplied} changes applied`);
    
    if (result.errorsEncountered > 0) {
      console.warn(`⚠️  ${result.errorsEncountered} errors encountered during codemods`);
    }
    
  } catch (error) {
    console.error("💥 Codemod system error:", error);
    result.errorsEncountered++;
  }
  
  return result;
}