"""Generate a civicpy cache pkl

Navigate to the transformers tests data directory and run the script to repopulate the
test cache PKL:

```console
cd tests/data/transformers
python generate_civicpy_cache.py
```
"""

from pathlib import Path

import civicpy.civic as civicpy

civicpy.load_cache()

working_cache = civicpy.CACHE

# IDs for items to save
# Populate these fields to select items for saving in the cache. In the future, this
# could probably be refactored such that the entity IDs are auto-populated given the
# selected ev item IDs.
evidence_item_ids = [238]
assertion_ids = []
variant_ids = [34]
mp_ids = [34]
disease_ids = [8]
therapy_ids = [15]

keys_to_save: list[str | int] = [
    "evidence_items_all_ids",
    "molecular_profiles_all_ids",
    "variants_all_ids",
    "diseases_all_ids",
    "therapies_all_ids",
    "assertions_all_ids",
]

# get hash for items and add to save list
for ei_id in evidence_item_ids:
    element_type = "evidence"
    klass = civicpy.get_class(element_type)
    r = klass(type=element_type, id=ei_id, partial=True)
    keys_to_save.append(hash(r))
for mp_id in mp_ids:
    element_type = "molecular_profile"
    klass = civicpy.get_class(element_type)
    r = klass(type=element_type, id=mp_id, partial=True)
    keys_to_save.append(hash(r))
for variant_id in variant_ids:
    element_type = "variant"
    klass = civicpy.get_class(element_type)
    r = klass(type=element_type, id=variant_id, partial=True)
    keys_to_save.append(hash(r))
for disease_id in disease_ids:
    element_type = "disease"
    klass = civicpy.get_class(element_type)
    r = klass(type=element_type, id=disease_id, partial=True)
    keys_to_save.append(hash(r))
for therapy_id in therapy_ids:
    element_type = "therapy"
    klass = civicpy.get_class(element_type)
    r = klass(type=element_type, id=therapy_id, partial=True)
    keys_to_save.append(hash(r))

# remove unwanted stuff from cache
working_cache["evidence_items_all_ids"] = evidence_item_ids
working_cache["assertions_all_ids"] = assertion_ids
working_cache["molecular_profiles_all_ids"] = mp_ids
working_cache["variants_all_ids"] = variant_ids
working_cache["diseases_all_ids"] = disease_ids
working_cache["therapies_all_ids"] = therapy_ids
keys = list(working_cache.keys())
for key in keys:
    if key in keys_to_save:
        continue
    del working_cache[key]

# save to new location
new_cache_location = Path("civicpy_transformer_cache.pkl")
civicpy.save_cache(str(new_cache_location))
