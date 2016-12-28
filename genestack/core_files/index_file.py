# -*- coding: utf-8 -*-

from genestack.core_files.genestack_file import File


class IndexFile(File):
    """
    Java IndexFile class representation for python code
    """
    INTERFACE_NAME = 'com.genestack.api.files.IIndexFile'
    MASTER_FILE = 'genestack:master'
    EXTERNAL_DATABASE = 'genestack:external.database'

    INDEX_SCHEMA = 'genestack:index.schema'
    INDEX_NAMESPACES = 'genestack:index.namespaces'

    INDEX_COLUMNS = 'genestack:index.columns'  # TODO: remove?
