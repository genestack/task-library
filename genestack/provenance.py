# coding=utf-8

from genestack.java import java_object, JAVA_LIST


class Provenance(object):
    CLASS_NAME = 'com.genestack.api.files.provenance.Provenance'

    def __init__(self, parent_accessions=None):
        self._parentAccessions = parent_accessions or []

    def as_java_object(self):
        # this method is needed to make the type checker happy
        raise NotImplementedError()

    def _get_object_dict(self):
        return {
            'parentAccessions': java_object(JAVA_LIST, self._parentAccessions)
        }


class ImportProvenance(Provenance):
    CLASS_NAME = 'com.genestack.api.files.provenance.ImportProvenance'

    def __init__(self, description=None, parent_accessions=None):
        super(ImportProvenance, self).__init__(parent_accessions)
        self._description = description

    def as_java_object(self):
        object_dict = self._get_object_dict()
        object_dict['description'] = self._description
        return java_object(self.CLASS_NAME, object_dict)


class ProcessProvenance(Provenance):
    CLASS_NAME = 'com.genestack.api.files.provenance.ProcessProvenance'

    def __init__(self, application_id, parent_accessions):
        super(ProcessProvenance, self).__init__(parent_accessions)
        self._application_id = application_id

    def as_java_object(self):
        object_dict = self._get_object_dict()
        object_dict['applicationId'] = self._application_id
        return java_object(self.CLASS_NAME, object_dict)
