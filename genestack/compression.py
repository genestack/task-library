# -*- coding: utf-8 -*-

import os
from subprocess import Popen, PIPE, check_call

from genestack.genestack_exceptions import GenestackException
from genestack.utils import get_unique_name, makedirs_p


UNCOMPRESSED = 'uncompressed'
GZIP = 'gzip'
BZIP2 = 'bzip2'
ZIP = 'zip'

AVAILABLE_COMPRESSIONS = (UNCOMPRESSED, BZIP2, GZIP, ZIP)
ARCHIVE_EXTENSIONS = ['.gz', '.bgz', '.zip', '.bz2']


def get_last_non_archive_extension(path):
    """
    Return last extenstion which is not an archive extension.

    >>> get_last_non_archive_extension('a.bb.gz.bz2')
    '.bb'
    >>> get_last_non_archive_extension('a.gz.bz2')
    ''
    :param path: path to the file
    :type file_name: str
    :return: return last non-archive extension
    :rtype: str
    """
    base, ext = os.path.splitext(path)
    while ext in ARCHIVE_EXTENSIONS:
        base, ext = os.path.splitext(base)
    return ext


def _get_file_compression_unchecked(file_name):
    if file_name.endswith(('.gz', '.bgz')):
        # .bgz is our extension to gzip files created by TABIX,
        # This is valid gzip but we use a different extension to avoid clashes on backend.
        return GZIP
    elif file_name.endswith('.bz2'):
        return BZIP2
    elif file_name.endswith('.zip'):
        return ZIP
    else:
        return UNCOMPRESSED


def get_file_compression(file_name):
    """
    Return constant that represents compression of a file. The file must be present on disc.

    :py:attr:`ZIP` zip compression
    :py:attr:`BZIP2` bgzip2 compression
    :py:attr:`GZIP` gzip
    :py:attr:`UNCOMPRESSED` file isn't compressed using any of the listed compressions

    :param file_name: filename
    :type file_name: str
    :return: compression constant
    :rtype: str
    """
    if not os.path.isfile(file_name):
        raise GenestackException('Cannot detect compression of "%s", '
                                 "file doesn't exist" % file_name)
    return _get_file_compression_unchecked(file_name)


def get_compression(files):
    """
    Return compression for group of files.
    If compression is not the same for all files,
    :py:class:`~genestack.GenestackException` is raised.

    :param files: list of files
    :type files: list[str]
    :return: compression constant
    :rtype: str
    """
    compressions = {get_file_compression(name) for name in files}
    if len(compressions) != 1:
        raise GenestackException('All files must have the same compression, different compressions detected: %s' %
                                 ', '.join(files))
    return compressions.pop()


def _pipe(source_path, list_of_commands, output_path):
    """
    Pipes commandlines together. Works like:
       `cat source_path > arg[0] [| args[1] | ...] > output_path`
    :param source_path: path of source file, file must exist
    :type source_path: str
    :param list_of_commands: list of command arguments that should be piped
    :type list_of_commands: list[str]
    :param output_path: path for the output file
    :type output_path: str
    :return: None
    """
    with open(source_path) as source, open(output_path, 'wb') as output:
        if len(list_of_commands) == 1:
            process = Popen(list_of_commands[0], stdin=source, stdout=output)
        else:
            process = Popen(list_of_commands[0], stdout=PIPE, stdin=source)
            for args in list_of_commands[1:-1]:
                process = Popen(args, stdin=process.stdout, stdout=PIPE)
            process = Popen(list_of_commands[-1], stdin=process.stdout, stdout=output)
        process.communicate()
        process.wait()


def compress_file(source, from_compression, to_compression, working_dir, remove_source=True):
    """
    Recompress file from one compression to another and remove existing file.
    Name for result file is chosen by changing file extension.
    If file with such name already exists, add unique prefix to file.

    If ``from_compression`` and ``to_compression`` are the same, then this function does nothing
    and simply returns ``source`` file.
    If ``from_compression`` or ``to_compression`` are not supported, they are ignored just as if
    ``UNCOMPRESSED`` was specified.

    :param source: path to existing file to be compressed
    :type source: str
    :param from_compression: compression from
    :type from_compression: str
    :param to_compression: compression to
    :type to_compression: str
    :param working_dir: directory to copy files into
    :type working_dir: str
    :param remove_source: flag if source file should be removed. Default ``True``
    :type remove_source: bool
    :return: compressed file path
    :rtype: str
    """
    if from_compression == to_compression:
        return source
    args = []
    current_source = source
    intermediate_files = []
    output = os.path.join(working_dir, os.path.basename(source))

    if from_compression == BZIP2:
        args.append(['bzip2', '-d', '-c'])
        output = os.path.splitext(output)[0]
    elif from_compression == GZIP:
        args.append(['gzip', '-d', '-c'])
        output = os.path.splitext(output)[0]
    elif from_compression == ZIP:
        output = get_unique_name(os.path.splitext(output)[0])
        with open(output, 'wb') as output_file:
            check_call(['unzip', '-p', current_source], stdout=output_file)
        current_source = output
        intermediate_files.append(current_source)

    if to_compression == BZIP2:
        args.append(['bzip2'])
        output += '.bz2'
    elif to_compression == GZIP:
        args.append(['gzip'])
        output += '.gz'
    elif to_compression == ZIP:
        raise GenestackException('Compression to ZIP is not supported')

    if args:
        # `args` is empty in case of ZIP -> UNCOMPRESSED (already uncompressed)
        output = get_unique_name(output)
        _pipe(current_source, args, output)

    if remove_source:
        intermediate_files.append(source)
    # Never remove output file, even if it is a source or one of the intermediate files created
    if output in intermediate_files:
        intermediate_files.remove(output)

    for name in intermediate_files:
        os.remove(name)
    return output


def gzip_file(path, dest_folder=None, remove_source=True):
    """
    Return path to gzipped file.

    If file is already gzipped return ``path``.

    Files placed in the same directory as its sources.
    If resulting file already exists exception will be thrown.

    To avoid name conflicts ``dest_folder`` can be specified.
    If ``dest_folder`` does not exist it will be created.

    :param path: path to existing file
    :type path: str
    :param dest_folder: folder path to store result
    :type dest_folder: str
    :param remove_source: flag if source files should be removed
    :type remove_source: bool
    :return: path to gzipped file
    """
    compression = get_file_compression(path)
    if compression == GZIP:
        return path

    if dest_folder:
        makedirs_p(dest_folder)
    else:
        dest_folder = os.path.dirname(path)

    return os.path.relpath(compress_file(path, compression, GZIP, dest_folder, remove_source=remove_source))


def decompress_file(path, dest_folder=None, remove_source=True):
    """
    If file is unpacked return path to it; otherwise unpack file to destination
    folder and return path to decompressed file.
    If ``dest_folder`` is not specified, use current working directory.
    By default remove source file to save disc space.


    ``GZIP``, ``BZIP2`` and ``ZIP`` are currently supported.

    :param path: path to file
    :type path: str
    :param dest_folder: place to put file
    :type dest_folder: str
    :param remove_source: flag if source file should be removed. Default ``True``
    :type remove_source: bool
    :return: path to unpacked file
    :rtype: str
    """
    dest_folder = dest_folder or os.curdir
    makedirs_p(dest_folder)
    compression = get_file_compression(path)
    if compression == UNCOMPRESSED:
        return path
    return os.path.relpath(
        compress_file(path, compression, UNCOMPRESSED, dest_folder, remove_source=remove_source))
