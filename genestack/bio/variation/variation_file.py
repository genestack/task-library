# -*- coding: utf-8 -*-
import os
import subprocess

from genestack import ReportFile, GenestackException, StorageUnit, utils
from genestack.cla import get_tool, RUN, OUTPUT
from genestack.compression import decompress_file, gzip_file
from genestack.metainfo import Metainfo


class Variation(ReportFile):
    """
    This class represents a genomic variants file.

    Required keys:
        - :py:attr:`~genestack.bio.Variation.DATA_LOCATION` - key to store the physical variation file.

    To put data to this key you can use :py:meth:`~genestack.bio.Variation.put_vcf_with_index`
    it will create all required indexes.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IVariationFile'

    DATA_LOCATION = Metainfo.DATA_LOCATION
    REFERENCE_GENOME_KEY = 'genestack.bio:referenceGenome'
    REFERENCE_GENOME = 'genestack.bio:referenceGenome'
    SOURCE_KEY = Metainfo.SOURCE_DATA_KEY
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
        :type path: str
        :rtype: None
        """
        compressed_data_file_path = self.__create_compressed_data_file(path)
        tabix = self.__create_tabix(compressed_data_file_path)
        num_of_variants = self.__get_number_of_variants(compressed_data_file_path)
        index = self.__create_index(compressed_data_file_path, num_of_variants)

        self.put_data_file(compressed_data_file_path)
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
        Creates an archive that contains the given variation file using BGZIP compression. Automatically converts
        BCF to VCF (because tabix doesn't support it).

        :param data_file_path: path to the variation file
        :type data_file_path: str
        :return: path to the compressed archive
        :rtype: str
        """
        if data_file_path.endswith('.bcf'):
            compressed_file = data_file_path[:-4] + '.vcf.bgz'
            bcftools = get_tool('bcftools', 'bcftools')
            bcftools['convert', '-Oz', data_file_path] & RUN(stdout=compressed_file)
        else:
            compressed_file = data_file_path + '.bgz'
            bgzip = get_tool('bcftools', 'bgzip')
            bgzip['-c', data_file_path] & RUN(stdout=compressed_file)
        return compressed_file

    def __create_tabix(self, data_file_path):
        """
        Creates the TABIX index for the given variation file.
        NOTE: the variation file MUST be compressed using BGZIP compression!

        :param data_file_path: path to the compressed variation file
        :type data_file_path: str
        :return: path to the built index
        :rtype: str
        """
        get_tool('bcftools', 'bcftools')['index', '-t', data_file_path] & RUN
        return data_file_path + '.tbi'

    def __get_number_of_variants(self, data_file_path):
        bcftools = get_tool('bcftools', 'bcftools')
        return (bcftools['index', '-n', data_file_path] & OUTPUT).strip()

    @staticmethod
    def __create_index(data_file_path, num_of_variants):
        """
        Indexes the given variation file to enable feature searching.
        NOTE: the variation file MUST be compressed using BGZIP compression!

        :param data_file_path: path to the compressed variation file
        :type data_file_path: str
        :return: path to the index archive
        :rtype: str
        """
        indexer = utils.get_java_tool('genestack-vcf-indexer')
        index_folder = os.path.join(os.path.dirname(data_file_path), data_file_path + '.index')

        cmd_args = [indexer, '-d', index_folder, '-n', num_of_variants, data_file_path]
        utils.run_java_tool(indexer, *cmd_args)

        # compress the index folder as a single ZIP archive
        archive_name = index_folder + '.zip'
        subprocess.check_call(['zip', '-rjq', archive_name, index_folder])

        return archive_name
