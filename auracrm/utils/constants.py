# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Constants
Application-wide constants for AuraCRM.
"""

# App metadata
APP_NAME = "auracrm"
APP_TITLE = "AuraCRM"
APP_PREFIX = "AC"
APP_COLOR = "#EC4899"

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache TTL (seconds)
CACHE_SHORT = 300       # 5 minutes
CACHE_MEDIUM = 3600     # 1 hour
CACHE_LONG = 86400      # 24 hours

# Status constants
STATUS_DRAFT = "Draft"
STATUS_ACTIVE = "Active"
STATUS_CANCELLED = "Cancelled"
STATUS_COMPLETED = "Completed"

# Date formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
