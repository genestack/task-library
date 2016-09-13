# -*- coding: utf-8 -*-
import os

from genestack import File
from genestack.compression import decompress_file
from genestack.metainfo import Metainfo
from genestack.utils import makedirs_p


class MicroarrayAssay(File):
    """
    This class represents a microarray assay.

    Required keys:
        - :py:attr:`~genestack.bio.MicroarrayAssay.DATA_LOCATION` - key to store the physical assay file.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IMicroarrayAssay'

    DATA_LOCATION = Metainfo.DATA_LOCATION

    def get_data_file(self, working_dir=None, decompressed=False):
        units = self.GET(self.DATA_LOCATION, working_dir=working_dir)
        data_file = units[0].get_first_file()
        if decompressed:
            return decompress_file(data_file, working_dir)
        return data_file

    def export(self, folder):
        # TODO Should we pack files if not compressed?
        if not os.path.exists(folder):
            makedirs_p(folder)
        return [self.get_data_file(working_dir=folder)]
