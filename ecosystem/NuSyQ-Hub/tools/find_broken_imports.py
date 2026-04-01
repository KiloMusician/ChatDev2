"""
Scan the repository for import statements, attempt to import each top-level module,
and report modules that fail to import along with the files that reference them.
Write JSON to tools/broken_imports.json and print a short summary.

Run from repo root: python tools/find_broken_imports.py

Notes:
- Relative imports (from .foo import X, level > 0) are skipped — they cannot be
  resolved as absolute top-level modules.
- Imports inside try/except ImportError blocks are tagged as "optional" in the
  output — they are guarded and degrade gracefully if missing.
- Known optional/external deps (torch, qiskit, transformers, etc.) are noted but
  not treated as hard failures.
"""
import ast
import importlib
import json
import os
import sys
import traceback
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Ensure repo root is first on sys.path so local packages (src/*) are importable
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SKIP_DIRS = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 'archive',
             'state', 'projects'}  # ChatDev-generated output — not project code

# Known optional/heavy deps that are expected to be absent in CI or dev installs.
# These are noted in output but not counted as errors.
OPTIONAL_DEPS = {
    'torch', 'torchvision', 'torchaudio',
    'qiskit', 'qiskit_aer', 'qiskit_ibm_runtime',
    'transformers', 'diffusers', 'accelerate', 'peft',
    'tensorflow', 'keras',
    'cv2', 'PIL',
    'scipy', 'sklearn', 'skimage',
    'cupy', 'numba',
    'openai', 'anthropic', 'cohere',
    'langchain', 'llama_index',
    'chromadb', 'faiss', 'pinecone',
    'chatdev',
    'ollama',
    # Project-local modules loaded via runtime sys.path manipulation
    'ArchitectureScanner',
    'LocalLLMConfigurationChatDevOllama',
    'Ollama_Client_for_ChatDev_Integration',
    'chatdev_launcher',
    'copilot_agent_launcher',
    'quantum_problem_resolver_test',
}


def _build_parent_map(tree):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    return parents


def _guarded_by_try_except(node, parents):
    """Walk up the parent chain; return True if any ancestor is a Try whose
    handlers include ImportError, ModuleNotFoundError, or bare Exception."""
    cur = node
    while id(cur) in parents:
        parent = parents[id(cur)]
        if isinstance(parent, ast.Try):
            for handler in parent.handlers:
                if handler.type is None:
                    return True  # bare except
                names = []
                if isinstance(handler.type, ast.Tuple):
                    names = [
                        n.id for n in handler.type.elts
                        if isinstance(n, ast.Name)
                    ]
                elif isinstance(handler.type, ast.Name):
                    names = [handler.type.id]
                if any(n in ('ImportError', 'ModuleNotFoundError', 'Exception') for n in names):
                    return True
        cur = parent
    return False


module_to_files = defaultdict(set)
optional_module_to_files = defaultdict(set)
all_modules = set()
optional_modules = set()

for root, dirs, files in os.walk(REPO_ROOT):
    # skip virtualenvs and large irrelevant dirs
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if not f.endswith('.py'):
            continue
        path = os.path.join(root, f)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                src = fh.read()
            tree = ast.parse(src, filename=path)
        except Exception:
            # skip files that don't parse
            continue
        parents = _build_parent_map(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if not name:
                        continue
                    top = name.split('.')[0]
                    guarded = _guarded_by_try_except(node, parents)
                    if guarded or top in OPTIONAL_DEPS:
                        optional_module_to_files[top].add(path)
                        optional_modules.add(top)
                    else:
                        module_to_files[top].add(path)
                        all_modules.add(top)
            elif isinstance(node, ast.ImportFrom):
                # Skip relative imports (from .foo import X, from ..bar import Y)
                if node.level and node.level > 0:
                    continue
                mod = node.module
                if mod is None:
                    continue
                top = mod.split('.')[0]
                if not top:
                    continue
                guarded = _guarded_by_try_except(node, parents)
                if guarded or top in OPTIONAL_DEPS:
                    optional_module_to_files[top].add(path)
                    optional_modules.add(top)
                else:
                    module_to_files[top].add(path)
                    all_modules.add(top)

missing = {}
checked = {}
for mod in sorted(all_modules):
    # Skip obviously internal/standard special-case names
    if mod in ('__future__',):
        continue
    try:
        importlib.import_module(mod)
        checked[mod] = {'ok': True}
    except Exception as e:
        missing[mod] = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'files': sorted(module_to_files.get(mod, []))
        }
        checked[mod] = {'ok': False, 'error': str(e)}

out = {
    'repo_root': REPO_ROOT,
    'total_required_modules': len(all_modules),
    'total_optional_modules': len(optional_modules),
    'checked_summary': checked,
    'missing': missing,
    'optional_not_checked': {
        mod: {'files': sorted(optional_module_to_files.get(mod, []))}
        for mod in sorted(optional_modules)
    },
}

out_path = os.path.join(REPO_ROOT, 'tools', 'broken_imports.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)

print(f"Wrote {out_path}")
print(f"Required modules: {len(all_modules)} checked; {len(missing)} failed to import.")
print(f"Optional/guarded: {len(optional_modules)} skipped (try/except or known optional dep).")
if missing:
    print("Hard-missing modules:")
    for m, info in list(missing.items())[:50]:
        print(f" - {m}: referenced in {len(info['files'])} files; error: {info['error']}")

print("Done.")
