# -*- coding: utf-8 -*-
import json
import os
import requests
import sys

from genestack import GenestackException, environment
from genestack.java import decode_object


class _Bridge(object):
    @staticmethod
    def _send_request(path, data):
        headers = {'Genestack-Token': os.getenv('GENESTACK_TOKEN')}
        url = environment.PROXY_URL.rstrip('/') + '/' + path
        request = requests.Request('POST', url, json=data, headers=headers)
        response = None

        prepared_request = request.prepare()
        with requests.Session() as session:
            try:
                response = session.send(prepared_request)
            except requests.RequestException as e:
                raise GenestackException(str(e))

        if response.status_code != 201:
            if response.status_code == 500:
                raise GenestackException('Internal server error')
            else:
                raise GenestackException('Request failed, got status: %s expect 201' % response.status_code)

        response_data = response.json()
        stdout = response_data.get('stdout')
        if stdout:
            print stdout
        stderr = response_data.get('stderr')
        if stderr:
            sys.stderr.write(stderr)
        error = response_data.get('error')
        if error:
            raise GenestackException('%s' % error)
        return response_data.get('result')

    @staticmethod
    def invoke(object_id, interface_name, method_name, types, values):
        """
        :param object_id: object id of requested file
        :param interface_name: interface name of requested file
        :param method_name:
        :param types: list of string class names as java.lang.Class.getName() method returns
                      http://docs.oracle.com/javase/7/docs/api/java/lang/Class.html#getName()
        :param values: method arguments
        :return: server response object
        """
        data = {
            'method_name': method_name,
            'types': types,
            'values': values,
            'interface_name': interface_name,
            'object_id': object_id,
        }
        response_data = _Bridge._send_request('invoke', data)
        decoded = decode_object(response_data)
        return decoded

    @staticmethod
    def get(obj, key, format_pattern, working_dir):
        absolute_path = os.path.abspath(working_dir)
        if not absolute_path.startswith(os.path.abspath(os.path.curdir)):
            raise GenestackException('"%s" is outside task directory' % working_dir)

        return _Bridge._send_request('get', {
            'key': key,
            'interface_name': obj.interface_name,
            'format_pattern': format_pattern and format_pattern.to_list(),
            'working_dir': absolute_path,
            'object_id': obj.object_id
        })

    @staticmethod
    def put(obj, key, storage_unit_list):
        # send absolute paths!!
        for unit in storage_unit_list:
            files = map(os.path.abspath, unit.files)
            for user_path, path_for_server in zip(unit.files, files):
                if not path_for_server.startswith(os.path.abspath(os.path.curdir)):
                    raise GenestackException('Cannot PUT file that outside current directory: %s' % user_path)
            unit.files = files

        return _Bridge._send_request('put', {
            'key': key,
            'storages': [x.to_map() for x in storage_unit_list],
            'interface_name': obj.interface_name,
            'object_id': obj.object_id,
        })

    @staticmethod
    def set_format(obj, key, storage_unit_list):
        # send absolute paths!!
        for unit in storage_unit_list:
            unit.files = map(os.path.abspath, unit.files)

        return _Bridge._send_request('set_format', {
            'key': key,
            'storages': [x.to_map() for x in storage_unit_list],
            'interface_name': obj.interface_name,
            'object_id': obj.object_id
        })

    @staticmethod
    def download(obj, storage_key, links_key, fold, put_to_storage, working_dir):
        # send absolute paths!!
        working_dir = working_dir if working_dir else os.curdir
        working_dir = os.path.abspath(working_dir)

        return _Bridge._send_request('download', {
            'storage_key': storage_key,
            'links_key': links_key,
            'fold': fold,
            'put_to_storage': put_to_storage,
            'interface_name': obj.interface_name,
            'object_id': obj.object_id,
            'working_dir': working_dir,
        })

    # we limit maximum sent json size to 5 Mb
    _MAX_CONTENT_SIZE = 5 * 10 ** 6

    @staticmethod
    def send_index(obj, values):
        for chunk in _Bridge.__get_value_chunks(values):
            _Bridge._send_request('dataindex', {
                'object_id': obj.object_id,
                'values': chunk,
                'interface_name': obj.interface_name
            })

    @staticmethod
    def __get_value_chunks(values):
        if not values:
            return [[]]

        def chunks(chunks_num):
            chunk_size = divide(len(values), chunks_num)
            return (values[i:i + chunk_size] for i in xrange(0, len(values), chunk_size))

        def divide(x, y):
            import math
            return int(math.ceil(x / float(y)))

        # this is not a very accurate approach, we should use a different one if the json size gets too big
        json_size = len(json.dumps(values[0]))
        if json_size > _Bridge._MAX_CONTENT_SIZE:
            raise GenestackException('JSON is too large: %d bytes' % json_size)

        size = json_size * len(values)
        if size > _Bridge._MAX_CONTENT_SIZE:
            chunks_num = divide(size, _Bridge._MAX_CONTENT_SIZE)
            return chunks(chunks_num)
        return [values]
