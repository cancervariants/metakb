"""This module integration tests the civic harvester."""

import os

from metakb.downloaders.civic import DEFAULT_OUTPUT_DIR
from metakb.utils import ioutils


def test_creates_file():
    """Should create a file with 300+ lines."""
    path = os.path.join(DEFAULT_OUTPUT_DIR, 'civic.json.gz')
    assert os.path.isfile(path), 'Should create a file.'
    reader = ioutils.reader(path)
    num_lines = sum(1 for line in reader)
    assert num_lines > 300, 'There should be over 300 genes.'
