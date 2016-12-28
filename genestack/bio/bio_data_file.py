# -*- coding: utf-8 -*-

from genestack.bio import bio_meta_keys
from genestack.core_files.genestack_file import File
from genestack.metainfo import Metainfo


# TODO remove this class after removing it s usages in bio-applications
class BioDataFile(File):
    REFERENCE_GENOME = bio_meta_keys.REFERENCE_GENOME
    # @Deprecated, use REFERENCE_GENOME
    REFERENCE_GENOME_KEY = REFERENCE_GENOME
    SOURCE_KEY = Metainfo.SOURCE_DATA_KEY
