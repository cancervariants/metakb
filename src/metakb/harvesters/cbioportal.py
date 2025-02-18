"""A module for the cBioPortal harvester."""
# import pybioportal 

# for testing, we can just run this as independent script and then hook it in once we are satisfied with the returned objects.

class cBioPortalHarvestedData(_HarvestedData):
    """Define output for harvested data from CIViC"""

    # genes: list[dict]
    # evidence: list[dict]
    # molecular_profiles: list[dict]
    # assertions: list[dict]


class cBioPortalHarvester(Harvester):


    # Code for harvesting the data goes
    # a list of the molecular profile ids for our desired studies
    # pybioportal methods that pull out allele frequency data for each study
    # return a cBioPortalHarvestedData object containing this

    # TODO: Evaluate where the calculations for Cohort Allele Frequency would live, i.e at harvested stage or transformer stage, or something else. 



