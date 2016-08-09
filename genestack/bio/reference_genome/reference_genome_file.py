# -*- coding: utf-8 -*-

from genestack.bio.genome_query import GenomeQuery
from genestack import File, GenestackException
from genestack.compression import decompress_file
from genestack.metainfo import Metainfo


class ReferenceGenome(File):
    """
    This class represents a reference genome file.

    Required keys:
        - :py:attr:`~genestack.bio.BED.SEQUENCE_LOCATION` - key to store sequencing files.
          One ore more fasta files each with one or more contigs can be stored here.
        - :py:attr:`~genestack.bio.BED.ANNOTATIONS_LOCATION` - key to store GTF annotation.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IReferenceGenome'

    SEQUENCE_LOCATION = 'genestack.location:sequence'
    ANNOTATIONS_LOCATION = 'genestack.location:annotations'

    REFERENCE_GENOME_KEY = 'genestack.bio:referenceGenome'
    SOURCE_KEY = Metainfo.SOURCE_DATA_KEY

    def get_sequence_files(self, working_dir=None, decompressed=False):
        """
        GET sequence files from storage, returns list of their paths.

        :param working_dir: directory to copy files, default is current working directory
        :type working_dir: str
        :param decompressed: whether files should be decompressed after downloading
        :type decompressed: bool
        :rtype: list[str]
        """
        units = self.GET(self.SEQUENCE_LOCATION, working_dir=working_dir)
        all_files = [p for x in units for p in x.files]
        if decompressed:
            return [decompress_file(f, working_dir) for f in all_files]
        return all_files

    def get_annotation_file(self, working_dir=None, decompressed=False):
        """
        GET annotation file from storage, returns its path.

        :param working_dir: directory to copy files, default is current working directory
        :type working_dir: str
        :param decompressed: whether files should be decompressed after downloading
        :type decompressed: bool
        :rtype: str
        """
        units = self.GET(self.ANNOTATIONS_LOCATION, working_dir=working_dir)
        annotation_file = units[0].get_first_file()
        if decompressed:
            return decompress_file(annotation_file, working_dir)
        return annotation_file

    def get_contigs(self):
        """
        Returns map from contig names into their lengths.

        :return: map: contigName -> contigLength
        :rtype: dict[str, int]
        """
        return self.invoke('getContigs')

    def find_features(self, query):
        """
        Return features matching query.

        Response has following keys:
          - features: list of features (could be incomplete)
          - total: total number of matched features

        :param query: query
        :type query: genestack.bio.GenomeQuery
        :return:  GenomeSearchResponse as dictionary
        :rtype: dict[str, object]
        """

        if not isinstance(query, GenomeQuery):
            raise GenestackException(
                'Query is not of type GenomeQuery: %s' % type(query)
            )
        return self.invoke(
            'findFeatures',
            types=['com.genestack.bio.files.GenomeQuery'],
            values=[query.get_java_object()]
        )
