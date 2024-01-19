"""Utility function to load/reload graph for development."""
import json

from metakb import APP_ROOT
from metakb.database import Graph

g = Graph(uri="bolt://localhost:7687", credentials=("neo4j", "admin"))
g.clear()

fpath = APP_ROOT / "data" / "civic" / "transform" / "civic_cdm.json"
with open(fpath, "r") as f:
    items = json.load(f)

count = 0
for item in items:
    if "assertion" in item.keys():
        continue
    else:
        g.add_transformed_data(item)
        count += 1
print(count)
