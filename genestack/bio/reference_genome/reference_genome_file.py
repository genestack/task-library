# -*- coding: utf-8 -*-

from pprint import pformat

from genestack.bio import bio_meta_keys
from genestack.bio.genome_query import GenomeQuery
from genestack.bio.annotation_utils import GTF, AVAILABLE_ANNOTATION_FORMATS
from genestack.compression import UNCOMPRESSED, AVAILABLE_COMPRESSIONS, decompress_file
from genestack.core_files.genestack_file import File
from genestack.genestack_exceptions import GenestackException
from genestack.metainfo import Metainfo
from genestack.utils import log_info, to_list, FormatPattern, deprecated


class ReferenceGenome(File):
    """
    This class represents a reference genome file.

    Required keys:
        - :py:attr:`~genestack.bio.BED.SEQUENCE_LOCATION` - key to store sequencing files.
          One ore more fasta files each with one or more contigs can be stored here.
        - :py:attr:`~genestack.bio.BED.ANNOTATIONS_LOCATION` - key to store GTF annotation.
    """

    INTERFACE_NAME = 'com.genestack.bio.files.IReferenceGenome'

    SEQUENCE_LOCATION = 'genestack.location:sequence'
    ANNOTATIONS_LOCATION = 'genestack.location:annotations'

    # @Deprecated, use Metainfo.SOURCE_DATA
    # Deprecated in 0.44.0, will be removed in 0.47.0
    SOURCE_KEY = Metainfo.SOURCE_DATA

    class Key:
        ANNOTATION_FORMAT = 'annotation_format'
        COMPRESSION = 'compression'

    def get_sequence_files(self, working_dir=None, decompressed=False):
        """
        GET sequence files from storage, returns list of their paths.

        :param working_dir: directory to copy files, default is current working directory
        :type working_dir: str
        :param decompressed: whether files should be decompressed after downloading
        :type decompressed: bool
        :rtype: list[str]
        """
        units = self.GET(self.SEQUENCE_LOCATION, working_dir=working_dir)
        all_files = [p for x in units for p in x.files]
        if decompressed:
            all_files = [decompress_file(f, working_dir) for f in all_files]
            log_info('Files are decompressed: %s\n' % ', '.join('"%s"' % x for x in all_files))
        return all_files

    def get_annotation_with_format(self, working_dir=None, format_pattern=None,
                                   annotation_formats=None, compressions=None):
        """
        Return annotation path in specified format, or raise error if it is not possible.

        :param working_dir: directory to copy files, default is current working directory
        :type working_dir: str
        :param format_pattern: format pattern
        :type format_pattern: :py:class:`~genestack.utils.FormatPattern`
        :param annotation_formats: expected annotation_formats, as single constant or list of possible constants,
                blank means list of all possible formats
        :type annotation_formats: str | [str]
        :param compressions: expected compression, as single constant or list of possible constants,
                blank means list of all possible compressions
        :type compressions: str | [str]
        :returns: tuple path and annotation format
        :rtype: (str, dict[str,str])
        """
        if format_pattern and any([compressions, annotation_formats]):
            raise GenestackException(
                'Arguments "compressions" and "annotation_formats"'
                ' cannot be combined with "format_pattern"')
        if not format_pattern:
            format_pattern = self.compose_format_pattern(compressions=compressions,
                                                         annotation_formats=annotation_formats)
        units = self.GET(self.ANNOTATIONS_LOCATION, working_dir=working_dir,
                         format_pattern=format_pattern)
        fmt = units[0].format
        fmt = {
            ReferenceGenome.Key.ANNOTATION_FORMAT: fmt[ReferenceGenome.Key.ANNOTATION_FORMAT],
            ReferenceGenome.Key.COMPRESSION: fmt[ReferenceGenome.Key.COMPRESSION]
        }
        return units[0].get_first_file(), fmt

    @deprecated('Use '
                'path, _ = get_annotation_with_format('
                'compression=UNCOMPRESSED, annotation_format=GTF) '
                'instead')
    def get_annotation_file(self, working_dir=None, decompressed=False):
        """
        GET annotation file from storage in GTF format, returns its path.
        This method always unpacks the annotation. `decompressed` argument is deprecated.
        This is not breaking changes since decompressed=False does not guaranty that
        you will get compressed file, it just return file as it is stored in storage.

        If you need other format or specific compression type, use :py:meth:`~get_annotation_with_format`

        :param working_dir: directory to copy files, default is current working directory
        :type working_dir: str
        :param decompressed: ignored, (will always behave as True)
        :type decompressed: bool
        :return: path to annotation file
        :rtype: str
        """
        annotation_file, _ = self.get_annotation_with_format(
            compressions=UNCOMPRESSED,
            annotation_formats=GTF,
            working_dir=working_dir
        )
        return annotation_file

    def get_contigs(self):
        """
        Returns map from contig names into their lengths.

        :return: map: contigName -> contigLength
        :rtype: dict[str, int]
        """
        return self.invoke('getContigs')

    def find_features(self, query):
        """
        Return features matching query.

        Response has following keys:
          - features: list of features (could be incomplete)
          - total: total number of matched features

        :param query: query
        :type query: genestack.bio.GenomeQuery
        :return:  GenomeSearchResponse as dictionary
        :rtype: dict[str, object]
        """
        if not isinstance(query, GenomeQuery):
            raise GenestackException(
                'Query is not of type GenomeQuery: %s' % type(query)
            )
        return self.invoke(
            'findFeatures',
            types=['com.genestack.bio.files.GenomeQuery'],
            values=[query.get_java_object()]
        )

    def compose_format_pattern(self, annotation_formats=None, compressions=None):
        format_map = {}
        for key, values in (
                (self.Key.COMPRESSION, compressions),
                (self.Key.ANNOTATION_FORMAT, annotation_formats),
        ):
            if values is None:
                continue
            else:
                format_map[key] = to_list(values)
        return FormatPattern([format_map])

    @classmethod
    def validate_format(cls, fmt):
        """
        Validates that format is correct.

        :param fmt: format dict
        :type fmt: dict
        :return: None
        """
        # Implementation details:
        # compressions is not enum yet, so we use old style of check here
        # this approach should not be copy-pasted to future code

        format_specification = {
            cls.Key.ANNOTATION_FORMAT: AVAILABLE_ANNOTATION_FORMATS,
        }

        if cls.Key.COMPRESSION in fmt:
            format_specification[cls.Key.COMPRESSION] = list(AVAILABLE_COMPRESSIONS)

        error_template = ('Invalid format: %s\n'
                          '  Error: %%s\n'
                          '  Format schema {key: list of allowed values}:\n%s') % (
                             fmt, pformat(format_specification, indent=4))

        if set(fmt) != set(format_specification):
            raise GenestackException(error_template % 'Keys do not match')

        for key, val in fmt.items():
            if val not in format_specification[key]:
                msg = 'Invalid value "%s" for key "%s". Expect one of %s.' % (
                val, key, format_specification[key])
                raise GenestackException(error_template % msg)
