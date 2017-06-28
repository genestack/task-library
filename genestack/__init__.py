# -*- coding: utf-8 -*-

import signal
import traceback

from genestack.bio.external_database import ExternalDatabase
from genestack.cla import CLA, Toolset, Tool
from genestack.core_files.application_page_file import ApplicationPageFile, StringMapFile, StringMapFileQuery
from genestack.core_files.auxiliary_file import AuxiliaryFile
from genestack.core_files.dictionary_file import DictionaryFile, DictionaryFileQuery
from genestack.core_files.genestack_file import File
from genestack.core_files.genestack_folder import Folder, CoreFileType, BioFileType
from genestack.core_files.index_file import IndexFile
from genestack.core_files.raw_file import RawFile
from genestack.core_files.report_file import ReportFile
from genestack.core_files.dataset import Dataset
from genestack.container_file_query import ContainerFileQuery
from genestack.file_filters import (BasicFileFilter, TypeFileFilter, MetainfoKeyFileFilter, MetainfoKeyValueFileFilter,
                                    ActualOwnerFileFilter, FixedValueFileFilter)
from genestack.frontend_object import StorageUnit
from genestack.genestack_exceptions import GenestackException
from genestack.genestack_indexer import Indexer


# Allow to get current trace by sending signal from system.
def debug(sig, frame):
    traceback.print_stack(frame)

signal.signal(signal.SIGUSR1, debug)
