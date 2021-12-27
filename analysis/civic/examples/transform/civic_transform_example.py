"""Create an example json file for CIViC Transform."""
import json
from datetime import datetime as dt

from metakb import PROJECT_ROOT, APP_ROOT, DATE_FMT
from metakb.transform import CIViCTransform


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
    supported_by_statement_ids = set()
    for s in civic_data['statements']:
        if s['id'] == 'civic.aid:6':
            supported_by_statement_ids = \
                {s for s in s['supported_by'] if s.startswith('civic.eid')}
            supported_by_statement_ids.add(s['id'])
            break

    proposition_ids = set()
    vids = set()
    tids = set()
    dids = set()
    gids = set()
    methods = set()
    documents = set()
    for s in civic_data['statements']:
        if s['id'] in supported_by_statement_ids:
            ex['statements'].append(s)
            proposition_ids.add(s['proposition'])
            vids.add(s['variation_descriptor'])
            tids.add(s['therapy_descriptor'])
            dids.add(s['disease_descriptor'])
            methods.add(s['method'])
            documents.update({d for d in s['supported_by'] if
                             not d.startswith('civic.eid')})

    for p in civic_data['propositions']:
        if p['id'] in proposition_ids:
            ex['propositions'].append(p)

    for v in civic_data['variation_descriptors']:
        if v['id'] in vids:
            ex['variation_descriptors'].append(v)
            gids.add(v['gene_context'])

    for t in civic_data['therapy_descriptors']:
        if t['id'] in tids:
            ex['therapy_descriptors'].append(t)

    for d in civic_data['disease_descriptors']:
        if d['id'] in dids:
            ex['disease_descriptors'].append(d)

    for g in civic_data['gene_descriptors']:
        if g['id'] in gids:
            ex['gene_descriptors'].append(g)

    for m in civic_data['methods']:
        if m['id'] in methods:
            ex['methods'].append(m)

    for d in civic_data['documents']:
        if d['id'] in documents:
            ex['documents'].append(d)

    today = dt.strftime(dt.today(), DATE_FMT)
    with open(PROJECT_ROOT / "analysis" / "civic" / "examples" /  # noqa: W504
              "transform" / f"civic_cdm_{today}.json", 'w+') as f2:
        json.dump(ex, f2, indent=4)


if __name__ == '__main__':
    civic = CIViCTransform()
    civic.transform()
    civic._create_json()
    with open(f"{APP_ROOT}/data/civic/transform/civic_cdm.json",
              'r') as f:
        civic_data = json.load(f)
    create_civic_example(civic_data)
