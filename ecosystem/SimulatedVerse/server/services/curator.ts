import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

type FMeta = {
  path: string; size: number; mtime: number; sha256: string;
  ext: string; type: "text"|"binary"; referenced?: boolean;
};

type PlanAction =
  | { kind:"compress"; path:string; dest:string }
  | { kind:"quarantine"; path:string; dest:string; reason:string }
  | { kind:"dedupe"; duplicate:string; canonical:string }
  | { kind:"rename"; from:string; to:string; reason:string };

const ROOT = path.resolve(process.cwd());

function sha256File(fp: string): string {
  try {
    if (!fs.existsSync(fp)) return "";
    const content = fs.readFileSync(fp);
    return crypto.createHash("sha256").update(content).digest("hex");
  } catch {
    return "";
  }
}

function listFiles(dir: string, out: string[], ignore: RegExp[]): void {
  try {
    for (const e of fs.readdirSync(dir, {withFileTypes:true})) {
      const p = path.join(dir, e.name);
      const rel = path.relative(ROOT, p).replace(/\\/g,"/");
      if (ignore.some(r=>r.test(rel))) continue;
      if (e.isDirectory()) listFiles(p, out, ignore);
      else out.push(rel);
    }
  } catch {
    // Skip inaccessible directories
  }
}

function isTextExt(ext: string) {
  return /^(md|mdx|txt|json|yaml|yml|ts|tsx|js|jsx|css|scss|html|svg|log|ndjson)$/i.test(ext);
}

function extOf(p: string){ return (p.split(".").pop()||"").toLowerCase(); }

export function scanRepo(ignore: string[]): FMeta[] {
  const ignoreRe = ignore.map(s => new RegExp(s));
  const files: string[] = [];
  listFiles(ROOT, files, ignoreRe);

  const metas: FMeta[] = [];
  for (const rel of files) {
    try {
      const fp = path.join(ROOT, rel);
      const st = fs.statSync(fp);
      const ext = extOf(rel);
      const type = isTextExt(ext) ? "text" : "binary";
      const sha = st.size <= 64*1024*1024 ? sha256File(fp) : ""; // skip hashing >64MB
      metas.push({ path: rel, size: st.size, mtime: st.mtimeMs, sha256: sha, ext, type });
    } catch {
      // Skip files that can't be accessed
    }
  }
  return metas;
}

export function buildRefGraph(files: FMeta[]): Set<string> {
  // Light ref crawl: TS/JS import/require, JSON $ref, MD links, basic HTML src=, href=
  const refs = new Set<string>();
  for (const f of files) {
    if (f.type !== "text" || f.size > 2_000_000) continue;
    try {
      const content = fs.readFileSync(path.join(ROOT, f.path), "utf8");
      const patts = [
        /from\s+["']([^"']+)["']/g, /require\(["']([^"']+)["']\)/g,
        /\$ref["']?\s*:\s*["']([^"']+)["']/g, /\]\(([^)]+)\)/g,
        /src=["']([^"']+)["']/g, /href=["']([^"']+)["']/g,
      ];
      for (const re of patts) {
        let m; 
        while ((m = re.exec(content))) {
          let target = m[1];
          if (!target) continue;
          if (target.startsWith("http")) continue;
          // normalize relative paths
          if (target.startsWith("./") || target.startsWith("../")) {
            const base = path.posix.dirname(f.path);
            const norm = path.posix.normalize(path.posix.join(base, target));
            refs.add(norm);
            // also consider extensionless TS/JS
            for (const ex of ["",".ts",".tsx",".js",".jsx",".json",".md",".css",".svg"]) {
              refs.add(norm + ex);
            }
          } else {
            // asset in project by bare path
            refs.add(target);
          }
        }
      }
    } catch {
      // Skip files that can't be read
    }
  }
  return refs;
}

export function planCurator(
  files: FMeta[],
  refs: Set<string>,
  policy: {
    max_file_mb: number; large_text_mb: number;
    logs_glob: string[]; compress_after_days: number;
    duplicate_preference: RegExp[]; quarantine: string;
  }
): PlanAction[] {
  const now = Date.now();
  const MB = 1024*1024;
  const actions: PlanAction[] = [];

  // mark referenced
  for (const f of files) f.referenced = refs.has(f.path);

  // duplicates by hash (text+binary)
  const byHash = new Map<string, FMeta[]>();
  for (const f of files) {
    if (!f.sha256) continue;
    const arr = byHash.get(f.sha256) || [];
    arr.push(f);
    byHash.set(f.sha256, arr);
  }
  
  for (const [sha, arr] of byHash) {
    if (arr.length < 2) continue;
    // pick canonical by preference > shortest path
    const canon = arr.sort((a,b) => {
      const prefA = policy.duplicate_preference.findIndex(re => re.test(a.path));
      const prefB = policy.duplicate_preference.findIndex(re => re.test(b.path));
      const pa = prefA === -1 ? 999 : prefA;
      const pb = prefB === -1 ? 999 : prefB;
      if (pa !== pb) return pa - pb;
      return a.path.length - b.path.length;
    })[0];
    if (!canon) continue;
    
    for (const d of arr) {
      if (d.path === canon.path) continue;
      actions.push({ kind:"dedupe", duplicate:d.path, canonical: canon.path });
    }
  }

  // big binaries / big text → quarantine (if unreferenced) or compress logs older than N days
  for (const f of files) {
    const ageDays = (now - f.mtime) / (1000*60*60*24);
    if (f.type === "text" && f.size > policy.large_text_mb*MB) {
      if (!f.referenced) actions.push({
        kind:"quarantine", path:f.path,
        dest: `${policy.quarantine}/${f.path}`, reason:`large-text>${policy.large_text_mb}MB`
      });
    }
    if (f.type === "binary" && f.size > policy.max_file_mb*MB) {
      if (!f.referenced) actions.push({
        kind:"quarantine", path:f.path,
        dest: `${policy.quarantine}/${f.path}`, reason:`large-binary>${policy.max_file_mb}MB`
      });
    }
    if (/\.(log|ndjson|trace|profile)$/i.test(f.path) && ageDays >= policy.compress_after_days) {
      actions.push({
        kind:"compress", path:f.path, dest: f.path + ".gz"
      });
    }
  }

  // unreferenced source assets (not docs) → quarantine
  for (const f of files) {
    if (!f.referenced && /^src|^client\/src|^public\//.test(f.path)) {
      actions.push({
        kind:"quarantine", path:f.path,
        dest: `${policy.quarantine}/${f.path}`, reason:"orphan-source-asset"
      });
    }
  }

  return actions;
}
