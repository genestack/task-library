# -*- coding: utf-8 -*-

from genestack import File, GenestackException, StorageUnit
from genestack.compression import gzip_file, decompress_file
from genestack.query_range import QueryRange
from genestack.java import java_object, JAVA_LIST


class DictionaryFileQuery(object):

    CLASS_NAME = 'com.genestack.api.files.queries.DictionaryFileQuery'
    MAX_LIMIT = 50

    class QueryType(object):
        CLASS_NAME = 'com.genestack.api.files.queries.DictionaryFileQuery$QueryType'

        PREFIX = java_object(CLASS_NAME, 'PREFIX')
        SUBSTRING = java_object(CLASS_NAME, 'SUBSTRING')
        EXACT_MATCH = java_object(CLASS_NAME, 'EXACT_MATCH')

        VALID_TYPES = [PREFIX, SUBSTRING, EXACT_MATCH]

    def __init__(self, query_string, query_type, offset, limit, attributes=None):
        if query_type not in DictionaryFileQuery.QueryType.VALID_TYPES:
            raise GenestackException("Invalid query type (must be one of the types defined in `DictionaryFileQuery.QueryType`)")

        self._query_string = query_string
        self._query_type = query_type
        self._range = QueryRange(offset, limit, self.MAX_LIMIT)
        self.attributes = attributes or []

    def get_java_object(self):
        query = {
            'queryString': self._query_string,
            'queryType': self._query_type,
            'range': self._range.as_java_object(),
            'attributes':  java_object(JAVA_LIST, self.attributes)
        }
        return java_object(self.CLASS_NAME, query)


class DictionaryFile(File):
    INTERFACE_NAME = 'com.genestack.api.files.IDictionaryFile'

    DATA_LOCATION = 'genestack.location:data'
    DATA_LINK = 'genestack.url:data'

    def put_data_file(self, path):
        self.PUT(self.DATA_LOCATION, StorageUnit(gzip_file(path)))

    def get_data_file(self, working_dir=None, decompressed=True):
        units = self.GET(self.DATA_LOCATION, working_dir=working_dir)
        if len(units) == 0:
            raise GenestackException('Unable to get dictionary file')
        if len(units) != 1:
            raise GenestackException('Too many dictionary files were fetched: %s files' % len(units))

        data_file = units[0].get_first_file()
        if decompressed:
            return decompress_file(data_file, working_dir)
        return data_file

    def list_terms(self, query):
        """
        Perform a query on a dictionary file
        :param query: query
        :type query: DictionaryFileQuery
        :return: a dictionary with the following structure:

            - total (int): total number of results
            - terms (list): list of results

        Each element in `terms` is a `dict` with the following structure:

            - label (str): term label
            - id (str): term unique identifier
            - data (dict): keys are the dictionary term attributes and values are lists of strings

        :rtype: dict
        """
        if not isinstance(query, DictionaryFileQuery):
            raise GenestackException("query must be a DictionaryFileQuery object.")

        return self.invoke('listTerms', types=[query.CLASS_NAME], values=[query.get_java_object()])

