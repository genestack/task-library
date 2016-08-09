# -*- coding: utf-8 -*-

from genestack import File
from genestack.bio.bed.bed_indexer import BEDIndexer
from genestack.metainfo import Metainfo


class BED(File):
    """
    This class represents a BED file.

    - :py:attr:`~genestack.bio.BED.DATA_LOCATION` - key to store the physical BED file
    """
    INTERFACE_NAME = 'com.genestack.bio.files.genomedata.IGenomeBEDData'

    DATA_LOCATION = Metainfo.DATA_LOCATION

    REFERENCE_GENOME_KEY = 'genestack.bio:referenceGenome'
    SOURCE_KEY = Metainfo.SOURCE_DATA_KEY

    def put_with_index(self, path):
        """
        PUT bed file to storage and create index for it.

        :param path: path to bed file
        :param path: str
        :return: None
        """
        indexer = BEDIndexer(self)
        indexer.create_index(path)

    def get_bed(self, working_dir=None):
        """
        Return bed source file.

        :param working_dir: directory to copy files into, default is current directory
        :type working_dir: str
        :return: None
        """
        return self.GET(BED.DATA_LOCATION, working_dir=working_dir)[0].get_first_file()
