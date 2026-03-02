### Transformers test data

* **base_build_statements_input.json**: contains source statement examples that have been produced by the transformers, but may or may not successfully normalize into MetaKB aggregations. Use as input to `Base._create_aggregate_statement()`
* **base_normalize_condition_input.json**: contains source Condition objects, pre-normalization. Use to test `Base._normalize_condition()`. Should contain simple diseases + complex disease/phenotype combos.
* **base_normalize_therapeutic_input.json**: contains source Therapeutic objects, pre-normalization. Use to test `Base._normalize_therapeutic()`. Should contain cases of single drugs + combo therapies.
