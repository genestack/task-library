# -*- coding: utf-8 -*-

from genestack import File
from genestack.metainfo import Metainfo


class WIG(File):
    """
    This class represents a WIG file.

    Required keys:
        - :py:attr:`~genestack.bio.WIG.WIG_SOURCE_LOCATION` - key to store the physical wiggle file.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.genomedata.IGenomeWiggleData'

    WIG_SOURCE_LOCATION = Metainfo.DATA_LOCATION

