#!/usr/bin/env tsx
/**
 * ΞNuSyQ Edge Import Rewriter - Safe Path Updates
 * Uses ts-morph for AST-based import rewriting with path aliases
 */
import { Project, SyntaxKind } from "ts-morph";
import fs from "fs";
import { Command } from "commander";
import path from "path";
import chalk from "chalk";

const program = new Command()
  .requiredOption("--map <json>", "path_alias_map.json")
  .option("--apply", "write changes", false)
  .option("--dry-run", "show changes without applying", false)
  .option("--max-changes <n>", "maximum changes per run", "8")
  .parse();

const { map: mapPath, apply, dryRun, maxChanges } = program.opts();

async function main() {
  console.log(chalk.cyan("🔧 ΞNuSyQ Edge Import Rewriter - Safe Path Updates"));
  
  if (!fs.existsSync(mapPath)) {
    console.log(chalk.red(`❌ Path alias map not found: ${mapPath}`));
    process.exit(1);
  }
  
  const aliasMap = JSON.parse(fs.readFileSync(mapPath, "utf8"));
  console.log(chalk.yellow(`📋 Loaded ${Object.keys(aliasMap).length} path aliases`));
  
  // Load overlay roster if available, otherwise scan ours.* files
  let targetFiles: string[] = [];
  const overlayRoster = "SystemDev/.edge/overlay/roster.json";
  
  if (fs.existsSync(overlayRoster)) {
    const roster = JSON.parse(fs.readFileSync(overlayRoster, "utf8"));
    targetFiles = roster.files
      .filter((f: any) => f.path.match(/\.(ts|tsx|js|jsx)$/))
      .map((f: any) => f.path);
    console.log(chalk.blue(`📁 Using overlay roster: ${targetFiles.length} TypeScript/JavaScript files`));
  } else {
    console.log(chalk.yellow("⚠️  No overlay roster found, scanning for TypeScript files..."));
    // Fallback to basic scan
    process.exit(1);
  }

  const project = new Project({ 
    skipAddingFilesFromTsConfig: true,
    useInMemoryFileSystem: !apply // Use in-memory for dry runs
  });
  
  // Add source files to project
  targetFiles.forEach(filePath => {
    if (fs.existsSync(filePath)) {
      project.addSourceFileAtPath(filePath);
    }
  });

  console.log(chalk.gray(`📝 Analyzing ${project.getSourceFiles().length} source files`));
  
  let changes = 0;
  const changeDetails: Array<{ file: string; from: string; to: string }> = [];
  const maxChange = parseInt(maxChanges, 10);

  for (const sf of project.getSourceFiles()) {
    if (changes >= maxChange) break;
    
    const filePath = sf.getFilePath();
    
    // Find import/export declarations and string literals
    sf.getDescendantsOfKind(SyntaxKind.StringLiteral).forEach(lit => {
      if (changes >= maxChange) return;
      
      const text = lit.getLiteralText();
      
      // Only process relative imports and explicit paths
      if (text.startsWith(".") || text.startsWith("/")) {
        for (const [from, to] of Object.entries(aliasMap as Record<string, string>)) {
          if (text.startsWith(from)) {
            const newText = text.replace(from, to as string);
            
            if (dryRun || !apply) {
              console.log(chalk.cyan(`   ${path.basename(filePath)}: "${text}" → "${newText}"`));
            } else {
              lit.replaceWithText(`"${newText}"`);
            }
            
            changeDetails.push({
              file: filePath,
              from: text,
              to: newText
            });
            
            changes++;
            break;
          }
        }
      }
    });
  }

  // Save changes if applying
  if (apply && !dryRun && changes > 0) {
    console.log(chalk.yellow(`💾 Saving ${changes} changes...`));
    project.saveSync();
  }

  const receipt = {
    breath: "ΞΘΛΔ_imports",
    timestamp: new Date().toISOString(),
    changes,
    applied: apply && !dryRun,
    dry_run: dryRun,
    max_changes: maxChange,
    files_analyzed: project.getSourceFiles().length,
    change_details: changeDetails
  };

  const receiptPath = `SystemDev/receipts/edge_imports_${Date.now()}.json`;
  fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));

  console.log(chalk.green("✅ Import rewrite analysis complete!"));
  console.log(chalk.blue(`🔧 Changes identified: ${changes}`));
  console.log(chalk.yellow(`📝 Applied: ${apply && !dryRun ? 'YES' : 'NO'}`));
  console.log(chalk.magenta(`📄 Receipt: ${receiptPath}`));

  if (changes > 0) {
    console.log(chalk.cyan("\n📋 Change summary:"));
    changeDetails.slice(0, 8).forEach((change, i) => {
      console.log(chalk.gray(`   ${i + 1}. ${path.basename(change.file)}`));
      console.log(chalk.gray(`      "${change.from}" → "${change.to}"`));
    });
    
    if (changeDetails.length > 8) {
      console.log(chalk.gray(`   ... and ${changeDetails.length - 8} more (see receipt)`));
    }
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}