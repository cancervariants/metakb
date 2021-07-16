"""A module for MetaKB uploader"""
import biothings, config  # noqa: E401
biothings.config_for_app(config)

import biothings.hub.dataload.uploader  # noqa: E402

from .parser import load_statements as statements_parser  # noqa: E402
from .parser import load_propositions as propositions_parser  # noqa: E402
from .parser import load_variation_descriptors as v_des_parser  # noqa: E402
from .parser import load_gene_descriptors as g_des_parser  # noqa: E402
from .parser import load_therapy_descriptors as t_des_parser  # noqa: E402
from .parser import load_disease_descriptors as d_des_parser  # noqa: E402
from .parser import load_methods as methods_parser  # noqa: E402
from .parser import load_documents as docs_parser  # noqa: E402


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
        return {}


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


class VariationDescriptorsUploader(biothings.hub.dataload.uploader.BaseSourceUploader):  # noqa: E501
    """VariationDescriptorsUploader"""

    main_source = "metakb"
    name = "variant_descriptors"
    __metadata__ = {"src_meta": {}}
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        """Load data"""
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return v_des_parser(data_folder)

    @classmethod
    def get_mapping(klass):
        """Return Mapping"""
        return {}


class GeneDescriptorsUploader(biothings.hub.dataload.uploader.BaseSourceUploader):  # noqa: E501
    """GeneDescriptorsUploader"""

    main_source = "metakb"
    name = "gene_descriptors"
    __metadata__ = {"src_meta": {}}
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        """Load data"""
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return g_des_parser(data_folder)

    @classmethod
    def get_mapping(klass):
        """Return Mapping"""
        return {}


class TherapyDescriptorsUploader(biothings.hub.dataload.uploader.BaseSourceUploader):  # noqa: E501
    """TherapyDescriptorsUploader"""

    main_source = "metakb"
    name = "therapy_descriptors"
    __metadata__ = {"src_meta": {}}
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        """Load data"""
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return t_des_parser(data_folder)

    @classmethod
    def get_mapping(klass):
        """Return Mapping"""
        return {}


class DiseaseDescriptorsUploader(biothings.hub.dataload.uploader.BaseSourceUploader):  # noqa: E501
    """DiseaseDescriptorsUploader"""

    main_source = "metakb"
    name = "disease_descriptors"
    __metadata__ = {"src_meta": {}}
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        """Load data"""
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return d_des_parser(data_folder)

    @classmethod
    def get_mapping(klass):
        """Return Mapping"""
        return {}


class MethodsUploader(biothings.hub.dataload.uploader.BaseSourceUploader):
    """MethodsUploader"""

    main_source = "metakb"
    name = "methods"
    __metadata__ = {"src_meta": {}}
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        """Load data"""
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return methods_parser(data_folder)

    @classmethod
    def get_mapping(klass):
        """Return Mapping"""
        return {}


class DocumentsUploader(biothings.hub.dataload.uploader.BaseSourceUploader):
    """DocumentsUploader"""

    main_source = "metakb"
    name = "documents"
    __metadata__ = {"src_meta": {}}
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        """Load data"""
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return docs_parser(data_folder)

    @classmethod
    def get_mapping(klass):
        """Return Mapping"""
        return {}
