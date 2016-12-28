# -*- coding: utf-8 -*-

from genestack.genestack_exceptions import GenestackException
from genestack.core_files.genestack_file import File
from genestack.java import java_object
from genestack.metainfo import MetainfoValue
from genestack.utils import validate_type


class BasicFileFilter(object):
    pass


class TypeFileFilter(BasicFileFilter):
    CLASS_NAME = "com.genestack.api.files.filters.TypeFileFilter"

    def __init__(self, file_type):
        BasicFileFilter.__init__(self)
        validate_type(file_type, type)
        if not issubclass(file_type, File):
            raise GenestackException("Invalid file type")
        self.type = file_type.INTERFACE_NAME

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {"type": self.type})


class MetainfoKeyFileFilter(BasicFileFilter):
    CLASS_NAME = "com.genestack.api.files.filters.MetainfoKeyFileFilter"

    def __init__(self, key):
        BasicFileFilter.__init__(self)
        validate_type(key, basestring)
        self.key = key

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {"key": self.key})


class MetainfoKeyValueFileFilter(BasicFileFilter):
    CLASS_NAME = "com.genestack.api.files.filters.MetainfoKeyValueFileFilter"

    def __init__(self, key, value):
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
    CLASS_NAME = "com.genestack.api.files.filters.ActualOwnerFileFilter"

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {})


class FixedValueFileFilter(BasicFileFilter):
    CLASS_NAME = "com.genestack.api.files.filters.FixedValueFileFilter"

    def __init__(self, value):
        BasicFileFilter.__init__(self)
        validate_type(value, bool)
        self.value = value

    def as_java_object(self):
        return java_object(self.CLASS_NAME, {"value": self.value})
