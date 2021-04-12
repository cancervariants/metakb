"""Create an example json file for MOA Transform."""
import json
from metakb.transform import MOATransform
from metakb import PROJECT_ROOT


def create_moa_example(moa_data):
    """Create MOA transform examples from list of evidence items."""
    assertion_id = ['moa:aid69', 'moa:aid186']
    ex = {}
    proposition = None
    var_des = None
    t_des = None
    d_des = None
    g_des = None
    method = None
    doc = None

    for asst_id in assertion_id:
        for statement in moa_data['statements']:
            if statement['id'] == asst_id:
                ex['statements'] = [statement]
                proposition = statement['proposition']
                var_des = statement['variation_descriptor']
                t_des = statement['therapy_descriptor']
                d_des = statement['disease_descriptor']
                method = statement['method']
                doc = statement['supported_by'][0]

        for p in moa_data['propositions']:
            if p['id'] == proposition:
                ex['propositions'] = [p]

        for v in moa_data['variation_descriptors']:
            if v['id'] == var_des:
                ex['variation_descriptors'] = [v]
                g_des = v['gene_context']

        for g in moa_data['gene_descriptors']:
            if g['id'] == g_des:
                ex['gene_descriptors'] = [g]

        for t in moa_data['therapy_descriptors']:
            if t['id'] == t_des:
                ex['therapy_descriptors'] = [t]

        for d in moa_data['disease_descriptors']:
            if d['id'] == d_des:
                ex['disease_descriptors'] = [d]

        for m in moa_data['methods']:
            if m['id'] == method:
                ex['methods'] = [m]

        for d in moa_data['documents']:
            if d['id'] == doc:
                ex['documents'] = [d]

        with open(f"{PROJECT_ROOT}/analysis/moa/examples/transform/"
                  f"{ex['statements'][0]['id']}.json", 'w+') as f:
            json.dump(ex, f)


if __name__ == '__main__':
    moa = MOATransform()
    moa.transform()
    moa._create_json()
    with open(f"{PROJECT_ROOT}/data/moa/transform/moa_cdm.json", 'r') as f:
        moa_data = json.load(f)
    create_moa_example(moa_data)
