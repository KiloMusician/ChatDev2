/**
 * 🔧 RENAME & REWIRE SURGEON - Culture-Ship Surgical Component
 * Zero-token file operations with dry-run safety
 */

interface RewireOperation {
  type: "rename" | "move" | "merge" | "delete";
  source: string;
  target?: string;
  reason: string;
  impact_score: number;
}

interface RewireResult {
  success: boolean;
  operations: RewireOperation[];
  dryRun: boolean;
  errors: string[];
  changedFiles: string[];
}

export async function renameAndRewire(payload: any): Promise<RewireResult> {
  console.log("🔧 Culture-Ship Surgeon: Preparing rename & rewire operations...");
  
  const operations: RewireOperation[] = [];
  const errors: string[] = [];
  const changedFiles: string[] = [];
  
  try {
    // Extract operations from payload
    if (payload.duplicates) {
      for (const duplicate of payload.duplicates) {
        if (duplicate.files.length > 1) {
          // Keep highest priority file, suggest others for deletion
          const [keep, ...remove] = duplicate.files;
          
          for (const file of remove) {
            operations.push({
              type: "delete",
              source: file.path,
              reason: `Duplicate of ${keep.path}`,
              impact_score: 2
            });
          }
        }
      }
    }
    
    if (payload.issues) {
      for (const issue of payload.issues) {
        if (issue.suggestion && issue.issue === "broken") {
          operations.push({
            type: "rename",
            source: issue.file,
            target: issue.suggestion,
            reason: `Fix broken import: ${issue.importPath}`,
            impact_score: 3
          });
        }
      }
    }
    
    // Dry run first
    console.log(`🧪 Performing dry run of ${operations.length} operations...`);
    const dryRunResult = await executeDryRun(operations);
    
    if (dryRunResult.success) {
      console.log("✅ Dry run successful, operations appear safe");
      // In real implementation, would ask for confirmation before applying
      console.log("🔄 Surgical operations staged for manual review");
      return {
        success: true,
        operations,
        dryRun: true,
        errors: [],
        changedFiles: operations.map(op => op.source)
      };
    } else {
      console.log("❌ Dry run failed, operations unsafe");
      return {
        success: false,
        operations,
        dryRun: true,
        errors: dryRunResult.errors,
        changedFiles: []
      };
    }
    
  } catch (error) {
    console.error("❌ Rename & rewire failed:", error);
    return {
      success: false,
      operations,
      dryRun: true,
      errors: [String(error)],
      changedFiles: []
    };
  }
}

async function executeDryRun(operations: RewireOperation[]): Promise<{ success: boolean; errors: string[] }> {
  const errors: string[] = [];
  
  // Validate each operation
  for (const op of operations) {
    try {
      const fs = await import("node:fs");
      
      // Check source exists
      if (!fs.existsSync(op.source)) {
        errors.push(`Source does not exist: ${op.source}`);
        continue;
      }
      
      // Check target constraints
      if (op.target) {
        const targetDir = require("node:path").dirname(op.target);
        if (!fs.existsSync(targetDir)) {
          errors.push(`Target directory does not exist: ${targetDir}`);
        }
        
        if (fs.existsSync(op.target)) {
          errors.push(`Target already exists: ${op.target}`);
        }
      }
      
      // Check for impact on other files
      if (op.impact_score > 5) {
        console.log(`⚠️ High impact operation: ${op.type} ${op.source} (score: ${op.impact_score})`);
      }
      
    } catch (error) {
      errors.push(`Validation failed for ${op.source}: ${error}`);
    }
  }
  
  return {
    success: errors.length === 0,
    errors
  };
}

export async function generateRewireDiff(operations: RewireOperation[]): Promise<string> {
  let diff = "# 🔧 Culture-Ship Rewire Operations Diff\n\n";
  
  diff += `**Summary:** ${operations.length} surgical operations planned\n\n`;
  
  for (const op of operations) {
    const icon = op.type === "delete" ? "🗑️" : 
                 op.type === "rename" ? "📝" : 
                 op.type === "move" ? "📁" : "🔀";
    
    diff += `${icon} **${op.type.toUpperCase()}**\n`;
    diff += `- Source: \`${op.source}\`\n`;
    if (op.target) {
      diff += `- Target: \`${op.target}\`\n`;
    }
    diff += `- Reason: ${op.reason}\n`;
    diff += `- Impact: ${op.impact_score}/10\n\n`;
  }
  
  return diff;
}