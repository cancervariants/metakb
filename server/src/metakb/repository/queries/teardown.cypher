// Drop all nodes
MATCH (n) DETACH DELETE n;

// Drop constraints
DROP CONSTRAINT coding_constraint IF EXISTS;
DROP CONSTRAINT gene_id_constraint IF EXISTS;
DROP CONSTRAINT disease_id_constraint IF EXISTS;
DROP CONSTRAINT therapy_id_constraint IF EXISTS;
DROP CONSTRAINT variation_id_constraint IF EXISTS;
DROP CONSTRAINT categoricalvariant_id_constraint IF EXISTS;
DROP CONSTRAINT variantgroup_id_constraint IF EXISTS;
DROP CONSTRAINT location_id_constraint IF EXISTS;
DROP CONSTRAINT document_id_constraint IF EXISTS;
DROP CONSTRAINT statement_id_constraint IF EXISTS;
DROP CONSTRAINT method_id_constraint IF EXISTS;
DROP CONSTRAINT classification_constraint IF EXISTS;
DROP CONSTRAINT evidence_line_id_constraint IF EXISTS;
