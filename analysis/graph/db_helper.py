"""Utility function to load/reload graph for development."""
from metakb.database import Graph
from metakb import PROJECT_ROOT
import json


g = Graph(uri="bolt://localhost:7687", credentials=("neo4j", "admin"))
g.clear()

fpath = PROJECT_ROOT / 'analysis' / 'graph' / 'civic_cdm_v3.json'
with open(fpath, 'r') as f:
    items = json.load(f)

count = 0
for item in items:
    if 'assertion' in item.keys():
        continue
    else:
        g.add_transformed_data(item)
        count += 1
print(count)
