# -*- coding: utf-8 -*-
from genestack.core_files.dataset import Dataset
from genestack.core_files.genestack_file import File
from genestack.genestack_exceptions import GenestackException
from genestack.java import java_object, JAVA_ARRAY_LIST, JAVA_COLLECTION, JAVA_CLASS, JAVA_STRING
from genestack.metainfo import Metainfo
from genestack.container_file_query import ContainerFileQuery
from genestack.utils import validate_type


class FileTypeEnum(object):
    @classmethod
    def get_all_types(cls):
        return {name for name in dir(cls) if not name.startswith("_")}


class CoreFileType(FileTypeEnum):
    _CLASS_NAME = "com.genestack.api.files.CoreFileType"

    AUXILIARY_FILE = "AUXILIARY_FILE"
    FOLDER = "FOLDER"
    SEARCH_FOLDER = "SEARCH_FOLDER"
    INDEX_FILE = "INDEX_FILE"

    APPLICATION_PAGE_FILE = "APPLICATION_PAGE_FILE"
    DICTIONARY_FILE = "DICTIONARY_FILE"
    PREFERENCES_FILE = "PREFERENCES_FILE"
    RAW_FILE = "RAW_FILE"
    REPORT_FILE = "REPORT_FILE"


class BioFileType(FileTypeEnum):
    _CLASS_NAME = "com.genestack.bio.files.BioFileType"

    EXPERIMENT = "EXPERIMENT"
    REFERENCE_GENOME = "REFERENCE_GENOME"
    VARIATION_FILE = "VARIATION_FILE"
    VARIATION_FILE_NG = "VARIATION_FILE_NG"
    VARIATION_DATABASE = "VARIATION_DATABASE"
    CODON_TABLE = "CODON_TABLE"
    GO_ANNOTATION_FILE = "GO_ANNOTATION_FILE"
    HT_SEQ_COUNTS = "HT_SEQ_COUNTS"
    UNALIGNED_READS_DATA = "UNALIGNED_READS_DATA"
    BAM_FILE = "BAM_FILE"
    STUDY = "STUDY"

    ASSAY_GROUP = "ASSAY_GROUP"
    SEQUENCING_ASSAY = "SEQUENCING_ASSAY"
    MICROARRAY_ASSAY = "MICROARRAY_ASSAY"
    MICROARRAY_DATA = "MICROARRAY_DATA"

    DIFFERENTIAL_EXPRESSION_FILE = "DIFFERENTIAL_EXPRESSION_FILE"

    GENOME_BED_DATA = "GENOME_BED_DATA"
    GENOME_WIGGLE_DATA = "GENOME_WIGGLE_DATA"

    FEATURE_LIST = "FEATURE_LIST"
    GENE_EXPRESSION_SIGNATURE = "GENE_EXPRESSION_SIGNATURE"


class Folder(File):
    """
    Representation of genestack folder.
    """
    INTERFACE_NAME = 'com.genestack.api.files.IFolder'

    MAX_QUERY_PAGE_SIZE = 100

    def create_dataset(self, metainfo, child_type, children):
        """
        Creates a new dataset in this folder.

        :param metainfo:  metainfo of the file to be created
        :type metainfo: Metainfo
        :param child_type: dataset type, must be one of file interfaces
        :type child_type: basestring
        :param children: list of files to be put in to the dataset
        :type children: list[File]

        :return: Dataset object
        :rtype: Dataset
        """
        validate_type(metainfo, Metainfo)
        validate_type(child_type, basestring)
        validate_type(children, list)

        children_list = [
            java_object(child.INTERFACE_NAME, {'id': child.object_id}) for child in children
        ]

        created_file_id = self.invoke(
            'createDatasetFromSelection',
            [
                'com.genestack.api.metainfo.IMetainfo',
                JAVA_CLASS,
                JAVA_COLLECTION
            ],
            [
                java_object(
                    'com.genestack.api.metainfo.MetainfoWritable',
                    metainfo.get_java_object()
                ),
                java_object(JAVA_CLASS, child_type),
                java_object(JAVA_ARRAY_LIST, children_list)

            ]
        )['id']
        return Dataset(created_file_id)

    def create_file(self, file_type, metainfo, return_type=File):
        """
        Creates a new file in this folder.

        Parameter file_type can be one of the names from Java CoreFileType or BioFileType enumerations
        (e.g. "FOLDER", "APPLICATION_PAGE_FILE" or "EXPERIMENT", "SEQUENCING_ASSAY", "MICROARRAY_ASSAY").

        :type file_type: str
        :param metainfo: metainfo of the file to be created
        :param return_type: expected class for the created file (must be a child class of `File`)
        :return: new file object
        """
        validate_type(file_type, basestring)
        validate_type(metainfo, Metainfo)
        validate_type(return_type, type)

        file_type_enum = None
        if file_type in BioFileType.get_all_types():
            file_type_enum = BioFileType._CLASS_NAME
        elif file_type in CoreFileType.get_all_types():
            file_type_enum = CoreFileType._CLASS_NAME

        if file_type_enum is None:
            raise GenestackException("Invalid file type: %s" % file_type)

        if not issubclass(return_type, File):
            raise GenestackException('"return_type" must be a child class of "File"')

        created_file_id = self.invoke(
            'createFile',
            [
                'com.genestack.api.files.IFileType',
                'com.genestack.api.metainfo.IMetainfo'
            ],
            [
                java_object(file_type_enum, file_type),
                java_object('com.genestack.api.metainfo.MetainfoWritable', metainfo.get_java_object())
            ]
        )['id']

        return return_type(created_file_id)

    def list_children(self, container_file_query):
        """
        List the children of the folder, using a query.
        :param container_file_query: query
        :type container_file_query: ContainerFileQuery
        :return: list of children
        """
        validate_type(container_file_query, ContainerFileQuery)
        response = self.invoke('listChildren', ['com.genestack.api.files.ContainerFileQuery'],
                               [container_file_query.as_java_object()])
        return [File(element['id']) for element in response]

    def list_all_children(self, query=ContainerFileQuery()):
        """
        Generator function to retrieve all the children of a folder
        :param query: container file query
        :type query: ContainerFileQuery
        :return: iterator over all children
        """
        validate_type(query, ContainerFileQuery)
        query.offset = 0
        query.limit = ContainerFileQuery.MAX_LIMIT

        while True:
            children_batch = self.list_children(query)
            if not children_batch:
                break
            for child in children_batch:
                yield child
            query = query.get_next_page_query()

    def link_file(self, genestack_file):
        validate_type(genestack_file, File)
        self.invoke('linkFile', ['com.genestack.api.files.IFile'], [genestack_file.as_java_object()])

    def unlink_file(self, genestack_file):
        validate_type(genestack_file, File)
        self.invoke('unlinkFile', ['com.genestack.api.files.IFile'], [genestack_file.as_java_object()])


