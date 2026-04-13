## Transformers test data

### test_base.py

* **base_construct_statements_input.json**: contains source statement examples that have been produced by the transformers, but may or may not successfully normalize into MetaKB aggregations. Use as input to `Base._create_aggregate_statement()`
  * Also used in `test_methodology.py`
* **base_normalize_condition_input.json**: contains source Condition objects, pre-normalization. Use to test `Base._normalize_condition()`. Should contain simple diseases + complex disease/phenotype combos.
* **base_normalize_therapeutic_input.json**: contains source Therapeutic objects, pre-normalization. Use to test `Base._normalize_therapeutic()`. Should contain cases of single drugs + combo therapies.

### test_moa.py

* **moa_create_variants_input.json**: contains MOA variant examples provided by the harvester. Use to test `MoaTransformer._create_moa_variant()`
* **moa_normalize_variants_input.json**: contains source catvars created by the transformer to attempt to normalize. Use to test `MoaTransformer._normalize_variant()`
* **moa_harvested_data.json**: a minimal example of a complete harvested data file to validate end-to-end transformation.

### test_civic.py

* **civic_ensure_conditionset_id_input.json**: CIViC ConditionSet objects to test in-place ID generation
* **civic_ensure_therapygroup_id_input.json**: CIViC TherapyGroup objects to test in-place ID generation
* **civic_normalize_variant_input.json**: Raw variants from CIViC for testing variation normalization
* **civicpy_transformer_cache.pkl**: civicpy cache to use for `transform()` tests
* **generate_civicpy_cache.py**: helper script for generating new test caches
