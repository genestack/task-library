# -*- coding: utf-8 -*-

"""
    Java ``ExternalDataBase`` object shadow
"""
import os
import pipes
import subprocess

from genestack import utils
from genestack.cla import get_tool, RUN
from genestack.core_files.genestack_file import File
from genestack.frontend_object import StorageUnit
from genestack.genestack_exceptions import GenestackException
from genestack.java import java_object, JAVA_HASH_MAP, JAVA_LIST


class ExternalDatabase(File):
    """
    This class represents an external database file.
    """

    INTERFACE_NAME = 'com.genestack.bio.files.IExternalDataBase'

    DATA_LOCATION = 'genestack.location:data'
    INDEX_LOCATION = 'genestack.location:index'
    TABIX_LOCATION = 'genestack.location:tabix'
    SCHEMA_LOCATION = 'genestack.location:schema'

    SCHEMA_KEY = 'genestack:database.schema'

    def __init__(self, file_id=None):
        super(ExternalDatabase, self).__init__(file_id=file_id)
        self.annotations_map = None
        self.metainfo = self.get_metainfo()

    def lookup_annotations(self, queries_list):
        """
        Extracts annotations from variation database by specified contigs and positions.

        :param queries_list: list of tuples (contig, position_from, position_to)
        :return:
        """
        def __create_genome_interval(contig, position_from, position_to):
            return java_object('com.genestack.bio.files.GenomeInterval', {
                'contigName': contig,
                'from': position_from,
                'to': position_to
            })

        intervals_list = []
        for query_contig, query_from, query_to in queries_list:
            intervals_list.append(__create_genome_interval(query_contig, query_from, query_to))

        genome_query = java_object('com.genestack.bio.files.GenomeQuery', {
            'requestedArea': java_object(JAVA_HASH_MAP, {
                'intervals': java_object(JAVA_LIST, intervals_list)
            })
        })

        return self.invoke(
            'getAnnotations',
            types=['com.genestack.bio.files.GenomeQuery'],
            values=[genome_query]
        )

    def get_typed_key(self, a_key):
        if self.annotations_map is None:
            self.annotations_map = {}
            annotations = self.metainfo.get(ExternalDatabase.SCHEMA_KEY).get('value').split(';')
            for annotation in annotations:
                annotation_parts = annotation.split('=')
                if len(annotation_parts) != 2:
                    raise GenestackException('Broken annotation: ' + annotation)
                self.annotations_map[annotation_parts[0]] = annotation_parts[1]
        return self.annotations_map.get(a_key)

    def get_available_info(self):
        """
        Returns the list of available annotations.
        Each annotation is a dict with the following keys: 'id', 'description', 'type',  and  'valuesNumber'.

        :return: list of annotations
        :rtype: list[dict]
        """
        return self.invoke('getAvailableInfo')

    def put_data_with_index(self, path, schema):
        """
        PUTs and indexes the given variation database file.

        :param path: path to the variation database file
        :type path: str
        :param schema: path to the xml with field descriptions
        :type schema: str
        :rtype: None
        """
        compressed_data_file = self.__create_compressed_data_file(path)
        tabix = self.__create_tabix(compressed_data_file)
        num_of_variants = self.__get_number_of_variants(path)
        index = self.__create_index(path, num_of_variants, schema)

        self.__put(self.DATA_LOCATION, compressed_data_file)
        self.__put(self.TABIX_LOCATION, tabix)
        self.__put(self.INDEX_LOCATION, index)
        self.__put(self.SCHEMA_LOCATION, schema)

    def __put(self, key, path):
        self.PUT(key, StorageUnit(path))

    def __create_compressed_data_file(self, data_file_path):
        """
        Creates an archive that contains the given variation database file using BGZIP compression.

        :param data_file_path: path to the variation database file
        :type data_file_path: str
        :return: path to the compressed archive
        :rtype: str
        """
        compressed_file = data_file_path + '.bgz'
        bgzip = get_tool('bcftools', 'bgzip')
        bgzip['-c', data_file_path] & RUN(stdout=compressed_file)
        return compressed_file

    def __create_tabix(self, data_file_path):
        """
        Creates the TABIX index for the given variation database file.
        NOTE: file MUST be compressed using BGZIP compression!

        :param data_file_path: path to the compressed variation database file
        :type data_file_path: str
        :return: path to the built index
        :rtype: str
        """
        tabix = get_tool('bcftools', 'tabix')
        tabix['-s', '1', '-b', '2', '-e', '2', data_file_path] & RUN
        return data_file_path + '.tbi'

    @staticmethod
    def __get_number_of_variants(data_file_path):
        cmd_line = "grep -v '^#' %s | wc -l" % pipes.quote(data_file_path)
        line_count = subprocess.check_output([cmd_line], shell=True)
        return int(line_count)

    @staticmethod
    def __create_index(data_file_path, num_of_variants, schema):
        """
        Indexes the given variation database file to enable feature searching.
        NOTE: file MUST be compressed using BGZIP compression!

        :param data_file_path: path to the compressed variation database file
        :type data_file_path: str
        :return: path to the index archive
        :rtype: str
        """
        indexer = utils.get_java_tool('genestack-variationdb-indexer')
        index_folder = os.path.join(os.path.dirname(data_file_path), data_file_path + '.index')

        cmd_args = [
            indexer,
            '-d', index_folder,
            '-n', str(num_of_variants),
            '-s', schema,
            data_file_path
        ]
        utils.run_java_tool(indexer, *cmd_args)

        # compress the index folder as a single ZIP archive
        archive_name = index_folder + '.zip'
        subprocess.check_call(['zip', '-rjq', archive_name, index_folder])

        return archive_name
