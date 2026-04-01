import {globSync} from "glob";
import {readFileSync, writeFileSync, mkdirSync} from "node:fs";

const files = globSync('**/*.{ts,tsx,js,jsx,mjs,cjs}', {
  ignore: ['**/node_modules/**','**/dist/**','**/.next/**','**/.git/**']
});

const issues = [];
for(const f of files){
  try {
    const src = readFileSync(f,'utf8');
    const importRegex = /\bimport\s+[\s\S]*?from\s+['"][^'"]+['"];?/g;
    const requireRegex = /require\(['"][^'"]+['"]\)/g;
    
    const matches = [...src.matchAll(importRegex), ...src.matchAll(requireRegex)];
    for(const match of matches){
      const statement = match[0];
      const quoteMatch = statement.match(/['"][^'"]+['"]/);
      if(!quoteMatch) continue;
      
      const importPath = quoteMatch[0].slice(1,-1);
      if(importPath.startsWith('.') && !importPath.endsWith('.js') && !importPath.endsWith('.ts') && !importPath.includes('?')){
        issues.push({file: f, import: importPath});
      }
    }
  } catch(e) {
    // Skip files that can't be read
    continue;
  }
}

mkdirSync("reports",{recursive:true});
writeFileSync("reports/scan_imports.json", JSON.stringify(issues, null, 2));
console.log(`✅ Import scan complete. Candidates: ${issues.length}`);