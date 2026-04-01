
import { existsSync, readFileSync } from "node:fs";
import { Council } from "../modules/culture_ship/agents/council.ts";

// Mock context for initial test
const mockContext = {
  readJSON: (path: string) => {
    try {
      return existsSync(path) ? JSON.parse(readFileSync(path, 'utf-8')) : null;
    } catch { return null; }
  },
  insights: {
    brokenImports: 10,
    dupes: 3, 
    todos: 100,
    smokeOk: true
  },
  appendJournal: (agent: string, message: string) => {
    console.log(`[journal] ${agent}: ${message}`);
  },
  queue: (task: any) => {
    console.log(`[queue] ${task.id}: ${task.title}`);
  }
};

async function testCouncil() {
  console.log("[council] 🏛️ Running Council scan...");
  const scanResult = Council.scan(mockContext);
  console.log("[council] 📊 Scan result:", JSON.stringify(scanResult, null, 2));
  
  console.log("[council] 📋 Running Council plan...");
  const planResult = Council.plan(mockContext);
  console.log("[council] 📋 Plan result:", JSON.stringify(planResult, null, 2));
  
  return { scanResult, planResult };
}

testCouncil().catch(console.error);
