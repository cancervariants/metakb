Glossary
========

.. glossary::

    Associations
        Associations are top-level records linking between one or more :term:`features<feature>` and
        one or more :term:`diseases<disease>`, supported by some amount of published :term:`evidence`.
        For somatic :term:`features<feature>`, associations typically describe a therapeutic response
        to a linked :term:`drug` in the context of a :term:`disease`.

    Disease
        Diseases are terms describing the phenotypic context of the containing :term:`Associations`,
        the majority of which are cancers. These terms have been normalized to `Disease Ontology`_
        terms when possible.

    Drug
        Drugs are terms describing therapeutic interventions, which have been normalized to the

    Evidence
        Evidence describes the clinical significance of :term:`associations` by :term:`evidence label`
        and links the significance to a publication or expert consensus.

    Evidence Label
        Evidence labels follow the `guidelines`_ jointly published by the Association for Molecular
        Pathology, American Society of Clinical Oncology, and the College of American Pathologists.
        We have normalized the :term:`evidence` for each knowledgebase to best fit these
        recommendations:

        .. image:: /images/amp_asco_cap_table.png

    Feature
        Genomic features identify changes to one or more genomic regions (e.g. genes, chromosomal
        segments, regulatory regions). These changes may be genetic, epigenetic, or transcriptomic in
        nature. For somatic mutations, this most commonly refers to a single amino-acid substitution
        in a gene. Features are normalized to records in the `Clingen Allele Registry`_ as available.


.. _Disease Ontology: http://disease-ontology.org/
.. _guidelines: https://jmd.amjpathol.org/article/S1525-1578(16)30223-9/abstract
.. _Clingen Allele Registry: http://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/landing

