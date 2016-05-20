# -*- coding: utf-8 -*-

from genestack import File, GenestackException

from genestack.file_filters import BasicFileFilter
from genestack.java import java_object, JAVA_LIST
from genestack.metainfo import Metainfo
from genestack.query_range import QueryRange
from genestack.utils import validate_type


class ContainerFileQuery(object):
    MAX_PAGE_SIZE = 100
    CLASS_NAME = 'com.genestack.api.files.ContainerFileQuery'

    class SortOrder(object):
        CLASS_NAME = 'com.genestack.api.files.ContainerFileQuery$SortOrder'
        BY_NAME = 'BY_NAME'
        BY_ACCESSION = 'BY_ACCESSION'
        BY_LAST_UPDATE = 'BY_LAST_UPDATE'
        DEFAULT = 'DEFAULT'

    def __init__(self, filters=None, order=SortOrder.DEFAULT, ascending=True, offset=0, limit=MAX_PAGE_SIZE):
        """
        Creates a new query to use in folder search

        :param filters: list of filters to use
        :type list of BasicFileFilter:
        :param offset: starting entry index (zero-based, included)
        :type offset: int
        :param limit: number of entries
        :type limit: int
        :param order: sorting order. Must be one of the constants in :py:class:`~genestack.ContainerFileQuery.SortOrder`
        :type order: basestring
        :param ascending: should sorting be in ascending order?
        :type ascending: bool
        """

        validate_type(filters, list, accept_none=True)
        validate_type(order, basestring)
        validate_type(limit, int)
        validate_type(offset, int)
        validate_type(ascending, bool)

        if filters is not None:
            for basic_filter in filters:
                validate_type(basic_filter, BasicFileFilter)

        if order not in (self.SortOrder.BY_ACCESSION, self.SortOrder.BY_LAST_UPDATE, self.SortOrder.BY_NAME,
                         self.SortOrder.DEFAULT):
            raise GenestackException('Invalid sort order')

        self.filters = filters
        self.range = QueryRange(offset, limit, self.MAX_PAGE_SIZE)
        self.order = order
        self.ascending = ascending

    @property
    def offset(self):
        return self.range.offset

    @offset.setter
    def offset(self, value):
        self.range.offset = value

    @property
    def limit(self):
        return self.range.limit

    @limit.setter
    def limit(self, value):
        self.range.limit = value

    def get_next_page_query(self):
        """
        Creates a new query to retrieve next page of values

        :return: query that can be used to get the next page
        :rtype: ContainerFileQuery
        """
        result = ContainerFileQuery(filters=self.filters,
                                    order=self.order,
                                    ascending=self.ascending,
                                    offset=self.offset + self.limit,
                                    limit=self.limit)
        return result

    def as_java_object(self):

        object_dict = {
            'filters': java_object(JAVA_LIST, [f.as_java_object() for f in self.filters]
                                   if self.filters is not None else []),
            'range': self.range.as_java_object(),
            'order': java_object(self.SortOrder.CLASS_NAME, self.order),
            'ascending': self.ascending
        }
        return java_object(self.CLASS_NAME, object_dict)


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

    DIFFERENTIAL_EXPRESSION_FILE = "DIFFERENTIAL_EXPRESSION_FILE"

    GENOME_BED_DATA = "GENOME_BED_DATA"
    GENOME_WIGGLE_DATA = "GENOME_WIGGLE_DATA"


class Folder(File):
    """
    Representation of genestack folder.
    """
    INTERFACE_NAME = 'com.genestack.api.files.IFolder'

    MAX_QUERY_PAGE_SIZE = 100

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
        query.limit = ContainerFileQuery.MAX_PAGE_SIZE

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


