.. _examples:

Examples
========

This section contains example queries for common types of searches on the meta-knowledgebase.

**Searching for interpretations given a variant or gene and disease**

BRAF V600E melanoma (`Try it <https://search.cancervariants.org/#BRAF%20V600E%20melanoma>`_)

BRAF "breast cancer" (`Try it <https://search.cancervariants.org/#BRAF%20%22breast%20cancer%22>`_)

**Searching primary fields only for interpretations given a gene and disease**

genes:BRAF diseases:"breast cancer" (`Try it <https://search.cancervariants.org/#genes%3ABRAF%20diseases%3A%22breast%20cancer%22>`_)

**Searching for interpretations describing a gene fusion**

BCR ABL fusion (`Try it <https://search.cancervariants.org/#BCR%20ABL%20fusion>`_)

ABL fusion (`Try it <https://search.cancervariants.org/#ABL%20fusion>`_)

**Searching for tier I interpretations for a gene**

genes:EGFR evidence_label:(A OR B) (`Try it <https://search.cancervariants.org/#genes%3AEGFR%20evidence_label%3A(A%20OR%20B)>`_)

**Search for interpretations describing increased sensitivity to a drug**

Cisplatin association.evidence.description:sensitiv* (`Try it <https://search.cancervariants.org/#Cisplatin%20association.evidence.description%3Asensitiv*>`_)

**Search the API for interpretations using the GA4GH VR Specification**

The `GA4GH VR specification`_ is a way of representing variants for quick lookup across systems:

*Examples:*
  * By Allele accession (`Try it <https://search.cancervariants.org/api/v1/associations?size=10&from=1&q=ga4gh:VA.mJbjSsW541oOsOtBoX36Mppr6hMjbjFr>`__)
  * By Sequence Location accession (`Try it <https://search.cancervariants.org/api/v1/associations?size=10&from=1&q=ga4gh:SL.gJeEs42k4qeXOKy9CJ515c0v2HTu8s4K>`__)

.. _GA4GH VR specification: https://vr-spec.readthedocs.io/en/latest/