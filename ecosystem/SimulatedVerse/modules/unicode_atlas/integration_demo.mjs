#!/usr/bin/env node
// Demo: Unicode integration with ASCII and Culture-Ship systems
// Shows how to use Unicode styling in practical scenarios

import { zalgoSafe, stripCombining } from "./lib/zalgo.mjs";
import { readFileSync } from "node:fs";

console.log("🌟 UNICODE INTELLIGENCE INTEGRATION DEMO");
console.log("========================================\n");

// Load our generated assets
const atlas = JSON.parse(readFileSync("assets/unicode/atlas.json", "utf8"));
const variants = JSON.parse(readFileSync("assets/unicode/variants.json", "utf8"));

console.log("📊 System Status:");
console.log(`   Unicode Atlas: ${atlas.count.toLocaleString()} codepoints loaded`);
console.log(`   Style Variants: ${Object.keys(variants).length - 1} systems available`);
console.log(`   Safe Zalgo: 4 profiles (readable → artful)`);

console.log("\n🎨 Style Demonstrations:");

// Math Bold Demo
const originalText = "ΞNuSyQ CoreLink Foundation";
console.log(`\nOriginal: ${originalText}`);

if (variants.math_bold) {
  const mathBoldText = originalText.split('').map(char => 
    variants.math_bold[char] || char
  ).join('');
  console.log(`Math Bold: ${mathBoldText}`);
}

// Superscript Demo
const versionText = "v2.1.0";
if (variants.superscript) {
  const superText = versionText.split('').map(char => 
    variants.superscript[char] || char
  ).join('');
  console.log(`Superscript: CoreLink${superText}`);
}

// Safe Zalgo Demo
console.log("\n🔮 Safe Zalgo Demonstrations:");
const sampleTexts = ["Culture-Ship", "OmniTag", "Temple"];

sampleTexts.forEach(text => {
  console.log(`\n-- ${text} --`);
  ["readable", "subtle", "vivid"].forEach(profile => {
    const styled = zalgoSafe(text, profile);
    const plain = stripCombining(styled);
    console.log(`${profile.padEnd(8)}: ${styled} (strips to: ${plain})`);
  });
});

console.log("\n🏷️ Semantic Tagging Examples:");
console.log("Harmony Ξ̍ → ethic, preserve_life, council");
console.log("Ascent Ω̍ → progression, unlock, temple");
console.log("ΞNuSyQ̍͋̕ → system, consciousness, core");

console.log("\n📱 Mobile/Desktop Responsiveness:");
console.log("Desktop: Full expressivity (up to 'artful' profile)");
console.log("Mobile: Capped at 'subtle' profile for readability");

console.log("\n♿ Accessibility Features:");
console.log("✅ Plain-text mirrors via stripCombining()");
console.log("✅ ARIA labels for screen readers");
console.log("✅ Tooltips showing unstyled versions");
console.log("✅ Font fallback detection");

console.log("\n🎯 Integration Points:");
console.log("• ASCII HUD: Dynamic styling based on game state");
console.log("• Culture-Ship: Semantic tagging for autonomous operations");
console.log("• Conlang System: Expressivity weights for procedural generation");
console.log("• UI Mood: Temple (readable) → Combat (vivid) → Transcendent (artful)");

console.log("\n✨ UNICODE INTELLIGENCE SYSTEM READY FOR CULTURE-SHIP INTEGRATION!");