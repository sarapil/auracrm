"""Deal Room public page context."""
import frappe


def get_context(context):
    from auracrm.deal_rooms.generator import get_deal_room_context
    get_deal_room_context(context)
