# -*- coding: utf-8 -*-
import os
import pipes
import subprocess
import time

from genestack import ReportFile, GenestackException, StorageUnit, environment, utils
from genestack.cla import CLA
from genestack.compression import decompress_file, gzip_file


class Variation(ReportFile):
    """
    This class represents a genomic variants file.

    Required keys:
        - :py:attr:`~genestack.bio.Variation.DATA_LOCATION` - key to store the physical variation file.

    To put data to this key you can use :py:meth:`~genestack.bio.Variation.put_vcf_with_index`
    it will create all required indexes.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IVariationFile'

    DATA_LOCATION = 'genestack.location:data'
    REFERENCE_GENOME_KEY = 'genestack.bio:referenceGenome'
    SOURCE_KEY = 'genestack.bio:sourceData'
    INDEX_LOCATION = 'genestack.location:index'
    TABIX_LOCATION = 'genestack.location:tabix'

    def put_data_file(self, path):
        self.PUT(self.DATA_LOCATION, StorageUnit(gzip_file(path, remove_source=False)))

    def put_tabix_file(self, path):
        self.PUT(self.TABIX_LOCATION, StorageUnit(path))

    def put_index(self, path):
        self.PUT(self.INDEX_LOCATION, StorageUnit(path))

    def put_vcf_with_index(self, path):
        """
        PUTs and indexes the given variation file.

        :param path: path to the variation file
        :type path: basestring
        :rtype: None
        """
        compressed_data_file = self.__create_compressed_data_file(path)
        tabix = self.__create_tabix(compressed_data_file)
        index = self.__create_index(compressed_data_file)

        self.put_data_file(compressed_data_file)
        self.put_tabix_file(tabix)
        self.put_index(index)

    def get_data_file(self, working_dir=None, decompressed=True):
        units = self.GET(self.DATA_LOCATION, working_dir=working_dir)
        if len(units) == 0:
            raise GenestackException('Unable to get VCF files')
        if len(units) != 1:
            raise GenestackException('Too many VCF files were fetched: %s files' % len(units))

        data_file = units[0].get_first_file()
        if decompressed:
            return decompress_file(data_file, working_dir)
        return data_file

    def __create_compressed_data_file(self, data_file_path):
        """
        Creates an archive that contains the given variation file using BGZIP compression.

        :param data_file_path: path to the variation file
        :type data_file_path: basestring
        :return: path to the compressed archive
        :rtype: basestring
        """
        compressed_file = data_file_path + '.bgz'
        CLA(self).get_tool('tabix', 'bgzip').run(['-c', pipes.quote(data_file_path), '>', pipes.quote(compressed_file)])
        return compressed_file

    def __create_tabix(self, data_file_path):
        """
        Creates the TABIX index for the given variation file.
        NOTE: the variation file MUST be compressed using BGZIP compression!

        :param data_file_path: path to the compressed variation file
        :type data_file_path: basestring
        :return: path to the built index
        :rtype: basestring
        """
        index_file = data_file_path + '.tbi'
        CLA(self).get_tool('tabix', 'tabix').run(['-p', 'vcf', pipes.quote(data_file_path)])
        return index_file

    def __create_index(self, data_file_path):
        """
        Indexes the given variation file to enable feature searching.
        NOTE: the variation file MUST be compressed using BGZIP compression!

        :param data_file_path: path to the compressed variation file
        :type data_file_path: basestring
        :return: path to the index archive
        :rtype: basestring
        """
        indexer = os.path.join(environment.TASK_LIBRARY_ROOT, 'tools', 'genestack-vcf-indexer.jar')
        index_folder = os.path.join(os.path.dirname(data_file_path), data_file_path + '.index')

        start_msg = 'Start vcf indexer'
        utils.log_info(start_msg)
        utils.log_warning(start_msg)
        start_time = time.time()

        subprocess.check_call(['java', '-jar', indexer, '-d', index_folder, data_file_path])

        tdelta = utils.format_tdelta(time.time() - start_time)
        exit_msg = 'Finish vcf indexer in %s' % tdelta
        utils.log_info(exit_msg)
        utils.log_warning(exit_msg)

        # compress the index folder as a single ZIP archive
        archive_name = index_folder + '.zip'
        subprocess.check_call(['zip', '-rjq', archive_name, index_folder])

        return archive_name
