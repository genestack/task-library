# -*- coding: utf-8 -*-

from genestack import File
from genestack.metainfo import Metainfo


class RawFile(File):
    """
    Java RawFile class representation for python code
    """
    INTERFACE_NAME = 'com.genestack.api.files.IRawFile'
    DATA_LOCATION = Metainfo.DATA_LOCATION
