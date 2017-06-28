# -*- coding: utf-8 -*-

import os
from tempfile import mkdtemp

from genestack.bio import bio_meta_keys
from genestack.cla import CLA, get_tool, get_version, RUN
from genestack.core_files.genestack_file import File
from genestack.frontend_object import StorageUnit
from genestack.genestack_exceptions import GenestackException
from genestack.metainfo import Metainfo
from genestack.utils import get_cpu_count
from plumbum import local


class AlignedReads(File):
    """
    This class represents a BAM file.

    Required keys:
       - :py:attr:`~genestack.bio.AlignedReads.BAM_FILE_LOCATION` - key to store the physical BAM file.
       - :py:attr:`~genestack.bio.AlignedReads.BAMINDEX_FILE_LOCATION` - key to store the physical BAI (BAM index) file.

    To put data to these keys you can use :py:meth:`~genestack.bio.AlignedReads.put_bam_with_index`.
    This method will preprocess the BAM file and create an index for it.

    Optional keys:
       - :py:attr:`~genestack.bio.AlignedReads.UNMAPPED_READS_FILE_LOCATION` - key to store a physical BAM file
         containing unmapped reads (this is to accommodate for the fact that some aligners, like tophat,
         produce a separate BAM file storing the reads that could not be mapped).
         To put this file use :py:meth:`~genestack.bio.AlignedReads.put_unmapped_bam`.

       - :py:attr:`~genestack.bio.AlignedReads.FEATURES_FILE_LOCATION` - key to store physical BED files with features
         (this is to accommodate for the fact that some aligners, like tophat, can produce BED files along with aligned
         reads to annotate junctions, insertions and deletions).

       - :py:attr:`~genestack.bio.AlignedReads.TRANSCRIPT_ALIGNED_BAM_FILE_LOCATION` - key to store the physical BAM
         file containing transcriptome-aligned reads.

    """
    INTERFACE_NAME = 'com.genestack.bio.files.IAlignedReads'

    BAM_FILE_LOCATION = 'genestack.location:bamfile'
    BAMINDEX_FILE_LOCATION = 'genestack.location:baifile'

    TRANSCRIPT_ALIGNED_BAM_FILE_LOCATION = 'genestack.location:transcript-aligned-bamfile'

    UNMAPPED_READS_FILE_LOCATION = 'genestack.location:unmapped-reads'
    FEATURES_FILE_LOCATION = 'genestack.location:features-annotation'

    # @Deprecated, use Metainfo.SOURCE_DATA
    # Deprecated in 0.44.0, will be removed in 0.47.0
    SOURCE_KEY = Metainfo.SOURCE_DATA

    def get_bam_file(self, working_dir=None):
        units = self.GET(self.BAM_FILE_LOCATION, working_dir=working_dir)
        return units[0].get_first_file()

    def get_unmapped_reads_file(self, working_dir=None):
        units = self.GET(self.UNMAPPED_READS_FILE_LOCATION, working_dir=working_dir)
        return units[0].get_first_file()

    def get_index_file(self, working_dir=None):
        units = self.GET(self.BAMINDEX_FILE_LOCATION, working_dir=working_dir)
        return units[0].get_first_file()

    def get_transcript_aligned_bam_file(self, working_dir=None):
        units = self.GET(self.TRANSCRIPT_ALIGNED_BAM_FILE_LOCATION, working_dir=working_dir)
        return units[0].get_first_file()

    def get_features_annotations(self, working_dir=None):
        """
        GET files by urls stored in metainfo under FEATURES_FILE_LOCATION key
        :param working_dir: same as in GET
        :type working_dir: str
        :return: list of paths to downloaded files
        :rtype: list[str]
        """
        units = self.GET(self.FEATURES_FILE_LOCATION, working_dir=working_dir)
        return [unit[0].get_first_file() for unit in units]

    def put_unmapped_bam(self, bam_path, sort=True, remove_program_options=True):
        """
        Put unmapped BAM file.

        :param bam_path: path to existing BAM file with unmapped reads
        :type bam_path: str
        :param sort: sort the BAM file by feature name and then by coordinates. If you know that the file is already sorted, set it to ``False``
        :type sort: bool
        :param remove_program_options: removes program options from the file header. Set it to ``False`` if those have
          already been removed
        :type remove_program_options: bool
        :return: None
        """
        if not os.path.exists(bam_path):
            raise GenestackException("Path does not points to file: %s" % bam_path)
        if remove_program_options:
            bam_path = self.remove_program_options(bam_path)
        if sort:
            bam_path = self.sort_by_name(bam_path)
            bam_path = self.sort_by_coordinate(bam_path)
        self.PUT(self.UNMAPPED_READS_FILE_LOCATION, StorageUnit(bam_path))

    def put_bam_with_index(self, bam_path, create_index=True, sort=True, remove_program_options=True):
        """
        PUT BAM and BAI files to storage.
        If the BAM file is absent, this method does nothing.
        If a BAI file with the same base name exists in the same folder, it is used as index.
        If the BAI file is absent and ``create_index=True``, then a new BAI file will be created.
        If the BAI file is absent and ``create_index=False``, then an exception will be raised.
        If the BAI file is absent and ``create_index=True`` and ``sort=True``, the BAM file will be sorted (first by
        feature name and then by coordinate), then indexed, before being PUT to storage.

        :param bam_path: path to BAM file
        :type bam_path: str
        :param create_index: flag indicating whether an index should be computed automatically
        :type create_index: bool
        :param sort: sort the BAM file by feature name and then by coordinates. If you know that the file is sorted, set it to ``False``
        :type sort: bool
        :param remove_program_options: removes program options from the file header. Set it to ``False`` if those have
          already been removed
        :type remove_program_options: bool
        :return: None
        """
        if not os.path.exists(bam_path):
            # TODO: maybe raise exception???
            return

        bai_path = bam_path + '.bai'
        if not os.path.exists(bai_path):
            if create_index:
                if remove_program_options:
                    bam_path = self.remove_program_options(bam_path)
                if sort:
                    bam_path = self.sort_by_name(bam_path)
                    bam_path = self.sort_by_coordinate(bam_path)
                bai_path = self.make_index(bam_path)
            else:
                raise GenestackException(
                    "Cannot put without .bai file, create file manually or set create_index=True; bam path: %s" %
                    bam_path)

        self.PUT(self.BAM_FILE_LOCATION, StorageUnit(bam_path))
        self.PUT(self.BAMINDEX_FILE_LOCATION, StorageUnit(bai_path))

    def __get_sort_order(self, path):
        samtools = CLA(self).get_tool('samtools', 'samtools')
        output = samtools.output(['view -H', path, '| grep ^@HD || true'])  # grep return error status if nothing match.
        for line in output.split('\n'):
            for item in line.split('\t'):
                if item.startswith('SO:'):
                    return item.split(':')[-1]

    def remove_program_options(self, bam_path, remove=True):
        tmp_folder = mkdtemp(prefix="without_options_", dir=os.getcwd())
        temp_file = os.path.join(tmp_folder, 'without_options.bam')
        # os.rename(bam_path, temp_file)
        samtools = get_tool('samtools', 'samtools')

        # newer samtools, by default, add 'PG' header info when you call 're-header' command
        # the '--no-PG' option is not available in older samtools

        command = samtools['view', '-H', bam_path] | local['grep']['-v', '^@PG']
        if get_version('samtools').startswith('1.3'):
            command = command | samtools['reheader', '--no-PG', '-', bam_path]
        else:
            command = command | samtools['reheader', '-', bam_path]
        command & RUN(stdout=temp_file)

        if remove:
            os.remove(bam_path)
        return temp_file

    def __sort(self, bam_path, by_name, remove):
        samtools = get_tool('samtools', 'samtools')
        version = get_version('samtools')
        # ignore sort headers for samtools 0.1.18
        ignore_sort_headers = version == '0.1.18'
        # samtools version 0.1.18 and 0.1.19 does not support sorting with threads
        use_threads = not version.startswith('0.1.')
        if not ignore_sort_headers:
            sort_order = self.__get_sort_order(bam_path)
            if by_name and sort_order == 'name' or not by_name and sort_order == 'coordinate':
                return bam_path
        tmp_folder = mkdtemp(prefix="sorted_bam", dir=os.getcwd())
        sorted_bam_prefix = os.path.join(tmp_folder,
                                         'sorted_by_name' if by_name else 'sorted_by_coord')
        args = ['sort']

        if use_threads:
            args.extend(['-@', str(get_cpu_count())])
        if by_name:
            args.append('-n')
        if version == '1.3.1':
            args.extend([bam_path, '-o', sorted_bam_prefix + '.bam'])
        else:
            args.extend([bam_path, sorted_bam_prefix])
        samtools[args] & RUN
        if remove:
            os.remove(bam_path)
        return sorted_bam_prefix + '.bam'

    def sort_by_name(self, bam_path, remove=True):
        return self.__sort(bam_path, True, remove)

    def sort_by_coordinate(self, bam_path, remove=True):
        return self.__sort(bam_path, False, remove)

    def make_index(self, bam_path):
        get_tool('samtools', 'samtools')['index', bam_path] & RUN
        bai_path = bam_path + '.bai'
        if not os.path.exists(bai_path):
            raise GenestackException('Index was not created for %s' % bam_path)
        return bai_path
