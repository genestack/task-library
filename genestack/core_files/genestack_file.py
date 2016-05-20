# -*- coding: utf-8 -*-

"""
    java File object shadow
"""
import hashlib
import os
import sys

from genestack.compression import ZIP, get_file_compression
from genestack.frontend_object import GenestackObject, StorageUnit
from genestack import GenestackException
from genestack.metainfo import FileReference, StringValue
from genestack.utils import to_list, opener, log_info, FormatPattern


def checked_filetype(filetype):
    if filetype is None:
        return File
    if not issubclass(filetype, File):
        raise GenestackException(
            'Type %s is not a subtype of genestack.File' % filetype
        )
    return filetype


def md5sum(filename_list):
    """
    Count md5 for list of files or directories, unpack gzip archives before counting.
    """
    md5 = hashlib.md5()
    for filename in filename_list:
        if os.path.isfile(filename):
            _count_md5_for_file(md5, filename)
        elif os.path.isdir(filename):
            for base, dirs, files in os.walk(filename):
                dirs.sort()  # ensure that directories will be traversed in same order on all platforms
                for name in sorted(files):
                    _count_md5_for_file(md5, os.path.join(base, name))
    return md5.hexdigest()


def _count_md5_for_file(md5, path):
    compression = get_file_compression(path)
    # opener does not support ZIP yet so count md5 for compressed file
    if compression == ZIP:
        _open = open
    else:
        _open = opener

    with _open(path) as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)


