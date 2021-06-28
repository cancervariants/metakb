"""Biothings parser function for Meta-KB CDM"""
import os
import json

# from biothings import config
# from biothings.utils.dataload import dict_convert, dict_sweep


def load_cdm(data_folder):
    """Load cdm"""
    infile = os.path.join(data_folder, "moa_cdmtest.json")
    assert os.path.exists(infile)
    with open(infile, "r") as f:
        data = json.load(f)

    results = {}
    proposition = None
    var_des = None
    t_des = None
    d_des = None
    g_des = None
    method = None
    doc = None

    for rec in data["statements"]:
        _id = rec["id"]
        record = {}
        record["statements"] = rec
        proposition = rec["proposition"]
        var_des = rec["variation_descriptor"]
        t_des = rec["therapy_descriptor"]
        d_des = rec["disease_descriptor"]
        method = rec["method"]
        doc = rec["supported_by"][0]

        for p in data["propositions"]:
            if p["id"] == proposition:
                record["propositions"] = p

        for v in data["variation_descriptors"]:
            if v["id"] == var_des:
                record["variation_descriptors"] = v
                g_des = v["gene_context"]

        for g in data["gene_descriptors"]:
            if g["id"] == g_des:
                record["gene_descriptors"] = g

        for t in data["therapy_descriptors"]:
            if t["id"] == t_des:
                record["therapy_descriptors"] = t

        for d in data["disease_descriptors"]:
            if d["id"] == d_des:
                record["disease_descriptors"] = d

        for m in data["methods"]:
            if m["id"] == method:
                record["methods"] = m

        for d in data["documents"]:
            if d["id"] == doc:
                record["documents"] = d
        results.setdefault(_id, []).append(record)

    for _id, docs in results.items():
        doc = {"_id": _id, "cdm": docs}
        doc = json.dumps(doc)
        yield doc

# a = load_cdm("/Users/jiachenliu/Documents/GitHub/metakb/data/moa/transform")
