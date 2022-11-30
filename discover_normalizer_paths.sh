#!/bin/bash 
#
# Export useful paths for data dependencies
#
python3 -c '
from therapy import APP_ROOT as THERAPY_PROJECT_ROOT
from disease import PROJECT_ROOT as DISEASE_PROJECT_ROOT
from gene import APP_ROOT as GENE_PROJECT_ROOT
from gene import SEQREPO_DATA_PATH
from variation import AMINO_ACID_PATH
import variation

print(f"""
export THERAPY_PROJECT_ROOT={THERAPY_PROJECT_ROOT}
export DISEASE_PROJECT_ROOT={DISEASE_PROJECT_ROOT}
export GENE_PROJECT_ROOT={GENE_PROJECT_ROOT}
export SEQREPO_DATA_PATH={SEQREPO_DATA_PATH}
export AMINO_ACID_PATH={AMINO_ACID_PATH}
export VARIATION_PROJECT_ROOT={variation.__path__[0]}
""")
'
