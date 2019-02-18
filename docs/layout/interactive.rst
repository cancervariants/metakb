Exploring Results
=================

.. _custom-filter:

Custom Filter
-------------

Search results may also be selectively reduced through the use of custom filters,
such as the previously described :ref:`paper-filter`. To create a new filter,
select **"Add a filter +"** on the filter bar to open the add filter form:

.. image:: /images/add_filter_form.png

After selecting **Save**, the above will create a filter for AMP/ASCO/CAP Tier I
(evidence label A, B) interpretations by selecting the *evidence_label* field and
designating a set of values (`A`, `B`) that the field must match. We now have this
additional filter available to be enable or disabled as needed during the review
of search results by selecting the *disable*/*enable* button on the filter:

.. image:: /images/filter_disable.png
    :width: 300px

Result Count
------------

The result count is the total number of :term:`associations` matching the search
criteria.

.. image:: /images/result_count.png
    :width: 300px

Source Pie
----------

This interactive pie chart illustrates the distribution of results across the
constituent sources of the meta-knowledgebase. Clicking on a segment of the pie chart
will automatically create a :ref:`custom-filter` for the selected element. This filter
may be manually edited to include additional sources.

.. image:: /images/source_pie.png
    :width: 600px

Evidence Pie
------------

This interactive pie chart illustrates the distribution of results by normalized
evidence label (levels A-D) based on the AMP/ASCO/CAP guidelines. Clicking on a segment
of the pie chart will automatically create a :ref:`custom-filter` for the selected
element. This filter may be manually edited to include additional evidence levels.

.. image:: /images/evidence_pie.png
    :width: 600px

Gene/Drug Heatmap
-----------------

This interactive heatmap visualizes the frequency of results describing a gene/drug
pair. Clicking on a tile of the heatmap will automatically create two
:ref:`Custom Filters<custom-filter>` for the selected gene and drug, respectively.
Each element may be enabled, disabled, and edited independently.

.. image:: /images/gene_drug_heatmap.png
    :width: 750px

Gene/Disease Heatmap
--------------------

This interactive heatmap visualizes the frequency of results describing a gene/disease
pair. Clicking on a tile of the heatmap will automatically create two
:ref:`Custom Filters<custom-filter>` for the selected gene and drug, respectively.
Each element may be enabled, disabled, and edited independently.

.. image:: /images/gene_drug_heatmap.png
    :width: 750px