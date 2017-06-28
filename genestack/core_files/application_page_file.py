# -*- coding: utf-8 -*-

from genestack.core_files.genestack_file import File
from genestack.genestack_exceptions import GenestackException
from genestack.java import java_object, JAVA_STRING, JAVA_HASH_MAP, JAVA_MAP
from genestack.query_range import QueryRange
from genestack.utils import deprecated, validate_type


class StringMapFile(File):
    """
    File that stores arbitrary text data as a key-value mapping.

    It supports prefixed lookups - that is, retrieves data by prepending the provided prefix to the given key
    """
    INTERFACE_NAME = 'com.genestack.api.files.IStringMapFile'

    def as_map(self, query):
        """
        Returns this file's entries as a dict.

        :param query: query that specifies number of entries and prefix
        :type query: StringMapFileQuery
        :rtype: dict
        """
        validate_type(query, StringMapFileQuery)
        return self.invoke('asMap', types=[query.CLASS_NAME], values=[query.as_java_object()])

    def keys(self, query):
        """
        Returns this file's entry keys.

        :param query: query that specifies number of entries and prefix
        :type query: StringMapFileQuery
        :rtype: set
        """
        validate_type(query, StringMapFileQuery)
        return frozenset(self.invoke('keys', types=[query.CLASS_NAME], values=[query.as_java_object()]))

    def values(self, query):
        """
        Returns this file's entry values. Result can be lexicographically sorted, by specifying sort_direction in the
        query parameter

        :param query: query that specifies number of entries, prefix and sorting direction
        :type query: StringMapFileQuery
        :rtype: list
        """
        validate_type(query, StringMapFileQuery)
        return self.invoke('values', types=[query.CLASS_NAME], values=[query.as_java_object()])

    def get(self, key, prefix=None):
        """
        Retrieves this file's entry value associated with the provided key.

        :type key: basestring
        :param prefix: perform prefixed lookup - find values which keys start with the specified string
        :type prefix: basestring
        :return: Entry value associated with the provided key or None if the value is not present
        :rtype: basestring
        """
        validate_type(key, basestring)
        validate_type(prefix, basestring, accept_none=True)

        if prefix is None:
            return self.invoke('get', types=[JAVA_STRING], values=[key])
        else:
            return self.invoke('get', types=[JAVA_STRING, JAVA_STRING], values=[prefix, key])

    def put(self, key, value, prefix=None):
        """
        Creates a file entry with the provided key, value and prefix.

        :type key: basestring
        :type value: basestring
        :type prefix: basestring
        """
        validate_type(key, basestring)
        validate_type(value, basestring, accept_none=True)
        validate_type(prefix, basestring, accept_none=True)

        if prefix is None:
            return self.invoke('put', types=[JAVA_STRING, JAVA_STRING], values=[key, value])
        else:
            return self.invoke('put', types=[JAVA_STRING, JAVA_STRING, JAVA_STRING], values=[prefix, key, value])

    def put_all(self, values_map, prefix=None):
        """
        Creates multiple entries that correspond to the provided dict.

        :param values_map: entries to be inserted
        :type values_map: dict
        :param prefix: perform prefixed insertion
        :type prefix: basestring
        """
        validate_type(values_map, dict)
        validate_type(prefix, basestring, accept_none=True)

        value = java_object(JAVA_HASH_MAP, values_map)
        if prefix is None:
            return self.invoke('putAll', types=[JAVA_MAP], values=[value])
        else:
            return self.invoke('putAll', types=[JAVA_STRING, JAVA_MAP], values=[prefix, value])

    def size(self):
        """
        Returns the number of entries in this file.
        """
        return self.invoke('size')

    def clear(self, prefix=None):
        """
        Removes all entries, which keys start with the specified prefix.

        :param prefix: if entry's key starts with this prefix, it will be deleted. If prefix is None -
            whole file content will be erased.
        :type prefix: basestring
        """
        validate_type(prefix, basestring, accept_none=True)

        if prefix is None:
            return self.invoke('clear')
        else:
            return self.invoke('clear', types=[JAVA_STRING], values=[prefix])

    def get_modification_token(self):
        """
        Retrieves current modification counter value. Required only in StringMapFileQuery to detect
        modifications to the file while iterating over it's content.

        :rtype: int
        """
        return self.invoke('getModificationToken')

    @deprecated('use "get" instead')
    def get_value(self, key):
        return self.get(key)

    @deprecated('use "put" instead')
    def set_value(self, key, value):
        return self.put(key, value)

    @deprecated('use "put_all" instead')
    def add_all(self, values_map):
        return self.put_all(values_map)


