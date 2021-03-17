"""Create an example json file for CIViC Harvester."""
import json
from metakb.harvesters import CIViC
from metakb import PROJECT_ROOT


def create_evidence_examples(data):
    """Create five CIViC evidence examples."""
    evidence_items = list()
    for i in range(len(data['evidence'])):
        if data['evidence'][i]['assertions']:
            evidence_items.append(data['evidence'][i])
        if len(evidence_items) == 6:
            break

    for evidence_item in evidence_items:
        variant_id = evidence_item['variant_id']
        gene_id = evidence_item['gene_id']
        assertions = evidence_item['assertions']

        for v in data['variants']:
            if v['id'] == variant_id:
                variant = v

        for g in data['genes']:
            if g['id'] == gene_id:
                gene = g

        with open(f"{PROJECT_ROOT}/analysis/civic/examples/harvester/"
                  f"{evidence_item['name']}.json", 'w+') as f:
            example = {
                'EVIDENCE': evidence_item,
                'GENE': gene,
                'VARIANT': variant,
                'ASSERTIONS': assertions
            }

            json.dump(example, f)


def create_variant_examples(data):
    """Create variant examples for BRAF600E, BCR-ABL Variant,
    TP53 Loss (of function), and EGFR Amplification.
    """
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


if __name__ == '__main__':
    c = CIViC()
    c.harvest()
    with open(f'{PROJECT_ROOT}/data/civic/civic_harvester.json', 'r') as f:
        civic_data = json.load(f)

    civic_ex_dir = PROJECT_ROOT / 'analysis' / 'civic' / 'examples'
    civic_ex_dir.mkdir(exist_ok=True, parents=True)

    create_evidence_examples(civic_data)
    create_variant_examples(civic_data)
