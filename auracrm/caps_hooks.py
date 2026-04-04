# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM × CAPS — Doc Event Handlers
=====================================

Server-side field filtering for core DocTypes (Lead, Opportunity)
that AuraCRM doesn't own but needs to protect.
"""

from caps.overrides import filter_response_fields, validate_field_write_permissions


def on_load_lead(doc, method):
    """Filter restricted fields when a Lead is loaded."""
    filter_response_fields(doc)


def on_load_opportunity(doc, method):
    """Filter restricted fields when an Opportunity is loaded."""
    filter_response_fields(doc)


def validate_lead(doc, method):
    """Prevent writes to restricted fields on Lead save."""
    validate_field_write_permissions(doc)


def validate_opportunity(doc, method):
    """Prevent writes to restricted fields on Opportunity save."""
    validate_field_write_permissions(doc)
