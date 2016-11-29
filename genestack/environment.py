# -*- coding: utf-8 -*-

# This is local environment
# All changes to this file should be propagated to/overriden by
# scripts/deploy/config/*/environment.py
import os


PROXY_URL = 'http://{}:8888'.format(os.environ.get("TASK_HOST_IP", "localhost"))

SYSTEM_DIRECTORY = '/var/lib/genestack'
FILESYSTEM_DIRECTORY = SYSTEM_DIRECTORY + '/filesystem'
STORAGE_DIRECTORY = SYSTEM_DIRECTORY + '/storage'
PROGRAMS_DIRECTORY = FILESYSTEM_DIRECTORY + '/programs'
DATA_READ_DIRECTORY = FILESYSTEM_DIRECTORY + '/data'
DATA_WRITE_DIRECTORY = FILESYSTEM_DIRECTORY + '/write_data'

BACKEND_URL = 'http://localhost:8080/backend/endpoint'

TASK_LIBRARY_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
