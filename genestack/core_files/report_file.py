# -*- coding: utf-8 -*-

"""
    java ReportFile object shadow
"""

import os
import urllib
import mimetypes

from genestack import File, StorageUnit
from genestack.metainfo import StringValue


class ReportFile(File):
    DESCRIPTORS_KEY = 'genestack.data:descriptors'
    FILE_URL = 'genestack.location:file'
    INTERFACE_NAME = 'com.genestack.api.files.IReportFile'

    NAME_PROPERTY = 'original-name'
    COMMENT_PROPERTY = 'comment'

    def set_reports(self, items):
        """
        Writes new report data for this ReportFile.
        Method takes a list of 3-tuples:
        [(path, mime, comment), ...]

        :param items: list of report data items, each item is 3-tuple (path, mime, comment)
        :type items: list
        """
        self.remove_metainfo_value(self.DESCRIPTORS_KEY)
        links = []
        for path, mime, comment in items:
            self.add_metainfo_value(
                self.DESCRIPTORS_KEY,
                StringValue(self.__create_meta_string(path, mime, comment))
            )
            links.append(StorageUnit(path))
        self.PUT(self.FILE_URL, links)

    def get_descriptors(self):
        """
        Returns list of report item descriptors.
        List of dict objects with keys 'index', 'mime', 'comment', and 'originalName'.

        :rtype: list
        """
        return self.invoke('getDescriptors')

    def get_reports(self, working_dir=None):
        """
        Returns all report data as list of pairs [(report descriptor, storage unit), ...]

        :rtype: list
        """
        descriptors = self.get_descriptors()
        if descriptors:
            units = self.GET(self.FILE_URL, working_dir=working_dir)
            return zip(descriptors, units)
        else:
            return []

    def __create_meta_string(self, path, mime, comment):
        properties = []

        def add_param(key, value):
            properties.append('%s=%s' % (key, self.__escape_quotation(value)))

        if mime:
            properties.append(mime)
        else:
            properties.append(self.__extract_mime(path))

        if comment:
            add_param(self.COMMENT_PROPERTY, comment)

        name = os.path.basename(os.path.abspath(path))
        if name:
            add_param(self.NAME_PROPERTY, name)

        return ';'.join(properties)

    @staticmethod
    def __escape_quotation(value_string):
        special_characters = ['(', ')', '<', '>', '@', ',', ';', ':', '\\', '"', '/', '[', ']', '?', '=']
        if any(char in value_string for char in special_characters):
            escaped = value_string.replace('\\', '\\\\').replace('"', '\\"')
            return '"' + escaped + '"'
        return value_string

    @staticmethod
    def __extract_mime(path):
        pathname_url = urllib.pathname2url(os.path.abspath(path))
        guessed_mime = mimetypes.guess_type(pathname_url)
        if guessed_mime[0] is None:
            return 'text/plain'
        return guessed_mime[0]
