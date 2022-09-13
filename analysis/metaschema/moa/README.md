# Metaschema Update Analysis for MOAlmanac

This analysis is only for Therapeutic Response evidence for MOAlmanac.

## Files

- `moa_does_not_support_variation.txt`
  - Variation Normalizer does not support these variations. In MOA transform, we have multiple conditions (such as required protein change and gene is required) that we know the variation normalizer does not support. This file provides a list of MOA Variant IDs and its associated query that is not supported.

- `moa_unable_to_normalize_variation.txt`
  - Tried running queries in the Variation Normalizer, but the Variation Normalizer was unable to return a variation descriptor given the query. This file provides a list of MOA Variant IDs and its associated query that was not able to be normalized.

- `moa_variant_id_to_aids_missed.txt`
  - Tried running query in the Variation Normalizer, but the Variation Normalizer was unable to return a variation descriptor given the query. This file contains a list of MOA Variant IDs, number of AIDs that were affected, and set the associated AIDs.
