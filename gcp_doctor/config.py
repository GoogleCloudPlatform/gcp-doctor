# Lint as: python3
"""Globals that will be potentially user-configurable in future."""

import appdirs

# gcp-doctor version (not configurable, but useful to have here)
VERSION = '0.10'

# Default number of retries for API Calls.
API_RETRIES = 2

# Cache directory for diskcache.
CACHE_DIR = appdirs.user_cache_dir('gcp-doctor')

# How long to cache documents that rarely change (e.g. predefined IAM roles).
STATIC_DOCUMENTS_EXPIRY_SECONDS = 3600 * 24
