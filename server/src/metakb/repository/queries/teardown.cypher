// these should, generally, be executed in a single transaction, and it'd be annoying to keep them in their own query files
// but they all have to be executed separately so the repository class has to do a little post-processing to split them all up
//
// drop constraints
DROP CONSTRAINT coding_constraint IF EXISTS;
DROP CONSTRAINT gene_id_constraint IF EXISTS;
DROP CONSTRAINT condition_id_constraint IF EXISTS;
DROP CONSTRAINT disease_id_constraint IF EXISTS;
DROP CONSTRAINT therapeutic_id_constraint IF EXISTS;
DROP CONSTRAINT variation_id_constraint IF EXISTS;
DROP CONSTRAINT categoricalvariant_id_constraint IF EXISTS;
DROP CONSTRAINT categoricalvariantconstraint_id_constraint IF EXISTS;
DROP CONSTRAINT location_id_constraint IF EXISTS;
DROP CONSTRAINT document_id_constraint IF EXISTS;
DROP CONSTRAINT statement_id_constraint IF EXISTS;
DROP CONSTRAINT method_id_constraint IF EXISTS;
DROP CONSTRAINT classification_constraint IF EXISTS;
DROP CONSTRAINT evidence_line_id_constraint IF EXISTS;
