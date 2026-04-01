/* 
OWNERS: team/infra, ai/prime
TAGS: infra, scope, resolver, workspace
STABILITY: stable  
INTEGRATIONS: agent/gateway, testing/chamber, ops/proof
*/

import fs from "fs";
import path from "path";
import yaml from "js-yaml";
import micromatch from "micromatch";
import { execSync } from "child_process";

type ModeSpec = { 
  include: string[]; 
  exclude?: string[]; 
  tags_any?: string[] 
};

type Config = { 
  modes: Record<string, ModeSpec>; 
  combos?: Record<string, {modes: string[]}>;
  policies?: Record<string, any>;
};

const CONFIG_PATH = "ops/viewmodes.yaml";
let cachedConfig: Config | null = null;

function loadConfig(): Config {
  if (!cachedConfig) {
    try {
      const content = fs.readFileSync(CONFIG_PATH, "utf8");
      cachedConfig = yaml.load(content) as Config;
    } catch (error) {
      console.warn(`[Scope] Failed to load ${CONFIG_PATH}:`, error);
      cachedConfig = { modes: { everything: { include: ["**/*"] } } };
    }
  }
  return cachedConfig;
}

export type ScopeSelection = { 
  view: string | string[]; 
  extraInclude?: string[]; 
  extraTags?: string[];
  maxFiles?: number;
};

export type ScopeResult = {
  files: string[];
  tags: string[];
  view: string[];
  policies: Record<string, any>;
  stats: {
    total_files: number;
    by_extension: Record<string, number>;
    missing_headers: string[];
  };
};

export function resolveScope(sel: ScopeSelection): ScopeResult {
  const cfg = loadConfig();
  const views = Array.isArray(sel.view) ? sel.view : [sel.view];
  
  const flatten = (view: string): ModeSpec => {
    if (cfg.combos?.[view]) {
      const modes = cfg.combos[view].modes.map(v => flatten(v));
      return {
        include: modes.flatMap(x => x.include),
        exclude: modes.flatMap(x => x.exclude || []),
        tags_any: modes.flatMap(x => x.tags_any || [])
      };
    }
    return cfg.modes[view] ?? { include: [], exclude: [] };
  };

  const merged = views.map(flatten).reduce<ModeSpec>((acc, cur) => ({
    include: [...(acc.include || []), ...(cur.include || [])],
    exclude: [...(acc.exclude || []), ...(cur.exclude || [])],
    tags_any: [...(acc.tags_any || []), ...(cur.tags_any || [])]
  }), { include: [] });

  if (sel.extraInclude) merged.include.push(...sel.extraInclude);
  if (sel.extraTags) merged.tags_any!.push(...sel.extraTags);

  // Materialize file list using git ls-files for performance
  const allFiles = execListFiles();
  let inScope = micromatch(allFiles, merged.include, { 
    ignore: merged.exclude || [],
    dot: true 
  });

  // Apply tag filtering if specified
  if (merged.tags_any?.length) {
    inScope = inScope.filter((f: string) => fileHasAnyTag(f, merged.tags_any!));
  }

  // Apply file limit
  const maxFiles = sel.maxFiles || cfg.policies?.max_scope_files || 500;
  if (inScope.length > maxFiles) {
    inScope = inScope.slice(0, maxFiles);
    console.warn(`[Scope] Truncated to ${maxFiles} files for performance`);
  }

  // Generate statistics
  const stats = generateStats(inScope);

  return { 
    files: inScope, 
    tags: merged.tags_any || [], 
    view: views,
    policies: cfg.policies || {},
    stats
  };
}

function execListFiles(): string[] {
  try {
    const out = execSync("git ls-files", { 
      stdio: ["ignore", "pipe", "ignore"], 
      encoding: "utf8",
      cwd: process.cwd()
    });
    const files = out.trim().split("\n").filter(Boolean);
    console.log(`[Scope] Found ${files.length} files via git ls-files`);
    return files;
  } catch (error) {
    console.warn(`[Scope] git ls-files failed:`, error);
    // Fallback to basic file walk
    return fallbackListFiles();
  }
}

function fallbackListFiles(): string[] {
  const files: string[] = [];
  const walkDir = (dir: string, basePath = "") => {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.name.startsWith('.') && entry.name !== '.env') continue;
        if (entry.name === 'node_modules') continue;
        
        const fullPath = path.join(dir, entry.name);
        const relativePath = path.join(basePath, entry.name);
        
        if (entry.isDirectory()) {
          walkDir(fullPath, relativePath);
        } else {
          files.push(relativePath);
        }
      }
    } catch (error) {
      console.warn(`[Scope] Error walking directory ${dir}:`, error);
    }
  };
  
  walkDir(process.cwd());
  console.log(`[Scope] Fallback found ${files.length} files`);
  return files;
}

function fileHasAnyTag(filePath: string, tags: string[]): boolean {
  try {
    const content = fs.readFileSync(filePath, "utf8").slice(0, 4096).toLowerCase();
    const hasTagsLine = content.includes("tags:");
    return hasTagsLine && tags.some(tag => content.includes(tag.toLowerCase()));
  } catch {
    return false;
  }
}

function generateStats(files: string[]): ScopeResult['stats'] {
  const byExtension: Record<string, number> = {};
  const missingHeaders: string[] = [];

  for (const file of files) {
    const ext = path.extname(file) || 'no-ext';
    byExtension[ext] = (byExtension[ext] || 0) + 1;

    // Check for Rosetta headers in code files
    if (['.ts', '.tsx', '.js', '.jsx'].includes(ext)) {
      if (!hasRosettaHeader(file)) {
        missingHeaders.push(file);
      }
    }
  }

  return {
    total_files: files.length,
    by_extension: byExtension,
    missing_headers: missingHeaders
  };
}

function hasRosettaHeader(filePath: string): boolean {
  try {
    const content = fs.readFileSync(filePath, "utf8").slice(0, 1024);
    return content.includes("OWNERS:") && content.includes("TAGS:");
  } catch {
    return false;
  }
}

export function listAvailableModes(): { modes: string[]; combos: string[] } {
  const cfg = loadConfig();
  return {
    modes: Object.keys(cfg.modes),
    combos: Object.keys(cfg.combos || {})
  };
}

export function validateScope(sel: ScopeSelection): { valid: boolean; errors: string[] } {
  const cfg = loadConfig();
  const errors: string[] = [];
  const views = Array.isArray(sel.view) ? sel.view : [sel.view];

  for (const view of views) {
    if (!cfg.modes[view] && !cfg.combos?.[view]) {
      errors.push(`Unknown view mode: ${view}`);
    }
  }

  return { valid: errors.length === 0, errors };
}