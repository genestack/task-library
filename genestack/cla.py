# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import time
from contextlib import contextmanager
from subprocess import PIPE

from genestack.genestack_exceptions import GenestackException
from genestack.core_files.genestack_file import File
from genestack.environment import PROGRAMS_DIRECTORY
from genestack.utils import join_program_path, log_info, log_warning, format_tdelta, deprecated
from plumbum import local
from plumbum.commands import ExecutionModifier


class RUN(ExecutionModifier):
    """
    An execution modifier that runs the given command in the foreground,
    passing it to the current process `stdout` and `stderr`.
    Add log markers to `stdout` and `stderr` if ``verbose``.
    """
    __slots__ = ('stdout', 'verbose')

    def __init__(self, stdout=None, verbose=True):
        self.stdout = stdout
        self.verbose = verbose

    def __rand__(self, cmd):
        with _print_command_info(cmd, self.verbose):
            if self.stdout:
                cmd = cmd > self.stdout
            cmd(stdout=None, stderr=None)


class OUTPUT(ExecutionModifier):
    """
    An execution modifier that runs the given command in the foreground,
    returns its `stdout` as string and passing its `stderr` to the current process `stderr`.
    Add log markers to `stdout` and `stderr` if ``verbose``.
    """
    __slots__ = ('verbose',)

    def __init__(self, verbose=True):
        self.verbose = verbose

    def __rand__(self, cmd):
        with _print_command_info(cmd, True), cmd.bgrun(stdin=None, stdout=PIPE, stderr=None) as p:
            return p.run()[1]


RUN = RUN()
OUTPUT = OUTPUT()

_toolset_inited = False
_toolsets = {}
_arguments = []


def _init_toolsets():
    global _toolset_inited
    if not _toolset_inited:
        params_key = 'genestack:tool.arguments'
        version_prefix = 'genestack:tool.version:'
        mi = File().get_metainfo()
        _arguments.extend(x.value for x in mi.get_value_as_list(params_key))
        versions = {k[len(version_prefix):]: mi.get(k).value for k in mi if k.startswith(version_prefix)}
        _toolsets.update({k: Toolset(k, v, verbose=True) for k, v in versions.items()})
        _toolset_inited = True


def get_argument_string():
    """
    Return argument string for CLA that uses only single command line.
    If more than one command found raises :py:class:`~genestack.GenestackException`,
    use :py:meth:`get_argument_string_list` in that case

    :return: argument string
    :rtype: str
    """
    _init_toolsets()
    if not _arguments:
        return ''
    if len(_arguments) == 1:
        return _arguments[0]
    else:
        raise GenestackException('Too many arguments found, use get_argument_string_list')


def get_argument_string_list():
    """
    Return list of the argument strings.
    If more than one command found raises :py:class:`~genestack.GenestackException`

    :return: list of argument strings
    :rtype: list[str]
    """
    _init_toolsets()
    return list(_arguments)


def _get_tool(toolset, tool, verbose=True):
    """
    Return Tool instance.

    :type toolset: str
    :type tool: str
    :rtype: Tool
    """
    _init_toolsets()
    if toolset not in _toolsets:
        raise GenestackException(
            'Cannot get version for toolset "%s", '
            'this version should be set in metainfo by application' % toolset)
    toolset = _toolsets[toolset]
    toolset.verbose = verbose
    return toolset.get_tool(tool)


@deprecated('use "get_tool" instead')
def get_command(toolset, tool, uses=None):
    return get_tool(toolset, tool, uses=uses)


def get_version(toolset):
    """
    Return toolset version.

    :param toolset: toolset name
    :type toolset: str
    :return: toolset version as a string
    :rtype: str
    """
    _init_toolsets()
    toolset = _toolsets.get(toolset)
    return toolset.version


def get_tool(toolset, tool, uses=None):
    """
    Return command with path and required environment.
    See plumbum docs for more info http://plumbum.readthedocs.io/en/latest/#

    :param toolset: toolset name
    :type toolset: str
    :param tool: tool name
    :type tool: str
    :param uses: list of toolset names to be added to PATH
    :type uses: list[str]
    :return: command to run tool
    :rtype: plumbum.commands.base.BoundEnvCommand | plumbum.machines.LocalCommand
    """
    tool = _get_tool(toolset, tool)
    cmd = tool.get_tool_command()

    if uses:
        # TODO make proper message if toolset is not present
        path = local.env['PATH'] + ':' + ':'.join([_toolsets[x].get_directory() for x in uses])
        cmd = cmd.with_env(PATH=path)
    return cmd


@deprecated('use "get_tool_path" instead')
def get_command_path(toolset, tool):
    return get_tool_path(toolset, tool)


def get_tool_path(toolset, tool):
    """
    Return path to tool executable.

    :param toolset: toolset name
    :type toolset: str
    :param tool: tool name
    :type tool: str
    :return:
    """
    tool = _get_tool(toolset, tool)
    return tool.get_executable_path()


def get_directory(toolset):
    """
    Return directory where executables are located.

    :param toolset: toolset name
    :type toolset: str
    :return: directory where executables are located
    :rtype: str
    """
    return _toolsets[toolset].get_directory()


@contextmanager
def _print_command_info(command, verbose):
    if verbose:
        start_message = 'Start: %s' % str(command).replace(PROGRAMS_DIRECTORY + '/', '', 1)
        log_info(start_message)
        log_warning(start_message)
        start = time.time()
        yield
        tdelta = format_tdelta(time.time() - start)
        exit_msg = 'Command run finished, %s elapsed' % tdelta
        log_info(exit_msg)
        log_warning(exit_msg)
        return
    yield
    return


class CLA(object):
    def __init__(self, a_file):
        pass

    def argument_string(self):
        return get_argument_string()

    def argument_string_list(self):
        return get_argument_string_list()

    def get_tool(self, toolset, tool, verbose=True):
        return _get_tool(toolset, tool, verbose=verbose)


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

    def get_tool_command(self):

        if self.__executable.endswith('.py'):
            command = local['python'][self.get_executable_path()]
        else:
            with local.env(PATH=self.get_directory()):
                command = local[self.__executable]
        return command
