import { spawn } from "node:child_process";

export async function analyze() {
  try {
    const child = spawn("npx", ["eslint", ".", "--ext", ".ts,.tsx,.js"], { stdio: ["pipe", "pipe", "pipe"] });
    
    let stdout = "";
    let stderr = "";
    
    child.stdout.on("data", (data) => { stdout += data.toString(); });
    child.stderr.on("data", (data) => { stderr += data.toString(); });
    
    const exitCode = await new Promise((resolve) => {
      child.on("close", (code) => resolve(code));
    });
    
    const out = stdout || stderr;
    const findings = out.split("\n").filter(l=>/error|warning/.test(l)).slice(0,500)
      .map(l=>({kind:l.includes("error")?"lint_error":"lint_warn", detail:l, severity:l.includes("error")?"error":"warn" as const}));
    return findings;
  } catch (e:any) {
    return [{kind:"lint_failure", severity:"error" as const, detail:String(e)}];
  }
}
export default { analyze };