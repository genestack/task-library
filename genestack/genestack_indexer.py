# -*- coding: utf-8 -*-
import string
from multiprocessing.dummy import Pool

from genestack.genestack_exceptions import GenestackException
from genestack.utils import log_warning

_SOLR_ALLOWED_CHARS = set(string.ascii_letters + string.digits + '_')

def _escape_key(k):
        if isinstance(k, Key):
            return k.get_key()
        else:
            return k


def _make_record(record):
    return {_escape_key(k): v for k, v in record.items()}


class Key(object):
    """
    Key is class that represent key in single index record.
    Required for proper escape of forbidden symbols.


    Key consist of 3 parts:
      - `prefix` helps to separate keys for special implementation-specififc purposes
        (like 'search'), may be empty, can contain only ASCII alphanumeric characters
        and underscore
      - `name` name of the key, must be unique for all keys with the same `prefix`,
        may be empty if prefix is specified, can contain any characters
      - `suffix` contains index-specific information about the key,
        can contain only ASCII alphanumeric characters and underscore

    Example:
      - ``Key('name', 'ss')  # name and suffix``
      - ``Key('search', 'name', 'ss_ci')  # prefix name suffix``
      - ``Key('search_all', None, 'ss_ci_ns')  # empty name``
    """
    def __init__(self, *args):
        if len(args) == 2:
            name, suffix = args
            prefix = None
        elif len(args) == 3:
            prefix, name, suffix = args
        else:
            raise GenestackException('Function expect 2 or 3 arguments')

        self.prefix = prefix
        self.name = name
        self.suffix = suffix
        self.validate()

    def validate(self):
        if not self.suffix:
            raise GenestackException(
                self._get_error('Suffix must not be empty')
            )

        if not self.prefix and not self.name:
            raise GenestackException(
                self._get_error('Both prefix and name cannot be empty')
            )

        if self.suffix.startswith('_'):
            raise GenestackException(
                self._get_error('Suffix must not starts with underscore')
            )

        if self.prefix and self.prefix.endswith('_'):
            raise GenestackException(
                self._get_error('Prefix must not ends with underscore')
            )
        for item in [self.prefix, self.suffix]:
            if item and not _SOLR_ALLOWED_CHARS.issuperset(item):
                raise GenestackException(
                    self._get_error('Only ascii letters, digits and, underscore allowed in keys name')
                )

    def _get_error(self, reason):
        return '%s, prefix: %s name: %s suffix: %s' % (reason, self.prefix, self.name, self.suffix)

    def get_key(self):
        return '_'.join(filter(None, (self.prefix, escape_field(self.name), self.suffix)))


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
        if exc_type is None and self.__indexing_recent_response is not None:
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
                log_warning('Fail to send index.')
                raise
        new_records = [_make_record(record) for record in records_list]

        if self.__indexing_recent_response is not None:
            self.__indexing_recent_response.get()
        self.__indexing_recent_response = self.__indexing_pool.apply_async(invoke, kwds={"values": new_records})

_ALLOWED_BYTES = set(bytearray(string.ascii_letters + string.digits))


def escape_field(field):
    def escape_byte(b):
        return chr(b) if b in _ALLOWED_BYTES else ('_' + hex(b).upper()[2:])

    array = bytearray(field, 'utf-8') if isinstance(field, unicode) else bytearray(field)
    return ''.join(map(escape_byte, array))
