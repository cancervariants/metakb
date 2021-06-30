"""A module for MetaKB dumper"""
import os

import biothings, config  # noqa: E401
biothings.config_for_app(config)
from config import DATA_ARCHIVE_ROOT  # noqa: E402

from biothings.utils.common import uncompressall  # noqa: E402

import biothings.hub.dataload.dumper  # noqa: E402


class MetakbDumper(biothings.hub.dataload.dumper.LastModifiedHTTPDumper):
    """Dumper for MOA"""

    SRC_NAME = "metakb"
    SRC_ROOT_FOLDER = os.path.join(DATA_ARCHIVE_ROOT, SRC_NAME)
    SCHEDULE = None
    UNCOMPRESS = False
    SRC_URLS = ['https://metakb-biothings.s3.amazonaws.com/moa_cdmtest.json']
    __metadata__ = {"src_meta": {}}

    def post_dump(self, *args, **kwargs):
        """If UNCOMPRESS = True, uncompress the file"""
        if self.__class__.UNCOMPRESS:
            self.logger.info("Uncompress all archive files in '%s'" %
                             self.new_data_folder)
            uncompressall(self.new_data_folder)
