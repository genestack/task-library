# -*- coding: utf-8 -*-

from genestack.bio import bio_meta_keys
from genestack.core_files.genestack_file import File
from genestack.metainfo import Metainfo


# TODO remove this class after removing it s usages in bio-applications
class BioDataFile(File):
    # @Deprecated, use Metainfo.SOURCE_DATA
    # Deprecated in 0.44.0, will be removed in 0.47.0
    SOURCE_KEY = Metainfo.SOURCE_DATA
