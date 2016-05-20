# -*- coding: utf-8 -*-

from genestack import File


class RawFile(File):
    """
    Java RawFile class representation for python code
    """
    INTERFACE_NAME = 'com.genestack.api.files.IRawFile'
    DATA_LOCATION = 'genestack.location:data'
