# -*- coding: utf-8 -*-

from genestack import File
from genestack.metainfo import Metainfo


class CodonTable(File):
    """
    This class represents a codon table file.

    Required keys:
        - :py:attr:`~genestack.bio.CodonTable.TABLE_LOCATION` - key to store the physical file with first two lines from codon table.

    Optional keys:
        - :py:attr:`~genestack.bio.CodonTable.DATA_LOCATION` - key to store the physical codon table file.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.ICodonTable'

    DATA_LOCATION = Metainfo.DATA_LOCATION
    TABLE_LOCATION = 'genestack.location:table'
