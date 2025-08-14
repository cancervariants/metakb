   // Enforce unique IDs
   CREATE CONSTRAINT coding_constraint IF NOT EXISTS FOR (n:Strength) REQUIRE n.primaryCoding IS UNIQUE;
   CREATE CONSTRAINT gene_id_constraint IF NOT EXISTS FOR (n:Gene) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT disease_id_constraint IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT therapy_id_constraint IF NOT EXISTS FOR (n:Therapy) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT variation_id_constraint IF NOT EXISTS FOR (n:Variation) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT categoricalvariant_id_constraint IF NOT EXISTS FOR (n:CategoricalVariant) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT variantgroup_id_constraint IF NOT EXISTS FOR (n:VariantGroup) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT location_id_constraint IF NOT EXISTS FOR (n:Location) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT document_id_constraint IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT statement_id_constraint IF NOT EXISTS FOR (n:Statement) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT method_id_constraint IF NOT EXISTS FOR (n:Method) REQUIRE n.id IS UNIQUE;
   CREATE CONSTRAINT classification_constraint IF NOT EXISTS FOR (n:Classification) REQUIRE n.primaryCoding IS UNIQUE;
   CREATE CONSTRAINT evidence_line_id_constraint IF NOT EXISTS FOR (n:EvidenceLine) REQUIRE n.id IS UNIQUE;
