"""Create an example json file for CIViC Transform."""
import json
from metakb.transform import CIViCTransform
from metakb import PROJECT_ROOT


def create_civic_example(civic_data):
    """Create CIViC transform examples from list of evidence items."""
    evidence_items = ['civic:eid2997']
    assertions = ['civic:aid6']
    for response in civic_data:
        if 'evidence' in response.keys():
            if response['evidence'][0]['id'] in evidence_items:
                with open(f"{PROJECT_ROOT}/analysis/civic/examples/transform/"
                          f"{response['evidence'][0]['id']}.json", 'w+') as f1:
                    json.dump(response, f1)
        if 'assertion' in response.keys():
            if response['assertion'][0]['id'] in assertions:
                with open(f"{PROJECT_ROOT}/analysis/civic/examples/transform/"
                          f"{response['assertion'][0]['id']}.json", 'w+') as f2:  # noqa: E501
                    json.dump(response, f2)


if __name__ == '__main__':
    civic = CIViCTransform()
    transformation = civic.transform()
    civic._create_json(transformation)
    with open(f"{PROJECT_ROOT}/data/civic/transform/civic_cdm.json", 'r') as f:
        civic_data = json.load(f)
    create_civic_example(civic_data)
