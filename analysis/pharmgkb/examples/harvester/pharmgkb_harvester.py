"""Grab some example data for pharmgkb."""

from metakb.harvesters import PharmGKBHarvester

if __name__ == "__main__":
    ph = PharmGKBHarvester()
    ph.harvest()
