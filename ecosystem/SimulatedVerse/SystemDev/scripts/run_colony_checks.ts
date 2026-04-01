import { writeJSON } from "../src/rosetta/io";
import * as fs from "fs";

function exists(p:string){ try{ return fs.statSync(p).isFile(); }catch{ return false; } }

const checks = [
  { name:"Receipts Discipline", passed: fs.existsSync("reports"), details:"reports/* present" },
  { name:"Backlog Next-Up", passed: fs.existsSync("backlog/next_up"), details:"backlog/next_up present" },
  { name:"Agents Receipt Flow", passed: !!glob(["reports/replit_pass_*.json","reports/*git*.json"]).length, details:"agent receipts exist" },
  { name:"Temple Alignment", passed: fs.existsSync("reports/temple_alignment.json"), details:"temple_alignment receipt exists" }
];

function glob(patterns:string[]):string[]{
  // super-light: list files in reports/ and match includes
  try {
    const all = fs.readdirSync("reports").map(f=>"reports/"+f);
    return all.filter(f => patterns.some(p => {
      const core = p.replace("*","");
      return f.includes(core);
    }));
  } catch { return []; }
}

const ts = new Date().toISOString().replace(/[:.]/g,"");
writeJSON(`reports/colony/checks_${ts}.json`, { checks, ok: checks.every(c=>c.passed) });
console.log("Colony checks written.");