"""Create an example json file for pmkb transform."""
import json
from metakb.transform import PMKBTransform
from metakb import PROJECT_ROOT
import logging

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


def create_pmkb_example(pmkb_data):
    """Create pmkb transform examples from list of evidence items."""
    ex = {}

    for statement in pmkb_data['statements']:
        if statement['id'] == 'pmkb:113':
            ex['statements'] = [statement]
            break

    for proposition in pmkb_data['propositions']:
        if proposition['subject'] == \
                'ga4gh:VA.6CgLeqGUIVF2XLiMwOpy142d2_iBTt7V' and \
                proposition['object_qualifier'] == 'ncit:C2852' and \
                proposition['object'] == 'ncit:C49236':
            ex['propositions'] = [proposition]
            break

    for vod in pmkb_data['variation_descriptors']:
        if vod['value_id'] == 'ga4gh:VA.6CgLeqGUIVF2XLiMwOpy142d2_iBTt7V':
            ex['variation_descriptors'] = [vod]
            break

    for vod in pmkb_data['disease_descriptors']:
        if vod['value']['id'] == 'ncit:C2852':
            ex['disease_descriptors'] = [vod]
            break

    for vod in pmkb_data['therapy_descriptors']:
        if vod['value']['id'] == 'ncit:C49236':
            ex['therapy_descriptors'] = [vod]
            break

    for vod in pmkb_data['gene_descriptors']:
        if vod['id'] == 'pmkb.normalize.gene:CTNNB1':
            ex['gene_descriptors'] = [vod]
            break

    for method in pmkb_data['methods']:
        if method['id'] == 'method:5':
            ex['methods'] = [method]
            break

    doc_ids = [
        "document:3",
        "document:4",
        "document:5",
        "document:6",
        "document:7",
        "document:8",
        "document:9",
        "document:10",
        "document:11",
        "document:12"
    ]
    ex['documents'] = []
    for document in pmkb_data['documents']:
        if document['id'] in doc_ids:
            ex['documents'].append(document)

    file_path = PROJECT_ROOT / 'analysis' / 'pmkb' / 'examples' / 'transform' / 'pmkb_cdm_example.json'  # noqa: E501
    with open(file_path, 'w+') as f2:
        json.dump(ex, f2)


if __name__ == '__main__':
    pmkb = PMKBTransform()
    pmkb.transform()
    pmkb._create_json()
    file_path = PROJECT_ROOT / 'data' / 'pmkb' / 'transform' / 'pmkb_cdm.json'
    with open(file_path, 'r') as f:
        pmkb_data = json.load(f)
    create_pmkb_example(pmkb_data)
