"""Module for the VICC Normalizers."""
import requests


class Normalizers:
    """Class for accessing VICC Normalizers."""

    def __init__(self):
        """Initialize the Normalizers."""
        self.normalize_url = "https://normalize.cancervariants.org/"

    def search(self, normalizer, query):
        """Return json from normalizer search endpoint.

        :param str normalizer: The normalizer to use (gene, therapy)
        :param str query: The string to query
        """
        r = requests.get(f"{self.normalize_url}/{normalizer}/search?q={query}")
        return r.json()
