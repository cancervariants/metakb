"""Create an example json file for CIViC Harvester."""
import json
from metakb.harvesters import CIViC
from metakb import PROJECT_ROOT


c = CIViC()
c.harvest()

with open(f'{PROJECT_ROOT}/data/civic/civic_harvester.json', 'r') as f:
    data = json.load(f)

# Create 5 examples from evidence items
evidence_items = list()
for i in range(len(data['evidence'])) and len(evidence_items) < 6:
    if data['evidence'][i]['assertions']:
        evidence_items.append(data['evidence'][i])


for evidence_item in evidence_items:
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

    with open(f'{PROJECT_ROOT}/analysis/civic/examples/ev_id_'
              f'{evidence_item_id}.json', 'w+') as f:
        example = {
            'EVIDENCE': evidence_item,
            'GENE': gene,
            'VARIANT': variant,
            'ASSERTIONS': assertions
        }

        json.dump(example, f)
        f.close()

# BRAF600E, BCR-ABL Variant, TP53 Loss (of function), EGFR Amplification
variants_ids = [12, 1, 221, 190]
variants = list()
for i in range(len(data['variants'])):
    if data['variants'][i]['id'] in variants_ids:
        variants.append(data['variants'][i])

for variant in variants:
    with open(f"{PROJECT_ROOT}/analysis/civic/examples/"
              f"{variant['name'].lower()}.json", 'w+') as f:
        variant['evidence_items'] = variant['evidence_items'][0]
        f.write(json.dumps(variant))
        print(f"Creating JSON for variant: {variant['name']}")
        f.close()
