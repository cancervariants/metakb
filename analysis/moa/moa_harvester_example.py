"""Create an example json file for MOAlmanac Harvester."""
from metakb.harvesters import MOAlmanac
from metakb import PROJECT_ROOT
import json


def create_assertion_examples(data):
    """Create five MOAlmanac assertion examples."""
    assertions = []
    for i in range(5):
        if data['assertions'][i]['source_ids']:
            assertions.append(data['assertions'][i])

    for assertion in assertions:
        source_id = assertion['source_ids'][0]
        for s in data['sourceOfevidence']:
            if s['id'] == source_id:
                source_item = s

        feature_id = assertion['feature_ids'][0]
        for v in data['variants']:
            if v['feature_id'] == feature_id:
                variant = v

        for key, val in variant.items():
            if key.startswith('gene'):
                gene_name = val
        for g in data['genes']:
            if g['name'] == gene_name:
                gene = g

        with open(f"{PROJECT_ROOT}/analysis/moa/examples/"
                  f"assertion {assertion['id']}.json", 'w+') as f:
            example = {
                'ASSERTIONS': assertion,
                'SOURCE_of_EVIDENCE': source_item,
                'GENE': gene,
                'VARIANT': variant
            }

            json.dump(example, f)
            print(f"Created JSON for evidence: assertion {assertion['id']}")
            f.close()


def create_variant_examples(data):
    """Create variant examples for BRAF600E, BCR-ABL Variant,
    TP53 (Nonsense), and EGFR Amplification.
    """
    variants_ids = [1, 147, 550, 699]
    variants = []
    for i in range(len(data['variants'])):
        if data['variants'][i]['feature_id'] in variants_ids:
            variants.append(data['variants'][i])
    for variant in variants:
        with open(f"{PROJECT_ROOT}/analysis/moa/examples/"
                  f"{variant['feature'].lower()}.json", 'w+') as f:
            f.write(json.dumps(variant))
            print(f"Created JSON for variant: {variant['feature']}")
            f.close()


if __name__ == '__main__':
    moa = MOAlmanac()
    moa.harvest()
    with open(f'{PROJECT_ROOT}/data/moa/moa_harvester.json', 'r') as f:
        moa_data = json.load(f)
    moa_ex_dir = PROJECT_ROOT / 'analysis' / 'moa' / 'examples'
    moa_ex_dir.mkdir(exist_ok=True, parents=True)
    create_assertion_examples(moa_data)
    create_variant_examples(moa_data)
