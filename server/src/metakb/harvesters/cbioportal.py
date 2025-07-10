from metakb.harvesters.base import Harvester, _HarvestedData
import logging
import pandas as pd


#################HEATHER CODE################
# imports

import pandas as pd
import requests
import tarfile
import os
import numpy

# dl_dir = "/Users/costellh/repos/metakb/hmc_notebooks/"


# download files

# download data 
study = "es_dfarber_broad_2014"
url = f"https://cbioportal-datahub.s3.amazonaws.com/{study}.tar.gz"
output_path = f"{study}}.tar.gz"
query_parameters = {"downloadformat": "tar.gz"}

response = requests.get(url, stream=True, params=query_parameters)
print(response.status_code)

with open (output_path, mode="wb") as file: 
    for chunk in response.iter_content(chunk_size=8192):
        file.write(chunk)
    print(f"Downloaded {output_path}")

#TODO: softcode this
extract_dir = f"{study}}_extracted"
os.makedirs(extract_dir, exist_ok=True)

with tarfile.open(output_path, mode="r:gz") as tar:
    tar.extractall(path=extract_dir)

print(f"Extracted to: {extract_dir}")
#############END HEATHER CODE################


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

    def __init__(self, study = STUDY_NAME[0]): # TODO: hard coded for now, eventually for study in STUDY_NAME
        """Initialize cBioPortal Harvester
        
        :param study: An individual study from the cBioPortal pediatric dataset"""
        self.filepath = f'{FILE_PATH}/{study}'
        #TODO: Methods to download and gunzip?

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


