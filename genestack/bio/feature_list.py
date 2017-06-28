# -*- coding: utf-8 -*-

import os

from genestack.core_files.genestack_file import File
from genestack.frontend_object import StorageUnit
from genestack.compression import gzip_file
from genestack.metainfo import Metainfo, IntegerValue, StringValue
from genestack.utils import escape_quotation


class FeatureList(File):
    """
    This class represents a list of features, possibly with some additional data.

    Required keys:
        - :py:attr:`~genestack.bio.FeatureList.DATA_LOCATION` - key to store the physical file.

    To put data to this key you can use :py:meth:`~genestack.bio.FeatureList.put`.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IFeatureList'

    DATA_LOCATION = 'genestack.location:data'

    # @Deprecated, use Metainfo.SOURCE_DATA
    # Deprecated in 0.44.0, will be removed in 0.47.0
    SOURCE_KEY = Metainfo.SOURCE_DATA

    METAKEY_FEATURES_COUNT = 'genestack:featuresCount'
    METAKEY_FEATURE_FIELD = 'genestack:featureField'

    DESCRIPTORS_KEY = 'genestack.data:descriptors'
    NAME_PROPERTY = 'original-name'

    def get_feature_list(self, working_dir=None):
        """
        GET file by url stored in metainfo under DATA_LOCATION key (it is assumed that there is only
        one file).
        :param working_dir: same as in GET
        :type working_dir: str
        :return: path to the downloaded file
        :rtype: str
        """
        storage_units = self.GET(self.DATA_LOCATION, working_dir=working_dir)
        return storage_units[0].get_first_file()

    def get_feature_field(self):
        return self.get_metainfo().get_first_string(self.METAKEY_FEATURE_FIELD)

    def save_feature_field(self, feature_field):
        self.replace_metainfo_value(self.METAKEY_FEATURE_FIELD, StringValue(feature_field))

    def put_feature_list(self, path, features_count):
        """
        Put file to storage.

        :param path: path to existing Feature List file
        :type path: str
        :param features_count: number of features in the file
        :type sort: int
        :return: None
        """
        self.PUT(self.DATA_LOCATION, StorageUnit(gzip_file(path, remove_source=False)))
        self.add_metainfo_value(self.METAKEY_FEATURES_COUNT, IntegerValue(features_count))
        self.add_metainfo_value(
            self.DESCRIPTORS_KEY,
            StringValue(self.__create_meta_string(path, 'text/plain')))

    def __create_meta_string(self, path, mime):
        properties = [mime]
        name = os.path.basename(os.path.abspath(path))
        properties.append('%s=%s' % (self.NAME_PROPERTY, escape_quotation(name)))

        return ';'.join(properties)


class GeneExpressionSignature(FeatureList):
    """
    This class represents a list of genes with logFC data.

    Required keys:
        - :py:attr:`~genestack.bio.FeatureList.DATA_LOCATION` - key to store the physical file.

    To put data to this key you can use :py:meth:`~genestack.bio.GeneExpressionSignature.put`.
    """
    INTERFACE_NAME = 'com.genestack.bio.files.IGeneExpressionSignature'

    # @Deprecated, use Metainfo.SOURCE_DATA
    # Deprecated in 0.44.0, will be removed in 0.47.0
    SOURCE_KEY = Metainfo.SOURCE_DATA

    METAKEY_LOGFC_FIELD = 'genestack:logFCField'

    def get_logFC_field(self):
        return self.get_metainfo().get_first_string(self.METAKEY_LOGFC_FIELD)

    def save_logFC_field(self, logFC_field):
        self.replace_metainfo_value(self.METAKEY_LOGFC_FIELD, StringValue(logFC_field))


