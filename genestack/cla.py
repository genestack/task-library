# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import time

from genestack.utils import join_program_path, log_info, log_warning, format_tdelta
from genestack import GenestackException

PARAMS_KEY = 'genestack:tool.arguments'


class CLA(object):
    def __init__(self, a_file):
        self.__metainfo = a_file.get_metainfo()

    def get_tool(self, toolset, tool, verbose=True):
        version_key = 'genestack:tool.version:' + toolset
        version_value = self.__metainfo.get(version_key)
        version = version_value.value if version_value is not None else None
        if version is None:
            raise GenestackException("Tool version should be set in file metainfo")
        return Toolset(toolset, version, verbose=verbose).get_tool(tool)

    def argument_string(self):
        value = self.__metainfo.get(PARAMS_KEY)
        return value.value if value is not None else ''

    def argument_string_list(self):
        values = self.__metainfo.get_value_as_list(PARAMS_KEY)
        return [v.value for v in values]


class Toolset(object):
    def __init__(self, name, version, verbose=False):
        self.__name = name
        self.__version = version
        self.__directory = join_program_path(name, version)
        self.verbose = verbose
        self.path_extras = []
        if not os.path.exists(self.__directory):
            raise GenestackException(
                'Tool "%s" with version "%s" is not installed' % (name, version))
        self.uses(self)

    @property
    def name(self):
        return self.__name

    @property
    def version(self):
        return self.__version

    def get_tool(self, name):
        return Tool(self, name)

    def get_directory(self):
        with_bin = os.path.join(self.__directory, 'bin')
        return with_bin if os.path.exists(with_bin) else self.__directory

    def uses(self, toolset):
        self.path_extras.append(toolset.get_directory())

    def get_version(self):
        sys.stderr.write('This method is deprecated, use "version" property\n')
        return self.__version

    @property
    def version(self):
        return self.__version

    @property
    def name(self):
        return self.__name


class Tool(object):
    def __init__(self, toolset, name):
        self.__toolset = toolset
        self.__executable = name
        if not os.path.exists(self.get_executable_path()):
            raise GenestackException(
                'Executable "%s" not found for tool "%s" with version "%s"' % (
                    self.__executable, toolset.name, toolset.version))

    def get_executable_name(self):
        return self.__executable

    def get_executable_path(self):
        return os.path.join(self.get_directory(), self.__executable)

    def __log_start(self, arguments):
        enter_msg = 'Start %s(%s): %s %s' % (self.__toolset.name, self.__toolset.version,
                                             self.get_executable_name(), ' '.join(arguments))
        log_info(enter_msg)
        log_warning(enter_msg)
        self.__start_time = time.time()

    def __log_finish(self):
        tdelta = format_tdelta(time.time() - self.__start_time)
        exit_msg = 'Running "%s" finished, %s elapsed\n' % (self.get_executable_name(), tdelta)
        log_info(exit_msg)
        log_warning(exit_msg)

    def run(self, arguments, verbose=None, stdout=None, stderr=None):
        """
        Run tool with arguments. Wait for tool to complete.

        If the exit code was zero then return, otherwise raise
        GenestackException.

        This method is thread safe, except log output. Use `verbose=False` when
        multiprocessing.

        :param arguments: command arguments
        :param verbose: flag to print start and end markers to log, if not
                        specified uses Toolset preferences
        :return: None
        """
        if verbose is None:
            verbose = self.__toolset.verbose

        if verbose:
            self.__log_start(arguments)
        try:
            retcode = subprocess.call(self.__compose_arguments(arguments),
                                      stdout=stdout,
                                      stderr=stderr,
                                      shell=True)
            if retcode != 0:
                raise GenestackException(
                    'Command "%s" returned non-zero exit status %d' % (
                        self.get_executable_name(), retcode))
        finally:
            if verbose:
                self.__log_finish()

    def output(self, arguments, verbose=None, stderr=None):
        """
        Run tool with arguments and return its output as a byte string.

        If the exit code was non-zero it raises a :py:class:`~genestack.GenestackException`.

        This method is thread safe, except log output. Use `verbose=False` when
        multiprocessing.

        :param arguments: command arguments
        :param verbose: flag to print start and end markers to log, if not
                        specified uses Toolset preferences
        :return: output
        :rtype: str
        """
        if verbose is None:
            verbose = self.__toolset.verbose

        if verbose:
            self.__log_start(arguments)
        try:
            return subprocess.check_output(self.__compose_arguments(arguments),
                                           shell=True,
                                           stderr=stderr
                                           )
        except subprocess.CalledProcessError as e:
            print e.output
            raise GenestackException(
                    'Command "%s" returned non-zero exit status %d' % (
                        self.get_executable_name(), e.returncode))
        finally:
            if verbose:
                self.__log_finish()

    def __compose_arguments(self, arguments):
        path_string = ':'.join(self.__toolset.path_extras + ['$PATH'])
        export_path_string = 'export PATH=%s;' % path_string
        if self.__executable.endswith('.py'):
            to_run = 'python ' + self.get_executable_path()
        else:
            to_run = self.__executable
        return ' '.join([export_path_string, to_run] + [str(x) for x in arguments])

    def get_directory(self):
        return self.__toolset.get_directory()

    def uses(self, toolset):
        self.__toolset.path_extras.append(toolset.get_directory())

    def get_version(self):
        sys.stderr.write('This method is deprecated, use "version" property\n')
        return self.__toolset.version

    @property
    def version(self):
        return self.__toolset.version
