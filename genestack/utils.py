# -*- coding: utf-8 -*-

import bz2
import gzip
import multiprocessing
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, tzinfo
from functools import wraps
from subprocess import check_call

from genestack.genestack_exceptions import GenestackException
from genestack import environment
from genestack.environment import PROGRAMS_DIRECTORY

DEFAULT_CPU_COUNT = 8


def join_program_path(*args):
    """
    Return path with prepended PROGRAMS_DIRECTORY. Same as:
    ``os.path(PROGRAMS_DIRECTORY, *args)``

    For example to get samtools executable:
    ``join_program_path('samtools', '0.1.19' 'samtools')``

    :param args: list of related paths from PROGRAMS_DIRECTORY
    :return: absolute path
    :rtype: str
    """
    return os.path.abspath(os.path.join(PROGRAMS_DIRECTORY, *args))


def to_list(obj):
    """
    Wrap object to list if it is not list.

    :param obj: object for wrapping
    :return: list
    """
    if type(obj) == list:
        return obj
    return [obj]


def makedirs_p(path):
    """
    Create directories recursively.

    :param path: path for folder to create
    :return: None
    """
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except os.error:
            # double-check on case directory was created between the first check
            # and a call to os.makedirs(path)
            if not os.path.isdir(path):
                raise


def remove_file(path):
    """
    Remove file or directory.

    :param path: path to remove
    :type path: str
    :return: None
    """
    if os.path.exists(path) or os.path.islink(path):
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


@contextmanager
def opener(filename, mode='r'):
    """
    Context manager for opening regular and compressed files.
    ``gzip`` and ``bzip2`` compression are supported.
    Always opens files in binary mode.

    Looks like best way to check if file is gzipped is to check extension:
    http://stackoverflow.com/a/3703300/1310066

    :param filename: name of file
    :type filename: str
    :param mode: is either 'r' or 'w' ('r' by default)
    :type mode: str
    """
    # avoid circular imports
    # noinspection PyProtectedMember
    from genestack.compression import _get_file_compression_unchecked, GZIP, BZIP2, UNCOMPRESSED

    if mode not in ['r', 'w']:
        raise GenestackException('Invalid mode: %s' % repr(mode))
    mode = '%sb' % mode

    compression = _get_file_compression_unchecked(filename)

    compression_map = {
        GZIP: gzip.open,
        BZIP2: bz2.BZ2File,
        UNCOMPRESSED: open,
    }

    _open = compression_map.get(compression)
    if _open is None:
        raise GenestackException('Compression is not supported: %s' % compression)

    f = _open(filename, mode=mode)
    try:
        yield f
    finally:
        f.close()


def is_empty_file(file_path):
    """
    Return True if file is empty.
    Gziped files always contains header and has non zero size.

    :param file_path: path to file
    :type file_path: str
    :return: boolean value if file is empty.
    :rtype: bool
    """
    if file_path.endswith('.gz'):
        with opener(file_path, 'r') as f:
            return not bool(f.read(1))
    else:
        return not os.path.getsize(file_path)


def concatenate_files(paths, output_path):
    """
    Concatenate files analog for: cat paths > output_path.

    :param paths: list of paths
    :type paths: list
    :param output_path: path of result file
    :type output_path: str
    :return: output_path
    """
    # TODO: should we check if output file already exists? -- Klas
    (_, inter_path) = tempfile.mkstemp(dir='.')
    with open(inter_path, 'wb') as result_file:
        for path in paths:
            with opener(path) as to_read:
                shutil.copyfileobj(to_read, result_file)
    shutil.move(inter_path, output_path)
    return output_path


def get_cpu_count():
    """
    Counts number of CPU on worker.

    :return: number of CPU
    """
    try:
        return multiprocessing.cpu_count()
    except NotImplemented:
        return DEFAULT_CPU_COUNT


def get_size(src):
    """
    Return size for file or folder.

    :param src: valid path
    :type src: str
    :return: size in bytes
    :rtype: int
    """
    if os.path.isfile(src):
        return os.path.getsize(src)
    size = 0
    for base, folders, files in os.walk(src):
        size += sum(os.path.getsize(os.path.join(base, f)) for f in files)
    return size


def unbuffer_stdout():
    """
    Make stdout stream unbuffered, so that ``print`` appear in e.g. logs at
    once rather than who knows when.

    :return: None
    """
    class UnbufferedStream(object):
        """
        Wrapper class for stream
        """
        def __init__(self, stream):
            self.stream = stream

        def write(self, data):
            self.stream.write(data)
            self.stream.flush()

        def __getattr__(self, attr):
            return getattr(self.stream, attr)

    # real ``stdout`` is kept in sys.__stdout__
    sys.stdout = UnbufferedStream(sys.stdout)


def format_tdelta(tdelta):
    """
    Convert seconds to human friendly string.

    :param tdelta: seconds
    :type tdelta: float
    :return: human friendly string
    :rtype: str
    """
    if tdelta >= 60:
        tdelta_s = str(timedelta(seconds=round(tdelta)))
    else:
        tdelta_s = '%.2f sec' % tdelta
    return tdelta_s


