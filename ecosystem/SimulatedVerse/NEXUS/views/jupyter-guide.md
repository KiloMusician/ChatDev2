# Quick Pandas Recipes

```python
import json, pandas as pd
from pathlib import Path

idx = [json.loads(l) for l in (Path("NEXUS/datasets/index.ndjson")).read_text().splitlines()]
df = pd.DataFrame(idx)

# What's missing Rosetta?
df[df["rosetta"].apply(lambda x: not bool(x))][["path","lang"]].head()

# Where are HUD/UI files?
hud = df[df["tags"].apply(lambda t: any("ui:hud" in (x or "") for x in t))]
hud[["path","rosetta"]].head()

# Anchors (APIs/pages/agents)
anchors = df.explode("anchors")
anchors.dropna(subset=["anchors"]).head()
```