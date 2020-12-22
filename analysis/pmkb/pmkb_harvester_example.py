"""Create an example json file using the PMKB Harvester."""
import json
from metakb.harvesters import PMKB
from metakb import PROJECT_ROOT


def create_evidence_examples(data):
    """Create five PMBK evidence examples."""
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

        with open(f"{PROJECT_ROOT}/analysis/civic/examples/"
                  f"{evidence_item['name']}.json", 'w+') as f:
            example = {
                'EVIDENCE': evidence_item,
                'GENE': gene,
                'VARIANT': variant,
                'ASSERTIONS': assertions
            }

            json.dump(example, f)
            print(f"Created JSON for evidence: {evidence_item['name']}")
            f.close()


def create_variant_examples(data):
    """Create example variant docs for a selection of sample variants:
    * `ABL1 any mutation`
    * `BRAF V600E`
    * `IDH1 R132L`
    * `FGFR3 F384L`
    """
    variant_names = ['ABL1 any mutation', 'BRAF V600E', 'IDH1 R132L',
                     'FGFR3 F384L']
    variants = list()
    for i in range(len(data['variants'])):
        if data['variants'][i]['id'] in variant_names:
            variants.append(data['variants'][i])

    for variant in variants:
        outdir = PROJECT_ROOT / 'analysis' / 'pmkb' /\
            f"{variant['name'].lower()}.json"
        with open(outdir, 'w+') as f:
            variant['evidence_items'] = variant['evidence_items'][0]
            f.write(json.dumps(variant))
            print(f"Created JSON for variant: {variant['name']}")
            f.close()


if __name__ == '__main__':
    pmkb = PMKB()
    pmkb.harvest()
    with open(f'{PROJECT_ROOT}/data/pmkb/pmkb_harvester.json', 'r') as f:
        pmkb_data = json.load(f)
    create_evidence_examples(pmkb_data)
    create_variant_examples(pmkb_data)