class ApplicationPageFile(StringMapFile):
    INTERFACE_NAME = 'com.genestack.api.files.IApplicationPageFile'

    def get_application_id(self):
        return self.invoke('getApplicationId')


class StringMapFileQuery(object):
    MAX_LIMIT = 5000
    CLASS_NAME = 'com.genestack.api.files.queries.StringMapFileQuery'

    __SORT_ORDER_CLASS = 'com.genestack.api.files.queries.StringMapFileQuery$SortOrder'
    __SORT_DIRECTION_CLASS = 'com.genestack.api.files.queries.StringMapFileQuery$SortDirection'

    ORDER_BY_KEY = 'BY_KEY'
    ORDER_BY_VALUE = 'BY_VALUE'
    ORDER_DEFAULT = 'DEFAULT'

    DIRECTION_DEFAULT = 'DEFAULT'
    DIRECTION_ASCENDING = 'ASCENDING'
    DIRECTION_DESCENDING = 'DESCENDING'

    def __init__(self, string_map_file, prefix=None,
                 offset=0, limit=MAX_LIMIT,
                 sort_order=ORDER_DEFAULT,
                 sort_direction=DIRECTION_DEFAULT
                 ):
        """
        Creates a new query to use in StringMapFile's methods

        :param string_map_file: file to create query for
        :type string_map_file: StringMapFile
        :param prefix: prefix to use when retrieving values
        :type prefix: basestring
        :param offset: starting entry index (zero-based, included)
        :type offset: int
        :param limit: number of entries
        :type limit: int
        :param sort_order: sorting order. Must be one of the provided SORT_ORDER_* constants
        :type sort_direction: basestring
        :param sort_direction: sorting direction. Must be one of the provided SORT_DIRECTION_* constants
        :type sort_direction: basestring
        """
        validate_type(string_map_file, StringMapFile, accept_none=True)
        validate_type(prefix, basestring, accept_none=True)
        validate_type(offset, (int, long))
        validate_type(limit, (int, long))
        validate_type(sort_order, basestring)
        validate_type(sort_direction, basestring)

        if sort_order not in (self.ORDER_BY_KEY,
                              self.ORDER_BY_VALUE,
                              self.ORDER_DEFAULT):
            raise GenestackException('Invalid sort order')
        if sort_direction not in (self.DIRECTION_DEFAULT,
                                  self.DIRECTION_ASCENDING,
                                  self.DIRECTION_DESCENDING):
            raise GenestackException('Invalid sort direction')

        self._token = None if string_map_file is None else string_map_file.get_modification_token()
        self.prefix = '' if prefix is None else prefix
        self.range = QueryRange(offset, limit, self.MAX_LIMIT)
        self.sort_order = sort_order
        self.sort_direction = sort_direction

    @property
    def offset(self):
        return self.range.offset

    @property
    def limit(self):
        return self.range.limit

    def get_next_page_query(self):
        """
        Creates a new query to retrieve next page of values

        :return: query that can be used to get the next page
        :rtype: StringMapFileQuery
        """
        result = StringMapFileQuery(None,
                                    prefix=self.prefix,
                                    offset=self.offset + self.limit,
                                    limit=self.limit,
                                    sort_order=self.sort_order,
                                    sort_direction=self.sort_direction)
        result._token = self._token
        return result

    def as_java_object(self):
        if self._token is None:
            raise GenestackException('Modification token was not set')
        object_dict = {
            'token': self._token,
            'prefix': self.prefix,
            'range': self.range.as_java_object(),
            'sortOrder': java_object(self.__SORT_ORDER_CLASS, self.sort_order),
            'sortDirection': java_object(self.__SORT_DIRECTION_CLASS, self.sort_direction)
        }
        return java_object(self.CLASS_NAME, object_dict)
