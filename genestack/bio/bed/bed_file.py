# -*- coding: utf-8 -*-

from genestack import File


class BED(File):
    """
    This class represents a BED file.

    - :py:attr:`~genestack.bio.BED.DATA_LOCATION` - key to store the physical BED file
    """
    INTERFACE_NAME = 'com.genestack.bio.files.genomedata.IGenomeBEDData'

    DATA_LOCATION = 'genestack.location:data'

    REFERENCE_GENOME_KEY = 'genestack.bio:referenceGenome'
    SOURCE_KEY = 'genestack.bio:sourceData'
