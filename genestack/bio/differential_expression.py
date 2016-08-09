# -*- coding: utf-8 -*-

from genestack import File, StorageUnit
from genestack.metainfo import Metainfo


class DifferentialExpression(File):
    """
    This class represents a Differential Expression file.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.differentialExpression.IDifferentialExpressionFile'

    SOURCE_KEY = Metainfo.SOURCE_DATA_KEY

    def put_result(self, path):
        """
        PUT result file to storage.

        :param path: path to result file
        :type path: str
        :return:
        """
        self.PUT(Metainfo.DATA_LOCATION, StorageUnit(path))

    def get_result(self, working_dir=None):
        """
        GET result file from storage.

        :param working_dir: directory to copy files into, default is current directory
        :type working_dir: str
        :return:
        """
        return self.GET(Metainfo.DATA_LOCATION, working_dir=working_dir)
