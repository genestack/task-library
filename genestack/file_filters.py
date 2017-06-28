# -*- coding: utf-8 -*-

from genestack.genestack_exceptions import GenestackException
from genestack.core_files.genestack_file import File
from genestack.java import java_object
from genestack.metainfo import MetainfoValue
from genestack.utils import validate_type


class BasicFileFilter(object):
    pass


class TypeFileFilter(BasicFileFilter):
    """
    FileFilter to filter files by file type.
    """
    CLASS_NAME = "com.genestack.api.files.filters.TypeFileFilter"

    def __init__(self, file_type):
        """
        :param file_type: type of file
        :type file_type: T <= File

        """
        BasicFileFilter.__init__(self)
        validate_type(file_type, type)
        if not issubclass(file_type, File):
            raise GenestackException("Invalid file type")
        self.type = file_type.INTERFACE_NAME

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {"type": self.type})


class MetainfoKeyFileFilter(BasicFileFilter):
    """
    FileFilter to filter files by metainfo key name.
    """
    CLASS_NAME = "com.genestack.api.files.filters.MetainfoKeyFileFilter"

    def __init__(self, key):
        """
        :param key: metainfo key
        :type key: basestring
        """
        BasicFileFilter.__init__(self)
        validate_type(key, basestring)
        self.key = key

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {"key": self.key})


class MetainfoKeyValueFileFilter(BasicFileFilter):
    """
    FileFilter to filter files by metainfo key value.
    """
    CLASS_NAME = "com.genestack.api.files.filters.MetainfoKeyValueFileFilter"

    def __init__(self, key, value):
        """
        :param key: metainfo key
        :type key: basestring
        :param value: metainfo value object
        :type value: T <= MetainfoValue
        """
        BasicFileFilter.__init__(self)
        validate_type(key, basestring, accept_none=True)
        validate_type(value, MetainfoValue, accept_none=True)
        if key is None and value is None:
            raise GenestackException("Key and value cannot be null simultaneously")
        self.key = key
        self.value = value

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {"key": self.key, "value": self.value})


class ActualOwnerFileFilter(BasicFileFilter):
    """
    FileFilter to filter files owned by current authority.
    In typical case, return files owned by user.
    If user is sudoed as a group, return files owned by that group.
    If user is sudoed as other user, return only files owned by that user.
    """
    CLASS_NAME = "com.genestack.api.files.filters.ActualOwnerFileFilter"

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {})


class FixedValueFileFilter(BasicFileFilter):
    """
    Utility FileFilter to get all files if ``all_files == True`` and no files otherwise.

    Can be used for better code organization.
    """
    CLASS_NAME = "com.genestack.api.files.filters.FixedValueFileFilter"

    def __init__(self, all_files):
        """
        :param all_files: flag if filter should match all files or none files
        :type all_files: bool
        """
        BasicFileFilter.__init__(self)
        validate_type(all_files, bool)
        self.value = all_files

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {"value": self.value})
