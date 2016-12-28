# -*- coding: utf-8 -*-

from genestack import utils
from genestack.genestack_exceptions import GenestackException
from genestack.java import java_object


class QueryRange(object):
    """
    Class that represents the offset-limit pair used in queries as query bounds.
    """
    CLASS_NAME = 'com.genestack.api.queries.QueryRange'

    def __init__(self, offset, limit, max_page_size):
        utils.validate_type(offset, (int, long))
        utils.validate_type(limit, (int, long))
        utils.validate_type(max_page_size, (int, long))

        if offset < 0 or limit <= 0:
            raise GenestackException('Incorrect query bounds')
        if limit > max_page_size:
            raise GenestackException('Maximum page size exceeded')

        self.offset = offset
        self.limit = limit

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {'offset': self.offset, 'limit': self.limit})
