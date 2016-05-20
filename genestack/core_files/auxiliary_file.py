# -*- coding: utf-8 -*-

"""
    java AuxiliaryFile object shadow
"""

from genestack import File


# TODO: Do we need this class only as constant container?
# We can move constants to module scope or not inherit it from File
# AUXILIARY_FILE_KEY_MASTER_FILE = 'genestack:master'
# AUXILIARY_FILE_KEY_DATA_LOCATION = 'genestack.location:data'  # same value used as constant in other places
# AUXILIARY_FILE_KEY_CLASS_NAME = 'com.genestack.api.files.IAuxiliaryFile'  # never used
class AuxiliaryFile(File):
    DATA_LOCATION = 'genestack.location:data'
    MASTER_FILE = 'genestack:master'
    INTERFACE_NAME = 'com.genestack.api.files.IAuxiliaryFile'