class File(GenestackObject):
    """
    Representation of genestack file.
    """
    WARNING_KEY = 'genestack.initialization:warning'
    PROGRESS_INFO = "genestack:progressInfo"
    INTERFACE_NAME = 'com.genestack.api.files.IFile'

    def __init__(self, file_id=None):
        if file_id is None:
            file_id = int(sys.argv[1])
        GenestackObject.__init__(self, file_id, self.INTERFACE_NAME)
        self._indexing_pool = None
        self._indexing_recent_response = None

    def add_warning(self, msg):
        self.add_metainfo_value(File.WARNING_KEY, StringValue(msg))

    def resolve_reference_list(self, key, filetype=None):
        """
        Return file list by file reference key.

        :param key: matainfo key
        :type key: str
        :param filetype: expected return class, must be subclass of File
        :type filetype: type
        :return: list of File or it subclass instances.
        """
        filetype = checked_filetype(filetype)
        return [self.__resolve_reference(key, ref, filetype)
                for ref in self.get_metainfo().get_value_as_list(key)]

    def resolve_reference(self, key, filetype=None):
        """
        Return file by file reference key.

        :param key: matainfo key
        :type key: str
        :param filetype: expected return class, must be subclass of File
        :type filetype: type
        :return: instance of File or it subclass.
        """
        return self.__resolve_reference(
            key,
            self.get_metainfo().get(key),  # TODO: use Java method with metaKey instead of getting metainfo here
            checked_filetype(filetype)
        )

    def __resolve_reference(self, key, ref, filetype):
        if not isinstance(ref, FileReference):
            raise GenestackException(
                'Metainfo value at %s is %s, not a FileReference' % (key, type(ref))
            )
        serialized_file_class = [
            'java.lang.Class', 'com.genestack.api.files.IFile'
        ]

        res = self.invoke(
            'resolveReference',
            ['com.genestack.api.metainfo.FileReference', 'java.lang.Class'],
            [ref, serialized_file_class])
        if ref is None:
            raise GenestackException('Cannot resolve reference: "%s", '
                                     'check if task owner has permission to access this file' % key)
        return filetype(res['id'])

    def add_checksum_conditionally(self, key, storage_units):
        check_key = 'genestack.checksum:markedForTests'
        checksum_key = 'genestack.checksum.actual:%s' % key

        if check_key in self.get_metainfo():
            files = []
            for unit in storage_units:
                files.extend(unit.files)
            self.replace_metainfo_value(checksum_key, StringValue(md5sum(files)))

    def set_progress_stage(self, stage_name, progress=None):
        """
        Saves stage_name and stage progress to metainfo.
        :param stage_name: name of stage
        :type stage_name: str
        :param progress: percentage of stage execution in rage 0-100
        :type progress: int | float
        :return: None
        """
        if progress is not None:
            progress = int(progress)
            stage_name += ' %3d%%' % progress
        self.replace_metainfo_value(self.PROGRESS_INFO, StringValue(stage_name))

    def GET(self, key, formats=None, format_pattern=None, working_dir=None):
        """
        Copies files to task working directory and returns list of :py:class:`~genestack.StorageUnit`
        stored by metainfo key.
        If ``working_dir`` is not specified, files stored in current working directory.
        It is allowed to specify ``format_pattern`` to convert file to required format during GET.
        See your File specification for more info about formats.
        If key in map is empty list or absent it means that any value matches this pattern.

        :param key: metainfo key
        :type key: str
        :param formats: deprecated use ``format_pattern`` instead
        :type formats: various
        :param format_pattern: format pattern
        :type format_pattern: :py:class:`~genestack.utils.FormatPattern`
        :param working_dir: optional dir to save files, default is current dir
        :type working_dir: str
        :return: List of :py:class:`~genestack.StorageUnit`
        :rtype: list
        :raise GenestackException: If has not files corresponding to key.
        """
        log_info('Getting file for key "%s"' % key)
        working_dir = working_dir or os.path.curdir

        if formats:
            sys.stderr.write('"formats" argument is deprecated, use "format_pattern" instead')
            if format_pattern:
                raise GenestackException('Both "formats" and "format_pattern" arguments are specified')
            format_pattern = FormatPattern([{k: to_list(v) for k, v in item.items()} for item in to_list(formats)])
        response = self.bridge.get(self, key, format_pattern, working_dir)

        storage_units = []
        for unit in response:
            # should we use relpath here?
            storage_units.append(StorageUnit(unit['files'], unit['format']))
        return storage_units

    def PUT(self, key, storage_or_list):
        """
        Save :py:class:`~genestack.StorageUnit` to database. All file names (os.path.basename(path))
        in all storage units should be unique.

        :param key: metainfo key
        :type key: str
        :param storage_or_list: list fo StorageUnits or single StorageUrl
        :return: None
        :raise GenestackException: if can not save file to database
        """
        storage_or_list = to_list(storage_or_list)
        self.add_checksum_conditionally(key, storage_or_list)
        log_info('Putting file for key "%s"' % key)
        # TODO: rewrite to accept only list|tuple
        self.bridge.put(self, key, storage_or_list)

    def set_format(self, key, storage_or_list):
        storage_unit_list = to_list(storage_or_list)
        self.bridge.set_format(self, key, storage_unit_list)

    def DOWNLOAD(self, storage_key, links_key, verify=None, fold=False, put_to_storage=True, working_dir=None):
        """
        Download files to task working directory and put them to storage.
        Every :py:class:`~genestack.metainfo.ExternalLink` for ``links_key`` in metainfo is stored to separate
        `StorageUrlValue` object for ``storage_key``.  If ``storage_key`` is declared
        in Java as `@MetainfoDeclaration(..., single=True)`, then you should use
        flag ``fold=True``, and this method will download all external links into
        one `StorageUrlValue`.  When ``fold`` is set to ``True`` then all external
        links should either have no format specified or have the same format.

        :param storage_key: key for `StorageUrlValue` objects
        :type storage_key: str
        :param links_key: key for `ExternalLink` objects
        :type links_key: str
        :param verify: optional verification function
        :type verify: function
        :param fold: flag if all external links should be downloaded into one
                     `StorageUrlValue`
        :type fold: bool
        :param put_to_storage: flag if file should be put to storage
        :type put_to_storage: bool
        :param working_dir: folder to store download files
        :type working_dir: str
        :return: list of paths to downloaded files
        :rtype: list
        :raise GenestackException: if files can be downloaded
        """
        # do validation?
        log_info('Downloading file from key "%s" to "%s"' % (links_key, storage_key))
        return self.bridge.download(self, storage_key, links_key, fold, put_to_storage, working_dir)
