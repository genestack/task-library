# -*- coding: utf-8 -*-

import json
import os
from tempfile import mkdtemp

from genestack.compression import get_compression, AVAILABLE_COMPRESSIONS, UNCOMPRESSED, gzip_file
from genestack.core_files.genestack_file import File
from genestack.frontend_object import StorageUnit
from genestack.genestack_exceptions import GenestackException
from genestack.metainfo import BooleanValue, Metainfo
from genestack.utils import is_empty_file, to_list, FormatPattern, log_warning


class UnalignedReads(File):
    """
    This class represents an unaligned reads file.

    Format specification:
    Unaligned reads can be stored in different formats.
    Call the ``get_reads`` method to retrieve the reads in the format of your choice.
    NB: not all possible conversions are implemented.


    - ``Format``(key format for format):
      - ``PHRED33``
      - ``PHRED64``
      - ``FASTA_QUAL``
      - ``SRA``
      - ``SFF``
      - ``FAST5``
    - `Space`
      - ``BASESPACE``
      - ``COLORSPACE``
    - ``Type``
      - ``SINGLE``
      - ``PAIRED``
      - ``PAIRED_WITH_UNPAIRED``
    - ``Compression`` see keys at ``compression_utils.Compression``


    Required keys:
        - :py:attr:`~genestack.bio.UnalignedReads.READS_LOCATION` - key to store the physical reads file(s).

    To put data to this key you can use the :py:meth:`~genestack.bio.UnalignedReads.put_reads` method.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IUnalignedReads'

    READS_LOCATION = 'genestack.location:reads'
    HAS_PAIRED_READS = "genestack.bio:hasPairedReads"
    SOURCE_KEY = Metainfo.SOURCE_DATA_KEY

    class Key(object):
        SPACE = 'space'
        FORMAT = 'format'
        TYPE = 'type'
        COMPRESSION = 'compression'

    class Space(object):
        BASESPACE = 'basespace'
        COLORSPACE = 'colorspace'

    class Format(object):
        PHRED33 = 'phred33'
        PHRED64 = 'phred64'
        FASTA_QUAL = 'fasta-qual'
        SRA = 'sra'
        SFF = 'sff'
        FAST5 = 'fast5'

    class Type(object):
        SINGLE = 'single'
        PAIRED = 'paired'
        PAIRED_WITH_UNPAIRED = 'paired-with-unpaired'

    # TODO check usages convert and convert to tuple, we send this values to server and serialize them as json
    ALL_TYPES = frozenset((Type.SINGLE, Type.PAIRED, Type.PAIRED_WITH_UNPAIRED))
    ALL_FORMATS = frozenset((Format.FASTA_QUAL, Format.PHRED33, Format.PHRED64, Format.SFF, Format.SRA, Format.FAST5))
    ALL_SPACES = frozenset((Space.BASESPACE, Space.COLORSPACE))
    ALL_COMPRESSIONS = frozenset(AVAILABLE_COMPRESSIONS)

    @staticmethod
    def compose_format_map(space, file_format, file_type):
        return {UnalignedReads.Key.SPACE: space,
                UnalignedReads.Key.FORMAT: file_format,
                UnalignedReads.Key.TYPE: file_type,
                }

    @classmethod
    def validate_format(cls, fmt):
        """
        Validates that format is correct.

        :param fmt: format dict
        :type fmt: dict
        :return: None
        """
        format_specification = {
            cls.Key.SPACE: list(cls.ALL_SPACES),
            cls.Key.FORMAT: list(cls.ALL_FORMATS),
            cls.Key.TYPE: list(cls.ALL_TYPES)
        }

        if cls.Key.COMPRESSION in fmt:
            format_specification[cls.Key.COMPRESSION] = list(cls.ALL_COMPRESSIONS)

        error_template = ('Invalid format: %s\n'
                          '  Error: %%s\n'
                          '  Format schema {key: list of allowed values}:\n%s') % (
            fmt, json.dumps(format_specification, indent=4))

        if set(fmt) != set(format_specification):
            raise GenestackException(error_template % 'Keys do not match')

        for key, val in fmt.items():
            if val not in format_specification[key]:
                msg = 'Invalid value "%s" for key "%s". Expected one of: %s' % (val, key, format_specification[key])
                raise GenestackException(error_template % msg)

    # def isBasespaceNotColorspace(self):
    #        return True or False

    @classmethod
    def _check_files_match_format(cls, files, file_format):
        """
        Check that format matches files.

        :param files: list of files
        :param file_format: format map of the file
        :return: None
        """
        if not file_format:
            raise GenestackException('Format required')
        if not files:
            raise GenestackException('List of files required')
        cls.validate_format(file_format)
        fmt = file_format[cls.Key.FORMAT]
        tp = file_format[cls.Key.TYPE]
        expected_count = {
            cls.Type.SINGLE: 1,
            cls.Type.PAIRED: 2,
            cls.Type.PAIRED_WITH_UNPAIRED: 3,
        }[tp]

        if fmt in (cls.Format.FAST5, cls.Format.SFF, cls.Format.SRA):
            if len(files) != 1:
                raise GenestackException('"%s" format expect 1 file, got: %s' % (fmt, len(files)))
        elif fmt in (cls.Format.PHRED33, cls.Format.PHRED64, cls.Format.FASTA_QUAL):
            expected_count *= (2 if fmt == cls.Format.FASTA_QUAL else 1)
            if expected_count != len(files):
                msg = 'Expected %s files for format "%s" and type "%s", got %s'
                raise GenestackException(msg % (expected_count, fmt, tp, len(files)))
        else:
            raise GenestackException('Unknown format: %s' % fmt)

    def put_reads(self, files, file_format):
        """
        Put files to storage.

        :param files: list of files
        :type files: list
        :param file_format: format of files
        :type file_format: dict
        """
        self._check_files_match_format(files, file_format)
        has_paired = file_format[UnalignedReads.Key.TYPE] in (UnalignedReads.Type.PAIRED,
                                                              UnalignedReads.Type.PAIRED_WITH_UNPAIRED)
        self.replace_metainfo_value(self.HAS_PAIRED_READS, BooleanValue(has_paired))
        # check only for fastq files
        if file_format[UnalignedReads.Key.FORMAT] in [UnalignedReads.Format.PHRED33, UnalignedReads.Format.PHRED64]:
            for file_obj, mate_name in zip(files, ('First', 'Second', 'Unpaired')):
                if is_empty_file(file_obj):
                    self.add_warning('%s mate is empty.' % mate_name)

        # find compression and set it to file_format
        compression = get_compression(files)

        if compression == UNCOMPRESSED and file_format[self.Key.FORMAT] in [self.Format.PHRED33,
                                                                            self.Format.PHRED64,
                                                                            self.Format.FASTA_QUAL]:

            temp_folder = mkdtemp(prefix="gzipped", dir=os.getcwd())
            files = [gzip_file(x, dest_folder=temp_folder, remove_source=False) for x in files]
        # Remove compression key from format
        if UnalignedReads.Key.COMPRESSION in file_format:
            file_format = file_format.copy()  # do not mutate arguments
            del file_format[UnalignedReads.Key.COMPRESSION]
        self.PUT(self.READS_LOCATION, StorageUnit(files, file_format))

    @staticmethod
    def __get_items(values, main_set):
        if values == '*':
            return main_set
        if isinstance(values, basestring):
            values = [values]
        if not main_set.issuperset(values):
            log_warning('Values are not valid: %s is not subset of %s' % (values, main_set))
        return values

    def get_reads(self, format_pattern=None, compressions='*', formats='*', spaces='*', types='*',  working_dir=None):
        """
        Return tuple (list of files, format of genestack file)

        There are two ways to specify format:

          - using the ``format_pattern`` argument;
          - using some or all of the following arguments: ``compressions``, ``formats``, ``spaces``, ``types``.

        These two ways cannot be combined, i.e. when ``format_pattern``
        is present, no other format argument must be specified.
        If no format arguments are specified, the existing format will be returned.

        :param format_pattern: composed Format pattern
        :param compressions: list of possible values for compression, or '*' for all
        :param formats: list of possible values for format, or '*' for all
        :param spaces: list of possible values for space, or '*' for all
        :param types: list of possible values for type, or '*' for all
        :return: tuple: list of paths, file format
        """
        if format_pattern is not None:
            if any(x != '*' for x in (compressions, formats, types, spaces)):
                raise GenestackException(
                    'Arguments "compressions", "formats", "types", "spaces" '
                    'cannot be combined with "format_pattern"')
        else:
            format_pattern = self.compose_format_pattern(types=types, formats=formats,
                                                         spaces=spaces, compressions=compressions)
        units = self.GET(UnalignedReads.READS_LOCATION, format_pattern=format_pattern, working_dir=working_dir)
        fmt = units[0].format
        if self.Key.COMPRESSION not in fmt:
            fmt[self.Key.COMPRESSION] = get_compression(units[0].files)
        return units[0].files, units[0].format

    def compose_format_pattern(self, compressions='*', formats='*', spaces='*', types='*'):
        format_map = {}
        for key, values in (
                (self.Key.COMPRESSION, compressions),
                (self.Key.TYPE, types),
                (self.Key.FORMAT, formats),
                (self.Key.SPACE, spaces)
        ):
            if values == '*':
                continue
            else:
                format_map[key] = to_list(values)
        return FormatPattern([format_map])
