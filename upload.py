"""A module for MetaKB uploader"""
import biothings, config  # noqa: E401
biothings.config_for_app(config)

import biothings.hub.dataload.uploader  # noqa: E402

# when code is exported, import becomes relative
try:
    from metakb.parser import load_statements as statements_parser
    from metakb.parser import load_propositions as propositions_parser
except ImportError:
    from .parser import load_statements as statements_parser
    from .parser import load_propositions as propositions_parser


class StatementsUploader(biothings.hub.dataload.uploader.BaseSourceUploader):
    """StatementsUploader"""

    main_source = "metakb"
    name = "statements"
    __metadata__ = {"src_meta": {}}
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        """Load data"""
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return statements_parser(data_folder)

    @classmethod
    def get_mapping(klass):
        """Return Mapping."""
        return {
            'statements': {
                'properties': {
                    'description': {
                        'type': 'text'
                    },
                    'disease_descriptor': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'evidence_level': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'id': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'method': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'proposition': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'supported_by': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'therapy_descriptor': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'type': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'variation_descriptor': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    },
                    'variation_origin': {
                        'normalizer': 'keyword_lowercase_normalizer',
                        'type': 'keyword'
                    }
                }
            }
        }


class PropositionsUploader(biothings.hub.dataload.uploader.BaseSourceUploader):
    """PropositionsUploader"""

    main_source = "metakb"
    name = "propositions"
    __metadata__ = {"src_meta": {}}
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        """Load data"""
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return propositions_parser(data_folder)

    @classmethod
    def get_mapping(klass):
        """Return Mapping"""
        return {}
