from metakb.harvesters.base import Harvester, _HarvestedData # Note: When testing before updating to the server / client switch, these imports worked, but as of right now I get: ModuleNotFoundError: No module named 'metakb.harvesters.base'
# similarly, if I run from base import Harvester, _HarvestedData, I get ImportError: cannot import name 'APP_ROOT' from 'metakb' (unknown location) 
import logging
import pandas as pd

logger = logging.getLogger(__name__)

FILE_PATH = 'data/cbioportal' # TODO: Update to proper intended data path

STUDY_NAME = ['es_dfarber_broad_2014'] # TODO: Intent is to drop in study names as needed, SEE cbioportal study structure

FILE_TYPES = ['data_mutations',
              'data_clinical_patient',
              'data_clinical_sample',
              'meta_study'] 


class cBioportalHarvestedData(_HarvestedData):
    """Define output for the harvested data from cBioPortal"""
    variants: list[dict]
    patients: list[dict]
    samples: list[dict]
    metadata: list[dict]


class cBioportalHarvester(Harvester):
    """A class for the cBioPortal Harvester"""

    def __init__(self, study = STUDY_NAME[0]):
        """Initialize cBioPortal Harvester
        
        :param study: An individual study from the cBioPortal pediatric dataset"""
        self.filepath = f'{FILE_PATH}/{study}'
       
    def harvest(self):
        """Get cBioPortal datasets from specified study
        
        :return: All data for mutations, patients, samples, and metadata for one study from cBioPortal pediatric dataset"""
        variants = pd.read_csv(f'{self.filepath}/{FILE_TYPES[0]}.txt', sep='\t').to_dict(orient='records')
        patients = pd.read_csv(f'{self.filepath}/{FILE_TYPES[1]}.txt', sep='\t', skiprows=4).to_dict(orient='records')
        samples = pd.read_csv(f'{self.filepath}/{FILE_TYPES[2]}.txt', sep='\t', skiprows=4).to_dict(orient='records')
        metadata = pd.read_csv(f'{self.filepath}/{FILE_TYPES[3]}.txt', sep='\t').to_dict(orient='records')
        
        # TODO: better way to load in the four files?

        return cBioportalHarvestedData(
            variants=variants,
            patients=patients,
            samples=samples,
            metadata=metadata
        )


