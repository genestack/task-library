# -*- coding: utf-8 -*-

from datetime import datetime

from genestack.java import JavaObject, java_object, JAVA_HASH_MAP, JAVA_LIST, decode_object
from genestack import GenestackException
from genestack.utils import deprecated, validate_type


class Metainfo(dict):
    """
    Represents metainfo of the file.
    """

    NAME = "genestack:name"
    DESCRIPTION = "genestack:description"
    CREATION_DATE = "genestack:dateCreated"
    LAST_UPDATE_DATE = "genestack:file.last-update"
    ACCESSION = "genestack:accession"
    DATA_URL = "genestack.url:data"
    DATA_LOCATION = "genestack.location:data"
    EXTERNAL_LINKS = "genestack:links"
    RAW_LOCATION = "genestack.rawFile:data"
    ORGANIZATION = "genestack:organization"
    CONTACT_PERSON = "genestack:contactPerson"
    STORAGE_DATA_SIZE = "genestack:storageDataSize"
    INDEX_DATA_SIZE = "genestack:indexDataSize"
    DATABASE_SIZE = "genestack:databaseDataSize"
    PROGRESS_INFO = "genestack:progressInfo"

    class Flag(object):

        REQUIRED_FOR_INITIALIZATION = 1 << 0
        FROZEN_AFTER_INITIALIZATION = 1 << 1
        SET_BY_INITIALIZATION = 1 << 2
        USED_AS_DATA_SOURCE = 1 << 3
        FILE = 1 << 4
        REQUIRED_FOR_COMPLETENESS = 1 << 5
        SINGLE = 1 << 6
        MULTIPLE = 1 << 7
        INITIALIZATION_PARAMETER = REQUIRED_FOR_INITIALIZATION | FROZEN_AFTER_INITIALIZATION
        INITIALIZATION_PARAMETER_FILE = INITIALIZATION_PARAMETER | FILE
        SINGLE_INITIALIZATION_PARAMETER_FILE = INITIALIZATION_PARAMETER_FILE | SINGLE
        MULTIPLE_INITIALIZATION_PARAMETER_FILE = INITIALIZATION_PARAMETER_FILE | MULTIPLE

    def __init__(self):
        super(Metainfo, self).__init__()
        self.flags = {}

    def get(self, key):
        """
        Return metainfo value corresponding to key.
        If there is no metainfo value ``None`` is returned,
        if value have single entry instance of subclass :py:class:`~genestack.metainfo.MetainfoValue` returned
        else returns list of instances of subclass :py:class:`~genestack.metainfo.MetainfoValue`.

        :param key: 'metainfo key'
        :type key: str
        :return: Representation of metainfo value
        :rtype: None | MetainfoValue | list
        """
        return super(Metainfo, self).get(key)

    def get_value_as_list(self, key):
        """
        Return list of metainfo values corresponding to key. If key is not present in metainfo returns empty list.

        :param key: metainfo key
        :type key: str
        :return: list of metainfo values
        :rtype: list
        """
        value = self.get(key)
        if value is None:
            return []
        if isinstance(value, MetainfoValue):
            return [value]
        return value

    def get_first_string(self, key):
        """
        Return first string if value type is StringValue, otherwise return None.
        """
        value = self.get(key)
        if value is not None and not isinstance(value, MetainfoValue):
            if isinstance(value, list):
                value = value[0] if value else None
            else:
                raise GenestackException('Invalid metainfo value type: %s' % type(value))
        return value.value if isinstance(value, StringValue) else None

    def get_java_object(self):
        data = {}
        for key, value in self.iteritems():
            if type(value) == list:
                # case 1: list of single values (we use `type` and not `isinstance`,
                # since `MetainfoValue` is itself a child class of `list`)
                for v in value:
                    validate_type(v, MetainfoValue)
                data[key] = java_object(MetainfoValue.METAINFO_LIST_VALUE, {"list": java_object(JAVA_LIST, value)})
            else:
                # case 2: single value
                validate_type(value, MetainfoValue)
                data[key] = value
        return {
            'data': java_object(JAVA_HASH_MAP, data),
            'flags': java_object(JAVA_HASH_MAP, self.flags)
        }

    def set_flags(self, key, mask):
        """
        Set a flag for a metainfo key. Setting a flag equal to ``0`` will remove any flag from the key.
        Accepted flag values can be found in the :py:class:`Metainfo.Flag`.
        """
        if mask == 0:
            if key in self.flags:
                del self.flags[key]
            return
        self.flags[key] = mask


