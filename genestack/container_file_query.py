# -*- coding: utf-8 -*-

from genestack.file_filters import BasicFileFilter
from genestack.genestack_exceptions import GenestackException
from genestack.java import java_object, JAVA_LIST
from genestack.query_range import QueryRange
from genestack.utils import validate_type


class ContainerFileQuery(object):
    """
    Query class to search the container.
    """
    MAX_LIMIT = 100
    CLASS_NAME = 'com.genestack.api.files.ContainerFileQuery'

    class SortOrder(object):
        CLASS_NAME = 'com.genestack.api.files.ContainerFileQuery$SortOrder'
        BY_NAME = 'BY_NAME'
        BY_ACCESSION = 'BY_ACCESSION'
        BY_LAST_UPDATE = 'BY_LAST_UPDATE'
        DEFAULT = 'DEFAULT'

    def __init__(self, filters=None, order=SortOrder.DEFAULT, ascending=True, offset=0, limit=MAX_LIMIT):
        """
        Creates a new query to use in folder search

        :param filters: list of filters to use
        :type list of BasicFileFilter:
        :param offset: starting entry index (zero-based, included)
        :type offset: int
        :param limit: number of entries
        :type limit: int
        :param order: sorting order. Must be one of the constants in :py:class:`~genestack.ContainerFileQuery.SortOrder`
        :type order: basestring
        :param ascending: should sorting be in ascending order?
        :type ascending: bool
        """
        validate_type(filters, list, accept_none=True)
        validate_type(order, basestring)
        validate_type(limit, int)
        validate_type(offset, int)
        validate_type(ascending, bool)

        if filters is not None:
            for basic_filter in filters:
                validate_type(basic_filter, BasicFileFilter)

        if order not in (self.SortOrder.BY_ACCESSION, self.SortOrder.BY_LAST_UPDATE, self.SortOrder.BY_NAME,
                         self.SortOrder.DEFAULT):
            raise GenestackException('Invalid sort order')

        self.filters = filters
        self.range = QueryRange(offset, limit, self.MAX_LIMIT)
        self.order = order
        self.ascending = ascending

    @property
    def offset(self):
        return self.range.offset

    @offset.setter
    def offset(self, value):
        self.range.offset = value

    @property
    def limit(self):
        return self.range.limit

    @limit.setter
    def limit(self, value):
        self.range.limit = value

    def get_next_page_query(self):
        """
        Creates a new query to retrieve next page of values

        :return: query that can be used to get the next page
        :rtype: ContainerFileQuery
        """
        result = ContainerFileQuery(filters=self.filters,
                                    order=self.order,
                                    ascending=self.ascending,
                                    offset=self.offset + self.limit,
                                    limit=self.limit)
        return result

    def as_java_object(self):

        object_dict = {
            'filters': java_object(JAVA_LIST, [f.as_java_object() for f in self.filters]
                                   if self.filters is not None else []),
            'range': self.range.as_java_object(),
            'order': java_object(self.SortOrder.CLASS_NAME, self.order),
            'ascending': self.ascending
        }
        return java_object(self.CLASS_NAME, object_dict)
