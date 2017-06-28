# -*- coding: utf-8 -*-

from genestack.compression import gzip_file
from genestack.core_files.genestack_file import File
from genestack.frontend_object import StorageUnit
from genestack.genestack_exceptions import GenestackException
from genestack.metainfo import Metainfo, IntegerValue
from genestack.utils import opener


class MappedReadsCounts(File):
    """
    This class represents a mapped reads count.

    Required keys:
        - :py:attr:`~genestack.bio.MappedReadsCounts.DATA_LOCATION` - key to store the physical file with mapped reads count.

    To put data to this key you can use :py:meth:`~genestack.bio.MappedReadsCounts.put_counts`.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IHTSeqCounts'

    DATA_LOCATION = 'genestack.location:data'

    # @Deprecated, use Metainfo.SOURCE_DATA
    # Deprecated in 0.44.0, will be removed in 0.47.0
    SOURCE_KEY = Metainfo.SOURCE_DATA

    HTSEQ_COUNT_NO_FEATURE = 'genestack.bio.htseqCount:no_feature'
    HTSEQ_COUNT_AMBIGUOUS = 'genestack.bio.htseqCount:ambiguous'
    HTSEQ_COUNT_TOO_LOW_AQUALITY = 'genestack.bio.htseqCount:too_low_aQual'
    HTSEQ_COUNT_ALIGNMENT_NOT_UNIQUE = 'genestack.bio.htseqCount:alignment_not_unique'
    HTSEQ_COUNT_NOT_ALIGNED = 'genestack.bio.htseqCount:not_aligned'

    # HTSeq format 0.5.4 and newer requires to use double underscore before key
    SPECIAL_COUNTERS_MAP = {
        'no_feature': HTSEQ_COUNT_NO_FEATURE,
        '__no_feature': HTSEQ_COUNT_NO_FEATURE,
        'ambiguous': HTSEQ_COUNT_AMBIGUOUS,
        '__ambiguous': HTSEQ_COUNT_AMBIGUOUS,
        'too_low_aQual': HTSEQ_COUNT_TOO_LOW_AQUALITY,
        '__too_low_aQual': HTSEQ_COUNT_TOO_LOW_AQUALITY,
        'alignment_not_unique': HTSEQ_COUNT_ALIGNMENT_NOT_UNIQUE,
        '__alignment_not_unique': HTSEQ_COUNT_ALIGNMENT_NOT_UNIQUE,
        'not_aligned': HTSEQ_COUNT_NOT_ALIGNED,
        '__not_aligned': HTSEQ_COUNT_NOT_ALIGNED
    }

    def get_counts(self, working_dir=None):
        storage_units = self.GET(self.DATA_LOCATION, working_dir=working_dir)
        return storage_units[0].get_first_file()

    def put_counts(self, path):
        self.PUT(self.DATA_LOCATION, StorageUnit(gzip_file(path, remove_source=False)))
        self.__index_file(path)

    def __index_file(self, path):
        with opener(path) as f:
            for line in f:
                line = line.strip()
                try:
                    feature, value = line.split('\t')
                    # Check that value can be parsed as an integer
                    value = int(value)
                except ValueError:
                    raise GenestackException('Bad line format: "%s"' % line)
                if feature in self.SPECIAL_COUNTERS_MAP.keys():
                    self.add_metainfo_value(self.SPECIAL_COUNTERS_MAP[feature], IntegerValue(value))