def log_info(msg):
    """
    Log a message with current date and time to stdout.
    """
    _log_with_timestamp(msg, sys.stdout)


def log_warning(msg):
    """Log a message with current date and time to stderr."""
    _log_with_timestamp(msg, sys.stderr)


class UTC(tzinfo):
    """tzinfo subclass for UTC"""
    ZERO = timedelta(0)

    def utcoffset(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return self.ZERO

utc_tz = UTC()


def _log_with_timestamp(msg, stream):
    # ``time.timezone`` stores offset to UTC in seconds
    utcnow = datetime.utcnow().replace(tzinfo=utc_tz)
    stream.write('{} - {}\n'.format(utcnow.strftime('%Y-%m-%d %H:%M:%S %Z'),
                                    msg))


def sort_file(path, save_path=None):
    if save_path is None:
        save_path = path
    if path.endswith('.gz'):
        command = 'gunzip -c "%s" | LC_ALL=C sort --output="%s"' % (path, save_path)
    else:
        command = 'LC_ALL=C sort "%s" --output="%s"' % (path, save_path)
    check_call(command, shell=True)


def normalize_contig_name(contig_name):
    """
    Returns normalized contig name. If normalized name is empty string return CHROMOSOME
    This function has java implementation in GenomeInterval. Both must return same result.

    This is used in current realization. Need to discuss to avoid this.
    One of possible solution:

        - Not normalize in reference genome
        - Add check for bed files: if contig in BED file can't be normilized to one of Reference genome contgs: fail.

    :type contig_name: str
    :param contig_name: raw name of contig
    """
    contig_name_normalized = contig_name.upper().replace('CHROMOSOME', '').replace('CHROM', '').replace('CHR', '').strip()
    return contig_name_normalized or contig_name


def get_script(name):
    """
    Returns path to script located in application script directory.

    :param name: name of the script
    :type name: str
    :return: path to script
    :rtype: str
    """
    directory = os.path.dirname(sys.argv[0])
    return os.path.join(directory, name)


class DumpData(object):
    def __init__(self):
        self.format = []
        self.data = []
        self.size = 0

    def _put_number(self, val, fmt):
        bytes_number = struct.calcsize(fmt)
        mask = ~(-1 << (bytes_number * 8))
        self.format.append(fmt)
        self.data.append(val & mask)
        self.size += bytes_number

    def _put(self, val, fmt):
        self.format.append(fmt)
        self.data.append(val)
        self.size += struct.calcsize(fmt)

    def put_int(self, val):
        self._put_number(val, 'I')

    def put_long(self, val):
        self._put_number(val, 'Q')

    def put_byte(self, val):
        self._put_number(val, 'B')

    def put_fixed_text(self, val, length):
        self._put(val, '%ss' % length)

    def put_text(self, val):
        length = len(val)
        if length > 255:
            length = 255
            val = val[:255]

        self.put_byte(length)
        self._put(val, '%ss' % length)

    def put_float(self, val):
        self._put(val, 'f')

    def to_binary(self):
        return struct.pack(">%s" % "".join(self.format), *self.data)

    def __str__(self):
        step = 4
        return ', '.join('%s: %s' % item for item in zip(self.format[:step], self.data[:step]))

    # TODO: return size of data written + remove self.size field?
    def dump_to_file(self, fs):
        fs.write(self.to_binary())


UNITS = ('B', 'KB', 'MB', 'GB', 'TB')


def _determine_units(num, step=0):
    """Finds the best unit and number to display size."""
    if num < 1000 or step >= len(UNITS) - 1:
        return num, step
    else:
        return _determine_units(int(num / 1000), step+1)


def prettify_size(size):
    """Prettyformats size."""
    num, unit_no = _determine_units(size)
    return '%s %s' % (num, UNITS[unit_no])


def optional_args_decorator(func):
    """
    Decorator that is used to decorate other decorators, so that they can take optional arguments and still be used
    without braces.

    :Example:

    >>> @optional_args_decorator
    >>> def decorated_decorator(function_to_decorate, optional_arguments...)
    >>>     # usual decorator code
    """
    @wraps(func)
    def wrapper(*args):
        if len(args) == 1 and callable(args[0]):
            return func(args[0])
        else:
            def actual(function_to_decorate):
                return func(function_to_decorate, *args)
            return actual
    return wrapper


@optional_args_decorator
def deprecated(func, message=''):
    """
    Decorator that prints a deprecation warning with the provided message to stderr.

    :Example:

    >>> @deprecated('use "bar" instead')
    >>> def deprecated_function():
    >>>  ...

    :param func: function to decorate
    :param message: deprecation message
    :return: wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        msg = ', ' + message if message else ''
        sys.stderr.write('WARNING: %s is deprecated%s\n' % (func.__name__, msg))
        return func(*args, **kwargs)
    return wrapper


class FormatPattern(object):
    def __init__(self, format_maps):
        """
        Format pattern is a list of format maps.

        You can specify all required formats in constructor or add them from other format pattern with ``add`` method

        :param format_maps: list of dicts
        :return:
        """
        if format_maps is None:
            format_maps = [{}]
        if not isinstance(format_maps, (list, tuple)):
            raise GenestackException('Format map should be list or tuple')
        map(self.validate, format_maps)
        self.__list = deepcopy(format_maps)

    def to_list(self):
        return self.__list

    @staticmethod
    def check_contains(pattern, item):
        if not set(pattern).issubset(item):
            return False
        return all(item[k] in value for k, value in pattern.items())

    def __contains__(self, item):
        if not isinstance(item, dict):
            raise GenestackException('Cannot check containing for not dict')
        return any(self.check_contains(pattern, item) for pattern in self.__list)

    @staticmethod
    def validate(format_map):
        if isinstance(format_map, dict):
            if all(isinstance(k, basestring) and isinstance(v, (list, tuple)) for k, v in format_map.items()):
                return
        message = 'Incorrect formats schema, expect dict(str:[str, ...], ...) got: %s'
        raise GenestackException(message % format_map)

    def __repr__(self):
        items_as_string = ['; '.join(['%s: %s' % (k, '|'.join(v)) for k, v in sorted(x.items())]) for x in self.__list]
        return 'Patterns %s' % ', '. join('%s) %s' % x for x in enumerate(items_as_string, start=1))

    def add(self, format_pattern):
        """Add other format patterns."""
        if not isinstance(format_pattern, self.__class__):
            raise GenestackException('Cannot add "%s" to format pattern' % type(format_pattern))
        self.__list.extend(format_pattern.to_list())


@deprecated('use "compression.gzip_file" instead')
def gzip_file(path, dest_folder=None):
    from compression import gzip_file
    return gzip_file(path, dest_folder=dest_folder)


@deprecated('use "compression.decompress_file" instead')
def decompress_file(path, dest_folder=None):
    from compression import decompress_file
    return decompress_file(path, dest_folder=dest_folder)


def validate_type(value, value_type, accept_none=False):
    """
    Validates a value against given types.

    :param value: value to validate
    :type value: object
    :param value_type: types to validate against
    :type value_type: class-or-type-or-tuple
    :param accept_none: indicates whether None value is acceptable.
        Providing None with accept_none=True will not raise an exception
    :type accept_none: bool
    :return: None, if validation was successful
    :raise GenestackException: if validation was unsuccessful
    """
    if accept_none and value is None:
        return
    if not isinstance(value, value_type):
        raise GenestackException('Parameter must be of type %s, not %s' % (value_type, type(value)))


def get_java_tool(jar_name):
    """
    Returns path to the executable jar from the 'tools' folder, specified by the given name.

    :param jar_name: name of the tool
    :type jar_name: str
    :return: path to the tool
    :rtype: str
    """
    return os.path.join(environment.TASK_LIBRARY_ROOT, 'tools', '%s.jar' % jar_name)


def run_java_tool(tool, *args):
    """
    Runs the java tool with the provided path and parameters and logs the process.

    :param tool: path to the java tool
    :type tool: str
    :param args: tool arguments
    :type args: list[str]
    """
    tool_name = os.path.basename(os.path.normpath(tool))
    start_msg = 'Start %s' % tool_name
    log_info(start_msg)
    log_warning(start_msg)
    start_time = time.time()

    params = ['java', '-jar', tool]
    params.extend(args)
    subprocess.check_call(params)

    tdelta = format_tdelta(time.time() - start_time)
    exit_msg = 'Finish %s in %s' % (tool_name, tdelta)
    log_info(exit_msg)
    log_warning(exit_msg)


def truncate_sequence_str(sequence, limit=10):
    """
    Return string representation of the sequence,
    if sequence have more elements than limit, truncate output and print total number.

    >>> truncate_sequence_str(['a', 'b', 'c'], limit=1)
    ['a', ... and 2 more]

    :param sequence: sequence to print
    :type sequence: list|tuple|set|frozenset|dict
    :param limit: max number of items to print
    :type limit: int

    :return: None
    """
    delimiter = ', '

    # convert types and select proper braces
    # set -> sorted list
    # dict -> list of items

    if isinstance(sequence, list):
        braces = '[]'
    elif isinstance(sequence, (set, frozenset)):
        sequence = sorted(sequence)
        braces = '{}'
    elif isinstance(sequence, dict):
        sequence = sorted(sequence.items())
        braces = '[]'
    else:
        braces = '()'

    size = len(sequence)
    if size > limit:
        suffix = '%s... and %s more' % (delimiter, size - limit)
    else:
        suffix = ''

    result = [
        braces[0],
        delimiter.join(repr(x) for x in sequence[:limit]),
        suffix,
        braces[1]
    ]
    return ''.join(result)


def get_unique_name(output):
    """
    Returns path to the new unique file name if output already exists.

    :param output: path
    :type output: str
    :return: path to the new unique file name if output is already exists
    :rtype: str
    """
    if os.path.exists(output):
        folder, basename = os.path.split(output)
        descriptor, output = tempfile.mkstemp(suffix='_%s' % basename, prefix='', dir=folder)
        os.close(descriptor)
    return output
