"""Helper script to process and format output of transformation logs."""
from metakb import PROJECT_ROOT
from collections import Counter
import re

failures_file = open(PROJECT_ROOT / 'analysis' / 'graph' / 'normalization_failures.txt')  # noqa: E501
unsupported_variants_civic = []
unsupported_variants_hgvs = []
unsupported_msg = 'variant-normalizer does not support '
unsupported_msg_2 = 'not supported in variant-normalizer.'
missing_variants = []
variant_re = r'Variant (.*?) could not be found in variant normalizer.'
missing_therapies = []
therapy_re = r'Therapy (.*?) could not be found in therapy normalizer.'
therapy_re_2 = r'(.*?) not found in Therapy Normalization normalize'
missing_diseases = []
disease_re = r'Disease (.*?) could not be found in disease normalizer.'
no_ncit_disease = []
no_ncit_disease_re = r'Could not find NCIt ID using Disease Normalization for (.*?) and (.*?)\.'  # noqa: E501


for line in failures_file:
    msg = line.split('WARNING : ')[1][:-1]
    if msg.startswith(unsupported_msg):
        unsupported_variants_civic.append(msg[:-1].split(unsupported_msg)[1])
    elif msg.endswith(unsupported_msg_2):
        unsupported_variants_hgvs.append(msg.split(' ', 1)[0])
    elif "does not have exactly one" in msg or 'has null DOID' in msg:
        continue
    elif "could not be found" in msg:
        if msg.startswith('Variant'):
            missing_variants.append(re.search(variant_re, msg).group(1))
        elif msg.startswith('Therapy'):
            missing_therapies.append(re.search(therapy_re, msg).group(1))
        elif msg.startswith('Disease'):
            missing_diseases.append(re.search(disease_re, msg).group(1))
    elif 'not found in' in msg:
        if "Therapy Normalization" in msg:
            missing_therapies.append(re.search(therapy_re_2, msg).group(1))
        elif 'Disease Normalization' in msg:
            missing_diseases.append(msg.split(' not found in Disease Normalization')[0])  # noqa: E501
    elif msg.startswith("Could not find NCIt ID"):
        if 'Disease Normalization' in msg:
            groups = re.search(no_ncit_disease_re, msg)
            no_ncit_disease.append(f'{groups.group(1)}|{groups.group(2)}')
    else:
        # not captured properly
        print(msg)

unsupported_variants_civic_counts = Counter(unsupported_variants_civic).most_common()  # noqa: E501
unsupported_variants_hgvs_counts = Counter(unsupported_variants_hgvs).most_common()  # noqa: E501
missing_variants_counts = Counter(missing_variants).most_common()
missing_therapies_counts = Counter(missing_therapies).most_common()
missing_diseases_counts = Counter(missing_diseases).most_common()
no_ncit_disease_counts = Counter(no_ncit_disease).most_common()

file = open('unsupported_variants_civic_counts.txt', 'w')
for item in unsupported_variants_civic_counts:
    file.write(f'{item[0]}, {item[1]}\n')
file.close()
file = open('unsupported_variants_hgvs_counts.txt', 'w')
for item in unsupported_variants_hgvs_counts:
    file.write(f'{item[0]}, {item[1]}\n')
file.close()
file = open('missing_variants_counts.txt', 'w')
for item in missing_variants_counts:
    file.write(f'{item[0]}, {item[1]}\n')
file.close()
file = open('missing_therapies_counts.txt', 'w')
for item in missing_therapies_counts:
    file.write(f'{item[0]}, {item[1]}\n')
file.close()
file = open('missing_diseases_counts.txt', 'w')
for item in missing_diseases_counts:
    file.write(f'{item[0]}, {item[1]}\n')
file.close()
file = open('no_ncit_disease_counts.txt', 'w')
for item in no_ncit_disease_counts:
    file.write(f'{item[0].split("|")[0]}, {item[0].split("|")[1]},{item[1]}\n')
file.close()