# This list is for json serialization purposes: [java_class_name, json_object]
class MetainfoValue(list):
    """
    Base class for representation of single metainfo value.
    It is two elements list. First element is type of value, second is dict containing value information.
    """
    # Metainfo value types:
    # 1. metainfo list value type:
    METAINFO_LIST_VALUE = 'com.genestack.api.metainfo.MetainfoListValue'
    # 2. metainfo scalar value types:
    # 2.1. metainfo simple scalar value types:
    BOOLEAN_VALUE = 'com.genestack.api.metainfo.BooleanValue'
    DECIMAL_VALUE = 'com.genestack.api.metainfo.DecimalValue'
    EXTERNAL_LINK = 'com.genestack.api.metainfo.ExternalLink'
    ORGANIZATION_VALUE = 'com.genestack.api.metainfo.OrganizationValue'
    PERSON_VALUE = 'com.genestack.api.metainfo.Person'
    PUBLICATION_VALUE = 'com.genestack.api.metainfo.Publication'
    # STORAGE_URL_VALUE is not sent to clients
    STRING_VALUE = 'com.genestack.api.metainfo.StringValue'
    EMPTY_VALUE = 'com.genestack.api.metainfo.EmptyValue'
    # 2.2. numeric value types
    DATE_TIME_VALUE = 'com.genestack.api.metainfo.DateTimeValue'
    INTEGER_VALUE = 'com.genestack.api.metainfo.IntegerValue'
    MEMORY_SIZE_VALUE = 'com.genestack.api.metainfo.MemorySizeValue'
    # 2.3. physical value types
    TEMPERATURE_VALUE = 'com.genestack.api.metainfo.TemperatureValue'
    TIME_VALUE = 'com.genestack.api.metainfo.TimeValue'
    # 2.4. other metainfo scalar value types:
    FILE_REFERENCE = 'com.genestack.api.metainfo.FileReference'

    def __init__(self, java_type, params):
        super(MetainfoValue, self).__init__()
        self.append(java_type)
        self.append(params)

    @deprecated('Use specific methods of metainfo values')
    def get(self, key):
        return self._get(key)

    def _get(self, key):
        return decode_object(self)[key]

    @staticmethod
    def get_metainfo_value(source_value):
        if not isinstance(source_value, JavaObject):
            raise GenestackException("Object expected, but %s found: %s" % (type(source_value), source_value))
        java_type = source_value.class_name

        if java_type == MetainfoValue.METAINFO_LIST_VALUE:
            return map(MetainfoValue.get_metainfo_value, source_value['list'])
        elif java_type == MetainfoValue.BOOLEAN_VALUE:
            return BooleanValue(source_value['value'])
        elif java_type == MetainfoValue.DATE_TIME_VALUE:
            return DateTimeValue(source_value['date'])
        elif java_type == MetainfoValue.EXTERNAL_LINK:
            return ExternalLink(
                source_value['text'], source_value['url'],
                source_value.get('format')
            )
        elif java_type == MetainfoValue.INTEGER_VALUE:
            return IntegerValue(source_value['value'])
        elif java_type == MetainfoValue.DECIMAL_VALUE:
            return DecimalValue(source_value['value'])
        elif java_type == MetainfoValue.MEMORY_SIZE_VALUE:
            return MemorySizeValue(source_value['value'])
        elif java_type == MetainfoValue.ORGANIZATION_VALUE:
            return OrganizationValue(
                source_value['name'], source_value['department'],
                source_value['street'], source_value['city'],
                source_value['state'], source_value['postalCode'],
                source_value['country'], source_value['email'],
                source_value['phone'], source_value['url']
            )
        elif java_type == MetainfoValue.PERSON_VALUE:
            return PersonValue(source_value['name'], source_value['email'], source_value['phone'])
        elif java_type == MetainfoValue.PUBLICATION_VALUE:
            return PublicationValue(
                source_value['journalName'], source_value['issueDate'],
                source_value['issueNumber'], source_value['title'],
                source_value['authors'], source_value['pages'],
                source_value['identifiers']
            )
        elif java_type == MetainfoValue.STRING_VALUE:
            return StringValue(source_value['value'])
        elif java_type == MetainfoValue.EMPTY_VALUE:
            return EmptyValue()
        elif java_type in [
            MetainfoValue.TEMPERATURE_VALUE,
            MetainfoValue.TIME_VALUE
        ]:
            return PhysicalValue(java_type, source_value['value'], source_value['unit'])
        elif java_type == MetainfoValue.FILE_REFERENCE:
            return FileReference(source_value['accession'], source_value['direction'])
        else:
            raise GenestackException('Unknown Metainfo value type : %s' % java_type)


