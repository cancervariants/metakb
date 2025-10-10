from metakb.harvesters.base import Harvester, _HarvestedData
import logging
import pandas as pd
import requests


# data = "pediatric-oncology-drug-approvals"
# url = https://www.fda.gov/about-fda/oncology-center-excellence/{data}
# output_path = f"{data}.tar.gz"
# query_parameters = {"downloadformat": "tar.gz"}
#
# response = requests.get(url, stream=True, params=query_parameters)
# print(response.status_code)


class PodaHarvester(Harvester):
    def harvest(self) -> _HarvestedData:
        raise NotImplementedError
