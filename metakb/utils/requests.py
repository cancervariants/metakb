"""Network utility."""
import os

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests_cache
import metakb.utils.ioutils as ioutils


def Client(cache_name, cache_directory="caches", retries=3, backoff_factor=0.3,
           status_forcelist=(500, 502, 504), session=None):
    """Client provides a requests session that is configured with automatic retries, caching, and more."""
    ioutils.ensure_directory(cache_directory)
    cache_path = os.path.join(cache_directory, cache_name)
    # TODO include rate limiting.
    session = session or requests_cache.CachedSession(cache_path)
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
