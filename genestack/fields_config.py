#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2017 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import json

from genestack.metainfo import StringValue


class FieldsConfig(object):
    class FieldType(object):
        STRING = 'STRING'
        DOUBLE = 'DOUBLE'
        LONG = 'LONG'
        BOOLEAN = 'BOOLEAN'

    class FieldConfig(object):
        def __init__(self, id, description, type, values_number):
            self.id = id
            self.description = description
            self.type = type
            self.values_number = values_number

        def as_list(self):
            return [self.id, self.description, self.type, self.values_number]

    METAKEY_FIELDS_CONFIG = 'genestack:fieldsConfig'

    def __init__(self):
        self.field_config = []

    def __fields_config(self):
        serialized_fields = []
        for field in self.field_config:
            serialized_fields.append(field.as_list())

        return json.dumps({
            'fields': serialized_fields
        })

    def add_field(self, id, description, type, values_number):
        field = self.FieldConfig(id, description, type, values_number)
        self.field_config.append(field)

    def save_to_metainfo(self, file):
        file.add_metainfo_value(self.METAKEY_FIELDS_CONFIG, StringValue(self.__fields_config()))
