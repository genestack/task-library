# -*- coding: utf-8 -*-

# This is local environment
# All changes to this file should be propagated to/overriden by
# scripts/deploy/config/*/environment.py
import os

# TODO: remove this file, pass all settings via environment.

PROXY_URL = 'http://{}:8888'.format(os.environ.get("TASK_HOST_IP", "localhost"))

__SYSTEM_DIRECTORY = '/var/lib/genestack'
PROGRAMS_DIRECTORY = os.path.join(__SYSTEM_DIRECTORY, 'filesystem', 'programs')

TASK_LIBRARY_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)


