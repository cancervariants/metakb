#!/usr/bin/env bash
# This file:
#
#  - Retrieves all genes from civi
#
# Usage:
#
#  - harvest_civic   # by default writes to source/civic/civic.json.gz
#

# Exit on error. Append "|| true" if you expect an error.
set -o errexit
# Exit on error inside any functions or subshells.
set -o errtrace
# Do not allow use of undefined vars. Use ${VAR:-} to use an undefined VAR
set -o nounset
# Catch the error in case mysqldump fails (but gzip succeeds) in `mysqldump |gzip`
set -o pipefail
# Turn on traces, useful while debugging but commented out by default
# set -o xtrace

python3 -m metakb.downloaders.civic
python3 -m pytest tests/integration/downloaders/test_civic.py
