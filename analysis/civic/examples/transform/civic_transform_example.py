"""Create an example json file for CIViC Transform."""
import json
from metakb.transform import CIViCTransform
from metakb import PROJECT_ROOT


def create_civic_example(civic_data):
    """Create CIViC transform examples from list of evidence items."""
    ex = {
        'statements': [],
        'propositions': [],
        'variation_descriptors': [],
        'gene_descriptors': [],
        'therapy_descriptors': [],
        'disease_descriptors': [],
        'methods': [],
        'documents': []
    }
    supported_by_statement_ids = list()
    for s in civic_data['statements']:
        if s['id'] == 'civic:aid6':
            supported_by_statement_ids = \
                [s for s in s['supported_by'] if s.startswith('civic:eid')]
            supported_by_statement_ids += s['id']
            break

    for s in civic_data['statements']:
        if s['id'] in supported_by_statement_ids:
            ex['statements'].append(s)

    for p in civic_data['propositions']:
        if p['subject'] == 'ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR' and p['object_qualifier'] == 'ncit:C2926' and p['object'] == 'ncit:C66940':  # noqa: E501
            ex['propositions'].append(p)
            break

    for v in civic_data['variation_descriptors']:
        if v['id'] == 'civic:vid33':
            ex['variation_descriptors'].append(v)
            break

    for t in civic_data['therapy_descriptors']:
        if t['id'] == 'civic:tid146':
            ex['therapy_descriptors'].append(t)
            break

    for g in civic_data['gene_descriptors']:
        if g['id'] == 'civic:gid19':
            ex['gene_descriptors'].append(g)
            break

    for m in civic_data['methods']:
        if m['id'] in ['method:001', 'method:002']:
            ex['methods'].append(m)

    for d in civic_data['documents']:
        if d['id'] in ['pmid:23982599', 'document:001']:
            ex['documents'].append(d)

    with open(f"{PROJECT_ROOT}/analysis/civic/examples/transform/"
              f"civic_cdm.json", 'w+') as f2:
        json.dump(ex, f2)


if __name__ == '__main__':
    civic = CIViCTransform()
    civic.transform()
    civic._create_json()
    with open(f"{PROJECT_ROOT}/data/civic/transform/civic_cdm.json", 'r') as f:
        civic_data = json.load(f)
    create_civic_example(civic_data)
