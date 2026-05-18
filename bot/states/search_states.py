from aiogram.fsm.state import State, StatesGroup


class SearchState(StatesGroup):
    browsing = State()


class ReportState(StatesGroup):
    reason = State()
