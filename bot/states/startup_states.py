from aiogram.fsm.state import State, StatesGroup


class StartupForm(StatesGroup):
    name = State()
    description = State()
    tags = State()
    stage = State()
    needs = State()
    contact = State()
    confirm = State()


class StartupEdit(StatesGroup):
    choose_field = State()
    edit_value = State()
