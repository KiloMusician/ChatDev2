import { spawn } from "node:child_process";

export async function analyze(){
  try {
    const child = spawn("npx", ["tsc", "-p", "tsconfig.json", "--noEmit"], { stdio: ["pipe", "pipe", "pipe"] });
    
    let stdout = "";
    let stderr = "";
    
    child.stdout.on("data", (data) => { stdout += data.toString(); });
    child.stderr.on("data", (data) => { stderr += data.toString(); });
    
    const exitCode = await new Promise((resolve) => {
      child.on("close", (code) => resolve(code));
    });
    
    if (exitCode === 0) return [];
    const lines = (stdout+stderr).split("\n").slice(0,300);
    return lines.map(l=>({kind:"type_error", severity:"error" as const, detail:l}));
  } catch (e: any) {
    return [{kind:"type_check_failure", severity:"error" as const, detail:String(e)}];
  }
}
export default { analyze };