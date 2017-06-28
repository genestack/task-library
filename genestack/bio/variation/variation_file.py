# -*- coding: utf-8 -*-
import os
import subprocess

from genestack import compression
from genestack import utils
from genestack.bio import bio_meta_keys
from genestack.cla import get_tool, get_tool_path, RUN, OUTPUT
from genestack.compression import decompress_file, gzip_file
from genestack.core_files.report_file import ReportFile
from genestack.frontend_object import StorageUnit
from genestack.genestack_exceptions import GenestackException
from genestack.metainfo import Metainfo

import time

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
    # @Deprecated, use Metainfo.SOURCE_DATA
    # Deprecated in 0.44.0, will be removed in 0.47.0
    SOURCE_KEY = Metainfo.SOURCE_DATA
    INDEX_LOCATION = 'genestack.location:index'
    TABIX_LOCATION = 'genestack.location:tabix'
    GENOTYPES_LOCATION = 'genestack.location:genotypes'


    def put_data_file(self, path):
        self.PUT(self.DATA_LOCATION, StorageUnit(gzip_file(path, remove_source=False)))

    def put_filtered_file(self, path):
        self.PUT(self.FILTERED_LOCATION, StorageUnit(path))

    def put_tabix_file(self, path):
        self.PUT(self.TABIX_LOCATION, StorageUnit(path))

    def put_index(self, path):
        self.PUT(self.INDEX_LOCATION, StorageUnit(path))

    def put_genotypes(self, path):
        self.PUT(self.GENOTYPES_LOCATION, StorageUnit(path))

    def put_vcf_with_index(self, path):
        """
        PUTs and indexes the given variation file.

        :param path: path to the variation file
        :type path: str
        :rtype: None
        """
        cutter = utils.get_java_tool('genestack-vcf-samples-cutter')
        method = compression.get_file_compression(path)
        compressed_data_file_path = path + '.filtered.bgz'
        temp_samples_headers = path + '.temp'
        genotypes_file = path + '.genotypes'
        index_folder = os.path.join(os.path.dirname(compressed_data_file_path), compressed_data_file_path + '.index')

        from plumbum.cmd import gunzip, java
        bgzip = get_tool('bcftools', 'bgzip')["-c"]

        cutter_arguments = ["-jar", cutter, "-d", index_folder, "-s", temp_samples_headers]
        if method == compression.UNCOMPRESSED:
            cutter_arguments.extend(["-i", path])
            first_pass_cmd = java[cutter_arguments]
        elif method == compression.GZIP:
            first_pass_cmd = gunzip["-c", path] | java[cutter_arguments]
        else:
            raise(GenestackException("vcf file must be gziped on uncompressed"))
        (first_pass_cmd | bgzip) & RUN(stdout=compressed_data_file_path)

        cutter_arguments.extend(["-g", genotypes_file])
        second_pass_cmd = java[cutter_arguments]
        if method != compression.UNCOMPRESSED:
            second_pass_cmd = gunzip["-c", path] | second_pass_cmd
        second_pass_cmd  & RUN

        tabix = self.__create_tabix(compressed_data_file_path)
        num_of_variants = self.__get_number_of_variants(compressed_data_file_path)
        index = self.__create_index(compressed_data_file_path, num_of_variants)

        self.put_data_file(compressed_data_file_path)
        self.put_tabix_file(tabix)
        self.put_index(index)
        self.put_genotypes(genotypes_file)

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
