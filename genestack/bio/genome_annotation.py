# -*- coding: utf-8 -*-

from genestack import File
from genestack.metainfo import Metainfo


class GenomeAnnotation(File):
    """
    This class represents a genome annotation file.

    Required keys:
        - :py:attr:`~genestack.bio.GenomeAnnotation.ANNOTATION_LOCATION` - key to store  the physicalfile with genome annotation.
        - :py:attr:`~genestack.bio.GenomeAnnotation.ANNOTATION_GENES_INDEX_LOCATION` - key that stores the physical
          index file for genome annotation.
    """

    INTERFACE_NAME = 'com.genestack.bio.files.IGenomeAnnotations'

    ANNOTATION_LOCATION = Metainfo.DATA_LOCATION
    ANNOTATION_GENES_INDEX_LOCATION = "genestack.location:gene_index"