class MetainfoSimpleValue(MetainfoValue):
    @property
    def value(self):
        """
        Returns value.

        :return: value
        """
        return self._get('value')

    def __str__(self):
        return str(self.value)


class BooleanValue(MetainfoSimpleValue):
    def __init__(self, value):
        MetainfoValue.__init__(self, MetainfoValue.BOOLEAN_VALUE, {'value': value})


class DateTimeValue(MetainfoValue):
    def __init__(self, date):
        MetainfoValue.__init__(self, MetainfoValue.DATE_TIME_VALUE, {'date': date})

    @property
    def date(self):
        """
        Returns date as :py:class:`datetime.datetime`

        :return: date value
        :rtype: datetime.datetime
        """
        return datetime.utcfromtimestamp(self._get('date') / 1000.0)

    def __str__(self):
        return self.date.strftime('%Y-%m-%d %H:%M:%S')


class StringValue(MetainfoSimpleValue):
    def __init__(self, value):
        MetainfoValue.__init__(self, MetainfoValue.STRING_VALUE, {'value': value})


class IntegerValue(MetainfoSimpleValue):
    def __init__(self, value):
        MetainfoValue.__init__(self, MetainfoValue.INTEGER_VALUE, {'value': int(value)})


class DecimalValue(MetainfoSimpleValue):
    def __init__(self, value):
        MetainfoValue.__init__(self, MetainfoValue.DECIMAL_VALUE, {'value': str(value)})


class MemorySizeValue(MetainfoSimpleValue):
    def __init__(self, value):
        MetainfoValue.__init__(self, MetainfoValue.MEMORY_SIZE_VALUE, {'value': int(value)})


class ExternalLink(MetainfoValue):
    def __init__(self, text, url, file_format):
        MetainfoValue.__init__(self, MetainfoValue.EXTERNAL_LINK, {'text': text, 'url': url,
                                                                   'format': java_object(JAVA_HASH_MAP, file_format)})

    @property
    def text(self):
        """
        Returns url title.

        :return: url title
        :rtype: str
        """
        return self._get('text')

    @property
    def url(self):
        """
        Returns URL.

        :return: URL value
        :rtype: str
        """
        return self._get('url')

    @property
    def format(self):
        """
        Return format, ``None`` if format is absent.

        :return: format dict or None
        :rtype: dict | None
        """
        return self._get('format')

    def __str__(self):
        return self.url


class OrganizationValue(MetainfoValue):
    def __init__(self, name, department, street, city, state, postal_code, country, email, phone, url):
        MetainfoValue.__init__(self, MetainfoValue.ORGANIZATION_VALUE, {
            'name': name, 'department': department,
            'street': street, 'city': city,
            'state': state, 'postalCode': postal_code,
            'country': country, 'email': email,
            'phone': phone, 'url': url
        })

    @property
    def name(self):
        """
        Returns organization name.

        :return: organizations name
        :rtype: str
        """
        return self._get('name')

    @property
    def department(self):
        """
        Returns department.

        :return: department
        :rtype: str
        """
        return self._get('department')

    @property
    def street(self):
        """
        Returns street.

        :return: street
        :rtype: str
        """
        return self._get('street')

    @property
    def city(self):
        """
        Returns city.

        :return: city
        :rtype: str
        """
        return self._get('city')

    @property
    def state(self):
        """
        Returns state.

        :return: state
        :rtype: str
        """
        return self._get('state')

    @property
    def postal_code(self):
        """
        Returns postal code as string.

        :return: department
        :rtype: postal code
        """
        return self._get('postalCode')

    @property
    def country(self):
        """
        Returns country.

        :return: country
        :rtype: str
        """
        return self._get('country')

    @property
    def email(self):
        """
        Returns email.

        :return: email
        :rtype: str
        """
        return self._get('email')

    @property
    def phone(self):
        """
        Returns phone.

        :return: phone
        :rtype: str
        """
        return self._get('phone')

    @property
    def url(self):
        return self._get('url')

    def __str__(self):
        return self.name


