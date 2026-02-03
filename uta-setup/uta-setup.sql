\c uta;
CREATE TABLE uta_20241220.genomic AS
SELECT t.hgnc, aes.alt_ac, aes.alt_aln_method,
    aes.alt_strand, ae.start_i AS alt_start_i,
    ae.end_i AS alt_end_i
FROM (((((uta_20241220.transcript t
    JOIN uta_20241220.exon_set tes ON (((t.ac = tes.tx_ac)
        AND (tes.alt_aln_method = 'transcript'::text))))
    JOIN uta_20241220.exon_set aes ON (((t.ac = aes.tx_ac)
        AND (aes.alt_aln_method <> 'transcript'::text))))
    JOIN uta_20241220.exon te ON
        ((tes.exon_set_id = te.exon_set_id)))
    JOIN uta_20241220.exon ae ON
        (((aes.exon_set_id = ae.exon_set_id)
        AND (te.ord = ae.ord))))
    LEFT JOIN uta_20241220.exon_aln ea ON
        (((te.exon_id = ea.tx_exon_id) AND
        (ae.exon_id = ea.alt_exon_id))));

CREATE INDEX alt_pos_index ON uta_20241220.genomic (alt_ac, alt_start_i, alt_end_i);
CREATE INDEX gene_alt_index ON uta_20241220.genomic (hgnc, alt_ac);
CREATE INDEX alt_ac_index ON uta_20241220.genomic (alt_ac);

GRANT CONNECT ON DATABASE uta TO anonymous;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA uta_20241220 TO anonymous;
ALTER DATABASE uta OWNER TO anonymous;
ALTER SCHEMA uta_20241220 OWNER to anonymous;
