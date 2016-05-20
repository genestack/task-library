# -*- coding: utf-8 -*-

from genestack import File


# TODO remove this class after removing it s usages in bio-applications
class BioDataFile(File):
    REFERENCE_GENOME_KEY = 'genestack.bio:referenceGenome'
    SOURCE_KEY = 'genestack.bio:sourceData'
