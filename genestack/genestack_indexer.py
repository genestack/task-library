# -*- coding: utf-8 -*-

from multiprocessing.dummy import Pool
import traceback

from genestack import GenestackException


class Indexer(object):
    def __init__(self, file_to_index):
        self.__file = file_to_index
        self.__indexing_pool = Pool(1)
        self.__indexing_recent_response = None
        self.__inside_context = False

    def __enter__(self):
        self.__inside_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__inside_context = False
        if self.__indexing_recent_response is not None:
            self.__indexing_recent_response.get()

    def index_records(self, records_list):
        """
        Adds given records to the file's index.
        Parameter records_list is a list of dicts. Every dict uses strings as keys.
        Note that this method is NOT thread-safe, so if you plan to index records from
        different threads you must synchronise manually.

        :param records_list: list of dicts with str keys
        :type records_list: list
        :return: a future-like object which can be queried via get() method. If an exception
         occurs during indexing it will be propagated to the client.
        """
        if not self.__inside_context:
            raise GenestackException('Indexer object must be used only inside a "with" statement')
        if not records_list:
            return

        def invoke(*args, **kwargs):
            try:
                return self.__file.send_index(*args, **kwargs)
            except:
                traceback.print_exc()
                raise

        if self.__indexing_recent_response is not None:
            self.__indexing_recent_response.get()
        self.__indexing_recent_response = self.__indexing_pool.apply_async(invoke, kwds={"values": records_list})
