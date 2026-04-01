// Quick test for Culture Ship agent - writes result to file for inspection
import { CultureShipAgent } from "./agents/culture-ship/index.js";

const testInput = {
  content: "Review NuSyQ-Hub theater score: 0.082 (15962 hits in 194655 lines)",
  metadata: {
    project: "NuSyQ-Hub",
    score: 0.082,
    hits: 15962,
    lines: 194655,
    patterns: {
      console_spam: 93,
      fake_progress: 219,
      todo_comments: 1847
    }
  },
  // Culture Ship expects these fields:
  t: Date.now(),
  utc: Date.now(),
  entropy: 0.082,
  budget: 0.95
};

console.log("Testing Culture Ship agent...");
console.log("Input:", JSON.stringify(testInput, null, 2));

try {
  const result = await CultureShipAgent.run(testInput as any);
  console.log("\n✅ SUCCESS!");
  console.log("Result:", JSON.stringify(result, null, 2));
  
  if (result.effects?.artifactPath) {
    console.log(`\n📄 Artifact created: ${result.effects.artifactPath}`);
  }
} catch (error) {
  console.error("\n❌ ERROR:");
  console.error(error);
  process.exit(1);
}
