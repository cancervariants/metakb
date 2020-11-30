"""Create an example json file for CIViC Harvester."""
import json
from metakb.harvesters import CIViC
from metakb import PROJECT_ROOT


c = CIViC()
c.harvest()

with open(f'{PROJECT_ROOT}/data/civic/civic_harvester.json', 'r') as f:
    data = json.load(f)

for i in range(len(data['evidence'])):
    if data['evidence'][i]['assertions']:
        evidence_item = data['evidence'][i]

evidence_item_id = evidence_item['id']
variant_id = evidence_item['variant_id']
gene_id = evidence_item['gene_id']
assertions = evidence_item['assertions']

for v in data['variants']:
    if v['id'] == variant_id:
        variant = v

for g in data['genes']:
    if g['id'] == gene_id:
        gene = g

with open(f'{PROJECT_ROOT}/analysis/civic_harvester_ev_id_'
          f'{evidence_item_id}.json', 'w+') as f:
    example = {
        'EVIDENCE': evidence_item,
        'GENE': gene,
        'VARIANT': variant,
        'ASSERTIONS': assertions
    }

    json.dump(example, f)
    f.close()
