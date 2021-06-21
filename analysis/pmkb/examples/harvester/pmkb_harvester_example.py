"""Create example json files from the PMKB harvester."""
import json
from metakb.harvesters import PMKB
from metakb import PROJECT_ROOT


def create_interpretation_examples(interpretations, output_dir):
    """Create some PMKB interp examples."""
    descr1 = 'CDKN2A gene functions as an important tumor suppressor via induction of cell growth arrest and senescence. Majority of the CDKN2A'  # noqa: E501
    descr2 = 'SMAD4 is tumor suppressor gene and it encodes an intracellular mediator in the transforming growth factor b (TGF b) signal transduction'  # noqa: E501
    for interp in interpretations:
        if interp['description'].startswith(descr1) or \
                interp['description'].startswith(descr2):
            filename = output_dir / f"{interp['description'][:10].strip()}.json"  # noqa: E501
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
