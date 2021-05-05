#!/bin/bash 
#
# Export useful paths for data dependencies
#
python3 -c '
from therapy import PROJECT_ROOT as THERAPY_PROJECT_ROOT
from disease import PROJECT_ROOT as DISEASE_PROJECT_ROOT
from gene import PROJECT_ROOT as GENE_PROJECT_ROOT
from variant import SEQREPO_DATA_PATH, TRANSCRIPT_MAPPINGS_PATH
import variant

print(f"""
export THERAPY_PROJECT_ROOT={THERAPY_PROJECT_ROOT}
export DISEASE_PROJECT_ROOT={DISEASE_PROJECT_ROOT}
export GENE_PROJECT_ROOT={GENE_PROJECT_ROOT}
export SEQREPO_DATA_PATH={SEQREPO_DATA_PATH}
export TRANSCRIPT_MAPPINGS_PATH={TRANSCRIPT_MAPPINGS_PATH}
export VARIANT_PROJECT_ROOT={variant.__path__[0]}
""")
'
