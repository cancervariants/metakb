"""Create example json files from the PMKB harvester."""
import json
from metakb.harvesters import PMKB
from metakb import PROJECT_ROOT
from random import choice


def create_interpretation_examples(interpretations, output_dir):
    """Create some PMKB interp examples."""
    for _ in range(3):
        interp = choice(interpretations)
        filename = output_dir / f"{interp['description'][:10].strip()}.json"
        with open(filename, 'w+') as f:
            f.write(json.dumps(interp))


def create_variant_examples(variants, output_dir):
    """Create examples of selected PMKB variant objects:
    * BRAF V600E
    * TP53 G245C
    * EGFR A763_Y764insFQEA
    """
    labels = ('BRAF V600E', 'TP53 G245C', 'EGFR A763_Y764insFQEA')
    for variant in variants:
        if variant['name'] in labels:
            filename = output_dir / f"{variant['name'].lower()}.json"
            with open(filename, 'w+') as f:
                f.write(json.dumps(variant))


if __name__ == '__main__':
    pmkb = PMKB()
    pmkb.harvest()
    with open(PROJECT_ROOT / 'data' / 'pmkb' / 'pmkb_harvester.json', 'r') as f:  # noqa: E501
        pmkb_data = json.load(f)

    output_dir = PROJECT_ROOT / 'analysis' / 'pmkb' / 'examples' / 'harvester'
    output_dir.mkdir(exist_ok=True, parents=True)

    create_interpretation_examples(pmkb_data['interpretations'], output_dir)
    create_variant_examples(pmkb_data['variants'], output_dir)
