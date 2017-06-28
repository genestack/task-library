# -*- coding: utf-8 -*-

from genestack.core_files.genestack_file import File
from genestack.container_file_query import ContainerFileQuery
from genestack.utils import validate_type


class Dataset(File):
    """
    Collection of files of the same type used for batch processing.
    """
    INTERFACE_NAME = 'com.genestack.api.files.IDataset'
    DATAFILE_INTERFACE_NAME = 'com.genestack.api.files.IDataFile'

    def add_file(self, genestack_file):
        """
        Adds a file to this dataset.
        """
        validate_type(genestack_file, File)
        self.invoke('addFile',
                    [self.DATAFILE_INTERFACE_NAME],
                    [genestack_file.as_java_object()])

    def get_children(self, query=None):
        """
        Generator function to retrieve all files in the dataset.

        :param query: container file query
        :type query: ContainerFileQuery
        :return: iterator over all children
        """

        if query is None:
            query = ContainerFileQuery()
        else:
            validate_type(query, ContainerFileQuery)

        while True:
            response = self.invoke('getChildren',
                                   [ContainerFileQuery.CLASS_NAME],
                                   [query.as_java_object()])
            if not response:
                break

            for element in response:
                yield File(element['id'])

            query = query.get_next_page_query()

    def mutable(self):
        """
        Returns True if files can be added to or removed from this dataset.
        """
        return self.invoke('isMutable', [], [])

    def size(self):
        """
        Returns the number of files in this dataset.
        """
        return self.invoke('size', [], [])
