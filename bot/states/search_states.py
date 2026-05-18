from vkbottle.dispatch.dispenser.base import BaseStateGroup


class SearchState(BaseStateGroup):
    BROWSING = "search_browsing"


class ReportState(BaseStateGroup):
    REASON = "report_reason"


class AdminState(BaseStateGroup):
    WAITING = "admin_waiting"
