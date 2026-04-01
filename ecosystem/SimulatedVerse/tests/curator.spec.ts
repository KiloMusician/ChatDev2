import { describe, it, expect } from "vitest";
import { planCurator } from "../server/services/curator.js";

describe("curator planner", () => {
  it("dedupes by SHA and prefers src/ over docs/", () => {
    const files = [
      { path:"src/a.txt", size:3, mtime:1, sha256:"x", ext:"txt", type:"text" as const },
      { path:"docs/a.txt", size:3, mtime:1, sha256:"x", ext:"txt", type:"text" as const },
    ];
    const refs = new Set<string>(["src/a.txt"]);
    const policy = {
      max_file_mb:25, 
      large_text_mb:5, 
      logs_glob:["**/*.log"], 
      compress_after_days:3,
      duplicate_preference:[/^src\//, /^client\/src\//, /^docs\//], 
      quarantine:"_quarantine"
    };
    const plan = planCurator(files, refs, policy);
    expect(plan.find(p => p.kind === "dedupe" && (p as any).duplicate === "docs/a.txt")).toBeTruthy();
  });

  it("quarantines large unreferenced files", () => {
    const files = [
      { path:"src/huge.bin", size:30*1024*1024, mtime:1, sha256:"y", ext:"bin", type:"binary" as const },
    ];
    const refs = new Set<string>(); // no references
    const policy = {
      max_file_mb:25, 
      large_text_mb:5, 
      logs_glob:["**/*.log"], 
      compress_after_days:3,
      duplicate_preference:[/^src\//], 
      quarantine:"_quarantine"
    };
    const plan = planCurator(files, refs, policy);
    expect(plan.find(p => p.kind === "quarantine" && p.path === "src/huge.bin")).toBeTruthy();
  });

  it("compresses old log files", () => {
    const oldTime = Date.now() - (5 * 24 * 60 * 60 * 1000); // 5 days ago
    const files = [
      { path:"logs/app.log", size:1024, mtime:oldTime, sha256:"z", ext:"log", type:"text" as const },
    ];
    const refs = new Set<string>();
    const policy = {
      max_file_mb:25, 
      large_text_mb:5, 
      logs_glob:["**/*.log"], 
      compress_after_days:3,
      duplicate_preference:[/^src\//], 
      quarantine:"_quarantine"
    };
    const plan = planCurator(files, refs, policy);
    expect(plan.find(p => p.kind === "compress" && p.path === "logs/app.log")).toBeTruthy();
  });

  it("preserves referenced files", () => {
    const files = [
      { path:"src/important.js", size:10*1024*1024, mtime:1, sha256:"ref", ext:"js", type:"text" as const },
    ];
    const refs = new Set<string>(["src/important.js"]);
    const policy = {
      max_file_mb:25, 
      large_text_mb:5, 
      logs_glob:["**/*.log"], 
      compress_after_days:3,
      duplicate_preference:[/^src\//], 
      quarantine:"_quarantine"
    };
    const plan = planCurator(files, refs, policy);
    expect(plan.find(p => (p.kind === "quarantine" && p.path === "src/important.js"))).toBeFalsy();
  });
});