# -*- coding: utf-8 -*-

from genestack.core_files.genestack_file import File
from genestack.frontend_object import StorageUnit
from genestack.metainfo import Metainfo


class DifferentialExpression(File):
    """
    This class represents a Differential Expression file.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.differentialExpression.IDifferentialExpressionFile'

    # @Deprecated, use Metainfo.SOURCE_DATA
    # Deprecated in 0.44.0, will be removed in 0.47.0
    SOURCE_KEY = Metainfo.SOURCE_DATA
    DATA_LOCATION = 'genestack.location:data'

    def put_result(self, path):
        """
        PUT result file to storage.

        :param path: path to result file
        :type path: str
        :return:
        """
        self.PUT(self.DATA_LOCATION, StorageUnit(path))

    def get_result(self, working_dir=None):
        """
        GET result file from storage.

        :param working_dir: directory to copy files into, default is current directory
        :type working_dir: str
        :return:
        """
        return self.GET(self.DATA_LOCATION, working_dir=working_dir)
