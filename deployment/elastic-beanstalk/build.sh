#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_ROOT="${PROJECT_ROOT}/build/elastic-beanstalk"
WHEEL_DIR="${BUILD_ROOT}/wheels"
BUNDLE_DIR="${BUILD_ROOT}/bundle"

cd "${PROJECT_ROOT}"

rm -rf "${BUILD_ROOT}"
mkdir -p "${WHEEL_DIR}" "${BUNDLE_DIR}/wheels"

# Fail early if the checkout does not contain Git metadata.
git rev-parse --is-inside-work-tree >/dev/null
git describe --tags --always

# Build the Python package while setuptools-scm can inspect Git.
python -m build \
  --wheel \
  --outdir "${WHEEL_DIR}" \
  server

wheel_path="$(find "${WHEEL_DIR}" -maxdepth 1 -name '*.whl' -print -quit)"

if [[ -z "${wheel_path}" ]]; then
  echo "No wheel was produced" >&2
  exit 1
fi

wheel_name="$(basename "${wheel_path}")"

cp "${wheel_path}" "${BUNDLE_DIR}/wheels/"

# Copy EB deployment configuration.
if [[ -d "${PROJECT_ROOT}/.ebextensions" ]]; then
  cp -R "${PROJECT_ROOT}/.ebextensions" "${BUNDLE_DIR}/"
fi

if [[ -d "${PROJECT_ROOT}/.platform" ]]; then
  cp -R "${PROJECT_ROOT}/.platform" "${BUNDLE_DIR}/"
fi

# Copy the application entrypoint and any other files EB needs.
cp "${PROJECT_ROOT}/application.py" "${BUNDLE_DIR}/"

# Generate the requirements file EB will install.
runtime_requirements="${PROJECT_ROOT}/deployment/elastic-beanstalk/requirements-runtime.txt"

if [[ -f "${runtime_requirements}" ]]; then
  cp "${runtime_requirements}" "${BUNDLE_DIR}/requirements.txt"
else
  : > "${BUNDLE_DIR}/requirements.txt"
fi

printf '\n./wheels/%s\n' "${wheel_name}" >> "${BUNDLE_DIR}/requirements.txt"

# Record deployment provenance for diagnostics.
git rev-parse HEAD > "${BUNDLE_DIR}/COMMIT_SHA"
python -m setuptools_scm > "${BUNDLE_DIR}/VERSION"

echo "Built Elastic Beanstalk bundle:"
echo "  ${BUNDLE_DIR}"
echo "  version: $(cat "${BUNDLE_DIR}/VERSION")"
echo "  commit:  $(cat "${BUNDLE_DIR}/COMMIT_SHA")"
