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
        assertion = evidence_item['assertions'][0]
        variants = assertion['variants']
        gene = assertion['gene']

        variants_out = list()
        for v in data['variants']:
            if v['name'] in [variant['name'] for variant in variants]:
                variants_out.append(v)

        for g in data['genes']:
            if g['name'] == gene['name']:
                gene_out = g
                break

        out_dir = PROJECT_ROOT / 'analysis' / 'pmkb' / 'examples'
        out_dir.mkdir(parents=True, exist_ok=True)
        name = assertion['description'][:12]
        with open(out_dir / f"{name}.json", 'w+') as f:
            example = {
                'EVIDENCE': evidence_item,
                'GENE': gene_out,
                'VARIANTS': variants_out,
                'ASSERTION': assertion,
            }

            json.dump(example, f)
        print(f"Created JSON for evidence: {name}")


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
        if data['variants'][i]['name'] in variant_names:
            variants.append(data['variants'][i])

    for variant in variants:
        outpath = PROJECT_ROOT / 'analysis' / 'pmkb' / 'examples' / \
            f"{variant['name'].lower()}.json"
        with open(outpath, 'w+') as f:
            json.dump(variant, f)
        print(f"Created JSON for variant: {variant['name']}")


if __name__ == '__main__':
    pmkb = PMKB()
    pmkb.harvest()
    with open(f'{PROJECT_ROOT}/data/pmkb/pmkb_harvester.json', 'r') as f:
        pmkb_data = json.load(f)
    create_evidence_examples(pmkb_data)
    create_variant_examples(pmkb_data)
