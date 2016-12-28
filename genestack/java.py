# -*- coding: utf-8 -*-

from genestack.genestack_exceptions import GenestackException

JAVA_STRING = 'java.lang.String'
JAVA_STRING_ARRAY = '[Ljava.lang.String;'
JAVA_STRING_ARRAY_OF_ARRAYS = '[[Ljava.lang.String;'
JAVA_OBJECT_ARRAY = '[Ljava.lang.Object;'
JAVA_OBJECT_ARRAY_OF_ARRAYS = '[[Ljava.lang.Object;'
JAVA_MAP = 'java.util.Map'
JAVA_HASH_MAP = 'java.util.HashMap'
JAVA_SET = 'java.util.Set'
JAVA_LIST = 'java.util.List'
JAVA_ARRAY_LIST = 'java.util.ArrayList'
JAVA_LONG = 'java.lang.Long'
JAVA_INTEGER = 'java.lang.Integer'


def java_object(java_type, value):
    return None if value is None else [java_type, value]


class JavaObject(dict):
    def __init__(self, class_name, obj):
        super(JavaObject, self).__init__()
        self.class_name = class_name
        self.update(obj)


class JavaPrimitive(object):
    def __init__(self, class_name, value):
        self.class_name = class_name
        self.value = value


def decode_object(obj):
    """
    Decodes server response.

    This method takes as input a python object that was decoded from server JSON response.
    Server uses special notation to represent Java objects as a list of two elements:
    the first element is a Java object's class name and the second element is the serialized
    object itself. This special notation is converted into corresponding python object,
    all other values are returned as is.

    The following Java class names are treated in a special way:
        - ``java.util.Map`` converted to dict
        - ``com.genestack.bridge.JsonNull`` converted to ``None``
        - ``com.genestack.bridge.JsonExceptionWrapper`` raises exception,
          with error message from server

    If serialized object is a ``dict``, :py:class:`JavaObject`` is returned;
    otherwise serialized object is returned as it is.

    :param obj: deserialized JSON from server
    :return: python representation of server response
    """
    decoded = _decode_object(obj)
    if isinstance(decoded, JavaObject):
        if decoded.class_name == 'com.genestack.bridge.JsonNull':
            return None
        if decoded.class_name == 'com.genestack.bridge.JsonExceptionWrapper':
            exception_class = decoded['className']
            message = ''
            if exception_class is not None:
                message += '[%s]: ' % exception_class
            message += decoded['message'] or ''
            uid = decoded['exceptionUid']
            if uid:
                message += ' (Exception UID: %s)' % uid
            raise GenestackException(message)
    return decoded


def _decode_object(obj):
    if not isinstance(obj, list):
        return _decode_content(obj)

    if len(obj) != 2:
        raise GenestackException("Object expected, but list found: %s" % obj)

    cls = _decode_content(obj[0])
    if not isinstance(cls, str):
        raise GenestackException("Class name (string) expected, but %s found: %s" % (type(cls), cls))

    if cls == JAVA_MAP:
        return _decode_map(obj[1])

    content = _decode_content(obj[1])

    if isinstance(content, dict):
        return JavaObject(cls, content)
    return content


def _decode_content(obj):
    if obj is None:
        return None
    if isinstance(obj, list):
        return [_decode_object(i) for i in obj]
    if isinstance(obj, dict):
        return {_decode_object(k): _decode_object(v) for k, v in obj.iteritems()}
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    return obj


def _decode_map(obj):
    if not isinstance(obj, dict):
        raise GenestackException("java.util.Map should be an object")
    try:
        entries = obj['entries']
    except KeyError as e:
        raise GenestackException("java.util.Map should have attribute %s" % e)
    if not isinstance(entries, list):
        raise GenestackException("java.util.Map 'entries' should be a list")

    try:
        return dict([
            (_decode_object(e['key']), _decode_object(e['value'])) for e in entries
        ])
    except KeyError as e:
        raise GenestackException("java.util.Map entry should have attribute %s" % e)


def encode_simple_object(obj):
    if isinstance(obj, list):
        return java_object(
            JAVA_ARRAY_LIST,
            [encode_simple_object(x) for x in obj]
        )
    if isinstance(obj, dict):
        return java_object(
            obj.class_name if isinstance(obj, JavaObject) else JAVA_HASH_MAP,
            {k: encode_simple_object(v) for k, v in obj.iteritems()}
        )
    if isinstance(obj, JavaPrimitive):
        return java_object(obj.class_name, obj.value)
    return obj


class JavaLong(JavaPrimitive):
    def __init__(self, value):
        super(JavaLong, self).__init__(JAVA_LONG, value)


class JavaInteger(JavaPrimitive):
    def __init__(self, value):
        super(JavaInteger, self).__init__(JAVA_INTEGER, value)
