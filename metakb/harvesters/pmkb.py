"""PMKB harvester"""
from base import Harvester
import requests


class PMKB(Harvester):
    """Harvester class for Weill Cornell PMKB"""

    def __init__(self):
        """Set up harvester object"""
        self.assertions = []

    def harvest(self):
        """Harvest PMKB source"""
        r = requests.get('https://pmkb.weill.cornell.edu/api/interpretations')
        self.assertions = r.json()['interpretations']
