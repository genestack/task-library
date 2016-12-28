# -*- coding: utf-8 -*-
import os

from genestack.bio import bio_meta_keys
from genestack.bio.genome_query import GenomeQuery
from genestack.compression import decompress_file
from genestack.core_files.genestack_file import File
from genestack.genestack_exceptions import GenestackException
from genestack.metainfo import Metainfo
from genestack.utils import log_info


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

    # @Deprecated, use bio_meta_keys.REFERENCE_GENOME
    REFERENCE_GENOME = bio_meta_keys.REFERENCE_GENOME
    # @Deprecated, use bio_meta_keys.REFERENCE_GENOME
    REFERENCE_GENOME_KEY = REFERENCE_GENOME

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
            all_files = [decompress_file(f, working_dir) for f in all_files]
            log_info('Files are decompressed: %s\n' % ', '.join('"%s"' % x for x in all_files))
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
            annotation_file = decompress_file(annotation_file, working_dir)
            log_info('File is decompressed: "%s"\n' % os.path.relpath(annotation_file))
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
