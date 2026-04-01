#!/usr/bin/env tsx
import fs from "node:fs";
import path from "node:path";
import yaml from "yaml";
import { globby } from "globby";

const cfg = yaml.parse(fs.readFileSync("ops/repo-targets.yaml","utf8"));
const roots: string[] = cfg.roots ?? ["."];
const include: string[] = cfg.include ?? ["**/*"];
const exclude: string[] = [...(cfg.exclude ?? []), ...(cfg.optional ?? [])];

(async () => {
  const cwd = process.cwd();
  const patterns = roots.flatMap((r:string)=> include.map((g:string)=> path.posix.join(r, g)));
  const files = await globby(patterns, { gitignore: true, ignore: exclude, expandDirectories: false, cwd });
  for (const f of files) console.log(f);
})();