class PersonValue(MetainfoValue):
    def __init__(self, name, email, phone):
        MetainfoValue.__init__(self, MetainfoValue.PERSON_VALUE, {'name': name, 'email': email, 'phone': phone})

    @property
    def name(self):
        """
        Returns name.

        :return: name
        :rtype: str
        """
        return self._get('name')

    @property
    def email(self):
        """
        Returns email

        :return: email
        :rtype: str
        """
        return self._get('email')

    @property
    def phone(self):
        """
        Returns phone.

        :return: phone
        :rtype: str
        """
        return self._get('phone')

    def __str__(self):
        return self.name


class PublicationValue(MetainfoValue):
    def __init__(self, journal_name, issue_date, issue_number, title, authors, pages, identifiers):
        MetainfoValue.__init__(self, MetainfoValue.PUBLICATION_VALUE, {
            'journalName': journal_name, 'issueDate': issue_date,
            'issueNumber': issue_number, 'title': title,
            'authors': authors, 'pages': pages,
            'identifiers': identifiers
        })

    @property
    def journal_name(self):
        """
        Returns journal name.

        :return: journal name
        :rtype: str
        """
        return self._get('journalName')

    @property
    def issue_date(self):
        """
        Returns issue date as string.

        :return: issue date
        :rtype: str
        """
        return self._get('issueDate')

    @property
    def issue_number(self):
        """
        Returns issue number as string.

        :return: issue number
        :rtype: str
        """
        return self._get('issueNumber')

    @property
    def title(self):
        """
        Returns title

        :return: title
        :rtype: str
        """
        return self._get('title')

    @property
    def authors(self):
        """
        Returns authors.

        :return: authors
        :rtype: str
        """
        return self._get('authors')

    @property
    def pages(self):
        """
        Returns pages.

        :return: pages
        :rtype: str
        """
        return self._get('pages')

    @property
    def identifiers(self):
        """
        Returns identifiers as map there keys and values are strings.

        :return: identifiers
        :rtype: dict
        """
        return self._get('identifiers')

    def __str__(self):
        return self.title


class PhysicalValue(MetainfoValue):
    def __init__(self, java_type, value, unit):
        MetainfoValue.__init__(self, java_type, {
            'value': ['java.math.BigDecimal', float(value)],
            'unit': ['%s$Unit' % java_type, unit]
        })

    @property
    def value(self):
        """
        Returns value as float.

        :return: value as float
        :rtype: float
        """
        return self._get('value')

    @property
    def unit(self):
        """
        Returns measure unit.

        :return: measre unit
        :rtype: str
        """
        return self._get('unit')

    def __str__(self):
        return '%s %s' % (self.value, self.unit)


class FileReference(MetainfoValue):
    def __init__(self, accession, direction):
        MetainfoValue.__init__(self, MetainfoValue.FILE_REFERENCE, {
            'accession': accession,
            'direction': ['com.genestack.api.metainfo.FileReference$Direction', direction]
        })

    @property
    def accession(self):
        """
        Return an accession of referenced file.

        :return: accession
        :rtype: str
        """
        return self._get('accession')

    @property
    def direction(self):
        """
        Return direction of file reference.

        :return: direction
        :rtype: str
        """
        return self._get('direction')

    def __str__(self):
        return self.accession


class EmptyValue(MetainfoValue):
    def __init__(self):
        super(EmptyValue, self).__init__(MetainfoValue.EMPTY_VALUE, {})

    def __str__(self):
        return ''
