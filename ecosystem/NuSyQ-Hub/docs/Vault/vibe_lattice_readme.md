# VIBE Lattice — quick README

This lattice was generated from `filipecalegario/awesome-vibe-coding` and
indexed by `src/tools/vibe_indexer.py`.

Location: `lattices/vibe.json`

How to use:

1. Inspect the lattice JSON for nodes and edges. Each node includes a `shadow`
   object with conservative metadata (lic, fresh, fit, risk).
2. Use your local RAG server or embedding pipeline to index
   `lattices/vibe.json`.
3. Register with ChatDev (or your planner) by pointing it at the lattice file.

Example commands:

```powershell
# parse the repo into the lattice (if you re-clone)
python -m src.tools.vibe_indexer _vibe --out lattices/vibe.json

# (manual) start a RAG server or register with ChatDev
# nu-syq-hub rag serve --index ./lattices/vibe.json --model ollama:llama3.1
# chatdev register-knowledge vibe ./lattices/vibe.json
```

Notes:

- The indexer is intentionally lightweight and conservative. It extracts
  headings and links from Markdown files and guesses 'fit' and 'kind' using
  heuristics. You should review and refine the lattice (licenses, risk) before
  using it in production.
