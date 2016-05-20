# -*- coding: utf-8 -*-

"""
    Java ``ExternalDataBase`` object shadow
"""

from genestack.java import java_object, JAVA_HASH_MAP, JAVA_LIST
from genestack import GenestackException, File


class ExternalDatabase(File):
    """
    This class represents an external database file.
    """

    INTERFACE_NAME = 'com.genestack.bio.files.IExternalDataBase'

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
