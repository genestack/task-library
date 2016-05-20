# -*- coding: utf-8 -*-

from genestack.java import java_object, JAVA_HASH_MAP, JAVA_ARRAY_LIST
from genestack import GenestackException
from genome_interval import GenomeInterval


# TODO: should we check all data types here (ex. string, booleans)?
# TODO: what kind of docs should be provided
class GenomeQuery:
    def __init__(self):
        self.requested_area = {}
        self.filter = {}
        self.response_format = {}
        self.response_offset = None
        self.response_limit = None
        self.sorting_order = None
        self.ascending = None

    def add_requested_area(self, key, value):
        """
        Adds requested area.
        :param key: requested area key, ex. 'featureId'
        :param value: requested area
        :return: None
        """
        if key == 'interval' or key == 'intervals':
            self.add_interval(value)
        else:
            self.requested_area[key] = value

    def add_interval(self, interval):
        """
        Adds interval to requested area 'intervals' field.
        :param interval: GenomeInterval
        :return: None
        """
        if not isinstance(interval, GenomeInterval):
            raise GenestackException(
                'Interval is not of type GenomeInterval: %s' % type(interval)
            )
        self.requested_area.setdefault('intervals', []).append(interval)

    def add_filter(self, key, value):
        """
        Adds filter.
        :param key: requested area key, ex. 'featureId'
        :param value: requested area
        :return: None
        """
        self.filter[key] = value

    def add_response_format(self, key, value):
        """
        Adds response format.
        :param key: requested area key, ex. 'featureId'
        :param value: requested area
        :return: None
        """
        self.response_format[key] = value

    def set_limits(self, response_offset, response_limit):
        if response_offset < 0:
            raise GenestackException("Response offset cannot be negative")
        if response_limit < 0:
            raise GenestackException("Response limit cannot be negative")
        if response_limit > self.MAX_LIMIT:
            raise GenestackException("Response limit must be less than %d" % self.MAX_LIMIT)
        self.response_offset = response_offset
        self.response_limit = response_limit

    def next_page(self):
        self.response_offset += self.response_limit

    def set_sorting_order(self, order, ascending):
        self.sorting_order = order
        self.ascending = ascending

    def get_java_object(self):
        req_area = {}
        for area in self.requested_area:
            if area == 'intervals':
                intervals = self.requested_area.get('intervals', [])
                if len(intervals) > 0:
                    java_intervals = []
                    for interval in intervals:
                        java_intervals.append(interval.get_java_object())
                    req_area['intervals'] = java_object(JAVA_ARRAY_LIST, java_intervals)
            else:
                req_area[area] = self.requested_area[area]
        query = {}
        if len(req_area) > 0:
            query['requestedArea'] = java_object(JAVA_HASH_MAP, req_area)
        if len(self.filter) > 0:
            query['filter'] = java_object(JAVA_HASH_MAP, self.filter)
        if len(self.response_format) > 0:
            query['responseFormat'] = java_object(JAVA_HASH_MAP, self.response_format)
        if self.response_offset is not None:
            query['responseOffset'] = self.response_offset
        if self.response_limit is not None:
            query['responseLimit'] = self.response_limit
        if self.sorting_order is not None:
            query['sortingOrder'] = self.sorting_order
        if self.ascending is not None:
            query['ascending'] = self.ascending

        return java_object('com.genestack.bio.files.GenomeQuery', query)
