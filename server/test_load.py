import json
from pathlib import Path
from timeit import default_timer as timer

from dotenv import load_dotenv

load_dotenv()

from neomodel import config as neomodel_config

from metakb.database.graph import clear_graph, configure_db
from metakb.load_data import _get_ids_to_load
from metakb.database.load import _add_dac_cv
from metakb.database.models import *

configure_db()
clear_graph()

with open(
    "/Users/jss009/.local/share/wags_tails/metakb/civic/transformers/civic_cdm_20250722.json"
) as f:
    data = json.load(f)


statements_evidence = data.get("statements_evidence", [])
ids_to_load = _get_ids_to_load(statements_evidence)

statements_assertions = data.get("statements_assertions", [])
ids_to_load.update(_get_ids_to_load(statements_assertions, ids_to_load=ids_to_load))
catvars = data["categorical_variants"]

start = timer()

for catvar in catvars:
    if catvar["id"] not in ids_to_load:
        continue
    _add_dac_cv(catvar)
end = timer()


print(f"Successfully loaded neo4j database in {(end - start):.5f} s")
