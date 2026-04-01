#!/usr/bin/env python3
"""
ΞNuSyQ Duplicate & Naming Consolidation - Detection Engine
Intelligently detects duplicates, near-duplicates, vague names, and broken imports
"""
import os
import json
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from dataclasses import dataclass, asdict

# Vague name patterns to flag
VAGUE_NAMES = {
    "util", "utils", "helper", "helpers", "common", "misc", "tmp", "new", 
    "final", "copy", "old", "backup", "test2", "foo", "bar", "placeholder",
    "index", "main", "app"
}

@dataclass
class FileCandidate:
    path: str
    hash: str
    exports: List[str]
    imports: List[str]
    usage_count: int = 0
    size: int = 0
    is_empty: bool = False
    is_placeholder: bool = False
    vague_score: float = 0.0

@dataclass
class SimilarityScore:
    content: float
    api: float
    name: float
    overall: float

@dataclass
class DuplicateGroup:
    id: str
    theme: str
    members: List[FileCandidate]
    similarity: SimilarityScore
    proposed_primary: str
    proposed_actions: List[str]
    confidence: float
    notes: str

class DuplicateDetector:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path)
        self.candidates = {}
        self.groups = []
        
    def scan_repository(self) -> Dict:
        """Main entry point - scan repo and build detection plan"""
        print("🔍 Scanning repository for duplicates and naming issues...")
        
        # Create .ops directory
        os.makedirs(".ops", exist_ok=True)
        
        # Step 1: Collect all files
        files = self._collect_files()
        print(f"📁 Found {len(files)} files to analyze")
        
        # Step 2: Analyze each file (with progress)
        for i, file_path in enumerate(files):
            if i % 50 == 0:
                print(f"   📊 Analyzing file {i+1}/{len(files)}...")
            candidate = self._analyze_file(file_path)
            if candidate:
                self.candidates[file_path] = candidate
        
        # Step 3: Detect duplicate groups
        self._detect_duplicate_groups()
        
        # Step 4: Detect vague names
        empties, placeholders, vague_files = self._detect_naming_issues()
        
        # Step 5: Build plan
        plan = {
            "groups": [asdict(g) for g in self.groups],
            "empties": empties,
            "placeholders": placeholders, 
            "vague_files": vague_files,
            "stats": {
                "total_files": len(files),
                "analyzed": len(self.candidates),
                "duplicate_groups": len(self.groups),
                "empty_files": len(empties),
                "placeholder_files": len(placeholders),
                "vague_named": len(vague_files)
            }
        }
        
        return plan
    
    def _collect_files(self) -> List[str]:
        """Collect all relevant source files"""
        extensions = {
            ".ts", ".tsx", ".js", ".jsx", ".mjs",
            ".py", ".gd", ".cs", ".go", ".rs",
            ".md", ".json", ".yml", ".yaml"
        }
        
        files = []
        for ext in extensions:
            try:
                # Use fd if available with exclusions
                result = subprocess.run([
                    "fd", "-e", ext.lstrip("."), "-t", "f",
                    "--exclude", "node_modules",
                    "--exclude", ".git", 
                    "--exclude", "dist",
                    "--exclude", "build",
                    "--exclude", ".cache",
                    "--exclude", "__pycache__",
                    "--exclude", ".ops"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    files.extend([f for f in result.stdout.strip().split("\n") if f])
                    continue
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to Python glob with filtering
            for p in self.root.rglob(f"*{ext}"):
                path_str = str(p)
                if not any(ex in path_str for ex in ["node_modules", ".git", "dist", "build", ".cache", "__pycache__", ".ops"]):
                    files.append(path_str)
        
        # Remove duplicates and empty strings
        files = list(set(f for f in files if f and os.path.exists(f)))
        
        # Limit to prevent timeout (analyze most relevant files first)
        if len(files) > 500:
            # Prioritize source files over config/docs
            source_files = [f for f in files if any(f.endswith(ext) for ext in [".ts", ".tsx", ".js", ".jsx", ".py", ".mjs"])]
            other_files = [f for f in files if f not in source_files]
            files = source_files[:400] + other_files[:100]
        
        return files
    
    def _analyze_file(self, file_path: str) -> Optional[FileCandidate]:
        """Analyze individual file for metadata"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Basic metrics
            file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            size = len(content)
            is_empty = size < 10 or content.strip() == ""
            is_placeholder = bool(re.search(r"\b(TODO|FIXME|placeholder|coming soon)\b", content, re.I))
            
            # Extract exports/imports based on file type
            exports, imports = self._extract_api_surface(file_path, content)
            
            # Vague name scoring
            vague_score = self._calculate_vague_score(file_path)
            
            return FileCandidate(
                path=file_path,
                hash=file_hash,
                exports=exports,
                imports=imports,
                size=size,
                is_empty=is_empty,
                is_placeholder=is_placeholder,
                vague_score=vague_score
            )
            
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
            return None
    
    def _extract_api_surface(self, file_path: str, content: str) -> Tuple[List[str], List[str]]:
        """Extract exports and imports from file content"""
        exports, imports = [], []
        
        if file_path.endswith(('.ts', '.tsx', '.js', '.jsx', '.mjs')):
            # TypeScript/JavaScript
            export_matches = re.findall(r"export\s+(?:const|function|class|interface|type)\s+(\w+)", content)
            export_default = re.findall(r"export\s+default\s+(\w+)", content)
            exports.extend(export_matches + export_default)
            
            import_matches = re.findall(r"import.*from\s+['\"]([^'\"]+)['\"]", content)
            imports.extend(import_matches)
            
        elif file_path.endswith('.py'):
            # Python
            export_matches = re.findall(r"^(?:def|class)\s+(\w+)", content, re.M)
            exports.extend(export_matches)
            
            import_matches = re.findall(r"^(?:from\s+[\w.]+\s+)?import\s+([\w.]+)", content, re.M)
            imports.extend(import_matches)
            
        elif file_path.endswith('.gd'):
            # GDScript
            export_matches = re.findall(r"^func\s+(\w+)", content, re.M)
            exports.extend(export_matches)
            
            import_matches = re.findall(r"load\(['\"]([^'\"]+)['\"]\)", content)
            imports.extend(import_matches)
        
        return list(set(exports)), list(set(imports))
    
    def _calculate_vague_score(self, file_path: str) -> float:
        """Calculate how vague a filename is (0=specific, 1=very vague)"""
        parts = file_path.replace(".", "/").split("/")
        base = parts[-1].lower()
        tokens = set(re.split(r"[-_.]", base)) - {""}
        
        if not tokens:
            return 1.0
            
        vague_tokens = tokens & VAGUE_NAMES
        return len(vague_tokens) / len(tokens)
    
    def _detect_duplicate_groups(self):
        """Detect groups of similar/duplicate files"""
        files = list(self.candidates.values())
        processed = set()
        group_id = 1
        
        for i, file1 in enumerate(files):
            if file1.path in processed:
                continue
                
            group_members = [file1]
            
            for j, file2 in enumerate(files[i+1:], i+1):
                if file2.path in processed:
                    continue
                    
                similarity = self._calculate_similarity(file1, file2)
                
                # Group if overall similarity > 0.7
                if similarity.overall > 0.7:
                    group_members.append(file2)
                    processed.add(file2.path)
            
            if len(group_members) > 1:
                processed.add(file1.path)
                
                # Determine primary (most used, largest, best name)
                primary = max(group_members, key=lambda f: (
                    f.usage_count,
                    f.size,
                    -f.vague_score
                ))
                
                # Calculate group similarity
                group_sim = self._calculate_group_similarity(group_members)
                
                group = DuplicateGroup(
                    id=f"G{group_id:03d}",
                    theme=self._infer_theme(group_members),
                    members=group_members,
                    similarity=group_sim,
                    proposed_primary=primary.path,
                    proposed_actions=self._suggest_actions(group_members, primary),
                    confidence=min(0.95, group_sim.overall),
                    notes=f"Found {len(group_members)} similar files"
                )
                
                self.groups.append(group)
                group_id += 1
    
    def _calculate_similarity(self, file1: FileCandidate, file2: FileCandidate) -> SimilarityScore:
        """Calculate similarity between two files"""
        # Content similarity (hash)
        content_sim = 1.0 if file1.hash == file2.hash else 0.0
        
        # API similarity (exports overlap)
        if file1.exports and file2.exports:
            common_exports = set(file1.exports) & set(file2.exports)
            total_exports = set(file1.exports) | set(file2.exports)
            api_sim = len(common_exports) / len(total_exports) if total_exports else 0.0
        else:
            api_sim = 0.0
        
        # Name similarity (filename)
        name1 = os.path.basename(file1.path)
        name2 = os.path.basename(file2.path)
        name_sim = SequenceMatcher(None, name1, name2).ratio()
        
        # Overall weighted score
        overall = (content_sim * 0.4 + api_sim * 0.4 + name_sim * 0.2)
        
        return SimilarityScore(
            content=content_sim,
            api=api_sim, 
            name=name_sim,
            overall=overall
        )
    
    def _calculate_group_similarity(self, members: List[FileCandidate]) -> SimilarityScore:
        """Calculate average similarity within a group"""
        if len(members) < 2:
            return SimilarityScore(1.0, 1.0, 1.0, 1.0)
        
        sims = []
        for i in range(len(members)):
            for j in range(i+1, len(members)):
                sims.append(self._calculate_similarity(members[i], members[j]))
        
        if not sims:
            return SimilarityScore(0.0, 0.0, 0.0, 0.0)
        
        avg_content = sum(s.content for s in sims) / len(sims)
        avg_api = sum(s.api for s in sims) / len(sims)
        avg_name = sum(s.name for s in sims) / len(sims)
        avg_overall = sum(s.overall for s in sims) / len(sims)
        
        return SimilarityScore(avg_content, avg_api, avg_name, avg_overall)
    
    def _infer_theme(self, members: List[FileCandidate]) -> str:
        """Infer the common theme/purpose of grouped files"""
        all_exports = []
        for member in members:
            all_exports.extend(member.exports)
        
        # Simple keyword extraction
        if any("string" in e.lower() for e in all_exports):
            return "string-utils"
        elif any("array" in e.lower() for e in all_exports):
            return "array-utils"
        elif any("http" in e.lower() or "api" in e.lower() for e in all_exports):
            return "api-utils"
        else:
            # Use common path prefix
            paths = [m.path for m in members]
            common_prefix = os.path.commonpath(paths) if len(paths) > 1 else paths[0]
            return os.path.basename(common_prefix) or "utilities"
    
    def _suggest_actions(self, members: List[FileCandidate], primary: FileCandidate) -> List[str]:
        """Suggest consolidation actions for a group"""
        actions = ["merge_exports"]
        
        if len(members) > 2:
            actions.append("redirect_imports")
        
        if any(m.path != primary.path for m in members):
            actions.append("deprecate_secondary")
        
        return actions
    
    def _detect_naming_issues(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Detect empty, placeholder, and vague-named files"""
        empties = []
        placeholders = []
        vague_files = []
        
        for candidate in self.candidates.values():
            if candidate.is_empty:
                empties.append({
                    "path": candidate.path,
                    "reason": "empty",
                    "size": candidate.size
                })
            
            if candidate.is_placeholder:
                placeholders.append({
                    "path": candidate.path,
                    "marker": "TODO",
                    "size": candidate.size
                })
            
            if candidate.vague_score >= 0.5:
                suggested_name = self._suggest_better_name(candidate)
                vague_files.append({
                    "path": candidate.path,
                    "score": candidate.vague_score,
                    "suggested_name": suggested_name
                })
        
        return empties, placeholders, vague_files
    
    def save_plan(self, plan: Dict):
        """Save plan to JSON file"""
        with open(".ops/dup_plan.json", "w") as f:
            json.dump(plan, f, indent=2)
    
    def _suggest_better_name(self, candidate: FileCandidate) -> str:
        """Suggest a better, more specific name"""
        # Analyze exports to infer purpose
        exports = candidate.exports
        path_parts = candidate.path.split("/")
        
        if not exports:
            return candidate.path
        
        # Simple heuristics based on exports
        if any("string" in e.lower() or "str" in e.lower() for e in exports):
            base_name = "string-utils"
        elif any("array" in e.lower() or "list" in e.lower() for e in exports):
            base_name = "array-utils"
        elif any("http" in e.lower() or "request" in e.lower() for e in exports):
            base_name = "http-client"
        elif any("auth" in e.lower() or "login" in e.lower() for e in exports):
            base_name = "auth-service"
        else:
            # Use first meaningful export name
            meaningful_exports = [e for e in exports if len(e) > 2]
            if meaningful_exports:
                base_name = meaningful_exports[0].lower() + "-utils"
            else:
                base_name = "utilities"
        
        # Reconstruct path with better name
        if len(path_parts) > 1:
            extension = os.path.splitext(candidate.path)[1]
            return "/".join(path_parts[:-1]) + "/" + base_name + extension
        else:
            return base_name + os.path.splitext(candidate.path)[1]

def main():
    detector = DuplicateDetector()
    plan = detector.scan_repository()
    
    # Save plan
    with open(".ops/dup_plan.json", "w") as f:
        json.dump(plan, f, indent=2)
    
    print("📊 Detection complete:")
    print(f"   • {plan['stats']['duplicate_groups']} duplicate groups")
    print(f"   • {plan['stats']['empty_files']} empty files")
    print(f"   • {plan['stats']['placeholder_files']} placeholder files")
    print(f"   • {plan['stats']['vague_named']} vague-named files")
    print("📁 Plan saved to .ops/dup_plan.json")

if __name__ == "__main__":
    main()