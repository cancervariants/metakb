.. _examples:

Examples
========

This section contains example queries for common types of searches on the meta-knowledgebase.

**Searching for interpretations given a variant or gene and disease**
::

 BRAF V600E melanoma
 BRAF "breast cancer"

**Searching primary fields only for interpretations given a gene and disease**
::

 genes:BRAF diseases:"breast cancer"

**Searching for interpretations describing a gene fusion**
::

 BCR ABL fusion
 ABL fusion

**Searching for tier I interpretations for a gene**
::

 genes:EGFR evidence_label:(A OR B)

**Search for interpretations describing increased sensitivity to a drug**
::

 Cisplatin association.evidence.description:sensitiv*