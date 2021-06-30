"""Biothings parser function for Meta-KB CDM"""
import os
import json

# from biothings import config
# from biothings.utils.dataload import dict_convert, dict_sweep


def load_statements(data_folder):
    """Load cdm"""
    infile = os.path.join(data_folder, "moa_cdmtest.json")
    assert os.path.exists(infile)
    with open(infile, "r") as f:
        data = json.load(f)

    for s in data["statements"]:
        _id = s["id"]
        record = {}
        record["statements"] = s
        doc = {"_id": _id, "statements": record}
        # print(doc)
        yield doc


def load_propositions(data_folder):
    """Load cdm"""
    infile = os.path.join(data_folder, "moa_cdmtest.json")
    assert os.path.exists(infile)
    with open(infile, "r") as f:
        data = json.load(f)

    for s in data["statements"]:
        _id = s["id"]
        proposition = s["proposition"]
        record = {}
        for p in data["propositions"]:
            if proposition == p["id"]:
                record["propositions"] = p
        doc = {"_id": _id, "propositions": record}
        # print(doc)
        yield doc
# a = load_cdm("/Users/jiachenliu/Documents/GitHub/metakb/data/moa/transform")
