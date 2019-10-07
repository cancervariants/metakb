"""This module tests requests cache."""

import os
import contextlib
from metakb.utils.requests import Client
import time


def test_creates_cachefile():
    """Should create a directory with a cache file."""
    path = 'caches/drug_enricher.sqlite'
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)
    requests = Client('drug_enricher')
    requests.get('https://google.com')
    assert os.path.isfile(path), 'Should have created new directory {}'.format(path)


def test_faster():
    """Should be faster than uncached."""
    path = 'caches/drug_enricher.sqlite'
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)

    requests = Client('drug_enricher')
    start = time.time()
    requests.get('https://google.com')
    end = time.time()
    elapsed_no_cache = end - start

    start = time.time()
    requests.get('https://google.com')
    end = time.time()
    elapsed_cache = end - start

    assert elapsed_cache < elapsed_no_cache, "cache should be faster"
