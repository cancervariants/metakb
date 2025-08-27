.. _config:

Configuration
-------------

.. _metakb-db-url:

MetaKB DB URL
=============

Use the environment variable ``METAKB_DB_URL`` to configure a connection to Neo4j, in the format of ``"<protocol>://<username>:<password>@<host>"``. The default value is ``bolt://neo4j:neo4j@localhost:7687``.

.. _config-data-directory:

Data directory
==============

During the process of data ingestion and upload, MetaKB generates a number of intermediate data objects. Organized by source and by type, these are stored within a data directory that can be set globally with the ``METAKB_DATA_DIR`` environment variable. Otherwise, the default location is determined by the ``wags-tails`` library (``~/.local/share/wags-tails/metakb``, absent further configuration). See the `wags-tails documentation <https://wags-tails.readthedocs.io/stable/reference/api/utils/wags_tails.utils.storage.html#wags_tails.utils.storage.get_data_dir>`_ for more information.
