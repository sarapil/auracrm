# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""Deal Room public page context."""
import frappe


def get_context(context):
    from auracrm.deal_rooms.generator import get_deal_room_context
    get_deal_room_context(context)
