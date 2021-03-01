"""Module for the VICC Normalizers."""
import requests


class Normalizers:
    """Class for accessing VICC Normalizers."""

    def __init__(self):
        """Initialize the Normalizers."""
        self.normalize_url = "https://normalize.cancervariants.org/"

    def search(self, normalizer, query, keyed=False, incl='', excl=''):
        """Return json from normalizer search endpoint.

        :param str normalizer: The normalizer to use (gene, therapy)
        :param str query: The string to query
        :param boolean keyed: If true, return response as key-value pairs
            of sources to source matches.
        :param str incl: Comma-separated list of source names to include
            in response.
        :param str excl: Comma-separated list of source names to exclude
            in response.
        :return: JSON response for query
        """
        normalizer = normalizer.lower()
        if normalizer not in ['therapy', 'gene', 'disease']:
            raise Exception('Not a normalizer.')
        if not incl and not excl:
            r = requests.get(f"{self.normalize_url}/{normalizer}/search?"
                             f"q={query}&keyed={keyed}")
        elif incl and not excl:
            r = requests.get(f"{self.normalize_url}/{normalizer}/search?"
                             f"q={query}&keyed={keyed}&incl={incl}")
        elif excl and not incl:
            r = requests.get(f"{self.normalize_url}/{normalizer}/search?"
                             f"q={query}&keyed={keyed}&excl={excl}")
        else:
            raise Exception('Cannot have both incl and excl.')
        return r.json()

    def normalize(self, normalizer, query):
        """Return json from normalizer normalize endpoint.

        :param str normalizer: The normalizer to use (gene, therapy)
        :param str query: The string to query
        :return: JSON response for query
        """
        r = requests.get(f"{self.normalize_url}/{normalizer}"
                         f"/normalize?q={query}")
        return r.json()

    def tovrs(self, query):
        """Return json from variant normalization toVRS endpoint.

        :param query: variant to translate to VRS representation.
        :return: JSON response for query
        """
        r = requests.get(f"{self.normalize_url}/variant/toVRS?q={query}")
        return r.json()
