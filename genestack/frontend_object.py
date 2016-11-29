# -*- coding: utf-8 -*-

# import logging
import os
from genestack.java import JAVA_STRING, JAVA_LIST
from genestack import GenestackException
from genestack.metainfo import MetainfoValue, Metainfo
from genestack.utils import log_warning, to_list, unbuffer_stdout, validate_type
from genestack.bridge import _Bridge
from genestack.java import java_object

_bridge = _Bridge()


def get_bridge():
    return _bridge


def set_bridge(bridge):
    global _bridge
    _bridge = bridge


unbuffer_stdout()


class StorageUnit(object):
    """
    Object representing storage unit in database.
        - files: list of files. Expected that it is valid paths. Files cannot be empty.
        - format: dictionary. This format describes whole group of files.
    """
    def __init__(self, file_or_list, file_format=None):
        """
        Creates storage unit. Accepts single path to file or list of paths.

        :param file_or_list: single path or list of paths
        :param file_format: file format
        :type file_format: dict
        :return:
        """
        self.files = to_list(file_or_list)

        base_names = {os.path.basename(x) for x in self.files}
        if len(base_names) != len(self.files):
            raise GenestackException('Put files with same base names are prohibited')

        self.format = file_format

    def validate(self):
        nonexistent_paths = [path for path in self.files if not os.path.exists(path)]
        if nonexistent_paths:
            raise GenestackException('Files do not exist: %s' % nonexistent_paths)

    def get_first_file(self):
        """
        Return first file from StorageUnit.
        It is common situation when we expect only one file in storage unit.

        :return: file path
        :rtype: str
        """
        return self.files[0]

    def __repr__(self):
        return 'StorageUnit(%r, file_format=%s)' % (self.files, self.format)

    def to_map(self):
        """
        Return map representation of object.

        :return:
        """
        return {'files': self.files, 'format': self.format}


class GenestackObject(object):
    def __init__(self, object_id, interface_name):
        """
        Creates new file by file Id

        :param object_id: file id
        :type object_id: int
        """
        if not isinstance(object_id, (int, long)):
            from pprint import pformat
            log_warning("Non-number `object_id` for %s: %s,"
                        " attempting to convert" % (interface_name,
                                                    pformat(object_id)))
        try:
            self.__object_id = int(object_id)
        except ValueError:
            raise GenestackException('Object ID is invalid: %s' % object_id)
        self.__interface_name = interface_name

    @property
    def object_id(self):
        return self.__object_id

    @property
    def interface_name(self):
        return self.__interface_name

    @property
    def bridge(self):
        return get_bridge()

    def __eq__(self, other):
        return self.interface_name == other.interface_name and self.object_id == other.object_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.interface_name, self.object_id))

    def invoke(self, method_name, types=None, values=None):
        return self.bridge.invoke(self.object_id, self.interface_name, method_name, types, values)

    def send_index(self, values=None):
        return self.bridge.send_index(self, values)

    def get_metainfo(self):
        """
        Return metainfo for file.

        :return: metainfo object
        :rtype: Metainfo
        """
        source_metainfo = self.invoke('getMetainfo')['data']
        metainfo = Metainfo()

        for key, value in source_metainfo.items():
            metainfo[key] = MetainfoValue.get_metainfo_value(value)
        return metainfo

    def add_metainfo_value(self, key, value, flag=Metainfo.Flag.SET_BY_INITIALIZATION):
        """
        Add metainfo value.
        By default, this will also set the flag `SET_BY_INITIALIZATION` on the key.

        :param key: metainfo Key
        :type key: str
        :param value: metainfo value or list of metainfo values
        :type value: MetainfoValue | list[MetainfoValue]
        :param flag: flag to set on the key (choose from ``Metainfo.Flag``) ; can be `None`
        :type flag: int
        :raise GenestackException:

        """
        validate_type(key, basestring)
        value_list = to_list(value)
        for val in value_list:
            validate_type(val, MetainfoValue, accept_none=True)
        java_value = java_object(MetainfoValue.METAINFO_LIST_VALUE, {"list": java_object(JAVA_LIST, value_list)})
        if flag is not None:
            self.set_metainfo_flags(key, flag)
        self.invoke(
            'addMetainfoValue',
            types=[JAVA_STRING, 'com.genestack.api.metainfo.IMetainfoValue'],
            values=[key, java_value]
        )

    def replace_metainfo_value(self, key, value, flag=Metainfo.Flag.SET_BY_INITIALIZATION):
        """
        Replace metainfo value.
        By default, this will also set the flag `SET_BY_INITIALIZATION` on the key.

        :param key: metainfo Key
        :type key: str
        :param value: metainfo value
        :type value: MetainfoValue
        :param flag: flag to set on the key (choose from `Metainfo.Flag`)
        :type flag: int
        :raise GenestackException:
        """
        validate_type(key, basestring)
        validate_type(value, MetainfoValue, accept_none=True)
        if flag is not None:
            self.set_metainfo_flags(key, flag)
        self.invoke(
            'replaceMetainfoValue',
            types=[JAVA_STRING, 'com.genestack.api.metainfo.IMetainfoValue'],
            values=[key, value]
        )

    def remove_metainfo_value(self, key):
        """
        Remove metainfo value.

        :param key: metainfo Key
        :type key: str
        :raise GenestackException:
        """
        validate_type(key, basestring)
        self.invoke(
            'removeMetainfoValue',
            types=[JAVA_STRING],
            values=[key]
        )

    def set_metainfo_flags(self, key, flags, set_flags=True):
        """
        Set/unset metainfo flags on a specific key.
        :param key: key
        :type key: str
        :param flags: flags to set/unset
        :type flags: int
        :param set_flags: should the flags be set or unset (default: set)
        :type set_flags: bool
        """
        validate_type(key, basestring)
        validate_type(flags, int)
        validate_type(set_flags, bool)
        self.invoke(
            'setMetainfoFlags',
            types=[JAVA_STRING, 'int', 'boolean'],
            values=[key, flags, set_flags]
        )

    def resolve_reference(self, key, filetype=None):
        """
        Return file by file reference key.

        :param key: matainfo key
        :type key: str
        :param filetype: expected return class, must be subclass of File
        :type filetype: T
        :return: instance of File or it subclass.
        :rtype: T
        """
        raise GenestackException('Not implemented for object: %s' % self.interface_name)

    def as_java_object(self):
        return java_object(self.interface_name, {"id": self.object_id})
