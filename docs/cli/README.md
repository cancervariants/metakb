# MetaKB CLI

More information on MetaKB CLI arguments

* `--db_url`
  * URL endpoint for the application Neo4j database. Can also be provided via environment variable `METAKB_DB_URL`.

* `--db_username`
  * Username to provide to application Neo4j database. Can also be provided via environment variable `METAKB_DB_USERNAME`.

* `--db_password`
  * Password to provide to application Neo4j database. Can also be provided via environment variable `METAKB_DB_PASSWORD`.

* `--load_normalizers_db`
  * Check normalizers' (therapy, disease, and gene) DynamoDB database and load data if source data is not present.

* `--force_load_normalizers_db`
  * Load all normalizers' (therapy, disease, and gene) data into DynamoDB database. Overrides `--load_normalizers_db` if both are selected.

* `--normalizers_db_url`
  * URL endpoint of normalizers' (therapy, disease, and gene) DynamoDB database. Set to `http://localhost:8000` by default.

* `--load_latest_cdms`
  * Deletes all nodes from the MetaKB Neo4j database and loads it with the latest source transformed CDM files stored locally in the `metakb/data` directory. This bypasses having to run the source harvest and transform steps. Exclusive with `--load_target_cdm` and `--load_latest_s3_cdms`.

* `--load_target_cdm`
  * Load a source's transformed CDM file at specified path. This bypasses having to run the source harvest and transform steps. Exclusive with `--load_latest_cdms` and `--load_latest_s3_cdms`.

* `--load_latest_s3_cdms`
  * Deletes all nodes from the MetaKB Neo4j database, retrieves latest source transformed CDM files from public s3 bucket, and loads the Neo4j database with the retrieved data. This bypasses having to run the source harvest and transform steps Exclusive with `--load_latest_cdms` and `--load_target_cdms`.