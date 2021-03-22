"""Create an example json file for MOA Transform."""
import json
from metakb.transform import MOATransform
from metakb import PROJECT_ROOT


def create_moa_example(moa_data):
    """Create MOA transform examples from list of evidence items."""
    evidence_items = 'moa:69'
    for response in moa_data:
        if 'evidence' in list(response.keys())[0]:
            if response['evidence'][0]['id'] == evidence_items:
                with open(f"{PROJECT_ROOT}/analysis/moa/examples/transform/"
                          f"{response['evidence'][0]['id']}.json", 'w+') as f:
                    json.dump(response, f)


if __name__ == '__main__':
    moa = MOATransform()
    transformation = moa.transform()
    moa._create_json(transformation)
    with open(f"{PROJECT_ROOT}/data/moa/transform/moa_cdm.json", 'r') as f:
        moa_data = json.load(f)
    create_moa_example(moa_data)
