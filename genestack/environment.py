# -*- coding: utf-8 -*-

# This is local environment
# All changes to this file should be propagated to/overriden by
# scripts/deploy/config/*/environment.py
import os

PROXY_URL = 'http://localhost:8888'

SYSTEM_DIRECTORY = '/var/genestack/Servers/filesystem'
PROGRAMS_DIRECTORY = SYSTEM_DIRECTORY + '/programs'
STORAGE_DIRECTORY = SYSTEM_DIRECTORY + '/storage'
DATA_READ_DIRECTORY = SYSTEM_DIRECTORY + '/data'
DATA_WRITE_DIRECTORY = SYSTEM_DIRECTORY + '/write_data'

BACKEND_URL = 'http://localhost:8080/backend/endpoint'

TASK_LIBRARY_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
