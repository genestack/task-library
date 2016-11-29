# -*- coding: utf-8 -*-

from genestack import File, StorageUnit
from genestack.compression import gzip_file
from genestack.metainfo import Metainfo


class MappedReadsCounts(File):
    """
    This class represents a mapped reads count.

    Required keys:
        - :py:attr:`~genestack.bio.MappedReadsCounts.DATA_LOCATION` - key to store the physical file with mapped reads count.

    To put data to this key you can use :py:meth:`~genestack.bio.MappedReadsCounts.put_counts`.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IHTSeqCounts'

    DATA_LOCATION = Metainfo.DATA_LOCATION
    LOCATION_DATA = DATA_LOCATION  # deprecated, use DATA_LOCATION instead

    SOURCE_KEY = Metainfo.SOURCE_DATA_KEY

    def get_counts(self, working_dir=None):
        storage_units = self.GET(self.DATA_LOCATION, working_dir=working_dir)
        return storage_units[0].get_first_file()

    def put_counts(self, path):
        self.PUT(self.DATA_LOCATION, StorageUnit(gzip_file(path, remove_source=False)))
