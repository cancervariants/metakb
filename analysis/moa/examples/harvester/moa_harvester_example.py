"""Create an example json file for MOAlmanac Harvester."""
import json

from metakb import PROJECT_ROOT, APP_ROOT
from metakb.harvesters import MOAHarvester


def create_assertion_examples(data):
    """Create five MOAlmanac assertion examples."""
    assertions = []
    for i in [0, 69, 599, 699, 759]:
        if data['assertions'][i]['source_ids']:
            assertions.append(data['assertions'][i])

    for assertion in assertions:
        source_id = assertion['source_ids']
        for s in data['sources']:
            if s['id'] == source_id:
                source = s
                break

        feature_id = assertion['variant']['id']
        for v in data['variants']:
            if v['id'] == feature_id:
                variant = v
                break

        with open(f"{PROJECT_ROOT}/analysis/moa/examples/harvester/"
                  f"assertion {assertion['id']}.json", 'w+') as f:
            example = {
                'ASSERTIONS': assertion,
                'SOURCES': source,
                'VARIANTS': variant
            }

            json.dump(example, f, indent=4)
            print(f"Created JSON for evidence: assertion {assertion['id']}")
            f.close()


def create_variant_examples(data):
    """Create variant examples for BRAF600E, BCR-ABL Variant,
    TP53 (Nonsense), and EGFR Amplification.
    """
    variants_ids = [1, 147, 551, 701]
    variants = []
    for i in range(len(data['variants'])):
        if data['variants'][i]['id'] in variants_ids:
            variants.append(data['variants'][i])
    for variant in variants:
        with open(f"{PROJECT_ROOT}/analysis/moa/examples/harvester/"
                  f"{variant['feature'].lower()}.json", 'w+') as f:
            f.write(json.dumps(variant, indent=4))
            print(f"Created JSON for variant: {variant['feature']}")
            f.close()


if __name__ == '__main__':
    moa = MOAHarvester()
    moa.harvest()
    latest = sorted((APP_ROOT / "data" / "moa" / "harvester").glob("moa_harvester_*.json"))[-1]  # noqa: E501
    with open(latest, "r") as f:
        moa_data = json.load(f)
    moa_ex_dir = PROJECT_ROOT / 'analysis' / 'moa' / 'examples'
    moa_ex_dir.mkdir(exist_ok=True, parents=True)
    create_assertion_examples(moa_data)
    create_variant_examples(moa_data)
